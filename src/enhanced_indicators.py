"""
Enhanced Technical Indicators System

This module provides an enhanced system for calculating technical indicators with
flexible multi-parameter support. It supports multiple instances of the same
indicator with different parameters and proper result labeling.

Example usage:
    indicators_config = {
        'ema': [{'period': 12}, {'period': 26}, {'period': 120}],
        'macd': [{'fast': 12, 'slow': 26, 'signal': 9}, {'fast': 5, 'slow': 35, 'signal': 5}],
        'rsi': [{'period': 14}, {'period': 21}]
    }

    result = enhanced_ta.calculate_indicators(df, indicators_config)
    # Returns columns like: ema_12, ema_26, ema_120, macd_12_26_9, rsi_14, rsi_21
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple
import numpy as np
import pandas as pd
import talib
from dataclasses import dataclass

try:
    from .talib_registry import TALibRegistry, IndicatorDefinition, DataType
except ImportError:
    from talib_registry import TALibRegistry, IndicatorDefinition, DataType

logger = logging.getLogger(__name__)


@dataclass
class IndicatorResult:
    """Result of indicator calculation"""
    name: str
    parameters: Dict[str, Any]
    columns: Dict[str, np.ndarray]
    label_suffix: str


class EnhancedTechnicalAnalysis:
    """Enhanced technical analysis with flexible multi-parameter support"""

    def __init__(self):
        self.registry = TALibRegistry()

    def calculate_indicators(self, df: pd.DataFrame, indicators_config: Dict[str, List[Dict[str, Any]]]) -> pd.DataFrame:
        """
        Calculate multiple indicators with flexible parameters

        Args:
            df: DataFrame with OHLCV data
            indicators_config: Dict with indicator names and parameter lists
                Example: {'ema': [{'period': 12}, {'period': 26}], 'macd': [{'fast': 12, 'slow': 26, 'signal': 9}]}

        Returns:
            DataFrame with original data plus calculated indicators
        """
        if df is None or df.empty:
            return df

        result_df = df.copy()

        for indicator_name, param_list in indicators_config.items():
            indicator_def = self.registry.get_indicator(indicator_name.lower())
            if not indicator_def:
                logger.warning(f"Unknown indicator: {indicator_name}")
                continue

            for params in param_list:
                try:
                    indicator_result = self._calculate_single_indicator(df, indicator_def, params)
                    if indicator_result:
                        # Add columns with proper labeling
                        for col_name, values in indicator_result.columns.items():
                            full_col_name = f"{indicator_name.lower()}_{indicator_result.label_suffix}_{col_name}"
                            if len(indicator_result.columns) == 1:
                                # Single output, use simpler naming
                                full_col_name = f"{indicator_name.lower()}_{indicator_result.label_suffix}"
                            result_df[full_col_name] = values

                except Exception as e:
                    logger.error(f"Error calculating {indicator_name} with params {params}: {e}")

        return result_df

    def _calculate_single_indicator(self, df: pd.DataFrame, indicator_def: IndicatorDefinition, params: Dict[str, Any]) -> Optional[IndicatorResult]:
        """Calculate a single indicator instance"""
        try:
            # Validate and prepare parameters
            validated_params = self._validate_parameters(indicator_def, params)

            # Prepare input data
            input_arrays = self._prepare_input_data(df, indicator_def.input_data)
            if not input_arrays:
                return None

            # Check minimum periods
            min_length = max(len(arr) for arr in input_arrays.values())
            if min_length < indicator_def.min_periods:
                logger.warning(f"Insufficient data for {indicator_def.name}: need {indicator_def.min_periods}, got {min_length}")
                return None

            # Calculate indicator
            result_arrays = self._call_talib_function(indicator_def.name, input_arrays, validated_params)
            if not result_arrays:
                return None

            # Create result columns
            result_columns = {}
            if len(indicator_def.output_names) == len(result_arrays):
                for i, output_name in enumerate(indicator_def.output_names):
                    result_columns[output_name] = result_arrays[i]
            else:
                # Fallback naming
                for i, arr in enumerate(result_arrays):
                    result_columns[f"output_{i}"] = arr

            # Generate label suffix
            label_suffix = self._generate_label_suffix(validated_params)

            return IndicatorResult(
                name=indicator_def.name,
                parameters=validated_params,
                columns=result_columns,
                label_suffix=label_suffix
            )

        except Exception as e:
            logger.error(f"Error in _calculate_single_indicator: {e}")
            return None

    def _validate_parameters(self, indicator_def: IndicatorDefinition, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and set default parameters"""
        validated = {}

        # Set defaults first
        for param_schema in indicator_def.parameters:
            validated[param_schema.name] = param_schema.default

        # Override with provided parameters
        for param_name, param_value in params.items():
            # Find parameter schema
            param_schema = None
            for schema in indicator_def.parameters:
                if schema.name == param_name:
                    param_schema = schema
                    break

            if not param_schema:
                logger.warning(f"Unknown parameter {param_name} for {indicator_def.name}")
                continue

            # Validate type
            if not isinstance(param_value, param_schema.type):
                try:
                    param_value = param_schema.type(param_value)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid type for {param_name}: expected {param_schema.type}, got {type(param_value)}")
                    continue

            # Validate range
            if param_schema.min_value is not None and param_value < param_schema.min_value:
                logger.warning(f"Parameter {param_name} below minimum: {param_value} < {param_schema.min_value}")
                param_value = param_schema.min_value

            if param_schema.max_value is not None and param_value > param_schema.max_value:
                logger.warning(f"Parameter {param_name} above maximum: {param_value} > {param_schema.max_value}")
                param_value = param_schema.max_value

            validated[param_name] = param_value

        return validated

    def _prepare_input_data(self, df: pd.DataFrame, required_data: List[DataType]) -> Optional[Dict[str, np.ndarray]]:
        """Prepare input data arrays for TA-Lib functions"""
        input_arrays = {}

        for data_type in required_data:
            column_name = data_type.value
            if column_name not in df.columns:
                logger.error(f"Required column {column_name} not found in DataFrame")
                return None

            # Convert to numpy array and handle NaN values
            arr = df[column_name].values.astype(np.float64)
            input_arrays[column_name] = arr

        return input_arrays

    def _call_talib_function(self, function_name: str, input_arrays: Dict[str, np.ndarray], params: Dict[str, Any]) -> Optional[List[np.ndarray]]:
        """Call the appropriate TA-Lib function"""
        try:
            # Get the TA-Lib function
            talib_func = getattr(talib, function_name.upper())

            # Prepare arguments based on function signature
            args = []

            # Add input arrays in the correct order
            if function_name.upper() in ['SMA', 'EMA', 'WMA', 'DEMA', 'TEMA', 'TRIMA', 'KAMA', 'T3', 'RSI', 'CMO']:
                args.append(input_arrays['close'])
            elif function_name.upper() in ['MACD', 'MACDEXT', 'MACDFIX', 'APO']:
                args.append(input_arrays['close'])
            elif function_name.upper() in ['STOCH', 'STOCHF', 'STOCHRSI']:
                if 'high' in input_arrays and 'low' in input_arrays:
                    args.extend([input_arrays['high'], input_arrays['low'], input_arrays['close']])
                else:
                    args.append(input_arrays['close'])
            elif function_name.upper() in ['ADX', 'ADXR', 'DX', 'CCI']:
                args.extend([input_arrays['high'], input_arrays['low'], input_arrays['close']])
            elif function_name.upper() in ['AROON', 'AROONOSC']:
                args.extend([input_arrays['high'], input_arrays['low']])
            elif function_name.upper() == 'BOP':
                args.extend([input_arrays['open'], input_arrays['high'], input_arrays['low'], input_arrays['close']])
            elif function_name.upper() in ['AD', 'ADOSC']:
                args.extend([input_arrays['high'], input_arrays['low'], input_arrays['close'], input_arrays['volume']])
            elif function_name.upper() == 'OBV':
                args.extend([input_arrays['close'], input_arrays['volume']])
            elif function_name.upper() in ['ATR', 'NATR', 'TRANGE']:
                args.extend([input_arrays['high'], input_arrays['low'], input_arrays['close']])
            elif function_name.upper() == 'AVGPRICE':
                args.extend([input_arrays['open'], input_arrays['high'], input_arrays['low'], input_arrays['close']])
            elif function_name.upper() in ['MEDPRICE', 'MIDPRICE']:
                args.extend([input_arrays['high'], input_arrays['low']])
            elif function_name.upper() in ['TYPPRICE', 'WCLPRICE']:
                args.extend([input_arrays['high'], input_arrays['low'], input_arrays['close']])
            elif function_name.upper() in ['SAR', 'SAREXT']:
                args.extend([input_arrays['high'], input_arrays['low']])
            elif function_name.upper() == 'BBANDS':
                args.append(input_arrays['close'])
            elif function_name.upper() in ['MIDPOINT', 'MA']:
                args.append(input_arrays['close'])
            else:
                # Default: use close price
                args.append(input_arrays['close'])

            # Add parameters in the correct order for each function
            if function_name.upper() == 'BBANDS':
                # BBANDS expects: close, timeperiod, nbdevup, nbdevdn, matype
                for param_name in ['timeperiod', 'nbdevup', 'nbdevdn', 'matype']:
                    if param_name in params:
                        args.append(params[param_name])
            elif function_name.upper() == 'MACD':
                # MACD expects: close, fastperiod, slowperiod, signalperiod
                for param_name in ['fastperiod', 'slowperiod', 'signalperiod']:
                    if param_name in params:
                        args.append(params[param_name])
            elif function_name.upper() == 'STOCH':
                # STOCH expects: high, low, close, fastkperiod, slowkperiod, slowkmatype, slowdperiod, slowdmatype
                for param_name in ['fastkperiod', 'slowkperiod', 'slowkmatype', 'slowdperiod', 'slowdmatype']:
                    if param_name in params:
                        args.append(params[param_name])
            else:
                # For other functions, add parameters in sorted order
                for param_name, param_value in sorted(params.items()):
                    args.append(param_value)

            # Call the function
            result = talib_func(*args)

            # Ensure result is always a tuple of arrays
            if isinstance(result, np.ndarray):
                return [result]
            elif isinstance(result, tuple):
                return list(result)
            else:
                return [np.array(result)]

        except Exception as e:
            logger.error(f"Error calling TA-Lib function {function_name}: {e}")
            return None

    def _generate_label_suffix(self, params: Dict[str, Any]) -> str:
        """Generate a label suffix from parameters"""
        if not params:
            return ""

        # Sort parameters for consistent naming
        sorted_params = sorted(params.items())

        # Create suffix from parameter values
        suffix_parts = []
        for param_name, param_value in sorted_params:
            if isinstance(param_value, float):
                # Format floats to avoid long decimal representations
                if param_value == int(param_value):
                    suffix_parts.append(str(int(param_value)))
                else:
                    suffix_parts.append(f"{param_value:.2f}".rstrip('0').rstrip('.'))
            else:
                suffix_parts.append(str(param_value))

        return "_".join(suffix_parts)

    def get_available_indicators(self) -> Dict[str, IndicatorDefinition]:
        """Get all available indicators"""
        return self.registry.get_all_indicators()

    def get_indicator_info(self, indicator_name: str) -> Optional[IndicatorDefinition]:
        """Get information about a specific indicator"""
        return self.registry.get_indicator(indicator_name)
