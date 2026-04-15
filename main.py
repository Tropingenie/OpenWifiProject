"""
A simple Selenium script that checks if we have an internet connection,
and attempts login to the A&W wifi network.
"""

from contextlib import contextmanager
from subprocess import run
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By

@contextmanager
def WebDriver():
    try:
        driver = webdriver.Chrome()
        yield driver
    finally:
       driver.quit()

# Validate environment
assert run(["command", "-v", "ping"]) == 0, "ping command not found. Please install ping and try again."
assert run(["command", "-v", "nmcli"]) == 0, "nmcli command not found. Please install nmcli and try again."

with WebDriver() as driver:

    while True:
        run_return = run(["ping", "-c", "1", "1.1.1.1"], capture_output=True, text=True)
        # print(run_return.stdout)
        if "1 packets transmitted, 1 received, 0% packet loss" in run_return.stdout:
            print("Internet connection is up!")
        elif "1 packets transmitted, 0 received, 100% packet loss" in run_return.stdout:
            print("No internet connection.")
        else:
            assert False, f"ping returning unexpected output: {run_return.stdout}"
        sleep(5)
