#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <bearssl/bearssl.h>

// WiFi credentials
const char* ssid = "Ziyad";
const char* password = "hawlader123";

// Flask server endpoint
const char* serverUrl = "http://192.168.1.102:5000/join";

// Device identity
String device_id = "esp8266-DEVICE-003";

// Function to calculate SHA256 firmware hash using BearSSL
String getFirmwareHash() {
  uint32_t sketchSize = ESP.getSketchSize();
  uint8_t buffer[512];
  br_sha256_context ctx;
  br_sha256_init(&ctx);

  for (uint32_t offset = 0; offset < sketchSize; offset += sizeof(buffer)) {
    uint32_t len = min(sizeof(buffer), sketchSize - offset);
    ESP.flashRead(ESP.getSketchSize() + offset, (uint32_t*)buffer, len);
    br_sha256_update(&ctx, buffer, len);
  }

  unsigned char out[32];
  br_sha256_out(&ctx, out);

  String hash = "";
  for (int i = 0; i < 32; ++i) {
    if (out[i] < 0x10) hash += "0";
    hash += String(out[i], HEX);
  }
  return hash;
}


void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  Serial.print("🔌 Connecting WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\\n✅ Connected to WiFi");

  String firmware_hash = getFirmwareHash();
  Serial.println("🔍 Firmware SHA256 Hash: " + firmware_hash);

  WiFiClient client;
  HTTPClient http;
  http.begin(client, serverUrl);
  http.addHeader("Content-Type", "application/json");

  String json = "{\"device_id\": \"" + device_id + "\", \"firmware_hash\": \"" + firmware_hash + "\"}";
  Serial.println("📤 Sending: " + json);

  int httpCode = http.POST(json);
  String response = http.getString();

  Serial.println("📥 HTTP Code: " + String(httpCode));
  Serial.println("📥 Server Response: " + response);

  http.end();
}

void loop() {
  // No loop needed for one-time registration
}
