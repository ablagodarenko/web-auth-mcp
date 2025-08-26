#!/usr/bin/env python3
"""
Example HTTP client for testing the Web Auth MCP Server over HTTP/SSE.

This script demonstrates how to connect to the MCP server via HTTP transport.
"""

import asyncio
import json
import sys
from pathlib import Path

import httpx

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def test_http_mcp_server():
    """Test the MCP server over HTTP/SSE transport."""
    base_url = "http://localhost:8080"
    
    async with httpx.AsyncClient() as client:
        print("Testing Web Auth MCP Server over HTTP/SSE")
        print("=" * 50)
        
        # Test SSE endpoint
        print(f"Testing SSE endpoint: {base_url}/sse")
        
        try:
            # Test basic connectivity
            response = await client.get(f"{base_url}/sse")
            print(f"SSE endpoint status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ HTTP/SSE transport is working!")
                print("Server is ready to accept MCP connections")
            else:
                print(f"❌ Unexpected status code: {response.status_code}")
                
        except httpx.ConnectError:
            print("❌ Could not connect to the server")
            print("Make sure the server is running with: web-auth-mcp-http")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test message endpoint
        print(f"\nTesting message endpoint: {base_url}/message")
        
        try:
            # Test message endpoint (should return method not allowed for GET)
            response = await client.get(f"{base_url}/message")
            print(f"Message endpoint GET status: {response.status_code}")
            
            # Test POST to message endpoint
            test_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            
            response = await client.post(
                f"{base_url}/message",
                json=test_message,
                headers={"Content-Type": "application/json"}
            )
            print(f"Message endpoint POST status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Message endpoint is working!")
            
        except Exception as e:
            print(f"❌ Message endpoint error: {e}")


async def main():
    """Main function."""
    print("Web Auth MCP Server HTTP Client Test")
    print("=" * 40)
    print()
    print("This script tests the HTTP/SSE transport of the MCP server.")
    print("Make sure to start the server first with:")
    print("  web-auth-mcp-http")
    print()
    
    await test_http_mcp_server()
    
    print("\nTest completed!")
    print("\nTo use the server with an MCP client, configure it with:")
    print('  "url": "http://localhost:8080/sse"')


if __name__ == "__main__":
    asyncio.run(main())
