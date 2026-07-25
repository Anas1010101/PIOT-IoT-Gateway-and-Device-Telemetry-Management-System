import logging

from importlib import import_module
from apscheduler.schedulers.background import BackgroundScheduler

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.cda.sim.HumiditySensorSimTask import HumiditySensorSimTask
from programmingtheiot.cda.sim.PressureSensorSimTask import PressureSensorSimTask
from programmingtheiot.cda.sim.TemperatureSensorSimTask import TemperatureSensorSimTask
from programmingtheiot.cda.sim.SensorDataGenerator import SensorDataGenerator


class SensorAdapterManager:

	def __init__(self):
		self.configUtil = ConfigUtil()

		self.pollRate = self.configUtil.getInteger(
			section = ConfigConst.CONSTRAINED_DEVICE,
			key = ConfigConst.POLL_CYCLES_KEY,
			defaultVal = ConfigConst.DEFAULT_POLL_CYCLES
		)

		self.useEmulator = self.configUtil.getBoolean(
			section = ConfigConst.CONSTRAINED_DEVICE,
			key = ConfigConst.ENABLE_EMULATOR_KEY
		)

		self.dataMsgListener = None
		self.scheduler = BackgroundScheduler()

		self.humidityAdapter = None
		self.pressureAdapter = None
		self.tempAdapter = None

		logging.info("SensorAdapterManager useEmulator flag: " + str(self.useEmulator))

		self._initEnvironmentalSensorTasks()

	def _initEnvironmentalSensorTasks(self):
		humidityFloor = self.configUtil.getFloat(
			section = ConfigConst.CONSTRAINED_DEVICE,
			key = ConfigConst.HUMIDITY_SIM_FLOOR_KEY,
			defaultVal = SensorDataGenerator.LOW_NORMAL_ENV_HUMIDITY
		)

		humidityCeiling = self.configUtil.getFloat(
			section = ConfigConst.CONSTRAINED_DEVICE,
			key = ConfigConst.HUMIDITY_SIM_CEILING_KEY,
			defaultVal = SensorDataGenerator.HI_NORMAL_ENV_HUMIDITY
		)

		pressureFloor = self.configUtil.getFloat(
			section = ConfigConst.CONSTRAINED_DEVICE,
			key = ConfigConst.PRESSURE_SIM_FLOOR_KEY,
			defaultVal = SensorDataGenerator.LOW_NORMAL_ENV_PRESSURE
		)

		pressureCeiling = self.configUtil.getFloat(
			section = ConfigConst.CONSTRAINED_DEVICE,
			key = ConfigConst.PRESSURE_SIM_CEILING_KEY,
			defaultVal = SensorDataGenerator.HI_NORMAL_ENV_PRESSURE
		)

		tempFloor = self.configUtil.getFloat(
			section = ConfigConst.CONSTRAINED_DEVICE,
			key = ConfigConst.TEMP_SIM_FLOOR_KEY,
			defaultVal = SensorDataGenerator.LOW_NORMAL_INDOOR_TEMP
		)

		tempCeiling = self.configUtil.getFloat(
			section = ConfigConst.CONSTRAINED_DEVICE,
			key = ConfigConst.TEMP_SIM_CEILING_KEY,
			defaultVal = SensorDataGenerator.HI_NORMAL_INDOOR_TEMP
		)

		if not self.useEmulator:
			logging.info("Loading simulated sensor tasks...")

			self.dataGenerator = SensorDataGenerator()

			humidityData = self.dataGenerator.generateDailyEnvironmentHumidityDataSet(
				minValue = humidityFloor,
				maxValue = humidityCeiling,
				useSeconds = False
			)

			pressureData = self.dataGenerator.generateDailyEnvironmentPressureDataSet(
				minValue = pressureFloor,
				maxValue = pressureCeiling,
				useSeconds = False
			)

			tempData = self.dataGenerator.generateDailyIndoorTemperatureDataSet(
				minValue = tempFloor,
				maxValue = tempCeiling,
				useSeconds = False
			)

			self.humidityAdapter = HumiditySensorSimTask(dataSet = humidityData)
			self.pressureAdapter = PressureSensorSimTask(dataSet = pressureData)
			self.tempAdapter = TemperatureSensorSimTask(dataSet = tempData)

		else:
			logging.info("Loading SenseHAT emulator sensor tasks...")

			heModule = import_module(
				"programmingtheiot.cda.emulated.HumiditySensorEmulatorTask"
			)
			heClazz = getattr(heModule, "HumiditySensorEmulatorTask")
			self.humidityAdapter = heClazz()

			peModule = import_module(
				"programmingtheiot.cda.emulated.PressureSensorEmulatorTask"
			)
			peClazz = getattr(peModule, "PressureSensorEmulatorTask")
			self.pressureAdapter = peClazz()

			teModule = import_module(
				"programmingtheiot.cda.emulated.TemperatureSensorEmulatorTask"
			)
			teClazz = getattr(teModule, "TemperatureSensorEmulatorTask")
			self.tempAdapter = teClazz()

	def setDataMessageListener(self, listener):
		self.dataMsgListener = listener

	def handleTelemetry(self):
		humidityData = self.humidityAdapter.generateTelemetry()
		pressureData = self.pressureAdapter.generateTelemetry()
		tempData = self.tempAdapter.generateTelemetry()

		logging.debug("Generated humidity data: " + str(humidityData.getValue()))
		logging.debug("Generated pressure data: " + str(pressureData.getValue()))
		logging.debug("Generated temp data: " + str(tempData.getValue()))

		if self.dataMsgListener:
			self.dataMsgListener.handleSensorMessage(humidityData)
			self.dataMsgListener.handleSensorMessage(pressureData)
			self.dataMsgListener.handleSensorMessage(tempData)

	def startManager(self):
		logging.info("Started SensorAdapterManager.")

		self.scheduler.add_job(
			self.handleTelemetry,
			"interval",
			seconds = self.pollRate
		)

		self.scheduler.start()

	def stopManager(self):
		logging.info("Stopped SensorAdapterManager.")

		try:
			self.scheduler.shutdown()
		except:
			pass