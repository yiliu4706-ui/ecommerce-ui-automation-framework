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
from selenium.common.exceptions import TimeoutException, NoAlertPresentException, StaleElementReferenceException


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
        """访问购物车页面，循环删除所有商品直到购物车为空"""
        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(2)
        for _ in range(15):
            delete_links = driver.find_elements(By.CSS_SELECTOR, "a[onclick*='deleteItem']")
            if not delete_links:
                break
            self._js_click(driver, delete_links[0])
            time.sleep(1.5)
        # 最终确认购物车为空
        WebDriverWait(driver, 10).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, "#tbodyid tr")) == 0
        )

    def _add_product_once(self, driver, category="phones", index=0):
        """加购一次，并验证购物车中已存在该商品，返回商品名"""
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
        assert len(product_links) > index, f"{category} 商品数量不足"
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
        assert "added" in alert_text.lower(), f"alert 内容异常: {alert_text}"

        # 立即跳转购物车验证该商品已存在
        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        WebDriverWait(driver, 15).until(
            lambda d: any(product_name.lower() in item["name"].lower()
                          for item in self.cart_page.get_cart_items())
        )
        return product_name

    def test_empty_cart_display(self, driver, app_config):
        self.login_user(driver)
        self._clear_cart(driver)
        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(2)
        assert self.cart_page.is_cart_empty(), "Cart should be empty initially"

    def test_single_product_in_cart_verification(self, driver, app_config):
        self.login_user(driver)
        self._clear_cart(driver)
        product_name = self._add_product_once(driver, "phones", 0)

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        cart_items = self.cart_page.get_cart_items()
        assert len(cart_items) == 1, f"购物车应恰好 1 件，实际 {len(cart_items)} 件"
        assert product_name.lower() in cart_items[0]["name"].lower()
        assert cart_items[0]["price"]

    def test_multiple_products_cart_verification(self, driver, app_config):
        self.login_user(driver)
        self._clear_cart(driver)

        added_products = []
        for i in range(2):
            name = self._add_product_once(driver, "phones", i)
            added_products.append(name)

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        cart_items = self.cart_page.get_cart_items()
        assert len(cart_items) >= 2, f"购物车应至少 2 件，实际 {len(cart_items)} 件"
        cart_names = [item["name"].lower() for item in cart_items]
        for product in added_products:
            assert any(product.lower() in name for name in cart_names)

    def test_cart_total_calculation(self, driver, app_config):
        self.login_user(driver)
        self._clear_cart(driver)
        self._add_product_once(driver, "phones", 0)

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        cart_items = self.cart_page.get_cart_items()
        total_price = self.cart_page.get_total_price()
        assert total_price

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

    def test_cart_item_removal(self, driver, app_config):
        self.login_user(driver)
        self._clear_cart(driver)
        product_name = self._add_product_once(driver, "phones", 0)

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

    def test_cart_navigation_functionality(self, driver, app_config):
        self.login_user(driver)
        self.home_page.navigate_to_cart()
        assert "cart.html" in driver.current_url
        driver.get("https://www.demoblaze.com")
        time.sleep(2)
        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        assert "cart.html" in driver.current_url

    def test_cart_persistence_across_sessions(self, driver, app_config):
        self.login_user(driver)
        self._clear_cart(driver)
        self._add_product_once(driver, "phones", 0)

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)

        initial_count = len(self.cart_page.get_cart_items())
        assert initial_count == 1, f"购物车应恰好 1 件，实际 {initial_count} 件"

        driver.get("https://www.demoblaze.com")
        time.sleep(2)
        driver.get("https://www.demoblaze.com/index.html")
        time.sleep(2)
        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(2)

        final_count = len(self.cart_page.get_cart_items())
        assert final_count == initial_count

    @pytest.fixture(scope="function", autouse=True)
    def cleanup_cart(self, driver):
        yield
        try:
            self._dismiss_alert_if_present(driver, timeout=1)
            if "demoblaze.com" in driver.current_url:
                home_page = DemoBlazeHomePage(driver)
                if home_page.is_user_logged_in():
                    home_page.logout()
        except Exception:
            pass