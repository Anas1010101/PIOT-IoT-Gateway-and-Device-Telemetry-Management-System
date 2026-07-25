import logging

from coapthon import defines
from coapthon.resources.resource import Resource

import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.data.DataUtil import DataUtil
from programmingtheiot.data.ActuatorData import ActuatorData


class UpdateActuatorResourceHandler(Resource):
    def __init__(self, dataMsgListener: IDataMessageListener = None):
        # Initialize the CoAP resource
        super(UpdateActuatorResourceHandler, self).__init__(
            name=ConfigConst.ACTUATOR_CMD_RESOURCE,
            coap_server=None,
            visible=True,
            observable=True,
            allow_children=True
        )

        self.dataMsgListener = dataMsgListener
        self.dataUtil = DataUtil()
        self.pollCycles = ConfigUtil().getInteger(
            section=ConfigConst.CONSTRAINED_DEVICE,
            key=ConfigConst.POLL_CYCLES_KEY,
            defaultVal=ConfigConst.DEFAULT_POLL_CYCLES
        )

    def render_PUT_advanced(self, request, response):
        if request:
            logging.info("PUT request received: " + str(request.get_payload()))
            # Convert incoming JSON payload to ActuatorData
            requestPayload = request.get_payload()
            actuatorCmdData = self.dataUtil.jsonToActuatorData(requestPayload)

            # Respond with result
            response.payload = self._createResponse(response=response, data=actuatorCmdData)
            response.max_age = self.pollCycles

        return self, response

    def _createResponse(self, response=None, data: ActuatorData = None) -> str:
        # Send the command to the DeviceDataManager (or CDA)
        actuatorResponseData = None
        if self.dataMsgListener:
            actuatorResponseData = self.dataMsgListener.handleActuatorCommandMessage(data)

        if not actuatorResponseData:
            # Fallback if something went wrong
            actuatorResponseData = ActuatorData()
            actuatorResponseData.updateData(data)
            actuatorResponseData.setAsResponse()
            actuatorResponseData.setStatusCode(-1)
            if response:
                response.code = defines.Codes.PRECONDITION_FAILED.number
        else:
            if response:
                response.code = defines.Codes.CHANGED.number

        # Return JSON representation of actuator response
        jsonData = self.dataUtil.actuatorDataToJson(actuatorResponseData)
        return (defines.Content_types["application/json"], jsonData)