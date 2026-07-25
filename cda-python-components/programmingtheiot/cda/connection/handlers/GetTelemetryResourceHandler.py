import logging

from coapthon import defines
from coapthon.resources.resource import Resource

import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.common.ITelemetryDataListener import ITelemetryDataListener
from programmingtheiot.data.DataUtil import DataUtil
from programmingtheiot.data.SensorData import SensorData


class GetTelemetryResourceHandler(Resource, ITelemetryDataListener):
    def __init__(self, name: str = ConfigConst.SENSOR_MSG, coap_server=None, dataMsgListener: IDataMessageListener = None):
        super(GetTelemetryResourceHandler, self).__init__(
            name, coap_server, visible=True, observable=True, allow_children=True)

        self.pollCycles = ConfigUtil().getInteger(
            section=ConfigConst.CONSTRAINED_DEVICE,
            key=ConfigConst.POLL_CYCLES_KEY,
            defaultVal=ConfigConst.DEFAULT_POLL_CYCLES
        )

        self.dataUtil = DataUtil()
        self.sensorData = SensorData()
        self.dataMsgListener = dataMsgListener

        if self.dataMsgListener:
            self.dataMsgListener.setTelemetryDataListener(self)

        self.payload = "GetSensorData"

    def render_GET_advanced(self, request, response):
        if request:
            response.code = defines.Codes.CONTENT.number
            jsonData = DataUtil().sensorDataToJson(self.sensorData)
            logging.info("Latest SensorData JSON: " + jsonData)
            response.payload = (defines.Content_types["application/json"], jsonData)
            response.max_age = self.pollCycles
            self.changed = False
        return self, response

    def onSensorDataUpdate(self, data: SensorData) -> bool:
        self.sensorData = data