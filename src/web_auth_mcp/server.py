#!/usr/bin/env python3
"""
Web Auth MCP Server

An MCP server that handles HTTP requests with browser-based authentication.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Sequence

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
)
from pydantic import BaseModel

from .auth_handler import AuthHandler
from .config import load_config
from .http_client import HttpClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class HttpRequestParams(BaseModel):
    """Parameters for HTTP request tool."""
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    body: Optional[str] = None
    auth_required: Optional[bool] = None


class WebAuthMCPServer:
    """MCP Server for HTTP requests with browser-based authentication."""

    def __init__(self):
        self.config = load_config()
        self.server = Server("web-auth-mcp")
        self.http_client = HttpClient()
        self.auth_handler = AuthHandler()
        self._setup_tools()
    
    def _setup_tools(self):
        """Register MCP tools."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="http_request",
                    description="Execute HTTP requests with automatic authentication handling",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to request"
                            },
                            "method": {
                                "type": "string",
                                "description": "HTTP method (GET, POST, PUT, DELETE, etc.)",
                                "default": "GET"
                            },
                            "headers": {
                                "type": "object",
                                "description": "Request headers",
                                "additionalProperties": {"type": "string"}
                            },
                            "body": {
                                "type": "string",
                                "description": "Request body"
                            },
                            "auth_required": {
                                "type": "boolean",
                                "description": "Force authentication flow"
                            }
                        },
                        "required": ["url"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> Sequence[TextContent]:
            """Handle tool calls."""
            if name == "http_request":
                return await self._handle_http_request(arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _handle_http_request(self, arguments: Dict[str, Any]) -> Sequence[TextContent]:
        """Handle HTTP request tool call."""
        try:
            # Validate parameters
            params = HttpRequestParams(**arguments)
            
            logger.info(f"Making HTTP request: {params.method} {params.url}")
            
            # Make initial HTTP request
            response = await self.http_client.request(
                method=params.method,
                url=params.url,
                headers=params.headers,
                body=params.body
            )
            
            # Check if authentication is required
            needs_auth = (
                params.auth_required or 
                self.auth_handler.needs_authentication(response)
            )
            
            if needs_auth:
                logger.info("Authentication required, starting browser flow")
                
                # Perform browser-based authentication
                auth_data = await self.auth_handler.authenticate(params.url)
                
                if auth_data:
                    logger.info("Authentication successful, retrying request")
                    
                    # Retry request with authentication
                    response = await self.http_client.request(
                        method=params.method,
                        url=params.url,
                        headers=params.headers,
                        body=params.body,
                        auth_data=auth_data
                    )
                else:
                    logger.warning("Authentication failed")
            
            # Format response
            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
                "authenticated": needs_auth and bool(auth_data) if needs_auth else False
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
            
        except Exception as e:
            logger.error(f"Error handling HTTP request: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "status_code": None,
                    "headers": {},
                    "body": "",
                    "authenticated": False
                }, indent=2)
            )]
    
    async def run(self):
        """Run the MCP server."""
        logger.info("Starting Web Auth MCP Server")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="web-auth-mcp",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )


async def async_main():
    """Async main entry point."""
    server = WebAuthMCPServer()
    await server.run()


def main():
    """Synchronous main entry point for console script."""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
