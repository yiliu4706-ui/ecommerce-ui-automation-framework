"""
DemoBlaze Checkout Test Suite - BDD Format
"""

import pytest
import time
from pages.demoblaze_home_page import DemoBlazeHomePage
from pages.demoblaze_cart_page import DemoBlazeCartPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoAlertPresentException, StaleElementReferenceException


class TestDemoBlazeCheckout:

    @pytest.fixture(autouse=True)
    def setup(self, driver, app_config):
        self.home_page = DemoBlazeHomePage(driver)
        self.cart_page = DemoBlazeCartPage(driver)
        self.test_user = {"username": "test", "password": "test"}
        self.valid_customer_info = {
            "name": "Test Customer",
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
        time.sleep(3)
        for attempt in range(20):
            try:
                delete_links = driver.find_elements(By.CSS_SELECTOR, "a[onclick*='deleteItem']")
                if not delete_links:
                    break
                self._js_click(driver, delete_links[0])
                time.sleep(1.5)
            except StaleElementReferenceException:
                time.sleep(1)
                continue
            except Exception:
                time.sleep(1)
                continue
        time.sleep(2)

    def _add_product_to_cart(self, driver, category="phones", index=0):
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
        time.sleep(3)
        return product_name

    def setup_cart_with_product(self, driver):
        self._clear_cart(driver)
        self._add_product_to_cart(driver, "phones", 0)
        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)
        cart_items = self.cart_page.get_cart_items()
        assert len(cart_items) > 0, "购物车为空，加购流程失败"

    def test_checkout_modal_opening(self, driver, app_config):
        self._login(driver)
        self.setup_cart_with_product(driver)
        self.cart_page.proceed_to_checkout()
        modal = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "orderModal"))
        )
        assert modal.is_displayed()
        try:
            self._js_click(driver, driver.find_element(By.CSS_SELECTOR, "#orderModal .btn-secondary"))
        except Exception:
            pass

    def test_checkout_form_fields_validation(self, driver, app_config):
        self._login(driver)
        self.setup_cart_with_product(driver)
        self.cart_page.proceed_to_checkout()
        for field_id in ["name", "country", "city", "card", "month", "year"]:
            field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, field_id))
            )
            assert field.is_displayed()
        try:
            self._js_click(driver, driver.find_element(By.CSS_SELECTOR, "#orderModal .btn-secondary"))
        except Exception:
            pass

    def test_successful_checkout_with_valid_data(self, driver, app_config):
        self._login(driver)
        self.setup_cart_with_product(driver)
        self.cart_page.proceed_to_checkout()
        self.cart_page.fill_checkout_form(self.valid_customer_info)
        assert self.cart_page.complete_purchase()
        details = self.cart_page.get_order_confirmation_details()
        assert details["success"]
        assert "thank you" in details["title"].lower()
        order_number = self.cart_page.extract_order_number(details)
        assert order_number and order_number.isdigit()
        self.cart_page.confirm_success_message()

    def test_checkout_form_data_entry(self, driver, app_config):
        self._login(driver)
        self.setup_cart_with_product(driver)
        self.cart_page.proceed_to_checkout()
        test_data = {
            "name": "John Doe",
            "country": "Canada",
            "city": "Toronto",
            "credit_card": "5555444433332222",
            "month": "03",
            "year": "2027"
        }
        self.cart_page.fill_checkout_form(test_data)
        assert driver.find_element(By.ID, "name").get_attribute("value") == test_data["name"]
        assert driver.find_element(By.ID, "country").get_attribute("value") == test_data["country"]
        try:
            self._js_click(driver, driver.find_element(By.CSS_SELECTOR, "#orderModal .btn-secondary"))
        except Exception:
            pass

    def test_checkout_with_empty_form(self, driver, app_config):
        self._login(driver)
        self.setup_cart_with_product(driver)
        self.cart_page.proceed_to_checkout()
        purchase_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[onclick='purchaseOrder()']"))
        )
        purchase_btn.click()
        time.sleep(2)
        alert_text = self._dismiss_alert_if_present(driver, timeout=5)
        assert alert_text is not None
        assert "fill out" in alert_text.lower() or "please" in alert_text.lower()
        try:
            self._js_click(driver, driver.find_element(By.CSS_SELECTOR, "#orderModal .btn-secondary"))
        except Exception:
            pass

    def test_checkout_with_different_customer_data(self, driver, app_config):
        self._login(driver)
        customer_variations = [
            {"name": "Alice Smith", "country": "United Kingdom", "city": "London",
             "credit_card": "4444555566667777", "month": "06", "year": "2026"},
            {"name": "Bob Johnson", "country": "Australia", "city": "Sydney",
             "credit_card": "5555666677778888", "month": "09", "year": "2027"}
        ]
        successful_orders = []
        for i, customer_data in enumerate(customer_variations, 1):
            self._dismiss_alert_if_present(driver, timeout=1)
            try:
                confirm_btn = driver.find_element(By.CSS_SELECTOR, ".confirm")
                if confirm_btn.is_displayed():
                    confirm_btn.click()
                    time.sleep(2)
            except Exception:
                pass
            self.setup_cart_with_product(driver)
            self.cart_page.proceed_to_checkout()
            self.cart_page.fill_checkout_form(customer_data)
            assert self.cart_page.complete_purchase(), f"第{i}个客户下单失败"
            details = self.cart_page.get_order_confirmation_details()
            order_number = self.cart_page.extract_order_number(details)
            assert order_number
            successful_orders.append(order_number)
            self.cart_page.confirm_success_message()
            time.sleep(2)
        assert len(set(successful_orders)) == len(successful_orders)

    def test_checkout_order_confirmation_details(self, driver, app_config):
        self._login(driver)
        self.setup_cart_with_product(driver)
        self.cart_page.proceed_to_checkout()
        self.cart_page.fill_checkout_form(self.valid_customer_info)
        self.cart_page.complete_purchase()
        details = self.cart_page.get_order_confirmation_details()
        assert self.valid_customer_info["name"] in details["details"]
        assert self.valid_customer_info["credit_card"] in details["details"]
        assert "Amount:" in details["details"] or "USD" in details["details"]
        assert self.cart_page.extract_order_number(details)
        self.cart_page.confirm_success_message()

    def test_checkout_process_screenshot_capture(self, driver, app_config):
        self._login(driver)
        self.setup_cart_with_product(driver)
        driver.save_screenshot("screenshots/checkout_cart_before.png")
        self.cart_page.proceed_to_checkout()
        driver.save_screenshot("screenshots/checkout_modal.png")
        self.cart_page.fill_checkout_form(self.valid_customer_info)
        driver.save_screenshot("screenshots/checkout_form_filled.png")
        self.cart_page.complete_purchase()
        driver.save_screenshot(f"screenshots/checkout_confirmation_{time.strftime('%Y%m%d_%H%M%S')}.png")
        details = self.cart_page.get_order_confirmation_details()
        assert self.cart_page.extract_order_number(details)
        self.cart_page.confirm_success_message()

    @pytest.fixture(scope="function", autouse=True)
    def cleanup_checkout(self, driver):
        yield
        try:
            self._dismiss_alert_if_present(driver, timeout=1)
            try:
                confirm_btn = driver.find_element(By.CSS_SELECTOR, ".confirm")
                if confirm_btn.is_displayed():
                    confirm_btn.click()
                    time.sleep(1)
            except Exception:
                pass
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
                    time.sleep(1)
        except Exception:
            pass