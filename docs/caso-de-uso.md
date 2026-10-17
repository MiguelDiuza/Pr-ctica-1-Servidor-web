# Caso de uso: bodega de café pergamino

## Contexto

Una cooperativa cafetera almacena **café pergamino seco** antes de venderlo a exportadores.
Si la humedad del ambiente sube, el grano la absorbe, aparece **moho** y el café pierde
**puntaje de taza** (sabores a tierra, a guardado) y, con eso, su precio.

## Qué hace el sistema

- Un ESP32 con sensor DHT22 instalado en la bodega mide temperatura y humedad relativa
  cada 10 segundos y las envía por Wi-Fi (HTTP) al servidor.
- El servidor clasifica cada lectura como **OK** o **ALERTA** y la guarda en una base de
  datos PostgreSQL y en un archivo CSV.
- Un tablero web muestra el estado actual, la gráfica y el historial.
- El registro histórico sirve como **evidencia de buenas condiciones de almacenamiento**
  ante compradores y certificadoras.

## Umbrales (aproximados)

| Variable | OK | ALERTA |
|---|---|---|
| Temperatura | 15 – 25 °C | fuera de ese rango |
| Humedad relativa | 50 – 65 % | > 65 % (riesgo de moho) |

Además marcamos ALERTA si la humedad baja de 50 % (el grano se reseca y pierde peso).
Los valores se cambian en `.env` (`TEMP_MIN`, `TEMP_MAX`, `HUM_MIN`, `HUM_MAX`) sin tocar código.

## Qué se guarda por lectura

| Campo | Ejemplo |
|---|---|
| fecha | `2026-10-17T11:14:28-05:00` (la pone el servidor, hora de Colombia) |
| dispositivo | `esp32-bodega-1` |
| temperatura | `21.2` (°C) |
| humedad | `57.8` (%) |
| estado | `OK` / `ALERTA` |
| motivos | `humedad alta (riesgo de moho)` |
