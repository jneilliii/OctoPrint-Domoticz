---
layout: plugin

id: domoticz
title: OctoPrint-Domoticz
description: Simple plugin to control light switches via Domoticz.
author: jneilliii
license: AGPLv3

date: 2017-11-24

homepage: https://github.com/jneilliii/OctoPrint-Domoticz
source: https://github.com/jneilliii/OctoPrint-Domoticz
archive: https://github.com/jneilliii/OctoPrint-Domoticz/archive/master.zip

tags:
- sonoff
- domoticz
- smartplug
- power

screenshots:
- url: /assets/img/plugins/domoticz/screenshot.png
  alt: Screenshot
  caption: Navbar screenshot
- url: /assets/img/plugins/domoticz/settings.png
  alt: Settings
  caption: Settings screenshot

featuredimage: /assets/img/plugins/domoticz/screenshot.png

compatibility:

  octoprint:
  - 1.2.0

  os:
  - linux
  - windows
  - macos
  - freebsd

---
This plugin is to control light switches through Domoticz via web calls.

## Configuration

Once installed go into settings and enter the ip address for your TP-Link Smartplug device. Adjust additional settings as needed.

## Settings Explained

- **Device**
  - The ip and port of the Domoticz server.
- **Index**
  - Index number reprensenting the switch to control.
- **Warn**
  - The left checkbox will always warn when checked.
  - The right checkbox will only warn when printer is printing.
- **GCODE**
  - When checked this will enable the processing of M80 and M81 commands from gcode to power on/off plug.  Syntax for gcode command is M80/M81 followed by hostname/ip and index.  For example if your plug is 192.168.1.2 and index of 1 your gcode command would be **M80 192.168.1.2 1**
- **postConnect**
  - Automatically connect to printer after plug is powered on.
  - Will wait for number of seconds configured in **Auto Connect Delay** setting prior to attempting connection to printer.
- **preDisconnect**
  - Automatically disconnect printer prior to powering off the plug.
  - Will wait for number of seconds configured in **Auto Disconnect Delay** prior to powering off the plug.
- **Cmd On**
  - When checked will run system command configured in **System Command On** setting after a delay in seconds configured in **System Command On Delay**.
- **Cmd Off**
  - When checked will run system command configured in **System Command Off** setting after a delay in seconds configured in **System Command Off Delay**.
