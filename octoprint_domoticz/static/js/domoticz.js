/*
 * View model for OctoPrint-Domoticz
 *
 * Author: jneilliii
 * License: AGPLv3
 */
$(function() {
	function domoticzViewModel(parameters) {
		var self = this;

		self.settings = parameters[0];
		self.loginState = parameters[1];

		self.arrSmartplugs = ko.observableArray();
		self.isPrinting = ko.observable(false);
		self.gcodeOnString = function(data){return 'M80 '+data.ip()+' '+data.idx();};
		self.gcodeOffString = function(data){return 'M81 '+data.ip()+' '+data.idx();};
		self.selectedPlug = ko.observable();
		self.processing = ko.observableArray([]);

		self.onBeforeBinding = function() {
			self.arrSmartplugs(self.settings.settings.plugins.domoticz.arrSmartplugs());
		}

		self.onAfterBinding = function() {
			self.checkStatuses();
		}

		self.onEventSettingsUpdated = function(payload) {
			self.settings.requestData();
			self.arrSmartplugs(self.settings.settings.plugins.domoticz.arrSmartplugs());
		}

		self.onEventPrinterStateChanged = function(payload) {
			if (payload.state_id == "PRINTING" || payload.state_id == "PAUSED"){
				self.isPrinting(true);
			} else {
				self.isPrinting(false);
			}
		}

		self.addPlug = function() {
			self.selectedPlug({'ip':ko.observable(''),
							   'idx':ko.observable('1'),
							   'displayWarning':ko.observable(true),
							   'warnPrinting':ko.observable(false),
							   'gcodeEnabled':ko.observable(false),
							   'gcodeOnDelay':ko.observable(0),
							   'gcodeOffDelay':ko.observable(0),
							   'autoConnect':ko.observable(true),
							   'autoConnectDelay':ko.observable(10.0),
							   'autoDisconnect':ko.observable(true),
							   'autoDisconnectDelay':ko.observable(0),
							   'sysCmdOn':ko.observable(false),
							   'sysRunCmdOn':ko.observable(''),
							   'sysCmdOnDelay':ko.observable(0),
							   'sysCmdOff':ko.observable(false),
							   'sysRunCmdOff':ko.observable(''),
							   'sysCmdOffDelay':ko.observable(0),
							   'currentState':ko.observable('unknown'),
							   'btnColor':ko.observable('#808080'),
							   'username':ko.observable(''),
							   'password':ko.observable(''),
							   'icon':ko.observable('icon-bolt'),
							   'label':ko.observable('')});
			self.settings.settings.plugins.domoticz.arrSmartplugs.push(self.selectedPlug());
			$("#DomoticzEditor").modal("show");
		}

		self.editPlug = function(data) {
			self.selectedPlug(data);
			$("#DomoticzEditor").modal("show");
		}

		self.removePlug = function(row) {
			self.settings.settings.plugins.domoticz.arrSmartplugs.remove(row);
		}

		self.cancelClick = function(data) {
			self.processing.remove(data.ip());
		}

		self.onDataUpdaterPluginMessage = function(plugin, data) {
			if (plugin != "domoticz") {
				return;
			}

			plug = ko.utils.arrayFirst(self.settings.settings.plugins.domoticz.arrSmartplugs(),function(item){
				return ((item.ip().toUpperCase() == data.ip.toUpperCase()) && (item.idx() == data.idx));
				}) || {'ip':data.ip,'idx':data.idx,'currentState':'unknown','btnColor':'#808080','gcodeEnabled':false};

			if(self.settings.settings.plugins.domoticz.debug_logging()){
				console.log(self.settings.settings.plugins.domoticz.arrSmartplugs());
				console.log('msg received:'+JSON.stringify(data));
				console.log('plug data:'+ko.toJSON(plug));
			}

			if (plug.currentState != data.currentState) {
				plug.currentState(data.currentState)
				switch(data.currentState) {
					case "on":
						break;
					case "off":
						break;
					default:
						new PNotify({
							title: 'Domoticz Error',
							text: 'Status ' + plug.currentState() + ' for ' + plug.ip() + '. Double check IP Address\\Hostname in Domoticz Settings.',
							type: 'error',
							hide: true
							});
				}
				self.settings.saveData();
			}
			self.processing.remove(data.ip);
		};

		self.toggleRelay = function(data) {
			self.processing.push(data.ip());
			switch(data.currentState()){
				case "on":
					self.turnOff(data);
					break;
				case "off":
					self.turnOn(data);
					break;
				default:
					self.checkStatus(data);
			}
		}

		self.turnOn = function(data) {
			self.sendTurnOn(data);
		}

		self.sendTurnOn = function(data) {
			$.ajax({
				url: API_BASEURL + "plugin/domoticz",
				type: "POST",
				dataType: "json",
				data: JSON.stringify({
					command: "turnOn",
					ip: data.ip(),
					idx: data.idx(),
					username: data.username(),
					password: data.password()
				}),
				contentType: "application/json; charset=UTF-8"
			});
		};

		self.turnOff = function(data) {
			if((data.displayWarning() || (self.isPrinting() && data.warnPrinting())) && !$("#DomoticzWarning").is(':visible')){
				self.selectedPlug(data);
				$("#DomoticzWarning").modal("show");
			} else {
				$("#DomoticzWarning").modal("hide");
				self.sendTurnOff(data);
			}
		}; 

		self.sendTurnOff = function(data) {
			$.ajax({
			url: API_BASEURL + "plugin/domoticz",
			type: "POST",
			dataType: "json",
			data: JSON.stringify({
				command: "turnOff",
					ip: data.ip(),
					idx: data.idx(),
					username: data.username(),
					password: data.password()
			}),
			contentType: "application/json; charset=UTF-8"
			});
		}

		self.checkStatus = function(data) {
			$.ajax({
				url: API_BASEURL + "plugin/domoticz",
				type: "POST",
				dataType: "json",
				data: JSON.stringify({
					command: "checkStatus",
					ip: data.ip(),
					idx: data.idx(),
					username: data.username(),
					password: data.password()
				}),
				contentType: "application/json; charset=UTF-8"
			}).done(function(){
				self.settings.saveData();
				});
		}; 

		self.disconnectPrinter = function() {
			$.ajax({
				url: API_BASEURL + "plugin/domoticz",
				type: "POST",
				dataType: "json",
				data: JSON.stringify({
					command: "disconnectPrinter"
				}),
				contentType: "application/json; charset=UTF-8"
			});
		}

		self.connectPrinter = function() {
			$.ajax({
				url: API_BASEURL + "plugin/domoticz",
				type: "POST",
				dataType: "json",
				data: JSON.stringify({
					command: "connectPrinter"
				}),
				contentType: "application/json; charset=UTF-8"
			});
		}

		self.sysCommand = function(sysCmd) {
			$.ajax({
				url: API_BASEURL + "plugin/domoticz",
				type: "POST",
				dataType: "json",
				data: JSON.stringify({
					command: "sysCommand",
					cmd: sysCmd
				}),
				contentType: "application/json; charset=UTF-8"
			});
		}

		self.checkStatuses = function() {
			ko.utils.arrayForEach(self.settings.settings.plugins.domoticz.arrSmartplugs(),function(item){
				if(item.ip() !== "") {
					if(self.settings.settings.plugins.domoticz.debug_logging()){
						console.log("checking " + item.ip() + " index " + item.idx());
					}
					self.checkStatus(item);
				}
			});
		};
	}

	// view model class, parameters for constructor, container to bind to
	OCTOPRINT_VIEWMODELS.push([
		domoticzViewModel,

		// e.g. loginStateViewModel, settingsViewModel, ...
		["settingsViewModel","loginStateViewModel"],

		// "#navbar_plugin_domoticz","#settings_plugin_domoticz"
		["#navbar_plugin_domoticz","#settings_plugin_domoticz"]
	]);
});
