"""Tests for authentication handler."""

import pytest
from unittest.mock import Mock, patch
import httpx

from web_auth_mcp.auth_handler import AuthHandler


class TestAuthHandler:
    """Test cases for AuthHandler."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.auth_handler = AuthHandler()
    
    def test_needs_authentication_401(self):
        """Test authentication detection for 401 status."""
        response = Mock(spec=httpx.Response)
        response.status_code = 401
        response.headers = {}
        response.text = ""
        
        assert self.auth_handler.needs_authentication(response) is True
    
    def test_needs_authentication_403(self):
        """Test authentication detection for 403 status."""
        response = Mock(spec=httpx.Response)
        response.status_code = 403
        response.headers = {}
        response.text = ""
        
        assert self.auth_handler.needs_authentication(response) is True
    
    def test_needs_authentication_redirect_to_login(self):
        """Test authentication detection for login redirect."""
        response = Mock(spec=httpx.Response)
        response.status_code = 302
        response.headers = {"location": "https://example.com/login"}
        response.text = ""
        
        assert self.auth_handler.needs_authentication(response) is True
    
    def test_needs_authentication_content_indicators(self):
        """Test authentication detection from content."""
        response = Mock(spec=httpx.Response)
        response.status_code = 200
        response.headers = {}
        response.text = "Please log in to continue"
        
        assert self.auth_handler.needs_authentication(response) is True
    
    def test_needs_authentication_www_authenticate_header(self):
        """Test authentication detection from WWW-Authenticate header."""
        response = Mock(spec=httpx.Response)
        response.status_code = 200
        response.headers = {"www-authenticate": "Bearer"}
        response.text = ""
        
        assert self.auth_handler.needs_authentication(response) is True
    
    def test_no_authentication_needed(self):
        """Test when no authentication is needed."""
        response = Mock(spec=httpx.Response)
        response.status_code = 200
        response.headers = {}
        response.text = "Welcome to the page"
        
        assert self.auth_handler.needs_authentication(response) is False
    
    def test_is_login_redirect(self):
        """Test login redirect detection."""
        test_cases = [
            ("https://example.com/login", True),
            ("https://example.com/signin", True),
            ("https://example.com/auth", True),
            ("https://login.example.com", True),
            ("https://auth.example.com", True),
            ("https://example.com/dashboard", False),
            ("https://example.com/home", False),
        ]
        
        for url, expected in test_cases:
            assert self.auth_handler._is_login_redirect(url) == expected
    
    def test_contains_auth_indicators(self):
        """Test authentication indicator detection in content."""
        test_cases = [
            ("Please log in to continue", True),
            ("Authentication required", True),
            ("Unauthorized access", True),
            ("Welcome to our site", False),
            ("", False),
        ]
        
        for content, expected in test_cases:
            assert self.auth_handler._contains_auth_indicators(content) == expected
