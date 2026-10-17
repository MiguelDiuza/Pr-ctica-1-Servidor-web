// Copia este archivo como secrets.h (no se sube a GitHub) y rellena tus datos.
#pragma once

#define WIFI_SSID "MiRedWiFi"          // el ESP32 solo soporta Wi-Fi de 2,4 GHz
#define WIFI_PASSWORD "clave-del-wifi"

// IP de la PC que ejecuta docker compose (ipconfig en Windows, en la misma red Wi-Fi)
// o la IP elástica de AWS en la segunda parte.
#define SERVER_URL "http://192.168.1.13:8000/api/lecturas"

// Debe ser igual a API_KEY del archivo .env del servidor
#define API_KEY "cambia-esta-api-key"
