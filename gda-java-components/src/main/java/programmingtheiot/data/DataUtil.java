package programmingtheiot.data;

import java.util.logging.Logger;

import com.google.gson.Gson;

public class DataUtil
{
// static
private static final Logger _Logger =
Logger.getLogger(DataUtil.class.getName());
// Le pattern du projet impose une initialisation directe et finale (Eager Initialization)
private static final DataUtil _Instance = new DataUtil();

public static final DataUtil getInstance()
{
return _Instance;
}
// constructors
// Le constructeur doit être privé pour verrouiller le pattern Singleton
private DataUtil()
{
super();
}
// public methods
// --- ACTUATOR DATA ---

public String actuatorDataToJson(ActuatorData data)
{
String jsonData = null;
if (data != null) {
Gson gson = new Gson();
jsonData = gson.toJson(data);
}
return jsonData;
}
public ActuatorData jsonToActuatorData(String jsonData)
{
ActuatorData data = null;
// Protection cruciale : si le JSON est vide ou nul, on évite le crash de Gson
if (jsonData != null && jsonData.trim().length() > 0) {
Gson gson = new Gson();
data = gson.fromJson(jsonData, ActuatorData.class);
}
return data;
}
// --- SENSOR DATA ---

public String sensorDataToJson(SensorData data)
{
String jsonData = null;
if (data != null) {
Gson gson = new Gson();
jsonData = gson.toJson(data);
}
return jsonData;
}
public SensorData jsonToSensorData(String jsonData)
{
SensorData data = null;
if (jsonData != null && jsonData.trim().length() > 0) {
Gson gson = new Gson();
data = gson.fromJson(jsonData, SensorData.class);
}
return data;
}
// --- SYSTEM PERFORMANCE DATA ---

public String systemPerformanceDataToJson(SystemPerformanceData data)
{
String jsonData = null;
if (data != null) {
Gson gson = new Gson();
jsonData = gson.toJson(data);
}
return jsonData;
}
public SystemPerformanceData jsonToSystemPerformanceData(String jsonData)
{
SystemPerformanceData data = null;
if (jsonData != null && jsonData.trim().length() > 0) {
Gson gson = new Gson();
data = gson.fromJson(jsonData, SystemPerformanceData.class);
}
return data;
}

// --- SYSTEM STATE DATA ---

public String systemStateDataToJson(SystemStateData data)
{
String jsonData = null;
if (data != null) {
Gson gson = new Gson();
jsonData = gson.toJson(data);
}
return jsonData;
}
public SystemStateData jsonToSystemStateData(String jsonData)
{
SystemStateData data = null;
if (jsonData != null && jsonData.trim().length() > 0) {
Gson gson = new Gson();
data = gson.fromJson(jsonData, SystemStateData.class);
}
return data;
}
}