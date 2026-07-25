import logging
import ssl
import time
import paho.mqtt.client as mqttClient

import programmingtheiot.common.ConfigConst as ConfigConst

from programmingtheiot.common.ConfigUtil import ConfigUtil
from programmingtheiot.common.IDataMessageListener import IDataMessageListener
from programmingtheiot.common.ResourceNameEnum import ResourceNameEnum

from programmingtheiot.cda.connection.IPubSubClient import IPubSubClient

from programmingtheiot.data.DataUtil import DataUtil


class MqttClientConnector(IPubSubClient):

	def __init__(self, clientID: str = None):
		self.config = ConfigUtil()
		self.dataMsgListener = None

		self.host = self.config.getProperty(
			ConfigConst.MQTT_GATEWAY_SERVICE,
			ConfigConst.HOST_KEY,
			ConfigConst.DEFAULT_HOST
		)

		self.port = self.config.getInteger(
			ConfigConst.MQTT_GATEWAY_SERVICE,
			ConfigConst.PORT_KEY,
			ConfigConst.DEFAULT_MQTT_PORT
		)

		self.securePort = self.config.getInteger(
			ConfigConst.MQTT_GATEWAY_SERVICE,
			ConfigConst.SECURE_PORT_KEY,
			8883
		)

		self.keepAlive = self.config.getInteger(
			ConfigConst.MQTT_GATEWAY_SERVICE,
			ConfigConst.KEEP_ALIVE_KEY,
			ConfigConst.DEFAULT_KEEP_ALIVE
		)

		self.defaultQos = self.config.getInteger(
			ConfigConst.MQTT_GATEWAY_SERVICE,
			ConfigConst.DEFAULT_QOS_KEY,
			ConfigConst.DEFAULT_QOS
		)

		self.enableCrypt = self.config.getBoolean(
			ConfigConst.MQTT_GATEWAY_SERVICE,
			ConfigConst.ENABLE_CRYPT_KEY,
			False
		)

		self.certFile = self.config.getProperty(
			ConfigConst.MQTT_GATEWAY_SERVICE,
			ConfigConst.CERT_FILE_KEY,
			None
		)

		self.mqttClient = None

		if clientID:
			self.clientID = clientID
		else:
			self.clientID = self.config.getProperty(
				ConfigConst.CONSTRAINED_DEVICE,
				ConfigConst.DEVICE_LOCATION_ID_KEY,
				"CDAMqttClientID001"
			)

		if self.enableCrypt:
			self.port = self.securePort

		logging.info("\tMQTT Client ID:   " + self.clientID)
		logging.info("\tMQTT Broker Host: " + self.host)
		logging.info("\tMQTT Broker Port: " + str(self.port))
		logging.info("\tMQTT Keep Alive:  " + str(self.keepAlive))
		logging.info("\tMQTT TLS Enabled: " + str(self.enableCrypt))

	def connectClient(self) -> bool:
		if not self.mqttClient:
			self.mqttClient = mqttClient.Client(
				client_id = self.clientID,
				clean_session = True
			)

			self.mqttClient.on_connect = self.onConnect
			self.mqttClient.on_disconnect = self.onDisconnect
			self.mqttClient.on_message = self.onMessage
			self.mqttClient.on_publish = self.onPublish
			self.mqttClient.on_subscribe = self.onSubscribe

			if self.enableCrypt:
				logging.info("Configuring MQTT TLS using cert file: " + str(self.certFile))

				self.mqttClient.tls_set(
					ca_certs = self.certFile,
					certfile = None,
					keyfile = None,
					cert_reqs = ssl.CERT_REQUIRED,
					tls_version = ssl.PROTOCOL_TLS_CLIENT
				)

		if not self.mqttClient.is_connected():
			logging.info("MQTT client connecting to broker at host: " + self.host)

			self.mqttClient.connect(
				self.host,
				self.port,
				self.keepAlive
			)

			self.mqttClient.loop_start()

			for i in range(10):
				if self.mqttClient.is_connected():
					return True
				time.sleep(0.1)

			logging.warning("MQTT client failed to connect within timeout.")
			return False

		logging.warning("MQTT client is already connected. Ignoring connect request.")
		return False

	def disconnectClient(self) -> bool:
		if self.mqttClient and self.mqttClient.is_connected():
			self.mqttClient.loop_stop()
			self.mqttClient.disconnect()
			return True

		logging.warning("MQTT client already disconnected. Ignoring.")
		return False

	def publishMessage(
		self,
		resource: ResourceNameEnum = None,
		msg: str = None,
		qos: int = ConfigConst.DEFAULT_QOS
	) -> bool:
		if not resource:
			logging.warning("No topic specified. Cannot publish message.")
			return False

		if not msg:
			logging.warning("No message specified. Cannot publish message to topic: " + resource.value)
			return False

		if qos < 0 or qos > 2:
			qos = ConfigConst.DEFAULT_QOS

		if not self.mqttClient or not self.mqttClient.is_connected():
			logging.warning("MQTT client is not connected. Cannot publish message.")
			return False

		msgInfo = self.mqttClient.publish(
			topic = resource.value,
			payload = msg,
			qos = qos
		)

		# Important for Lab Module 10: do not block here
		# msgInfo.wait_for_publish()

		return True

	def subscribeToTopic(
		self,
		resource: ResourceNameEnum = None,
		callback = None,
		qos: int = ConfigConst.DEFAULT_QOS
	) -> bool:
		if not resource:
			logging.warning("No topic specified. Cannot subscribe.")
			return False

		if qos < 0 or qos > 2:
			qos = ConfigConst.DEFAULT_QOS

		if not self.mqttClient or not self.mqttClient.is_connected():
			logging.warning("MQTT client is not connected. Cannot subscribe.")
			return False

		logging.info("Subscribing to topic %s", resource.value)

		if callback:
			self.mqttClient.message_callback_add(resource.value, callback)

		self.mqttClient.subscribe(resource.value, qos)

		return True

	def unsubscribeFromTopic(self, resource: ResourceNameEnum = None) -> bool:
		if not resource:
			logging.warning("No topic specified. Cannot unsubscribe.")
			return False

		if not self.mqttClient or not self.mqttClient.is_connected():
			logging.warning("MQTT client is not connected. Cannot unsubscribe.")
			return False

		logging.info("Unsubscribing from topic %s", resource.value)

		self.mqttClient.unsubscribe(resource.value)

		try:
			self.mqttClient.message_callback_remove(resource.value)
		except Exception:
			pass

		return True

	def setDataMessageListener(self, listener: IDataMessageListener = None) -> bool:
		if listener:
			self.dataMsgListener = listener
			return True

		return False

	def onConnect(self, client, userdata, flags, rc):
		logging.info("[Callback] Connected to MQTT broker. Result code: " + str(rc))

		self.mqttClient.subscribe(
			topic = ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE.value,
			qos = self.defaultQos
		)

		self.mqttClient.message_callback_add(
			sub = ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE.value,
			callback = self.onActuatorCommandMessage
		)

	def onDisconnect(self, client, userdata, rc):
		logging.info("[Callback] Disconnected from MQTT broker. Result code: " + str(rc))

	def onMessage(self, client, userdata, msg):
		payload = msg.payload

		if payload:
			payloadStr = payload.decode("utf-8")

			logging.info("MQTT message received with payload: " + payloadStr)

			if self.dataMsgListener:
				self.dataMsgListener.handleIncomingMessage(
					resourceEnum = ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE,
					msg = payloadStr
				)

		else:
			logging.info("MQTT message received with no payload: " + str(msg))

	def onPublish(self, client, userdata, mid):
		pass

	def onSubscribe(self, client, userdata, mid, granted_qos):
		logging.info("[Callback] Subscribed MID: " + str(mid))

	def onActuatorCommandMessage(self, client, userdata, msg):
		logging.info("[Callback] Actuator command message received. Topic: %s.", msg.topic)

		if self.dataMsgListener:
			try:
				actuatorData = DataUtil().jsonToActuatorData(
					msg.payload.decode("utf-8")
				)

				self.dataMsgListener.handleActuatorCommandMessage(actuatorData)

			except Exception:
				logging.exception(
					"Failed to convert incoming actuation command payload to ActuatorData."
				)