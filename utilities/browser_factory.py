"""
Browser Factory Module

This module contains the BrowserFactory class for managing browser instances
with support for Chrome and Firefox browsers.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
import logging
import os
import glob
from typing import Optional


class BrowserFactory:
    """Factory class for creating and managing browser instances."""
    
    @staticmethod
    def get_browser(browser_name: str = "chrome", headless: bool = False, 
                   window_size: tuple = (1920, 1080)) -> webdriver.Remote:
        """
        Create and return a browser instance based on the browser name.
        """
        browser_name = browser_name.lower()
        
        if browser_name == "chrome":
            return BrowserFactory._create_chrome_browser(headless, window_size)
        elif browser_name == "firefox":
            return BrowserFactory._create_firefox_browser(headless, window_size)
        else:
            raise ValueError(f"Unsupported browser: {browser_name}. "
                           "Supported browsers are 'chrome' and 'firefox'")
    
    @staticmethod
    def _create_chrome_browser(headless: bool = False, 
                              window_size: tuple = (1920, 1080)) -> webdriver.Chrome:
        """
        Create Chrome browser instance with optimized settings.
        """
        chrome_options = ChromeOptions()
        
        # Performance optimizations
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        
        # Window management
        chrome_options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
        
        # Headless mode
        if headless:
            chrome_options.add_argument("--headless")
        
        # Additional stability options
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--ignore-certificate-errors")
        
        # Remove automation indicators
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            # 直接使用 Selenium 4 内置的 Selenium Manager
            # 避开 webdriver-manager 返回 THIRD_PARTY_NOTICES 的路径Bug
            # 同时修复了原代码中因函数内 import os 导致的局部变量未定义报错
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.maximize_window()
            logging.info("Chrome browser initialized successfully")
            return driver
        except Exception as e:
            logging.error(f"Failed to initialize Chrome browser: {str(e)}")
            raise
    
    @staticmethod
    def _create_firefox_browser(headless: bool = False, 
                               window_size: tuple = (1920, 1080)) -> webdriver.Firefox:
        """
        Create Firefox browser instance with optimized settings for CI/CD environments.
        """
        firefox_options = FirefoxOptions()
        
        # Essential CI/CD environment settings
        firefox_options.add_argument("--no-sandbox")
        firefox_options.add_argument("--disable-dev-shm-usage")
        firefox_options.add_argument("--disable-gpu")
        firefox_options.add_argument("--disable-software-rasterizer")
        
        # Headless mode
        if headless or os.getenv('HEADLESS') == 'true' or os.getenv('CI') or os.getenv('MOZ_HEADLESS'):
            firefox_options.add_argument("--headless")
            logging.info("Firefox running in headless mode")
        
        # Window management
        firefox_options.add_argument(f"--width={window_size[0]}")
        firefox_options.add_argument(f"--height={window_size[1]}")
        
        # Enhanced marionette and connection settings for CI stability
        firefox_options.set_preference('marionette.log.level', 'Info')
        firefox_options.set_preference('remote.log.level', 'Info')
        firefox_options.set_preference('webdriver.log.level', 'info')
        
        # Critical timeout and connection settings
        firefox_options.set_preference('network.http.connection-timeout', 90)
        firefox_options.set_preference('network.http.connection-retry-timeout', 90)
        firefox_options.set_preference('network.http.response.timeout', 90)
        firefox_options.set_preference('dom.max_script_run_time', 0)
        firefox_options.set_preference('dom.max_chrome_script_run_time', 0)
        
        # Disable crash recovery and session restore
        firefox_options.set_preference('browser.sessionstore.resume_from_crash', False)
        firefox_options.set_preference('browser.sessionstore.resume_session_once', False)
        firefox_options.set_preference('browser.crashReports.unsubmittedCheck.enabled', False)
        firefox_options.set_preference('browser.crashReports.unsubmittedCheck.autoSubmit2', False)
        firefox_options.set_preference('browser.tabs.crashReporting.sendReport', False)
        
        # Performance optimizations
        firefox_options.set_preference("browser.cache.disk.enable", False)
        firefox_options.set_preference("browser.cache.memory.enable", False)
        firefox_options.set_preference("browser.cache.offline.enable", False)
        firefox_options.set_preference("network.http.use-cache", False)
        firefox_options.set_preference("permissions.default.image", 2)  # Block images for speed
        
        # Security and stability preferences for CI environments
        firefox_options.set_preference("security.tls.insecure_fallback_hosts", "localhost")
        firefox_options.set_preference("security.tls.hello_downgrade_check", False)
        firefox_options.set_preference("browser.safebrowsing.enabled", False)
        firefox_options.set_preference("browser.safebrowsing.malware.enabled", False)
        
        # Disable update checks and crash reporting
        firefox_options.set_preference("app.update.enabled", False)
        firefox_options.set_preference("app.update.auto", False)
        firefox_options.set_preference("toolkit.crashreporter.enabled", False)
        firefox_options.set_preference("datareporting.healthreport.uploadEnabled", False)
        
        # Media and notification preferences for CI stability
        firefox_options.set_preference("media.volume_scale", "0.0")
        firefox_options.set_preference("dom.push.enabled", False)
        firefox_options.set_preference("dom.webnotifications.enabled", False)
        
        # Profile directory settings for CI environments
        firefox_options.set_preference("browser.download.folderList", 2)
        firefox_options.set_preference("browser.download.manager.showWhenStarting", False)
        firefox_options.set_preference("browser.download.dir", "/tmp")
        
        try:
            # Create service with enhanced logging and timeout for CI environments
            log_path = os.path.join(os.getcwd(), "geckodriver.log") if os.getcwd().startswith('/') else "/tmp/geckodriver.log"
            
            service = FirefoxService(
                executable_path=GeckoDriverManager().install(),
                log_path=log_path
            )
            
            logging.info("Creating Firefox WebDriver instance with enhanced CI configuration...")
            
            # Create Firefox instance with multiple retry attempts
            max_retries = 3
            driver = None
            for attempt in range(max_retries):
                try:
                    driver = webdriver.Firefox(service=service, options=firefox_options)
                    break
                except Exception as e:
                    logging.warning(f"Firefox creation attempt {attempt + 1} failed: {e}")
                    if attempt == max_retries - 1:
                        raise
                    import time
                    time.sleep(3)  # Wait before retry
            
            # Set enhanced timeouts for stability in CI
            driver.set_page_load_timeout(90)
            driver.implicitly_wait(20)
            
            # Maximize window after creation with fallback
            try:
                driver.maximize_window()
            except Exception as e:
                logging.warning(f"Could not maximize Firefox window: {e}")
                try:
                    driver.set_window_size(window_size[0], window_size[1])
                except Exception as e2:
                    logging.warning(f"Could not set Firefox window size: {e2}")
            
            logging.info("Firefox browser initialized successfully for CI/CD environment")
            return driver
            
        except Exception as e:
            logging.error(f"Failed to initialize Firefox browser: {str(e)}")
            
            # Enhanced error logging and debugging information
            logging.error("Firefox initialization failed. Debugging information:")
            logging.error(f"Environment variables:")
            logging.error(f"  DISPLAY: {os.getenv('DISPLAY')}")
            logging.error(f"  MOZ_HEADLESS: {os.getenv('MOZ_HEADLESS')}")
            logging.error(f"  CI: {os.getenv('CI')}")
            logging.error(f"  HEADLESS: {os.getenv('HEADLESS')}")
            
            # Try to read and log GeckoDriver logs
            try:
                log_files = ["/tmp/geckodriver.log", "geckodriver.log"]
                for log_file in log_files:
                    if os.path.exists(log_file):
                        with open(log_file, 'r') as f:
                            logging.error(f"GeckoDriver logs from {log_file}:")
                            logging.error(f.read())
                        break
            except Exception as log_error:
                logging.error(f"Could not read GeckoDriver logs: {log_error}")
            
            logging.error("Common Firefox CI issues and solutions:")
            logging.error("1. Missing system dependencies (X11 libraries) - Check apt-get install")
            logging.error("2. Marionette port conflicts - Check for existing Firefox/GeckoDriver processes")
            logging.error("3. Insufficient display/Xvfb setup - Verify DISPLAY environment and Xvfb")
            logging.error("4. Firefox version compatibility with GeckoDriver - Update versions")
            logging.error("5. Permission issues - Check Firefox profile directory permissions")
            
            raise
    
    @staticmethod
    def quit_browser(driver: Optional[webdriver.Remote]) -> None:
        """
        Safely quit the browser instance.
        """
        if driver:
            try:
                driver.quit()
                logging.info("Browser closed successfully")
            except Exception as e:
                logging.error(f"Error while closing browser: {str(e)}")