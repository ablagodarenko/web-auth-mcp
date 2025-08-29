"""Configuration management for Web Auth MCP Server."""

import os
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class BrowserConfig(BaseModel):
    """Browser configuration settings."""
    headless: bool = Field(default=True, description="Run browser in headless mode")
    timeout: int = Field(default=30, description="Browser timeout in seconds")
    window_size: str = Field(default="1920x1080", description="Browser window size")
    use_default_profile: bool = Field(default=False, description="Use system Chrome profile with saved passwords")
    enable_password_manager: bool = Field(default=True, description="Enable Chrome password manager features")
    auto_fill_passwords: bool = Field(default=True, description="Automatically fill login forms with saved passwords")


class AuthConfig(BaseModel):
    """Authentication configuration settings."""
    cache_ttl: int = Field(default=3600, description="Authentication cache TTL in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    login_patterns: List[str] = Field(
        default=[
            r"/login",
            r"/signin", 
            r"/auth",
            r"/oauth",
            r"/sso",
            r"login\.",
            r"auth\.",
            r"accounts\."
        ],
        description="Regex patterns for login page detection"
    )
    auth_indicators: List[str] = Field(
        default=[
            "please log in",
            "please sign in", 
            "authentication required",
            "unauthorized",
            "access denied",
            "login required",
            "session expired",
            "please authenticate"
        ],
        description="Text indicators for authentication requirements"
    )


class ServerConfig(BaseModel):
    """Server configuration settings."""
    log_level: str = Field(default="INFO", description="Logging level")
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)


def load_config() -> ServerConfig:
    """Load configuration from environment variables."""
    return ServerConfig(
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        browser=BrowserConfig(
            headless=os.getenv("BROWSER_HEADLESS", "true").lower() == "true",
            timeout=int(os.getenv("BROWSER_TIMEOUT", "30")),
            window_size=os.getenv("BROWSER_WINDOW_SIZE", "1920x1080"),
            use_default_profile=os.getenv("BROWSER_USE_DEFAULT_PROFILE", "false").lower() == "true",
            enable_password_manager=os.getenv("BROWSER_ENABLE_PASSWORD_MANAGER", "true").lower() == "true",
            auto_fill_passwords=os.getenv("BROWSER_AUTO_FILL_PASSWORDS", "true").lower() == "true"
        ),
        auth=AuthConfig(
            cache_ttl=int(os.getenv("AUTH_CACHE_TTL", "3600")),
            retry_attempts=int(os.getenv("AUTH_RETRY_ATTEMPTS", "3"))
        )
    )
