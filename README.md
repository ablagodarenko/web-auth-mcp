# Web Auth MCP Server

An MCP (Model Context Protocol) server that handles HTTP requests with automatic browser-based authentication.

## Features

- Execute HTTP requests through MCP tools
- Automatic detection of authentication requirements
- Browser-based authentication for OAuth flows and login forms
- **Chrome password manager integration** - automatically use saved passwords
- **Automatic form filling and submission** - streamlined login process
- Retry requests with captured authentication credentials
- Support for cookies, tokens, and session management
- Configurable browser profiles (system or temporary)

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

#### Stdio Mode (Default)
```bash
# Activate virtual environment
source venv/bin/activate

# Run the server with stdio transport
web-auth-mcp
```

#### HTTP/SSE Mode
```bash
# Activate virtual environment
source venv/bin/activate

# Run the server with HTTP transport on default port 8080
web-auth-mcp-http

# Or specify custom host and port
web-auth-mcp --http 0.0.0.0 8080

# Access the server at: http://localhost:8080/sse
```

### MCP Client Configuration

#### For Stdio Transport
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

#### For HTTP/SSE Transport
Configure your MCP client to connect to the HTTP endpoint:

```json
{
  "mcpServers": {
    "web-auth-mcp": {
      "url": "http://localhost:8080/sse",
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
# Browser configuration
BROWSER_HEADLESS=false
BROWSER_TIMEOUT=60
BROWSER_WINDOW_SIZE=1920x1080

# Chrome Password Manager (NEW!)
BROWSER_USE_DEFAULT_PROFILE=false
BROWSER_ENABLE_PASSWORD_MANAGER=true
BROWSER_AUTO_FILL_PASSWORDS=true

# Authentication configuration
AUTH_CACHE_TTL=3600
AUTH_RETRY_ATTEMPTS=3

# Authentication timing (fixes quick closing issue)
BROWSER_TIMEOUT=300
MANUAL_AUTH_TIMEOUT=180
AUTH_WAIT_TIME=10

# Logging configuration
LOG_LEVEL=INFO
SUPPRESS_MCP_WARNINGS=true
```

## Chrome Password Manager Integration

The server now supports using Chrome's saved passwords for automatic authentication:

### Quick Start

1. **Enable password manager features:**
   ```bash
   export BROWSER_ENABLE_PASSWORD_MANAGER=true
   export BROWSER_AUTO_FILL_PASSWORDS=true
   export BROWSER_HEADLESS=false
   ```

2. **Choose profile mode:**
   - **System Profile** (access to all saved passwords):
     ```bash
     export BROWSER_USE_DEFAULT_PROFILE=true
     ```
   - **Temporary Profile** (session-only passwords):
     ```bash
     export BROWSER_USE_DEFAULT_PROFILE=false
     ```

3. **Test the functionality:**
   ```bash
   python test_password_manager.py
   python example_password_manager.py
   ```

### How It Works

1. **Automatic Detection**: Detects login forms on web pages
2. **Chrome Autofill**: Triggers Chrome's built-in password autofill
3. **Form Submission**: Automatically submits forms when credentials are found
4. **Fallback**: Manual interaction available if auto-fill fails

### Supported Login Forms

- Standard HTML login forms
- Email/username + password combinations
- Common form field patterns and selectors
- Various submit button types

For detailed documentation, see [CHROME_PASSWORD_MANAGER.md](CHROME_PASSWORD_MANAGER.md).

## Troubleshooting

### MCP Initialization Warnings

You may see warnings like:
```
WARNING - Failed to validate request: Received request before initialization was complete
```

**This is normal MCP protocol behavior** and doesn't affect functionality. These warnings occur during the client-server handshake when requests are received before initialization completes.

**To suppress these warnings:**
```bash
export SUPPRESS_MCP_WARNINGS=true
# or add to your .env file:
echo "SUPPRESS_MCP_WARNINGS=true" >> .env
```

The server will continue to function correctly regardless of these warnings.

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

## Troubleshooting

### Browser Issues

**Browser doesn't open:**
- Check that `BROWSER_HEADLESS=false` (default)
- Ensure Chrome is installed on your system

**Browser opens but doesn't close:**
- The server detects authentication completion automatically
- Wait for the success message: "✅ Authentication completed successfully!"
- If stuck, check that you've completed the login process fully

**Authentication timeout:**
- Increase timeout: `BROWSER_TIMEOUT=120` (default: 60 seconds)
- Ensure you complete authentication within the timeout period

### Common Solutions

```bash
# Force visible browser
export BROWSER_HEADLESS=false

# Increase timeout
export BROWSER_TIMEOUT=120

# Debug mode
export LOG_LEVEL=DEBUG
```
