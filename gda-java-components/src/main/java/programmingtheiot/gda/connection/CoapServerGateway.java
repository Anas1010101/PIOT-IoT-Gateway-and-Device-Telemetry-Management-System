/**
* This class is part of the Programming the Internet of Things
* project, and is available via the MIT License, which can be
* found in the LICENSE file at the top level of this repository.
* * Copyright (c) 2020 - 2026 by Andrew D. King
*/


package programmingtheiot.gda.connection;


import java.util.List;
import java.util.Queue;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.eclipse.californium.core.CoapResource;
import org.eclipse.californium.core.CoapServer;
import org.eclipse.californium.core.config.CoapConfig;
import org.eclipse.californium.core.network.Endpoint;
import org.eclipse.californium.core.network.interceptors.MessageTracer;
import org.eclipse.californium.core.server.resources.Resource;
import org.eclipse.californium.elements.config.Configuration;

import programmingtheiot.common.IDataMessageListener;
import programmingtheiot.common.ResourceNameEnum;
import programmingtheiot.gda.connection.handlers.GetActuatorCommandResourceHandler;
import programmingtheiot.gda.connection.handlers.UpdateSystemPerformanceResourceHandler;
import programmingtheiot.gda.connection.handlers.UpdateTelemetryResourceHandler;


/**
* Class representation for Eclipse Californium CoAP Server implementation.
* Manages the explicit binding, dynamic runtime orchestration, and cascading hierarchical
* tree initialization for all system and telemetry CoAP resources.
*/
public class CoapServerGateway
{
// static
private static final Logger _Logger =
Logger.getLogger(CoapServerGateway.class.getName());
static {
CoapConfig.register();
}
// params
private CoapServer coapServer = null;
private IDataMessageListener dataMsgListener = null;
private boolean isInitialized = false;
// constructors
/**
* Constructor.
* @param dataMsgListener Reference to the core orchestrator listener.
*/
public CoapServerGateway(IDataMessageListener dataMsgListener)
{
super();
this.dataMsgListener = dataMsgListener;
initServer();
}


// public methods
/**
* Public runtime method to add an externally managed resource handler into the tree.
* @param resourceType The target logical enum path definition.
* @param endName Optional overriding terminal name (can be null).
* @param resource The specialized resource handler instance to register.
*/
public void addResource(ResourceNameEnum resourceType, String endName, Resource resource)
{
if (resourceType != null && resource != null) {
createAndAddResourceChain(resourceType, resource);
} else {
_Logger.warning("Cannot add resource: resourceType or resource reference is null.");
}
}
public boolean hasResource(String name)
{
if (this.coapServer != null && name != null) {
return this.coapServer.getRoot().getChild(name) != null;
}
return false;
}
public void setDataMessageListener(IDataMessageListener listener)
{
if (listener != null) {
this.dataMsgListener = listener;
}
}
public boolean startServer()
{
try {
if (this.coapServer != null) {
this.coapServer.start();
for (Endpoint ep : this.coapServer.getEndpoints()) {
ep.addInterceptor(new MessageTracer());
}
_Logger.info("CoAP Server successfully started.");
return true;
} else {
_Logger.warning("CoAP server START failed. Not yet initialized.");
}
} catch (Exception e) {
_Logger.log(Level.SEVERE, "Failed to start CoAP server.", e);
}
return false;
}
public boolean stopServer()
{
try {
if (this.coapServer != null) {
this.coapServer.stop();
_Logger.info("CoAP Server successfully stopped.");
return true;
} else {
_Logger.warning("CoAP server STOP failed. Not yet initialized.");
}
} catch (Exception e) {
_Logger.log(Level.SEVERE, "Failed to stop CoAP server.", e);
}
return false;
}
// private methods
/**
* Dynamically unpacks a ResourceNameEnum path into a composite structure representation tree.
* Parses segments via an ArrayBlockingQueue and appends structural or leaves elements securely.
*/
private void createAndAddResourceChain(ResourceNameEnum resourceType, Resource resource)
{
_Logger.info("Adding server resource handler chain: " + resourceType.getResourceName());
List<String> resourceNames = resourceType.getResourceNameChain();
Queue<String> queue = new ArrayBlockingQueue<>(resourceNames.size());
queue.addAll(resourceNames);
Resource parentResource = this.coapServer.getRoot();
if (parentResource == null) {
String rootName = queue.poll();
parentResource = new CoapResource(rootName);
this.coapServer.add(parentResource);
}
while (!queue.isEmpty()) {
String resourceName = queue.poll();
Resource nextResource = parentResource.getChild(resourceName);
if (nextResource == null) {
if (queue.isEmpty()) {
// C'est le nœud terminal (la feuille), on injecte le handler spécialisé fourni
nextResource = resource;
nextResource.setName(resourceName);
} else {
// Segment structurel intermédiaire (ex: PIOT ou ConstrainedDevice)
nextResource = new CoapResource(resourceName);
}
parentResource.add(nextResource);
}
parentResource = nextResource;
}
}
/**
* Explicitly loads Californium standard network properties and instances the target resources.
*/
private void initServer(ResourceNameEnum ...resources)
{
if (this.isInitialized) {
return;
}
try {
Configuration config = Configuration.getStandard();
this.coapServer = new CoapServer(config);
_Logger.info("CoAP server instance created successfully with standard configuration.");
initDefaultResources();
this.isInitialized = true;
} catch (Exception e) {
_Logger.log(Level.SEVERE, "Failed to initialize CoAP server instance.", e);
}
}
/**
* Instantiates and registers pre-defined functional resource handlers internally.
*/
private void initDefaultResources()
{
_Logger.info("Initializing pre-defined default CoAP resource handlers...");


// 1. Gestionnaire d'actionnement observable (GDA -> CDA)
GetActuatorCommandResourceHandler getActuatorCmdResourceHandler =
new GetActuatorCommandResourceHandler(ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE.getResourceType());
if (this.dataMsgListener != null) {
this.dataMsgListener.setActuatorDataListener(null, getActuatorCmdResourceHandler);
}
addResource(ResourceNameEnum.CDA_ACTUATOR_CMD_RESOURCE, null, getActuatorCmdResourceHandler);
// 2. Gestionnaire de télémétrie des capteurs (CDA -> GDA)
UpdateTelemetryResourceHandler updateTelemetryResourceHandler =
new UpdateTelemetryResourceHandler(ResourceNameEnum.CDA_SENSOR_MSG_RESOURCE.getResourceType());
updateTelemetryResourceHandler.setDataMessageListener(this.dataMsgListener);
addResource(ResourceNameEnum.CDA_SENSOR_MSG_RESOURCE, null, updateTelemetryResourceHandler);
// 3. Gestionnaire des métriques de performance système (CDA -> GDA)
UpdateSystemPerformanceResourceHandler updateSystemPerformanceResourceHandler =
new UpdateSystemPerformanceResourceHandler(ResourceNameEnum.CDA_SYSTEM_PERF_MSG_RESOURCE.getResourceType());
updateSystemPerformanceResourceHandler.setDataMessageListener(this.dataMsgListener);
addResource(ResourceNameEnum.CDA_SYSTEM_PERF_MSG_RESOURCE, null, updateSystemPerformanceResourceHandler);
}
}

