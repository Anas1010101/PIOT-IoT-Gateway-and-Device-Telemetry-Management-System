/**
* This class is part of the Programming the Internet of Things
* project, and is available via the MIT License, which can be
* found in the LICENSE file at the top level of this repository.
* * Copyright (c) 2020 - 2025 by Andrew D. King
*/

package programmingtheiot.gda.connection.handlers;

import java.util.logging.Logger;

import org.eclipse.californium.core.CoapResource;
import org.eclipse.californium.core.coap.CoAP.ResponseCode;
import org.eclipse.californium.core.server.resources.CoapExchange;

import programmingtheiot.common.IActuatorDataListener;
import programmingtheiot.data.ActuatorData;
import programmingtheiot.data.DataUtil;

/**
* Observable CoAP resource handler that enables the Constrained Device Application (CDA)
* to observe and pull actuation commands from the Gateway Device Application (GDA).
*/
public class GetActuatorCommandResourceHandler extends CoapResource
implements IActuatorDataListener
{
// static
private static final Logger _Logger =
Logger.getLogger(GetActuatorCommandResourceHandler.class.getName());
// params
private ActuatorData actuatorData = null;
// constructors
/**
* Constructor. Initializes the resource and marks it as observable.
* * @param resourceName The name of the resource segment.
*/
public GetActuatorCommandResourceHandler(String resourceName)
{
super(resourceName);
// Initialisation d'une instance vide par défaut pour éviter les NullPointerException lors du premier GET
this.actuatorData = new ActuatorData();
this.actuatorData.setName(resourceName);

// Active le support de la spécification CoAP OBSERVE
super.setObservable(true);
}

// public methods
/**
* Callback triggered when an actuator command is generated inside the GDA (via DeviceDataManager).
* Updates the local cache and automatically triggers CoAP notifications to all observed subscribers.
*/
@Override
public boolean onActuatorDataUpdate(ActuatorData data)
{
if (data != null && this.actuatorData != null) {
this.actuatorData.updateData(data);
// Notifie immédiatement tous les clients CoAP abonnés (le CDA) que la ressource a changé
super.changed();
_Logger.fine("Actuator data updated for URI: " + super.getURI() + " -> Value: " + this.actuatorData.getValue());
return true;
}
return false;
}

/**
* Handles incoming CoAP GET and OBSERVE requests from clients.
*/
@Override
public void handleGET(CoapExchange context)
{
if (context == null) {
_Logger.warning("Incoming CoAP GET exchange context is null.");
return;
}

// Accepte formellement le traitement de la requête
context.accept();
_Logger.info("Handling GET/OBSERVE request for URI: " + super.getURI() + " from " + context.getSourceAddress());
// Sérialisation des données d'actionnement courantes en JSON
String jsonData = DataUtil.getInstance().actuatorDataToJson(this.actuatorData);

// Envoi de la réponse avec le code de succès CONTENT et la payload JSON
context.respond(ResponseCode.CONTENT, jsonData);
}
}