# API Documentation

Complete API reference for the Crypto PowerData MCP Service with enhanced indicators and dual transport support.

## Overview

The service provides 6 main tools with comprehensive TA-Lib indicator support (158 indicators) and dual transport protocols (stdio + HTTP/SSE).

## Tools Reference

### 🆕 `get_enhanced_dex_data_with_indicators`

**Description**: Fetches DEX candlestick data with enhanced flexible technical indicators supporting multiple instances of the same indicator.

**Parameters**:
- `chain_index` (string, required): Blockchain chain index (e.g., "1" for Ethereum)
- `token_address` (string, required): Token contract address
- `timeframe` (string, optional): Candlestick timeframe (default: "1h")
  - Supported: "1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"
- `limit` (integer, optional): Number of candlesticks (default: 100, max: 300)
- `indicators_config` (string, required): JSON string with flexible indicator configuration

**Indicators Config Format**:
```json
{
  "ema": [
    {"timeperiod": 12},
    {"timeperiod": 26},
    {"timeperiod": 120}
  ],
  "macd": [
    {"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}
  ],
  "rsi": [
    {"timeperiod": 14},
    {"timeperiod": 21}
  ],
  "bbands": [
    {"timeperiod": 20, "nbdevup": 2, "nbdevdn": 2}
  ]
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "candles": [
      {
        "timestamp": "2024-01-01T00:00:00",
        "open": 50000.0,
        "high": 50500.0,
        "low": 49500.0,
        "close": 50200.0,
        "volume": 1000.0,
        "ema_12": 50150.0,
        "ema_26": 50100.0,
        "ema_120": 50000.0,
        "macd_12_26_9_macd": 25.5,
        "macd_12_26_9_macdsignal": 20.0,
        "macd_12_26_9_macdhist": 5.5,
        "rsi_14": 65.5,
        "rsi_21": 62.3
      }
    ],
    "metadata": {
      "chain_index": "1",
      "token_address": "0x...",
      "timeframe": "1h",
      "indicators_applied": ["ema", "macd", "rsi"],
      "total_candles": 100,
      "columns": ["timestamp", "open", "high", "low", "close", "volume", "ema_12", "ema_26", "ema_120", "macd_12_26_9_macd", "macd_12_26_9_macdsignal", "macd_12_26_9_macdhist", "rsi_14", "rsi_21"]
    }
  }
}
```

### 🆕 `get_available_indicators`

**Description**: Returns comprehensive information about all 158 available TA-Lib indicators.

**Parameters**: None

**Response**:
```json
{
  "success": true,
  "data": {
    "indicators": {
      "sma": {
        "category": "Overlap Studies",
        "description": "Simple Moving Average",
        "input_data": ["close"],
        "parameters": [
          {
            "name": "timeperiod",
            "type": "int",
            "default": 30,
            "min_value": 2,
            "max_value": 100000,
            "description": "Time period"
          }
        ],
        "output_names": ["sma"],
        "min_periods": 1
      }
    },
    "total_indicators": 158,
    "categories": [
      "Cycle Indicators",
      "Math Operators", 
      "Math Transform",
      "Momentum Indicators",
      "Overlap Studies",
      "Pattern Recognition",
      "Price Transform",
      "Statistic Functions",
      "Volatility Indicators",
      "Volume Indicators"
    ],
    "usage_example": {
      "ema": [{"timeperiod": 12}, {"timeperiod": 26}, {"timeperiod": 120}],
      "macd": [{"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}],
      "rsi": [{"timeperiod": 14}, {"timeperiod": 21}],
      "bbands": [{"timeperiod": 20, "nbdevup": 2, "nbdevdn": 2}]
    }
  }
}
```

### 🔄 `get_cex_data_with_indicators` (Enhanced)

**Description**: Fetches CEX candlestick data with enhanced indicator support.

**Parameters**:
- `exchange` (string, required): Exchange ID (e.g., "binance", "coinbase", "kraken")
- `symbol` (string, required): Trading pair (e.g., "BTC/USDT", "ETH/USD")
- `timeframe` (string, optional): Time interval (default: "1h")
- `limit` (integer, optional): Number of data points (default: 100, max: 500)
- `indicators_config` (string, optional): JSON string with indicator configuration
- `use_enhanced` (boolean, optional): Use enhanced indicators system (default: true)

### 🔄 `get_dex_data_with_indicators` (Enhanced)

**Description**: Fetches DEX candlestick data with enhanced indicator support.

**Parameters**:
- `chain_index` (string, required): Chain identifier
- `token_address` (string, required): Token contract address
- `timeframe` (string, optional): Time interval (default: "1h")
- `limit` (integer, optional): Number of data points (default: 100)
- `indicators_config` (string, optional): JSON string with indicator configuration
- `use_enhanced` (boolean, optional): Use enhanced indicators system (default: true)

### `get_dex_token_price`

**Description**: Fetches current price of a DEX token.

