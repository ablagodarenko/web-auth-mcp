#!/usr/bin/env python3
"""
Test script to verify browser-based authentication works correctly.

This script tests the authentication flow with a visible browser window.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent / "src"))

from web_auth_mcp.server import WebAuthMCPServer


async def test_browser_authentication():
    """Test browser authentication with O'Reilly."""
    print("Testing Browser Authentication")
    print("=" * 40)
    print()
    print("This will test the browser authentication flow.")
    print("A Chrome browser window should open for you to complete authentication.")
    print()
    
    server = WebAuthMCPServer()
    
    # Test with O'Reilly URL that requires authentication
    test_url = "https://learning.oreilly.com/library/view/psp-sm-a-self-improvement/9780321579300/chapter10.html"
    
    arguments = {
        "url": test_url,
        "method": "GET",
        "headers": {
            "User-Agent": "Web-Auth-MCP/0.1.0"
        }
    }
    
    print(f"Testing authentication with: {test_url}")
    print()
    print("Expected behavior:")
    print("1. Initial request will be made")
    print("2. Authentication will be detected as required")
    print("3. Chrome browser window will open")
    print("4. You can complete authentication in the browser")
    print("5. Server will detect completion and retry the request")
    print()
    print("Starting test...")
    print("-" * 40)
    
    try:
        result = await server._handle_http_request(arguments)
        response_text = result[0].text
        
        print()
        print("Test Results:")
        print("=" * 40)
        print(response_text)
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    await test_browser_authentication()


if __name__ == "__main__":
    asyncio.run(main())
