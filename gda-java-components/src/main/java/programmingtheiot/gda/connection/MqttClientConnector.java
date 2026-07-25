package programmingtheiot.gda.connection;
import java.io.File;
import java.util.Properties;
import java.util.logging.Level;
import java.util.logging.Logger;

import javax.net.ssl.SSLSocketFactory;

import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttCallbackExtended;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;

import programmingtheiot.common.ConfigConst;
import programmingtheiot.common.ConfigUtil;
import programmingtheiot.common.IDataMessageListener;
import programmingtheiot.common.ResourceNameEnum;
import programmingtheiot.common.SimpleCertManagementUtil;
import programmingtheiot.data.DataUtil;

public class MqttClientConnector implements IPubSubClient, MqttCallbackExtended
{
	private static final Logger _Logger =
		Logger.getLogger(MqttClientConnector.class.getName());

	private boolean useAsyncClient = false;

	private String pemFileName = null;
	private boolean enableEncryption = false;
	private boolean useCleanSession = false;
	private boolean enableAutoReconnect = true;

	private MqttClient mqttClient = null;
	private MqttConnectOptions connOpts = null;
	private MemoryPersistence persistence = null;
	private IDataMessageListener dataMsgListener = null;

	private String clientID = null;
	private String brokerAddr = null;
	private String host = ConfigConst.DEFAULT_HOST;
	private String protocol = ConfigConst.DEFAULT_MQTT_PROTOCOL;

	private int port = ConfigConst.DEFAULT_MQTT_PORT;
	private int brokerKeepAlive = ConfigConst.DEFAULT_KEEP_ALIVE;

	public MqttClientConnector()
	{
		super();

		initClientParameters(ConfigConst.MQTT_GATEWAY_SERVICE);
	}

	@Override
	public boolean connectClient()
	{
		try {
			if (this.mqttClient == null) {
				this.mqttClient =
					new MqttClient(
						this.brokerAddr,
						this.clientID,
						this.persistence);

				this.mqttClient.setCallback(this);
			}

			if (!this.mqttClient.isConnected()) {
				_Logger.info("MQTT client connecting to broker: " + this.brokerAddr);

				this.mqttClient.connect(this.connOpts);

				return true;
			} else {
				_Logger.warning("MQTT client already connected to broker: " + this.brokerAddr);
			}
		} catch (Exception e) {
			_Logger.log(Level.SEVERE, "Failed to connect MQTT client to broker.", e);
		}

		return false;
	}

	@Override
	public boolean disconnectClient()
	{
		try {
			if (this.mqttClient != null) {
				if (this.mqttClient.isConnected()) {
					_Logger.info("Disconnecting MQTT client from broker: " + this.brokerAddr);

					this.mqttClient.disconnect();

					return true;
				} else {
					_Logger.warning("MQTT client not connected to broker: " + this.brokerAddr);
				}
			}
		} catch (Exception e) {
			_Logger.log(Level.SEVERE, "Failed to disconnect MQTT client from broker: " + this.brokerAddr, e);
		}

		return false;
	}

	public boolean isConnected()
	{
		return (
			this.mqttClient != null &&
			this.mqttClient.isConnected()
		);
	}

	@Override
	public boolean publishMessage(ResourceNameEnum topicName, String msg, int qos)
	{
		if (topicName == null) {
			_Logger.warning("Resource is null. Unable to publish message: " + this.brokerAddr);
			return false;
		}

		if (msg == null || msg.length() == 0) {
			_Logger.warning("Message is null or empty. Unable to publish message: " + this.brokerAddr);
			return false;
		}

		if (qos < 0 || qos > 2) {
			qos = ConfigConst.DEFAULT_QOS;
		}

		try {
			byte[] payload = msg.getBytes();

			MqttMessage mqttMsg = new MqttMessage(payload);
			mqttMsg.setQos(qos);

			this.mqttClient.publish(topicName.getResourceName(), mqttMsg);

			return true;
		} catch (Exception e) {
			_Logger.log(Level.SEVERE, "Failed to publish message to topic: " + topicName, e);
		}

		return false;
	}

