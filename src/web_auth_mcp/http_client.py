"""HTTP client with authentication support."""

import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class HttpClient:
    """HTTP client that handles requests with authentication data."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True
        )
    
    async def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        auth_data: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """
        Make an HTTP request with optional authentication data.
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            body: Request body
            auth_data: Authentication data from browser session
            
        Returns:
            HTTP response
        """
        # Prepare headers
        request_headers = headers or {}
        
        # Apply authentication data if available
        if auth_data:
            request_headers.update(self._apply_auth_data(auth_data))
        
        # Prepare request parameters
        request_params = {
            "method": method.upper(),
            "url": url,
            "headers": request_headers
        }
        
        # Add body if provided
        if body:
            if method.upper() in ["POST", "PUT", "PATCH"]:
                request_params["content"] = body
            else:
                logger.warning(f"Body provided for {method} request, ignoring")
        
        # Add cookies if available in auth data
        if auth_data and "cookies" in auth_data:
            request_params["cookies"] = auth_data["cookies"]
        
        logger.debug(f"Making request: {method} {url}")
        
        try:
            response = await self.client.request(**request_params)
            logger.debug(f"Response: {response.status_code}")
            return response
            
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise
    
    def _apply_auth_data(self, auth_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Apply authentication data to request headers.
        
        Args:
            auth_data: Authentication data from browser session
            
        Returns:
            Headers to add to the request
        """
        headers = {}
        
        # Add Authorization header if token is available
        if "access_token" in auth_data:
            headers["Authorization"] = f"Bearer {auth_data['access_token']}"
        elif "token" in auth_data:
            headers["Authorization"] = f"Bearer {auth_data['token']}"
        
        # Add custom headers if available
        if "headers" in auth_data:
            headers.update(auth_data["headers"])
        
        # Add CSRF token if available
        if "csrf_token" in auth_data:
            headers["X-CSRF-Token"] = auth_data["csrf_token"]
        
        return headers
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
