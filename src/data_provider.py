import asyncio
import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import aiohttp
import pandas as pd
import talib
from asyncio_throttle import Throttler
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    from .enhanced_indicators import EnhancedTechnicalAnalysis
except ImportError:
    from enhanced_indicators import EnhancedTechnicalAnalysis

# Configure logging
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Configuration settings for data providers"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra fields
    )

    # OKX DEX API Configuration
    okx_api_key: Optional[str] = None
    okx_secret_key: Optional[str] = None
    okx_api_passphrase: Optional[str] = None
    okx_project_id: Optional[str] = None
    okx_base_url: str = "https://web3.okx.com/api/v5/"

    # Rate limiting
    rate_limit_requests_per_second: int = 10

    # Error handling
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout_seconds: int = 30

    # Technical Analysis Configuration
    default_indicators: str = "sma,ema,rsi,macd,bb,stoch"
    sma_periods: str = "20,50,200"
    ema_periods: str = "12,26,50"
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    bb_period: int = 20
    bb_std: float = 2.0
    stoch_k: int = 14
    stoch_d: int = 3

    @classmethod
    def from_env_dict(cls, env_vars: Dict[str, str]) -> 'Settings':
        """Create Settings instance from environment variables dictionary"""
        # Temporarily set environment variables
        original_env = {}
        for key, value in env_vars.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value

        try:
            # Create a Settings instance, which will read the configuration from the environment variables
            settings = cls()
            return settings
        finally:
            # Restore the original environment variables
            for key, original_value in original_env.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value


# Removed unnecessary MarketData class


