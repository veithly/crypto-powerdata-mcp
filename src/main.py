import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import asyncio

import pandas as pd
import numpy as np
import ccxt
import talib
from mcp.server.fastmcp import FastMCP

try:
    from .data_provider import Settings, OKXDEXClient, TechnicalAnalysis
except ImportError:
    from data_provider import Settings, OKXDEXClient, TechnicalAnalysis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global settings instance
_global_settings: Optional[Settings] = None

def set_global_settings(env_vars: Optional[Dict[str, str]] = None) -> None:
    """Set global settings from environment variables"""
    global _global_settings
    if env_vars:
        _global_settings = Settings.from_env_dict(env_vars)
    else:
        _global_settings = Settings()

def get_global_settings() -> Settings:
    """Get global settings instance"""
    global _global_settings
    if _global_settings is None:
        _global_settings = Settings()
    return _global_settings


def parse_indicators_config(indicators_config: Any) -> Dict[str, Any]:
    """
    Robust parsing of indicators configuration from various input formats.

    Handles quote format conversion between JSON strings and Python dictionaries:
    - JSON input: {"macd": [{"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}]}
    - Python output: {'macd': [{'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9}]}

    Also handles:
    - String JSON input (most common from MCP clients)
    - Dictionary input (direct Python usage)
    - Malformed JSON with common issues
    - Empty or None inputs

    Args:
        indicators_config: Input configuration in various formats

    Returns:
        Parsed dictionary with single quotes (Python dict format) or raises ValueError
    """
    if not indicators_config:
        logger.debug("Empty indicators_config, returning empty dict")
        return {}

    # If already a dictionary, return as-is (already in Python format with single quotes)
    if isinstance(indicators_config, dict):
        logger.debug(f"indicators_config already a dict: {indicators_config}")
        return indicators_config

    # If not a string, try to convert
    if not isinstance(indicators_config, str):
        try:
            indicators_config = str(indicators_config)
            logger.debug(f"Converted indicators_config to string: {indicators_config}")
        except Exception:
            raise ValueError("indicators_config must be a JSON string or dictionary")

    # Clean up common JSON formatting issues
    indicators_config = indicators_config.strip()

    # Handle empty string
    if not indicators_config:
        logger.debug("Empty string indicators_config, returning empty dict")
        return {}

    logger.debug(f"Parsing JSON string: {indicators_config}")

    # Handle double-encoded JSON (when JSON string is passed within another JSON)
    # Example: "{\"macd\": [{\"fastperiod\": 12}]}" -> {"macd": [{"fastperiod": 12}]}
    if indicators_config.startswith('"{') and indicators_config.endswith('}"'):
        logger.debug("Detected double-encoded JSON, attempting to decode")
        try:
            # First decode the outer JSON string
            decoded_once = json.loads(indicators_config)
            logger.debug(f"First decode result: {decoded_once}")

            # Now parse the inner JSON
            if isinstance(decoded_once, str):
                indicators_config = decoded_once
                logger.debug(f"Using decoded string: {indicators_config}")
        except json.JSONDecodeError:
            logger.debug("Double-decode failed, continuing with original string")

    # Try to parse as JSON (this will convert double quotes to single quotes in Python dict)
    try:
        parsed = json.loads(indicators_config)
        if not isinstance(parsed, dict):
            raise ValueError("indicators_config must be a JSON object/dictionary")

        logger.debug(f"Successfully parsed JSON to Python dict: {parsed}")
        return parsed

    except json.JSONDecodeError as e:
        logger.debug(f"Initial JSON parsing failed: {e}, attempting auto-correction")

        # Try to fix common JSON issues
        try:
            # Fix single quotes to double quotes
            fixed_config = indicators_config.replace("'", '"')

            # Fix unquoted keys (basic regex for simple cases)
            fixed_config = re.sub(r'(\w+):', r'"\1":', fixed_config)

            logger.debug(f"Auto-corrected JSON: {fixed_config}")

            # Try parsing again
            parsed = json.loads(fixed_config)
            if not isinstance(parsed, dict):
                raise ValueError("indicators_config must be a JSON object/dictionary")

            logger.info(f"Successfully auto-corrected and parsed JSON: {parsed}")
            return parsed

        except json.JSONDecodeError:
            # Provide helpful error message with examples showing quote conversion
            raise ValueError(
                f"Invalid JSON format in indicators_config: {str(e)}\n\n"
                "Expected format examples (JSON strings with double quotes):\n"
                '1. Enhanced format: \'{"ema": [{"timeperiod": 12}, {"timeperiod": 26}], "macd": [{"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}]}\'\n'
                '2. Legacy format: \'{"sma": {"period": 20}, "rsi": {"period": 14}}\'\n'
                '3. Double-encoded: \'"{\\\"macd\\\": [{\\\"fastperiod\\\": 12, \\\"slowperiod\\\": 26, \\\"signalperiod\\\": 9}]}"\'\n'
                '4. Simple format: \'{"ema": {"timeperiod": 12}, "rsi": {"timeperiod": 14}}\'\n\n'
                "Note: JSON input uses double quotes, Python output uses single quotes (automatic conversion)\n"
                "Input:  {\"macd\": [{\"fastperiod\": 12, \"slowperiod\": 26, \"signalperiod\": 9}]}\n"
                "Output: {'macd': [{'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9}]}\n\n"
                "Double-encoded JSON (from MCP clients):\n"
                'Input:  "{\\\"macd\\\": [{\\\"fastperiod\\\": 12, \\\"slowperiod\\\": 26, \\\"signalperiod\\\": 9}]}"\n'
                "Output: {'macd': [{'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9}]}\n\n"
                "Common issues:\n"
                "- Use double quotes (\") in JSON strings, not single quotes (')\n"
                "- Ensure all keys and string values are quoted\n"
                "- Check for missing commas or brackets\n"
                "- Avoid trailing commas"
            )


