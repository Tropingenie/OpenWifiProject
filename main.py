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
from shared import nmcli_lock

from test import auto_login

LOG_LEVEL = logging.DEBUG
FORCE_NO_INTERNET = False
logger = logging.getLogger(__name__)
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')

MIN_SIG_STRENGTH = 50
CONNECTION_TIMEOUT = 30 # seconds to wait for nmcli conn to finish
POLL_RATE_LONG = 5 # seconds to wait between checks when you have internet
POLL_RATE_SHORT = 1 # seconds to wait between checks when without internet
PING_TIMEOUT = 5 # 5000 ms

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
        logger.debug(ping_return.stdout.strip())
    if len(ping_return.stderr) > 0:
        logger.debug(ping_return.stderr.strip())
    def check_curl():
        try:
            curl_return = run("curl networkcheck.kde.org", shell=True, capture_output=True, text=True, timeout=PING_TIMEOUT)
            logger.debug(f"curl returned returncode: {curl_return.returncode} with page contents:" + (f"\n{curl_return.stdout.strip()}" if len(curl_return.stdout) > 0 else ""))
            return curl_return.returncode == 0 and curl_return.stdout.strip() == "OK"
        except (TimeoutError, TimeoutExpired) as e:
            logger.debug(e)
            return False
    logger.debug(f"ping returned returncode: {ping_return.returncode}")
    curl_result = check_curl()
    return (ping_return.returncode == 0) and curl_result

def get_ssids():
    logger.debug("Fetching ssids")
    unique_ssids = set()
    nmcli_return =  run(f"nmcli -t -f \"SECURITY,SIGNAL,SSID\" device wifi list --rescan yes ifname {IFNAME_2}", shell=True, capture_output=True, text=True)
    if len(nmcli_return.stdout) > 0:
        logger.debug(nmcli_return.stdout.strip())
    if len(nmcli_return.stderr) > 0:
        logger.error(nmcli_return.stderr.strip())
    if nmcli_return.returncode != 0:
        logger.error("Error while fetching ssids")
        return

    for line in nmcli_return.stdout.splitlines():
        logger.debug(f"Scanning line: {line}")
        try:
            security, signal, ssid = line.split(':', 3)
        except ValueError as e:
            # Workaround for when ':' appears in the SSID
            # SSID spec allows for any unicode so string parsing should be removed
            logger.error(f"Intercepted ValueError when parsing {line}")
            logger.error(e)
            pass

        signal = int(signal) # strtoi
        logger.debug(f"Found network\n\tname     = {ssid}\n\tsignal   = {signal}\n\tsecurity = {security}")
        if ssid not in unique_ssids:
            unique_ssids.add(ssid)
            if signal < MIN_SIG_STRENGTH: # nmcli returns sorted in order of signal strength
                break
            elif ssid == "": # hidden network
                continue
            else:
                yield ssid, (security == "") # True if open network

    if len(unique_ssids) < 1:
        logging.warning("No SSIDs found! WLAN1 may be broken.")
    else:
        logging.debug(f"Parsed {len(unique_ssids)} unique ssids\n{unique_ssids}")


ssid_list = []

def connect_to_ssid(ssid):
    global ssid_list
    global nmcli_lock
    try:
        with nmcli_lock:
            conn_attempt_return = run(f"nmcli d wifi connect '{ssid}' ifname {IFNAME_2}", shell=True, capture_output=True, text=True, timeout=CONNECTION_TIMEOUT)
        ssid_list.append(ssid)
    except (TimeoutError, TimeoutExpired) as e:
        logger.warning(f"Timed out while connecting to {ssid}.")
        logger.debug(e)
        return -1 # return non-Unix return code so we know it is Python
    logger.debug(f"\"{conn_attempt_return.args}\" returned {conn_attempt_return.returncode}")
    logger.info(f"{conn_attempt_return.stdout[5:-1]}") # Slice list to strip ANSI terminal codes
    if conn_attempt_return.returncode != 0:
        logger.error(f"{conn_attempt_return.stderr.strip()}")
    return conn_attempt_return.returncode

def cleanup_ssids():
    global ssid_list
    for ssid in ssid_list:
        cleanup_return = run(f"nmcli connection delete id '{ssid}'", shell=True, capture_output=True)
        cleanup_return.check_returncode()
    ssid_list.clear()

def get_known_networks():
    nmcli_return = run("nmcli -t -g \"NAME\" conn show", shell=True, text=True, capture_output=True)
    logger.info("Pulling known SSID list")
    if len(nmcli_return.stdout + nmcli_return.stderr) > 0:
        logger.debug(nmcli_return.stdout + nmcli_return.stderr.strip())
    return nmcli_return.stdout

# ssids = get_ssids()
# logger.debug(ssids)

known_networks = get_known_networks()
# logger.debug(known_networks)

def main():
#    try:
#        with navigate_portal.WebDriver() as driver:
    if True:
        if True:
            while True:
                # FORCE_NO_INTERNET is a dev switch for debugging
                connected = has_internet() and not FORCE_NO_INTERNET
                if connected:
                    internet_check_interval = POLL_RATE_LONG
                    logger.info("Internet connection is up!")
                else:
                    logger.info("No internet connection.")
                    auto_login()
#                    cleanup_ssids()
#                    internet_check_interval = POLL_RATE_SHORT
#                    for ssid, is_open in get_ssids():
#                        logger.debug(f"{ssid} is {'open' if is_open else 'secure'}")
#                        if (is_open and connect_to_ssid(ssid) == 0 and not has_internet()):
#                            navigate_portal.CaptivePortalNavigator(driver).navigate(portal="http://1.1.1.1") # Use an http IP to trigger captive portal
#                            if has_internet():
#                                break
#                            elif LOG_LEVEL == logging.DEBUG:
#                                logger.error("Portal navigation failed.")
#                                input("Press enter to continue.")
#                        elif has_internet(): # check is quick enough that doing it twice isn't a problem
#                            break
#                        elif(ssid in known_networks and connect_to_ssid(ssid) == 0 and has_internet()):
#                            break
                logger.debug("Scan cycle finished")
                sleep(internet_check_interval)
                #input("Press enter to run next cycle") # manual run for debug
#    finally:
#        cleanup_ssids()


if __name__ == "__main__":
    main()
