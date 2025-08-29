#!/usr/bin/env python3
"""
Test script to access JIRA issue EX-10514 with improved authentication timing.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent / "src"))

from web_auth_mcp.server import WebAuthMCPServer


async def test_jira_access():
    """Test accessing JIRA issue with improved authentication timing."""
    print("🎫 Testing JIRA Access - EX-10514")
    print("=" * 60)
    print()
    
    # Configure for patient authentication
    os.environ['BROWSER_HEADLESS'] = 'false'
    os.environ['BROWSER_TIMEOUT'] = '300'  # 5 minutes
    os.environ['BROWSER_USE_DEFAULT_PROFILE'] = 'true'
    os.environ['BROWSER_AUTO_FILL_PASSWORDS'] = 'true'
    os.environ['MANUAL_AUTH_TIMEOUT'] = '180'  # 3 minutes for manual auth
    os.environ['AUTH_WAIT_TIME'] = '10'  # 10 seconds for autofill
    os.environ['SUPPRESS_MCP_WARNINGS'] = 'true'
    
    server = WebAuthMCPServer()
    
    print("🔧 Configuration:")
    print(f"  Browser timeout: {server.auth_handler.browser_timeout} seconds (5 minutes)")
    print(f"  Manual auth timeout: {server.auth_handler.manual_auth_timeout} seconds (3 minutes)")
    print(f"  Autofill wait time: {server.auth_handler.auth_wait_time} seconds")
    print(f"  Use Chrome profile: {server.auth_handler.use_default_profile}")
    print(f"  Auto-fill passwords: {server.auth_handler.auto_fill_passwords}")
    print()
    
    # JIRA issue URL
    jira_url = "https://jira.whamcloud.com/browse/EX-10514"
    
    print(f"🎯 Target: {jira_url}")
    print()
    print("🔐 Authentication Process:")
    print("  1. Browser will open and load the JIRA login page")
    print("  2. System will wait 5 seconds for page to load completely")
    print("  3. If login form is detected:")
    print("     - Username field will be clicked to trigger autofill")
    print("     - System will wait 10 seconds for Chrome to autofill")
    print("     - If credentials are autofilled, form will be submitted automatically")
    print("  4. If no autofill or manual entry needed:")
    print("     - Browser will stay open for up to 3 minutes")
    print("     - You can manually enter your JIRA credentials")
    print("     - Progress updates will show every 30 seconds")
    print("  5. Browser will close only after successful authentication")
    print()
    
    print("💡 Tips for JIRA Authentication:")
    print("  - If you have JIRA credentials saved in Chrome, wait for autofill")
    print("  - If not, manually enter your username and password")
    print("  - Don't close the browser window - it will close automatically")
    print("  - The system is now much more patient with authentication")
    print()
    
    # Ask user if they want to proceed
    proceed = input("Proceed with JIRA authentication test? (y/n): ").strip().lower()
    
    if proceed == 'y':
        print("\n🚀 Starting JIRA access test...")
        print("Opening Chrome for authentication...")
        print()
        
        arguments = {
            "url": jira_url,
            "method": "GET",
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        }
        
        try:
            result = await server._handle_http_request(arguments)
            response_text = result[0].text
            response_data = json.loads(response_text)
            
            print("✅ JIRA access test completed!")
            print(f"   Status: {response_data.get('status_code')}")
            print(f"   Authenticated: {response_data.get('authenticated')}")
            print(f"   Content length: {len(response_data.get('body', ''))} characters")
            print()
            
            if response_data.get('authenticated'):
                print("🎉 Successfully authenticated and accessed JIRA!")
                print("   You should now be able to see the EX-10514 issue details.")
                
                # Check if we got the actual issue content
                body = response_data.get('body', '').lower()
                if 'ex-10514' in body:
                    print("   ✅ Issue EX-10514 content detected in response")
                if 'jira' in body:
                    print("   ✅ JIRA interface detected")
            else:
                print("ℹ️  Authentication may still be in progress or required")
                print("   The browser should have stayed open long enough for you to authenticate")
                
        except Exception as e:
            print(f"❌ Error during JIRA access: {e}")
            print("   This might be due to network issues or JIRA being unavailable")
            
    else:
        print("Skipping live test.")
        print()
        print("To test manually, use the MCP tool with these parameters:")
        print(f"  Tool: http_request")
        print(f"  URL: {jira_url}")
        print(f"  Method: GET")
        print()
        print("The improved timing will ensure the browser stays open long enough")
        print("for you to complete the JIRA authentication process!")


async def main():
    """Main test function."""
    await test_jira_access()
    
    print("\n" + "=" * 60)
    print("🎫 JIRA Access Test Summary")
    print()
    print("The web_auth_mcp tool is now configured with:")
    print("✅ Extended browser timeout (5 minutes)")
    print("✅ Patient manual authentication (3 minutes)")
    print("✅ Generous autofill wait time (10 seconds)")
    print("✅ Better authentication detection")
    print("✅ Clear user feedback and progress updates")
    print()
    print("This should resolve the issue where the browser")
    print("was closing too quickly before you could authenticate!")


if __name__ == "__main__":
    asyncio.run(main())
