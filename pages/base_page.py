"""
Base Page Module

This module contains the BasePage class which serves as the foundation
for all page object classes in the framework.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementNotInteractableException,
    StaleElementReferenceException
)
import logging
import time
from typing import List, Optional, Tuple, Any


class BasePage:
    """
    Base page class that provides common functionality for all page objects.
    Implements Page Object Model (POM) design pattern.
    """
    
    def __init__(self, driver: webdriver.Remote, timeout: int = 10):
        """
        Initialize the base page with driver and timeout settings.
        
        Args:
            driver (webdriver.Remote): WebDriver instance
            timeout (int): Default timeout for explicit waits
        """
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(self.driver, self.timeout)
        self.actions = ActionChains(self.driver)
        self.logger = logging.getLogger(__name__)
    
    def open_url(self, url: str) -> None:
        """
        Navigate to a specific URL.
        
        Args:
            url (str): URL to navigate to
        """
        try:
            self.driver.get(url)
            self.logger.info(f"Navigated to URL: {url}")
        except Exception as e:
            self.logger.error(f"Failed to navigate to URL {url}: {str(e)}")
            raise
    
    def get_current_url(self) -> str:
        """
        Get the current page URL.
        
        Returns:
            str: Current page URL
        """
        return self.driver.current_url
    
    def get_page_title(self) -> str:
        """
        Get the current page title.
        
        Returns:
            str: Current page title
        """
        return self.driver.title
    
    def find_element(self, locator: Tuple[By, str], timeout: Optional[int] = None) -> Any:
        """
        Find a single element with explicit wait.
        
        Args:
            locator (Tuple[By, str]): Element locator (By strategy, locator value)
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            WebElement: Found element
            
        Raises:
            TimeoutException: If element is not found within timeout
        """
        wait_time = timeout or self.timeout
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located(locator)
            )
            self.logger.debug(f"Element found: {locator}")
            return element
        except TimeoutException:
            self.logger.error(f"Element not found within {wait_time} seconds: {locator}")
            raise
    
    def find_elements(self, locator: Tuple[By, str], timeout: Optional[int] = None) -> List[Any]:
        """
        Find multiple elements with explicit wait.
        
        Args:
            locator (Tuple[By, str]): Element locator (By strategy, locator value)
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            List[WebElement]: List of found elements
        """
        wait_time = timeout or self.timeout
        try:
            elements = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_all_elements_located(locator)
            )
            self.logger.debug(f"Elements found: {len(elements)} for locator: {locator}")
            return elements
        except TimeoutException:
            self.logger.error(f"Elements not found within {wait_time} seconds: {locator}")
            return []
    
    def wait_for_element_clickable(self, locator: Tuple[By, str], timeout: Optional[int] = None) -> Any:
        """
        Wait for element to be clickable.
        
        Args:
            locator (Tuple[By, str]): Element locator
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            WebElement: Clickable element
        """
        wait_time = timeout or self.timeout
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.element_to_be_clickable(locator)
            )
            return element
        except TimeoutException:
            self.logger.error(f"Element not clickable within {wait_time} seconds: {locator}")
            raise
    
    def wait_for_element_visible(self, locator: Tuple[By, str], timeout: Optional[int] = None) -> Any:
        """
        Wait for element to be visible.
        
        Args:
            locator (Tuple[By, str]): Element locator
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            WebElement: Visible element
        """
        wait_time = timeout or self.timeout
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located(locator)
            )
            return element
        except TimeoutException:
            self.logger.error(f"Element not visible within {wait_time} seconds: {locator}")
            raise
    
    def click_element(self, locator: Tuple[By, str], timeout: Optional[int] = None) -> None:
        """
        Click on an element with explicit wait.
        
        Args:
            locator (Tuple[By, str]): Element locator
            timeout (int, optional): Custom timeout for this operation
        """
        try:
            element = self.wait_for_element_clickable(locator, timeout)
            element.click()
            self.logger.debug(f"Clicked element: {locator}")
        except Exception as e:
            self.logger.error(f"Failed to click element {locator}: {str(e)}")
            raise
    
    def send_keys(self, locator: Tuple[By, str], text: str, clear_first: bool = True, 
                  timeout: Optional[int] = None) -> None:
        """
        Send keys to an element.
        
        Args:
            locator (Tuple[By, str]): Element locator
            text (str): Text to send
            clear_first (bool): Whether to clear the field first
            timeout (int, optional): Custom timeout for this operation
        """
        try:
            element = self.find_element(locator, timeout)
            if clear_first:
                element.clear()
            element.send_keys(text)
            self.logger.debug(f"Sent keys '{text}' to element: {locator}")
        except Exception as e:
            self.logger.error(f"Failed to send keys to element {locator}: {str(e)}")
            raise
    
    def get_text(self, locator: Tuple[By, str], timeout: Optional[int] = None) -> str:
        """
        Get text from an element.
        
        Args:
            locator (Tuple[By, str]): Element locator
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            str: Element text
        """
        try:
            element = self.find_element(locator, timeout)
            text = element.text
            self.logger.debug(f"Got text '{text}' from element: {locator}")
            return text
        except Exception as e:
            self.logger.error(f"Failed to get text from element {locator}: {str(e)}")
            raise
    
    def get_attribute(self, locator: Tuple[By, str], attribute_name: str, 
                     timeout: Optional[int] = None) -> str:
        """
        Get attribute value from an element.
        
        Args:
            locator (Tuple[By, str]): Element locator
            attribute_name (str): Name of the attribute
            timeout (int, optional): Custom timeout for this operation
            
        Returns:
            str: Attribute value
        """
        try:
            element = self.find_element(locator, timeout)
            value = element.get_attribute(attribute_name)
            self.logger.debug(f"Got attribute '{attribute_name}' = '{value}' from element: {locator}")
            return value or ""
        except Exception as e:
            self.logger.error(f"Failed to get attribute from element {locator}: {str(e)}")
            raise
    
    def is_element_present(self, locator: Tuple[By, str], timeout: int = 5) -> bool:
        """
        Check if element is present on the page.
        
        Args:
            locator (Tuple[By, str]): Element locator
            timeout (int): Timeout for the check
            
        Returns:
            bool: True if element is present, False otherwise
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False
    
    def is_element_visible(self, locator: Tuple[By, str], timeout: int = 5) -> bool:
        """
        Check if element is visible on the page.
        
        Args:
            locator (Tuple[By, str]): Element locator
            timeout (int): Timeout for the check
            
        Returns:
            bool: True if element is visible, False otherwise
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False
    
    def scroll_to_element(self, locator: Tuple[By, str], timeout: Optional[int] = None) -> None:
        """
        Scroll to an element.
        
        Args:
            locator (Tuple[By, str]): Element locator
            timeout (int, optional): Custom timeout for this operation
        """
        try:
            element = self.find_element(locator, timeout)
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)  # Allow time for scroll animation
            self.logger.debug(f"Scrolled to element: {locator}")
        except Exception as e:
            self.logger.error(f"Failed to scroll to element {locator}: {str(e)}")
            raise
    
    def hover_over_element(self, locator: Tuple[By, str], timeout: Optional[int] = None) -> None:
        """
        Hover over an element.
        
        Args:
            locator (Tuple[By, str]): Element locator
            timeout (int, optional): Custom timeout for this operation
        """
        try:
            element = self.find_element(locator, timeout)
            self.actions.move_to_element(element).perform()
            self.logger.debug(f"Hovered over element: {locator}")
        except Exception as e:
            self.logger.error(f"Failed to hover over element {locator}: {str(e)}")
            raise
    
    def select_dropdown_by_text(self, locator: Tuple[By, str], text: str, 
                               timeout: Optional[int] = None) -> None:
        """
        Select dropdown option by visible text.
        
        Args:
            locator (Tuple[By, str]): Dropdown element locator
            text (str): Visible text to select
            timeout (int, optional): Custom timeout for this operation
        """
        try:
            element = self.find_element(locator, timeout)
            select = Select(element)
            select.select_by_visible_text(text)
            self.logger.debug(f"Selected '{text}' from dropdown: {locator}")
        except Exception as e:
            self.logger.error(f"Failed to select '{text}' from dropdown {locator}: {str(e)}")
            raise
    
    def select_dropdown_by_value(self, locator: Tuple[By, str], value: str, 
                                timeout: Optional[int] = None) -> None:
        """
        Select dropdown option by value.
        
        Args:
            locator (Tuple[By, str]): Dropdown element locator
            value (str): Value to select
            timeout (int, optional): Custom timeout for this operation
        """
        try:
            element = self.find_element(locator, timeout)
            select = Select(element)
            select.select_by_value(value)
            self.logger.debug(f"Selected value '{value}' from dropdown: {locator}")
        except Exception as e:
            self.logger.error(f"Failed to select value '{value}' from dropdown {locator}: {str(e)}")
            raise
    
    def wait_for_page_load(self, timeout: Optional[int] = None) -> None:
        """
        Wait for page to load completely.
        
        Args:
            timeout (int, optional): Custom timeout for this operation
        """
        wait_time = timeout or self.timeout
        try:
            WebDriverWait(self.driver, wait_time).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            self.logger.debug("Page loaded successfully")
        except TimeoutException:
            self.logger.error(f"Page did not load within {wait_time} seconds")
            raise
    
    def take_screenshot(self, filename: str = None) -> str:
        """
        Take a screenshot of the current page.
        
        Args:
            filename (str, optional): Custom filename for the screenshot
            
        Returns:
            str: Path to the saved screenshot
        """
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        
        try:
            screenshot_path = f"screenshots/{filename}"
            self.driver.save_screenshot(screenshot_path)
            self.logger.info(f"Screenshot saved: {screenshot_path}")
            return screenshot_path
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {str(e)}")
            raise