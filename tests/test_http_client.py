"""Tests for HTTP client."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx

from web_auth_mcp.http_client import HttpClient


class TestHttpClient:
    """Test cases for HttpClient."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.http_client = HttpClient()
    
    @pytest.mark.asyncio
    async def test_request_basic(self):
        """Test basic HTTP request."""
        with patch.object(self.http_client.client, 'request') as mock_request:
            mock_response = Mock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_request.return_value = mock_response
            
            response = await self.http_client.request("GET", "https://example.com")
            
            assert response == mock_response
            mock_request.assert_called_once_with(
                method="GET",
                url="https://example.com",
                headers={}
            )
    
    @pytest.mark.asyncio
    async def test_request_with_headers(self):
        """Test HTTP request with custom headers."""
        with patch.object(self.http_client.client, 'request') as mock_request:
            mock_response = Mock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_request.return_value = mock_response

            headers = {"User-Agent": "Test"}
            await self.http_client.request("GET", "https://example.com", headers=headers)
            
            mock_request.assert_called_once_with(
                method="GET",
                url="https://example.com",
                headers=headers
            )
    
    @pytest.mark.asyncio
    async def test_request_with_body(self):
        """Test HTTP request with body."""
        with patch.object(self.http_client.client, 'request') as mock_request:
            mock_response = Mock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_request.return_value = mock_response

            body = '{"test": "data"}'
            await self.http_client.request("POST", "https://example.com", body=body)
            
            mock_request.assert_called_once_with(
                method="POST",
                url="https://example.com",
                headers={},
                content=body
            )
    
    @pytest.mark.asyncio
    async def test_request_with_auth_data(self):
        """Test HTTP request with authentication data."""
        with patch.object(self.http_client.client, 'request') as mock_request:
            mock_response = Mock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_request.return_value = mock_response

            auth_data = {
                "access_token": "test_token",
                "cookies": {"session": "abc123"}
            }

            await self.http_client.request("GET", "https://example.com", auth_data=auth_data)
            
            mock_request.assert_called_once_with(
                method="GET",
                url="https://example.com",
                headers={"Authorization": "Bearer test_token"},
                cookies={"session": "abc123"}
            )
    
    def test_apply_auth_data_access_token(self):
        """Test applying access token to headers."""
        auth_data = {"access_token": "test_token"}
        headers = self.http_client._apply_auth_data(auth_data)
        
        assert headers == {"Authorization": "Bearer test_token"}
    
    def test_apply_auth_data_csrf_token(self):
        """Test applying CSRF token to headers."""
        auth_data = {"csrf_token": "csrf123"}
        headers = self.http_client._apply_auth_data(auth_data)
        
        assert headers == {"X-CSRF-Token": "csrf123"}
    
    def test_apply_auth_data_custom_headers(self):
        """Test applying custom headers."""
        auth_data = {
            "headers": {"X-Custom": "value"},
            "access_token": "token123"
        }
        headers = self.http_client._apply_auth_data(auth_data)
        
        expected = {
            "Authorization": "Bearer token123",
            "X-Custom": "value"
        }
        assert headers == expected
