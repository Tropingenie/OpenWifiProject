import logging
import os
import re
from contextlib import contextmanager
from subprocess import run
from time import sleep

from playwright.sync_api import Playwright, sync_playwright, expect
from playwright._impl._errors import TimeoutError, Error

ACCEPT_TEXT = ["accept", "connect", "agree", "continue", "submit", "internet", "access", "online"]
EMAIL_TEXT = ["email"]
PASSWORD_TEXT = ["password"]
NAME_TEXT = ["name"]

logger = logging.getLogger(__name__)

@contextmanager
def WebDriver():
    driver = None
    try:
        with sync_playwright() as playwright:
            driver = playwright
            yield playwright
    except Exception as e:
        logger.error(e)
        logger.info("""If on Pi, try: 
        playwright install-deps
        playwright install webkit""")
        raise

class CaptivePortalNavigator:
    def __init__(self, playwright=None):
        if playwright is None:
            with WebDriver() as p:
                self.playwright = p
        else:
            self.playwright = playwright

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

        browser = self.playwright.webkit.launch(headless=False)
        context = browser.new_context(ignore_https_errors=True)
        self.page = context.new_page()
        self.page.goto(portal, wait_until="networkidle")

        # Simple algorithm:
        #    1. Look for and tick any checkboxes
        #    2. Look for and fill any text inputs with "name" or "email" in the placeholder or label
        #    3. Look for and click any buttons with "accept" or "connect" in the text
        #    4. Profit
        if __name__ == "__main__":
            input("Page loaded")
        self._check_boxes()
        if __name__ == "__main__":
            input("Boxes checked")
        self._fill_inputs()
        if __name__ == "__main__":
            input("Inputs filled")
        self._click_buttons()
        if __name__ == "__main__":
            input("Buttons clicked")
            
            input("Debug: Press enter to close Playwright.")
        context.close()
        browser.close()

    def _navigate_script(self, script):
        raise NotImplementedError

    def _check_boxes(self):
        check_boxes = self.page.get_by_role("checkbox")
        radio_buttons = self.page.get_by_role("radio")
        locators = []
        if check_boxes is not None:
            locators.extend(check_boxes.all())
        if radio_buttons is not None:
            locators.extend(radio_buttons.all())

        for loc in locators:
            if not loc.is_checked():
                loc.click(timeout=500)

    def _fill_inputs(self):
        email_inputs = self.page.get_by_role("textbox", name=re.compile("|".join(EMAIL_TEXT), re.IGNORECASE))
        name_inputs = self.page.get_by_role("textbox", name=re.compile("|".join(NAME_TEXT), re.IGNORECASE))
        password_inputs = self.page.get_by_role("textbox", name=re.compile("|".join(PASSWORD_TEXT), re.IGNORECASE))
        all_inputs = self.page.get_by_role("textbox")
        for loc in all_inputs.all():
            try:
                if loc in email_inputs.all():
                    loc.fill("email@domain.com", timeout=500)
                elif loc in name_inputs.all():
                    loc.fill("name", timeout=500)
                elif loc in password_inputs.all():
                    pass # assume no password (and fail if there is one)
                else:
                    loc.fill("lorem ipsum dolor", timeout=500)
            except (TimeoutError, Error):
                pass # expected, e.g. if element is not interactable

    def _click_buttons(self):
        links = self.page.get_by_role("link", name=re.compile("|".join(ACCEPT_TEXT), re.IGNORECASE))
        buttons = self.page.get_by_role("button", name=re.compile("|".join(ACCEPT_TEXT), re.IGNORECASE)) 
        locators = []
        if links is not None:
            locators.extend(links.all())
        if buttons is not None:
            locators.extend(buttons.all())
        try:
            for loc in locators:
                loc.click(timeout=500)
        except TimeoutError:
            pass # expected if the first locator works


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    with WebDriver() as driver:
        navigator = CaptivePortalNavigator(driver)
        #navigator.navigate(portal="file:///" + os.path.join(os.getcwd(), "test", "aandw.html"))
        navigator.navigate(portal="https://www.selenium.dev/selenium/web/web-form.html")
        input("press enter to exit")