class OKXDEXClient:
    """OKX DEX API client with authentication"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.session: Optional[aiohttp.ClientSession] = None
        self.throttler = Throttler(
            rate_limit=settings.rate_limit_requests_per_second,
            period=1.0
        )

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.settings.timeout_seconds)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _get_headers(self, timestamp: str, method: str, request_path: str, query_string: str = "", body: str = "") -> Dict[str, str]:
        """Generate authenticated headers for OKX API"""
        if not all([self.settings.okx_api_key, self.settings.okx_secret_key,
                   self.settings.okx_api_passphrase, self.settings.okx_project_id]):
            raise ValueError("OKX API credentials not configured")

        string_to_sign = timestamp + method + request_path + query_string + body
        import base64
        signature_b64 = base64.b64encode(
            hmac.new(
                self.settings.okx_secret_key.encode(),
                string_to_sign.encode(),
                hashlib.sha256
            ).digest()
        ).decode()

        return {
            "Content-Type": "application/json",
            "OK-ACCESS-KEY": self.settings.okx_api_key,
            "OK-ACCESS-SIGN": signature_b64,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.settings.okx_api_passphrase,
            "OK-ACCESS-PROJECT": self.settings.okx_project_id
        }

    async def get_batch_token_prices(self, tokens: List[Dict[str, str]]) -> Optional[List[Dict[str, Any]]]:
        """Get batch token prices from OKX DEX API"""
        async with self.throttler:
            path = "dex/market/price"
            url = f"{self.settings.okx_base_url}{path}"

            # OKX required timestamp format: 2020-12-08T09:08:57.715Z
            timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            request_path = f"/api/v5/{path}"
            body = json.dumps(tokens)

            headers = self._get_headers(timestamp, "POST", request_path, "", body)

            try:
                async with self.session.post(url, headers=headers, data=body) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("code") == "0":
                            return result.get("data", [])
                    logger.error(f"OKX API error: {response.status} - {await response.text()}")
                    return None
            except Exception as e:
                logger.error(f"Error fetching OKX price data: {e}")
                return None

    async def get_token_price(self, chain_index: str, token_address: str) -> Optional[Dict[str, Any]]:
        """Get a single token price from OKX DEX API"""
        tokens = [{"chainIndex": chain_index, "tokenContractAddress": token_address}]
        prices = await self.get_batch_token_prices(tokens)
        if prices:
            return prices[0]
        return None

    async def get_token_candles(self, chain_index: str, token_address: str, bar: str = "1H", limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """Get token K-line data from OKX DEX API"""
        async with self.throttler:
            path = "dex/market/candles"
            url = f"{self.settings.okx_base_url}{path}"

            params = {
                "chainIndex": chain_index,
                "tokenContractAddress": token_address.lower(),  # EVM chains require lowercase addresses
                "bar": bar,
                "limit": str(min(limit, 299))
            }

            # OKX required timestamp format: 2020-12-08T09:08:57.715Z
            timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            request_path = f"/api/v5/{path}"
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])

            headers = self._get_headers(timestamp, "GET", request_path, f"?{query_string}")

            try:
                async with self.session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("code") == "0":
                            return result.get("data", [])
                    logger.error(f"OKX API error: {response.status} - {await response.text()}")
                    return None
            except Exception as e:
                logger.error(f"Error fetching OKX candles data: {e}")
                return None


# Removed unnecessary EnhancedDataProvider class, keeping only core functionality

class TechnicalAnalysis:
    """Advanced technical analysis using TA-Lib"""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.enhanced_ta = EnhancedTechnicalAnalysis()

    def add_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add various moving averages"""
        if df is None or df.empty:
            return df

        close = df['close'].values

        # Simple Moving Averages
        sma_periods = [int(p) for p in self.settings.sma_periods.split(',')]
        for period in sma_periods:
            if len(close) >= period:
                df[f'SMA_{period}'] = talib.SMA(close, timeperiod=period)

        # Exponential Moving Averages
        ema_periods = [int(p) for p in self.settings.ema_periods.split(',')]
        for period in ema_periods:
            if len(close) >= period:
                df[f'EMA_{period}'] = talib.EMA(close, timeperiod=period)

        # Weighted Moving Average
        if len(close) >= 20:
            df['WMA_20'] = talib.WMA(close, timeperiod=20)

        return df

    def add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum indicators"""
        if df is None or df.empty:
            return df

        close = df['close'].values
        high = df['high'].values
        low = df['low'].values

        # RSI
        if len(close) >= self.settings.rsi_period:
            df['RSI'] = talib.RSI(close, timeperiod=self.settings.rsi_period)

        # MACD
        if len(close) >= max(self.settings.macd_fast, self.settings.macd_slow):
            macd, macd_signal, macd_hist = talib.MACD(
                close,
                fastperiod=self.settings.macd_fast,
                slowperiod=self.settings.macd_slow,
                signalperiod=self.settings.macd_signal
            )
            df['MACD'] = macd
            df['MACD_Signal'] = macd_signal
            df['MACD_Histogram'] = macd_hist

        # Stochastic
        if len(close) >= self.settings.stoch_k:
            slowk, slowd = talib.STOCH(
                high, low, close,
                fastk_period=self.settings.stoch_k,
                slowk_period=self.settings.stoch_d,
                slowd_period=self.settings.stoch_d
            )
            df['STOCH_K'] = slowk
            df['STOCH_D'] = slowd

        # Williams %R
        if len(close) >= 14:
            df['WILLR'] = talib.WILLR(high, low, close, timeperiod=14)

        # Commodity Channel Index
        if len(close) >= 14:
            df['CCI'] = talib.CCI(high, low, close, timeperiod=14)

        return df

    def add_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility indicators"""
        if df is None or df.empty:
            return df

        close = df['close'].values
        high = df['high'].values
        low = df['low'].values

        # Bollinger Bands
        if len(close) >= self.settings.bb_period:
            bb_upper, bb_middle, bb_lower = talib.BBANDS(
                close,
                timeperiod=self.settings.bb_period,
                nbdevup=self.settings.bb_std,
                nbdevdn=self.settings.bb_std
            )
            df['BB_Upper'] = bb_upper
            df['BB_Middle'] = bb_middle
            df['BB_Lower'] = bb_lower
            df['BB_Width'] = (bb_upper - bb_lower) / bb_middle
            df['BB_Position'] = (close - bb_lower) / (bb_upper - bb_lower)

        # Average True Range
        if len(close) >= 14:
            df['ATR'] = talib.ATR(high, low, close, timeperiod=14)

        # Standard Deviation
        if len(close) >= 20:
            df['STDDEV'] = talib.STDDEV(close, timeperiod=20)

        return df

    def add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume indicators"""
        if df is None or df.empty:
            return df

        close = df['close'].values
        volume = df['volume'].values
        high = df['high'].values
        low = df['low'].values

        # On Balance Volume
        if len(close) >= 2:
            df['OBV'] = talib.OBV(close, volume)

        # Volume Weighted Average Price (approximation)
        if len(close) >= 20:
            typical_price = (high + low + close) / 3
            df['VWAP_20'] = (typical_price * volume).rolling(20).sum() / volume.rolling(20).sum()

        # Accumulation/Distribution Line
        if len(close) >= 2:
            df['AD'] = talib.AD(high, low, close, volume)

        return df

    def add_trend_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add trend indicators"""
        if df is None or df.empty:
            return df

        close = df['close'].values
        high = df['high'].values
        low = df['low'].values

        # Average Directional Index
        if len(close) >= 14:
            df['ADX'] = talib.ADX(high, low, close, timeperiod=14)
            df['PLUS_DI'] = talib.PLUS_DI(high, low, close, timeperiod=14)
            df['MINUS_DI'] = talib.MINUS_DI(high, low, close, timeperiod=14)

        # Parabolic SAR
        if len(close) >= 2:
            df['SAR'] = talib.SAR(high, low, acceleration=0.02, maximum=0.2)

        # Aroon
        if len(close) >= 14:
            aroon_down, aroon_up = talib.AROON(high, low, timeperiod=14)
            df['AROON_UP'] = aroon_up
            df['AROON_DOWN'] = aroon_down
            df['AROON_OSC'] = aroon_up - aroon_down

        return df

    def add_custom_indicators(self, df: pd.DataFrame, indicators_config: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
        """Add technical indicators with custom parameters"""
        if df is None or df.empty:
            return df

        if isinstance(indicators_config, str):
            try:
                indicators_config = json.loads(indicators_config)
            except json.JSONDecodeError:
                logger.error("Invalid JSON format for indicators_config")
                return df

        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values

        for indicator_name, params in indicators_config.items():
            try:
                if indicator_name.lower() == 'sma':
                    period = params.get('period', 20)
                    if len(close) >= period:
                        df[f'SMA_{period}'] = talib.SMA(close, timeperiod=period)

                elif indicator_name.lower() == 'ema':
                    period = params.get('period', 20)
                    if len(close) >= period:
                        df[f'EMA_{period}'] = talib.EMA(close, timeperiod=period)

                elif indicator_name.lower() == 'rsi':
                    period = params.get('period', 14)
                    if len(close) >= period:
                        df[f'RSI_{period}'] = talib.RSI(close, timeperiod=period)

                elif indicator_name.lower() == 'macd':
                    fast = params.get('fast', 12)
                    slow = params.get('slow', 26)
                    signal = params.get('signal', 9)
                    if len(close) >= max(fast, slow):
                        macd, macd_signal, macd_hist = talib.MACD(
                            close, fastperiod=fast, slowperiod=slow, signalperiod=signal
                        )
                        df[f'MACD_{fast}_{slow}'] = macd
                        df[f'MACD_Signal_{fast}_{slow}_{signal}'] = macd_signal
                        df[f'MACD_Histogram_{fast}_{slow}_{signal}'] = macd_hist

                elif indicator_name.lower() == 'bb':
                    period = params.get('period', 20)
                    std = params.get('std', 2)
                    if len(close) >= period:
                        bb_upper, bb_middle, bb_lower = talib.BBANDS(
                            close, timeperiod=period, nbdevup=std, nbdevdn=std
                        )
                        df[f'BB_Upper_{period}_{std}'] = bb_upper
                        df[f'BB_Middle_{period}_{std}'] = bb_middle
                        df[f'BB_Lower_{period}_{std}'] = bb_lower
                        df[f'BB_Width_{period}_{std}'] = (bb_upper - bb_lower) / bb_middle

                elif indicator_name.lower() == 'stoch':
                    k_period = params.get('k_period', 14)
                    d_period = params.get('d_period', 3)
                    if len(close) >= k_period:
                        slowk, slowd = talib.STOCH(
                            high, low, close,
                            fastk_period=k_period,
                            slowk_period=d_period,
                            slowd_period=d_period
                        )
                        df[f'STOCH_K_{k_period}_{d_period}'] = slowk
                        df[f'STOCH_D_{k_period}_{d_period}'] = slowd

                elif indicator_name.lower() == 'atr':
                    period = params.get('period', 14)
                    if len(close) >= period:
                        df[f'ATR_{period}'] = talib.ATR(high, low, close, timeperiod=period)

                elif indicator_name.lower() == 'adx':
                    period = params.get('period', 14)
                    if len(close) >= period:
                        df[f'ADX_{period}'] = talib.ADX(high, low, close, timeperiod=period)
                        df[f'PLUS_DI_{period}'] = talib.PLUS_DI(high, low, close, timeperiod=period)
                        df[f'MINUS_DI_{period}'] = talib.MINUS_DI(high, low, close, timeperiod=period)

                elif indicator_name.lower() == 'obv':
                    if len(close) >= 2:
                        df['OBV'] = talib.OBV(close, volume)

                elif indicator_name.lower() == 'cci':
                    period = params.get('period', 14)
                    if len(close) >= period:
                        df[f'CCI_{period}'] = talib.CCI(high, low, close, timeperiod=period)

                elif indicator_name.lower() == 'willr':
                    period = params.get('period', 14)
                    if len(close) >= period:
                        df[f'WILLR_{period}'] = talib.WILLR(high, low, close, timeperiod=period)

            except Exception as e:
                logger.error(f"Error calculating {indicator_name}: {e}")

        return df

    def add_all_indicators(self, df: pd.DataFrame, indicators: Optional[List[str]] = None) -> pd.DataFrame:
        """Add all or specified technical indicators"""
        if df is None or df.empty:
            return df

        if indicators is None:
            indicators = self.settings.default_indicators.split(',')

        indicator_map = {
            'sma': self.add_moving_averages,
            'ema': self.add_moving_averages,
            'rsi': self.add_momentum_indicators,
            'macd': self.add_momentum_indicators,
            'bb': self.add_volatility_indicators,
            'stoch': self.add_momentum_indicators,
            'volume': self.add_volume_indicators,
            'trend': self.add_trend_indicators,
        }

        # Apply indicators
        for indicator in indicators:
            indicator = indicator.strip().lower()
            if indicator in indicator_map:
                try:
                    df = indicator_map[indicator](df)
                except Exception as e:
                    logger.error(f"Error adding {indicator} indicators: {e}")

        return df

    def add_enhanced_indicators(self, df: pd.DataFrame, indicators_config: Dict[str, List[Dict[str, Any]]]) -> pd.DataFrame:
        """
        Add technical indicators with flexible multi-parameter support

        Args:
            df: DataFrame with OHLCV data
            indicators_config: Dict with indicator names and parameter lists
                Example: {
                    'ema': [{'timeperiod': 12}, {'timeperiod': 26}, {'timeperiod': 120}],
                    'macd': [{'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9}],
                    'rsi': [{'timeperiod': 14}, {'timeperiod': 21}]
                }

        Returns:
            DataFrame with original data plus calculated indicators with proper labeling
            (e.g., ema_12, ema_26, ema_120, macd_12_26_9, rsi_14, rsi_21)
        """
        if df is None or df.empty:
            return df

        try:
            return self.enhanced_ta.calculate_indicators(df, indicators_config)
        except Exception as e:
            logger.error(f"Error calculating enhanced indicators: {e}")
            return df

    def get_available_indicators(self) -> Dict[str, Any]:
        """Get information about all available indicators"""
        try:
            indicators = self.enhanced_ta.get_available_indicators()
            return {
                name: {
                    'category': indicator.category.value,
                    'description': indicator.description,
                    'input_data': [data.value for data in indicator.input_data],
                    'parameters': [
                        {
                            'name': param.name,
                            'type': param.type.__name__,
                            'default': param.default,
                            'min_value': param.min_value,
                            'max_value': param.max_value,
                            'description': param.description
                        }
                        for param in indicator.parameters
                    ],
                    'output_names': indicator.output_names,
                    'min_periods': indicator.min_periods
                }
                for name, indicator in indicators.items()
            }
        except Exception as e:
            logger.error(f"Error getting available indicators: {e}")
            return {}


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Legacy function for backward compatibility"""
    if df is None or df.empty:
        return df

    ta = TechnicalAnalysis()
    return ta.add_all_indicators(df)

# Removed unnecessary functions, keeping only core functionality

# Removed example code