**Parameters**:
- `chain_index` (string, required): Blockchain chain index
- `token_address` (string, required): Token contract address

**Response**:
```json
{
  "success": true,
  "data": {
    "chainIndex": "1",
    "tokenContractAddress": "0x...",
    "price": "50000.0",
    "priceUsd": "50000.0",
    "time": "1640995200000"
  }
}
```

### `get_cex_price`

**Description**: Fetches current price from a centralized exchange.

**Parameters**:
- `exchange` (string, required): Exchange name
- `symbol` (string, required): Trading pair symbol

## Indicator Categories and Examples

### Momentum Indicators (30 indicators)
```json
{
  "rsi": [{"timeperiod": 14}, {"timeperiod": 21}],
  "macd": [{"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}],
  "stoch": [{"fastkperiod": 5, "slowkperiod": 3, "slowdperiod": 3}],
  "cci": [{"timeperiod": 14}],
  "adx": [{"timeperiod": 14}],
  "willr": [{"timeperiod": 14}],
  "mfi": [{"timeperiod": 14}],
  "bop": [{}],
  "cmo": [{"timeperiod": 14}],
  "dx": [{"timeperiod": 14}]
}
```

### Overlap Studies (17 indicators)
```json
{
  "sma": [{"timeperiod": 20}, {"timeperiod": 50}],
  "ema": [{"timeperiod": 12}, {"timeperiod": 26}],
  "wma": [{"timeperiod": 20}],
  "dema": [{"timeperiod": 30}],
  "tema": [{"timeperiod": 30}],
  "trima": [{"timeperiod": 30}],
  "kama": [{"timeperiod": 30}],
  "t3": [{"timeperiod": 5, "vfactor": 0.7}],
  "bbands": [{"timeperiod": 20, "nbdevup": 2, "nbdevdn": 2}],
  "sar": [{"acceleration": 0.02, "maximum": 0.2}]
}
```

### Volatility Indicators (3 indicators)
```json
{
  "atr": [{"timeperiod": 14}],
  "natr": [{"timeperiod": 14}],
  "trange": [{}]
}
```

### Volume Indicators (3 indicators)
```json
{
  "obv": [{}],
  "ad": [{}],
  "adosc": [{"fastperiod": 3, "slowperiod": 10}]
}
```

### Pattern Recognition (61 indicators)
```json
{
  "cdldoji": [{}],
  "cdlhammer": [{}],
  "cdlengulfing": [{}],
  "cdl2crows": [{}],
  "cdl3blackcrows": [{}],
  "cdl3inside": [{}],
  "cdl3linestrike": [{}],
  "cdl3outside": [{}]
}
```

## Transport Protocols

### stdio Transport
**Usage**: Standard MCP client integration
**Protocol**: JSON-RPC over stdin/stdout
**Best for**: Command-line tools, local integrations

### HTTP/SSE Transport
**Base URL**: `http://localhost:8000`
**Protocol**: JSON-RPC over HTTP with SSE streaming
**Best for**: Web applications, multiple clients

#### HTTP Endpoints
- `POST /mcp` - JSON-RPC requests
- `GET /mcp` - SSE stream
- `DELETE /mcp` - Terminate session
- `GET /health` - Health check
- `GET /` - Server info

## Error Handling

### Common Error Codes
- `-32600`: Invalid Request
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error

### Error Response Format
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32603,
    "message": "Internal error: Tool execution failed"
  },
  "id": 1
}
```

## Rate Limits and Quotas

### Default Limits
- **Requests per second**: 10
- **Maximum candles per request**: 300 (DEX), 500 (CEX)
- **Maximum indicators per request**: No limit
- **Session timeout**: 1 hour (HTTP transport)

### Optimization Tips
1. **Batch requests**: Use multiple indicators in single request
2. **Cache results**: Store frequently used data locally
3. **Limit timeframes**: Use appropriate timeframes for your use case
4. **Monitor rate limits**: Implement exponential backoff

## Examples

### Complete Trading Analysis
```json
{
  "sma": [{"timeperiod": 20}, {"timeperiod": 50}, {"timeperiod": 200}],
  "ema": [{"timeperiod": 12}, {"timeperiod": 26}],
  "macd": [{"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}],
  "rsi": [{"timeperiod": 14}],
  "bbands": [{"timeperiod": 20, "nbdevup": 2, "nbdevdn": 2}],
  "stoch": [{"fastkperiod": 5, "slowkperiod": 3, "slowdperiod": 3}],
  "atr": [{"timeperiod": 14}],
  "obv": [{}],
  "adx": [{"timeperiod": 14}],
  "cci": [{"timeperiod": 14}]
}
```

This configuration provides:
- Trend analysis (SMA, EMA)
- Momentum analysis (MACD, RSI, Stochastic)
- Volatility analysis (Bollinger Bands, ATR)
- Volume analysis (OBV)
- Strength analysis (ADX, CCI)
