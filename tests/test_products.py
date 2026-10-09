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
from selenium.common.exceptions import (
    TimeoutException,
    NoAlertPresentException,
    StaleElementReferenceException
)


class TestDemoBlazeProducts:

    @pytest.fixture(autouse=True)
    def setup(self, driver, app_config):
        self.home_page = DemoBlazeHomePage(driver)
        self.cart_page = DemoBlazeCartPage(driver)
        self.test_user = {"username": "test", "password": "test"}

    def _dismiss_alert_if_present(self, driver, timeout=5):
        try:
            WebDriverWait(driver, timeout).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            text = alert.text
            alert.accept()
            return text
        except (TimeoutException, NoAlertPresentException):
            return None

    def login_user(self, driver):
        self.home_page.load_home_page()
        self.home_page.perform_login(
            username=self.test_user["username"],
            password=self.test_user["password"]
        )
        self._dismiss_alert_if_present(driver, timeout=2)
        WebDriverWait(driver, 15).until(lambda d: self.home_page.is_user_logged_in())

    def _js_click(self, driver, element):
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", element)

    def _click_add_to_cart_with_retry(self, driver, max_attempts=3):
        """点击加购按钮并等待 alert，最多重试 3 次"""
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                add_to_cart_btn = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a[onclick*='addToCart']"))
                )
                self._js_click(driver, add_to_cart_btn)
                print(f"[加购] 第 {attempt} 次点击 addToCart，等待 alert...")

                alert_text = self._dismiss_alert_if_present(driver, timeout=10)
                if alert_text is not None:
                    print(f"[加购] alert 已捕获: {alert_text}")
                    return alert_text

                print(f"[加购] 第 {attempt} 次未弹出 alert，准备重试")
                time.sleep(2)
                # 刷新详情页再试
                driver.refresh()
                time.sleep(2)
            except Exception as e:
                last_error = e
                print(f"[加购] 第 {attempt} 次异常: {e}")
                time.sleep(2)

        raise AssertionError(f"重试 {max_attempts} 次后加购仍未弹出 alert，最后异常: {last_error}")

    def _add_product(self, driver, category, index=0):
        """稳健加购：JS 点击 + 等待列表刷新 + 等待 URL 跳转 + 重试点击加购"""
        driver.get("https://www.demoblaze.com")
        self.home_page.wait_for_page_load()
        time.sleep(2)

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
        assert len(product_links) > index, f"{category} 商品不足 index={index}"
        product_name = product_links[index].text.strip()
        assert product_name, "商品名为空"
        print(f"[加购] 分类={category}, index={index}, 商品名={product_name}")

        self._js_click(driver, product_links[index])

        WebDriverWait(driver, 20).until(lambda d: "prod.html" in d.current_url)
        time.sleep(2)

        self._click_add_to_cart_with_retry(driver, max_attempts=3)

        time.sleep(3)
        return product_name

    def test_product_categories_navigation(self, driver, app_config):
        self.login_user(driver)

        categories = ["phones", "laptops", "monitors"]
        for category in categories:
            self.home_page.select_category(category)
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".hrefch"))
            )
            time.sleep(2)
            try:
                products = self.home_page.get_product_list()
            except StaleElementReferenceException:
                time.sleep(2)
                products = self.home_page.get_product_list()
            assert len(products) > 0, f"No products displayed in {category} category"

    def test_product_list_display(self, driver, app_config):
        self.login_user(driver)
        self.home_page.select_category("phones")
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".hrefch"))
        )
        time.sleep(2)

        try:
            products = self.home_page.get_product_list()
        except StaleElementReferenceException:
            time.sleep(2)
            products = self.home_page.get_product_list()

        assert len(products) > 0

        for i, product in enumerate(products[:3]):
            assert product["name"]
            assert product["price"]

    def test_single_product_addition_to_cart(self, driver, app_config):
        self.login_user(driver)
        selected_product = self._add_product(driver, "phones", 0)

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        cart_items = self.cart_page.get_cart_items()
        assert len(cart_items) > 0, "购物车为空"
        cart_names = [item["name"].lower() for item in cart_items]
        assert any(selected_product.lower() in name for name in cart_names), \
            f"商品 '{selected_product}' 不在购物车 {cart_names}"

    def test_multiple_products_from_same_category(self, driver, app_config):
        self.login_user(driver)

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

        assert len(cart_items) >= 2, f"购物车应至少 2 件，实际 {len(cart_items)} 件"

        for product in added_products:
            assert any(product.lower() in name for name in cart_names), \
                f"商品 '{product}' 不在购物车 {cart_names}"

    def test_products_from_different_categories(self, driver, app_config):
        self.login_user(driver)

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

        assert len(cart_items) >= 2, f"购物车应至少 2 件，实际 {len(cart_items)} 件"

        for product in added_products:
            assert any(product.lower() in name for name in cart_names), \
                f"商品 '{product}' 不在购物车 {cart_names}"

    def test_product_price_display(self, driver, app_config):
        self.login_user(driver)
        self.home_page.select_category("phones")
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".hrefch"))
        )
        time.sleep(2)

        price_elements = driver.find_elements(By.CSS_SELECTOR, ".card-block h5, .card h5")
        assert len(price_elements) > 0, "Price elements should be present"

        valid_count = 0
        for price_el in price_elements[:3]:
            try:
                price = price_el.text.strip()
            except StaleElementReferenceException:
                continue
            assert price, "Price text should not be empty"
            assert "$" in price or any(c.isdigit() for c in price), f"Invalid price format: {price}"
            valid_count += 1

        assert valid_count >= 3, "At least 3 prices should be verified"

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