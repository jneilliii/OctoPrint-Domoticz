# OctoPrint-Domoticz

This plugin is to control switches via Domoticz server.

[Changelog](changelog.md)

##  Screenshots
![screenshot](screenshot.png)

![screenshot](settings.png)

![screenshot](domoticz_editor.png)

## Setup

Install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:

    https://github.com/jneilliii/OctoPrint-Domoticz/archive/master.zip


## Configuration

Once installed go into settings and enter the details for your Domoticz server connection and switch index. Adjust additional settings as needed.

## Settings Explained

- **IP:PORT**
  - The ip and port of Domoticz server.
- **Index**
  - Index number reprensenting the switch to control.
- **Icon**
  - Icon class name from the [fontawesome](https://fontawesome.com/v3.2.1/icons/) library.
- **Label**
  - Title attribute on icon that shows on mouseover.
- **Username**
  - Username used to connect to web interface. If authentication is not configured on your Domoticz server leave this blank.
- **Password**
  - Password used to connect to web interface. If authentication is not configured on your Domoticz server leave this blank.
- **Warn**
  - The left checkbox will always warn when checked.
  - The right checkbox will only warn when printer is printing.
- **GCODE**
  - When checked this will enable the processing of M80 and M81 commands from gcode to power on/off plug.  Syntax for gcode command is M80/M81 followed by hostname/ip and index.  For example if your plug is 192.168.1.2:8080 and index of 1 your gcode command would be **M80 192.168.1.2:8080 1**
  - As of version 0.0.3 you can now use the custom gcode commands `@DOMOTICZON` and `@DOMOTICZOFF`. The difference here is that you only need to supply the index value with the command.  For example `@DOMOTICZOFF 1` will turn the switch with an Index of 1 off.
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
  
## Get Help

If you experience issues with this plugin or need assistance please use the issue tracker by clicking issues above.

### Additional Plugins

Check out my other plugins [here](https://plugins.octoprint.org/by_author/#jneilliii)

### Sponsors
- Andreas Lindermayr
- [@Mearman](https://github.com/Mearman)
- [@TxBillbr](https://github.com/TxBillbr)
- Gerald Dachs
- [@TheTuxKeeper](https://github.com/thetuxkeeper)
- @tideline3d
- [SimplyPrint](https://simplyprint.dk/)
- [Andrew Beeman](https://github.com/Kiendeleo)
- [Calanish](https://github.com/calanish)
- [Will O]https://github.com/4wrxb

### Support My Efforts
I, jneilliii, programmed this plugin for fun and do my best effort to support those that have issues with it, please return the favor and leave me a tip or become a Patron if you find this plugin helpful and want me to continue future development.

[![Patreon](patreon-with-text-new.png)](https://www.patreon.com/jneilliii) [![paypal](paypal-with-text.png)](https://paypal.me/jneilliii)

<small>No paypal.me? Send funds via PayPal to jneilliii&#64;gmail&#46;com</small>


