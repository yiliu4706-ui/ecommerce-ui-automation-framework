"""
DemoBlaze Product Management Test Suite - BDD Format
"""

import pytest
import time
from pages.demoblaze_home_page import DemoBlazeHomePage
from pages.demoblaze_cart_page import DemoBlazeCartPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoAlertPresentException, StaleElementReferenceException


class TestDemoBlazeProducts:

    @pytest.fixture(autouse=True)
    def setup(self, driver, app_config):
        self.home_page = DemoBlazeHomePage(driver)
        self.cart_page = DemoBlazeCartPage(driver)
        self.test_user = {"username": "test", "password": "test"}

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

    def login_user(self, driver):
        self.home_page.load_home_page()
        self.home_page.perform_login(
            username=self.test_user["username"],
            password=self.test_user["password"]
        )
        self._dismiss_alert_if_present(driver, timeout=2)
        WebDriverWait(driver, 15).until(lambda d: self.home_page.is_user_logged_in())

    def _clear_cart(self, driver):
        try:
            driver.get("https://www.demoblaze.com/cart.html")
            self.cart_page.wait_for_page_load()
            time.sleep(2)
            for _ in range(10):
                delete_links = driver.find_elements(By.CSS_SELECTOR, "a[onclick*='deleteItem']")
                if not delete_links:
                    break
                self._js_click(driver, delete_links[0])
                time.sleep(2)
        except Exception:
            pass

    def _add_product(self, driver, category, index=0):
        """稳健加购：只点击一次，不重试"""
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
        print(f"[加购] 分类={category}, index={index}, 商品名={product_name}")

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

    def test_product_categories_navigation(self, driver, app_config):
        self.login_user(driver)
        for category in ["phones", "laptops", "monitors"]:
            self.home_page.select_category(category)
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".hrefch"))
            )
            time.sleep(1)
            products = self.home_page.get_product_list()
            assert len(products) > 0

    def test_product_list_display(self, driver, app_config):
        self.login_user(driver)
        self.home_page.select_category("phones")
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".hrefch"))
        )
        time.sleep(1)
        products = self.home_page.get_product_list()
        assert len(products) > 0
        for product in products[:3]:
            assert product["name"]
            assert product["price"]

    def test_single_product_addition_to_cart(self, driver, app_config):
        self.login_user(driver)
        self._clear_cart(driver)
        selected_product = self._add_product(driver, "phones", 0)

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        cart_items = self.cart_page.get_cart_items()
        assert len(cart_items) > 0
        cart_names = [item["name"].lower() for item in cart_items]
        assert any(selected_product.lower() in name for name in cart_names)

    def test_multiple_products_from_same_category(self, driver, app_config):
        self.login_user(driver)
        self._clear_cart(driver)

        added_products = []
        for i in range(2):
            name = self._add_product(driver, "phones", i)
            added_products.append(name)

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        cart_items = self.cart_page.get_cart_items()
        cart_names = [item["name"].lower() for item in cart_items]
        print(f"[期望商品] {added_products}")
        print(f"[购物车实际] {cart_names}")
        assert len(cart_items) >= 2
        for product in added_products:
            assert any(product.lower() in name for name in cart_names)

    def test_products_from_different_categories(self, driver, app_config):
        self.login_user(driver)
        self._clear_cart(driver)

        added_products = []
        for category in ["phones", "laptops"]:
            name = self._add_product(driver, category, 0)
            added_products.append(name)

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        cart_items = self.cart_page.get_cart_items()
        cart_names = [item["name"].lower() for item in cart_items]
        print(f"[期望商品] {added_products}")
        print(f"[购物车实际] {cart_names}")
        assert len(cart_items) >= 2
        for product in added_products:
            assert any(product.lower() in name for name in cart_names)

    def test_product_price_display(self, driver, app_config):
        self.login_user(driver)
        self.home_page.select_category("phones")
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".hrefch"))
        )
        time.sleep(2)

        price_elements = driver.find_elements(By.CSS_SELECTOR, ".card-block h5, .card h5")
        assert len(price_elements) > 0

        valid_count = 0
        for price_el in price_elements[:3]:
            try:
                price = price_el.text.strip()
            except StaleElementReferenceException:
                continue
            assert price
            assert "$" in price or any(c.isdigit() for c in price)
            valid_count += 1
        assert valid_count >= 3

    @pytest.fixture(scope="function", autouse=True)
    def cleanup_products(self, driver):
        yield
        try:
            self._dismiss_alert_if_present(driver, timeout=1)
            if "demoblaze.com" in driver.current_url:
                home_page = DemoBlazeHomePage(driver)
                if home_page.is_user_logged_in():
                    home_page.logout()
        except Exception:
            pass