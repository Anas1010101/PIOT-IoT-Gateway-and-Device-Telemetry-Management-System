package programmingtheiot.gda.app;

import java.time.OffsetDateTime;
import java.time.temporal.ChronoUnit;
import java.util.logging.Logger;

import programmingtheiot.common.ConfigConst;
import programmingtheiot.common.ConfigUtil;
import programmingtheiot.common.IActuatorDataListener;
import programmingtheiot.common.IDataMessageListener;
import programmingtheiot.common.ResourceNameEnum;
import programmingtheiot.data.ActuatorData;
import programmingtheiot.data.BaseIotData;
import programmingtheiot.data.DataUtil;
import programmingtheiot.data.SensorData;
import programmingtheiot.data.SystemPerformanceData;
import programmingtheiot.gda.connection.CoapServerGateway;
import programmingtheiot.gda.connection.IPersistenceClient;
import programmingtheiot.gda.connection.IPubSubClient;
import programmingtheiot.gda.connection.MqttClientConnector;
import programmingtheiot.gda.system.SystemPerformanceManager;

public class DeviceDataManager implements IDataMessageListener
{
	private static final Logger _Logger =
		Logger.getLogger(DeviceDataManager.class.getName());

	private boolean enableMqttClient = true;
	private boolean enableCoapServer = false;
	private boolean enableCloudClient = false;
	private boolean enablePersistenceClient = false;
	private boolean enableSystemPerf = false;

	private MqttClientConnector mqttClient = null;
	private IPubSubClient cloudClient = null;
	private IPersistenceClient persistenceClient = null;
	private CoapServerGateway coapServer = null;
	private SystemPerformanceManager sysPerfMgr = null;
	private IActuatorDataListener actuatorDataListener = null;

	private ActuatorData latestHumidifierActuatorData = null;
	private ActuatorData latestHumidifierActuatorResponse = null;
	private SensorData latestHumiditySensorData = null;
	private OffsetDateTime latestHumiditySensorTimeStamp = null;

	private boolean handleHumidityChangeOnDevice = false;
	private int lastKnownHumidifierCommand = ConfigConst.OFF_COMMAND;

	private long humidityMaxTimePastThreshold = 300;
	private float nominalHumiditySetting = 40.0f;
	private float triggerHumidifierFloor = 30.0f;
	private float triggerHumidifierCeiling = 50.0f;

	public DeviceDataManager()
	{
		super();

		ConfigUtil configUtil = ConfigUtil.getInstance();

		this.enableMqttClient =
			configUtil.getBoolean(ConfigConst.GATEWAY_DEVICE, ConfigConst.ENABLE_MQTT_CLIENT_KEY);

		this.enableCoapServer =
			configUtil.getBoolean(ConfigConst.GATEWAY_DEVICE, ConfigConst.ENABLE_COAP_SERVER_KEY);

		this.enableCloudClient =
			configUtil.getBoolean(ConfigConst.GATEWAY_DEVICE, ConfigConst.ENABLE_CLOUD_CLIENT_KEY);

		this.enablePersistenceClient =
			configUtil.getBoolean(ConfigConst.GATEWAY_DEVICE, ConfigConst.ENABLE_PERSISTENCE_CLIENT_KEY);

		this.handleHumidityChangeOnDevice =
			configUtil.getBoolean(ConfigConst.GATEWAY_DEVICE, "handleHumidityChangeOnDevice");

		this.humidityMaxTimePastThreshold =
			configUtil.getInteger(ConfigConst.GATEWAY_DEVICE, "humidityMaxTimePastThreshold");

		this.nominalHumiditySetting =
			configUtil.getFloat(ConfigConst.GATEWAY_DEVICE, "nominalHumiditySetting");

		this.triggerHumidifierFloor =
			configUtil.getFloat(ConfigConst.GATEWAY_DEVICE, "triggerHumidifierFloor");

		this.triggerHumidifierCeiling =
			configUtil.getFloat(ConfigConst.GATEWAY_DEVICE, "triggerHumidifierCeiling");

		if (this.humidityMaxTimePastThreshold < 10 || this.humidityMaxTimePastThreshold > 7200) {
			this.humidityMaxTimePastThreshold = 300;
		}

		initManager();
	}

	public DeviceDataManager(
		boolean enableMqttClient,
		boolean enableCoapClient,
		boolean enableCloudClient,
		boolean enableSmtpClient,
		boolean enablePersistenceClient)
	{
		super();

		this.enableMqttClient = enableMqttClient;
		this.enableCoapServer = enableCoapClient;
		this.enableCloudClient = enableCloudClient;
		this.enablePersistenceClient = enablePersistenceClient;

		initConnections();
	}

