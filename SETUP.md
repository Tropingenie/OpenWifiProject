Steps for setting up the Pi

## Polkit
Raspbian by default does not allow certain nmcli commands to be run without sudo. Therefore a pokit rule is added to allow NetworkManager to run without sudo.

First, open the file for editing:

```
sudo nano /etc/polkit-1/rules.d/10-networkmanager.rules
```

And insert:

```
polkit.addRule(function(action, subject) {
    if (action.id.indexOf("org.freedesktop.NetworkManager.") === 0 && subject.active) {
        return polkit.Result.YES;
    }
});
```

Note that this is insecure; in the future a user should be specified.

If polkit does not load the rule, it is likely due to the incorrect file permissions (as polkit is sensitive to those). The following sets the ownership and permissions explicitly to ensure polkit is happy.
```
sudo chown root:polkitd /etc/polkit-1/rules.d/10-networkmanager.rules
```
```
sudo chmod 640 /etc/polkit-1/rules.d/10-networkmanager.rules
```

## Core Clock
To reduce power consumption, as well as minimize chances of brownout, the Pi is underclocked to 800 MHz.

To do so, we edit the boot configs by opening:

```
sudo nano /boot/firmware/config.txt
```

And appending:

```ini
# Limit peak CPU power draw to stabilize USB rail
arm_freq=800
core_freq=400
```

Then reboot:

```
sudo reboot
```

To check the clock applied, the following command should return 800000000:

```
vcgencmd measure_clock arm
```

## Python Script
Clone the repo

```
git clone www.github.com/Tropingenie/OpenWifiRouter.git
```
```
cd OpenWifiRouter
```

Set up the virtual environment:

```
python -m venv .venv
```
```
source .venv/bin/activate
```
```
pip install -r requirements.txt --no-cache-dir
```

Set up Playwright

```
playwright install --with-deps webkit
```
