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
from selenium.common.exceptions import TimeoutException, NoAlertPresentException


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

    def _close_order_modal_if_present(self, driver):
        try:
            close_btn = driver.find_element(By.CSS_SELECTOR, "#orderModal .btn-secondary")
            if close_btn.is_displayed():
                close_btn.click()
                time.sleep(1)
        except Exception:
            pass

    def _add_product_to_cart(self, driver, category="phones", index=0):
        """稳健加购：等待商品列表 → 点击商品 → 点击加购 → 断言 alert → 等同步"""
        driver.get("https://www.demoblaze.com")
        self.home_page.wait_for_page_load()

        category_selector = {
            "phones": "a[onclick*='phone']",
            "laptops": "a[onclick*='notebook']",
            "monitors": "a[onclick*='monitor']"
        }[category]

        category_link = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, category_selector))
        )
        category_link.click()

        # 关键等待：商品列表必须出现
        product_links = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".hrefch"))
        )
        assert len(product_links) > 0, f"{category} 分类商品列表为空"
        product_links[index].click()

        # 等待商品详情页的加购按钮
        add_to_cart_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[onclick*='addToCart']"))
        )
        add_to_cart_btn.click()

        # 关键断言：alert 必须出现，否则加购失败
        alert_text = self._dismiss_alert_if_present(driver, timeout=10)
        assert alert_text is not None, "点击加购后未出现 alert，商品未加入"
        assert "added" in alert_text.lower(), f"alert 内容异常: {alert_text}"

        # 等服务端同步
        time.sleep(3)

    def _ensure_clean_session(self, driver):
        self.home_page.load_home_page()
        time.sleep(1)
        try:
            if self.home_page.is_user_logged_in():
                self.home_page.logout()
                time.sleep(2)
                self.home_page.load_home_page()
                time.sleep(1)
        except Exception:
            pass

    def setup_cart_with_product(self, driver):
        self._ensure_clean_session(driver)

        # 登录并等待成功
        self.home_page.perform_login(
            username=self.test_user["username"],
            password=self.test_user["password"]
        )
        self._dismiss_alert_if_present(driver, timeout=2)
        WebDriverWait(driver, 15).until(
            lambda d: self.home_page.is_user_logged_in()
        )

        # 清空购物车
        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(2)
        try:
            self.cart_page.clear_cart()
        except Exception:
            pass
        time.sleep(1)

        # 加商品
        self._add_product_to_cart(driver, "phones", 0)

        # 跳转购物车验证
        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        # 强断言：必须至少有一个商品
        cart_items = self.cart_page.get_cart_items()
        assert len(cart_items) > 0, f"购物车为空，加购流程失败"

    def test_checkout_modal_opening(self, driver, app_config):
        self.setup_cart_with_product(driver)
        self.cart_page.proceed_to_checkout()

        modal = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "orderModal"))
        )
        assert modal.is_displayed()
        self._close_order_modal_if_present(driver)

    def test_checkout_form_fields_validation(self, driver, app_config):
        self.setup_cart_with_product(driver)
        self.cart_page.proceed_to_checkout()

        required_fields = ["name", "country", "city", "card", "month", "year"]
        for field_id in required_fields:
            field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, field_id))
            )
            assert field.is_displayed(), f"Field {field_id} should be visible"

        self._close_order_modal_if_present(driver)

    def test_successful_checkout_with_valid_data(self, driver, app_config):
        self.setup_cart_with_product(driver)
        self.cart_page.proceed_to_checkout()
        self.cart_page.fill_checkout_form(self.valid_customer_info)

        purchase_success = self.cart_page.complete_purchase()
        assert purchase_success, "Purchase should complete successfully"

        confirmation_details = self.cart_page.get_order_confirmation_details()
        assert confirmation_details["success"]
        assert "thank you" in confirmation_details["title"].lower()

        order_number = self.cart_page.extract_order_number(confirmation_details)
        assert order_number and order_number.isdigit()

        self.cart_page.confirm_success_message()

    def test_checkout_form_data_entry(self, driver, app_config):
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

        name_field = driver.find_element(By.ID, "name")
        assert name_field.get_attribute("value") == test_data["name"]

        country_field = driver.find_element(By.ID, "country")
        assert country_field.get_attribute("value") == test_data["country"]

        self._close_order_modal_if_present(driver)

    def test_checkout_with_empty_form(self, driver, app_config):
        self.setup_cart_with_product(driver)
        self.cart_page.proceed_to_checkout()

        purchase_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[onclick='purchaseOrder()']"))
        )
        purchase_btn.click()
        time.sleep(2)

        alert_text = self._dismiss_alert_if_present(driver, timeout=5)
        assert alert_text is not None, "Expected alert for empty form submission"
        assert "fill out" in alert_text.lower() or "please" in alert_text.lower()

        self._close_order_modal_if_present(driver)

    def test_checkout_with_different_customer_data(self, driver, app_config):
        customer_variations = [
            {
                "name": "Alice Smith",
                "country": "United Kingdom",
                "city": "London",
                "credit_card": "4444555566667777",
                "month": "06",
                "year": "2026"
            },
            {
                "name": "Bob Johnson",
                "country": "Australia",
                "city": "Sydney",
                "credit_card": "5555666677778888",
                "month": "09",
                "year": "2027"
            }
        ]

        successful_orders = []
        for i, customer_data in enumerate(customer_variations, 1):
            self._dismiss_alert_if_present(driver, timeout=1)
            self._close_order_modal_if_present(driver)

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

            purchase_success = self.cart_page.complete_purchase()
            assert purchase_success, f"Purchase should succeed for customer {i}"

            confirmation_details = self.cart_page.get_order_confirmation_details()
            order_number = self.cart_page.extract_order_number(confirmation_details)
            assert order_number, f"Order number should be generated for customer {i}"
            successful_orders.append(order_number)

            self.cart_page.confirm_success_message()
            time.sleep(2)

        unique_orders = set(successful_orders)
        assert len(unique_orders) == len(successful_orders)

    def test_checkout_order_confirmation_details(self, driver, app_config):
        self.setup_cart_with_product(driver)
        self.cart_page.proceed_to_checkout()
        self.cart_page.fill_checkout_form(self.valid_customer_info)
        self.cart_page.complete_purchase()

        confirmation_details = self.cart_page.get_order_confirmation_details()
        details_text = confirmation_details["details"]

        assert self.valid_customer_info["name"] in details_text
        assert self.valid_customer_info["credit_card"] in details_text
        assert "Amount:" in details_text or "USD" in details_text

        order_number = self.cart_page.extract_order_number(confirmation_details)
        assert order_number

        self.cart_page.confirm_success_message()

    def test_checkout_process_screenshot_capture(self, driver, app_config):
        self.setup_cart_with_product(driver)
        driver.save_screenshot("screenshots/checkout_cart_before.png")

        self.cart_page.proceed_to_checkout()
        driver.save_screenshot("screenshots/checkout_modal.png")

        self.cart_page.fill_checkout_form(self.valid_customer_info)
        driver.save_screenshot("screenshots/checkout_form_filled.png")

        self.cart_page.complete_purchase()
        screenshot_path = f"screenshots/checkout_confirmation_{time.strftime('%Y%m%d_%H%M%S')}.png"
        driver.save_screenshot(screenshot_path)

        confirmation_details = self.cart_page.get_order_confirmation_details()
        order_number = self.cart_page.extract_order_number(confirmation_details)
        assert order_number

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