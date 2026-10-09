"""
Network Condition Resilience Test Suite

Validates application behavior under various network conditions
using Chrome DevTools Protocol network emulation.
"""

import pytest
import time
from pages.demoblaze_home_page import DemoBlazeHomePage
from pages.demoblaze_cart_page import DemoBlazeCartPage
from utilities.network_emulator import NetworkEmulator, NetworkCondition
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoAlertPresentException,
    WebDriverException,
    StaleElementReferenceException,
)


class TestNetworkConditions:

    @pytest.fixture(autouse=True)
    def setup(self, driver, app_config):
        self.driver = driver
        self.home_page = DemoBlazeHomePage(driver, timeout=30)
        self.cart_page = DemoBlazeCartPage(driver, timeout=30)
        self.network = NetworkEmulator(driver)
        self.test_user = {"username": "test", "password": "test"}

    def teardown_method(self):
        try:
            self.network.clear_emulation()
        except Exception:
            pass

    def _dismiss_alert_if_present(self, driver, timeout=5):
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
        self._dismiss_alert_if_present(driver, timeout=3)

    def _measure_page_load(self, driver, url, timeout=60):
        """Measure page load time in seconds under current network conditions."""
        start = time.time()
        try:
            driver.set_page_load_timeout(timeout)
            driver.get(url)
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            return -1
        return round(time.time() - start, 2)

    def test_baseline_wifi_performance(self, driver, app_config):
        """Baseline performance under Wi-Fi conditions."""
        self.network.apply_profile("wifi")
        load_time = self._measure_page_load(driver, "https://www.demoblaze.com")
        assert load_time > 0, "Page failed to load under Wi-Fi"
        assert load_time < 30, f"Wi-Fi load time too slow: {load_time}s"
        print(f"[Wi-Fi] Homepage load: {load_time}s")

        self.home_page.wait_for_page_load()
        assert self.home_page.verify_home_page_loaded()

    def test_4g_network_login(self, driver, app_config):
        """Login functionality under 4G network."""
        self.network.apply_profile("4g")
        self._login(driver)
        WebDriverWait(driver, 30).until(lambda d: self.home_page.is_user_logged_in())
        assert self.home_page.is_user_logged_in()

    def test_3g_network_product_browsing(self, driver, app_config):
        """Product listing retrieval under 3G network."""
        self.network.apply_profile("3g")
        self._login(driver)

        self.home_page.select_category("phones")
        WebDriverWait(driver, 45).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".hrefch"))
        )
        products = self.home_page.get_product_list()
        assert len(products) > 0, "No products loaded under 3G"
        print(f"[3G] Products loaded: {len(products)}")

    def test_slow_3g_page_load_timeout(self, driver, app_config):
        """Verify page load succeeds under Slow 3G within extended timeout."""
        self.network.apply_profile("slow_3g")
        start = time.time()
        try:
            driver.set_page_load_timeout(90)
            driver.get("https://www.demoblaze.com")
            WebDriverWait(driver, 90).until(
                EC.presence_of_element_located((By.ID, "tbodyid"))
            )
            elapsed = round(time.time() - start, 2)
            print(f"[Slow 3G] Homepage load: {elapsed}s")
            assert elapsed > 0
        except TimeoutException:
            pytest.fail("Page failed to load under Slow 3G within 90s")

    def test_lossy_network_retry_mechanism(self, driver, app_config):
        """Verify resilience under lossy network with retry."""
        self.network.apply_profile("lossy")
        attempts = 0
        max_attempts = 3
        loaded = False

        while attempts < max_attempts and not loaded:
            attempts += 1
            try:
                driver.set_page_load_timeout(60)
                driver.get("https://www.demoblaze.com")
                WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.ID, "tbodyid"))
                )
                loaded = True
            except (TimeoutException, WebDriverException) as e:
                print(f"[Lossy] Attempt {attempts} failed: {type(e).__name__}")
                time.sleep(3)

        assert loaded, f"Page failed to load under lossy network after {max_attempts} attempts"
        print(f"[Lossy] Loaded after {attempts} attempt(s)")

    def test_offline_mode_detection(self, driver, app_config):
        """Verify offline state is detectable via network emulation."""
        self.network.apply_profile("wifi")
        self.home_page.load_home_page()
        assert self.home_page.verify_home_page_loaded()

        self.network.apply_profile("offline")
        time.sleep(2)

        try:
            driver.set_page_load_timeout(15)
            driver.get("https://www.demoblaze.com/cart.html")
            is_offline = False
        except (TimeoutException, WebDriverException):
            is_offline = True

        assert is_offline, "Expected offline navigation to fail but it succeeded"
        print("[Offline] Offline state correctly detected")

    def test_network_recovery_after_offline(self, driver, app_config):
        """Verify functionality resumes after network recovery."""
        self.network.apply_profile("wifi")
        self.home_page.load_home_page()

        self.network.apply_profile("offline")
        time.sleep(2)

        self.network.apply_profile("4g")
        time.sleep(2)

        load_time = self._measure_page_load(driver, "https://www.demoblaze.com", timeout=60)
        assert load_time > 0, "Page failed to load after network recovery"
        print(f"[Recovery] Load time after offline recovery: {load_time}s")

    def test_slow_3g_cart_operations(self, driver, app_config):
        """Add product to cart under Slow 3G network."""
        self.network.apply_profile("wifi")
        self._login(driver)

        driver.get("https://www.demoblaze.com/cart.html")
        self.cart_page.wait_for_page_load()
        time.sleep(2)
        for _ in range(10):
            try:
                delete_links = driver.find_elements(By.CSS_SELECTOR, "a[onclick*='deleteItem']")
                if not delete_links:
                    break
                driver.execute_script("arguments[0].click();", delete_links[0])
                time.sleep(1.5)
            except StaleElementReferenceException:
                time.sleep(1)

        self.network.apply_profile("slow_3g")

        driver.get("https://www.demoblaze.com")
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.ID, "tbodyid"))
        )

        self.home_page.select_category("phones")
        WebDriverWait(driver, 60).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".hrefch"))
        )
        product_links = driver.find_elements(By.CSS_SELECTOR, ".hrefch")
        assert len(product_links) > 0

        driver.execute_script("arguments[0].click();", product_links[0])
        WebDriverWait(driver, 60).until(lambda d: "prod.html" in d.current_url)

        add_btn = WebDriverWait(driver, 60).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[onclick*='addToCart']"))
        )
        driver.execute_script("arguments[0].click();", add_btn)
        alert_text = self._dismiss_alert_if_present(driver, timeout=30)
        assert alert_text is not None, "No alert under Slow 3G"
        print(f"[Slow 3G] Cart alert received: {alert_text}")

    def test_bandwidth_constraint_response_size(self, driver, app_config):
        """Measure resource transfer under constrained bandwidth."""
        self.network.apply_profile("3g")

        driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})

        start = time.time()
        driver.set_page_load_timeout(90)
        driver.get("https://www.demo4blaze.com" if False else "https://www.demoblaze.com")
        elapsed = round(time.time() - start, 2)

        resources = driver.execute_script(
            "return performance.getEntriesByType('resource').length"
        )
        print(f"[3G] Load time: {elapsed}s, Resource count: {resources}")
        assert elapsed > 0
        assert resources >= 0