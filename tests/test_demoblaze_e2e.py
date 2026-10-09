"""
DemoBlaze End-to-End Integration Test Suite - BDD Format
"""

import pytest
import time
from pages.demoblaze_home_page import DemoBlazeHomePage
from pages.demoblaze_cart_page import DemoBlazeCartPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoAlertPresentException


class TestDemoBlazeE2EIntegration:

    @pytest.fixture(autouse=True)
    def setup(self, driver, app_config):
        self.home_page = DemoBlazeHomePage(driver)
        self.cart_page = DemoBlazeCartPage(driver)
        self.test_user = {"username": "test", "password": "test"}
        self.customer_info = {
            "name": "John Doe",
            "country": "United States",
            "city": "New York",
            "credit_card": "4111111111111111",
            "month": "12",
            "year": "2025"
        }

    def _dismiss_alert_if_present(self, driver, timeout=3):
        try:
            WebDriverWait(driver, timeout).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            text = alert.text
            alert.accept()
            return text
        except (TimeoutException, NoAlertPresentException):
            return None

    def _login(self, driver):
        self.home_page.load_home_page()
        self.home_page.perform_login(
            username=self.test_user["username"],
            password=self.test_user["password"]
        )
        self._dismiss_alert_if_present(driver, timeout=2)
        WebDriverWait(driver, 15).until(lambda d: self.home_page.is_user_logged_in())

    def _add_product_from_category(self, driver, category, index=0):
        driver.get("https://www.demoblaze.com")
        self.home_page.wait_for_page_load()

        category_selector = {
            "phones": "a[onclick*='phone']",
            "laptops": "a[onclick*='notebook']",
            "monitors": "a[onclick*='monitor']"
        }[category]

        cat_link = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, category_selector))
        )
        cat_link.click()

        product_links = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".hrefch"))
        )
        assert len(product_links) > index

        products = self.home_page.get_product_list()
        product_name = products[index]["name"]

        product_links[index].click()

        add_to_cart_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[onclick*='addToCart']"))
        )
        add_to_cart_btn.click()

        alert_text = self._dismiss_alert_if_present(driver, timeout=10)
        assert alert_text is not None, f"{category} 加购未弹出 alert"

        time.sleep(3)
        return product_name

    def test_complete_single_product_purchase_flow(self, driver, app_config):
        self._login(driver)
        assert self.home_page.is_user_logged_in()

        selected_product = self._add_product_from_category(driver, "phones")

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        cart_items = self.cart_page.get_cart_items()
        assert len(cart_items) > 0, "购物车为空"

        self.cart_page.proceed_to_checkout()
        self.cart_page.fill_checkout_form(self.customer_info)

        purchase_success = self.cart_page.complete_purchase()
        assert purchase_success

        confirmation_details = self.cart_page.get_order_confirmation_details()
        assert confirmation_details["success"]
        order_number = self.cart_page.extract_order_number(confirmation_details)
        assert order_number

        driver.save_screenshot(f"screenshots/e2e_single_product_{time.strftime('%Y%m%d_%H%M%S')}.png")
        self.cart_page.confirm_success_message()

    def test_complete_multi_product_purchase_flow(self, driver, app_config):
        self._login(driver)
        assert self.home_page.is_user_logged_in()

        selected_products = []
        for category in ["phones", "laptops"]:
            product = self._add_product_from_category(driver, category)
            selected_products.append(product)

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        cart_items = self.cart_page.get_cart_items()
        assert len(cart_items) >= 2, f"购物车应至少 2 件，实际 {len(cart_items)} 件"

        self.cart_page.proceed_to_checkout()
        self.cart_page.fill_checkout_form(self.customer_info)

        purchase_success = self.cart_page.complete_purchase()
        assert purchase_success

        confirmation_details = self.cart_page.get_order_confirmation_details()
        assert confirmation_details["success"]
        order_number = self.cart_page.extract_order_number(confirmation_details)
        assert order_number

        driver.save_screenshot(f"screenshots/e2e_multi_product_{time.strftime('%Y%m%d_%H%M%S')}.png")
        self.cart_page.confirm_success_message()

    def test_complete_user_session_workflow(self, driver, app_config):
        self.home_page.load_home_page()
        assert self.home_page.verify_home_page_loaded()

        self.home_page.perform_login(
            username=self.test_user["username"],
            password=self.test_user["password"]
        )
        self._dismiss_alert_if_present(driver, timeout=2)
        WebDriverWait(driver, 15).until(lambda d: self.home_page.is_user_logged_in())

        categories_explored = []
        for category in ["phones", "laptops", "monitors"]:
            self.home_page.select_category(category)
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".hrefch"))
            )
            products = self.home_page.get_product_list()
            categories_explored.append(category)
            assert len(products) > 0

        selected_phone = self._add_product_from_category(driver, "phones")

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        cart_summary = self.cart_page.get_cart_summary()
        assert not cart_summary["is_empty"], "购物车为空，会话工作流失败"

        self.cart_page.proceed_to_checkout()
        session_customer_info = {
            "name": "Session User",
            "country": "United Kingdom",
            "city": "London",
            "credit_card": "4444333322221111",
            "month": "09",
            "year": "2026"
        }
        self.cart_page.fill_checkout_form(session_customer_info)

        purchase_success = self.cart_page.complete_purchase()
        assert purchase_success

        confirmation_details = self.cart_page.get_order_confirmation_details()
        order_number = self.cart_page.extract_order_number(confirmation_details)
        assert order_number

        self.cart_page.confirm_success_message()
        time.sleep(3)

        self._dismiss_alert_if_present(driver, timeout=2)
        try:
            logout_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "logout2"))
            )
            driver.execute_script("arguments[0].click();", logout_btn)
            time.sleep(3)
        except Exception:
            pass

        assert not self.home_page.is_user_logged_in()

        driver.save_screenshot(f"screenshots/e2e_complete_session_{time.strftime('%Y%m%d_%H%M%S')}.png")

    def test_single_product_purchase_with_verification(self, driver, app_config):
        self._login(driver)
        assert self.home_page.is_user_logged_in()

        selected_product = self._add_product_from_category(driver, "phones")

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        cart_items = self.cart_page.get_cart_items()
        assert len(cart_items) > 0
        assert any(selected_product.lower() in item["name"].lower() for item in cart_items)

        self.cart_page.proceed_to_checkout()
        self.cart_page.fill_checkout_form(self.customer_info)

        purchase_success = self.cart_page.complete_purchase()
        assert purchase_success

        confirmation_details = self.cart_page.get_order_confirmation_details()
        assert confirmation_details["success"]
        assert "thank you" in confirmation_details["title"].lower()

        order_number = self.cart_page.extract_order_number(confirmation_details)
        assert order_number and order_number.isdigit()

        driver.save_screenshot(f"screenshots/verified_purchase_{time.strftime('%Y%m%d_%H%M%S')}.png")
        self.cart_page.confirm_success_message()

    def test_two_different_products_purchase(self, driver, app_config):
        self._login(driver)
        assert self.home_page.is_user_logged_in()

        selected_products = []
        for category in ["phones", "laptops"]:
            product = self._add_product_from_category(driver, category)
            selected_products.append(product)

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        cart_items = self.cart_page.get_cart_items()
        assert len(cart_items) >= 2

        cart_names = [item["name"].lower() for item in cart_items]
        for product in selected_products:
            assert any(product.lower() in name for name in cart_names)

        self.cart_page.proceed_to_checkout()
        checkout_data = {
            "name": "Two Products Customer",
            "country": "Canada",
            "city": "Toronto",
            "credit_card": "5555444433332222",
            "month": "03",
            "year": "2027"
        }
        self.cart_page.fill_checkout_form(checkout_data)

        purchase_success = self.cart_page.complete_purchase()
        assert purchase_success

        confirmation_details = self.cart_page.get_order_confirmation_details()
        assert confirmation_details["success"]

        order_number = self.cart_page.extract_order_number(confirmation_details)
        assert order_number

        driver.save_screenshot(f"screenshots/two_products_purchase_{time.strftime('%Y%m%d_%H%M%S')}.png")
        self.cart_page.confirm_success_message()

    @pytest.fixture(scope="function", autouse=True)
    def cleanup_e2e(self, driver):
        yield
        try:
            self._dismiss_alert_if_present(driver, timeout=1)
            try:
                close_btn = driver.find_element(By.CSS_SELECTOR, "#orderModal .btn-secondary")
                if close_btn.is_displayed():
                    close_btn.click()
            except Exception:
                pass

            if "demoblaze.com" in driver.current_url:
                home_page = DemoBlazeHomePage(driver)
                if home_page.is_user_logged_in():
                    home_page.logout()
        except Exception:
            pass