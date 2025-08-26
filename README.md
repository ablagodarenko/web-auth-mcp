# Web Auth MCP Server

An MCP (Model Context Protocol) server that handles HTTP requests with automatic browser-based authentication.

## Features

- Execute HTTP requests through MCP tools
- Automatic detection of authentication requirements
- Browser-based authentication for OAuth flows and login forms
- Retry requests with captured authentication credentials
- Support for cookies, tokens, and session management

## Installation

### Quick Install

```bash
./install.sh
```

### Manual Install

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .
```

## Usage

### Running the MCP Server

```bash
# Activate virtual environment
source venv/bin/activate

# Run the server
web-auth-mcp
```

### MCP Client Configuration

Add to your MCP client configuration (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "web-auth-mcp": {
      "command": "python",
      "args": ["-m", "web_auth_mcp.server"],
      "env": {
        "BROWSER_HEADLESS": "false",
        "BROWSER_TIMEOUT": "60"
      }
    }
  }
}
```

### Testing

```bash
# Run tests
pytest

# Run example
python example_usage.py
```

## Configuration

Create a `.env` file with optional configuration:

```
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30
AUTH_CACHE_TTL=3600
```

## Tools

### http_request

Execute HTTP requests with automatic authentication handling.

**Parameters:**
- `url` (string): The URL to request
- `method` (string): HTTP method (GET, POST, PUT, DELETE, etc.)
- `headers` (object, optional): Request headers
- `body` (string, optional): Request body
- `auth_required` (boolean, optional): Force authentication flow

**Returns:**
- Response status, headers, and body
- Authentication details if authentication was performed

## How It Works

1. **HTTP Request**: The server receives an HTTP request through the MCP tool
2. **Authentication Detection**: Checks if authentication is required by examining:
   - HTTP status codes (401, 403)
   - Redirect responses to login pages
   - Content indicators ("please log in", etc.)
   - WWW-Authenticate headers
3. **Browser Authentication**: If authentication is needed:
   - Opens a browser window (headless or visible)
   - Navigates to the URL requiring authentication
   - Waits for user to complete authentication
   - Extracts authentication data (cookies, tokens, headers)
4. **Request Retry**: Retries the original request with authentication data
5. **Response**: Returns the final response with authentication status

## Supported Authentication Types

- **OAuth 2.0 flows** (Authorization Code, Implicit, etc.)
- **Form-based login** (username/password forms)
- **Cookie-based sessions**
- **Token-based authentication** (JWT, Bearer tokens)
- **CSRF protection** (automatic token extraction)

## Browser Automation

The server uses Selenium WebDriver with Chrome to handle authentication:
- Supports both headless and visible browser modes
- Automatically detects authentication completion
- Extracts tokens from localStorage, sessionStorage, and cookies
- Handles CSRF tokens from meta tags
- Configurable timeouts and window sizes
