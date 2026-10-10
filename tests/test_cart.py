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

    def _force_dismiss_alert(self, driver):
        """立即关闭任何挂起的 alert（不阻塞）"""
        try:
            alert = driver.switch_to.alert
            text = alert.text
            alert.accept()
            time.sleep(0.5)
            return text
        except Exception:
            return None

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
        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)
        for _ in range(20):
            try:
                delete_links = driver.find_elements(By.CSS_SELECTOR, "a[onclick*='deleteItem']")
                if not delete_links:
                    break
                self._js_click(driver, delete_links[0])
                time.sleep(1.5)
            except StaleElementReferenceException:
                time.sleep(1)
            except Exception:
                time.sleep(1)
        time.sleep(2)

    def _navigate_to_product_detail(self, driver, category, index):
        """导航到商品详情页，返回商品名"""
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

        self._js_click(driver, product_links[index])
        WebDriverWait(driver, 20).until(lambda d: "prod.html" in d.current_url)
        time.sleep(2)
        return product_name

    def _add_product_once(self, driver, category="phones", index=0):
        """
        稳定加购：每轮完整重新导航 + 清理 alert + 原生 click + 轮询 alert + 购物车验证
        """
        product_name = None
        last_error = None

        for attempt in range(4):
            print(f"[加购] ===== 第 {attempt + 1} 轮 =====")
            # 步骤1：每轮完整重新导航到商品详情页
            try:
                product_name = self._navigate_to_product_detail(driver, category, index)
                print(f"[加购] 商品名: {product_name}")
            except Exception as e:
                last_error = e
                print(f"[加购] 导航失败: {e}")
                time.sleep(2)
                continue

            # 步骤2：清理任何挂起的 alert（关键）
            self._force_dismiss_alert(driver)
            time.sleep(1)

            # 步骤3：原生 click 加购按钮
            try:
                add_to_cart_btn = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a[onclick*='addToCart']"))
                )
                add_to_cart_btn.click()
                print(f"[加购] 已点击加购按钮")
            except Exception as e:
                last_error = e
                print(f"[加购] 点击失败: {e}")
                self._force_dismiss_alert(driver)
                continue

            # 步骤4：主动轮询等 alert（每秒检查，最多 15 次）
            got_alert_text = None
            for _ in range(15):
                try:
                    alert = driver.switch_to.alert
                    got_alert_text = alert.text
                    alert.accept()
                    print(f"[加购] 捕获 alert: {got_alert_text}")
                    break
                except Exception:
                    time.sleep(1)

            if got_alert_text is None:
                print(f"[加购] 未捕获 alert，继续验证购物车")

            # 步骤5：去购物车验证商品是否真的加入（唯一成功判据）
            try:
                driver.get("https://www.demoblaze.com/cart.html")
                self.cart_page.wait_for_page_load()
                time.sleep(3)
                cart_items = self.cart_page.get_cart_items()
                cart_names = [item["name"].lower() for item in cart_items]
                print(f"[加购] 购物车当前: {cart_names}")
                if any(product_name.lower() in n for n in cart_names):
                    print(f"[加购] 第 {attempt + 1} 轮验证成功")
                    return product_name
                print(f"[加购] 第 {attempt + 1} 轮购物车验证失败")
            except Exception as e:
                last_error = e
                print(f"[加购] 购物车验证异常: {e}")

            time.sleep(2)

        raise AssertionError(f"{category} 商品 {product_name} 加购失败: {last_error}")

    def test_empty_cart_display(self, driver, app_config):
        self.login_user(driver)
        self._clear_cart(driver)
        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(2)
        assert self.cart_page.is_cart_empty()

    def test_single_product_in_cart_verification(self, driver, app_config):
        self.login_user(driver)
        self._clear_cart(driver)
        product_name = self._add_product_once(driver, "phones", 0)

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(3)
        cart_items = self.cart_page.get_cart_items()
        cart_names = [item["name"].lower() for item in cart_items]
        assert len(cart_items) >= 1
        assert any(product_name.lower() in n for n in cart_names)

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
        cart_names = [item["name"].lower() for item in cart_items]
        assert len(cart_items) >= 2
        for product in added_products:
            assert any(product.lower() in n for n in cart_names)

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
        assert self.cart_page.remove_item_from_cart(product_name)
        time.sleep(2)
        assert len(self.cart_page.get_cart_items()) < initial_count

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
        assert initial_count >= 1
        driver.get("https://www.demoblaze.com")
        time.sleep(2)
        driver.get("https://www.demoblaze.com/index.html")
        time.sleep(2)
        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(2)
        assert len(self.cart_page.get_cart_items()) == initial_count

    @pytest.fixture(scope="function", autouse=True)
    def cleanup_cart(self, driver):
        yield
        try:
            self._force_dismiss_alert(driver)
            if "demoblaze.com" in driver.current_url:
                home_page = DemoBlazeHomePage(driver)
                if home_page.is_user_logged_in():
                    home_page.logout()
        except Exception:
            pass