	@Override
	public boolean subscribeToTopic(ResourceNameEnum topicName, int qos)
	{
		if (topicName == null) {
			_Logger.warning("Resource is null. Unable to subscribe to topic: " + this.brokerAddr);
			return false;
		}

		if (qos < 0 || qos > 2) {
			qos = ConfigConst.DEFAULT_QOS;
		}

		try {
			this.mqttClient.subscribe(topicName.getResourceName(), qos);

			_Logger.info("Successfully subscribed to topic: " + topicName.getResourceName());

			return true;
		} catch (Exception e) {
			_Logger.log(Level.SEVERE, "Failed to subscribe to topic: " + topicName, e);
		}

		return false;
	}

	@Override
	public boolean unsubscribeFromTopic(ResourceNameEnum topicName)
	{
		if (topicName == null) {
			_Logger.warning("Resource is null. Unable to unsubscribe from topic: " + this.brokerAddr);
			return false;
		}

		try {
			this.mqttClient.unsubscribe(topicName.getResourceName());

			_Logger.info("Successfully unsubscribed from topic: " + topicName.getResourceName());

			return true;
		} catch (Exception e) {
			_Logger.log(Level.SEVERE, "Failed to unsubscribe from topic: " + topicName, e);
		}

		return false;
	}

	@Override
	public boolean setConnectionListener(IConnectionListener listener)
	{
		return false;
	}

	@Override
	public boolean setDataMessageListener(IDataMessageListener listener)
	{
		if (listener != null) {
			this.dataMsgListener = listener;
			return true;
		}

		return false;
	}

	@Override
	public void connectComplete(boolean reconnect, String serverURI)
	{
		_Logger.info(
			"MQTT connection successful (is reconnect = " +
			reconnect +
			"). Broker: " +
			serverURI);

		int qos = 1;

		this.subscribeToTopic(ResourceNameEnum.CDA_ACTUATOR_RESPONSE_RESOURCE, qos);
		this.subscribeToTopic(ResourceNameEnum.CDA_SENSOR_MSG_RESOURCE, qos);
		this.subscribeToTopic(ResourceNameEnum.CDA_SYSTEM_PERF_MSG_RESOURCE, qos);
	}

	@Override
	public void connectionLost(Throwable t)
	{
		_Logger.log(Level.WARNING, "Lost connection to MQTT broker: " + this.brokerAddr, t);
	}

	@Override
	public void deliveryComplete(IMqttDeliveryToken token)
	{
		_Logger.info("Delivered MQTT message with ID: " + token.getMessageId());
	}

	@Override
	public void messageArrived(String topic, MqttMessage msg) throws Exception
	{
		_Logger.info("MQTT message arrived on topic: " + topic);

		String payload = new String(msg.getPayload());

		try {
			if (topic.equals(ResourceNameEnum.CDA_ACTUATOR_RESPONSE_RESOURCE.getResourceName())) {

				_Logger.info("Received ActuatorData response.");

				if (this.dataMsgListener != null) {
					this.dataMsgListener.handleActuatorCommandResponse(
						ResourceNameEnum.CDA_ACTUATOR_RESPONSE_RESOURCE,
						DataUtil.getInstance().jsonToActuatorData(payload));
				}

			} else if (topic.equals(ResourceNameEnum.CDA_SENSOR_MSG_RESOURCE.getResourceName())) {

				_Logger.info("Received SensorData.");

				if (this.dataMsgListener != null) {
					this.dataMsgListener.handleSensorMessage(
						ResourceNameEnum.CDA_SENSOR_MSG_RESOURCE,
						DataUtil.getInstance().jsonToSensorData(payload));
				}

			} else if (topic.equals(ResourceNameEnum.CDA_SYSTEM_PERF_MSG_RESOURCE.getResourceName())) {

				_Logger.info("Received SystemPerformanceData.");

				if (this.dataMsgListener != null) {
					this.dataMsgListener.handleSystemPerformanceMessage(
						ResourceNameEnum.CDA_SYSTEM_PERF_MSG_RESOURCE,
						DataUtil.getInstance().jsonToSystemPerformanceData(payload));
				}
			}

		} catch (Exception e) {
			_Logger.log(
				Level.WARNING,
				"Failed to process incoming MQTT message on topic: " + topic,
				e);
		}
	}

