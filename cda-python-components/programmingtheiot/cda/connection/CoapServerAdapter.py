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

import logging
import traceback
from threading import Thread
from time import sleep

from coapthon.server.coap import CoAP
from coapthon.resources.resource import Resource

import programmingtheiot.common.ConfigConst as ConfigConst
from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum
from programmingtheiot.common.IDataMessageListener import IDataMessageListener

# Importation des gestionnaires de ressources (Handlers)
from programmingtheiot.cda.connection.handlers.GetTelemetryResourceHandler import GetTelemetryResourceHandler
from programmingtheiot.cda.connection.handlers.UpdateActuatorResourceHandler import UpdateActuatorResourceHandler
from programmingtheiot.cda.connection.handlers.GetSystemPerformanceResourceHandler import GetSystemPerformanceResourceHandler


class CoapServerAdapter():
    """
    Definition for a CoAP communications server, with embedded test functions.
    """

    def __init__(self, dataMsgListener=None):
        self.config = ConfigUtil()
        self.dataMsgListener = dataMsgListener
        self.enableConfirmedMsgs = False
        self.host = self.config.getProperty(
            ConfigConst.COAP_GATEWAY_SERVICE,
            ConfigConst.HOST_KEY,
            ConfigConst.DEFAULT_HOST
        )
        self.port = self.config.getInteger(
            ConfigConst.COAP_GATEWAY_SERVICE,
            ConfigConst.PORT_KEY,
            ConfigConst.DEFAULT_COAP_PORT
        )
        self.serverUri = f"coap://{self.host}:{self.port}"

        self.coapServer = None
        self.coapServerTask = None
        self.listenTimeout = 30

        self._initServer()
        logging.info(f"CoAP server configured for host and port: {self.serverUri}")

    def _initServer(self):
        try:
            # Initialisation du serveur de base CoAPthon
            self.coapServer = CoAP(server_address=(self.host, self.port))

            # Enregistrement dynamique de la ressource d'Actionneur (PUT)
            self.addResource(
                resourcePath=ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE,
                resource=UpdateActuatorResourceHandler(dataMsgListener=self.dataMsgListener)
            )

            # Enregistrement dynamique de la ressource de Performance Système (GET - Observable)
            self.addResource(
                resourcePath=ResourceNameEnum.CDA_SYSTEM_PERF_MSG_RESOURCE,
                resource=GetSystemPerformanceResourceHandler(dataMsgListener=self.dataMsgListener)
            )

            # Enregistrement dynamique de la ressource de Télémétrie/Capteurs (GET - Observable)
            self.addResource(
                resourcePath=ResourceNameEnum.CDA_SENSOR_MSG_RESOURCE,
                resource=GetTelemetryResourceHandler(dataMsgListener=self.dataMsgListener)
            )

            logging.info("Created CoAP server with default hierarchical resources.")

        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)
            logging.warning("Failed to create CoAP server with dynamic resources.")

    def _runServer(self):
        try:
            logging.info("CoAP server thread is now listening...")
            self.coapServer.listen(self.listenTimeout)
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)
            logging.warning("Failed to run CoAP server listener safely.")

    def addResource(self, resourcePath: ResourceNameEnum = None, endName: str = None, resource=None):
        if resourcePath and resource:
            uriPath = resourcePath.value

            # Gestion optionnelle d'un sous-chemin spécifique (ex: Humidifier)
            if endName:
                uriPath = uriPath + '/' + endName
                resource.name = endName

            trimmedUriPath = uriPath.strip("/")
            resourceList = trimmedUriPath.split("/")
            resourceTree = None
            registrationPath = ""
            generationCount = 0

            # Analyse hiérarchique de l'arborescence CoAP
            for resourceName in resourceList:
                generationCount += 1
                registrationPath = registrationPath + "/" + resourceName
                try:
                    resourceTree = self.coapServer.root[registrationPath]
                except KeyError:
                    resourceTree = None

                # Si le chemin complet n'existe pas encore, on l'ajoute au serveur
                if not resourceTree:
                    if len(resourceList) != generationCount:
                        return None
                    resource.path = registrationPath
                    self.coapServer.root[registrationPath] = resource

            logging.info(f"Successfully registered resource tree path: {registrationPath}")
        else:
            logging.warning("No resource provided for path: " + str(resourcePath.value if resourcePath else "None"))

    def startServer(self):
        if self.coapServer:
            logging.info("Starting CoAP server...")
            if self.coapServerTask and self.coapServerTask.is_alive():
                self.stopServer()
                self.coapServerTask = None

            self.coapServerTask = Thread(target=self._runServer)
            self.coapServerTask.setDaemon(True)
            self.coapServerTask.start()
            logging.info("\n\n***** CoAP server started. *****\n\n")
        else:
            logging.warning("CoAP server not yet initialized (shouldn't happen).")

    def stopServer(self):
        if self.coapServer:
            logging.info("Stopping CoAP server...")
            try:
                self.coapServer.close()
                if self.coapServerTask:
                    self.coapServerTask.join(5)
            except Exception as e:
                logging.warning(f"Error while closing CoAP server: {e}")
        else:
            logging.warning("CoAP server not yet initialized (shouldn't happen).")

    def setDataMessageListener(self, listener: IDataMessageListener = None) -> bool:
        if listener:
            self.dataMsgListener = listener
            return True
        return False