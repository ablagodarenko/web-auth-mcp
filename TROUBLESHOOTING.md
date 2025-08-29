# web_auth_mcp Troubleshooting Guide

## Issue: "web_auth_mcp doesn't work"

If you're getting errors when trying to use the `http_request` tool from web_auth_mcp, here are the most common solutions:

## 1. Check MCP Server Configuration

### For Claude Desktop

The MCP server needs to be properly configured in your Claude Desktop settings.

**Location of config file:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**Correct configuration:**
```json
{
  "mcpServers": {
    "web-auth-mcp": {
      "command": "/Users/ablagodarenko/web-auth-mcp/venv/bin/python",
      "args": ["-m", "web_auth_mcp.server"],
      "cwd": "/Users/ablagodarenko/web-auth-mcp",
      "env": {
        "BROWSER_HEADLESS": "false",
        "BROWSER_USE_DEFAULT_PROFILE": "true",
        "BROWSER_AUTO_FILL_PASSWORDS": "true",
        "SUPPRESS_MCP_WARNINGS": "true"
      }
    }
  }
}
```

**Important:** Replace `/Users/ablagodarenko/web-auth-mcp` with your actual project path.

## 2. Verify Installation

```bash
# Navigate to project directory
cd /Users/ablagodarenko/web-auth-mcp

# Activate virtual environment
source venv/bin/activate

# Test server directly
python test_oreilly_access.py
```

You should see:
```
✅ Server capabilities retrieved
✅ HTTP request tool working correctly
```

## 3. Common Issues and Solutions

### Issue: "Command not found" or "Module not found"

**Solution:** Check the Python path in your MCP config:
```bash
# Find the correct Python path
which python
# Should output something like: /Users/ablagodarenko/web-auth-mcp/venv/bin/python
```

### Issue: "Permission denied"

**Solution:** Make sure the Python executable is executable:
```bash
chmod +x /Users/ablagodarenko/web-auth-mcp/venv/bin/python
```

### Issue: "Server not responding"

**Solution:** Restart Claude Desktop after changing the configuration.

### Issue: "Authentication not working"

**Solution:** Ensure Chrome password manager settings:
```bash
# Set environment variables
export BROWSER_HEADLESS=false
export BROWSER_USE_DEFAULT_PROFILE=true
export BROWSER_AUTO_FILL_PASSWORDS=true
```

## 4. Test the Tool Manually

You can test the tool functionality directly:

```bash
# Activate environment
source venv/bin/activate

# Test basic functionality
python -c "
from web_auth_mcp.server import WebAuthMCPServer
import asyncio

async def test():
    server = WebAuthMCPServer()
    result = await server._handle_http_request({
        'url': 'https://httpbin.org/get',
        'method': 'GET'
    })
    print('✅ Tool working:', len(result[0].text) > 0)

asyncio.run(test())
"
```

## 5. Debug Mode

Enable debug logging to see what's happening:

```json
{
  "mcpServers": {
    "web-auth-mcp": {
      "command": "/Users/ablagodarenko/web-auth-mcp/venv/bin/python",
      "args": ["-m", "web_auth_mcp.server"],
      "cwd": "/Users/ablagodarenko/web-auth-mcp",
      "env": {
        "LOG_LEVEL": "DEBUG",
        "BROWSER_HEADLESS": "false"
      }
    }
  }
}
```

## 6. Alternative: HTTP Mode

If stdio mode isn't working, try HTTP mode:

```json
{
  "mcpServers": {
    "web-auth-mcp": {
      "command": "/Users/ablagodarenko/web-auth-mcp/venv/bin/python",
      "args": ["-m", "web_auth_mcp.server", "--http"],
      "cwd": "/Users/ablagodarenko/web-auth-mcp"
    }
  }
}
```

## 7. Verify Tool Registration

The tool should be available as `http_request` with these parameters:
- `url` (required): The URL to request
- `method` (optional): HTTP method (default: GET)
- `headers` (optional): HTTP headers
- `body` (optional): Request body
- `auth_required` (optional): Force authentication

## 8. O'Reilly Specific Usage

For O'Reilly access:
```
Tool: http_request
URL: https://learning.oreilly.com/search/?q=linux+kernel+memory+management
Method: GET
```

The tool will:
1. Detect authentication is required
2. Open Chrome with password manager
3. Auto-fill saved credentials
4. Return the authenticated content

## 9. Still Not Working?

If none of the above solutions work:

1. **Check Claude Desktop logs** (if available)
2. **Try a simple test URL first**: `https://httpbin.org/get`
3. **Verify Python and dependencies**:
   ```bash
   pip list | grep -E "(mcp|selenium|httpx)"
   ```
4. **Create a minimal test**:
   ```bash
   python test_server_init.py
   ```

## 10. Success Indicators

When working correctly, you should see:
- ✅ Tool appears in Claude's available tools
- ✅ Requests to public URLs work immediately
- ✅ Requests to authenticated sites trigger Chrome browser
- ✅ Chrome auto-fills passwords when available
- ✅ Content is returned after authentication

The web_auth_mcp tool is designed to handle the complete authentication flow automatically, making it seamless to access protected content like O'Reilly books.
