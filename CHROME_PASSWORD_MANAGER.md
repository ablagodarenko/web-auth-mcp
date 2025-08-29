# Chrome Password Manager Integration

This document explains how to use Chrome's saved passwords for automatic authentication in the Web Auth MCP server.

## Overview

The Web Auth MCP server now supports using Chrome's built-in password manager to automatically fill and submit login forms. This feature can significantly streamline the authentication process by leveraging passwords you've already saved in Chrome.

## Configuration Options

### Environment Variables

Add these to your `.env` file or set as environment variables:

```bash
# Use your system's Chrome profile (access to all saved passwords)
BROWSER_USE_DEFAULT_PROFILE=true

# Enable Chrome password manager features (default: true)
BROWSER_ENABLE_PASSWORD_MANAGER=true

# Automatically detect and fill login forms (default: true)
BROWSER_AUTO_FILL_PASSWORDS=true

# Run browser in non-headless mode to see the process (recommended for password manager)
BROWSER_HEADLESS=false

# Authentication timing (NEW - fixes quick closing issue)
BROWSER_TIMEOUT=300          # Total browser timeout (5 minutes)
MANUAL_AUTH_TIMEOUT=180      # Time for manual authentication (3 minutes)
AUTH_WAIT_TIME=10           # Wait time for Chrome autofill (10 seconds)
```

### Configuration Modes

#### 1. Default Mode (Temporary Profile)
```bash
BROWSER_USE_DEFAULT_PROFILE=false
BROWSER_ENABLE_PASSWORD_MANAGER=true
BROWSER_AUTO_FILL_PASSWORDS=true
```

- Uses a temporary Chrome profile
- Password manager enabled for the session
- Passwords can be saved and used during the session
- Profile is cleaned up after use

#### 2. System Profile Mode
```bash
BROWSER_USE_DEFAULT_PROFILE=true
BROWSER_ENABLE_PASSWORD_MANAGER=true
BROWSER_AUTO_FILL_PASSWORDS=true
```

- Uses your system's Chrome profile
- Access to all your existing saved passwords
- New passwords are saved to your main Chrome profile
- May show "Chrome is being controlled by automated test software" warning

## How It Works

### Automatic Login Process

1. **Page Load**: When authentication is required, Chrome opens the login page
2. **Form Detection**: The system automatically detects login forms using common selectors:
   - Email/username fields: `input[type="email"]`, `input[name*="user"]`, etc.
   - Password fields: `input[type="password"]`, `input[name="password"]`, etc.
3. **Autofill Trigger**: Clicks on the username field to trigger Chrome's autofill
4. **Credential Check**: Verifies if Chrome has populated the fields with saved credentials
5. **Form Submission**: Automatically submits the form if credentials are found
6. **Fallback**: If auto-submission fails, user can manually complete the process

### Supported Login Form Patterns

The system recognizes various login form patterns:

**Username/Email Fields:**
- `input[type="email"]`
- `input[type="text"][name*="user"]`
- `input[type="text"][name*="email"]`
- `input[id*="login"]`
- `input[class*="username"]`

**Password Fields:**
- `input[type="password"]`
- `input[name="password"]`
- `input[id*="password"]`

**Submit Buttons:**
- `button[type="submit"]`
- `button[name*="login"]`
- `button:contains("Sign in")`
- `button:contains("Log in")`

## Usage Examples

### Basic Usage with Auto-fill

```python
import os
from web_auth_mcp.server import WebAuthMCPServer

# Configure for automatic password filling
os.environ['BROWSER_USE_DEFAULT_PROFILE'] = 'true'
os.environ['BROWSER_AUTO_FILL_PASSWORDS'] = 'true'
os.environ['BROWSER_HEADLESS'] = 'false'

server = WebAuthMCPServer()

# Make a request that requires authentication
arguments = {
    "url": "https://example.com/protected-resource",
    "method": "GET"
}

result = await server._handle_http_request(arguments)
```

### Manual Password Entry Mode

```python
# Disable auto-fill for manual control
os.environ['BROWSER_AUTO_FILL_PASSWORDS'] = 'false'
os.environ['BROWSER_ENABLE_PASSWORD_MANAGER'] = 'true'

# Chrome will still offer password suggestions, but won't auto-submit
```

## Testing

### Test Password Manager Configuration

```bash
python test_password_manager.py
```

This will show your current configuration and explain the different modes.

### Test with Real Authentication

```bash
python test_browser_auth.py
```

This will test the complete authentication flow with a real website.

## Troubleshooting

### Common Issues

1. **Browser Closes Too Quickly** ⭐ **FIXED**
   - **Problem**: Authentication window closes before you can enter credentials
   - **Solution**: Updated timing configuration
   - **Settings**:
     ```bash
     BROWSER_TIMEOUT=300          # 5 minutes total
     MANUAL_AUTH_TIMEOUT=180      # 3 minutes for manual entry
     AUTH_WAIT_TIME=10           # 10 seconds for autofill
     ```

2. **Autofill Not Working**
   - Ensure `BROWSER_ENABLE_PASSWORD_MANAGER=true`
   - Check that you have saved passwords for the site
   - Try using `BROWSER_USE_DEFAULT_PROFILE=true`
   - Wait for the full autofill delay (10 seconds)

3. **Form Not Submitting**
   - The system may not recognize the submit button
   - Manual submission will be required
   - Check browser console for JavaScript errors

4. **Chrome Profile Conflicts** ⭐ **FIXED**
   - **Problem**: "user data directory is already in use" error
   - **Cause**: Chrome already running while trying to use default profile
   - **Solution**: Now handled automatically
     - System detects running Chrome processes
     - Creates temporary copy of profile data
     - Falls back to fresh profile if needed
     - Preserves all password manager functionality

5. **Profile Access Issues**
   - Check Chrome profile path permissions
   - Try temporary profile mode first
   - System now handles most conflicts automatically

### Debug Mode

Enable debug logging to see detailed information:

```bash
LOG_LEVEL=DEBUG python your_script.py
```

## Security Considerations

- **System Profile Mode**: Gives the automation access to all your saved passwords
- **Temporary Profile Mode**: More secure, only passwords saved during the session
- **Headless Mode**: Disable for password manager functionality (`BROWSER_HEADLESS=false`)
- **Network Security**: Ensure you're on a trusted network when using saved passwords

## Best Practices

1. **Start with Temporary Profile**: Test with `BROWSER_USE_DEFAULT_PROFILE=false` first
2. **Use Non-Headless Mode**: Set `BROWSER_HEADLESS=false` for password manager features
3. **Monitor Auto-fill**: Watch the process to ensure it's working correctly
4. **Fallback Plan**: Always be prepared to manually complete authentication
5. **Regular Testing**: Test your configuration periodically to ensure it still works

## Limitations

- Only works with standard HTML login forms
- May not work with complex JavaScript-based authentication
- Single-page applications (SPAs) may require manual intervention
- Some sites may block automated form submission
- OAuth flows may still require manual interaction
