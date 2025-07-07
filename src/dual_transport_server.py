"""
Dual Transport MCP Server

This module implements a dual transport MCP server that supports both:
1. Standard stdio transport (for command-line and programmatic access)
2. Streamable HTTP transport with SSE (for web applications and real-time data feeds)

Both protocols expose identical functionality and tool interfaces.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, Optional, List
from datetime import datetime

from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware
import uvicorn

try:
    from .main import mcp, get_global_settings, set_global_settings
    from .data_provider import Settings
    from .mcp_bridge import bridge
except ImportError:
    from main import mcp, get_global_settings, set_global_settings
    from data_provider import Settings
    from mcp_bridge import bridge

logger = logging.getLogger(__name__)


class DualTransportServer:
    """MCP Server with dual transport support (stdio + HTTP/SSE)"""

    def __init__(self, port: int = 8000, host: str = "127.0.0.1"):
        self.port = port
        self.host = host
        self.app = FastAPI(
            title="Crypto PowerData MCP Server",
            description="MCP service for cryptocurrency data with dual transport support",
            version="1.0.0"
        )
        self.setup_fastapi()
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def setup_fastapi(self):
        """Setup FastAPI application with CORS and routes"""
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add routes
        self.app.post("/mcp")(self.handle_mcp_post)
        self.app.get("/mcp")(self.handle_mcp_get)
        self.app.delete("/mcp")(self.handle_mcp_delete)
        self.app.get("/health")(self.health_check)
        self.app.get("/")(self.root)

    async def root(self):
        """Root endpoint with server information"""
        return {
            "name": "Crypto PowerData MCP Server",
            "version": "1.0.0",
            "transport": "dual (stdio + http/sse)",
            "endpoints": {
                "mcp_post": "/mcp (POST) - JSON-RPC requests",
                "mcp_sse": "/mcp (GET) - Server-Sent Events stream",
                "health": "/health - Health check",
                "session_delete": "/mcp (DELETE) - Terminate session"
            },
            "features": [
                "Comprehensive TA-Lib indicators (158 functions)",
                "Flexible multi-parameter indicator support",
                "CEX data via CCXT (100+ exchanges)",
                "DEX data via OKX DEX API",
                "Real-time price feeds",
                "Dual transport protocols"
            ]
        }

    async def health_check(self):
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "active_sessions": len(self.sessions)
        }

    async def handle_mcp_post(self, request: Request):
        """Handle HTTP POST requests (client-to-server communication)"""
        try:
            # Get session ID from headers
            session_id = request.headers.get("Mcp-Session-Id")

            # Parse JSON-RPC request
            body = await request.json()

            # Validate JSON-RPC format
            if not self._validate_jsonrpc(body):
                return Response(
                    content=json.dumps({
                        "jsonrpc": "2.0",
                        "error": {"code": -32600, "message": "Invalid Request"},
                        "id": body.get("id")
                    }),
                    media_type="application/json",
                    status_code=400
                )

            # Handle initialization
            if body.get("method") == "initialize":
                session_id = self._generate_session_id()
                self.sessions[session_id] = {
                    "created_at": datetime.now(),
                    "last_activity": datetime.now()
                }

                # Initialize global settings if provided
                params = body.get("params", {})
                if "env_vars" in params:
                    set_global_settings(params["env_vars"])

                response = {
                    "jsonrpc": "2.0",
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {},
                            "resources": {},
                            "prompts": {},
                            "experimental": {}
                        },
                        "serverInfo": {
                            "name": "Crypto PowerData MCP",
                            "version": "1.0.0"
                        }
                    },
                    "id": body.get("id")
                }

                return Response(
                    content=json.dumps(response),
                    media_type="application/json",
                    headers={"Mcp-Session-Id": session_id}
                )

            # Handle other requests
            if session_id and session_id in self.sessions:
                self.sessions[session_id]["last_activity"] = datetime.now()

            # Process the request using FastMCP
            response = await self._process_mcp_request(body)

            return Response(
                content=json.dumps(response),
                media_type="application/json"
            )

        except Exception as e:
            logger.error(f"Error handling MCP POST request: {e}")
            return Response(
                content=json.dumps({
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                    "id": None
                }),
                media_type="application/json",
                status_code=500
            )

    async def handle_mcp_get(self, request: Request):
        """Handle HTTP GET requests (SSE stream for server-to-client communication)"""
        try:
            session_id = request.headers.get("Mcp-Session-Id")

            async def event_stream():
                """Generate SSE events"""
                # Send initial connection event
                yield f"data: {json.dumps({'type': 'connected', 'session_id': session_id})}\n\n"

                # Keep connection alive and send periodic heartbeats
                while True:
                    try:
                        # Send heartbeat every 30 seconds
                        yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
                        await asyncio.sleep(30)
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        logger.error(f"Error in SSE stream: {e}")
                        break

            return StreamingResponse(
                event_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Headers": "*"
                }
            )

        except Exception as e:
            logger.error(f"Error handling MCP GET request: {e}")
            return Response(
                content=f"Error: {str(e)}",
                status_code=500
            )

    async def handle_mcp_delete(self, request: Request):
        """Handle session termination"""
        try:
            session_id = request.headers.get("Mcp-Session-Id")

            if session_id and session_id in self.sessions:
                del self.sessions[session_id]
                return {"status": "session_terminated", "session_id": session_id}
            else:
                return Response(
                    content=json.dumps({"error": "Session not found"}),
                    status_code=404
                )

        except Exception as e:
            logger.error(f"Error handling session deletion: {e}")
            return Response(
                content=json.dumps({"error": str(e)}),
                status_code=500
            )

    def _validate_jsonrpc(self, body: Dict[str, Any]) -> bool:
        """Validate JSON-RPC 2.0 format"""
        return (
            isinstance(body, dict) and
            body.get("jsonrpc") == "2.0" and
            "method" in body and
            isinstance(body["method"], str)
        )

    def _generate_session_id(self) -> str:
        """Generate a secure session ID"""
        import uuid
        return str(uuid.uuid4())

    async def _process_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process MCP request using the MCP bridge"""
        try:
            return await bridge.process_request(request)
        except Exception as e:
            logger.error(f"Error processing MCP request: {e}")
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                "id": request.get("id")
            }

    async def run_http_server(self):
        """Run the HTTP/SSE server"""
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

    async def run_stdio_server(self):
        """Run the stdio server"""
        # This would run the existing FastMCP stdio server
        mcp.run()


