# Crypto PowerData MCP 服务

专注于加密货币数据获取的MCP服务：**CEX K线与指标** + **DEX K线与指标** + **DEX 实时价格**

## ✨ 核心功能

### 1. CEX K线数据与指标获取
- 支持100+中心化交易所（通过CCXT）
- 获取K线数据（OHLCV）
- **支持自定义技术指标参数**
- **一次性返回K线+指标**

### 2. DEX K线数据与指标获取
- **正确使用OKX DEX API** 获取标准K线数据
- 直接调用 `/api/v5/dex/market/candles` 接口
- **支持自定义技术指标参数**
- **一次性返回K线+指标**
- 支持多种时间周期（1m-1M）

### 3. DEX 实时价格获取
- 使用OKX DEX API的 `/api/v5/dex/market/price` 端点获取单个代币的实时价格。

## 🚀 快速开始

```bash
# 1. 安装依赖
uv sync

# 2. 启动服务
uv run python -m src.main

# 3. 测试功能
uv run python test_mcp_functionality.py
```

## 🔧 核心工具

### `get_cex_data_with_indicators`
从CEX获取K线数据并计算自定义技术指标。
```json
{
  "exchange": "binance",
  "symbol": "BTC/USDT",
  "timeframe": "1h",
  "limit": 100,
  "indicators_config": {
    "macd": {"fast": 12, "slow": 26, "signal": 9},
    "rsi": {"period": 14}
  }
}
```

### `get_dex_data_with_indicators`
从OKX DEX API获取代币数据并计算自定义技术指标。
```json
{
  "chain_index": "1",
  "token_address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
  "timeframe": "1h",
  "limit": 100,
  "indicators_config": {
    "sma": {"period": 20},
    "rsi": {"period": 14}
  }
}
```

### `get_dex_token_price`
从OKX DEX API获取单个代币的当前价格。
```json
{
  "chain_index": "1",
  "token_address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
}
```

## ⚙️ 配置

### 必需配置
- Python 3.10+
- UV包管理器

### 可选配置（DEX功能）
在 `.env` 文件中配置OKX API凭据：
```env
OKX_API_KEY=your_api_key
OKX_SECRET_KEY=your_secret_key
OKX_API_PASSPHRASE=your_passphrase
OKX_PROJECT_ID=your_project_id
```

## 🧪 MCP 客户端测试指南

### MCP Studio / Claude Desktop 配置
将以下配置添加到您的MCP客户端：
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
**注意**: 如果您的客户端不支持 `cwd`，请移除该行并将 `PYTHONPATH` 设置为项目的绝对路径。

### 自定义客户端测试 (Python)
```python
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_server():
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "src.main"],
        cwd=".",
        env={"PYTHONPATH": "."}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 在此测试工具调用
            result = await session.call_tool(
                "get_dex_token_price",
                {
                    "chain_index": "1",
                    "token_address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
                }
            )
            print(json.dumps(json.loads(result.content[0].text), indent=2))

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
```

## 📊 技术指标支持

| 指标 | 参数 | 示例 |
|------|------|------|
| SMA | period | `{"sma": {"period": 20}}` |
| EMA | period | `{"ema": {"period": 50}}` |
| RSI | period | `{"rsi": {"period": 14}}` |
| MACD | fast, slow, signal | `{"macd": {"fast": 12, "slow": 26, "signal": 9}}` |
| Bollinger Bands | period, std | `{"bb": {"period": 20, "std": 2}}` |