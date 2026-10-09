# Configuration settings for DemoBlaze e-commerce test framework
# This file stores environment-specific configurations for DemoBlaze testing

# DemoBlaze Application URLs
BASE_URL = "https://www.demoblaze.com"
HOME_URL = "https://www.demoblaze.com/index.html"
CART_URL = "https://www.demoblaze.com/cart.html"

# Browser Settings
DEFAULT_BROWSER = "chrome"
DEFAULT_TIMEOUT = 10
DEFAULT_WINDOW_SIZE = (1920, 1080)
HEADLESS_MODE = True

# DemoBlaze Test Credentials
VALID_USERNAME = "test"
VALID_PASSWORD = "test"

# Directories
SCREENSHOTS_DIR = "screenshots"
REPORTS_DIR = "reports"
LOGS_DIR = "reports"

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Test Execution Settings
IMPLICIT_WAIT = 2
EXPLICIT_WAIT = 10
POLL_FREQUENCY = 0.5

# Browser Optimization Settings for E-commerce Testing
CHROME_OPTIONS = [
    "--disable-extensions",
    "--disable-plugins", 
    "--disable-dev-shm-usage",
    "--no-sandbox",
    "--disable-gpu"
]

FIREFOX_PREFERENCES = {
    "browser.cache.disk.enable": False,
    "browser.cache.memory.enable": False,
    "browser.cache.offline.enable": False,
    "network.http.use-cache": False
}