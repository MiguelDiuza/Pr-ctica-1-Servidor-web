/*
 * Bodega de café pergamino — ESP32 + DHT22
 *
 * Lee temperatura y humedad cada INTERVALO_MS y las envía por HTTP POST (JSON)
 * a la API: POST http://<servidor>:8000/api/lecturas  con cabecera X-API-Key.
 *
 * Librerías (Arduino IDE > Gestor de librerías):
 *   - "DHT sensor library" de Adafruit (instala también "Adafruit Unified Sensor")
 * Placa: "ESP32 Dev Module" (paquete esp32 de Espressif).
 *
 * Configuración: copia secrets.example.h a secrets.h y rellena Wi-Fi, servidor y API key.
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include "secrets.h"

#define DHT_PIN 4            // GPIO donde va el pin DATA del DHT22
#define DHT_TIPO DHT22       // cambia a DHT11 si usas ese sensor
#define LED_PIN 2            // LED integrado: parpadea en cada envío correcto

const unsigned long INTERVALO_MS = 10000;  // el DHT22 necesita >= 2 s entre lecturas
const char *DISPOSITIVO = "esp32-bodega-1";

DHT dht(DHT_PIN, DHT_TIPO);
unsigned long ultimoEnvio = 0;

void conectarWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;
  Serial.printf("Conectando a %s", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  unsigned long inicio = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - inicio < 20000) {
    delay(500);
    Serial.print(".");
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\nWi-Fi OK, IP %s, RSSI %d dBm\n", WiFi.localIP().toString().c_str(), WiFi.RSSI());
  } else {
    Serial.println("\nNo se pudo conectar; se reintenta en el siguiente ciclo");
  }
}

bool enviarLectura(float temperatura, float humedad) {
  HTTPClient http;
  http.begin(SERVER_URL);
  http.setTimeout(5000);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);

  char cuerpo[128];
  snprintf(cuerpo, sizeof(cuerpo),
           "{\"dispositivo\":\"%s\",\"temperatura\":%.1f,\"humedad\":%.1f}",
           DISPOSITIVO, temperatura, humedad);

  int codigo = http.POST(cuerpo);
  String respuesta = http.getString();
  http.end();

  Serial.printf("POST %s -> %d %s\n", cuerpo, codigo, respuesta.c_str());
  return codigo == 201;
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  dht.begin();
  conectarWiFi();
}

void loop() {
  if (millis() - ultimoEnvio < INTERVALO_MS) return;
  ultimoEnvio = millis();

  conectarWiFi();
  if (WiFi.status() != WL_CONNECTED) return;

  float humedad = dht.readHumidity();
  float temperatura = dht.readTemperature();
  if (isnan(humedad) || isnan(temperatura)) {
    Serial.println("Error leyendo el DHT22 (revisa cableado y resistencia pull-up)");
    return;
  }

  if (enviarLectura(temperatura, humedad)) {
    digitalWrite(LED_PIN, HIGH);
    delay(100);
    digitalWrite(LED_PIN, LOW);
  }
}
