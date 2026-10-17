# Guía del ESP32 + DHT22

## Materiales

- ESP32 DevKit (ESP32-WROOM-32)
- Sensor DHT22 (AM2302). Si es el módulo de 3 pines, ya trae la resistencia pull-up.
- Cables dupont, cable USB de datos.

## Conexiones

| DHT22 | ESP32 |
|---|---|
| VCC (+) | 3V3 |
| DATA (out) | GPIO 4 |
| GND (−) | GND |

Si usas el sensor "pelado" de 4 pines: resistencia de **10 kΩ entre DATA y 3V3**; el pin 3 queda libre.

## Software

1. **Arduino IDE 2.x**.
2. Placas: *Archivo → Preferencias → URLs adicionales*:
   `https://espressif.github.io/arduino-esp32/package_esp32_index.json`,
   luego *Gestor de placas* → instalar **esp32 (Espressif)**. Placa: **ESP32 Dev Module**.
3. Librerías (*Gestor de librerías*): **DHT sensor library** (Adafruit), que pide también
   **Adafruit Unified Sensor**.
4. Windows: si no aparece el puerto COM, instala el driver CP210x o CH340 según tu placa.

## Configurar y subir

1. Abre `firmware/esp32_bodega/esp32_bodega.ino`.
2. Copia `secrets.example.h` como `secrets.h` (misma carpeta; no se sube a git) y rellena:
   - `WIFI_SSID`, `WIFI_PASSWORD`: red de **2,4 GHz** (el ESP32 no ve redes de 5 GHz).
   - `SERVER_URL`: `http://<IP-de-la-PC-con-docker>:8000/api/lecturas`
     (en la parte 2: `http://<IP-elástica>/api/lecturas`).
   - `API_KEY`: la misma que `API_KEY` del `.env` del servidor.
3. Sube el sketch y abre el **Monitor serie a 115200**. Debes ver algo como:

```
Wi-Fi OK, IP 192.168.1.50, RSSI -58 dBm
POST {"dispositivo":"esp32-bodega-1","temperatura":22.4,"humedad":61.0} -> 201 {"id":15,...,"estado":"OK",...}
```

El LED integrado parpadea en cada envío correcto. Si pierde el Wi-Fi, se reconecta solo en el siguiente ciclo.

## Ajustes en el código

- `DHT_TIPO`: `DHT22` (o `DHT11`).
- `DHT_PIN`: GPIO del pin DATA.
- `INTERVALO_MS`: cada cuánto se envía (mínimo 2000 para el DHT22).
- `DISPOSITIVO`: nombre que aparece en la base de datos (útil si hay varios ESP32).

## Protocolo

HTTP/1.1 `POST /api/lecturas`, `Content-Type: application/json`, cabecera `X-API-Key`.
Respuestas: `201` guardado · `401` API key incorrecta · `422` datos fuera de rango.
