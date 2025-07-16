# Quick Start Guide - Using uvx

This guide shows how to use `crypto-powerdata-mcp` directly with `uvx` without cloning the repository.

## Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) installed

## Installation & Usage

### 1. Direct Usage with uvx (Recommended)

Run the MCP server directly without installation:

```bash
# Run in stdio mode (for MCP clients like Claude Desktop)
uvx crypto-powerdata-mcp

# Run in HTTP mode for web access
uvx crypto-powerdata-mcp --http

# Run with custom environment variables
uvx crypto-powerdata-mcp --env OKX_API_KEY=your_key --env OKX_SECRET_KEY=your_secret

# Run HTTP server on custom port
uvx crypto-powerdata-mcp --http --env HTTP_PORT=8080
```

### 2. Configuration for Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "crypto-powerdata": {
      "command": "uvx",
      "args": ["crypto-powerdata-mcp"],
      "env": {
        "OKX_API_KEY": "your_okx_api_key",
        "OKX_SECRET_KEY": "your_okx_secret_key",
        "OKX_PASSPHRASE": "your_okx_passphrase"
      }
    }
  }
}
```

### 3. Configuration for MCP Studio

Add to your MCP Studio configuration:

```json
{
  "name": "Crypto PowerData MCP",
  "command": "uvx",
  "args": ["crypto-powerdata-mcp"],
  "env": {
    "OKX_API_KEY": "your_okx_api_key",
    "OKX_SECRET_KEY": "your_okx_secret_key",
    "OKX_PASSPHRASE": "your_okx_passphrase"
  }
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OKX_API_KEY` | OKX API key for DEX data | None |
| `OKX_SECRET_KEY` | OKX secret key for DEX data | None |
| `OKX_PASSPHRASE` | OKX passphrase for DEX data | None |
| `HTTP_PORT` | Port for HTTP server | 8000 |
| `HTTP_HOST` | Host for HTTP server | localhost |
| `RATE_LIMIT_REQUESTS` | Rate limit requests per minute | 60 |
| `RATE_LIMIT_WINDOW` | Rate limit window in seconds | 60 |
| `LOG_LEVEL` | Logging level | INFO |

## Available Tools

- **get_cex_data_with_indicators**: Fetch CEX candlestick data with technical indicators
- **get_dex_data_with_indicators**: Fetch DEX token data with technical indicators
- **get_cex_price**: Get real-time CEX prices
- **get_dex_token_price**: Get real-time DEX token prices
- **get_available_indicators**: List all available technical indicators

## Example Usage

### Fetch Bitcoin data from Binance with indicators

```python
# This would be called by your MCP client
{
  "tool": "get_cex_data_with_indicators",
  "arguments": {
    "exchange": "binance",
    "symbol": "BTC/USDT",
    "timeframe": "1h",
    "limit": 100,
    "indicators_config": "{\"ema\": [{\"timeperiod\": 12}, {\"timeperiod\": 26}], \"rsi\": [{\"timeperiod\": 14}]}"
  }
}
```

### Fetch DEX token data with MACD

```python
{
  "tool": "get_dex_data_with_indicators",
  "arguments": {
    "chain_index": "1",
    "token_address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "timeframe": "4h",
    "indicators_config": "{\"macd\": [{\"fastperiod\": 12, \"slowperiod\": 26, \"signalperiod\": 9}]}"
  }
}
```

## Troubleshooting

### Common Issues

1. **Permission denied**: Make sure `uv` is installed and in your PATH
2. **API errors**: Verify your OKX API credentials are correct
3. **Network issues**: Check your internet connection and firewall settings

### Getting Help

- Check the full documentation in the repository
- Review the API documentation for detailed parameter information
- Enable debug logging with `--env LOG_LEVEL=DEBUG`

## Advantages of uvx

- ✅ No need to clone repository
- ✅ No manual dependency management
- ✅ Automatic isolation
- ✅ Always uses latest published version
- ✅ Easy to update (`uvx` automatically handles updates)
- ✅ Works across different environments
