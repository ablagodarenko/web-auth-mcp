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
        self.browser_timeout = int(os.getenv("BROWSER_TIMEOUT", "300"))  # Increased to 5 minutes
        self.headless = os.getenv("BROWSER_HEADLESS", "false").lower() == "true"
        self.window_size = os.getenv("BROWSER_WINDOW_SIZE", "1920x1080")
        self.use_default_profile = os.getenv("BROWSER_USE_DEFAULT_PROFILE", "false").lower() == "true"
        self.enable_password_manager = os.getenv("BROWSER_ENABLE_PASSWORD_MANAGER", "true").lower() == "true"
        self.auto_fill_passwords = os.getenv("BROWSER_AUTO_FILL_PASSWORDS", "true").lower() == "true"
        self.auth_wait_time = int(os.getenv("AUTH_WAIT_TIME", "10"))  # Wait time for autofill
        self.manual_auth_timeout = int(os.getenv("MANUAL_AUTH_TIMEOUT", "180"))  # 3 minutes for manual auth
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

        # Check if Chrome is running and warn user
        if self.use_default_profile and self._check_chrome_running():
            logger.warning("Chrome is currently running. This may cause profile conflicts.")
            logger.info("If you encounter 'user data directory is already in use' errors:")
            logger.info("1. Close all Chrome windows and try again, or")
            logger.info("2. The system will automatically fall back to a temporary profile")

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

        # Configure Chrome profile with better conflict handling
        if self.use_default_profile:
            import platform
            import os.path
            import tempfile
            import shutil

            system = platform.system()
            if system == "Darwin":  # macOS
                base_profile_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
                profile_dir = "Default"
            elif system == "Windows":
                base_profile_path = os.path.expanduser("~/AppData/Local/Google/Chrome/User Data")
                profile_dir = "Default"
            else:  # Linux
                base_profile_path = os.path.expanduser("~/.config/google-chrome")
                profile_dir = "Default"

            original_profile = os.path.join(base_profile_path, profile_dir)

            if os.path.exists(original_profile):
                # Create a temporary copy of the profile to avoid conflicts
                temp_base = tempfile.mkdtemp(prefix="chrome_auth_profile_")
                temp_profile_dir = os.path.join(temp_base, "Default")

                try:
                    # Copy essential profile data (passwords, cookies, etc.)
                    os.makedirs(temp_profile_dir, exist_ok=True)

                    # Copy key files for password manager and cookies
                    key_files = [
                        "Login Data", "Login Data-journal",
                        "Cookies", "Cookies-journal",
                        "Web Data", "Web Data-journal",
                        "Preferences", "Local State"
                    ]

                    for file_name in key_files:
                        src_file = os.path.join(original_profile, file_name)
                        dst_file = os.path.join(temp_profile_dir, file_name)
                        if os.path.exists(src_file):
                            try:
                                if os.path.isfile(src_file):
                                    shutil.copy2(src_file, dst_file)
                                else:
                                    shutil.copytree(src_file, dst_file, dirs_exist_ok=True)
                            except (PermissionError, OSError) as e:
                                logger.debug(f"Could not copy {file_name}: {e}")

                    chrome_options.add_argument(f"--user-data-dir={temp_base}")
                    chrome_options.add_argument(f"--profile-directory=Default")
                    logger.info(f"Using temporary copy of Chrome profile: {temp_base}")

                except Exception as e:
                    logger.warning(f"Could not copy profile data: {e}, using fresh temporary profile")
                    chrome_options.add_argument(f"--user-data-dir={temp_base}")
            else:
                logger.warning(f"Chrome profile not found at {original_profile}, using temporary profile")
                temp_dir = tempfile.mkdtemp(prefix="chrome_auth_")
                chrome_options.add_argument(f"--user-data-dir={temp_dir}")
        else:
            # Use a persistent temporary profile for password storage during session
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix="chrome_auth_")
            chrome_options.add_argument(f"--user-data-dir={temp_dir}")
            logger.debug(f"Using temporary Chrome profile: {temp_dir}")

        # Add additional options to avoid conflicts
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-extensions-except")
        chrome_options.add_argument("--disable-component-extensions-with-background-pages")
        
        driver = None
        try:
            # Initialize WebDriver with better error handling
            service = Service(ChromeDriverManager().install())

            try:
                driver = webdriver.Chrome(service=service, options=chrome_options)
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            except Exception as e:
                if "user data directory is already in use" in str(e).lower():
                    logger.warning("Chrome profile in use, trying with fresh temporary profile...")

                    # Fall back to a completely fresh temporary profile
                    import tempfile
                    fresh_temp_dir = tempfile.mkdtemp(prefix="chrome_auth_fresh_")

                    # Create new options with fresh profile
                    fresh_options = Options()
                    if self.headless:
                        fresh_options.add_argument("--headless")
                    fresh_options.add_argument("--no-sandbox")
                    fresh_options.add_argument("--disable-dev-shm-usage")
                    fresh_options.add_argument(f"--window-size={self.window_size}")
                    fresh_options.add_argument("--disable-blink-features=AutomationControlled")
                    fresh_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                    fresh_options.add_experimental_option('useAutomationExtension', False)
                    fresh_options.add_argument(f"--user-data-dir={fresh_temp_dir}")
                    fresh_options.add_argument("--no-first-run")
                    fresh_options.add_argument("--disable-default-apps")

                    # Configure password manager for fresh profile
                    if self.enable_password_manager and self.auto_fill_passwords:
                        fresh_options.add_experimental_option("prefs", {
                            "profile.password_manager_enabled": True,
                            "profile.default_content_setting_values.notifications": 2,
                            "autofill.profile_enabled": True,
                            "credentials_enable_service": True,
                            "credentials_enable_autosignin": True,
                        })

                    driver = webdriver.Chrome(service=service, options=fresh_options)
                    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    logger.info(f"Using fresh temporary profile: {fresh_temp_dir}")
                else:
                    raise e
            
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

    def _check_chrome_running(self) -> bool:
        """
        Check if Chrome is currently running using system commands.

        Returns:
            True if Chrome processes are detected
        """
        try:
            import subprocess
            import platform

            system = platform.system()
            if system == "Darwin":  # macOS
                result = subprocess.run(['pgrep', '-f', 'Google Chrome'],
                                      capture_output=True, text=True)
                return result.returncode == 0
            elif system == "Linux":
                result = subprocess.run(['pgrep', '-f', 'chrome'],
                                      capture_output=True, text=True)
                return result.returncode == 0
            elif system == "Windows":
                result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq chrome.exe'],
                                      capture_output=True, text=True)
                return 'chrome.exe' in result.stdout.lower()
        except Exception as e:
            logger.debug(f"Error checking for Chrome processes: {e}")

        return False

    async def _attempt_auto_login(self, driver: webdriver.Chrome) -> bool:
        """
        Attempt to automatically fill and submit login forms using saved passwords.

        Args:
            driver: WebDriver instance

        Returns:
            True if auto-login was attempted, False otherwise
        """
        try:
            # Wait longer for the page to load completely
            logger.info("Waiting for page to load completely...")
            await asyncio.sleep(5)

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
                await asyncio.sleep(2)

                # Try to trigger autofill by simulating user interaction
                driver.execute_script("arguments[0].focus();", username_field)
                await asyncio.sleep(2)

                # Give Chrome more time to autofill
                logger.info(f"Waiting {self.auth_wait_time} seconds for Chrome autofill...")
                await asyncio.sleep(self.auth_wait_time)

                # Check if Chrome has filled the fields
                username_value = username_field.get_attribute('value')
                password_value = password_field.get_attribute('value')

                logger.info(f"Autofill check - Username: {'✅' if username_value else '❌'}, Password: {'✅' if password_value else '❌'}")

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
                print(f"\n🔐 Authentication Required")
                print(f"   Original URL: {original_url}")
                print(f"   Current URL: {driver.current_url}")
                print(f"   Browser timeout: {self.browser_timeout} seconds")
                print(f"   Manual auth timeout: {self.manual_auth_timeout} seconds")
                print(f"\n💡 What to do:")
                print(f"   1. If you have saved passwords: Wait for Chrome to autofill")
                print(f"   2. If no autofill: Manually enter your credentials")
                print(f"   3. The browser will stay open until authentication completes")
                print(f"   4. Don't close the browser - it will close automatically\n")
            
            # Wait for authentication completion indicators
            auth_completed = False
            start_time = time.time()
            last_url = driver.current_url
            stable_url_count = 0

            # Use different timeout for manual authentication
            effective_timeout = self.manual_auth_timeout if not self.auto_fill_passwords else self.browser_timeout

            while not auth_completed and (time.time() - start_time) < effective_timeout:
                current_url = driver.current_url

                # Check if URL has been stable (not changing)
                if current_url == last_url:
                    stable_url_count += 1
                else:
                    stable_url_count = 0
                    last_url = current_url
                    logger.info(f"URL changed to: {current_url}")

                # Check multiple indicators for successful authentication
                # Be more conservative - require more indicators to be sure
                auth_indicators = [
                    # Not on a login page
                    not self._is_login_redirect(current_url),
                    # URL has been stable for longer
                    stable_url_count >= 5,  # Increased from 3 to 5
                    # Check for success indicators in page content
                    self._check_auth_success_indicators(driver),
                    # Check if we're on a content page (not login/error)
                    self._is_content_page(current_url)
                ]

                # Require more confidence before considering authentication complete
                if sum(auth_indicators) >= 3:  # Increased threshold
                    logger.info("Strong authentication indicators detected, verifying...")

                    # Test access to original URL in a new tab to avoid disrupting current session
                    original_window = driver.current_window_handle
                    driver.execute_script("window.open('');")
                    driver.switch_to.window(driver.window_handles[-1])

                    try:
                        driver.get(original_url)
                        await asyncio.sleep(5)  # Wait longer for page load

                        test_url = driver.current_url
                        page_source = driver.page_source.lower()

                        # Check if we successfully accessed the content
                        success_indicators = [
                            not self._is_login_redirect(test_url),
                            not self._contains_auth_indicators(page_source),
                            len(page_source) > 1000,  # Substantial content
                            "content" in page_source or "article" in page_source or "search" in page_source
                        ]

                        if sum(success_indicators) >= 3:
                            auth_completed = True
                            logger.info("Authentication verification successful")
                            break
                        else:
                            logger.info("Authentication verification failed, continuing to wait...")
                            logger.debug(f"Success indicators: {sum(success_indicators)}/4")

                    except Exception as e:
                        logger.debug(f"Error during authentication verification: {e}")
                    finally:
                        # Close test tab and return to original
                        driver.close()
                        driver.switch_to.window(original_window)

                # Show progress every 30 seconds
                elapsed = time.time() - start_time
                if int(elapsed) % 30 == 0 and int(elapsed) > 0:
                    remaining = effective_timeout - elapsed
                    logger.info(f"Still waiting for authentication... {remaining:.0f} seconds remaining")

                await asyncio.sleep(2)  # Check less frequently
            
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