	@Override
	public boolean handleActuatorCommandResponse(ResourceNameEnum resourceName, ActuatorData data)
	{
		if (data != null) {
			_Logger.info("Handling actuator response: " + data.getName());

			if (data.hasError()) {
				_Logger.warning("Error flag set for ActuatorData instance.");
			}

			this.latestHumidifierActuatorResponse = data;
			handleIncomingDataAnalysis(resourceName, data);

			return true;
		}

		return false;
	}

	@Override
	public boolean handleActuatorCommandRequest(ResourceNameEnum resourceName, ActuatorData data)
	{
		if (data != null) {
			_Logger.info("Handling actuator request command outbound: " + data.getName());
			handleIncomingDataAnalysis(resourceName, data);
			return true;
		}

		return false;
	}

	@Override
	public boolean handleIncomingMessage(ResourceNameEnum resourceName, String msg)
	{
		if (msg != null) {
			_Logger.info("Handling incoming generic message: " + msg);
			return true;
		}

		return false;
	}

	@Override
	public boolean handleSensorMessage(ResourceNameEnum resourceName, SensorData data)
	{
		if (data != null) {
			_Logger.info("Handling sensor message: " + data.getName());

			if (data.hasError()) {
				_Logger.warning("Error flag set for SensorData instance.");
			}

			String jsonData = DataUtil.getInstance().sensorDataToJson(data);
			int qos = ConfigConst.DEFAULT_QOS;

			if (this.enablePersistenceClient && this.persistenceClient != null) {
				this.persistenceClient.storeData(resourceName.getResourceName(), qos, data);
			}

			handleIncomingDataAnalysis(resourceName, data);
			handleUpstreamTransmission(resourceName, jsonData, qos);

			return true;
		}

		return false;
	}

	@Override
	public boolean handleSystemPerformanceMessage(ResourceNameEnum resourceName, SystemPerformanceData data)
	{
		if (data != null) {
			_Logger.info("Handling system performance message: " + data.getName());

			if (data.hasError()) {
				_Logger.warning("Error flag set for SystemPerformanceData instance.");
			}

			String jsonData = DataUtil.getInstance().systemPerformanceDataToJson(data);
			int qos = ConfigConst.DEFAULT_QOS;

			if (this.enablePersistenceClient && this.persistenceClient != null) {
				this.persistenceClient.storeData(resourceName.getResourceName(), qos, data);
			}

			handleUpstreamTransmission(resourceName, jsonData, qos);

			return true;
		}

		return false;
	}

	@Override
	public void setActuatorDataListener(String name, IActuatorDataListener listener)
	{
		if (listener != null) {
			this.actuatorDataListener = listener;
			_Logger.info("Successfully registered ActuatorDataListener.");
		}
	}

	public void startManager()
	{
		if (this.mqttClient != null) {
			if (this.mqttClient.connectClient()) {
				_Logger.info("Successfully connected MQTT client to broker.");
			} else {
				_Logger.severe("Failed to connect MQTT client to broker.");
			}
		}

		if (this.enableCoapServer && this.coapServer != null) {
			if (this.coapServer.startServer()) {
				_Logger.info("CoAP server started successfully via Manager.");
			} else {
				_Logger.severe("Failed to start CoAP server. Check log file for details.");
			}
		}

		if (this.sysPerfMgr != null) {
			this.sysPerfMgr.startManager();
		}
	}

	public void stopManager()
	{
		if (this.sysPerfMgr != null) {
			this.sysPerfMgr.stopManager();
		}

		if (this.enableCoapServer && this.coapServer != null) {
			this.coapServer.stopServer();
		}

		if (this.mqttClient != null) {
			this.mqttClient.unsubscribeFromTopic(ResourceNameEnum.CDA_ACTUATOR_RESPONSE_RESOURCE);
			this.mqttClient.unsubscribeFromTopic(ResourceNameEnum.CDA_SENSOR_MSG_RESOURCE);
			this.mqttClient.unsubscribeFromTopic(ResourceNameEnum.CDA_SYSTEM_PERF_MSG_RESOURCE);
			this.mqttClient.disconnectClient();
		}
	}

	private void handleIncomingDataAnalysis(ResourceNameEnum resource, ActuatorData data)
	{
		_Logger.fine("Analyzing incoming actuator data: " + data.getName());

		if (data.isResponseFlagEnabled()) {
			this.latestHumidifierActuatorResponse = data;
			_Logger.info("Received actuator response from CDA: " + data.getName());
		}
	}

	private void handleIncomingDataAnalysis(ResourceNameEnum resource, SensorData data)
	{
		_Logger.fine("Analyzing incoming sensor data: " + data.getName());

		if (data.getTypeID() == ConfigConst.HUMIDITY_SENSOR_TYPE) {
			handleHumiditySensorAnalysis(resource, data);
		}
	}

