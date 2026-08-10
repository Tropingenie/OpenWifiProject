import re
import logging

from playwright.sync_api import sync_playwright


logger = logging.getLogger(__name__)


class PortalNavigator():

    def __init__(self, p):
        logger.debug("Initializing Playwright")
        self.p = p
        self.browser = p.webkit.launch()
        self.context = self.browser.new_context(
            ignore_https_errors=True
        )
        self.page = self.context.new_page()

        self.page.route(
            "**/*.{png,jpg,jpeg,gif,svg,css,font}",
            lambda route: route.abort()
        )


    def auto_login(self):
        page = self.page # workaround due to copy pasting from other code
        logger.debug("nav to networkcheck...")
        page.goto("http://networkcheck.kde.org", wait_until="networkidle")
        logger.debug(page.content())
#        with open("portal.html", "w") as file:
#            file.write(page.content())
        #page.screenshot(path="portal.png", full_page=True)
        if "fgtauth" in page.content():
            # fortinet debug stuff
            logger.debug(f"current url: {page.url}")
            logger.debug(f"waiting for '**/fgtauth*'")
            try:
                page.wait_for_url("**/fgtauth*") # matches the fortigate redirect
            except Exception as e:
                logger.error(e)
            logger.debug(f"current url: {page.url}")
            logger.debug(page.content())
            # end fortinet debug stuff

            # fortigate portal
            logger.debug("looking for button...")
            link_locator = page.get_by_role("button", name="agree").first
            link_locator.click(no_wait_after=True)
        else:
            # a&w portal
            logger.debug("looking for link...")
            link_locator = page.get_by_role("link", name="accept").first
            url = link_locator.get_attribute("href")
            try:
                page.goto(url, timeout=10000)
            except Exception as e:
                logger.error(e)

        page.wait_for_timeout(5000) # wait for connection to stabilise
