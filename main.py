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


ssids = get_ssids()
logger.debug(ssids)
exit(0)

with navigate_portal.WebDriver() as driver:

    while True:
        connected = has_internet() # force false for dev testing
        if connected:
            logger.info("Internet connection is up!")
        else:
            logger.info("No internet connection.")
#            dev_list_return =
            logger.debug(f"# nmcli wifi list\n\nstdout:\n{dev_list_return.stdout}\n\nstderr:\n{dev_list_return.stderr}")
            lines = dev_list_return.stdout.splitlines()
            lines.pop(0)
            for line in lines: # Parse all but the header
                logger.debug(f"Parsing line: {line}")
                logger.info(f"Found network: {line[27:50]}")
                if "WPA" in line:
                    logger.info(f"{line[27:50]} is a secure network.")
                    logger.info("Checking nmcli list of known wifi connections...")
                    # Nice one liner to get a list of known SSIDs by Rich S: https://askubuntu.com/a/1542499
                    ssid_return = run(r'nmcli -t -f name,type c | sed -nE "s/(.*)\:.*wireless/\1/p" | xargs -I {} nmcli -f 802-11-wireless.ssid c show {} | sed -nE "s/.*\s+(.*)/\1/p"', shell=True, capture_output=True, text=True)
                    for ssid in ssid_return.stdout.splitlines():
                        logger.debug(f"Known network: {ssid}")
                        if ssid in line:
                            logger.info(f"Attempting to connect to {ssid}...")
                            conn_attempt_return = run(f"nmcli d wifi connect '{ssid}'", shell=True, capture_output=True, text=True)
                            logger.debug(f"nmcli connection attempt\n\nstdout:\n{conn_attempt_return.stdout}\n\nstderr:\n{conn_attempt_return.stderr}")
                            break
                else:
                    logger.info(f"{line[27:50]} is an open network.")
                    conn_attempt_return = run(f"nmcli d wifi connect '{line[27:50].strip()}'", shell=True, capture_output=True, text=True)
                    logger.debug(f"nmcli connection attempt\n\nstdout:\n{conn_attempt_return.stdout}\n\nstderr:\n{conn_attempt_return.stderr}")
                    # For now, we only use generic mode
                    navigate_portal.CaptivePortalNavigator(driver).navigate(portal="http://1.1.1.1") # Use an http IP to trigger captive portal

                if has_internet():
                    logger.info("Internet connection is up!")
                    break
        #sleep(5)
        input("Press enter to run next cycle") # manual run for debug
