"""
电商 UI 自动化测试 - 测试数据配置
"""

# DemoBlaze 公开测试账号（不可修改，否则登录失败）
TEST_USERS = {
    "valid_user": {
        "username": "test",
        "password": "test"
    },
    "admin_user": {
        "username": "admin",
        "password": "admin123"
    }
}

# 结算客户信息（可自定义）
CUSTOMER_DATA = {
    "customer1": {
        "name": "张伟",
        "country": "China",
        "city": "Chengdu",
        "credit_card": "6222020200112233445",
        "month": "12",
        "year": "2026"
    },
    "customer2": {
        "name": "李娜",
        "country": "China",
        "city": "Shanghai",
        "credit_card": "6217000011002233445",
        "month": "06",
        "year": "2027"
    },
    "international_customer": {
        "name": "Wang Lei",
        "country": "Singapore",
        "city": "Singapore",
        "credit_card": "4111111111111111",
        "month": "03",
        "year": "2028"
    }
}

# 商品分类（与目标网站元素绑定，不可修改）
PRODUCT_CATEGORIES = {
    "phones": [
        "Samsung galaxy s6",
        "Nokia lumia 1520",
        "Nexus 6",
        "Samsung galaxy s7",
        "Iphone 6 32gb",
        "Sony xperia z5",
        "HTC One M9"
    ],
    "laptops": [
        "Sony vaio i5",
        "Sony vaio i7",
        "MacBook air",
        "Dell i7 8gb",
        "2017 Dell 15.6 Inch",
        "MacBook Pro"
    ],
    "monitors": [
        "Apple monitor 24",
        "ASUS Full HD"
    ]
}

# 测试参数
TEST_CONFIG = {
    "default_timeout": 10,
    "page_load_timeout": 15,
    "explicit_wait_timeout": 10,
    "products_to_add_to_cart": 2,
    "retry_attempts": 3
}

# 预期消息（与目标网站返回文本绑定，不可修改）
EXPECTED_MESSAGES = {
    "add_to_cart_success": "Product added",
    "login_success_indicator": "Welcome",
    "purchase_success": "Thank you for your purchase!",
    "empty_cart_message": "",
    "invalid_login": "User does not exist"
}

# 目标网站地址（不可修改）
URLS = {
    "base_url": "https://www.demoblaze.com",
    "home": "https://www.demoblaze.com/index.html",
    "cart": "https://www.demoblaze.com/cart.html"
}

# 浏览器配置
BROWSER_CONFIG = {
    "chrome": {
        "window_size": "1920,1080",
        "headless": False
    },
    "firefox": {
        "window_size": "1920,1080",
        "headless": False
    }
}