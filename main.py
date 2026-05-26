"""
A simple Selenium script that checks if we have an internet connection,
and attempts login to the A&W wifi network.
"""

import logging
import os
import re
from contextlib import contextmanager
from subprocess import run, TimeoutExpired
from time import sleep

from tabulate import tabulate

import navigate_portal

LOG_LEVEL = logging.DEBUG
FORCE_NO_INTERNET = False
logger = logging.getLogger(__name__)
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')

MIN_SIG_STRENGTH = 33
CONNECTION_TIMEOUT = 10 # seconds to wait for nmcli conn to finish
POLL_RATE_LONG = 5 # seconds to wait between checks when you have internet
POLL_RATE_SHORT = 1 # seconds to wait between checks when without internet
PING_TIMEOUT = 0.5 # 500 ms

# Interface names
IFNAME_1 = "wlan0" # default pi NIC, use this  as hotspot so we can ssh without internet
IFNAME_2 = "wlan1" # used to connect to WAN

# Validate environment
def cmd_exists(cmd):
	return run(f"command -v {cmd}", shell=True).returncode == 0
# Todo: Use logger.error and exit so user gets full list of missing stuff
assert run("command -v ping", shell=True, capture_output=True).returncode == 0, "ping command not found. Please install ping and try again."
assert run("command -v nmcli", shell=True, capture_output=True).returncode == 0, "nmcli command not found. Please install nmcli (sudo apt install network-manager) and try again."

run_return = run("nmcli dev", shell=True, capture_output=True, text=True)
#print(f"nmcli device list\n{run_return.stdout}")
wifi_exists = any([w in run_return.stdout for w in ['wifi', 'wlan', '802.11']])
if not wifi_exists:
    logger.error(f"No wifi interface detected! Please check output of 'nmcli dev' below:\n{run_return.stdout}")
    exit(1)

run_return = run("nmcli r wifi", shell=True, capture_output=True, text=True)
wifi_enabled = "enabled" in run_return.stdout
if not wifi_enabled:
    logger.error(f"Wifi is disabled! Please enable wifi and try again.")
    exit(1)

del run_return # Clean up namespace

def has_internet():
    try:
        ping_return = run("ping -c 1 1.1.1.1", shell=True, capture_output=True, text=True, timeout=PING_TIMEOUT)
    except (TimeoutError, TimeoutExpired) as e:
        logger.debug(e)
        return False
    if len(ping_return.stdout) > 0:
        logger.debug(ping_return.stdout)
    if len(ping_return.stderr) > 0:
        logger.debug(ping_return.stderr)
    if "1 packets transmitted, 1 received" in ping_return.stdout:
        return True
    elif "1 packets transmitted, 0 received" in ping_return.stdout or "Network is unreachable" in ping_return.stderr:
        return False
    else:
        assert False, f"ping returning unexpected output: \nstdout: {ping_return.stdout}\n\nstderr: {ping_return.stderr}"

def get_ssids():
    nmcli_return =  run(f"nmcli -t -f \"SSID,SECURITY,SIGNAL\" device wifi list --rescan yes ifname {IFNAME_2}", shell=True, capture_output=True, text=True)
    logger.debug(nmcli_return.stdout)
    for line in nmcli_return.stdout.splitlines():
        logger.debug(f"Scanning line: {line}")
        ssid, security, signal = line.split(':')
        signal = int(signal) # strtoi
        logger.debug(f"Found network\n\tname     = {ssid}\n\tsignal   = {signal}\n\tsecurity = {security}")
        if signal < MIN_SIG_STRENGTH: # nmcli returns sorted in order of signal strength
            break
        elif ssid == "": # hidden network
            continue
        else:
            yield ssid, (security == "") # True if open network

ssid_list = []

def connect_to_ssid(ssid):
    global ssid_list
    try:
        conn_attempt_return = run(f"nmcli d wifi connect '{ssid}' ifname {IFNAME_2}", shell=True, capture_output=True, text=True, timeout=CONNECTION_TIMEOUT)
        ssid_list.append(ssid)
    except (TimeoutError, TimeoutExpired) as e:
        logger.warning(f"Timed out while connecting to {ssid}.")
        logger.debug(e)
        return -1 # return non-Unix return code so we know it is Python
    logger.debug(f"\"{conn_attempt_return.args}\" returned {conn_attempt_return.returncode}")
    logger.info(f"{conn_attempt_return.stdout[5:-1]}") # Slice list to strip ANSI terminal codes
    if conn_attempt_return.returncode != 0:
        logger.error(f"{conn_attempt_return.stderr}")
    return conn_attempt_return.returncode

def cleanup_ssids():
    global ssid_list
    for ssid in ssid_list:
        cleanup_return = run(f"nmcli connection delete id '{ssid}'", shell=True, capture_output=True)
        cleanup_return.check_returncode()
    ssid_list.clear()

# ssids = get_ssids()
# logger.debug(ssids)

# known_networks = get_known_networks()
# logger.debug(known_networks)


with navigate_portal.WebDriver() as driver:
    while True:
        # dev switch for debugging
        connected = has_internet() and not FORCE_NO_INTERNET

        if connected:
            internet_check_interval = POLL_RATE_LONG
            logger.info("Internet connection is up!")
        else:
            logger.info("No internet connection.")
            cleanup_ssids()
            internet_check_interval = POLL_RATE_SHORT
            for ssid, is_open in get_ssids():
                logger.debug(f"{ssid} is {'open' if is_open else 'secure'}")
                if is_open:
                    if connect_to_ssid(ssid) == 0: # non zero return code indicates error
                        if not has_internet():
                            navigate_portal.CaptivePortalNavigator(driver).navigate(portal="http://1.1.1.1") # Use an http IP to trigger captive portal
                            if has_internet():
                                break
                            elif LOG_LEVEL == logging.DEBUG:
                                logger.error("Portal navigation failed.")
                                input("Press enter to continue.")
                        else:
                            break
        sleep(internet_check_interval)
        #input("Press enter to run next cycle") # manual run for debug
