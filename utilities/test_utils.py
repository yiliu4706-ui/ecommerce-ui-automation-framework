"""
Test Utilities Module

This module contains utility classes and functions for common test operations.
"""

import os
import time
import json
import yaml
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestUtils:
    """Utility class for common test operations."""
    
    @staticmethod
    def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
        """
        Setup logging configuration for the test framework.
        
        Args:
            log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR)
            log_file (str, optional): Log file path
        """
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        if log_file:
            logging.basicConfig(
                level=getattr(logging, log_level.upper()),
                format=log_format,
                handlers=[
                    logging.FileHandler(log_file),
                    logging.StreamHandler()
                ]
            )
        else:
            logging.basicConfig(
                level=getattr(logging, log_level.upper()),
                format=log_format
            )
        
        logging.info("Logging configured successfully")
    
    @staticmethod
    def load_test_data(file_path: str) -> Dict[str, Any]:
        """
        Load test data from JSON or YAML file.
        
        Args:
            file_path (str): Path to the test data file
            
        Returns:
            Dict[str, Any]: Test data dictionary
            
        Raises:
            FileNotFoundError: If file is not found
            ValueError: If file format is not supported
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Test data file not found: {file_path}")
        
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                if file_extension == '.json':
                    return json.load(file)
                elif file_extension in ['.yaml', '.yml']:
                    return yaml.safe_load(file)
                else:
                    raise ValueError(f"Unsupported file format: {file_extension}")
        except Exception as e:
            logging.error(f"Failed to load test data from {file_path}: {str(e)}")
            raise
    
    @staticmethod
    def create_directory_if_not_exists(directory_path: str) -> None:
        """
        Create directory if it doesn't exist.
        
        Args:
            directory_path (str): Path to the directory
        """
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            logging.info(f"Created directory: {directory_path}")
    
    @staticmethod
    def generate_timestamp(format_str: str = "%Y%m%d_%H%M%S") -> str:
        """
        Generate timestamp string.
        
        Args:
            format_str (str): Timestamp format string
            
        Returns:
            str: Formatted timestamp
        """
        return datetime.now().strftime(format_str)
    
    @staticmethod
    def wait_for_condition(condition_func, timeout: int = 10, poll_frequency: float = 0.5) -> bool:
        """
        Wait for a custom condition to be true.
        
        Args:
            condition_func: Function that returns boolean
            timeout (int): Maximum time to wait
            poll_frequency (float): How often to check the condition
            
        Returns:
            bool: True if condition met, False if timeout
        """
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            try:
                if condition_func():
                    return True
            except Exception:
                pass
            time.sleep(poll_frequency)
        
        return False


class ScreenshotHelper:
    """Helper class for managing screenshots during test execution."""
    
    def __init__(self, screenshots_dir: str = "screenshots"):
        """
        Initialize screenshot helper.
        
        Args:
            screenshots_dir (str): Directory to save screenshots
        """
        self.screenshots_dir = screenshots_dir
        TestUtils.create_directory_if_not_exists(screenshots_dir)
    
    def take_screenshot(self, driver: webdriver.Remote, test_name: str, 
                       status: str = "failed") -> str:
        """
        Take screenshot with descriptive filename.
        
        Args:
            driver (webdriver.Remote): WebDriver instance
            test_name (str): Name of the test
            status (str): Test status (passed, failed, etc.)
            
        Returns:
            str: Path to the screenshot file
        """
        timestamp = TestUtils.generate_timestamp()
        filename = f"{test_name}_{status}_{timestamp}.png"
        filepath = os.path.join(self.screenshots_dir, filename)
        
        try:
            driver.save_screenshot(filepath)
            logging.info(f"Screenshot saved: {filepath}")
            return filepath
        except Exception as e:
            logging.error(f"Failed to take screenshot: {str(e)}")
            return ""
    
    def cleanup_old_screenshots(self, days_old: int = 7) -> None:
        """
        Clean up screenshots older than specified days.
        
        Args:
            days_old (int): Delete screenshots older than this many days
        """
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        
        try:
            for filename in os.listdir(self.screenshots_dir):
                filepath = os.path.join(self.screenshots_dir, filename)
                if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff_time:
                    os.remove(filepath)
                    logging.info(f"Deleted old screenshot: {filename}")
        except Exception as e:
            logging.error(f"Failed to cleanup old screenshots: {str(e)}")


class WaitHelper:
    """Helper class for advanced waiting strategies."""
    
    def __init__(self, driver: webdriver.Remote, default_timeout: int = 10):
        """
        Initialize wait helper.
        
        Args:
            driver (webdriver.Remote): WebDriver instance
            default_timeout (int): Default timeout for waits
        """
        self.driver = driver
        self.default_timeout = default_timeout
        self.wait = WebDriverWait(driver, default_timeout)
    
    def wait_for_url_contains(self, text: str, timeout: Optional[int] = None) -> bool:
        """
        Wait for URL to contain specific text.
        
        Args:
            text (str): Text to wait for in URL
            timeout (int, optional): Custom timeout
            
        Returns:
            bool: True if condition met within timeout
        """
        wait_time = timeout or self.default_timeout
        try:
            WebDriverWait(self.driver, wait_time).until(EC.url_contains(text))
            return True
        except Exception:
            return False
    
    def wait_for_title_contains(self, text: str, timeout: Optional[int] = None) -> bool:
        """
        Wait for page title to contain specific text.
        
        Args:
            text (str): Text to wait for in title
            timeout (int, optional): Custom timeout
            
        Returns:
            bool: True if condition met within timeout
        """
        wait_time = timeout or self.default_timeout
        try:
            WebDriverWait(self.driver, wait_time).until(EC.title_contains(text))
            return True
        except Exception:
            return False
    
    def wait_for_page_ready(self, timeout: Optional[int] = None) -> bool:
        """
        Wait for page to be in ready state.
        
        Args:
            timeout (int, optional): Custom timeout
            
        Returns:
            bool: True if page is ready within timeout
        """
        wait_time = timeout or self.default_timeout
        try:
            WebDriverWait(self.driver, wait_time).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            return True
        except Exception:
            return False
    
    def wait_for_ajax_complete(self, timeout: Optional[int] = None) -> bool:
        """
        Wait for jQuery AJAX calls to complete.
        
        Args:
            timeout (int, optional): Custom timeout
            
        Returns:
            bool: True if AJAX calls completed within timeout
        """
        wait_time = timeout or self.default_timeout
        try:
            WebDriverWait(self.driver, wait_time).until(
                lambda driver: driver.execute_script("return jQuery.active == 0")
            )
            return True
        except Exception:
            return False


class TestDataGenerator:
    """Helper class for generating test data."""
    
    @staticmethod
    def generate_email(domain: str = "testmail.com") -> str:
        """
        Generate a unique email address.
        
        Args:
            domain (str): Email domain
            
        Returns:
            str: Generated email address
        """
        timestamp = TestUtils.generate_timestamp()
        return f"test_user_{timestamp}@{domain}"
    
    @staticmethod
    def generate_phone_number(country_code: str = "+1") -> str:
        """
        Generate a phone number.
        
        Args:
            country_code (str): Country code prefix
            
        Returns:
            str: Generated phone number
        """
        import random
        area_code = random.randint(100, 999)
        exchange = random.randint(100, 999)
        number = random.randint(1000, 9999)
        return f"{country_code} ({area_code}) {exchange}-{number}"
    
    @staticmethod
    def generate_text(length: int = 10) -> str:
        """
        Generate random text string.
        
        Args:
            length (int): Length of the text
            
        Returns:
            str: Generated text
        """
        import string
        import random
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for _ in range(length))