#!/usr/bin/env python3
"""
Example script demonstrating Chrome password manager integration.

This script shows how to configure and use the Chrome password manager
for automatic authentication.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent / "src"))

from web_auth_mcp.server import WebAuthMCPServer


async def example_with_password_manager():
    """Example using Chrome password manager for authentication."""
    print("Chrome Password Manager Example")
    print("=" * 50)
    print()
    
    # Configure Chrome to use password manager
    os.environ['BROWSER_HEADLESS'] = 'false'  # Must be false for password manager
    os.environ['BROWSER_USE_DEFAULT_PROFILE'] = 'true'  # Use your Chrome profile
    os.environ['BROWSER_ENABLE_PASSWORD_MANAGER'] = 'true'
    os.environ['BROWSER_AUTO_FILL_PASSWORDS'] = 'true'
    os.environ['BROWSER_TIMEOUT'] = '120'  # Give more time for manual interaction
    
    print("Configuration:")
    print(f"  Using Chrome profile: {os.environ['BROWSER_USE_DEFAULT_PROFILE']}")
    print(f"  Password manager: {os.environ['BROWSER_ENABLE_PASSWORD_MANAGER']}")
    print(f"  Auto-fill passwords: {os.environ['BROWSER_AUTO_FILL_PASSWORDS']}")
    print(f"  Headless mode: {os.environ['BROWSER_HEADLESS']}")
    print()
    
    server = WebAuthMCPServer()
    
    # Example with a site that requires authentication
    # Replace with a real URL that you have saved credentials for
    test_url = input("Enter a URL that requires authentication (or press Enter for demo): ").strip()
    
    if not test_url:
        test_url = "https://httpbin.org/basic-auth/user/pass"
        print(f"Using demo URL: {test_url}")
        print("Note: This is a basic auth demo, not a form-based login")
    
    print()
    print("Making request...")
    print("Chrome will open and attempt to:")
    print("1. Load the page")
    print("2. Detect login forms")
    print("3. Auto-fill with saved credentials")
    print("4. Submit the form automatically")
    print()
    print("If auto-fill doesn't work, you can:")
    print("- Use Chrome's password suggestions")
    print("- Fill the form manually")
    print("- Save new passwords for future use")
    print()
    
    arguments = {
        "url": test_url,
        "method": "GET",
        "headers": {
            "User-Agent": "Web-Auth-MCP/0.1.0"
        }
    }
    
    try:
        result = await server._handle_http_request(arguments)
        response_text = result[0].text
        
        print("Authentication completed!")
        print(f"Response length: {len(response_text)} characters")
        
        # Show first 500 characters of response
        if len(response_text) > 500:
            print(f"Response preview: {response_text[:500]}...")
        else:
            print(f"Response: {response_text}")
            
    except Exception as e:
        print(f"Error: {e}")


async def example_temporary_profile():
    """Example using temporary profile with password manager."""
    print("\nTemporary Profile Example")
    print("=" * 50)
    print()
    
    # Configure for temporary profile
    os.environ['BROWSER_HEADLESS'] = 'false'
    os.environ['BROWSER_USE_DEFAULT_PROFILE'] = 'false'  # Use temporary profile
    os.environ['BROWSER_ENABLE_PASSWORD_MANAGER'] = 'true'
    os.environ['BROWSER_AUTO_FILL_PASSWORDS'] = 'true'
    
    print("Configuration:")
    print("  Using temporary Chrome profile")
    print("  Password manager enabled for session")
    print("  Passwords can be saved during this session")
    print()
    
    server = WebAuthMCPServer()
    
    test_url = "https://httpbin.org/forms/post"
    print(f"Testing with form URL: {test_url}")
    print()
    print("This will:")
    print("1. Open a fresh Chrome profile")
    print("2. Load a test form")
    print("3. Allow you to fill and save credentials")
    print("4. Demonstrate password manager in temporary profile")
    print()
    
    arguments = {
        "url": test_url,
        "method": "GET"
    }
    
    try:
        result = await server._handle_http_request(arguments)
        print("Form loaded successfully!")
        print("You can now test saving and using passwords in the temporary profile.")
        
    except Exception as e:
        print(f"Error: {e}")


async def main():
    """Main example function."""
    print("Web Auth MCP - Chrome Password Manager Examples")
    print("=" * 60)
    print()
    
    print("Choose an example:")
    print("1. Use system Chrome profile (access to saved passwords)")
    print("2. Use temporary profile (clean session)")
    print("3. Both examples")
    print()
    
    choice = input("Enter choice (1-3, or Enter for all): ").strip()
    
    if choice == "1":
        await example_with_password_manager()
    elif choice == "2":
        await example_temporary_profile()
    else:
        await example_with_password_manager()
        await example_temporary_profile()
    
    print("\nExamples completed!")
    print()
    print("Tips for using Chrome password manager:")
    print("- Make sure Chrome is closed before running")
    print("- Use non-headless mode (BROWSER_HEADLESS=false)")
    print("- Save passwords in Chrome for automatic filling")
    print("- Check Chrome's password manager settings if issues occur")


if __name__ == "__main__":
    asyncio.run(main())
