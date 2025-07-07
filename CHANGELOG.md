# Changelog

All notable changes to the Crypto PowerData MCP service will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Crypto PowerData MCP service
- Comprehensive TA-Lib indicator support (158 indicators across 10 categories)
- Dual transport protocol support (stdio and HTTP/SSE)
- Flexible multi-parameter indicator configuration
- CEX data integration via CCXT (100+ exchanges)
- DEX data integration via OKX DEX API
- Real-time price fetching for DEX tokens
- Enhanced parameter parsing and validation
- Comprehensive test suite
- Detailed documentation and configuration guides

### Features
- **Enhanced Indicators System**: Support for multiple instances of the same indicator with different parameters
- **Intelligent Result Labeling**: Automatic column naming based on indicator parameters (e.g., `ema_12`, `macd_12_26_9`)
- **Robust Parameter Handling**: Automatic parsing of JSON strings, Python dictionaries, and various input formats
- **Transport Flexibility**: Auto-detection between stdio and HTTP/SSE modes
- **Comprehensive Error Handling**: Detailed error messages and graceful fallbacks
- **Performance Optimization**: Efficient indicator calculations and data processing

### Technical Details
- Python 3.10+ support
- UV package manager integration
- FastAPI for HTTP transport
- Pydantic for data validation
- Comprehensive logging and debugging support

## [0.1.0] - 2024-12-XX

### Added
- Initial project setup
- Core MCP service architecture
- Basic indicator calculations
- CCXT integration for CEX data
- OKX DEX API integration
- Configuration management
- Test framework setup

### Dependencies
- mcp >= 1.0.0
- ccxt >= 4.0.0
- pandas >= 2.0.0
- numpy >= 1.24.0
- ta-lib >= 0.4.25
- python-dotenv >= 1.0.0
- aiohttp >= 3.8.0
- fastapi >= 0.104.0
- uvicorn >= 0.24.0
- pydantic >= 2.0.0

### Documentation
- Comprehensive README with usage examples
- API documentation
- Configuration guide
- Testing documentation
- Chinese language documentation (README-zh.md)

---

## Release Notes

### Version 0.1.0 Features

#### Core Functionality
- **Multi-Exchange Support**: Access to 100+ centralized exchanges via CCXT
- **DEX Integration**: Direct integration with OKX DEX API for decentralized exchange data
- **Technical Analysis**: Complete TA-Lib integration with 158 indicators
- **Flexible Configuration**: Support for multiple parameter sets per indicator

#### Transport Protocols
- **stdio Transport**: Standard input/output for command-line and programmatic access
- **HTTP/SSE Transport**: Server-Sent Events for web applications and real-time feeds
- **Auto-Detection**: Automatic transport selection based on environment

#### Data Sources
- **CEX Data**: OHLCV candlestick data from centralized exchanges
- **DEX Data**: Candlestick data from decentralized exchanges via OKX DEX API
- **Real-time Prices**: Current token prices from DEX markets
- **Historical Data**: Configurable time ranges and intervals

#### Developer Experience
- **Comprehensive Testing**: Multiple test suites for different use cases
- **Rich Documentation**: Detailed guides for setup, configuration, and usage
- **Example Configurations**: Ready-to-use configuration examples
- **Error Handling**: Robust error handling with helpful error messages

### Upcoming Features (Roadmap)
- Additional DEX integrations (Uniswap, PancakeSwap, etc.)
- WebSocket support for real-time data streaming
- Advanced indicator combinations and custom formulas
- Portfolio tracking and analysis tools
- Performance monitoring and metrics
- Plugin system for custom indicators
- GraphQL API support
- Database integration for historical data storage
