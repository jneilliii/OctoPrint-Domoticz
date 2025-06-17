# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import os
import threading
import time

import octoprint.plugin
import octoprint.util
import requests
from octoprint.access.permissions import Permissions, ADMIN_GROUP, USER_GROUP
from flask_babel import gettext


class domoticzPlugin(
        octoprint.plugin.SettingsPlugin,
        octoprint.plugin.AssetPlugin,
        octoprint.plugin.TemplatePlugin,
        octoprint.plugin.SimpleApiPlugin,
        octoprint.plugin.StartupPlugin,
):
        def __init__(self):
                self._logger = logging.getLogger("octoprint.plugins.domoticz")
                self._domoticz_logger = logging.getLogger("octoprint.plugins.domoticz.debug")

        ##~~ StartupPlugin mixin

        def on_startup(self, host, port):
                # setup customized logger
                from octoprint.logging.handlers import CleaningTimedRotatingFileHandler

                domoticz_logging_handler = CleaningTimedRotatingFileHandler(
                        self._settings.get_plugin_logfile_path(postfix="debug"),
                        when="D",
                        backupCount=3,
                )
                domoticz_logging_handler.setFormatter(
                        logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
                )
                domoticz_logging_handler.setLevel(logging.DEBUG)

                self._domoticz_logger.addHandler(domoticz_logging_handler)
                self._domoticz_logger.setLevel(
                        logging.DEBUG
                        if self._settings.get_boolean(["debug_logging"])
                        else logging.INFO
                )
                self._domoticz_logger.propagate = False

        def on_after_startup(self):
                self._logger.info("Domoticz loaded!")

        ##~~ SettingsPlugin mixin

        def get_settings_defaults(self):
                return {
                        "debug_logging": False,
                        "arrSmartplugs": [
                                {
                                        "ip": "",
                                        "displayWarning": True,
                                        "ignoreSSL": False,
                                        "idx": "1",
                                        "warnPrinting": False,
                                        "gcodeEnabled": False,
                                        "gcodeOnDelay": 0,
                                        "gcodeOffDelay": 0,
                                        "autoConnect": True,
                                        "autoConnectDelay": 10.0,
                                        "autoDisconnect": True,
                                        "autoDisconnectDelay": 0,
                                        "sysCmdOn": False,
                                        "sysRunCmdOn": "",
                                        "sysCmdOnDelay": 0,
                                        "sysCmdOff": False,
                                        "sysRunCmdOff": "",
                                        "sysCmdOffDelay": 0,
                                        "currentState": "unknown",
                                        "btnColor": "#808080",
                                        "username": "",
                                        "password": "",
                                        "passcode": "",
                                        "icon": "icon-bolt",
                                        "label": "",
                                }
                        ],
                }

        def on_settings_save(self, data):
                old_debug_logging = self._settings.get_boolean(["debug_logging"])

                octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

                new_debug_logging = self._settings.get_boolean(["debug_logging"])
                if old_debug_logging != new_debug_logging:
                        if new_debug_logging:
                                self._domoticz_logger.setLevel(logging.DEBUG)
                        else:
                                self._domoticz_logger.setLevel(logging.INFO)

        def get_settings_version(self):
                return 5

        def on_settings_migrate(self, target, current=None):
                if current is None or current < 3:
                        # Reset plug settings to defaults.
                        self._logger.debug("Resetting arrSmartplugs for domoticz settings.")
                        self._settings.set(
                                ["arrSmartplugs"], self.get_settings_defaults()["arrSmartplugs"]
                        )
                if current == 3:
                        # add new properties to configured switches
                        arr_smart_plugs_new = []
                        for plug in self._settings.get(['arrSmartplugs']):
                                plug["passcode"] = ""
                                arr_smart_plugs_new.append(plug)
                        self._settings.set(["arrSmartplugs"], arr_smart_plugs_new)
                if current < 5 and current > 2:
                        # add new properties to configured switches
                        arr_smart_plugs_new = []
                        for plug in self._settings.get(['arrSmartplugs']):
                                plug["ip"] = "http://" + plug["ip"]
                                plug["ignoreSSL"] = False
                                arr_smart_plugs_new.append(plug)
                        self._settings.set(["arrSmartplugs"], arr_smart_plugs_new)

        ##~~ AssetPlugin mixin

        def get_assets(self):
                return {"js": ["js/domoticz.js"], "css": ["css/domoticz.css"]}

        ##~~ TemplatePlugin mixin

        def get_template_configs(self):
                return [
                        {"type": "navbar", "custom_bindings": True},
                        {"type": "settings", "custom_bindings": True},
                ]

        ##~~ SimpleApiPlugin mixin

        def turn_on(self, plug_ip, plug_idx, ignoreSSL, username="", password="", passcode=""):
                if self._settings.get(["singleRelay"]):
                        plug_idx = ""
                self._domoticz_logger.debug(f"Turning on {plug_ip} index {plug_idx}.")
                plug = self.plug_search(self._settings.get(["arrSmartplugs"]), "ip", plug_ip, "idx", plug_idx)
                try:
                        str_url = f"{plug_ip}/json.htm?type=command&param=switchlight&idx={plug_idx}&switchcmd=On"
                        if passcode != "":
                                str_url = f"{str_url}&passcode={passcode}"
                        if ignoreSSL:
                            if username and password:
                                web_response = requests.get(str_url, auth=(username, password), timeout=10, verify=False)
                            else:
                                web_response = requests.get(str_url, timeout=10, verify=False)
                        else:
                            if username and password:
                                web_response = requests.get(str_url, auth=(username, password), timeout=10)
                            else:
                                web_response = requests.get(str_url, timeout=10)
                        response = web_response.json()
                        chk = response["status"]
                except Exception:
                        self._domoticz_logger.error(f"Invalid ip or unknown error connecting to {plug_ip}.", exc_info=True)
                        response = f"Unknown error turning on {plug_ip} index {plug_idx}."
                        chk = "UNKNOWN"

                self._domoticz_logger.debug(f"Response: {response}")
                if chk == "OK":
                        if plug["autoConnect"] and self._printer.is_closed_or_error():
                                c = threading.Timer(int(plug["autoConnectDelay"]), self._printer.connect)
                                c.start()
                        if plug["sysCmdOn"]:
                                t = threading.Timer(
                                        int(plug["sysCmdOnDelay"]), os.system, args=[plug["sysRunCmdOn"]]
                                )
                                t.start()
                        self._plugin_manager.send_plugin_message(
                                self._identifier, {"currentState": "on", "ip": plug_ip, "idx": plug_idx}
                        )
                else:
                        self._domoticz_logger.debug(response)
                        self._plugin_manager.send_plugin_message(
                                self._identifier,
                                {"currentState": "unknown", "ip": plug_ip, "idx": plug_idx},
                        )

        def turn_off(self, plug_ip, plug_idx, ignoreSSL, username="", password="", passcode=""):
                self._domoticz_logger.debug(f"Turning off {plug_ip} index {plug_idx}.")
                plug = self.plug_search(self._settings.get(["arrSmartplugs"]), "ip", plug_ip, "idx", plug_idx)
                try:
                        if plug["sysCmdOff"]:
                                self._domoticz_logger.debug(f'Running system command: {plug["sysRunCmdOff"]} in {plug["sysCmdOffDelay"]}')
                                t = threading.Timer(int(plug["sysCmdOffDelay"]), os.system, args=[plug["sysRunCmdOff"]])
                                t.start()

                        if plug["autoDisconnect"]:
                                self._domoticz_logger.debug("Disconnecting from printer")
                                self._printer.disconnect()
                                time.sleep(int(plug["autoDisconnectDelay"]))
                        str_url = f"{plug_ip}/json.htm?type=command&param=switchlight&idx={plug_idx}&switchcmd=Off"
                        if passcode != "":
                                str_url = f"{str_url}&passcode={passcode}"
                        if ignoreSSL:
                            if username and password:
                                web_response = requests.get(str_url, auth=(username, password), timeout=10, verify=False)
                            else:
                                web_response = requests.get(str_url, timeout=10, verify=False)
                        else:
                            if username and password:
                                web_response = requests.get(str_url, auth=(username, password), timeout=10)
                            else:
                                web_response = requests.get(str_url, timeout=10)
                        response = web_response.json()
                        chk = response["status"]
                except Exception:
                        self._domoticz_logger.error(f"Invalid ip or unknown error connecting to {plug_ip}.", exc_info=True)
                        response = f"Unknown error turning off {plug_ip} index {plug_idx}."
                        chk = "UNKNOWN"

                self._domoticz_logger.debug("Response: %s" % response)
                if chk == "OK":
                        self._plugin_manager.send_plugin_message(
                                self._identifier, {"currentState": "off", "ip": plug_ip, "idx": plug_idx}
                        )
                else:
                        self._domoticz_logger.debug(response)
                        self._plugin_manager.send_plugin_message(
                                self._identifier,
                                {"currentState": "unknown", "ip": plug_ip, "idx": plug_idx},
                        )

        def gcode_turn_off(self, plug):
                if plug["warnPrinting"] and self._printer.is_printing():
                        self._domoticz_logger.debug(f"Not powering off {plug['label']} since new print has started.")
                else:
                        self.turn_off(plug["ip"], plug["idx"], username=plug["username"], password=plug["password"],
                                                  passcode=plug["passcode"])

        def check_status(self, plug_ip, plug_idx, ignoreSSL, username="", password=""):
                self._domoticz_logger.debug(f"Checking status of {plug_ip} index {plug_idx}.")
                if plug_ip != "":
                        try:
                            str_url = f"{plug_ip}/json.htm?type=command&param=getdevices&rid={plug_idx}"
                            if ignoreSSL:
                                if username != "":
                                    web_response = requests.get(str_url, auth=(username, password), timeout=10, verify=False)
                                else:
                                    web_response = requests.get(str_url, timeout=10, verify=False)
                            else:
                                if username != "":
                                    web_response = requests.get(str_url, auth=(username, password), timeout=10)
                                else:
                                    web_response = requests.get(str_url, timeout=10)

                            self._domoticz_logger.debug(f"{plug_ip} index {plug_idx} response: {web_response}")
                            response = web_response.json()
                            chk = response["result"][0]["Status"]
                        except Exception:
                            self._domoticz_logger.error(f"Invalid ip or unknown error connecting to {plug_ip}.", exc_info=True)
                            response = f"unknown error with {plug_ip}."
                            chk = "UNKNOWN"

                        self._domoticz_logger.debug(f"{plug_ip} index {plug_idx} is {chk}")
                        if chk == "On":
                            self._plugin_manager.send_plugin_message(
                                self._identifier, {"currentState": "on", "ip": plug_ip, "idx": plug_idx}
                            )
                        elif chk == "Off":
                            self._plugin_manager.send_plugin_message(
                                self._identifier,
                                {"currentState": "off", "ip": plug_ip, "idx": plug_idx},
                            )
                        else:
                            self._domoticz_logger.debug(response)
                            self._plugin_manager.send_plugin_message(
                                self._identifier,
                                {"currentState": "unknown", "ip": plug_ip, "idx": plug_idx},
                            )

        def get_api_commands(self):
                return {
                        "turnOn": ["ip", "idx"],
                        "turnOff": ["ip", "idx"],
                        "checkStatus": ["ip", "idx"],
                        "connectPrinter": [],
                        "disconnectPrinter": [],
                }

        def on_api_command(self, command, data):
                self._domoticz_logger.debug(data)
                if not Permissions.PLUGIN_DOMOTICZ_CONTROL.can():
                        from flask import make_response
                        return make_response("Insufficient rights", 403)

                # Find the plug config to get ignoreSSL
                plug = self.plug_search(
                        self._settings.get(["arrSmartplugs"]),
                        "ip", data.get("ip", ""),
                        "idx", data.get("idx", "")
                )
                ignoreSSL = plug["ignoreSSL"] if plug and "ignoreSSL" in plug else False

                if command == "turnOn":
                        if "username" in data and data["username"] != "":
                                self._domoticz_logger.debug(
                                        "Using authentication for %s." % "{ip}".format(**data)
                                )
                                self.turn_on(
                                        "{ip}".format(**data),
                                        "{idx}".format(**data),
                                        ignoreSSL,
                                        username="{username}".format(**data),
                                        password="{password}".format(**data),
                                        passcode="{passcode}".format(**data)
                                )
                        else:
                                self.turn_on(
                                        "{ip}".format(**data),
                                        "{idx}".format(**data),
                                        ignoreSSL,
                                        passcode="{passcode}".format(**data)
                                )
                elif command == "turnOff":
                        if "username" in data and data["username"] != "":
                                self._domoticz_logger.debug(
                                        "Using authentication for %s." % "{ip}".format(**data)
                                )
                                self.turn_off(
                                        "{ip}".format(**data),
                                        "{idx}".format(**data),
                                        ignoreSSL,
                                        username="{username}".format(**data),
                                        password="{password}".format(**data),
                                        passcode="{passcode}".format(**data)
                                )
                        else:
                                self.turn_off(
                                        "{ip}".format(**data),
                                        "{idx}".format(**data),
                                        ignoreSSL,
                                        passcode="{passcode}".format(**data)
                                )
                elif command == "checkStatus":
                        if "username" in data and data["username"] != "":
                                self._domoticz_logger.debug(
                                        "Using authentication for %s." % "{ip}".format(**data)
                                )
                                self.check_status(
                                        "{ip}".format(**data),
                                        "{idx}".format(**data),
                                        ignoreSSL,
                                        username="{username}".format(**data),
                                        password="{password}".format(**data),
                                )
                        else:
                                self.check_status(
                                        "{ip}".format(**data),
                                        "{idx}".format(**data),
                                        ignoreSSL
                                )
                elif command == "connectPrinter":
                        self._domoticz_logger.debug("Connecting printer.")
                        self._printer.connect()
                elif command == "disconnectPrinter":
                        self._domoticz_logger.debug("Disconnecting printer.")
                        self._printer.disconnect()

        ##~~ Gcode processing hook

        def process_gcode(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
                if gcode:
                        if cmd.startswith("M8") and cmd.count(" ") >= 2:
                                plugip = cmd.split()[1]
                                plugidx = cmd.split()[2]
                                for plug in self._settings.get(["arrSmartplugs"]):
                                        if (
                                                        plug["ip"].upper() == plugip.upper()
                                                        and plug["idx"] == plugidx
                                                        and plug["gcodeEnabled"]
                                        ):
                                                if cmd.startswith("M80"):
                                                        t = threading.Timer(
                                                                int(plug["gcodeOnDelay"]),
                                                                self.turn_on,
                                                                [plug["ip"], plug["idx"]],
                                                                {
                                                                        "username": plug["username"],
                                                                        "password": plug["password"],
                                                                        "passcode": plug["passcode"]
                                                                },
                                                        )
                                                        t.start()
                                                        self._domoticz_logger.debug(
                                                                "Received M80 command, attempting power on of %s index %s."
                                                                % (plugip, plugidx)
                                                        )
                                                        return
                                                elif cmd.startswith("M81"):
                                                        t = threading.Timer(
                                                                int(plug["gcodeOffDelay"]), self.gcode_turn_off, [plug]
                                                        )
                                                        t.start()
                                                        self._domoticz_logger.debug(
                                                                "Received M81 command, attempting power off of %s index %s."
                                                                % (plugip, plugidx)
                                                        )
                                                        return
                                                else:
                                                        return
                elif cmd.startswith("@DOMOTICZ") and cmd.count(" ") == 1:
                        plugidx = cmd.split()[1]
                        for plug in self._settings.get(["arrSmartplugs"]):
                                if plug["idx"] == plugidx and plug["gcodeEnabled"]:
                                        if cmd.startswith("@DOMOTICZON"):
                                                t = threading.Timer(
                                                        int(plug["gcodeOnDelay"]),
                                                        self.turn_on,
                                                        [plug["ip"], plug["idx"]],
                                                        {"username": plug["username"], "password": plug["password"], "passcode": plug["passcode"]},
                                                )
                                                t.start()
                                                self._domoticz_logger.debug(
                                                        "Received @DOMOTICZON command, attempting power on of %s index %s."
                                                        % (plug["ip"], plugidx)
                                                )
                                                return
                                        elif cmd.startswith("@DOMOTICZOFF"):
                                                t = threading.Timer(
                                                        int(plug["gcodeOffDelay"]), self.gcode_turn_off, [plug]
                                                )
                                                t.start()
                                                self._domoticz_logger.debug(
                                                        "Received @DOMOTICZOFF command, attempting power off of %s index %s."
                                                        % (plug["ip"], plugidx)
                                                )
                                                return
                                        else:
                                                return
                        return

        ##~~ Utility functions

        def lookup(self, dic, key, *keys):
                if keys:
                        return self.lookup(dic.get(key, {}), *keys)
                return dic.get(key)

        def plug_search(self, search_list, key1, value1, key2, value2):
                for item in search_list:
                        if item[key1] == value1 and item[key2] == value2:
                                return item

        ##~~ Access Permissions Hook

        def get_additional_permissions(self, *args, **kwargs):
                return [
                        dict(key="CONTROL",
                                 name="Control Devices",
                                 description=gettext("Allows control of configured devices."),
                                 roles=["admin"],
                                 dangerous=True,
                                 default_groups=[ADMIN_GROUP])
                ]

        ##~~ Softwareupdate hook

        def get_update_information(self):
                return {
                        "domoticz": {
                                "displayName": "OctoPrint-Domoticz",
                                "displayVersion": self._plugin_version,
                                # version check: github repository
                                "type": "github_release",
                                "user": "jneilliii",
                                "repo": "OctoPrint-Domoticz",
                                "current": self._plugin_version,
                                "stable_branch": {
                                        "name": "Stable", "branch": "master", "comittish": ["master"]
                                },
                                "prerelease_branches": [
                                        {
                                                "name": "Release Candidate",
                                                "branch": "rc",
                                                "comittish": ["rc", "master"],
                                        }
                                ],
                                # update method: pip
                                "pip": "https://github.com/jneilliii/OctoPrint-Domoticz/archive/{target_version}.zip",
                        }
                }


__plugin_name__ = "Domoticz"
__plugin_pythoncompat__ = ">=3.7,<4"


def __plugin_load__():
        global __plugin_implementation__
        __plugin_implementation__ = domoticzPlugin()

        global __plugin_hooks__
        __plugin_hooks__ = {
                "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.process_gcode,
                "octoprint.access.permissions": __plugin_implementation__.get_additional_permissions,
                "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        }
