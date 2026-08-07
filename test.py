import re

from playwright.sync_api import sync_playwright


def auto_login():
    with sync_playwright() as p:
        browser = p.webkit.launch()
        context = browser.new_context(
            ignore_https_errors=True
        )
        page = context.new_page()

        page.route(
            "**/*.{png,jpg,jpeg,gif,svg,css,font}",
            lambda route: route.abort()
        )

        print("nav to networkcheck...")
        page.goto("http://networkcheck.kde.org", wait_until="networkidle")
#       ok = page.get_by_text("OK")
#       print(ok is not None)
        print(page.content())
        with open("portal.html", "w") as file:
            file.write(page.content())
        #page.screenshot(path="portal.png", full_page=True)
        if "fgtauth" in page.content():
            # fortinet debug stuff
            print(f"current url: {page.url}")
            print(f"waiting for '**/fgtauth*'")
            try:
                page.wait_for_url("**/fgtauth*") # matches the fortigate redirect
            except Exception as e:
                print(e)
            print(f"current url: {page.url}")
            print(page.content())
            # end fortinet debug stuff

            # fortigate portal
            print("looking for button...")
            link_locator = page.get_by_role("button", name="agree").first
            link_locator.click(no_wait_after=True)
        else:
            # a&w portal
            print("looking for link...")
            link_locator = page.get_by_role("link", name="accept").first
            url = link_locator.get_attribute("href")
            try:
                page.goto(url, timeout=3000)
            except Exception as e:
                print(e)

        page.wait_for_timeout(5000) # wait for connection to stabilise

        # Verify internet access by probing a simple lightweight endpoint
        try:
            response = page.request.get("http://connectivitycheck.gstatic.com/generate_204", timeout=5000)
            if response.status == 204:
                print("[+] Internet connection verified!")
        except Exception as e:
            print(e)
            print("[-] Check internet status manually.")