def validate_exchange_symbol(exchange: str, symbol: str) -> tuple[bool, str]:
    """
    Validate exchange and symbol parameters.

    Args:
        exchange: Exchange identifier
        symbol: Trading pair symbol

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not exchange or not isinstance(exchange, str):
        return False, "exchange must be a non-empty string (e.g., 'binance', 'coinbase', 'kraken')"

    if not symbol or not isinstance(symbol, str):
        return False, "symbol must be a non-empty string (e.g., 'BTC/USDT', 'ETH/USD')"

    # Check if symbol has the expected format
    if '/' not in symbol:
        return False, f"symbol '{symbol}' should be in format 'BASE/QUOTE' (e.g., 'BTC/USDT', 'ETH/USD')"

    return True, ""


def validate_dex_parameters(chain_index: str, token_address: str) -> tuple[bool, str]:
    """
    Validate DEX parameters.

    Args:
        chain_index: Blockchain chain identifier
        token_address: Token contract address

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not chain_index or not isinstance(chain_index, str):
        return False, "chain_index must be a non-empty string (e.g., '1' for Ethereum, '56' for BSC)"

    if not token_address or not isinstance(token_address, str):
        return False, "token_address must be a non-empty string (contract address)"

    # Basic validation for Ethereum-like addresses
    if len(token_address) == 42 and token_address.startswith('0x'):
        # Valid Ethereum address format
        pass
    elif len(token_address) < 10:
        return False, f"token_address '{token_address}' appears to be too short for a valid contract address"

    return True, ""

# Create the FastMCP server
mcp = FastMCP(
    name="Crypto PowerData MCP",
    instructions="MCP service for fetching cryptocurrency data: CEX real-time prices and DEX data with custom technical indicators."
)


def convert_okx_candles_to_dataframe(candles_data: List[List], timeframe: str = "1H") -> pd.DataFrame:
    """Converts OKX candlestick data to a DataFrame."""
    if not candles_data:
        return pd.DataFrame()

    # OKX returns data in the format: [ts, o, h, l, c, vol, volUsd, confirm]
    df_data = []
    for candle in candles_data:
        df_data.append({
            'timestamp': pd.to_datetime(int(candle[0]), unit='ms'),
            'open': float(candle[1]),
            'high': float(candle[2]),
            'low': float(candle[3]),
            'close': float(candle[4]),
            'volume': float(candle[5]),
            'volume_usd': float(candle[6]),
            'confirm': int(candle[7])
        })

    df = pd.DataFrame(df_data)
    df.set_index('timestamp', inplace=True)
    df.sort_index(inplace=True)  # Ensure correct time order

    return df


