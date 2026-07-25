import logging

from pisense import SenseHAT

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.cda.sim.BaseActuatorSimTask import BaseActuatorSimTask


class LedDisplayEmulatorTask(BaseActuatorSimTask):

	def __init__(self):
		super(LedDisplayEmulatorTask, self).__init__(
			name = ConfigConst.LED_ACTUATOR_NAME,
			typeID = ConfigConst.LED_DISPLAY_ACTUATOR_TYPE,
			simpleName = "LED_Display"
		)

		enableEmulation = ConfigUtil().getBoolean(
			ConfigConst.CONSTRAINED_DEVICE,
			ConfigConst.ENABLE_EMULATOR_KEY
		)

		self.sh = SenseHAT(emulate = enableEmulation)

	def _activateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
		if self.sh.screen:
			if stateData:
				self.sh.screen.scroll_text(stateData, size = 8)
			else:
				self.sh.screen.scroll_text("LED Display ON", size = 8)

			return 0
		else:
			logging.warning("No SenseHAT LED screen instance to write.")
			return -1

	def _deactivateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
		if self.sh.screen:
			self.sh.screen.clear()
			return 0
		else:
			logging.warning("No SenseHAT LED screen instance to clear / close.")
			return -1