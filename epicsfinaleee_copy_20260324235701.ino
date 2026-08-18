#include <ESP8266WiFi.h>
#include <DHT.h>

// ===== WiFi Credentials =====
const char* WIFI_SSID = "krupa";
const char* WIFI_PASS = "";

// ===== ThingSpeak Config =====
const char* TS_SERVER = "api.thingspeak.com";
String TS_API_KEY = "6XJ3FC1MV437RCIV";

// ===== DHT Sensor =====
#define DHT_PIN D4
#define DHT_MODEL DHT11
DHT dhtSensor(DHT_PIN, DHT_MODEL);

// ===== Hardware Pins =====
#define PIN_SOIL   A0
#define PIN_RAIN   D5
#define PIN_LIGHT  D6
#define PIN_RELAY  D1

WiFiClient wifiClient;

// ===== Function: Connect WiFi =====
void connectWiFi() {
  Serial.print("Connecting to WiFi");

  WiFi.begin(WIFI_SSID, WIFI_PASS);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConnected to WiFi");
}

// ===== Function: Read Sensors =====
void readSensors(int &soilPercent, float &temp, float &hum, int &rain, int &light) {
  
  int rawSoil = analogRead(PIN_SOIL);
  soilPercent = map(rawSoil, 1023, 300, 0, 100);

  temp = dhtSensor.readTemperature();
  hum  = dhtSensor.readHumidity();

  rain  = digitalRead(PIN_RAIN);   // 0 = rain
  light = digitalRead(PIN_LIGHT);  // 1 = bright

  Serial.println("----- Sensor Data -----");
  Serial.printf("Soil Moisture: %d%%\n", soilPercent);
  Serial.printf("Temperature: %.2f°C\n", temp);
  Serial.printf("Humidity: %.2f%%\n", hum);
  Serial.printf("Rain Status: %d\n", rain);
  Serial.printf("Light Status: %d\n", light);
}

// ===== Function: ML Logic =====
int calculateIrrigation(int soil, float temp, int rain, int light) {

  if (rain == 0) return 0;

  if (soil < 30) {
    if (temp > 30 && light == 1) return 8;
    return 5;
  }

  return 0;
}

// ===== Function: Control Pump =====
void controlPump(int durationSec) {

  if (durationSec <= 0) return;

  Serial.println("Pump ON");
  digitalWrite(PIN_RELAY, HIGH);

  delay(durationSec * 1000); // demo timing

  digitalWrite(PIN_RELAY, LOW);
  Serial.println("Pump OFF");
}

// ===== Function: Send Data to ThingSpeak =====
void sendToThingSpeak(int soil, float temp, float hum, int rain, int light, int irrigation) {

  if (wifiClient.connect(TS_SERVER, 80)) {

    String request = "/update?api_key=" + TS_API_KEY;
    request += "&field1=" + String(soil);
    request += "&field2=" + String(temp);
    request += "&field3=" + String(hum);
    request += "&field4=" + String(rain);
    request += "&field5=" + String(light);
    request += "&field6=" + String(irrigation);

    wifiClient.print(String("GET ") + request + " HTTP/1.1\r\n" +
                     "Host: " + TS_SERVER + "\r\n" +
                     "Connection: close\r\n\r\n");

    Serial.println("Uploaded to ThingSpeak");
  }
}

// ===== Setup =====
void setup() {
  Serial.begin(115200);

  pinMode(PIN_RAIN, INPUT);
  pinMode(PIN_LIGHT, INPUT);
  pinMode(PIN_RELAY, OUTPUT);

  digitalWrite(PIN_RELAY, LOW);

  dhtSensor.begin();

  connectWiFi();
}

// ===== Loop =====
void loop() {

  int soil = 0, rain = 0, light = 0;
  float temperature = 0, humidity = 0;

  readSensors(soil, temperature, humidity, rain, light);

  int irrigationTime = calculateIrrigation(soil, temperature, rain, light);

  controlPump(irrigationTime);

  sendToThingSpeak(soil, temperature, humidity, rain, light, irrigationTime);

  delay(15000); // ThingSpeak limit
}