	private void initClientParameters(String configSectionName)
	{
		ConfigUtil configUtil = ConfigUtil.getInstance();

		this.host =
			configUtil.getProperty(
				configSectionName,
				ConfigConst.HOST_KEY,
				ConfigConst.DEFAULT_HOST);

		this.port =
			configUtil.getInteger(
				configSectionName,
				ConfigConst.PORT_KEY,
				ConfigConst.DEFAULT_MQTT_PORT);

		this.brokerKeepAlive =
			configUtil.getInteger(
				configSectionName,
				ConfigConst.KEEP_ALIVE_KEY,
				ConfigConst.DEFAULT_KEEP_ALIVE);

		this.enableEncryption =
			configUtil.getBoolean(
				configSectionName,
				ConfigConst.ENABLE_CRYPT_KEY);

		this.pemFileName =
			configUtil.getProperty(
				configSectionName,
				ConfigConst.CERT_FILE_KEY);

		this.useAsyncClient =
			configUtil.getBoolean(
				ConfigConst.MQTT_GATEWAY_SERVICE,
				ConfigConst.USE_ASYNC_CLIENT_KEY);

		this.clientID =
			configUtil.getProperty(
				ConfigConst.GATEWAY_DEVICE,
				ConfigConst.DEVICE_LOCATION_ID_KEY,
				MqttClient.generateClientId());

		this.persistence = new MemoryPersistence();
		this.connOpts = new MqttConnectOptions();

		this.connOpts.setKeepAliveInterval(this.brokerKeepAlive);
		this.connOpts.setCleanSession(this.useCleanSession);
		this.connOpts.setAutomaticReconnect(this.enableAutoReconnect);

		if (this.enableEncryption) {
			initSecureConnectionParameters(configSectionName);
		}

		if (configUtil.hasProperty(configSectionName, ConfigConst.CRED_FILE_KEY)) {
			initCredentialConnectionParameters(configSectionName);
		}

		this.brokerAddr = this.protocol + "://" + this.host + ":" + this.port;

		_Logger.info("Using URL for broker conn: " + this.brokerAddr);
	}

	private void initCredentialConnectionParameters(String configSectionName)
	{
		ConfigUtil configUtil = ConfigUtil.getInstance();

		try {
			_Logger.info("Checking if credentials file exists and is loadable...");

			Properties props = configUtil.getCredentials(configSectionName);

			if (props != null) {
				this.connOpts.setUserName(
					props.getProperty(ConfigConst.USER_NAME_TOKEN_KEY, ""));

				this.connOpts.setPassword(
					props.getProperty(ConfigConst.USER_AUTH_TOKEN_KEY, "").toCharArray());

				_Logger.info("Credentials now set.");
			} else {
				_Logger.warning("No credentials are set.");
			}
		} catch (Exception e) {
			_Logger.log(Level.WARNING, "Credential file non-existent. Disabling auth requirement.");
		}
	}

	private void initSecureConnectionParameters(String configSectionName)
	{
		ConfigUtil configUtil = ConfigUtil.getInstance();

		try {
			_Logger.info("Configuring TLS...");

			if (this.pemFileName != null) {
				File file = new File(this.pemFileName);

				if (file.exists()) {
					_Logger.info("PEM file valid. Using secure connection: " + this.pemFileName);
				} else {
					this.enableEncryption = false;

					_Logger.log(
						Level.WARNING,
						"PEM file invalid. Using insecure connection: " + this.pemFileName,
						new Exception());

					return;
				}
			}

			SSLSocketFactory sslFactory =
				SimpleCertManagementUtil.getInstance().loadCertificate(this.pemFileName);

			this.connOpts.setSocketFactory(sslFactory);

			this.port =
				configUtil.getInteger(
					configSectionName,
					ConfigConst.SECURE_PORT_KEY,
					ConfigConst.DEFAULT_MQTT_SECURE_PORT);

			this.protocol = ConfigConst.DEFAULT_MQTT_SECURE_PROTOCOL;

			_Logger.info("TLS enabled.");
		} catch (Exception e) {
			_Logger.log(Level.SEVERE, "Failed to initialize secure MQTT connection. Using insecure connection.", e);

			this.enableEncryption = false;
		}
	}
}