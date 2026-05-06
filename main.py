"""
A simple Selenium script that checks if we have an internet connection,
and attempts login to the A&W wifi network.
"""

import logging
import os
import re
from contextlib import contextmanager
from subprocess import run
from time import sleep

from tabulate import tabulate

import navigate_portal

LOG_LEVEL = logging.DEBUG
logger = logging.getLogger(__name__)
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')

MIN_SIG_STRENGTH = 50

# Validate environment
def cmd_exists(cmd):
	return run(f"command -v {cmd}", shell=True).returncode == 0
# Todo: Use logger.error and exit so user gets full list of missing stuff
assert run("command -v ping", shell=True).returncode == 0, "ping command not found. Please install ping and try again."
assert run("command -v nmcli", shell=True).returncode == 0, "nmcli command not found. Please install nmcli (sudo apt install network-manager) and try again."

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
    ping_return = run("ping -c 1 1.1.1.1", shell=True, capture_output=True, text=True)
    if "1 packets transmitted, 1 received" in ping_return.stdout:
        return True
    elif "1 packets transmitted, 0 received" in ping_return.stdout or "Network is unreachable" in ping_return.stderr:
        return False
    else:
        assert False, f"ping returning unexpected output: \nstdout: {ping_return.stdout}\n\nstderr: {ping_return.stderr}"

def get_ssids():
    global logger
    ssids = {}
    nmcli_return =  run("nmcli device wifi list", shell=True, capture_output=True, text=True)
    logger.debug(nmcli_return.stdout)
    for line in nmcli_return.stdout.splitlines():
        logger.debug(f"Scanning line: {line}")
        try:
            ssid = re.search(string=line, pattern=r"(?<=[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}\s{2}).+(?=(Infra|Mesh))")[0].strip()
            security = re.search(string=line, pattern=r"(?<=[_▂▄▆█]  )(WPA|802\.1X|--).+")[0].strip()
            signal = int(re.search(string=line, pattern=r"(?<=Mbit/s)\s*\d{1,3}")[0].strip())
            logger.debug(f"Found network\n\tname     = {ssid}\n\tsignal   = {signal}\n\tsecurity = {security}")
            if ssid not in ssids.keys() and signal >= MIN_SIG_STRENGTH:
                logger.debug('Writing to dict...')
                ssids[ssid] = (security == "--") # True if open network
            elif signal < MIN_SIG_STRENGTH: # nmcli returns sorted in order of signal strength
               break
        except TypeError as e:
            logger.warning(e)
            logger.warning("This is expected exactly once per scan.")
    return ssids

def connect_to_ssid(ssid):
    conn_attempt_return = run(f"nmcli d wifi connect '{ssid}'", shell=True, capture_output=True, text=True)
    logger.debug(f"\"{conn_attempt_return.args}\" returned {conn_attempt_return.returncode}")
    logger.info(f"{conn_attempt_return.stdout[5:-1]}") # Slice list to strip ANSI terminal codes
    if conn_attempt_return.returncode != 0:
        logger.error(f"{conn_attempt_return.stderr}")
    return conn_attempt_return.returncode

# ssids = get_ssids()
# logger.debug(ssids)

# known_networks = get_known_networks()
# logger.debug(known_networks)

connect_to_ssid("BeMyGuest")
exit(0)

with navigate_portal.WebDriver() as driver:

    while True:
        connected = False # has_internet() # force false for dev testing
        if connected:
            logger.info("Internet connection is up!")
        else:
            logger.info("No internet connection.")
            
            navigate_portal.CaptivePortalNavigator(driver).navigate(portal="http://1.1.1.1") # Use an http IP to trigger captive portal
            for ssid, is_open in get_ssids().items():
                logger.debug(f"{ssid} is {'open' if is_open else 'secure'}")
                if is_open():
                    connect_to_ssid(ssid)
        #sleep(5)
        input("Press enter to run next cycle") # manual run for debug
