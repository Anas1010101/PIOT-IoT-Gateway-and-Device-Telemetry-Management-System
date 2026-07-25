import logging

from apscheduler.schedulers.background import BackgroundScheduler

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.cda.system.SystemCpuUtilTask import SystemCpuUtilTask
from programmingtheiot.cda.system.SystemMemUtilTask import SystemMemUtilTask
from programmingtheiot.data.SystemPerformanceData import SystemPerformanceData
from programmingtheiot.common.IDataMessageListener import IDataMessageListener


class SystemPerformanceManager:

	def __init__(self):
		self.configUtil = ConfigUtil()

		self.locationID = self.configUtil.getProperty(
		section = ConfigConst.CONSTRAINED_DEVICE,
		key = ConfigConst.DEVICE_LOCATION_ID_KEY,
		defaultVal = "constraineddevice001"
		)

		self.pollRate = self.configUtil.getInteger(
			section = ConfigConst.CONSTRAINED_DEVICE,
			key = ConfigConst.POLL_CYCLES_KEY,
			defaultVal = ConfigConst.DEFAULT_POLL_CYCLES
		)

		self.cpuUtilPct = 0.0
		self.memUtilPct = 0.0
		self.dataMsgListener = None

		self.cpuUtilTask = SystemCpuUtilTask()
		self.memUtilTask = SystemMemUtilTask()

		self.scheduler = BackgroundScheduler()

	def handleTelemetry(self):
		self.cpuUtilPct = self.cpuUtilTask.getTelemetryValue()
		self.memUtilPct = self.memUtilTask.getTelemetryValue()

		logging.debug(
			"CPU utilization is %s percent, and memory utilization is %s percent.",
			str(self.cpuUtilPct),
			str(self.memUtilPct)
		)

		sysPerfData = SystemPerformanceData()
		sysPerfData.setLocationID(self.locationID)
		sysPerfData.setCpuUtilization(self.cpuUtilPct)
		sysPerfData.setMemoryUtilization(self.memUtilPct)

		if self.dataMsgListener:
			self.dataMsgListener.handleSystemPerformanceMessage(data = sysPerfData)

	def setDataMessageListener(self, listener: IDataMessageListener) -> bool:
		if listener:
			self.dataMsgListener = listener
			return True

		return False

	def startManager(self):
		logging.info("Started SystemPerformanceManager.")

		self.scheduler.add_job(
			self.handleTelemetry,
			"interval",
			seconds = self.pollRate
		)

		self.scheduler.start()

	def stopManager(self):
		logging.info("Stopped SystemPerformanceManager.")

		try:
			self.scheduler.shutdown()
		except:
			pass