	private void handleHumiditySensorAnalysis(ResourceNameEnum resource, SensorData data)
	{
		if (!this.handleHumidityChangeOnDevice) {
			return;
		}

		_Logger.info("Analyzing humidity data from CDA. Value: " + data.getValue());

		boolean isLow = data.getValue() < this.triggerHumidifierFloor;
		boolean isHigh = data.getValue() > this.triggerHumidifierCeiling;

		if (isLow || isHigh) {
			if (this.latestHumiditySensorData == null) {
				this.latestHumiditySensorData = data;
				this.latestHumiditySensorTimeStamp = getDateTimeFromData(data);

				_Logger.info(
					"Humidity threshold crossed. Waiting for confirmation period: " +
					this.humidityMaxTimePastThreshold +
					" seconds.");

				return;
			}

			OffsetDateTime currentTimeStamp = getDateTimeFromData(data);

			long diffSeconds =
				ChronoUnit.SECONDS.between(
					this.latestHumiditySensorTimeStamp,
					currentTimeStamp);

			_Logger.info("Humidity threshold time delta: " + diffSeconds + " seconds.");

			if (diffSeconds >= this.humidityMaxTimePastThreshold) {
				ActuatorData ad = new ActuatorData();
				ad.setName(ConfigConst.HUMIDIFIER_ACTUATOR_NAME);
				ad.setLocationID(data.getLocationID());
				ad.setTypeID(ConfigConst.HUMIDIFIER_ACTUATOR_TYPE);
				ad.setValue(this.nominalHumiditySetting);

				if (isLow) {
					ad.setCommand(ConfigConst.ON_COMMAND);
				} else {
					ad.setCommand(ConfigConst.OFF_COMMAND);
				}

				_Logger.info("Humidity actuation event triggered. Sending command to CDA: " + ad);

				this.lastKnownHumidifierCommand = ad.getCommand();
				this.latestHumidifierActuatorData = ad;

				sendActuatorCommandToCda(ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE, ad);

				this.latestHumiditySensorData = null;
				this.latestHumiditySensorTimeStamp = null;
			}
		} else {
			this.latestHumiditySensorData = null;
			this.latestHumiditySensorTimeStamp = null;

			if (this.lastKnownHumidifierCommand == ConfigConst.ON_COMMAND) {
				ActuatorData ad = new ActuatorData();
				ad.setName(ConfigConst.HUMIDIFIER_ACTUATOR_NAME);
				ad.setLocationID(data.getLocationID());
				ad.setTypeID(ConfigConst.HUMIDIFIER_ACTUATOR_TYPE);
				ad.setCommand(ConfigConst.OFF_COMMAND);
				ad.setValue(this.nominalHumiditySetting);

				_Logger.info("Humidity returned to nominal range. Sending humidifier OFF command.");

				this.lastKnownHumidifierCommand = ConfigConst.OFF_COMMAND;
				this.latestHumidifierActuatorData = ad;

				sendActuatorCommandToCda(ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE, ad);
			}
		}
	}

	private void sendActuatorCommandToCda(ResourceNameEnum resource, ActuatorData data)
	{
		if (this.actuatorDataListener != null) {
			this.actuatorDataListener.onActuatorDataUpdate(data);
		}

		if (this.enableMqttClient && this.mqttClient != null) {
			String jsonData = DataUtil.getInstance().actuatorDataToJson(data);

			if (this.mqttClient.publishMessage(resource, jsonData, ConfigConst.DEFAULT_QOS)) {
				_Logger.info("Published ActuatorData command from GDA to CDA: " + data.getCommand());
			} else {
				_Logger.warning("Failed to publish ActuatorData command from GDA to CDA: " + data.getCommand());
			}
		}
	}

	private void handleUpstreamTransmission(ResourceNameEnum resource, String jsonData, int qos)
	{
		_Logger.info("TODO: Send JSON data to cloud service: " + resource);
	}

	private OffsetDateTime getDateTimeFromData(BaseIotData data)
	{
		try {
			return OffsetDateTime.parse(data.getTimeStamp());
		} catch (Exception e) {
			_Logger.warning("Failed to parse timestamp. Using current time.");
			return OffsetDateTime.now();
		}
	}

	private void initConnections()
	{
		if (this.enableMqttClient) {
			this.mqttClient = new MqttClientConnector();
			this.mqttClient.setDataMessageListener(this);
		}

		if (this.enableCoapServer) {
			this.coapServer = new CoapServerGateway(this);
		}
	}

	private void initManager()
	{
		ConfigUtil configUtil = ConfigUtil.getInstance();

		this.enableSystemPerf =
			configUtil.getBoolean(ConfigConst.GATEWAY_DEVICE, ConfigConst.ENABLE_SYSTEM_PERF_KEY);

		if (this.enableSystemPerf) {
			this.sysPerfMgr = new SystemPerformanceManager();
			this.sysPerfMgr.setDataMessageListener(this);
		}

		initConnections();
	}
}