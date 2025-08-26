#!/usr/bin/env python3
"""
Example usage of the Web Auth MCP Server.

This script demonstrates how to use the MCP server to make HTTP requests
with automatic authentication handling.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent / "src"))

from web_auth_mcp.server import WebAuthMCPServer


async def example_request():
    """Example of making an HTTP request through the MCP server."""
    server = WebAuthMCPServer()
    
    # Example request that might require authentication
    arguments = {
        "url": "https://httpbin.org/bearer",
        "method": "GET",
        "headers": {
            "User-Agent": "Web-Auth-MCP/0.1.0"
        }
    }
    
    print("Making HTTP request...")
    print(f"URL: {arguments['url']}")
    print(f"Method: {arguments['method']}")
    
    try:
        result = await server._handle_http_request(arguments)
        response_text = result[0].text
        response_data = json.loads(response_text)
        
        print("\nResponse:")
        print(f"Status: {response_data.get('status_code')}")
        print(f"Authenticated: {response_data.get('authenticated')}")
        print(f"Body: {response_data.get('body', '')[:200]}...")
        
    except Exception as e:
        print(f"Error: {e}")


async def example_auth_required():
    """Example of making a request that requires authentication."""
    server = WebAuthMCPServer()
    
    # Example request that requires authentication
    arguments = {
        "url": "https://httpbin.org/status/401",
        "method": "GET",
        "auth_required": True
    }
    
    print("\nMaking request that requires authentication...")
    print(f"URL: {arguments['url']}")
    
    try:
        result = await server._handle_http_request(arguments)
        response_text = result[0].text
        response_data = json.loads(response_text)
        
        print("\nResponse:")
        print(f"Status: {response_data.get('status_code')}")
        print(f"Authenticated: {response_data.get('authenticated')}")
        
    except Exception as e:
        print(f"Error: {e}")


async def main():
    """Main example function."""
    print("Web Auth MCP Server Examples")
    print("=" * 40)
    
    # Example 1: Basic HTTP request
    await example_request()
    
    # Example 2: Request requiring authentication
    await example_auth_required()
    
    print("\nExamples completed!")


if __name__ == "__main__":
    asyncio.run(main())
