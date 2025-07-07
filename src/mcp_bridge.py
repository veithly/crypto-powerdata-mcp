"""
MCP Bridge for Dual Transport

This module provides a bridge between FastMCP and the dual transport server,
allowing the same MCP tools to be exposed via both stdio and HTTP/SSE transports.
"""

import json
import logging
from typing import Any, Dict, List, Optional
import asyncio

try:
    from .main import mcp
except ImportError:
    from main import mcp

logger = logging.getLogger(__name__)


class MCPBridge:
    """Bridge between FastMCP and dual transport protocols"""

    def __init__(self):
        self.mcp_instance = mcp

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools from FastMCP"""
        try:
            # Extract tools from FastMCP instance
            tools = []

            # Get tools from the FastMCP registry
            if hasattr(self.mcp_instance, '_tools'):
                for tool_name, tool_info in self.mcp_instance._tools.items():
                    tool_schema = {
                        "name": tool_name,
                        "description": tool_info.get("description", ""),
                        "inputSchema": tool_info.get("inputSchema", {
                            "type": "object",
                            "properties": {},
                            "required": []
                        })
                    }
                    tools.append(tool_schema)
            else:
                # Fallback: manually define available tools
                tools = [
                    {
                        "name": "get_cex_data_with_indicators",
                        "description": "Get CEX candlestick data with technical indicators",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "exchange": {"type": "string", "description": "Exchange name"},
                                "symbol": {"type": "string", "description": "Trading pair symbol"},
                                "timeframe": {"type": "string", "default": "1h", "description": "Timeframe"},
                                "limit": {"type": "integer", "default": 100, "description": "Number of candles"},
                                "indicators": {"type": "string", "default": "sma,ema,rsi", "description": "Indicators to calculate"}
                            },
                            "required": ["exchange", "symbol"]
                        }
                    },
                    {
                        "name": "get_dex_data_with_indicators",
                        "description": "Get DEX candlestick data with technical indicators",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "chain_index": {"type": "string", "description": "Blockchain chain index"},
                                "token_address": {"type": "string", "description": "Token contract address"},
                                "timeframe": {"type": "string", "default": "1h", "description": "Timeframe"},
                                "limit": {"type": "integer", "default": 100, "description": "Number of candles"},
                                "indicators": {"type": "string", "default": "sma,ema,rsi", "description": "Indicators to calculate"}
                            },
                            "required": ["chain_index", "token_address"]
                        }
                    },
                    {
                        "name": "get_enhanced_dex_data_with_indicators",
                        "description": "Get DEX data with enhanced flexible technical indicators",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "chain_index": {"type": "string", "description": "Blockchain chain index"},
                                "token_address": {"type": "string", "description": "Token contract address"},
                                "timeframe": {"type": "string", "default": "1h", "description": "Timeframe"},
                                "limit": {"type": "integer", "default": 100, "description": "Number of candles"},
                                "indicators_config": {
                                    "type": "string",
                                    "default": '{"ema": [{"timeperiod": 12}, {"timeperiod": 26}], "rsi": [{"timeperiod": 14}]}',
                                    "description": "JSON string with flexible indicator configuration"
                                }
                            },
                            "required": ["chain_index", "token_address"]
                        }
                    },
                    {
                        "name": "get_available_indicators",
                        "description": "Get information about all available technical indicators",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    },
                    {
                        "name": "get_dex_token_price",
                        "description": "Get current price of a DEX token",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "chain_index": {"type": "string", "description": "Blockchain chain index"},
                                "token_address": {"type": "string", "description": "Token contract address"}
                            },
                            "required": ["chain_index", "token_address"]
                        }
                    },
                    {
                        "name": "get_cex_price",
                        "description": "Get current price from a centralized exchange",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "exchange": {"type": "string", "description": "Exchange name"},
                                "symbol": {"type": "string", "description": "Trading pair symbol"}
                            },
                            "required": ["exchange", "symbol"]
                        }
                    }
                ]

            return tools

        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            return []

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool via FastMCP"""
        try:
            # Import the tool functions directly
            try:
                from .main import (
                    get_cex_data_with_indicators,
                    get_dex_data_with_indicators,
                    get_enhanced_dex_data_with_indicators,
                    get_available_indicators,
                    get_dex_token_price,
                    get_cex_price
                )
            except ImportError:
                from main import (
                    get_cex_data_with_indicators,
                    get_dex_data_with_indicators,
                    get_enhanced_dex_data_with_indicators,
                    get_available_indicators,
                    get_dex_token_price,
                    get_cex_price
                )

            # Map tool names to functions
            tool_functions = {
                "get_cex_data_with_indicators": get_cex_data_with_indicators,
                "get_dex_data_with_indicators": get_dex_data_with_indicators,
                "get_enhanced_dex_data_with_indicators": get_enhanced_dex_data_with_indicators,
                "get_available_indicators": get_available_indicators,
                "get_dex_token_price": get_dex_token_price,
                "get_cex_price": get_cex_price
            }

            if tool_name not in tool_functions:
                return {
                    "error": f"Unknown tool: {tool_name}",
                    "available_tools": list(tool_functions.keys())
                }

            # Call the function
            func = tool_functions[tool_name]

            # Handle async functions
            if asyncio.iscoroutinefunction(func):
                result = await func(**arguments)
            else:
                result = func(**arguments)

            return result

        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {"error": f"Tool execution failed: {str(e)}"}

    def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        return {
            "name": "Crypto PowerData MCP",
            "version": "1.0.0",
            "description": "MCP service for cryptocurrency data with dual transport support",
            "capabilities": {
                "tools": True,
                "resources": False,
                "prompts": False,
                "experimental": {
                    "dual_transport": True,
                    "enhanced_indicators": True,
                    "flexible_parameters": True
                }
            },
            "features": [
                "Comprehensive TA-Lib indicators (158 functions)",
                "Flexible multi-parameter indicator support",
                "CEX data via CCXT (100+ exchanges)",
                "DEX data via OKX DEX API",
                "Real-time price feeds",
                "Dual transport protocols (stdio + HTTP/SSE)"
            ]
        }

    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialization request"""
        try:
            # Initialize global settings if provided
            if "env_vars" in params:
                from main import set_global_settings
                set_global_settings(params["env_vars"])

            server_info = self.get_server_info()

            return {
                "protocolVersion": "2024-11-05",
                "capabilities": server_info["capabilities"],
                "serverInfo": {
                    "name": server_info["name"],
                    "version": server_info["version"]
                },
                "instructions": "Use this MCP server to fetch cryptocurrency data from both centralized and decentralized exchanges, with comprehensive technical analysis capabilities."
            }

        except Exception as e:
            logger.error(f"Error in initialization: {e}")
            raise

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a JSON-RPC request"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                tools = await self.list_tools()
                result = {"tools": tools}
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                result = await self.call_tool(tool_name, tool_args)

                # Format result for MCP
                if isinstance(result, dict) and "success" in result:
                    # Convert our result format to MCP format
                    if result["success"]:
                        content = [{"type": "text", "text": json.dumps(result["data"], indent=2)}]
                    else:
                        content = [{"type": "text", "text": f"Error: {result.get('error', 'Unknown error')}"}]
                    result = {"content": content}
                else:
                    # Fallback formatting
                    content = [{"type": "text", "text": json.dumps(result, indent=2)}]
                    result = {"content": content}
            else:
                raise ValueError(f"Unknown method: {method}")

            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            }

        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": request.get("id")
            }


# Global bridge instance
bridge = MCPBridge()