async def run_dual_server(
    mode: str = "auto",
    http_port: int = 8000,
    http_host: str = "127.0.0.1",
    env_vars: Optional[Dict[str, str]] = None
):
    """
    Run the dual transport server

    Args:
        mode: "stdio", "http", or "auto" (detect based on environment)
        http_port: Port for HTTP server
        http_host: Host for HTTP server
        env_vars: Environment variables for configuration
    """
    # Initialize settings
    if env_vars:
        set_global_settings(env_vars)
    else:
        set_global_settings()

    server = DualTransportServer(port=http_port, host=http_host)

    if mode == "auto":
        # Auto-detect mode based on environment
        if sys.stdin.isatty():
            mode = "http"
        else:
            mode = "stdio"

    if mode == "stdio":
        logger.info("Starting MCP server in stdio mode")
        await server.run_stdio_server()
    elif mode == "http":
        logger.info(f"Starting MCP server in HTTP/SSE mode on {http_host}:{http_port}")
        await server.run_http_server()
    else:
        raise ValueError(f"Invalid mode: {mode}. Use 'stdio', 'http', or 'auto'")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Crypto PowerData MCP Server with Dual Transport")
    parser.add_argument("--mode", choices=["stdio", "http", "auto"], default="auto",
                       help="Transport mode (default: auto)")
    parser.add_argument("--port", type=int, default=8000,
                       help="HTTP server port (default: 8000)")
    parser.add_argument("--host", default="127.0.0.1",
                       help="HTTP server host (default: 127.0.0.1)")

    args = parser.parse_args()

    asyncio.run(run_dual_server(
        mode=args.mode,
        http_port=args.port,
        http_host=args.host
    ))
