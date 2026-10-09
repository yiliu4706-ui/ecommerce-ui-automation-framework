# 电商 UI 自动化测试框架（Selenium + Pytest + BDD）

[![CI](https://github.com/yiliu4706-ui/ecommerce-ui-automation-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/yiliu4706-ui/ecommerce-ui-automation-framework/actions/workflows/ci.yml)

## 项目简介
基于 Selenium + Pytest + BDD 的 UI 自动化测试框架，覆盖登录、商品浏览、购物车、订单结算全链路。

## 技术栈
- 语言/框架：Python、Selenium、Pytest、pytest-bdd
- 设计模式：Page Object Model
- 测试报告：Allure、pytest-html、JUnit XML、JSON
- CI/CD：GitHub Actions（Chrome/Firefox × Python 3.11/3.12 矩阵）
- 异常处理：失败自动截图、浏览器原生弹窗捕获
- 特色优化：基于 Chrome DevTools Protocol 的弱网模拟测试

## 项目结构
```text
ecommerce-ui-automation-framework/
├── .github/workflows/       # GitHub Actions CI/CD
├── config/                  # 测试数据与全局配置
│   ├── settings.py
│   └── demoblaze_test_data.py
├── pages/                   # 页面对象层
│   ├── base_page.py
│   ├── demoblaze_home_page.py
│   └── demoblaze_cart_page.py
├── tests/                   # BDD 测试用例
│   ├── test_login.py
│   ├── test_cart.py
│   ├── test_checkout.py
│   ├── test_products.py
│   └── test_demoblaze_e2e.py
├── utilities/               # 工具层（截图、日志、浏览器工厂、测试报告）
├── conftest.py              # Pytest Fixture 与钩子
├── pytest.ini               # Pytest 配置
└── requirements.txt         # 依赖