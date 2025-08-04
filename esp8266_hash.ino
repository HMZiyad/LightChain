#include <WiFi.h>
#include <HTTPClient.h>
#include "mbedtls/sha256.h"

// WiFi credentials
const char* ssid = "AUSTSat";
const char* password = "@austsat456";

// Flask server endpoint
const char* serverUrl = "http://192.168.1.2:5000/join";

// Device identity
String device_id = "esp32-DEVICE-001";

// Function to calculate SHA256 firmware hash using mbedTLS
String getFirmwareHash() {
  uint32_t sketchSize = ESP.getSketchSize();
  uint8_t buffer[512];
  mbedtls_sha256_context ctx;
  uint8_t hash[32];

  mbedtls_sha256_init(&ctx);
  mbedtls_sha256_starts_ret(&ctx, 0); // 0 for SHA-256

  for (uint32_t offset = 0; offset < sketchSize; offset += sizeof(buffer)) {
    uint32_t len = min(sizeof(buffer), sketchSize - offset);
    memcpy_P(buffer, (const void*)(ESP.getSketchStart() + offset), len);
    mbedtls_sha256_update_ret(&ctx, buffer, len);
  }

  mbedtls_sha256_finish_ret(&ctx, hash);
  mbedtls_sha256_free(&ctx);

  String hashStr = "";
  for (int i = 0; i < 32; ++i) {
    if (hash[i] < 0x10) hashStr += "0";
    hashStr += String(hash[i], HEX);
  }
  return hashStr;
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  Serial.print("🔌 Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n✅ Connected to WiFi");

  String firmware_hash = getFirmwareHash();
  Serial.println("🔍 Firmware SHA256 Hash: " + firmware_hash);

  HTTPClient http;
  http.begin(serverUrl);
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
