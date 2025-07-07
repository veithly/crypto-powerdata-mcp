# Configuration Guide

This guide covers all configuration options for the Crypto PowerData MCP Service with dual transport support.

## Environment Variables

### Required for DEX Features
```bash
# OKX DEX API Configuration
OKX_API_KEY=your_api_key_here
OKX_SECRET_KEY=your_secret_key_here
OKX_API_PASSPHRASE=your_passphrase_here
OKX_PROJECT_ID=your_project_id_here
```

### Optional Configuration
```bash
# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_SECOND=10

# Timeouts
TIMEOUT_SECONDS=30

# Technical Analysis Defaults
DEFAULT_INDICATORS=sma,ema,rsi,macd,bb,stoch
SMA_PERIODS=20,50,200
EMA_PERIODS=12,26,50
RSI_PERIOD=14
MACD_FAST=12
MACD_SLOW=26
MACD_SIGNAL=9
```

## MCP Client Configurations

### Claude Desktop (stdio)
```json
{
  "mcpServers": {
    "crypto-powerdata-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.main"],
      "cwd": "/absolute/path/to/crypto-powerdata-mcp",
      "env": {
        "PYTHONPATH": ".",
        "LOG_LEVEL": "INFO",
        "OKX_API_KEY": "your_okx_api_key_here",
        "OKX_SECRET_KEY": "your_okx_secret_key_here",
        "OKX_API_PASSPHRASE": "your_okx_api_passphrase_here",
        "OKX_PROJECT_ID": "your_okx_project_id_here",
        "RATE_LIMIT_REQUESTS_PER_SECOND": "10",
        "TIMEOUT_SECONDS": "30"
      },
      "alwaysAllow": [
        "get_enhanced_dex_data_with_indicators",
        "get_available_indicators",
        "get_cex_data_with_indicators",
        "get_dex_data_with_indicators",
        "get_dex_token_price",
        "get_cex_price"
      ]
    }
  }
}
```

### Claude Desktop (HTTP/SSE)
```json
{
  "mcpServers": {
    "crypto-powerdata-mcp-http": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.dual_transport_server", "--mode", "http", "--port", "8000"],
      "cwd": "/absolute/path/to/crypto-powerdata-mcp",
      "env": {
        "PYTHONPATH": ".",
        "LOG_LEVEL": "INFO",
        "OKX_API_KEY": "your_okx_api_key_here",
        "OKX_SECRET_KEY": "your_okx_secret_key_here",
        "OKX_API_PASSPHRASE": "your_okx_api_passphrase_here",
        "OKX_PROJECT_ID": "your_okx_project_id_here"
      }
    }
  }
}
```

### MCP Studio
```json
{
  "mcpServers": {
    "crypto-powerdata-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.main"],
      "cwd": "/absolute/path/to/crypto-powerdata-mcp",
      "env": {
        "PYTHONPATH": ".",
        "LOG_LEVEL": "INFO",
        "OKX_API_KEY": "your_okx_api_key_here",
        "OKX_SECRET_KEY": "your_okx_secret_key_here",
        "OKX_API_PASSPHRASE": "your_okx_api_passphrase_here",
        "OKX_PROJECT_ID": "your_okx_project_id_here"
      }
    }
  }
}
```

## Indicator Configuration Examples

### Basic Indicators
```json
{
  "ema": [{"timeperiod": 12}, {"timeperiod": 26}],
  "rsi": [{"timeperiod": 14}],
  "sma": [{"timeperiod": 20}, {"timeperiod": 50}]
}
```

### Advanced Multi-Parameter Setup
```json
{
  "ema": [
    {"timeperiod": 12},
    {"timeperiod": 26},
    {"timeperiod": 50},
    {"timeperiod": 120},
    {"timeperiod": 200}
  ],
  "macd": [
    {"fastperiod": 12, "slowperiod": 26, "signalperiod": 9},
    {"fastperiod": 5, "slowperiod": 35, "signalperiod": 5}
  ],
  "rsi": [
    {"timeperiod": 14},
    {"timeperiod": 21},
    {"timeperiod": 30}
  ],
  "bbands": [
    {"timeperiod": 20, "nbdevup": 2, "nbdevdn": 2},
    {"timeperiod": 10, "nbdevup": 1.5, "nbdevdn": 1.5}
  ],
  "stoch": [
    {"fastkperiod": 5, "slowkperiod": 3, "slowdperiod": 3},
    {"fastkperiod": 14, "slowkperiod": 3, "slowdperiod": 3}
  ],
  "atr": [
    {"timeperiod": 14},
    {"timeperiod": 21}
  ]
}
```

