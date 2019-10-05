# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
from octoprint.server import user_permission
import socket
import json
import time
import logging
import os
import re
import requests
import threading
import base64

class domoticzPlugin(octoprint.plugin.SettingsPlugin,
                            octoprint.plugin.AssetPlugin,
                            octoprint.plugin.TemplatePlugin,
							octoprint.plugin.SimpleApiPlugin,
							octoprint.plugin.StartupPlugin):
							
	def __init__(self):
		self._logger = logging.getLogger("octoprint.plugins.domoticz")
		self._domoticz_logger = logging.getLogger("octoprint.plugins.domoticz.debug")
							
	##~~ StartupPlugin mixin
	
	def on_startup(self, host, port):
		# setup customized logger
		from octoprint.logging.handlers import CleaningTimedRotatingFileHandler
		domoticz_logging_handler = CleaningTimedRotatingFileHandler(self._settings.get_plugin_logfile_path(postfix="debug"), when="D", backupCount=3)
		domoticz_logging_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
		domoticz_logging_handler.setLevel(logging.DEBUG)

		self._domoticz_logger.addHandler(domoticz_logging_handler)
		self._domoticz_logger.setLevel(logging.DEBUG if self._settings.get_boolean(["debug_logging"]) else logging.INFO)
		self._domoticz_logger.propagate = False
	
	def on_after_startup(self):
		self._logger.info("Domoticz loaded!")
	
	##~~ SettingsPlugin mixin
	
	def get_settings_defaults(self):
		return dict(
			debug_logging = False,
			arrSmartplugs = [{'ip':'','displayWarning':True,'idx':'1','warnPrinting':False,'gcodeEnabled':False,'gcodeOnDelay':0,'gcodeOffDelay':0,'autoConnect':True,'autoConnectDelay':10.0,'autoDisconnect':True,'autoDisconnectDelay':0,'sysCmdOn':False,'sysRunCmdOn':'','sysCmdOnDelay':0,'sysCmdOff':False,'sysRunCmdOff':'','sysCmdOffDelay':0,'currentState':'unknown','btnColor':'#808080','username':'','password':'','icon':'icon-bolt','label':''}],
		)
		
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
		return 3
		
	def on_settings_migrate(self, target, current=None):
		if current is None or current < self.get_settings_version():
			# Reset plug settings to defaults.
			self._logger.debug("Resetting arrSmartplugs for domoticz settings.")
			self._settings.set(['arrSmartplugs'], self.get_settings_defaults()["arrSmartplugs"])
		
	##~~ AssetPlugin mixin

	def get_assets(self):
		return dict(
			js=["js/domoticz.js"],
			css=["css/domoticz.css"]
		)
		
	##~~ TemplatePlugin mixin
	
	def get_template_configs(self):
		return [
			dict(type="navbar", custom_bindings=True),
			dict(type="settings", custom_bindings=True)
		]
		
	##~~ SimpleApiPlugin mixin
	
	def turn_on(self, plugip, plugidx, username="", password=""):
		if self._settings.get(['singleRelay']):
			plugidx = ''
		self._domoticz_logger.debug("Turning on %s index %s." % (plugip, plugidx))
		try:
			strURL = "http://" + plugip + "/json.htm?type=command&param=switchlight&idx=" + str(plugidx) + "&switchcmd=On"
			if username != "":
				strURL = strURL + "&username=" + base64.b64encode(bytes(username)) + "&password=" + base64.b64encode(bytes(password))
			webresponse = requests.get(strURL)
			response = json.loads(webresponse)
			chk = response["status"]
		except:			
			self._domoticz_logger.error('Invalid ip or unknown error connecting to %s.' % plugip, exc_info=True)
			response = "Unknown error turning on %s index %s." % (plugip, plugidx)
			chk = "UNKNOWN"
			
		self._domoticz_logger.debug("Response: %s" % response)
		if chk == "OK":
			self._plugin_manager.send_plugin_message(self._identifier, dict(currentState="on",ip=plugip,idx=plugidx))
		else:
			self._domoticz_logger.debug(response)
			self._plugin_manager.send_plugin_message(self._identifier, dict(currentState="unknown",ip=plugip,idx=plugidx))
	
	def turn_off(self, plugip, plugidx, username="", password=""):
		self._domoticz_logger.debug("Turning off %s index %s." % (plugip, plugidx))
		try:
			strURL = "http://" + plugip + "/json.htm?type=command&param=switchlight&idx=" + str(plugidx) + "&switchcmd=Off"
			if username != "":
				strURL = strURL + "&username=" + base64.b64encode(bytes(username)) + "&password=" + base64.b64encode(bytes(password))
			webresponse = requests.get(strURL)
			response = json.loads(webresponse)
			chk = response["status"]
		except:
			self._domoticz_logger.error('Invalid ip or unknown error connecting to %s.' % plugip, exc_info=True)
			response = "Unknown error turning off %s index %s." % (plugip, plugidx)
			chk = "UNKNOWN"
			
		self._domoticz_logger.debug("Response: %s" % response)
		if chk == "OK":
			self._plugin_manager.send_plugin_message(self._identifier, dict(currentState="off",ip=plugip,idx=plugidx))
		else:
			self._domoticz_logger.debug(response)
			self._plugin_manager.send_plugin_message(self._identifier, dict(currentState="unknown",ip=plugip,idx=plugidx))
			
	def gcode_turn_off(self, plug):
		if plug["warnPrinting"] and self._printer.is_printing():
			self._domoticz_logger.debug("Not powering off %s since new print has started." % plug["label"])
		else:
			self.turn_off(plug["ip"],plug["idx"],plug["username"],plug["password"])
		
	def check_status(self, plugip, plugidx, username="", password=""):
		self._domoticz_logger.debug("Checking status of %s index %s." % (plugip, plugidx))
		if plugip != "":
			try:
				strURL = "http://" + plugip + "/json.htm?type=devices&rid=" + str(plugidx)
				if username != "":
					strURL = strURL + "&username=" + base64.b64encode(bytes(username)) + "&password=" + base64.b64encode(bytes(password))				
				webresponse = requests.get(strURL)
				self._domoticz_logger.debug("%s index %s response: %s" % (plugip, plugidx, webresponse))
				response = json.loads(webresponse)
				chk = response["result"][0]["Status"]
			except:
				self._domoticz_logger.error('Invalid ip or unknown error connecting to %s.' % plugip, exc_info=True)
				response = "unknown error with %s." % plugip
				chk = "UNKNOWN"
				
			self._domoticz_logger.debug("%s index %s is %s" % (plugip, plugidx, chk))
			if chk == "On":
				self._plugin_manager.send_plugin_message(self._identifier, dict(currentState="on",ip=plugip,idx=plugidx))
			elif chk == "Off":
				self._plugin_manager.send_plugin_message(self._identifier, dict(currentState="off",ip=plugip,idx=plugidx))
			else:
				self._domoticz_logger.debug(response)
				self._plugin_manager.send_plugin_message(self._identifier, dict(currentState="unknown",ip=plugip,idx=plugidx))		
	
	def get_api_commands(self):
		return dict(turnOn=["ip","idx"],turnOff=["ip","idx"],checkStatus=["ip","idx"],connectPrinter=[],disconnectPrinter=[],sysCommand=["cmd"])

	def on_api_command(self, command, data):
		self._domoticz_logger.debug(data)
		if not user_permission.can():
			from flask import make_response
			return make_response("Insufficient rights", 403)
        
		if command == 'turnOn':
			if "username" in data and data["username"] != "":
				self._domoticz_logger.debug("Using authentication for %s." % "{ip}".format(**data))
				self.turn_on("{ip}".format(**data),"{idx}".format(**data),username="{username}".format(**data),password="{password}".format(**data))
			else:
				self.turn_on("{ip}".format(**data),"{idx}".format(**data))
		elif command == 'turnOff':
			if "username" in data and data["username"] != "":
				self._domoticz_logger.debug("Using authentication for %s." % "{ip}".format(**data))
				self.turn_off("{ip}".format(**data),"{idx}".format(**data),username="{username}".format(**data),password="{password}".format(**data))
			else:				
				self.turn_off("{ip}".format(**data),"{idx}".format(**data))
		elif command == 'checkStatus':
			if "username" in data and data["username"] != "":
				self._domoticz_logger.debug("Using authentication for %s." % "{ip}".format(**data))
				self.check_status("{ip}".format(**data),"{idx}".format(**data),username="{username}".format(**data),password="{password}".format(**data))
			else:
				self.check_status("{ip}".format(**data),"{idx}".format(**data))
		elif command == 'connectPrinter':
			self._domoticz_logger.debug("Connecting printer.")
			self._printer.connect()
		elif command == 'disconnectPrinter':
			self._domoticz_logger.debug("Disconnecting printer.")
			self._printer.disconnect()
		elif command == 'sysCommand':
			self._domoticz_logger.debug("Running system command %s." % "{cmd}".format(**data))
			os.system("{cmd}".format(**data))
			
	##~~ Gcode processing hook
	
	def processGCODE(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
		if gcode:
			if cmd.startswith("M8") and cmd.count(" ") >= 2:
				plugip = cmd.split()[1]
				plugidx = cmd.split()[2]					
				for plug in self._settings.get(["arrSmartplugs"]):
					if plug["ip"].upper() == plugip.upper() and plug["idx"] == plugidx and plug["gcodeEnabled"]:
						if cmd.startswith("M80"):
							t = threading.Timer(int(plug["gcodeOnDelay"]),self.turn_on, [plug["ip"],plug["idx"]],{'username': plug["username"],'password': plug["password"]})
							t.start()
							self._domoticz_logger.debug("Received M80 command, attempting power on of %s index %s." % (plugip,plugidx))
							return
						elif cmd.startswith("M81"):
							t = threading.Timer(int(plug["gcodeOffDelay"]),self.gcode_turn_off, [plug])
							t.start()
							self._domoticz_logger.debug("Received M81 command, attempting power off of %s index %s." % (plugip,plugidx))
							return
						else:
							return
		elif cmd.startswith("@DOMOTICZ") and cmd.count(" ") == 1:
			plugidx = cmd.split()[1]
			for plug in self._settings.get(["arrSmartplugs"]):
				if plug["idx"] == plugidx and plug["gcodeEnabled"]:
					if cmd.startswith("@DOMOTICZON"):
						t = threading.Timer(int(plug["gcodeOnDelay"]),self.turn_on, [plug["ip"],plug["idx"]],{'username': plug["username"],'password': plug["password"]})
						t.start()
						self._domoticz_logger.debug("Received @DOMOTICZON command, attempting power on of %s index %s." % (plug["ip"],plugidx))
						return
					elif cmd.startswith("@DOMOTICZOFF"):
						t = threading.Timer(int(plug["gcodeOffDelay"]),self.gcode_turn_off, [plug])
						t.start()
						self._domoticz_logger.debug("Received @DOMOTICZOFF command, attempting power off of %s index %s." % (plug["ip"],plugidx))
						return
					else:
						return
			return


	##~~ Softwareupdate hook

	def get_update_information(self):
		return dict(
			domoticz=dict(
				displayName="OctoPrint-Domoticz",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="jneilliii",
				repo="OctoPrint-Domoticz",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/jneilliii/OctoPrint-Domoticz/archive/{target_version}.zip"
			)
		)

__plugin_name__ = "Domoticz"
__plugin_pythoncompat__ = ">=2.7,<4"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = domoticzPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.processGCODE,
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}

