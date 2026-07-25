from programmingtheiot.data.SensorData import SensorData

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.cda.sim.BaseSensorSimTask import BaseSensorSimTask

from pisense import SenseHAT


class HumiditySensorEmulatorTask(BaseSensorSimTask):
	def __init__(self):
		super(HumiditySensorEmulatorTask, self).__init__(
			name=ConfigConst.HUMIDITY_SENSOR_NAME,
			typeID=ConfigConst.HUMIDITY_SENSOR_TYPE
		)

		enableEmulation = ConfigUtil().getBoolean(
			ConfigConst.CONSTRAINED_DEVICE,
			ConfigConst.ENABLE_EMULATOR_KEY
		)

		self.sh = SenseHAT(emulate=enableEmulation)

	def generateTelemetry(self) -> SensorData:
		sensorData = SensorData(name=self.getName(), typeID=self.getTypeID())
		sensorVal = self.sh.environ.humidity

		sensorData.setValue(sensorVal)
		self.latestSensorData = sensorData

		return sensorData