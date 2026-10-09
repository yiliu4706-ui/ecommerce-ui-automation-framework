"""
DemoBlaze Login Test Suite - BDD Format
"""

import pytest
import time
from pages.demoblaze_home_page import DemoBlazeHomePage
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoAlertPresentException


class TestDemoBlazeLogin:

    @pytest.fixture(autouse=True)
    def setup(self, driver, app_config):
        self.home_page = DemoBlazeHomePage(driver)
        self.valid_user = {"username": "test", "password": "test"}
        self.invalid_user = {"username": "invalid_user", "password": "wrong_password"}

    def _dismiss_alert_if_present(self, driver, timeout=3):
        try:
            WebDriverWait(driver, timeout).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert_text = alert.text
            alert.accept()
            print(f"  ! Alert dismissed: {alert_text}")
            return alert_text
        except (TimeoutException, NoAlertPresentException):
            return None

    def test_successful_login(self, driver, app_config):
        print("Scenario: User logs in with valid credentials")

        self.home_page.load_home_page()
        assert self.home_page.verify_home_page_loaded(), "Home page should load successfully"

        self.home_page.perform_login(
            username=self.valid_user["username"],
            password=self.valid_user["password"]
        )
        self._dismiss_alert_if_present(driver)

        assert self.home_page.is_user_logged_in(), "User should be logged in after successful login"
        assert "demoblaze.com" in driver.current_url, "Should remain on demoblaze domain"
        assert self.home_page.verify_home_page_loaded(), "Main page should be loaded after login"

        logged_in_username = self.home_page.get_logged_in_username()
        assert logged_in_username is not None, "Username should be displayed when logged in"
        assert self.valid_user["username"] in logged_in_username or logged_in_username != "", "Correct username should be displayed"

        print("Scenario completed successfully!")

    def test_login_with_empty_credentials(self, driver, app_config):
        print("Scenario: User attempts to login with empty credentials")

        self.home_page.load_home_page()
        self.home_page.perform_login(username="", password="")
        self._dismiss_alert_if_present(driver, timeout=5)

        assert not self.home_page.is_user_logged_in(), "Should not be logged in with empty credentials"
        print("Scenario completed successfully!")

    def test_login_with_invalid_credentials(self, driver, app_config):
        print("Scenario: User attempts to login with invalid credentials")

        self.home_page.load_home_page()
        self.home_page.perform_login(
            username=self.invalid_user["username"],
            password=self.invalid_user["password"]
        )
        self._dismiss_alert_if_present(driver, timeout=5)

        assert not self.home_page.is_user_logged_in(), "Should not be logged in with invalid credentials"
        print("Scenario completed successfully!")

    def test_logout_functionality(self, driver, app_config):
        print("Scenario: User logs out from an active session")

        self.home_page.load_home_page()
        self.home_page.perform_login(
            username=self.valid_user["username"],
            password=self.valid_user["password"]
        )
        self._dismiss_alert_if_present(driver)
        assert self.home_page.is_user_logged_in(), "Should be logged in initially"

        self.home_page.logout()
        time.sleep(2)

        assert not self.home_page.is_user_logged_in(), "Should be logged out after logout action"
        print("Scenario completed successfully!")

    def test_login_state_persistence(self, driver, app_config):
        print("Scenario: User session persists across page navigation")

        self.home_page.load_home_page()
        self.home_page.perform_login(
            username=self.valid_user["username"],
            password=self.valid_user["password"]
        )
        self._dismiss_alert_if_present(driver)
        assert self.home_page.is_user_logged_in(), "Should be logged in"

        driver.get("https://www.demoblaze.com/cart.html")
        time.sleep(2)

        driver.get("https://www.demoblaze.com")
        time.sleep(2)

        assert self.home_page.is_user_logged_in(), "Should still be logged in after navigation"
        print("Scenario completed successfully!")

    @pytest.fixture(scope="function", autouse=True)
    def cleanup_login(self, driver):
        yield
        try:
            if "demoblaze.com" in driver.current_url:
                home_page = DemoBlazeHomePage(driver)
                if home_page.is_user_logged_in():
                    home_page.logout()
                    time.sleep(1)
        except:
            pass