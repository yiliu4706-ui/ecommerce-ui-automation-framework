"""
DemoBlaze Cart Management Test Suite - BDD Format
"""

import pytest
import time
from pages.demoblaze_home_page import DemoBlazeHomePage
from pages.demoblaze_cart_page import DemoBlazeCartPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoAlertPresentException


class TestDemoBlazeCart:

    @pytest.fixture(autouse=True)
    def setup(self, driver, app_config):
        self.home_page = DemoBlazeHomePage(driver)
        self.cart_page = DemoBlazeCartPage(driver)
        self.test_user = {"username": "test", "password": "test"}

    def _dismiss_alert_if_present(self, driver, timeout=3):
        try:
            WebDriverWait(driver, timeout).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert_text = alert.text
            alert.accept()
            return alert_text
        except (TimeoutException, NoAlertPresentException):
            return None

    def _login_and_clear_cart(self, driver):
        """登录并清空购物车，保证测试从干净状态开始"""
        self.home_page.load_home_page()
        self.home_page.perform_login(
            username=self.test_user["username"],
            password=self.test_user["password"]
        )
        self._dismiss_alert_if_present(driver)
        time.sleep(2)

        # 清空购物车，避免跨用例残留
        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(2)
        self.cart_page.clear_cart()
        time.sleep(1)

    def login_and_add_product(self, driver, category="phones", product_index=0):
        # 先清空购物车，确保干净状态
        self._login_and_clear_cart(driver)

        # 回到首页，添加商品
        self.home_page.load_home_page()
        self.home_page.select_category(category)
        time.sleep(2)

        products = self.home_page.get_product_list()
        product_name = products[product_index]["name"]

        product_links = driver.find_elements(By.CSS_SELECTOR, ".hrefch")
        product_links[product_index].click()
        time.sleep(3)

        add_to_cart_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[onclick*='addToCart']"))
        )
        add_to_cart_btn.click()
        time.sleep(2)
        self._dismiss_alert_if_present(driver, timeout=5)

        return product_name

    def test_empty_cart_display(self, driver, app_config):
        print("Scenario: User views an empty shopping cart")

        # 登录后强制清空购物车
        self._login_and_clear_cart(driver)

        # 重新加载购物车页面确认已空
        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(2)

        assert self.cart_page.is_cart_empty(), "Cart should be empty after clear_cart"

        cart_summary = self.cart_page.get_cart_summary()
        assert cart_summary["item_count"] == 0
        assert cart_summary["is_empty"] == True

        print("Empty cart displays correctly")

    def test_single_product_in_cart_verification(self, driver, app_config):
        print("Scenario: User views cart item information")

        # login_and_add_product 内部已先清空购物车
        product_name = self.login_and_add_product(driver, "phones", 0)

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        cart_items = self.cart_page.get_cart_items()
        assert len(cart_items) == 1, f"Cart should contain exactly 1 item, found {len(cart_items)}"

        cart_item = cart_items[0]
        assert product_name.lower() in cart_item["name"].lower()
        assert cart_item["price"]

        print(f"Single product verified in cart: {cart_item['name']} - {cart_item['price']}")

    def test_multiple_products_cart_verification(self, driver, app_config):
        print("Scenario: User verifies multiple products in cart")

        # 第一次添加会清空购物车
        product1 = self.login_and_add_product(driver, "phones", 0)
        added_products = [product1]

        # 添加第二个商品（不清空）
        driver.get("https://www.demoblaze.com")
        self._dismiss_alert_if_present(driver, timeout=2)
        self.home_page.select_category("laptops")
        time.sleep(2)

        laptops = self.home_page.get_product_list()
        product2 = laptops[0]["name"]
        added_products.append(product2)

        laptop_links = driver.find_elements(By.CSS_SELECTOR, ".hrefch")
        laptop_links[0].click()
        time.sleep(3)

        add_to_cart_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[onclick*='addToCart']"))
        )
        add_to_cart_btn.click()
        time.sleep(2)
        self._dismiss_alert_if_present(driver, timeout=5)

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        cart_items = self.cart_page.get_cart_items()
        assert len(cart_items) >= 2

        cart_names = [item["name"].lower() for item in cart_items]
        for product_name in added_products:
            assert any(product_name.lower() in cart_name for cart_name in cart_names)

        print(f"Multiple products verified in cart: {len(cart_items)} items")

    def test_cart_total_calculation(self, driver, app_config):
        print("Scenario: User verifies cart total calculation accuracy")

        product_name = self.login_and_add_product(driver, "phones", 0)

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        cart_items = self.cart_page.get_cart_items()
        total_price = self.cart_page.get_total_price()

        assert total_price, "Total price should be displayed"

        calculated_total = 0
        for item in cart_items:
            price_text = item["price"].replace("$", "").replace(",", "").strip()
            try:
                calculated_total += float(price_text)
            except ValueError:
                continue

        displayed_total_text = total_price.replace("$", "").replace(",", "").strip()
        try:
            displayed_total = float(displayed_total_text)
            assert abs(calculated_total - displayed_total) < 0.01
        except ValueError:
            pass

        print(f"Cart total calculation verified: {total_price}")

    def test_cart_item_removal(self, driver, app_config):
        print("Scenario: User removes an item from their cart")

        product_name = self.login_and_add_product(driver, "phones", 0)

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        cart_items = self.cart_page.get_cart_items()
        initial_count = len(cart_items)
        assert initial_count > 0

        success = self.cart_page.remove_item_from_cart(product_name)
        assert success

        time.sleep(2)
        cart_items_after = self.cart_page.get_cart_items()
        assert len(cart_items_after) < initial_count

        print(f"Product removal verified: {product_name}")

    def test_cart_navigation_functionality(self, driver, app_config):
        print("Scenario: User navigates cart page interface elements")

        self.home_page.load_home_page()
        self.home_page.perform_login(
            username=self.test_user["username"],
            password=self.test_user["password"]
        )
        self._dismiss_alert_if_present(driver)

        self.home_page.navigate_to_cart()
        assert "cart.html" in driver.current_url

        driver.get("https://www.demoblaze.com")
        time.sleep(2)

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()

        assert "cart.html" in driver.current_url

        print("Cart navigation functionality verified")

    def test_cart_persistence_across_sessions(self, driver, app_config):
        print("Scenario: User verifies cart persistence during site navigation")

        product_name = self.login_and_add_product(driver, "phones", 0)

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        initial_cart_items = self.cart_page.get_cart_items()
        initial_count = len(initial_cart_items)
        assert initial_count > 0

        driver.get("https://www.demoblaze.com")
        time.sleep(2)

        driver.get("https://www.demoblaze.com/index.html")
        time.sleep(2)

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(2)

        persisted_cart_items = self.cart_page.get_cart_items()
        assert len(persisted_cart_items) == initial_count

        print(f"Cart persistence verified: {len(persisted_cart_items)} items maintained")

    @pytest.fixture(scope="function", autouse=True)
    def cleanup_cart(self, driver):
        yield
        try:
            self._dismiss_alert_if_present(driver, timeout=1)
            if "demoblaze.com" in driver.current_url:
                home_page = DemoBlazeHomePage(driver)
                if home_page.is_user_logged_in():
                    home_page.logout()
                    time.sleep(1)
        except Exception:
            pass