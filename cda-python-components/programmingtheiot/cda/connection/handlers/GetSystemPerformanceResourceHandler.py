import logging

from coapthon import defines
from coapthon.resources.resource import Resource

import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.common.ISystemPerformanceDataListener import ISystemPerformanceDataListener
from programmingtheiot.data.DataUtil import DataUtil
from programmingtheiot.data.SystemPerformanceData import SystemPerformanceData


class GetSystemPerformanceResourceHandler(Resource, ISystemPerformanceDataListener):
    def __init__(self, name: str = ConfigConst.SYSTEM_PERF_MSG, coap_server=None, dataMsgListener: IDataMessageListener = None):
        super(GetSystemPerformanceResourceHandler, self).__init__(
            name, coap_server, visible=True, observable=True, allow_children=True)

        self.pollCycles = ConfigUtil().getInteger(
            section=ConfigConst.CONSTRAINED_DEVICE,
            key=ConfigConst.POLL_CYCLES_KEY,
            defaultVal=ConfigConst.DEFAULT_POLL_CYCLES
        )

        self.dataUtil = DataUtil()
        self.sysPerfData = SystemPerformanceData()
        self.dataMsgListener = dataMsgListener

        if self.dataMsgListener:
            self.dataMsgListener.setSystemPerformanceDataListener(self)

        self.payload = "GetSysPerfData"

    def render_GET_advanced(self, request, response):
        if request:
            response.code = defines.Codes.CONTENT.number
            jsonData = DataUtil().systemPerformanceDataToJson(self.sysPerfData)
            logging.info("Latest SystemPerformanceData JSON: " + jsonData)
            response.payload = (defines.Content_types["application/json"], jsonData)
            response.max_age = self.pollCycles
            self.changed = False
        return self, response

    def onSystemPerformanceDataUpdate(self, data: SystemPerformanceData) -> bool:
        self.sysPerfData = data