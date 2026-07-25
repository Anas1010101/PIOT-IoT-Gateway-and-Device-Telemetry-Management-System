#####
#
# This class is part of the Programming the Internet of Things
# project, and is available via the MIT License, which can be
# found in the LICENSE file at the top level of this repository.
#
# You may find it more helpful to your design to adjust the
# functionality, constants and interfaces (if there are any)
# provided within in order to meet the needs of your specific
# Programming the Internet of Things project.
#

import argparse
import logging
import traceback
from time import sleep

import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.cda.app.DeviceDataManager import DeviceDataManager

# Configuration globale du logger au niveau DEBUG
logging.basicConfig(format='%(asctime)s:%(name)s:%(levelname)s:%(message)s', level=logging.DEBUG)

class ConstrainedDeviceApp:
    """
    Definition of the ConstrainedDeviceApp class.
    """

    def __init__(self):
        """
        Initialization of class.
        """
        logging.info("Initializing CDA...")
        self.configUtil = ConfigUtil()
        self.dataMgr = DeviceDataManager()
        # Initialisation de la variable d'état de l'application
        self.isStarted = False

    def isAppStarted(self) -> bool:
        """
        Returns the execution state of the application.
        """
        return self.isStarted

    def startApp(self):
        """
        Start the CDA. Calls startManager() on the device data manager instance.
        """
        logging.info("Starting CDA...")
        self.dataMgr.startManager()
        self.isStarted = True  # Changement d'état
        logging.info("CDA started.")

    def stopApp(self, code: int):
        """
        Stop the CDA. Calls stopManager() on the device data manager instance.
        """
        logging.info("CDA stopping...")
        self.dataMgr.stopManager()
        self.isStarted = False  # Changement d'état
        logging.info("CDA stopped with exit code %s.", str(code))


def main():
    cda = ConstrainedDeviceApp()
    cda.startApp()

    configUtil = ConfigUtil()
    runForever = configUtil.getBoolean(ConfigConst.CONSTRAINED_DEVICE, ConfigConst.RUN_FOREVER_KEY)

    if runForever:
        while True:
            sleep(5)
    else:
        # Rendre les 65 secondes configurables dynamiquement
        testRunTime = configUtil.getInteger(
            section=ConfigConst.CONSTRAINED_DEVICE,
            key="testRunTime",
            defaultVal=65
        )
        logging.info("CDA running in test mode. Will automatically shutdown in %s seconds.", str(testRunTime))
        sleep(testRunTime)
        cda.stopApp(0)


if __name__ == '__main__':
    main()