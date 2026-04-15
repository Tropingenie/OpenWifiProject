Walking around the city, I noticed that I was constantly passing by open Wifi networks. Tim Hortons, Starbucks, A&W, and too many more to list them all. Being a frugal person, and with my engineering background, I knew it would be a simple matter to run a NAT server with a Python/Selenium script to automatically connect to all of these, thus saving data and, in my case, money.

## Features
> [!IMPORTANT]  
> This project is currently WIP. This is therefore a planning document, not a guarantee

- [ ] Automatically scan and connect to open networks
- [ ] Automatically attempt login through captive portals
- [ ] Simple, script-based logging scripts for known SSIDs
- [ ] Automated VPN connection (using CLI or WireGuard)
  - [ ] ProtonVPN
  - [ ] NordVPN
  - [ ] Surfshark
- [ ] DNS Configuration
  - [ ] Custom DNS
  - [ ] [Pi-hole®](https://github.com/pi-hole/pi-hole?tab=readme-ov-file)
- [ ] Ready to order PCB and enclosure

## Development
I started by purchasing an Arduino Uno R4, as I was expecting to use the onboard ESP32 for most of the heavy lifting, and the Renesas for running extra logic. The Arduino also meant my BOM was starting out at the price of a(n expensive) cup of coffee. However, this proved to be a hack at best, so I quickly pivoted to a Raspberry Pi Zero 2 W for simplicity, allowing me to use the Raspbian DE for initial development and later pivot to running Selenium headless. This ran me $40 on Amazon Canada, but at the end of the day it is still less than a month's phone bill. An allegedly genuine Zero 1 W is as low as $22 on AliExpress, and should be a drop in replacement. In fact, another benefit of using the Raspberry Pi platform is that it is actually just Debian, meaning any SBC running Linux should be able to be used for implementation with minor or no changes to the code.

For development, I am using a mix of [Nobara](https://nobaraproject.org/) (a custom Fedora by GloriousEggroll), which runs on my PC, and Debian, which runs on my Chromebook. Portability will be achieved by using python, git, and venv, as well as dynamically scanning for the required programs in the PATH at runtime. Since this is meant to run on Raspbian first and foremost, a Linux environment will always be assumed, especially since WiFi connectivity scripting relies heavily on `nmcli`, as Python lacks an up-to-date library. Hardware is always an interesting beast to interact with git (not to mention licensing), but a PCB will be designed in KiCAD, simulated using Diode, and an enclosure designed using Onshape. Initial hardware prototyping, however, will simply copy [SlimeVR](https://docs.slimevr.dev/diy/tracker-schematics.html) and use TP4056 charging boards. Power consumption of the RPi Zero 2 W is pending review, as WiFi does tend to be pretty hungry.

## License
All code (software) is under the GNU GPL 3.0 license. Hardware designs remain all rights reserved; [please email](mailto:github.com.pruning991@passinbox.com) for a hardware license.

    OpenWifiProject, an RPi based auto login for public wifi portals
    Copyright (C) 2025  Tropingenie

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
