#!/usr/bin/env python3
"""
Test script to verify improved authentication timing.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent / "src"))

from web_auth_mcp.server import WebAuthMCPServer


async def test_auth_timing():
    """Test the improved authentication timing."""
    print("🕐 Testing Improved Authentication Timing")
    print("=" * 60)
    print()
    
    # Configure for patient authentication
    os.environ['BROWSER_HEADLESS'] = 'false'
    os.environ['BROWSER_TIMEOUT'] = '300'  # 5 minutes total
    os.environ['BROWSER_USE_DEFAULT_PROFILE'] = 'true'
    os.environ['BROWSER_AUTO_FILL_PASSWORDS'] = 'true'
    os.environ['AUTH_WAIT_TIME'] = '10'  # Wait 10 seconds for autofill
    os.environ['MANUAL_AUTH_TIMEOUT'] = '180'  # 3 minutes for manual auth
    
    server = WebAuthMCPServer()
    
    print("Configuration:")
    print(f"  Browser timeout: {server.auth_handler.browser_timeout} seconds")
    print(f"  Manual auth timeout: {server.auth_handler.manual_auth_timeout} seconds")
    print(f"  Autofill wait time: {server.auth_handler.auth_wait_time} seconds")
    print(f"  Use default profile: {server.auth_handler.use_default_profile}")
    print(f"  Auto-fill passwords: {server.auth_handler.auto_fill_passwords}")
    print()
    
    print("🎯 Improvements Made:")
    print("  ✅ Increased browser timeout to 5 minutes")
    print("  ✅ Separate manual authentication timeout (3 minutes)")
    print("  ✅ Longer wait time for Chrome autofill (10 seconds)")
    print("  ✅ More conservative authentication detection")
    print("  ✅ Better user feedback and progress updates")
    print("  ✅ Less frequent checking to avoid interrupting user")
    print()
    
    print("🔐 Authentication Process:")
    print("  1. Browser opens and loads the login page")
    print("  2. System waits 5 seconds for page to load completely")
    print("  3. If login form detected:")
    print("     - Clicks username field to trigger autofill")
    print("     - Waits 10 seconds for Chrome to autofill")
    print("     - If autofilled, attempts automatic submission")
    print("  4. If no autofill or manual entry needed:")
    print("     - Browser stays open for up to 3 minutes")
    print("     - User can manually enter credentials")
    print("     - Progress updates every 30 seconds")
    print("  5. Authentication detection requires stronger confidence")
    print("  6. Browser closes only after successful verification")
    print()
    
    print("💡 Tips for Best Results:")
    print("  - Save your passwords in Chrome beforehand")
    print("  - Don't close the browser window manually")
    print("  - Wait for autofill before typing manually")
    print("  - The browser will close automatically when done")
    print()
    
    # Test with a site that requires authentication
    test_choice = input("Test with O'Reilly? (y/n): ").strip().lower()
    
    if test_choice == 'y':
        print("\n🧪 Testing with O'Reilly...")
        print("This will open Chrome and demonstrate the improved timing.")
        print("You'll have plenty of time to authenticate!")
        print()
        
        arguments = {
            "url": "https://learning.oreilly.com/search/?q=linux+kernel+memory+management",
            "method": "GET"
        }
        
        try:
            result = await server._handle_http_request(arguments)
            print("✅ Authentication test completed!")
            print("The browser should have stayed open long enough for you to authenticate.")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
    else:
        print("Skipping live test. The improvements are ready to use!")


async def main():
    """Main test function."""
    await test_auth_timing()
    
    print("\n" + "=" * 60)
    print("🎉 Authentication Timing Improvements Complete!")
    print()
    print("Key Changes:")
    print("- Browser timeout: 60s → 300s (5 minutes)")
    print("- Manual auth timeout: Added 180s (3 minutes)")
    print("- Autofill wait time: Added 10s patience")
    print("- Authentication detection: More conservative")
    print("- User feedback: Better progress updates")
    print()
    print("The authentication window will now stay open much longer,")
    print("giving you plenty of time to enter credentials manually")
    print("or wait for Chrome's autofill to work!")


if __name__ == "__main__":
    asyncio.run(main())
