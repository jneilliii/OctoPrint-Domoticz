# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2020-03-27
### Fixed
- Moved system commands and printer connection logic to server-side processing.

## [0.1.1] - 2019-10-22
### Fixed
- Issues introduced in last release that prevented the plugin from working.

## [0.1.0] - 2019-10-06
### Added
- Python 3 compatibility

## [0.0.3] - 2018-11-03
### Added
- Added custom `@DOMOTICZON` and `@DOMOTICZOFF` GCODE commands.
- Bypass previously delayed power off trigger if `Warn While Printing` option is enabled.

## [0.0.2] - 2018-07-07
### Added
- User authentication to Domoticz server.

### Notes
- If authenthication is not enabled leave username and password blank.
- Passwords are stored in plain text and encoded during web call.

## [0.0.1] - 2018-07-06
### Added
- Initial release.

[0.1.1]: https://github.com/jneilliii/OctoPrint-Domoticz/tree/0.1.1
[0.1.0]: https://github.com/jneilliii/OctoPrint-Domoticz/tree/0.1.0
[0.0.3]: https://github.com/jneilliii/OctoPrint-Domoticz/tree/0.0.3
[0.0.2]: https://github.com/jneilliii/OctoPrint-Domoticz/tree/0.0.2
[0.0.1]: https://github.com/jneilliii/OctoPrint-Domoticz/tree/0.0.1