### Comprehensive Analysis Setup
```json
{
  "overlap": {
    "sma": [{"timeperiod": 20}, {"timeperiod": 50}, {"timeperiod": 200}],
    "ema": [{"timeperiod": 12}, {"timeperiod": 26}, {"timeperiod": 50}],
    "bbands": [{"timeperiod": 20, "nbdevup": 2, "nbdevdn": 2}]
  },
  "momentum": {
    "rsi": [{"timeperiod": 14}, {"timeperiod": 21}],
    "macd": [{"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}],
    "stoch": [{"fastkperiod": 5, "slowkperiod": 3, "slowdperiod": 3}],
    "cci": [{"timeperiod": 14}],
    "adx": [{"timeperiod": 14}]
  },
  "volatility": {
    "atr": [{"timeperiod": 14}],
    "natr": [{"timeperiod": 14}]
  },
  "volume": {
    "obv": [{}],
    "ad": [{}]
  }
}
```

## Transport Protocol Selection

### When to Use stdio
- **Command-line tools and scripts**
- **Local integrations**
- **Single client scenarios**
- **Simple request-response patterns**
- **Lower resource usage**

### When to Use HTTP/SSE
- **Web applications**
- **Multiple concurrent clients**
- **Real-time data streaming**
- **Stateful sessions**
- **Cross-platform compatibility**
- **Network-based access**

### Auto-Detection Logic
```bash
# The server automatically chooses:
# - stdio: When stdin is not a TTY (pipes, redirects, scripts)
# - HTTP: When stdin is a TTY (interactive terminal)

uv run python -m src.dual_transport_server --mode auto
```

## Performance Tuning

### Rate Limiting
```bash
# Adjust based on your API limits and usage patterns
RATE_LIMIT_REQUESTS_PER_SECOND=10  # Conservative
RATE_LIMIT_REQUESTS_PER_SECOND=20  # Moderate
RATE_LIMIT_REQUESTS_PER_SECOND=50  # Aggressive
```

### Timeout Configuration
```bash
# Network timeouts
TIMEOUT_SECONDS=30     # Default
TIMEOUT_SECONDS=60     # For slow networks
TIMEOUT_SECONDS=10     # For fast networks

# HTTP server timeouts (for HTTP transport)
HTTP_TIMEOUT=30
HTTP_KEEPALIVE=60
```

### Memory Optimization
```bash
# Limit data points for large datasets
DEFAULT_LIMIT=100      # Conservative
DEFAULT_LIMIT=500      # Moderate
DEFAULT_LIMIT=1000     # High memory usage

# Indicator calculation limits
MAX_INDICATORS_PER_REQUEST=10
MAX_PARAMETER_SETS_PER_INDICATOR=5
```

## Security Considerations

### API Key Management
- Store API keys in environment variables, not in code
- Use different API keys for different environments
- Rotate API keys regularly
- Monitor API key usage

### Network Security (HTTP Transport)
```bash
# Bind to localhost only for local use
HOST=127.0.0.1

# Use specific port
PORT=8000

# Enable CORS for web applications (configure appropriately)
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
```

### Access Control
```json
{
  "alwaysAllow": [
    "get_available_indicators",
    "get_cex_price"
  ],
  "requireConfirmation": [
    "get_enhanced_dex_data_with_indicators",
    "get_dex_data_with_indicators"
  ]
}
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure PYTHONPATH is set correctly
   export PYTHONPATH=/path/to/crypto-powerdata-mcp
   ```

2. **API Rate Limits**
   ```bash
   # Reduce request rate
   RATE_LIMIT_REQUESTS_PER_SECOND=5
   ```

3. **Memory Issues**
   ```bash
   # Reduce data limits
   DEFAULT_LIMIT=50
   ```

4. **Network Timeouts**
   ```bash
   # Increase timeout
   TIMEOUT_SECONDS=60
   ```

### Debug Mode
```bash
# Enable debug logging
LOG_LEVEL=DEBUG

# Run with verbose output
uv run python -m src.main --debug
```
