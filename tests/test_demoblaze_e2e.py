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

    def _js_click(self, driver, element):
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", element)

    def _login(self, driver):
        self.home_page.load_home_page()
        self.home_page.perform_login(
            username=self.test_user["username"],
            password=self.test_user["password"]
        )
        self._dismiss_alert_if_present(driver, timeout=2)
        WebDriverWait(driver, 15).until(lambda d: self.home_page.is_user_logged_in())

    def _clear_cart(self, driver):
        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(2)
        for _ in range(15):
            delete_links = driver.find_elements(By.CSS_SELECTOR, "a[onclick*='deleteItem']")
            if not delete_links:
                break
            self._js_click(driver, delete_links[0])
            time.sleep(1.5)
        WebDriverWait(driver, 10).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "#tbodyid tr")) == 0
        )

    def _add_product_from_category(self, driver, category, index=0):
        driver.get("https://www.demoblaze.com")
        self.home_page.wait_for_page_load()

        category_selector = {
            "phones": "a[onclick*='phone']",
            "laptops": "a[onclick*='notebook']",
            "monitors": "a[onclick*='monitor']"
        }[category]

        cat_link = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, category_selector))
        )
        self._js_click(driver, cat_link)
        time.sleep(3)
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".hrefch"))
        )

        product_links = driver.find_elements(By.CSS_SELECTOR, ".hrefch")
        assert len(product_links) > index
        product_name = product_links[index].text.strip()

        self._js_click(driver, product_links[index])
        WebDriverWait(driver, 20).until(lambda d: "prod.html" in d.current_url)
        time.sleep(2)

        add_to_cart_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[onclick*='addToCart']"))
        )
        self._js_click(driver, add_to_cart_btn)

        alert_text = self._dismiss_alert_if_present(driver, timeout=15)
        assert alert_text is not None, f"{category} 加购未弹出 alert"

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        WebDriverWait(driver, 15).until(
            lambda d: any(product_name.lower() in item["name"].lower()
                          for item in self.cart_page.get_cart_items())
        )
        return product_name

    def test_complete_single_product_purchase_flow(self, driver, app_config):
        self._login(driver)
        self._clear_cart(driver)
        self._add_product_from_category(driver, "phones")

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        cart_items = self.cart_page.get_cart_items()
        assert len(cart_items) > 0

        self.cart_page.proceed_to_checkout()
        self.cart_page.fill_checkout_form(self.customer_info)
        assert self.cart_page.complete_purchase()

        details = self.cart_page.get_order_confirmation_details()
        assert details["success"]
        assert self.cart_page.extract_order_number(details)

        driver.save_screenshot(f"screenshots/e2e_single_product_{time.strftime('%Y%m%d_%H%M%S')}.png")
        self.cart_page.confirm_success_message()

    def test_complete_multi_product_purchase_flow(self, driver, app_config):
        self._login(driver)
        self._clear_cart(driver)

        for category in ["phones", "laptops"]:
            self._add_product_from_category(driver, category)

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        cart_items = self.cart_page.get_cart_items()
        assert len(cart_items) >= 2

        self.cart_page.proceed_to_checkout()
        self.cart_page.fill_checkout_form(self.customer_info)
        assert self.cart_page.complete_purchase()

        details = self.cart_page.get_order_confirmation_details()
        assert details["success"]
        assert self.cart_page.extract_order_number(details)

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

        for category in ["phones", "laptops", "monitors"]:
            self.home_page.select_category(category)
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".hrefch"))
            )
            assert len(self.home_page.get_product_list()) > 0

        self._clear_cart(driver)
        self._add_product_from_category(driver, "phones")

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        cart_summary = self.cart_page.get_cart_summary()
        assert not cart_summary["is_empty"]

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
        assert self.cart_page.complete_purchase()

        details = self.cart_page.get_order_confirmation_details()
        assert self.cart_page.extract_order_number(details)

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
        self._clear_cart(driver)
        selected_product = self._add_product_from_category(driver, "phones")

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        cart_items = self.cart_page.get_cart_items()
        assert len(cart_items) > 0
        assert any(selected_product.lower() in item["name"].lower() for item in cart_items)

        self.cart_page.proceed_to_checkout()
        self.cart_page.fill_checkout_form(self.customer_info)
        assert self.cart_page.complete_purchase()

        details = self.cart_page.get_order_confirmation_details()
        assert details["success"]
        assert "thank you" in details["title"].lower()
        assert self.cart_page.extract_order_number(details)

        driver.save_screenshot(f"screenshots/verified_purchase_{time.strftime('%Y%m%d_%H%M%S')}.png")
        self.cart_page.confirm_success_message()

    def test_two_different_products_purchase(self, driver, app_config):
        self._login(driver)
        self._clear_cart(driver)

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
        assert self.cart_page.complete_purchase()

        details = self.cart_page.get_order_confirmation_details()
        assert details["success"]
        assert self.cart_page.extract_order_number(details)

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