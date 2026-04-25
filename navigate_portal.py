import logging
import os
from contextlib import contextmanager
from subprocess import run
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import NoSuchDriverException

ACCEPT_TEXT = ["accept", "connect", "agree", "continue", "submit"]
GECKO_DRIVER = os.path.abspath("./geckodriver")

@contextmanager
def WebDriver():
    try:
        service = Service(executable_path=GECKO_DRIVER)
        driver = webdriver.Firefox(service=service)
        yield driver
    except NoSuchDriverException as e:
        logger.error(e)
        logger.info("""If on Pi, try: 
        wget https://www.github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-linux-aarch64.tar.gz
        tar -xf geckodriver-v0.36.0-linux-aarch64.tar.gz""")
        exit(1)
    else:
       driver.quit()

class CaptivePortalNavigator:
    def __init__(self, driver):
        self.driver = driver

    def navigate(self, portal=None, script=None):
        """
        Automatically navigate captive portal, trying a variety of common flows
        """
        if portal:
            self._navigate_portal(portal)
        if script:
            self._navigate_script(script)

    def _navigate_portal(self, portal):
        """
        Automatically navigate captive portal with a known url, trying a variety of common flows
        """
        self.driver.get(portal)
        self.driver.implicitly_wait(1)
        # Simple algorithm:
        #    1. Look for and tick any checkboxes
        #    2. Look for and fill any text inputs with "name" or "email" in the placeholder or label
        #    3. Look for and click any buttons with "accept" or "connect" in the text
        #    4. Profit
        self._check_boxes()
        self._fill_inputs()
        self._click_buttons()

    def _navigate_script(self, script):
        """
        Navigate captive portal using provided script, which is a list of steps to execute
        Each step is a dict with keys:
            - action: "click" or "input"
            - selector: CSS selector for the element to interact with
            - value: (for input) the value to input
        """
        for step in script:
            if step["action"] == "click":
                element = self.driver.find_element(By.CSS_SELECTOR, step["selector"])
                element.click()
            elif step["action"] == "input":
                element = self.driver.find_element(By.CSS_SELECTOR, step["selector"])
                element.send_keys(step["value"])
            else:
                logger.error(f"Unknown action {step['action']} in script")

    def _check_boxes(self):
        checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        for checkbox in checkboxes:
            if not checkbox.is_selected():
                checkbox.click()

    def _fill_inputs(self):
        pass

    def _click_buttons(self):
        buttons = self.driver.find_elements(By.CSS_SELECTOR, "button")
        links = self.driver.find_elements(By.CSS_SELECTOR, "a")
        for button in buttons:
            if self._accept_text_in(button.text.lower()):
                button.click()
                return
        for link in links:
            if self._accept_text_in(link.text.lower()):
                link.click()
                return

    def _accept_text_in(self, text):
        for accept_text in ACCEPT_TEXT:
            if accept_text in text:
                return True
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    with WebDriver() as driver:
        navigator = CaptivePortalNavigator(driver)
        navigator.navigate(portal="file:///" + os.path.join(os.getcwd(), "test", "aandw.html"))
        # navigator.navigate(portal="https://www.selenium.dev/selenium/web/web-form.html")
        input()