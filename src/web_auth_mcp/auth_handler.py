"""Authentication handler with browser automation."""

import asyncio
import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import httpx
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


class AuthHandler:
    """Handles authentication detection and browser-based authentication flows."""
    
    def __init__(self):
        self.browser_timeout = int(os.getenv("BROWSER_TIMEOUT", "60"))
        self.headless = os.getenv("BROWSER_HEADLESS", "false").lower() == "true"
        self.window_size = os.getenv("BROWSER_WINDOW_SIZE", "1920x1080")
        self.use_default_profile = os.getenv("BROWSER_USE_DEFAULT_PROFILE", "false").lower() == "true"
        self.enable_password_manager = os.getenv("BROWSER_ENABLE_PASSWORD_MANAGER", "true").lower() == "true"
        self.auto_fill_passwords = os.getenv("BROWSER_AUTO_FILL_PASSWORDS", "true").lower() == "true"
        self.auth_cache = {}
        self.cache_ttl = int(os.getenv("AUTH_CACHE_TTL", "3600"))
    
    def needs_authentication(self, response: httpx.Response) -> bool:
        """
        Determine if a response indicates authentication is required.
        
        Args:
            response: HTTP response to check
            
        Returns:
            True if authentication is needed
        """
        # Check status codes
        if response.status_code in [401, 403]:
            logger.debug(f"Authentication required: status {response.status_code}")
            return True
        
        # Check for redirect to login page
        if response.status_code in [302, 303, 307, 308]:
            location = response.headers.get("location", "")
            if self._is_login_redirect(location):
                logger.debug(f"Authentication required: redirect to {location}")
                return True
        
        # Check response content for authentication indicators
        if self._contains_auth_indicators(response.text):
            logger.debug("Authentication required: content indicators")
            return True
        
        # Check WWW-Authenticate header
        if "www-authenticate" in response.headers:
            logger.debug("Authentication required: WWW-Authenticate header")
            return True
        
        return False
    
    def _is_login_redirect(self, location: str) -> bool:
        """Check if a redirect location is likely a login page."""
        login_patterns = [
            r"/login",
            r"/signin",
            r"/auth",
            r"/oauth",
            r"/sso",
            r"login\.",
            r"auth\.",
            r"accounts\."
        ]
        
        location_lower = location.lower()
        return any(re.search(pattern, location_lower) for pattern in login_patterns)
    
    def _contains_auth_indicators(self, content: str) -> bool:
        """Check if response content contains authentication indicators."""
        if not content:
            return False
        
        content_lower = content.lower()
        
        # Common authentication indicators
        auth_indicators = [
            "please log in",
            "please sign in",
            "authentication required",
            "unauthorized",
            "access denied",
            "login required",
            "session expired",
            "please authenticate",
            "sign in to continue",
            "membership required",
            "subscription required",
            "premium content",
            "member login"
        ]
        
        return any(indicator in content_lower for indicator in auth_indicators)
    
    async def authenticate(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Perform browser-based authentication for the given URL.
        
        Args:
            url: URL that requires authentication
            
        Returns:
            Authentication data (cookies, tokens, headers) or None if failed
        """
        domain = urlparse(url).netloc
        
        # Check cache first
        cache_key = f"auth_{domain}"
        if cache_key in self.auth_cache:
            cached_data, timestamp = self.auth_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"Using cached authentication for {domain}")
                return cached_data
        
        logger.info(f"Starting browser authentication for {domain}")
        
        # Set up Chrome options
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"--window-size={self.window_size}")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Configure password manager and autofill
        if self.enable_password_manager:
            # Enable password manager features
            chrome_options.add_argument("--enable-password-manager-reauthentication")
            chrome_options.add_argument("--password-store=basic")

            # Enable autofill if requested
            if self.auto_fill_passwords:
                chrome_options.add_experimental_option("prefs", {
                    "profile.password_manager_enabled": True,
                    "profile.default_content_setting_values.notifications": 2,  # Block notifications
                    "autofill.profile_enabled": True,
                    "autofill.credit_card_enabled": True,
                    "credentials_enable_service": True,
                    "credentials_enable_autosignin": True,
                })

        # Use default Chrome profile if requested
        if self.use_default_profile:
            import platform
            import os.path

            system = platform.system()
            if system == "Darwin":  # macOS
                profile_path = os.path.expanduser("~/Library/Application Support/Google/Chrome/Default")
            elif system == "Windows":
                profile_path = os.path.expanduser("~/AppData/Local/Google/Chrome/User Data/Default")
            else:  # Linux
                profile_path = os.path.expanduser("~/.config/google-chrome/Default")

            if os.path.exists(profile_path):
                chrome_options.add_argument(f"--user-data-dir={os.path.dirname(profile_path)}")
                chrome_options.add_argument("--profile-directory=Default")
                logger.info(f"Using Chrome profile: {profile_path}")
            else:
                logger.warning(f"Chrome profile not found at {profile_path}, using temporary profile")
        else:
            # Use a persistent temporary profile for password storage during session
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix="chrome_auth_")
            chrome_options.add_argument(f"--user-data-dir={temp_dir}")
            logger.debug(f"Using temporary Chrome profile: {temp_dir}")
        
        driver = None
        try:
            # Initialize WebDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Navigate to the URL
            driver.get(url)

            # Try to auto-fill login forms if enabled
            if self.auto_fill_passwords:
                await self._attempt_auto_login(driver)

            # Wait for user to complete authentication
            auth_data = await self._wait_for_authentication(driver, url)
            
            if auth_data:
                # Cache the authentication data
                self.auth_cache[cache_key] = (auth_data, time.time())
                logger.info(f"Authentication successful for {domain}")
                return auth_data
            else:
                logger.warning(f"Authentication failed for {domain}")
                return None
                
        except Exception as e:
            logger.error(f"Browser authentication error: {e}")
            return None
        finally:
            if driver:
                driver.quit()

    async def _attempt_auto_login(self, driver: webdriver.Chrome) -> bool:
        """
        Attempt to automatically fill and submit login forms using saved passwords.

        Args:
            driver: WebDriver instance

        Returns:
            True if auto-login was attempted, False otherwise
        """
        try:
            # Wait a moment for the page to load
            await asyncio.sleep(2)

            # Look for common login form patterns
            login_selectors = [
                # Username/email fields
                'input[type="email"]',
                'input[type="text"][name*="user"]',
                'input[type="text"][name*="email"]',
                'input[type="text"][name*="login"]',
                'input[id*="user"]',
                'input[id*="email"]',
                'input[id*="login"]',
                'input[name="username"]',
                'input[name="email"]',
                'input[class*="username"]',
                'input[class*="email"]'
            ]

            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[id*="password"]',
                'input[class*="password"]'
            ]

            # Find username/email field
            username_field = None
            for selector in login_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and elements[0].is_displayed():
                        username_field = elements[0]
                        break
                except:
                    continue

            # Find password field
            password_field = None
            for selector in password_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and elements[0].is_displayed():
                        password_field = elements[0]
                        break
                except:
                    continue

            if username_field and password_field:
                logger.info("Found login form, triggering autofill...")

                # Click on username field to trigger Chrome's autofill
                username_field.click()
                await asyncio.sleep(1)

                # Try to trigger autofill by simulating user interaction
                driver.execute_script("arguments[0].focus();", username_field)
                await asyncio.sleep(1)

                # Check if Chrome has filled the fields
                username_value = username_field.get_attribute('value')
                password_value = password_field.get_attribute('value')

                if username_value and password_value:
                    logger.info("Chrome autofill detected credentials, looking for submit button...")

                    # Look for submit button
                    submit_selectors = [
                        'button[type="submit"]',
                        'input[type="submit"]',
                        'button[name*="login"]',
                        'button[id*="login"]',
                        'button[class*="login"]',
                        'button[class*="submit"]',
                        'button:contains("Sign in")',
                        'button:contains("Log in")',
                        'button:contains("Login")'
                    ]

                    for selector in submit_selectors:
                        try:
                            submit_button = driver.find_element(By.CSS_SELECTOR, selector)
                            if submit_button.is_displayed() and submit_button.is_enabled():
                                logger.info("Submitting login form automatically...")
                                submit_button.click()
                                await asyncio.sleep(3)  # Wait for submission
                                return True
                        except:
                            continue

                    # If no submit button found, try pressing Enter on password field
                    try:
                        password_field.send_keys(Keys.RETURN)
                        await asyncio.sleep(3)
                        logger.info("Submitted login form using Enter key")
                        return True
                    except:
                        pass
                else:
                    logger.debug("Chrome autofill did not populate credentials")
            else:
                logger.debug("No login form detected on page")

            return False

        except Exception as e:
            logger.debug(f"Auto-login attempt failed: {e}")
            return False

    async def _wait_for_authentication(
        self, 
        driver: webdriver.Chrome, 
        original_url: str
    ) -> Optional[Dict[str, Any]]:
        """
        Wait for user to complete authentication and extract auth data.
        
        Args:
            driver: WebDriver instance
            original_url: Original URL that required authentication
            
        Returns:
            Authentication data or None
        """
        wait = WebDriverWait(driver, self.browser_timeout)
        
        try:
            # If not headless, show message to user
            if not self.headless:
                print(f"\n🔐 Please complete authentication in the browser window.")
                print(f"   Original URL: {original_url}")
                print(f"   Current URL: {driver.current_url}")
                print(f"   Waiting up to {self.browser_timeout} seconds...\n")
            
            # Wait for authentication completion indicators
            auth_completed = False
            start_time = time.time()
            last_url = driver.current_url
            stable_url_count = 0

            while not auth_completed and (time.time() - start_time) < self.browser_timeout:
                current_url = driver.current_url

                # Check if URL has been stable (not changing)
                if current_url == last_url:
                    stable_url_count += 1
                else:
                    stable_url_count = 0
                    last_url = current_url

                # Check multiple indicators for successful authentication
                auth_indicators = [
                    # Not on a login page
                    not self._is_login_redirect(current_url),
                    # URL has been stable for a few seconds
                    stable_url_count >= 3,
                    # Check for success indicators in page content
                    self._check_auth_success_indicators(driver),
                    # Check if we're on a content page (not login/error)
                    self._is_content_page(current_url)
                ]

                # If multiple indicators suggest success, verify by testing original URL
                if sum(auth_indicators) >= 2:
                    logger.debug("Authentication indicators suggest success, verifying...")

                    # Test access to original URL in a new tab to avoid disrupting current session
                    original_window = driver.current_window_handle
                    driver.execute_script("window.open('');")
                    driver.switch_to.window(driver.window_handles[-1])

                    try:
                        driver.get(original_url)
                        await asyncio.sleep(3)  # Wait for page load

                        test_url = driver.current_url
                        page_source = driver.page_source.lower()

                        # Check if we successfully accessed the content
                        success_indicators = [
                            not self._is_login_redirect(test_url),
                            not self._contains_auth_indicators(page_source),
                            len(page_source) > 1000,  # Substantial content
                            "content" in page_source or "article" in page_source
                        ]

                        if sum(success_indicators) >= 3:
                            auth_completed = True
                            logger.info("Authentication verification successful")
                            break
                        else:
                            logger.debug("Authentication verification failed, continuing to wait")

                    except Exception as e:
                        logger.debug(f"Error during authentication verification: {e}")
                    finally:
                        # Close test tab and return to original
                        driver.close()
                        driver.switch_to.window(original_window)

                await asyncio.sleep(1)
            
            if not auth_completed:
                logger.warning("Authentication timeout")
                return None

            # Extract authentication data
            auth_data = self._extract_auth_data(driver)

            # Show success message
            if not self.headless:
                print("✅ Authentication completed successfully!")
                print("   Closing browser and continuing with request...\n")

            return auth_data

        except Exception as e:
            logger.error(f"Error waiting for authentication: {e}")
            return None
    
    def _extract_auth_data(self, driver: webdriver.Chrome) -> Dict[str, Any]:
        """
        Extract authentication data from the browser session.
        
        Args:
            driver: WebDriver instance
            
        Returns:
            Dictionary containing authentication data
        """
        auth_data = {}
        
        # Extract cookies
        cookies = driver.get_cookies()
        if cookies:
            auth_data["cookies"] = {cookie["name"]: cookie["value"] for cookie in cookies}
        
        # Try to extract tokens from localStorage
        try:
            local_storage = driver.execute_script("return window.localStorage;")
            if local_storage:
                # Look for common token keys
                token_keys = ["access_token", "token", "auth_token", "jwt", "bearer_token"]
                for key in token_keys:
                    if key in local_storage:
                        auth_data[key] = local_storage[key]
        except Exception as e:
            logger.debug(f"Could not access localStorage: {e}")
        
        # Try to extract tokens from sessionStorage
        try:
            session_storage = driver.execute_script("return window.sessionStorage;")
            if session_storage:
                token_keys = ["access_token", "token", "auth_token", "jwt", "bearer_token"]
                for key in token_keys:
                    if key in session_storage:
                        auth_data[key] = session_storage[key]
        except Exception as e:
            logger.debug(f"Could not access sessionStorage: {e}")
        
        # Try to extract CSRF tokens from meta tags
        try:
            csrf_elements = driver.find_elements(By.CSS_SELECTOR, 'meta[name*="csrf"], meta[name*="token"]')
            for element in csrf_elements:
                name = element.get_attribute("name")
                content = element.get_attribute("content")
                if name and content and "csrf" in name.lower():
                    auth_data["csrf_token"] = content
                    break
        except Exception as e:
            logger.debug(f"Could not extract CSRF token: {e}")
        
        logger.debug(f"Extracted auth data keys: {list(auth_data.keys())}")
        return auth_data

    def _check_auth_success_indicators(self, driver) -> bool:
        """Check if the current page indicates successful authentication."""
        try:
            page_source = driver.page_source.lower()

            # Look for success indicators
            success_indicators = [
                "dashboard" in page_source,
                "welcome" in page_source,
                "profile" in page_source,
                "account" in page_source,
                "logout" in page_source,
                "sign out" in page_source,
                "my library" in page_source,
                "bookmarks" in page_source
            ]

            return any(indicator for indicator in success_indicators)

        except Exception as e:
            logger.debug(f"Error checking auth success indicators: {e}")
            return False

    def _is_content_page(self, url: str) -> bool:
        """Check if URL appears to be a content page rather than auth/error page."""
        if not url:
            return False

        url_lower = url.lower()

        # Content page indicators
        content_indicators = [
            "/library/" in url_lower,
            "/book/" in url_lower,
            "/chapter/" in url_lower,
            "/article/" in url_lower,
            "/view/" in url_lower,
            "/content/" in url_lower
        ]

        # Auth/error page indicators (should not be present)
        auth_indicators = [
            "/login" in url_lower,
            "/signin" in url_lower,
            "/auth" in url_lower,
            "/error" in url_lower,
            "/denied" in url_lower
        ]

        return any(content_indicators) and not any(auth_indicators)
