package programmingtheiot.integration.connection;

import java.util.logging.Logger;

import org.junit.After;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import org.junit.Before;
import org.junit.Test;

import programmingtheiot.gda.connection.MqttClientConnector;

public class MqttClientConnectorTest
{
	private static final Logger _Logger =
		Logger.getLogger(MqttClientConnectorTest.class.getName());

	private MqttClientConnector mqttClient = null;

	@Before
	public void setUp() throws Exception
	{
		this.mqttClient = new MqttClientConnector();
	}

	@After
	public void tearDown() throws Exception
	{
		if (this.mqttClient != null && this.mqttClient.isConnected()) {
			this.mqttClient.disconnectClient();
		}
	}

	@Test
	public void testConnectAndDisconnect()
		{
			
			assertTrue(this.mqttClient.connectClient());
			try {
		Thread.sleep(2000);
	} catch (Exception e) {
		// ignore
	}

		assertFalse(this.mqttClient.connectClient());

		assertTrue(this.mqttClient.disconnectClient());

		assertFalse(this.mqttClient.disconnectClient());
	}

	//@Test
	public void testPublishAndSubscribe()
	{
		// Disabled for PIOT-GDA-07-001.
		// This will be used in the next MQTT card.
	}
}