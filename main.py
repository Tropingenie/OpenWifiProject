"""
A simple Selenium script that checks if we have an internet connection,
and attempts login to the A&W wifi network.
"""

from contextlib import contextmanager
from subprocess import run
from time import sleep

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchDriverException
from tabulate import tabulate

@contextmanager
def WebDriver():
    try:
        driver = webdriver.Chrome()
        yield driver
    except NoSuchDriverException as e:
        print(e)
        exit(1)
    finally:
       driver.quit()

# Validate environment
assert run("command -v ping", shell=True).returncode == 0, "ping command not found. Please install ping and try again."
assert run("command -v nmcli", shell=True).returncode == 0, "nmcli command not found. Please install nmcli (sudo apt install network-manager) and try again."

run_return = run("nmcli dev", shell=True, capture_output=True, text=True)
#print(f"nmcli device list\n{run_return.stdout}")
wifi_exists = any([w in run_return.stdout for w in ['wifi', 'wlan', '802.11']])
if not wifi_exists:
    print(f"No wifi interface detected! Please check output of 'nmcli dev' below:\n{run_return.stdout}")
    exit(1)

with WebDriver() as driver:

    while True:
        run_return = run("ping -c 1 1.1.1.1", shell=True, capture_output=True, text=True)
        # print(run_return.stdout)
        if "1 packets transmitted, 1 received" in run_return.stdout:
            print("Internet connection is up!")
        elif "1 packets transmitted, 0 received" in run_return.stdout:
            print("No internet connection.")
            run_return = run("nmcli device wifi list", shell=True, capture_output=True, text=True)
            print(f"# nmcli wifi list\n{run_return.stdout+run_return.stderr}")
            table = [line.split('\t') for line in run_return.stdout.splitlines()]
            print(tabulate(table))
        else:
            assert False, f"ping returning unexpected output: {run_return.stdout}"
        sleep(5)