def apply_custom_indicators(df: pd.DataFrame, indicators_config: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """Applies custom technical indicators."""
    if df.empty or not indicators_config:
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

        except Exception as e:
            logger.error(f"Error calculating {indicator_name}: {e}")

    return df


@mcp.tool(title="Get CEX Data with Enhanced Indicators")
async def get_cex_data_with_indicators(
    exchange: str,
    symbol: str,
    timeframe: str = "1h",
    limit: int = 100,
    indicators_config: Union[str, Dict[str, Any]] = '{"ema": [{"timeperiod": 12}, {"timeperiod": 26}], "rsi": [{"timeperiod": 14}]}',
    use_enhanced: bool = True
) -> Dict[str, Any]:
    """
    Fetches candlestick data from a centralized exchange (CEX) and calculates technical indicators.

    This tool supports fetching OHLCV (Open, High, Low, Close, Volume) data from 100+ cryptocurrency
    exchanges via CCXT library and applies comprehensive technical analysis indicators.

    PARAMETER FORMATS:
    All parameters are passed as strings when called via MCP. The tool handles parsing automatically.

    EXCHANGE EXAMPLES:
    - Major exchanges: 'binance', 'coinbase', 'kraken', 'okx', 'bybit', 'kucoin'
    - Regional exchanges: 'bitfinex', 'huobi', 'gate', 'mexc', 'bitget'
    - Full list: https://docs.ccxt.com/en/latest/exchange-markets.html

    SYMBOL FORMATS:
    - Spot trading pairs: 'BTC/USDT', 'ETH/USD', 'ADA/BTC', 'DOT/EUR'
    - Futures contracts: 'BTC/USDT:USDT' (perpetual), 'ETH/USD:USD-240329' (dated)
    - Options: 'BTC/USD:USD-240329-50000-C' (call option)

    TIMEFRAME OPTIONS:
    - Minutes: '1m', '3m', '5m', '15m', '30m'
    - Hours: '1h', '2h', '4h', '6h', '8h', '12h'
    - Days: '1d', '3d', '1w', '1M' (1 month)

    INDICATORS CONFIGURATION:
    Pass as JSON string OR Python dictionary with flexible multi-parameter support.
    The server automatically converts between different quote formats and handles both
    input types seamlessly.

    Enhanced Format (Recommended):
    JSON String: '{"ema": [{"timeperiod": 12}, {"timeperiod": 26}], "macd": [{"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}]}'
    Python Dict: {'ema': [{'timeperiod': 12}, {'timeperiod': 26}], 'macd': [{'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9}]}

    Legacy Format (Also Supported):
    JSON String: '{"sma": {"period": 20}, "rsi": {"period": 14}}'
    Python Dict: {'sma': {'period': 20}, 'rsi': {'period': 14}}

    PARAMETER QUOTE HANDLING:
    - JSON strings use double quotes: {"macd": [{"fastperiod": 12}]}
    - Python dictionaries use single quotes: {'macd': [{'fastperiod': 12}]}
    - Server automatically handles the conversion between formats

    DOUBLE-ENCODED JSON SUPPORT:
    - Handles MCP client double-encoding: "{\"macd\": [{\"fastperiod\": 12}]}"
    - Automatically detects and decodes nested JSON strings
    - Works with complex multi-indicator configurations

    COMMON INDICATORS:
    - Moving Averages: sma, ema, wma, dema, tema, trima
    - Momentum: rsi, stoch, willr, cci, mfi, roc, mom
    - Trend: macd, adx, aroon, sar, apo, ppo
    - Volatility: bbands, atr, natr, trange
    - Volume: obv, ad, adosc, chaikin

    Args:
        exchange: Exchange identifier (string) - e.g., 'binance', 'coinbase', 'kraken'
        symbol: Trading pair (string) - e.g., 'BTC/USDT', 'ETH/USD', 'BTC/USDT:USDT'
        timeframe: Candlestick interval (string) - e.g., '1m', '5m', '1h', '4h', '1d'
        limit: Number of candles to fetch (string/int) - range: 1-500, default: 100
        indicators_config: JSON string or dictionary with indicator configuration (see examples above)
        use_enhanced: Use enhanced indicator system (string/bool) - 'true'/'false', default: true

    Returns:
        Dictionary with success status, OHLCV data, calculated indicators, and metadata.

    Example Response:
    {
        "success": true,
        "data": [
            {
                "timestamp": "2024-01-01T00:00:00",
                "open": 42000.0, "high": 42500.0, "low": 41800.0, "close": 42200.0, "volume": 1234.56,
                "ema_12": 42150.0, "ema_26": 42100.0, "rsi_14": 65.5
            }
        ],
        "metadata": {
            "source": "CEX", "exchange": "binance", "symbol": "BTC/USDT",
            "total_candles": 100, "indicators_applied": ["ema", "rsi"]
        }
    }
    """
    try:
        # Validate input parameters
        is_valid, error_msg = validate_exchange_symbol(exchange, symbol)
        if not is_valid:
            return {"success": False, "error": error_msg}

        # Validate and convert limit
        try:
            limit = int(limit)
            if limit < 1 or limit > 500:
                return {"success": False, "error": "limit must be between 1 and 500"}
        except (ValueError, TypeError):
            return {"success": False, "error": "limit must be a valid integer"}

        # Parse indicators configuration with robust error handling
        try:
            indicators_dict = parse_indicators_config(indicators_config)
        except ValueError as e:
            return {"success": False, "error": str(e)}

        # Validate exchange exists and supports OHLCV
        try:
            exchange_class = getattr(ccxt, exchange.lower())
        except AttributeError:
            return {
                "success": False,
                "error": f"Exchange '{exchange}' not supported. Available exchanges: {', '.join(sorted(ccxt.exchanges))}"
            }

        exchange_instance = exchange_class()

        if not exchange_instance.has.get('fetchOHLCV', False):
            return {"success": False, "error": f"Exchange '{exchange}' does not support fetching OHLCV data"}

        # Fetch OHLCV data
        try:
            ohlcv = exchange_instance.fetch_ohlcv(symbol, timeframe, limit=limit)
        except ccxt.BaseError as e:
            return {"success": False, "error": f"Failed to fetch data from {exchange}: {str(e)}"}
        finally:
            if hasattr(exchange_instance, 'close'):
                await exchange_instance.close()

        if not ohlcv:
            return {"success": False, "error": "No OHLCV data returned from exchange"}

        # Convert to DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        # Apply indicators if configured
        if indicators_dict:
            settings = get_global_settings()
            ta = TechnicalAnalysis(settings)

            if use_enhanced:
                # Use enhanced indicators system
                df = ta.add_enhanced_indicators(df, indicators_dict)
            else:
                # Use legacy system (convert format if needed)
                legacy_config = {}
                for indicator, params in indicators_dict.items():
                    if isinstance(params, list) and len(params) > 0:
                        # Take first parameter set for legacy compatibility
                        legacy_config[indicator] = params[0]
                    else:
                        legacy_config[indicator] = params
                df = apply_custom_indicators(df, legacy_config)

        # Convert to JSON-serializable format
        result_data = df.reset_index().to_dict('records')

        # Convert timestamps to ISO format and handle NaN values
        for record in result_data:
            if 'timestamp' in record:
                record['timestamp'] = record['timestamp'].isoformat()
            # Convert NaN values to None for JSON serialization
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None

        return {
            "success": True,
            "data": result_data,
            "metadata": {
                "source": "CEX",
                "exchange": exchange,
                "symbol": symbol,
                "timeframe": timeframe,
                "limit": limit,
                "indicators_applied": list(indicators_dict.keys()) if indicators_dict else [],
                "enhanced_mode": use_enhanced,
                "total_candles": len(result_data),
                "columns": list(df.columns),
                "fetched_at": datetime.now().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"Error in get_cex_data_with_indicators: {e}")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}


@mcp.tool(title="Get DEX Data with Enhanced Indicators")
async def get_dex_data_with_indicators(
    chain_index: str,
    token_address: str,
    timeframe: str = "1h",
    limit: int = 100,
    indicators_config: Union[str, Dict[str, Any]] = '{"ema": [{"timeperiod": 12}, {"timeperiod": 26}], "rsi": [{"timeperiod": 14}]}',
    use_enhanced: bool = True
) -> Dict[str, Any]:
    """
    Fetches decentralized exchange (DEX) token data from OKX DEX API and calculates technical indicators.

    This tool provides access to DEX token candlestick data and real-time prices across multiple
    blockchain networks, with comprehensive technical analysis capabilities.

    SUPPORTED BLOCKCHAINS:
    - Ethereum (chain_index: '1')
    - BSC/BNB Chain (chain_index: '56')
    - Polygon (chain_index: '137')
    - Avalanche (chain_index: '43114')
    - Arbitrum (chain_index: '42161')
    - Optimism (chain_index: '10')
    - Fantom (chain_index: '250')

    TOKEN ADDRESS FORMATS:
    - Ethereum/EVM: '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48' (USDC)
    - Must be valid contract addresses (42 characters starting with 0x)
    - Case-insensitive (automatically converted to lowercase)

    TIMEFRAME OPTIONS:
    - Minutes: '1m', '3m', '5m', '15m', '30m'
    - Hours: '1h', '2h', '4h', '6h', '12h'
    - Days: '1d', '1w', '1M'

    INDICATORS CONFIGURATION:
    Same flexible format as CEX data - pass as JSON string with automatic quote conversion:

    Enhanced Format:
    Input: '{"ema": [{"timeperiod": 12}, {"timeperiod": 26}], "macd": [{"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}]}'
    Parsed: {'ema': [{'timeperiod': 12}, {'timeperiod': 26}], 'macd': [{'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9}]}

    QUOTE FORMAT CONVERSION:
    - JSON input uses double quotes: {"macd": [{"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}]}
    - Python processing uses single quotes: {'macd': [{'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9}]}
    - Server handles conversion automatically - both formats work correctly

    DOUBLE-ENCODED JSON SUPPORT:
    - Handles MCP client double-encoding: "{\"macd\": [{\"fastperiod\": 12, \"slowperiod\": 26, \"signalperiod\": 9}]}"
    - Automatically detects and decodes when JSON is passed within JSON
    - Supports complex nested indicator configurations

    POPULAR DEX TOKENS:
    - USDC: '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48' (Ethereum)
    - USDT: '0xdac17f958d2ee523a2206206994597c13d831ec7' (Ethereum)
    - WETH: '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2' (Ethereum)
    - WBNB: '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c' (BSC)

    Args:
        chain_index: Blockchain identifier (string) - e.g., '1' for Ethereum, '56' for BSC
        token_address: Token contract address (string) - e.g., '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
        timeframe: Candlestick interval (string) - e.g., '1m', '1h', '4h', '1d'
        limit: Number of candles to fetch (string/int) - range: 1-300, default: 100
        indicators_config: JSON string or dictionary with indicator configuration
        use_enhanced: Use enhanced indicator system (string/bool) - default: true

    Returns:
        Dictionary with success status, price info, candlestick data, indicators, and metadata.

    Example Response:
    {
        "success": true,
        "data": {
            "price_info": {"price": "1.0001", "priceChange24h": "0.0001"},
            "klines": [{"timestamp": "2024-01-01T00:00:00", "open": 1.0, "close": 1.0001, "ema_12": 1.0005}],
            "indicators": {"columns": ["ema_12", "rsi_14"], "latest_values": {"ema_12": 1.0005, "rsi_14": 45.2}}
        }
    }
    """
    try:
        # Validate input parameters
        is_valid, error_msg = validate_dex_parameters(chain_index, token_address)
        if not is_valid:
            return {"success": False, "error": error_msg}

        # Validate and convert limit
        try:
            limit = int(limit)
            if limit < 1 or limit > 300:
                return {"success": False, "error": "limit must be between 1 and 300 for DEX data"}
        except (ValueError, TypeError):
            return {"success": False, "error": "limit must be a valid integer"}

        # Parse indicators configuration with robust error handling
        try:
            indicators_dict = parse_indicators_config(indicators_config)
        except ValueError as e:
            return {"success": False, "error": str(e)}

        # Use global settings
        settings = get_global_settings()

        # Get OKX DEX data
        async with OKXDEXClient(settings) as client:
            # Get token price information
            price_data = await client.get_token_price(chain_index, token_address)

            if not price_data:
                return {
                    "success": False,
                    "error": "Could not fetch token price data from OKX DEX API. Check chain_index and token_address."
                }

            # Convert timeframe format (1h -> 1H, 1d -> 1D, etc.)
            timeframe_map = {
                '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1h': '1H', '2h': '2H', '4h': '4H', '6h': '6H', '12h': '12H',
                '1d': '1D', '1w': '1W', '1M': '1M'
            }
            okx_timeframe = timeframe_map.get(timeframe, '1H')

            # Get candlestick data
            candles_data = await client.get_token_candles(chain_index, token_address, okx_timeframe, limit)

            if not candles_data:
                # If no candlestick data, return only price information
                return {
                    "success": True,
                    "data": {
                        "price_info": price_data,
                        "klines": [],
                        "indicators": {}
                    },
                    "metadata": {
                        "chain_index": chain_index,
                        "token_address": token_address,
                        "source": "OKX DEX API",
                        "note": "No historical candlestick data available, only current price",
                        "timestamp": datetime.now().isoformat()
                    }
                }

            # Convert candlestick data to DataFrame
            klines_df = convert_okx_candles_to_dataframe(candles_data, timeframe)

            if klines_df.empty:
                return {
                    "success": False,
                    "error": "Could not process candlestick data"
                }

            # Apply technical indicators if configured
            if indicators_dict:
                settings = get_global_settings()
                ta = TechnicalAnalysis(settings)

                if use_enhanced:
                    # Use enhanced indicators system
                    klines_df = ta.add_enhanced_indicators(klines_df, indicators_dict)
                else:
                    # Use legacy system (convert format if needed)
                    legacy_config = {}
                    for indicator, params in indicators_dict.items():
                        if isinstance(params, list) and len(params) > 0:
                            # Take first parameter set for legacy compatibility
                            legacy_config[indicator] = params[0]
                        else:
                            legacy_config[indicator] = params
                    klines_df = apply_custom_indicators(klines_df, legacy_config)

            # Get indicator list and latest values
            indicator_columns = [col for col in klines_df.columns if col not in ['open', 'high', 'low', 'close', 'volume', 'volume_usd', 'confirm']]
            latest_indicators = {}
            if not klines_df.empty:
                latest_row = klines_df.iloc[-1]
                for col in indicator_columns:
                    value = latest_row[col]
                    latest_indicators[col] = float(value) if not pd.isna(value) else None

            # Convert DataFrame to JSON-serializable format
            klines_data = klines_df.reset_index().to_dict('records')

            # Convert timestamps to ISO format and handle NaN values
            for record in klines_data:
                if 'timestamp' in record:
                    record['timestamp'] = record['timestamp'].isoformat()
                # Convert NaN values to None for JSON serialization
                for key, value in record.items():
                    if pd.isna(value):
                        record[key] = None

            return {
                "success": True,
                "data": {
                    "price_info": price_data,
                    "klines": klines_data,
                    "indicators": {
                        "columns": indicator_columns,
                        "latest_values": latest_indicators
                    }
                },
                "metadata": {
                    "chain_index": chain_index,
                    "token_address": token_address,
                    "timeframe": timeframe,
                    "klines_count": len(klines_data),
                    "indicators_applied": list(indicators_dict.keys()) if indicators_dict else [],
                    "enhanced_mode": use_enhanced,
                    "source": "OKX DEX API",
                    "timestamp": datetime.now().isoformat()
                }
            }

    except Exception as e:
        logger.error(f"Error in get_dex_data_with_indicators: {e}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "metadata": {
                "chain_index": chain_index,
                "token_address": token_address,
                "timestamp": datetime.now().isoformat()
            }
        }


