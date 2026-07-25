import logging

from importlib import import_module

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.cda.sim.HumidifierActuatorSimTask import HumidifierActuatorSimTask
from programmingtheiot.cda.sim.HvacActuatorSimTask import HvacActuatorSimTask


class ActuatorAdapterManager:

	def __init__(self):
		self.configUtil = ConfigUtil()

		self.useEmulator = self.configUtil.getBoolean(
			section = ConfigConst.CONSTRAINED_DEVICE,
			key = ConfigConst.ENABLE_EMULATOR_KEY
		)

		self.dataMsgListener = None

		self.humidifierActuator = None
		self.hvacActuator = None
		self.ledDisplayActuator = None

		logging.info("ActuatorAdapterManager useEmulator flag: " + str(self.useEmulator))

		self._initEnvironmentalActuationTasks()

	def _initEnvironmentalActuationTasks(self):
		if not self.useEmulator:
			logging.info("Loading simulated actuator tasks...")

			self.humidifierActuator = HumidifierActuatorSimTask()
			self.hvacActuator = HvacActuatorSimTask()

		else:
			logging.info("Loading SenseHAT emulator actuator tasks...")

			hueModule = import_module(
				"programmingtheiot.cda.emulated.HumidifierEmulatorTask"
			)
			hueClazz = getattr(hueModule, "HumidifierEmulatorTask")
			self.humidifierActuator = hueClazz()

			hveModule = import_module(
				"programmingtheiot.cda.emulated.HvacEmulatorTask"
			)
			hveClazz = getattr(hveModule, "HvacEmulatorTask")
			self.hvacActuator = hveClazz()

			ledModule = import_module(
				"programmingtheiot.cda.emulated.LedDisplayEmulatorTask"
			)
			ledClazz = getattr(ledModule, "LedDisplayEmulatorTask")
			self.ledDisplayActuator = ledClazz()

	def setDataMessageListener(self, listener):
		self.dataMsgListener = listener

	def sendActuatorCommand(self, actuatorData):
		logging.info(
			"Actuator command received for location ID "
			+ str(actuatorData.getLocationID())
			+ ". Processing..."
		)

		typeID = actuatorData.getTypeID()

		if typeID == ConfigConst.HUMIDIFIER_ACTUATOR_TYPE:
			return self.humidifierActuator.updateActuator(actuatorData)

		elif typeID == ConfigConst.HVAC_ACTUATOR_TYPE:
			return self.hvacActuator.updateActuator(actuatorData)

		elif typeID == ConfigConst.LED_DISPLAY_ACTUATOR_TYPE:
			return self.ledDisplayActuator.updateActuator(actuatorData)

		else:
			logging.warning("No actuator adapter found for typeID: " + str(typeID))
			return None