"""
DemoBlaze Cart Page Object
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from pages.base_page import BasePage
import time


class DemoBlazeCartPage(BasePage):

    def __init__(self, driver, timeout=10):
        super().__init__(driver, timeout)
        self.url = "https://www.demoblaze.com/cart.html"

    CART_ITEMS = (By.CSS_SELECTOR, "#tbodyid tr")
    CART_ITEM_NAME = (By.CSS_SELECTOR, "td:nth-child(2)")
    CART_ITEM_PRICE = (By.CSS_SELECTOR, "td:nth-child(3)")
    DELETE_BUTTONS = (By.CSS_SELECTOR, "td:nth-child(4) a")
    TOTAL_PRICE = (By.ID, "totalp")
    PLACE_ORDER_BTN = (By.CSS_SELECTOR, "button[data-target='#orderModal']")

    ORDER_MODAL = (By.ID, "orderModal")
    NAME_INPUT = (By.ID, "name")
    COUNTRY_INPUT = (By.ID, "country")
    CITY_INPUT = (By.ID, "city")
    CREDIT_CARD_INPUT = (By.ID, "card")
    MONTH_INPUT = (By.ID, "month")
    YEAR_INPUT = (By.ID, "year")
    PURCHASE_BUTTON = (By.CSS_SELECTOR, "button[onclick='purchaseOrder()']")
    CLOSE_MODAL_BTN = (By.CSS_SELECTOR, "#orderModal .btn-secondary")

    SUCCESS_MESSAGE = (By.CSS_SELECTOR, ".sweet-alert")
    SUCCESS_MESSAGE_TEXT = (By.CSS_SELECTOR, ".sweet-alert h2")
    SUCCESS_DETAILS = (By.CSS_SELECTOR, ".sweet-alert p")
    CONFIRM_SUCCESS_BTN = (By.CSS_SELECTOR, ".confirm")

    def load_cart_page(self):
        self.driver.get(self.url)
        self.wait_for_page_load()
        return self

    def wait_for_page_load(self):
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.any_of(
                    EC.presence_of_element_located((By.ID, "tbodyid")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".table")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
                )
            )
            time.sleep(2)
        except TimeoutException:
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                raise Exception("Cart page failed to load")

    def get_cart_items(self):
        items = []
        try:
            cart_rows = self.driver.find_elements(*self.CART_ITEMS)
            for row in cart_rows:
                if row.find_elements(By.TAG_NAME, "td"):
                    name_element = row.find_element(*self.CART_ITEM_NAME)
                    price_element = row.find_element(*self.CART_ITEM_PRICE)
                    item_data = {
                        "name": name_element.text.strip(),
                        "price": price_element.text.strip(),
                        "element": row
                    }
                    items.append(item_data)
        except NoSuchElementException:
            pass
        return items

    def get_cart_item_count(self):
        return len(self.get_cart_items())

    def get_total_price(self):
        try:
            total_element = self.wait_for_element_visible(self.TOTAL_PRICE)
            return total_element.text.strip()
        except TimeoutException:
            return "0"

    def verify_item_in_cart(self, product_name):
        cart_items = self.get_cart_items()
        for item in cart_items:
            if product_name.lower() in item["name"].lower():
                return True
        return False

    def verify_cart_total_calculation(self):
        items = self.get_cart_items()
        calculated_total = 0
        for item in items:
            price_text = item["price"].replace("$", "").replace(",", "").strip()
            try:
                calculated_total += float(price_text)
            except ValueError:
                continue
        displayed_total_text = self.get_total_price().replace("$", "").replace(",", "").strip()
        try:
            displayed_total = float(displayed_total_text)
            return abs(calculated_total - displayed_total) < 0.01
        except ValueError:
            return False

    def clear_cart(self):
        """
        清空购物车中的所有商品。
        用于解决 DemoBlaze 购物车跨用例持久化导致的测试污染问题。
        """
        try:
            max_iterations = 20
            for _ in range(max_iterations):
                cart_items = self.get_cart_items()
                if not cart_items:
                    break
                delete_btn = cart_items[0]["element"].find_element(*self.DELETE_BUTTONS)
                try:
                    delete_btn.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", delete_btn)
                time.sleep(1.5)
            return True
        except Exception:
            return False

    def remove_item_from_cart(self, product_name):
        items = self.get_cart_items()
        for item in items:
            if product_name.lower() in item["name"].lower():
                delete_btn = item["element"].find_element(*self.DELETE_BUTTONS)
                delete_btn.click()
                time.sleep(2)
                return True
        return False

    def proceed_to_checkout(self):
        place_order_btn = self.wait_for_element_clickable(self.PLACE_ORDER_BTN)
        place_order_btn.click()
        WebDriverWait(self.driver, self.timeout).until(
            EC.visibility_of_element_located(self.ORDER_MODAL)
        )
        return self

    def fill_checkout_form(self, customer_info):
        self.wait_for_element_visible(self.ORDER_MODAL)

        name_field = self.wait_for_element_visible(self.NAME_INPUT)
        name_field.clear()
        name_field.send_keys(customer_info.get("name", ""))

        country_field = self.wait_for_element_visible(self.COUNTRY_INPUT)
        country_field.clear()
        country_field.send_keys(customer_info.get("country", ""))

        city_field = self.wait_for_element_visible(self.CITY_INPUT)
        city_field.clear()
        city_field.send_keys(customer_info.get("city", ""))

        card_field = self.wait_for_element_visible(self.CREDIT_CARD_INPUT)
        card_field.clear()
        card_field.send_keys(customer_info.get("credit_card", ""))

        month_field = self.wait_for_element_visible(self.MONTH_INPUT)
        month_field.clear()
        month_field.send_keys(customer_info.get("month", ""))

        year_field = self.wait_for_element_visible(self.YEAR_INPUT)
        year_field.clear()
        year_field.send_keys(customer_info.get("year", ""))

        return self

    def complete_purchase(self):
        purchase_btn = self.wait_for_element_clickable(self.PURCHASE_BUTTON)
        purchase_btn.click()
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.visibility_of_element_located(self.SUCCESS_MESSAGE)
            )
            return True
        except TimeoutException:
            return False

    def get_order_confirmation_details(self):
        try:
            success_element = self.wait_for_element_visible(self.SUCCESS_MESSAGE)
            title_element = success_element.find_element(*self.SUCCESS_MESSAGE_TEXT)
            title = title_element.text if title_element else ""
            details_element = success_element.find_element(*self.SUCCESS_DETAILS)
            details = details_element.text if details_element else ""
            return {
                "title": title,
                "details": details,
                "success": "Thank you for your purchase!" in title
            }
        except (TimeoutException, NoSuchElementException):
            return {"title": "", "details": "", "success": False}

    def extract_order_number(self, confirmation_details):
        details_text = confirmation_details.get("details", "")
        import re
        patterns = [
            r"Id:\s*(\d+)",
            r"Order.*?(\d+)",
            r"#(\d+)",
            r"ID:\s*(\d+)"
        ]
        for pattern in patterns:
            match = re.search(pattern, details_text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def confirm_success_message(self):
        try:
            confirm_btn = self.wait_for_element_clickable(self.CONFIRM_SUCCESS_BTN)
            confirm_btn.click()
            time.sleep(2)
            return True
        except TimeoutException:
            return False

    def is_cart_empty(self):
        return self.get_cart_item_count() == 0

    def get_cart_summary(self):
        items = self.get_cart_items()
        total = self.get_total_price()
        return {
            "items": items,
            "item_count": len(items),
            "total_price": total,
            "is_empty": len(items) == 0
        }