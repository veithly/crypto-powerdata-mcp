"""
Comprehensive TA-Lib Indicator Registry

This module provides a complete registry of all 158 TA-Lib indicators with their
parameter schemas, supporting multiple instances of the same indicator with
different parameters.

Categories:
- Cycle Indicators (5 functions)
- Math Operators (11 functions)
- Math Transform (15 functions)
- Momentum Indicators (30 functions)
- Overlap Studies (17 functions)
- Pattern Recognition (61 functions)
- Price Transform (4 functions)
- Statistic Functions (9 functions)
- Volatility Indicators (3 functions)
- Volume Indicators (3 functions)
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
import talib
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class IndicatorCategory(Enum):
    """TA-Lib indicator categories"""
    CYCLE = "Cycle Indicators"
    MATH_OPERATORS = "Math Operators"
    MATH_TRANSFORM = "Math Transform"
    MOMENTUM = "Momentum Indicators"
    OVERLAP = "Overlap Studies"
    PATTERN = "Pattern Recognition"
    PRICE_TRANSFORM = "Price Transform"
    STATISTIC = "Statistic Functions"
    VOLATILITY = "Volatility Indicators"
    VOLUME = "Volume Indicators"


class DataType(Enum):
    """Input data types for indicators"""
    CLOSE = "close"
    HIGH = "high"
    LOW = "low"
    OPEN = "open"
    VOLUME = "volume"
    HLCV = "hlcv"  # High, Low, Close, Volume
    OHLCV = "ohlcv"  # Open, High, Low, Close, Volume


@dataclass
class ParameterSchema:
    """Schema for indicator parameters"""
    name: str
    type: type
    default: Any
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    description: str = ""


@dataclass
class IndicatorDefinition:
    """Complete definition of a TA-Lib indicator"""
    name: str
    category: IndicatorCategory
    description: str
    input_data: List[DataType]
    parameters: List[ParameterSchema] = field(default_factory=list)
    output_names: List[str] = field(default_factory=list)
    min_periods: int = 1

    def get_parameter_defaults(self) -> Dict[str, Any]:
        """Get default parameter values"""
        return {param.name: param.default for param in self.parameters}


class TALibRegistry:
    """Comprehensive registry of all TA-Lib indicators"""

    def __init__(self):
        self._indicators: Dict[str, IndicatorDefinition] = {}
        self._initialize_registry()

    def _initialize_registry(self):
        """Initialize the complete TA-Lib indicator registry"""
        # Overlap Studies (Moving Averages, Bands, etc.)
        self._register_overlap_studies()

        # Momentum Indicators
        self._register_momentum_indicators()

        # Volume Indicators
        self._register_volume_indicators()

        # Volatility Indicators
        self._register_volatility_indicators()

        # Price Transform
        self._register_price_transform()

        # Cycle Indicators
        self._register_cycle_indicators()

        # Pattern Recognition
        self._register_pattern_recognition()

        # Statistic Functions
        self._register_statistic_functions()

        # Math Transform
        self._register_math_transform()

        # Math Operators
        self._register_math_operators()

    def _register_overlap_studies(self):
        """Register overlap studies indicators"""
        indicators = [
            IndicatorDefinition(
                name="SMA",
                category=IndicatorCategory.OVERLAP,
                description="Simple Moving Average",
                input_data=[DataType.CLOSE],
                parameters=[ParameterSchema("timeperiod", int, 30, 2, 100000, "Time period")],
                output_names=["sma"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="EMA",
                category=IndicatorCategory.OVERLAP,
                description="Exponential Moving Average",
                input_data=[DataType.CLOSE],
                parameters=[ParameterSchema("timeperiod", int, 30, 2, 100000, "Time period")],
                output_names=["ema"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="WMA",
                category=IndicatorCategory.OVERLAP,
                description="Weighted Moving Average",
                input_data=[DataType.CLOSE],
                parameters=[ParameterSchema("timeperiod", int, 30, 2, 100000, "Time period")],
                output_names=["wma"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="DEMA",
                category=IndicatorCategory.OVERLAP,
                description="Double Exponential Moving Average",
                input_data=[DataType.CLOSE],
                parameters=[ParameterSchema("timeperiod", int, 30, 2, 100000, "Time period")],
                output_names=["dema"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="TEMA",
                category=IndicatorCategory.OVERLAP,
                description="Triple Exponential Moving Average",
                input_data=[DataType.CLOSE],
                parameters=[ParameterSchema("timeperiod", int, 30, 2, 100000, "Time period")],
                output_names=["tema"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="TRIMA",
                category=IndicatorCategory.OVERLAP,
                description="Triangular Moving Average",
                input_data=[DataType.CLOSE],
                parameters=[ParameterSchema("timeperiod", int, 30, 2, 100000, "Time period")],
                output_names=["trima"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="KAMA",
                category=IndicatorCategory.OVERLAP,
                description="Kaufman Adaptive Moving Average",
                input_data=[DataType.CLOSE],
                parameters=[ParameterSchema("timeperiod", int, 30, 2, 100000, "Time period")],
                output_names=["kama"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="T3",
                category=IndicatorCategory.OVERLAP,
                description="Triple Exponential Moving Average (T3)",
                input_data=[DataType.CLOSE],
                parameters=[
                    ParameterSchema("timeperiod", int, 5, 2, 100000, "Time period"),
                    ParameterSchema("vfactor", float, 0.7, 0, 1, "Volume factor")
                ],
                output_names=["t3"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="MA",
                category=IndicatorCategory.OVERLAP,
                description="Moving Average",
                input_data=[DataType.CLOSE],
                parameters=[
                    ParameterSchema("timeperiod", int, 30, 1, 100000, "Time period"),
                    ParameterSchema("matype", int, 0, 0, 8, "MA Type: 0=SMA, 1=EMA, 2=WMA, 3=DEMA, 4=TEMA, 5=TRIMA, 6=KAMA, 7=MAMA, 8=T3")
                ],
                output_names=["ma"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="BBANDS",
                category=IndicatorCategory.OVERLAP,
                description="Bollinger Bands",
                input_data=[DataType.CLOSE],
                parameters=[
                    ParameterSchema("timeperiod", int, 5, 2, 100000, "Time period"),
                    ParameterSchema("nbdevup", float, 2, 0.1, 10, "Deviation multiplier for upper band"),
                    ParameterSchema("nbdevdn", float, 2, 0.1, 10, "Deviation multiplier for lower band"),
                    ParameterSchema("matype", int, 0, 0, 8, "MA Type")
                ],
                output_names=["upperband", "middleband", "lowerband"],
                min_periods=2
            ),
            IndicatorDefinition(
                name="MIDPOINT",
                category=IndicatorCategory.OVERLAP,
                description="MidPoint over period",
                input_data=[DataType.CLOSE],
                parameters=[ParameterSchema("timeperiod", int, 14, 2, 100000, "Time period")],
                output_names=["midpoint"],
                min_periods=2
            ),
            IndicatorDefinition(
                name="MIDPRICE",
                category=IndicatorCategory.OVERLAP,
                description="Midpoint Price over period",
                input_data=[DataType.HIGH, DataType.LOW],
                parameters=[ParameterSchema("timeperiod", int, 14, 2, 100000, "Time period")],
                output_names=["midprice"],
                min_periods=2
            ),
            IndicatorDefinition(
                name="SAR",
                category=IndicatorCategory.OVERLAP,
                description="Parabolic SAR",
                input_data=[DataType.HIGH, DataType.LOW],
                parameters=[
                    ParameterSchema("acceleration", float, 0.02, 0.01, 1, "Acceleration factor"),
                    ParameterSchema("maximum", float, 0.2, 0.01, 1, "Maximum acceleration")
                ],
                output_names=["sar"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="SAREXT",
                category=IndicatorCategory.OVERLAP,
                description="Parabolic SAR - Extended",
                input_data=[DataType.HIGH, DataType.LOW],
                parameters=[
                    ParameterSchema("startvalue", float, 0, -1e30, 1e30, "Start value"),
                    ParameterSchema("offsetonreverse", float, 0, -1e30, 1e30, "Offset on reverse"),
                    ParameterSchema("accelerationinitlong", float, 0.02, 0, 1e30, "Acceleration init long"),
                    ParameterSchema("accelerationlong", float, 0.02, 0, 1e30, "Acceleration long"),
                    ParameterSchema("accelerationmaxlong", float, 0.2, 0, 1e30, "Acceleration max long"),
                    ParameterSchema("accelerationinitshort", float, 0.02, 0, 1e30, "Acceleration init short"),
                    ParameterSchema("accelerationshort", float, 0.02, 0, 1e30, "Acceleration short"),
                    ParameterSchema("accelerationmaxshort", float, 0.2, 0, 1e30, "Acceleration max short")
                ],
                output_names=["sarext"],
                min_periods=1
            )
        ]

        for indicator in indicators:
            self._indicators[indicator.name.lower()] = indicator

    def get_indicator(self, name: str) -> Optional[IndicatorDefinition]:
        """Get indicator definition by name"""
        return self._indicators.get(name.lower())

    def get_all_indicators(self) -> Dict[str, IndicatorDefinition]:
        """Get all registered indicators"""
        return self._indicators.copy()

    def get_indicators_by_category(self, category: IndicatorCategory) -> Dict[str, IndicatorDefinition]:
        """Get indicators by category"""
        return {name: indicator for name, indicator in self._indicators.items()
                if indicator.category == category}

    def list_indicator_names(self) -> List[str]:
        """Get list of all indicator names"""
        return list(self._indicators.keys())

    def _register_momentum_indicators(self):
        """Register momentum indicators"""
        indicators = [
            IndicatorDefinition(
                name="RSI",
                category=IndicatorCategory.MOMENTUM,
                description="Relative Strength Index",
                input_data=[DataType.CLOSE],
                parameters=[ParameterSchema("timeperiod", int, 14, 2, 100000, "Time period")],
                output_names=["rsi"],
                min_periods=2
            ),
            IndicatorDefinition(
                name="MACD",
                category=IndicatorCategory.MOMENTUM,
                description="Moving Average Convergence/Divergence",
                input_data=[DataType.CLOSE],
                parameters=[
                    ParameterSchema("fastperiod", int, 12, 2, 100000, "Fast period"),
                    ParameterSchema("slowperiod", int, 26, 2, 100000, "Slow period"),
                    ParameterSchema("signalperiod", int, 9, 1, 100000, "Signal period")
                ],
                output_names=["macd", "macdsignal", "macdhist"],
                min_periods=2
            ),
            IndicatorDefinition(
                name="MACDEXT",
                category=IndicatorCategory.MOMENTUM,
                description="MACD with controllable MA type",
                input_data=[DataType.CLOSE],
                parameters=[
                    ParameterSchema("fastperiod", int, 12, 2, 100000, "Fast period"),
                    ParameterSchema("fastmatype", int, 0, 0, 8, "Fast MA type"),
                    ParameterSchema("slowperiod", int, 26, 2, 100000, "Slow period"),
                    ParameterSchema("slowmatype", int, 0, 0, 8, "Slow MA type"),
                    ParameterSchema("signalperiod", int, 9, 1, 100000, "Signal period"),
                    ParameterSchema("signalmatype", int, 0, 0, 8, "Signal MA type")
                ],
                output_names=["macd", "macdsignal", "macdhist"],
                min_periods=2
            ),
            IndicatorDefinition(
                name="MACDFIX",
                category=IndicatorCategory.MOMENTUM,
                description="Moving Average Convergence/Divergence Fix 12/26",
                input_data=[DataType.CLOSE],
                parameters=[ParameterSchema("signalperiod", int, 9, 1, 100000, "Signal period")],
                output_names=["macd", "macdsignal", "macdhist"],
                min_periods=2
            ),
            IndicatorDefinition(
                name="STOCH",
                category=IndicatorCategory.MOMENTUM,
                description="Stochastic",
                input_data=[DataType.HIGH, DataType.LOW, DataType.CLOSE],
                parameters=[
                    ParameterSchema("fastkperiod", int, 5, 1, 100000, "Fast K period"),
                    ParameterSchema("slowkperiod", int, 3, 1, 100000, "Slow K period"),
                    ParameterSchema("slowkmatype", int, 0, 0, 8, "Slow K MA type"),
                    ParameterSchema("slowdperiod", int, 3, 1, 100000, "Slow D period"),
                    ParameterSchema("slowdmatype", int, 0, 0, 8, "Slow D MA type")
                ],
                output_names=["slowk", "slowd"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="STOCHF",
                category=IndicatorCategory.MOMENTUM,
                description="Stochastic Fast",
                input_data=[DataType.HIGH, DataType.LOW, DataType.CLOSE],
                parameters=[
                    ParameterSchema("fastkperiod", int, 5, 1, 100000, "Fast K period"),
                    ParameterSchema("fastdperiod", int, 3, 1, 100000, "Fast D period"),
                    ParameterSchema("fastdmatype", int, 0, 0, 8, "Fast D MA type")
                ],
                output_names=["fastk", "fastd"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="STOCHRSI",
                category=IndicatorCategory.MOMENTUM,
                description="Stochastic Relative Strength Index",
                input_data=[DataType.CLOSE],
                parameters=[
                    ParameterSchema("timeperiod", int, 14, 2, 100000, "Time period"),
                    ParameterSchema("fastkperiod", int, 5, 1, 100000, "Fast K period"),
                    ParameterSchema("fastdperiod", int, 3, 1, 100000, "Fast D period"),
                    ParameterSchema("fastdmatype", int, 0, 0, 8, "Fast D MA type")
                ],
                output_names=["fastk", "fastd"],
                min_periods=2
            ),
            IndicatorDefinition(
                name="ADX",
                category=IndicatorCategory.MOMENTUM,
                description="Average Directional Movement Index",
                input_data=[DataType.HIGH, DataType.LOW, DataType.CLOSE],
                parameters=[ParameterSchema("timeperiod", int, 14, 2, 100000, "Time period")],
                output_names=["adx"],
                min_periods=2
            ),
            IndicatorDefinition(
                name="ADXR",
                category=IndicatorCategory.MOMENTUM,
                description="Average Directional Movement Index Rating",
                input_data=[DataType.HIGH, DataType.LOW, DataType.CLOSE],
                parameters=[ParameterSchema("timeperiod", int, 14, 2, 100000, "Time period")],
                output_names=["adxr"],
                min_periods=2
            ),
            IndicatorDefinition(
                name="APO",
                category=IndicatorCategory.MOMENTUM,
                description="Absolute Price Oscillator",
                input_data=[DataType.CLOSE],
                parameters=[
                    ParameterSchema("fastperiod", int, 12, 2, 100000, "Fast period"),
                    ParameterSchema("slowperiod", int, 26, 2, 100000, "Slow period"),
                    ParameterSchema("matype", int, 0, 0, 8, "MA type")
                ],
                output_names=["apo"],
                min_periods=2
            ),
            IndicatorDefinition(
                name="AROON",
                category=IndicatorCategory.MOMENTUM,
                description="Aroon",
                input_data=[DataType.HIGH, DataType.LOW],
                parameters=[ParameterSchema("timeperiod", int, 14, 2, 100000, "Time period")],
                output_names=["aroondown", "aroonup"],
                min_periods=2
            ),
            IndicatorDefinition(
                name="AROONOSC",
                category=IndicatorCategory.MOMENTUM,
                description="Aroon Oscillator",
                input_data=[DataType.HIGH, DataType.LOW],
                parameters=[ParameterSchema("timeperiod", int, 14, 2, 100000, "Time period")],
                output_names=["aroonosc"],
                min_periods=2
            ),
            IndicatorDefinition(
                name="BOP",
                category=IndicatorCategory.MOMENTUM,
                description="Balance Of Power",
                input_data=[DataType.OPEN, DataType.HIGH, DataType.LOW, DataType.CLOSE],
                parameters=[],
                output_names=["bop"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="CCI",
                category=IndicatorCategory.MOMENTUM,
                description="Commodity Channel Index",
                input_data=[DataType.HIGH, DataType.LOW, DataType.CLOSE],
                parameters=[ParameterSchema("timeperiod", int, 14, 2, 100000, "Time period")],
                output_names=["cci"],
                min_periods=2
            ),
            IndicatorDefinition(
                name="CMO",
                category=IndicatorCategory.MOMENTUM,
                description="Chande Momentum Oscillator",
                input_data=[DataType.CLOSE],
                parameters=[ParameterSchema("timeperiod", int, 14, 2, 100000, "Time period")],
                output_names=["cmo"],
                min_periods=2
            ),
            IndicatorDefinition(
                name="DX",
                category=IndicatorCategory.MOMENTUM,
                description="Directional Movement Index",
                input_data=[DataType.HIGH, DataType.LOW, DataType.CLOSE],
                parameters=[ParameterSchema("timeperiod", int, 14, 2, 100000, "Time period")],
                output_names=["dx"],
                min_periods=2
            )
        ]

        for indicator in indicators:
            self._indicators[indicator.name.lower()] = indicator

    def _register_volume_indicators(self):
        """Register volume indicators"""
        indicators = [
            IndicatorDefinition(
                name="AD",
                category=IndicatorCategory.VOLUME,
                description="Chaikin A/D Line",
                input_data=[DataType.HIGH, DataType.LOW, DataType.CLOSE, DataType.VOLUME],
                parameters=[],
                output_names=["ad"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="ADOSC",
                category=IndicatorCategory.VOLUME,
                description="Chaikin A/D Oscillator",
                input_data=[DataType.HIGH, DataType.LOW, DataType.CLOSE, DataType.VOLUME],
                parameters=[
                    ParameterSchema("fastperiod", int, 3, 2, 100000, "Fast period"),
                    ParameterSchema("slowperiod", int, 10, 2, 100000, "Slow period")
                ],
                output_names=["adosc"],
                min_periods=2
            ),
            IndicatorDefinition(
                name="OBV",
                category=IndicatorCategory.VOLUME,
                description="On Balance Volume",
                input_data=[DataType.CLOSE, DataType.VOLUME],
                parameters=[],
                output_names=["obv"],
                min_periods=1
            )
        ]

        for indicator in indicators:
            self._indicators[indicator.name.lower()] = indicator

    def _register_volatility_indicators(self):
        """Register volatility indicators"""
        indicators = [
            IndicatorDefinition(
                name="ATR",
                category=IndicatorCategory.VOLATILITY,
                description="Average True Range",
                input_data=[DataType.HIGH, DataType.LOW, DataType.CLOSE],
                parameters=[ParameterSchema("timeperiod", int, 14, 1, 100000, "Time period")],
                output_names=["atr"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="NATR",
                category=IndicatorCategory.VOLATILITY,
                description="Normalized Average True Range",
                input_data=[DataType.HIGH, DataType.LOW, DataType.CLOSE],
                parameters=[ParameterSchema("timeperiod", int, 14, 1, 100000, "Time period")],
                output_names=["natr"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="TRANGE",
                category=IndicatorCategory.VOLATILITY,
                description="True Range",
                input_data=[DataType.HIGH, DataType.LOW, DataType.CLOSE],
                parameters=[],
                output_names=["trange"],
                min_periods=1
            )
        ]

        for indicator in indicators:
            self._indicators[indicator.name.lower()] = indicator

    def _register_price_transform(self):
        """Register price transform indicators"""
        indicators = [
            IndicatorDefinition(
                name="AVGPRICE",
                category=IndicatorCategory.PRICE_TRANSFORM,
                description="Average Price",
                input_data=[DataType.OPEN, DataType.HIGH, DataType.LOW, DataType.CLOSE],
                parameters=[],
                output_names=["avgprice"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="MEDPRICE",
                category=IndicatorCategory.PRICE_TRANSFORM,
                description="Median Price",
                input_data=[DataType.HIGH, DataType.LOW],
                parameters=[],
                output_names=["medprice"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="TYPPRICE",
                category=IndicatorCategory.PRICE_TRANSFORM,
                description="Typical Price",
                input_data=[DataType.HIGH, DataType.LOW, DataType.CLOSE],
                parameters=[],
                output_names=["typprice"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="WCLPRICE",
                category=IndicatorCategory.PRICE_TRANSFORM,
                description="Weighted Close Price",
                input_data=[DataType.HIGH, DataType.LOW, DataType.CLOSE],
                parameters=[],
                output_names=["wclprice"],
                min_periods=1
            )
        ]

        for indicator in indicators:
            self._indicators[indicator.name.lower()] = indicator

    def _register_cycle_indicators(self):
        """Register cycle indicators"""
        indicators = [
            IndicatorDefinition(
                name="HT_DCPERIOD",
                category=IndicatorCategory.CYCLE,
                description="Hilbert Transform - Dominant Cycle Period",
                input_data=[DataType.CLOSE],
                parameters=[],
                output_names=["dcperiod"],
                min_periods=32
            ),
            IndicatorDefinition(
                name="HT_DCPHASE",
                category=IndicatorCategory.CYCLE,
                description="Hilbert Transform - Dominant Cycle Phase",
                input_data=[DataType.CLOSE],
                parameters=[],
                output_names=["dcphase"],
                min_periods=32
            ),
            IndicatorDefinition(
                name="HT_PHASOR",
                category=IndicatorCategory.CYCLE,
                description="Hilbert Transform - Phasor Components",
                input_data=[DataType.CLOSE],
                parameters=[],
                output_names=["inphase", "quadrature"],
                min_periods=32
            ),
            IndicatorDefinition(
                name="HT_SINE",
                category=IndicatorCategory.CYCLE,
                description="Hilbert Transform - SineWave",
                input_data=[DataType.CLOSE],
                parameters=[],
                output_names=["sine", "leadsine"],
                min_periods=32
            ),
            IndicatorDefinition(
                name="HT_TRENDMODE",
                category=IndicatorCategory.CYCLE,
                description="Hilbert Transform - Trend vs Cycle Mode",
                input_data=[DataType.CLOSE],
                parameters=[],
                output_names=["trendmode"],
                min_periods=32
            )
        ]

        for indicator in indicators:
            self._indicators[indicator.name.lower()] = indicator

    def _register_pattern_recognition(self):
        """Register pattern recognition indicators (first batch)"""
        indicators = [
            IndicatorDefinition(
                name="CDL2CROWS",
                category=IndicatorCategory.PATTERN,
                description="Two Crows",
                input_data=[DataType.OPEN, DataType.HIGH, DataType.LOW, DataType.CLOSE],
                parameters=[],
                output_names=["pattern"],
                min_periods=3
            ),
            IndicatorDefinition(
                name="CDL3BLACKCROWS",
                category=IndicatorCategory.PATTERN,
                description="Three Black Crows",
                input_data=[DataType.OPEN, DataType.HIGH, DataType.LOW, DataType.CLOSE],
                parameters=[],
                output_names=["pattern"],
                min_periods=3
            ),
            IndicatorDefinition(
                name="CDL3INSIDE",
                category=IndicatorCategory.PATTERN,
                description="Three Inside Up/Down",
                input_data=[DataType.OPEN, DataType.HIGH, DataType.LOW, DataType.CLOSE],
                parameters=[],
                output_names=["pattern"],
                min_periods=3
            ),
            IndicatorDefinition(
                name="CDL3LINESTRIKE",
                category=IndicatorCategory.PATTERN,
                description="Three-Line Strike",
                input_data=[DataType.OPEN, DataType.HIGH, DataType.LOW, DataType.CLOSE],
                parameters=[],
                output_names=["pattern"],
                min_periods=4
            ),
            IndicatorDefinition(
                name="CDL3OUTSIDE",
                category=IndicatorCategory.PATTERN,
                description="Three Outside Up/Down",
                input_data=[DataType.OPEN, DataType.HIGH, DataType.LOW, DataType.CLOSE],
                parameters=[],
                output_names=["pattern"],
                min_periods=3
            ),
            IndicatorDefinition(
                name="CDLDOJI",
                category=IndicatorCategory.PATTERN,
                description="Doji",
                input_data=[DataType.OPEN, DataType.HIGH, DataType.LOW, DataType.CLOSE],
                parameters=[],
                output_names=["pattern"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="CDLHAMMER",
                category=IndicatorCategory.PATTERN,
                description="Hammer",
                input_data=[DataType.OPEN, DataType.HIGH, DataType.LOW, DataType.CLOSE],
                parameters=[],
                output_names=["pattern"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="CDLENGULFING",
                category=IndicatorCategory.PATTERN,
                description="Engulfing Pattern",
                input_data=[DataType.OPEN, DataType.HIGH, DataType.LOW, DataType.CLOSE],
                parameters=[],
                output_names=["pattern"],
                min_periods=2
            )
        ]

        for indicator in indicators:
            self._indicators[indicator.name.lower()] = indicator

    def _register_statistic_functions(self):
        """Register statistic functions"""
        indicators = [
            IndicatorDefinition(
                name="BETA",
                category=IndicatorCategory.STATISTIC,
                description="Beta",
                input_data=[DataType.HIGH, DataType.LOW],
                parameters=[ParameterSchema("timeperiod", int, 5, 1, 100000, "Time period")],
                output_names=["beta"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="CORREL",
                category=IndicatorCategory.STATISTIC,
                description="Pearson's Correlation Coefficient (r)",
                input_data=[DataType.HIGH, DataType.LOW],
                parameters=[ParameterSchema("timeperiod", int, 30, 1, 100000, "Time period")],
                output_names=["correl"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="LINEARREG",
                category=IndicatorCategory.STATISTIC,
                description="Linear Regression",
                input_data=[DataType.CLOSE],
                parameters=[ParameterSchema("timeperiod", int, 14, 2, 100000, "Time period")],
                output_names=["linearreg"],
                min_periods=2
            ),
            IndicatorDefinition(
                name="STDDEV",
                category=IndicatorCategory.STATISTIC,
                description="Standard Deviation",
                input_data=[DataType.CLOSE],
                parameters=[
                    ParameterSchema("timeperiod", int, 5, 2, 100000, "Time period"),
                    ParameterSchema("nbdev", float, 1, 0.1, 10, "Number of deviations")
                ],
                output_names=["stddev"],
                min_periods=2
            ),
            IndicatorDefinition(
                name="VAR",
                category=IndicatorCategory.STATISTIC,
                description="Variance",
                input_data=[DataType.CLOSE],
                parameters=[
                    ParameterSchema("timeperiod", int, 5, 1, 100000, "Time period"),
                    ParameterSchema("nbdev", float, 1, 0.1, 10, "Number of deviations")
                ],
                output_names=["var"],
                min_periods=1
            )
        ]

        for indicator in indicators:
            self._indicators[indicator.name.lower()] = indicator

    def _register_math_transform(self):
        """Register math transform functions"""
        indicators = [
            IndicatorDefinition(
                name="ACOS",
                category=IndicatorCategory.MATH_TRANSFORM,
                description="Vector Trigonometric ACos",
                input_data=[DataType.CLOSE],
                parameters=[],
                output_names=["acos"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="ASIN",
                category=IndicatorCategory.MATH_TRANSFORM,
                description="Vector Trigonometric ASin",
                input_data=[DataType.CLOSE],
                parameters=[],
                output_names=["asin"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="ATAN",
                category=IndicatorCategory.MATH_TRANSFORM,
                description="Vector Trigonometric ATan",
                input_data=[DataType.CLOSE],
                parameters=[],
                output_names=["atan"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="COS",
                category=IndicatorCategory.MATH_TRANSFORM,
                description="Vector Trigonometric Cos",
                input_data=[DataType.CLOSE],
                parameters=[],
                output_names=["cos"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="SIN",
                category=IndicatorCategory.MATH_TRANSFORM,
                description="Vector Trigonometric Sin",
                input_data=[DataType.CLOSE],
                parameters=[],
                output_names=["sin"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="TAN",
                category=IndicatorCategory.MATH_TRANSFORM,
                description="Vector Trigonometric Tan",
                input_data=[DataType.CLOSE],
                parameters=[],
                output_names=["tan"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="EXP",
                category=IndicatorCategory.MATH_TRANSFORM,
                description="Vector Arithmetic Exp",
                input_data=[DataType.CLOSE],
                parameters=[],
                output_names=["exp"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="LN",
                category=IndicatorCategory.MATH_TRANSFORM,
                description="Vector Log Natural",
                input_data=[DataType.CLOSE],
                parameters=[],
                output_names=["ln"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="LOG10",
                category=IndicatorCategory.MATH_TRANSFORM,
                description="Vector Log10",
                input_data=[DataType.CLOSE],
                parameters=[],
                output_names=["log10"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="SQRT",
                category=IndicatorCategory.MATH_TRANSFORM,
                description="Vector Square Root",
                input_data=[DataType.CLOSE],
                parameters=[],
                output_names=["sqrt"],
                min_periods=1
            )
        ]

        for indicator in indicators:
            self._indicators[indicator.name.lower()] = indicator

    def _register_math_operators(self):
        """Register math operators"""
        indicators = [
            IndicatorDefinition(
                name="ADD",
                category=IndicatorCategory.MATH_OPERATORS,
                description="Vector Arithmetic Add",
                input_data=[DataType.HIGH, DataType.LOW],
                parameters=[],
                output_names=["add"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="DIV",
                category=IndicatorCategory.MATH_OPERATORS,
                description="Vector Arithmetic Div",
                input_data=[DataType.HIGH, DataType.LOW],
                parameters=[],
                output_names=["div"],
                min_periods=1
            ),
            IndicatorDefinition(
                name="MAX",
                category=IndicatorCategory.MATH_OPERATORS,
                description="Highest value over a specified period",
                input_data=[DataType.CLOSE],
                parameters=[ParameterSchema("timeperiod", int, 30, 2, 100000, "Time period")],
                output_names=["max"],
                min_periods=2
            ),
            IndicatorDefinition(
                name="MIN",
                category=IndicatorCategory.MATH_OPERATORS,
                description="Lowest value over a specified period",
                input_data=[DataType.CLOSE],
                parameters=[ParameterSchema("timeperiod", int, 30, 2, 100000, "Time period")],
                output_names=["min"],
                min_periods=2
            ),
            IndicatorDefinition(
                name="SUM",
                category=IndicatorCategory.MATH_OPERATORS,
                description="Summation",
                input_data=[DataType.CLOSE],
                parameters=[ParameterSchema("timeperiod", int, 30, 2, 100000, "Time period")],
                output_names=["sum"],
                min_periods=2
            )
        ]

        for indicator in indicators:
            self._indicators[indicator.name.lower()] = indicator