@mcp.tool(title="Get Enhanced DEX Data with Flexible Indicators")
async def get_enhanced_dex_data_with_indicators(
    chain_index: str,
    token_address: str,
    timeframe: str = "1h",
    limit: int = 100,
    indicators_config: Union[str, Dict[str, Any]] = '{"ema": [{"timeperiod": 12}, {"timeperiod": 26}], "rsi": [{"timeperiod": 14}]}'
) -> Dict[str, Any]:
    """
    Fetches DEX candlestick data with enhanced flexible technical indicators.

    Supports multiple instances of the same indicator with different parameters.

    Args:
        chain_index: Blockchain chain index (e.g., "1" for Ethereum)
        token_address: Token contract address
        timeframe: Candlestick timeframe (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1M)
        limit: Number of candlesticks to fetch (max 300)
        indicators_config: JSON string with flexible indicator configuration
            Example: '{"ema": [{"timeperiod": 12}, {"timeperiod": 26}, {"timeperiod": 120}],
                      "macd": [{"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}],
                      "rsi": [{"timeperiod": 14}, {"timeperiod": 21}]}'

    Returns:
        Dictionary containing candlestick data with enhanced indicators
        Indicators are labeled like: ema_12, ema_26, ema_120, macd_12_26_9, rsi_14, rsi_21
    """
    try:
        # Parse indicators configuration
        try:
            indicators_dict = json.loads(indicators_config)
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid indicators_config JSON: {e}"}

        settings = get_global_settings()
        async with OKXDEXClient(settings) as client:
            # Fetch candlestick data
            candles_data = await client.get_candlestick_data(
                chain_index=chain_index,
                token_address=token_address,
                timeframe=timeframe,
                limit=limit
            )

            if not candles_data:
                return {"success": False, "error": "No candlestick data available"}

            # Convert to DataFrame
            df = convert_okx_candles_to_dataframe(candles_data, timeframe)
            if df.empty:
                return {"success": False, "error": "Failed to process candlestick data"}

            # Apply enhanced indicators
            ta = TechnicalAnalysis(settings)
            df_with_indicators = ta.add_enhanced_indicators(df, indicators_dict)

            # Convert to JSON-serializable format
            result_data = df_with_indicators.reset_index().to_dict('records')

            # Convert timestamps to ISO format
            for record in result_data:
                if 'timestamp' in record:
                    record['timestamp'] = record['timestamp'].isoformat()

            return {
                "success": True,
                "data": {
                    "candles": result_data,
                    "metadata": {
                        "chain_index": chain_index,
                        "token_address": token_address,
                        "timeframe": timeframe,
                        "limit": limit,
                        "indicators_applied": list(indicators_dict.keys()),
                        "total_candles": len(result_data),
                        "columns": list(df_with_indicators.columns),
                        "timestamp": datetime.now().isoformat()
                    }
                }
            }

    except Exception as e:
        logger.error(f"Error in get_enhanced_dex_data_with_indicators: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool(title="Get Available Indicators")
async def get_available_indicators() -> Dict[str, Any]:
    """
    Get information about all available technical indicators.

    Returns:
        Dictionary containing all available indicators with their parameters,
        categories, descriptions, and usage information.
    """
    try:
        settings = get_global_settings()
        ta = TechnicalAnalysis(settings)
        indicators_info = ta.get_available_indicators()

        return {
            "success": True,
            "data": {
                "indicators": indicators_info,
                "total_indicators": len(indicators_info),
                "categories": list(set(info['category'] for info in indicators_info.values())),
                "usage_example": {
                    "ema": [{"timeperiod": 12}, {"timeperiod": 26}, {"timeperiod": 120}],
                    "macd": [{"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}],
                    "rsi": [{"timeperiod": 14}, {"timeperiod": 21}],
                    "bbands": [{"timeperiod": 20, "nbdevup": 2, "nbdevdn": 2}]
                }
            }
        }

    except Exception as e:
        logger.error(f"Error in get_available_indicators: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool(title="Get CEX Real-time Price")
async def get_cex_price(
    exchange: str,
    symbol: str,
    market_type: str = "spot"
) -> Dict[str, Any]:
    """
    Fetches real-time price data from centralized exchanges (CEX).

    Supports both spot and derivatives markets with comprehensive price information.

    MARKET TYPES:
    - 'spot': Spot trading pairs (BTC/USDT, ETH/USD)
    - 'future': Perpetual futures (BTC/USDT:USDT, ETH/USD:USD)
    - 'option': Options contracts (BTC/USD:USD-240329-50000-C)
    - 'swap': Perpetual swaps (same as future for most exchanges)

    SYMBOL FORMATS BY MARKET TYPE:

    Spot Markets:
    - 'BTC/USDT', 'ETH/USD', 'ADA/BTC', 'DOT/EUR'
    - 'MATIC/USDT', 'AVAX/USD', 'SOL/USDT'

    Futures/Perpetual:
    - 'BTC/USDT:USDT' (USDT-margined perpetual)
    - 'ETH/USD:USD' (USD-margined perpetual)
    - 'BTC/USD:USD-240329' (quarterly futures)

    Options:
    - 'BTC/USD:USD-240329-50000-C' (call option)
    - 'ETH/USD:USD-240329-3000-P' (put option)

    POPULAR EXCHANGES:
    - Spot: binance, coinbase, kraken, okx, bybit, kucoin
    - Futures: binance, okx, bybit, deribit, bitmex
    - Options: deribit, okx, bybit

    Args:
        exchange: Exchange identifier (string) - e.g., 'binance', 'okx', 'bybit'
        symbol: Trading symbol (string) - format depends on market_type
        market_type: Market type (string) - 'spot', 'future', 'option', 'swap'

    Returns:
        Dictionary with current price, 24h change, volume, and market data.

    Example Response:
    {
        "success": true,
        "data": {
            "symbol": "BTC/USDT",
            "price": 42000.0,
            "change": 1200.0,
            "percentage": 2.94,
            "high": 42500.0,
            "low": 40800.0,
            "volume": 1234567.89,
            "quoteVolume": 51234567890.12,
            "timestamp": "2024-01-01T12:00:00Z"
        }
    }
    """
    try:
        # Validate input parameters
        is_valid, error_msg = validate_exchange_symbol(exchange, symbol)
        if not is_valid:
            return {"success": False, "error": error_msg}

        if market_type not in ['spot', 'future', 'option', 'swap']:
            return {"success": False, "error": "market_type must be one of: spot, future, option, swap"}

        # Get exchange instance
        try:
            exchange_class = getattr(ccxt, exchange.lower())
        except AttributeError:
            return {
                "success": False,
                "error": f"Exchange '{exchange}' not supported. Available exchanges: {', '.join(sorted(ccxt.exchanges))}"
            }

        exchange_instance = exchange_class()

        try:
            # Set market type if supported
            if hasattr(exchange_instance, 'options'):
                if market_type == 'future' or market_type == 'swap':
                    exchange_instance.options['defaultType'] = 'future'
                elif market_type == 'option':
                    exchange_instance.options['defaultType'] = 'option'
                else:
                    exchange_instance.options['defaultType'] = 'spot'

            # Fetch ticker data
            ticker = exchange_instance.fetch_ticker(symbol)

            return {
                "success": True,
                "data": {
                    "symbol": ticker.get('symbol', symbol),
                    "price": ticker.get('last'),
                    "bid": ticker.get('bid'),
                    "ask": ticker.get('ask'),
                    "change": ticker.get('change'),
                    "percentage": ticker.get('percentage'),
                    "high": ticker.get('high'),
                    "low": ticker.get('low'),
                    "volume": ticker.get('baseVolume'),
                    "quoteVolume": ticker.get('quoteVolume'),
                    "open": ticker.get('open'),
                    "close": ticker.get('close'),
                    "timestamp": datetime.fromtimestamp(ticker.get('timestamp', 0) / 1000).isoformat() if ticker.get('timestamp') else None,
                    "market_type": market_type
                },
                "metadata": {
                    "source": "CEX",
                    "exchange": exchange,
                    "market_type": market_type,
                    "fetched_at": datetime.now().isoformat()
                }
            }

        except ccxt.BaseError as e:
            return {"success": False, "error": f"Failed to fetch price from {exchange}: {str(e)}"}
        finally:
            if hasattr(exchange_instance, 'close'):
                await exchange_instance.close()

    except Exception as e:
        logger.error(f"Error in get_cex_price: {e}")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}


@mcp.tool(title="Get DEX Token Price")
async def get_dex_token_price(chain_index: str, token_address: str) -> Dict[str, Any]:
    """
    Fetches real-time price of a DEX token from the OKX DEX API.

    Provides current price, 24h change, and basic token information for tokens
    traded on decentralized exchanges across multiple blockchain networks.

    SUPPORTED BLOCKCHAINS:
    - Ethereum (chain_index: '1')
    - BSC/BNB Chain (chain_index: '56')
    - Polygon (chain_index: '137')
    - Avalanche (chain_index: '43114')
    - Arbitrum (chain_index: '42161')
    - Optimism (chain_index: '10')
    - Fantom (chain_index: '250')

    POPULAR TOKEN EXAMPLES:
    Ethereum (chain_index: '1'):
    - USDC: '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
    - USDT: '0xdac17f958d2ee523a2206206994597c13d831ec7'
    - WETH: '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'
    - UNI: '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984'

    BSC (chain_index: '56'):
    - WBNB: '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c'
    - BUSD: '0xe9e7cea3dedca5984780bafc599bd69add087d56'
    - CAKE: '0x0e09fabb73bd3ade0a17ecc321fd13a19e81ce82'

    Args:
        chain_index: Blockchain identifier (string) - e.g., '1' for Ethereum, '56' for BSC
        token_address: Token contract address (string) - e.g., '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'

    Returns:
        Dictionary with current token price and market information.

    Example Response:
    {
        "success": true,
        "data": {
            "chainIndex": "1",
            "tokenContractAddress": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "price": "1.0001",
            "priceChange24h": "0.0001",
            "symbol": "USDC",
            "tokenName": "USD Coin"
        }
    }
    """
    try:
        # Validate input parameters
        is_valid, error_msg = validate_dex_parameters(chain_index, token_address)
        if not is_valid:
            return {"success": False, "error": error_msg}

        settings = get_global_settings()
        async with OKXDEXClient(settings) as client:
            price_data = await client.get_token_price(chain_index, token_address)
            if price_data:
                return {
                    "success": True,
                    "data": price_data,
                    "metadata": {
                        "source": "OKX DEX API",
                        "chain_index": chain_index,
                        "token_address": token_address,
                        "fetched_at": datetime.now().isoformat()
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Could not fetch token price. Check chain_index and token_address are valid."
                }
    except Exception as e:
        logger.error(f"Error in get_dex_token_price: {e}")
        return {"success": False, "error": f"Unexpected error: {str(e)}"}


def main(env_vars: Optional[Dict[str, str]] = None, transport_mode: str = "stdio"):
    """Main entry point for the MCP server"""
    # Initialize global settings
    set_global_settings(env_vars)

    if transport_mode == "stdio":
        # Start the MCP server in stdio mode
        mcp.run()
    else:
        # For HTTP/SSE mode, use the dual transport server
        import asyncio
        from dual_transport_server import run_dual_server
        asyncio.run(run_dual_server(mode=transport_mode, env_vars=env_vars))


if __name__ == "__main__":
    import sys

    # Check if running in HTTP mode
    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        main(transport_mode="http")
    else:
        main()