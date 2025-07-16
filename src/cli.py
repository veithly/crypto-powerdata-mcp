#!/usr/bin/env python3
"""
CLI entry point for crypto-powerdata-mcp.

This module provides command-line interface for running the MCP server
in different modes (stdio, http, sse) with environment variable support.
"""

import argparse
import os
import sys
from typing import Dict, Optional

def parse_env_vars(env_args: Optional[list] = None) -> Dict[str, str]:
    """Parse environment variables from command line arguments."""
    env_vars = {}
    if env_args:
        for env_arg in env_args:
            if '=' in env_arg:
                key, value = env_arg.split('=', 1)
                env_vars[key] = value
            else:
                # If no value provided, try to get from environment
                env_vars[env_arg] = os.getenv(env_arg, '')
    return env_vars


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Crypto PowerData MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run in stdio mode (default, for MCP clients)
  uvx crypto-powerdata-mcp

  # Run in HTTP mode for web access
  uvx crypto-powerdata-mcp --http

  # Run in SSE mode for server-sent events
  uvx crypto-powerdata-mcp --sse

  # Run with custom environment variables
  uvx crypto-powerdata-mcp --env OKX_API_KEY=your_key --env OKX_SECRET_KEY=your_secret

  # Run HTTP server on custom port
  uvx crypto-powerdata-mcp --http --env HTTP_PORT=8080

Environment Variables:
  OKX_API_KEY          OKX API key for DEX data access
  OKX_SECRET_KEY       OKX secret key for DEX data access
  OKX_PASSPHRASE       OKX passphrase for DEX data access
  HTTP_PORT            Port for HTTP server (default: 8000)
  HTTP_HOST            Host for HTTP server (default: localhost)
  RATE_LIMIT_REQUESTS  Rate limit requests per minute (default: 60)
  RATE_LIMIT_WINDOW    Rate limit window in seconds (default: 60)
  LOG_LEVEL            Logging level (default: INFO)
        """
    )
    
    parser.add_argument(
        '--http', 
        action='store_true',
        help='Run in HTTP mode for web access'
    )
    
    parser.add_argument(
        '--sse', 
        action='store_true',
        help='Run in SSE (Server-Sent Events) mode'
    )
    
    parser.add_argument(
        '--env', 
        action='append',
        help='Set environment variable (format: KEY=value or KEY to use existing env var)'
    )
    
    parser.add_argument(
        '--version', 
        action='version',
        version='crypto-powerdata-mcp 0.1.0'
    )

    args = parser.parse_args()

    # Parse environment variables
    env_vars = parse_env_vars(args.env)

    # Determine transport mode
    if args.http:
        transport_mode = "http"
    elif args.sse:
        transport_mode = "sse"
    else:
        transport_mode = "stdio"

    # Import and run the main function
    try:
        from .main import main as run_server
        run_server(env_vars=env_vars, transport_mode=transport_mode)
    except ImportError:
        # Fallback for direct execution
        from main import main as run_server
        run_server(env_vars=env_vars, transport_mode=transport_mode)


if __name__ == "__main__":
    main()
