#####
#
# DeviceDataManager.py
#

import logging

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.cda.connection.CoapClientConnector import CoapClientConnector
from programmingtheiot.cda.connection.CoapServerAdapter import CoapServerAdapter
from programmingtheiot.cda.connection.MqttClientConnector import MqttClientConnector

from programmingtheiot.cda.system.ActuatorAdapterManager import ActuatorAdapterManager
from programmingtheiot.cda.system.SensorAdapterManager import SensorAdapterManager
from programmingtheiot.cda.system.SystemPerformanceManager import SystemPerformanceManager

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum

from programmingtheiot.data.DataUtil import DataUtil
from programmingtheiot.data.ActuatorData import ActuatorData
from programmingtheiot.data.SensorData import SensorData
from programmingtheiot.data.SystemPerformanceData import SystemPerformanceData


class DeviceDataManager(IDataMessageListener):

    def __init__(self, disableAllComms: bool = False):
        self.configUtil = ConfigUtil()

        self.enableSystemPerf = self.configUtil.getBoolean(
            ConfigConst.CONSTRAINED_DEVICE,
            ConfigConst.ENABLE_SYSTEM_PERF_KEY
        )

        self.enableSensing = self.configUtil.getBoolean(
            ConfigConst.CONSTRAINED_DEVICE,
            ConfigConst.ENABLE_SENSING_KEY
        )

        if disableAllComms:
            self.enableMqttClient = False
            self.enableCoapServer = False
            self.enableCoapClient = False
        else:
            self.enableMqttClient = self.configUtil.getBoolean(
                ConfigConst.CONSTRAINED_DEVICE,
                ConfigConst.ENABLE_MQTT_CLIENT_KEY
            )

            self.enableCoapServer = self.configUtil.getBoolean(
                ConfigConst.CONSTRAINED_DEVICE,
                ConfigConst.ENABLE_COAP_SERVER_KEY
            )

            self.enableCoapClient = self.configUtil.getBoolean(
                ConfigConst.CONSTRAINED_DEVICE,
                ConfigConst.ENABLE_COAP_CLIENT_KEY
            )

        self.enableActuation = True

        self.sysPerfMgr = None
        self.sensorAdapterMgr = None
        self.actuatorAdapterMgr = None

        self.mqttClient = None
        self.coapClient = None
        self.coapServer = None

        self.actuatorDataListener: IDataMessageListener = None
        self.actuatorResponseCache = {}

        if self.enableMqttClient:
            self.mqttClient = MqttClientConnector()
            self.mqttClient.setDataMessageListener(self)
            logging.info("MQTT client enabled")

        if self.enableCoapServer:
            self.coapServer = CoapServerAdapter(dataMsgListener=self)
            logging.info("CoAP server enabled")

        if self.enableCoapClient:
            self.coapClient = CoapClientConnector(dataMsgListener=self)
            logging.info("CoAP client enabled")

        if self.enableSystemPerf:
            self.sysPerfMgr = SystemPerformanceManager()
            self.sysPerfMgr.setDataMessageListener(self)
            logging.info("System performance manager enabled")

        if self.enableSensing:
            self.sensorAdapterMgr = SensorAdapterManager()
            self.sensorAdapterMgr.setDataMessageListener(self)
            logging.info("Sensor manager enabled")

        if self.enableActuation:
            self.actuatorAdapterMgr = ActuatorAdapterManager()
            self.actuatorAdapterMgr.setDataMessageListener(self)
            logging.info("Actuator manager enabled")

        self.handleTempChangeOnDevice = self.configUtil.getBoolean(
            ConfigConst.CONSTRAINED_DEVICE,
            ConfigConst.HANDLE_TEMP_CHANGE_ON_DEVICE_KEY
        )

        self.triggerHvacTempFloor = self.configUtil.getFloat(
            ConfigConst.CONSTRAINED_DEVICE,
            ConfigConst.TRIGGER_HVAC_TEMP_FLOOR_KEY,
            18.0
        )

        self.triggerHvacTempCeiling = self.configUtil.getFloat(
            ConfigConst.CONSTRAINED_DEVICE,
            ConfigConst.TRIGGER_HVAC_TEMP_CEILING_KEY,
            20.0
        )

    def setActuatorDataListener(self, name: str, listener: IDataMessageListener):
        if listener is not None:
            self.actuatorDataListener = listener

    def getLatestActuatorDataResponseFromCache(self, name: str = None) -> ActuatorData:
        return self.actuatorResponseCache.get(name) if name else None

    def getLatestSensorDataFromCache(self, name: str = None) -> SensorData:
        pass

    def getLatestSystemPerformanceDataFromCache(self, name: str = None) -> SystemPerformanceData:
        pass

    def handleActuatorCommandMessage(self, data: ActuatorData = None) -> ActuatorData:
        if data:
            logging.info("Processing actuator command message.")
            return self.actuatorAdapterMgr.sendActuatorCommand(data)
        else:
            logging.warning("Received invalid ActuatorData command message. Ignoring.")
            return None

    def handleActuatorCommandResponse(self, data: ActuatorData = None) -> bool:
        if data:
            self.actuatorResponseCache[data.getName()] = data

            msg = DataUtil().actuatorDataToJson(data)

            if self.coapClient:
                self.coapClient.sendPutRequest(
                    ResourceNameEnum.CDA_ACTUATOR_RESPONSE_RESOURCE,
                    payload=msg
                )

            return True

        return False

    def handleIncomingMessage(self, resourceEnum: ResourceNameEnum = None, msg: str = None) -> bool:
        if resourceEnum and msg:
            self._handleIncomingDataAnalysis(msg)
            return True

        return False

    def handleSensorMessage(self, data: SensorData = None) -> bool:
        if data:
            logging.info("Incoming sensor data received.")

            self._handleSensorDataAnalysis(data=data)

            jsonData = DataUtil().sensorDataToJson(data=data)

            self._handleUpstreamTransmission(
                resourceName=ResourceNameEnum.CDA_SENSOR_MSG_RESOURCE,
                msg=jsonData
            )

            return True

        logging.warning("Incoming sensor data is invalid. Ignoring.")
        return False

    def handleSystemPerformanceMessage(self, data: SystemPerformanceData = None) -> bool:
        if data:
            logging.info("Incoming system performance data received.")

            jsonData = DataUtil().systemPerformanceDataToJson(data=data)

            self._handleUpstreamTransmission(
                resourceName=ResourceNameEnum.CDA_SYSTEM_PERF_MSG_RESOURCE,
                msg=jsonData
            )

            return True

        logging.warning("Incoming system performance data is invalid. Ignoring.")
        return False

    def startManager(self):
        logging.info("Starting DeviceDataManager...")

        if self.mqttClient:
            self.mqttClient.connectClient()

        if self.coapServer:
            self.coapServer.startServer()

        if self.sysPerfMgr:
            self.sysPerfMgr.startManager()

        if self.sensorAdapterMgr:
            self.sensorAdapterMgr.startManager()

        logging.info("DeviceDataManager started")

    def stopManager(self):
        logging.info("Stopping DeviceDataManager...")

        if self.mqttClient:
            self.mqttClient.unsubscribeFromTopic(ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE)
            self.mqttClient.disconnectClient()

        if self.coapServer:
            self.coapServer.stopServer()

        if self.sysPerfMgr:
            self.sysPerfMgr.stopManager()

        if self.sensorAdapterMgr:
            self.sensorAdapterMgr.stopManager()

        logging.info("DeviceDataManager stopped")

    def _handleIncomingDataAnalysis(self, msg: str = None):
        try:
            dataUtil = DataUtil()
            actuatorData = dataUtil.jsonToActuatorData(msg)

            if actuatorData and self.actuatorDataListener:
                self.actuatorDataListener.onActuatorDataUpdate(actuatorData)

        except Exception as e:
            logging.error(f"Error analyzing incoming actuator payload: {e}")

    def _handleSensorDataAnalysis(self, resource=None, data: SensorData = None):
        if data and self.handleTempChangeOnDevice and data.getTypeID() == ConfigConst.TEMP_SENSOR_TYPE:
            ad = ActuatorData()
            ad.setName(ConfigConst.HVAC_ACTUATOR_NAME)
            ad.setTypeID(ConfigConst.HVAC_ACTUATOR_TYPE)

            if data.getValue() > self.triggerHvacTempCeiling:
                logging.info("Temperature above ceiling. Triggering HVAC actuator.")
                ad.setCommand(ConfigConst.COMMAND_ON)
                ad.setValue(self.triggerHvacTempCeiling)
                self.handleActuatorCommandMessage(ad)

            elif data.getValue() < self.triggerHvacTempFloor:
                logging.info("Temperature below floor. Triggering HVAC actuator.")
                ad.setCommand(ConfigConst.COMMAND_ON)
                ad.setValue(self.triggerHvacTempFloor)
                self.handleActuatorCommandMessage(ad)

    def _handleUpstreamTransmission(self, resourceName: ResourceNameEnum = None, msg: str = None):
        logging.info("Upstream transmission invoked. Checking comm's integration.")

        if not resourceName or not msg:
            logging.warning("Missing resource name or message. Cannot transmit upstream.")
            return

        if self.mqttClient:
            if self.mqttClient.publishMessage(resource=resourceName, msg=msg):
                logging.debug("Published incoming data to resource using MQTT: %s", str(resourceName))
            else:
                logging.warning("Failed to publish incoming data using MQTT: %s", str(resourceName))

        if self.coapClient:
            if self.coapClient.sendPostRequest(resource=resourceName, payload=msg):
                logging.debug("Posted incoming data to resource using CoAP: %s", str(resourceName))
            else:
                logging.warning("Failed to post incoming data using CoAP: %s", str(resourceName))