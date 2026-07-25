import logging

import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.data.ActuatorData import ActuatorData


class BaseActuatorSimTask:
    def __init__(
        self,
        name: str = ConfigConst.NOT_SET,
        typeID: int = ConfigConst.DEFAULT_ACTUATOR_TYPE,
        simpleName: str = "Actuator"
    ):
        self.latestActuatorResponse = ActuatorData(typeID=typeID, name=name)
        self.latestActuatorResponse.setAsResponse()

        self.name = name
        self.typeID = typeID
        self.simpleName = simpleName

        self.lastKnownCommand = ConfigConst.DEFAULT_COMMAND
        self.lastKnownValue = ConfigConst.DEFAULT_VAL
        self.lastKnownState = ""

    # =========================
    # ACTIVATE (ON)
    # =========================
    def _activateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
        msg = "\n*******"
        msg += "\n* O N *"
        msg += "\n*******"
        msg += "\n" + self.name + " VALUE -> " + str(val) + "\n======="

        logging.info("Simulating %s actuator ON: %s", self.name, msg)

        return 0

    # =========================
    # DEACTIVATE (OFF)
    # =========================
    def _deactivateActuator(self, val: float = ConfigConst.DEFAULT_VAL, stateData: str = None) -> int:
        msg = "\n*******"
        msg += "\n* OFF *"
        msg += "\n*******"

        logging.info("Simulating %s actuator OFF: %s", self.name, msg)

        return 0

    # =========================
    # MAIN LOGIC
    # =========================
    def updateActuator(self, data: ActuatorData) -> ActuatorData:
        if data and self.typeID == data.getTypeID():

            statusCode = ConfigConst.DEFAULT_STATUS

            curCommand = data.getCommand()
            curVal = data.getValue()
            curState = data.getStateData()

            # ignore duplicates
            if (
                curCommand == self.lastKnownCommand
                and curVal == self.lastKnownValue
                and curState == self.lastKnownState
            ):
                logging.debug(
                    "Duplicate actuator command ignored: %s %s",
                    str(curCommand),
                    str(curVal)
                )
                return None

            logging.debug(
                "Applying actuator command: %s %s",
                str(curCommand),
                str(curVal)
            )

            # ON
            if curCommand == ConfigConst.COMMAND_ON:
                logging.info("Activating actuator...")
                statusCode = self._activateActuator(val=curVal, stateData=curState)

            # OFF
            elif curCommand == ConfigConst.COMMAND_OFF:
                logging.info("Deactivating actuator...")
                statusCode = self._deactivateActuator(val=curVal, stateData=curState)

            # UNKNOWN
            else:
                logging.warning("Unknown actuator command: %s", str(curCommand))
                statusCode = -1

            # update last known state
            self.lastKnownCommand = curCommand
            self.lastKnownValue = curVal
            self.lastKnownState = curState

            # build response
            actuatorResponse = ActuatorData()
            actuatorResponse.updateData(data)
            actuatorResponse.setStatusCode(statusCode)
            actuatorResponse.setAsResponse()

            self.latestActuatorResponse.updateData(actuatorResponse)

            return actuatorResponse

        return None