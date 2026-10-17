# Práctica 1 — Servidor web para un proyecto IoT

**Bodega de café pergamino:** un ESP32 con sensor DHT22 mide temperatura y humedad y las
envía por HTTP a una aplicación web (FastAPI). La aplicación clasifica cada lectura como
**OK** o **ALERTA** y la guarda en **PostgreSQL** y en un archivo **CSV**.

> Especialización en IA — Inteligencia Artificial aplicada a Internet de las Cosas.
> Caso de uso completo: [docs/caso-de-uso.md](docs/caso-de-uso.md)

| Variable | OK | ALERTA |
|---|---|---|
| Temperatura | 15 – 25 °C | fuera de ese rango |
| Humedad relativa | 50 – 65 % | > 65 % (riesgo de moho) o < 50 % (grano se reseca) |

---

## Arquitectura

```
                    Wi-Fi / Internet
  ┌──────────┐   HTTP POST /api/lecturas    ┌─────────────────────── Docker ───────────────────────┐
  │  ESP32   │   JSON + cabecera X-API-Key  │  red "publica"              red "privada" (internal) │
  │ + DHT22  │ ───────────────────────────► │  ┌──────────────┐          ┌──────────────────┐      │
  └──────────┘          puerto 8000         │  │ web (FastAPI)│ ───────► │ db (PostgreSQL)  │      │
                                            │  │  tablero +API│          │ sin puertos fuera│      │
  ┌──────────┐   http://<ip>:8000           │  └──────┬───────┘          └──────────────────┘      │
  │Navegador │ ───────────────────────────► │         └─► ./data/lecturas.csv (volumen)            │
  └──────────┘                              └──────────────────────────────────────────────────────┘
```

- **web**: la única pieza expuesta (puerto 8000). Recibe lecturas, sirve el tablero y la API.
- **db**: PostgreSQL 16 en una red `internal`: no publica puertos, no tiene salida a internet
  y solo el contenedor `web` llega a ella. Es el equivalente local de la **subred privada** de AWS.
- **CSV**: `./data/lecturas.csv` en tu PC (montado como volumen).

La parte 2 (AWS: subred pública/privada, IP elástica, grupos de seguridad) reutiliza esta misma
imagen; ver [docs/aws.md](docs/aws.md).

## Estructura del repo

```
app/                  Aplicación FastAPI
  bodega/main.py        endpoints (POST/GET lecturas, CSV, health, tablero)
  bodega/estado.py      regla OK/ALERTA con los umbrales
  bodega/db.py          modelo de la tabla "lecturas" (SQLAlchemy)
  bodega/csv_store.py   escritura del CSV
  bodega/static/        tablero web (HTML + Chart.js)
  tests/                pruebas (pytest)
  Dockerfile
firmware/esp32_bodega/ Código Arduino del ESP32 (+ secrets.example.h)
simulador/            Script que imita al ESP32 (para probar sin hardware)
docs/                 Caso de uso, guía del ESP32, guía de AWS
data/                 Aquí aparece lecturas.csv (no se sube a git)
docker-compose.yml    Stack local: web + db con red privada
.env.example          Plantilla de configuración (copiar a .env)
CLAUDE.md             Instrucciones para agentes de IA que trabajen en el repo
```

## Puesta en marcha (local)

**Requisito único:** [Docker Desktop](https://www.docker.com/products/docker-desktop/)
(Windows/Mac) o Docker Engine + plugin compose (Linux/Ubuntu/WSL).

```bash
git clone https://github.com/MiguelDiuza/Pr-ctica-1-Servidor-web.git
cd Pr-ctica-1-Servidor-web
cp .env.example .env        # en PowerShell: Copy-Item .env.example .env
```

Edita `.env` y cambia `POSTGRES_PASSWORD` y `API_KEY`. Luego:

```bash
docker compose up -d --build
```

Abre **http://localhost:8000** → tablero. La API documentada está en **http://localhost:8000/docs**.

### Probar sin ESP32 (simulador)

```bash
python simulador/simular_esp32.py --cantidad 30 --intervalo 1 --picos
```

Lee la `API_KEY` de `.env` automáticamente. `--picos` provoca de vez en cuando humedad > 65 %
para ver alertas. Sin `--cantidad` envía sin parar cada 10 s, como el ESP32 real.

### Conectar el ESP32 real

Resumen (guía completa con cableado en [docs/esp32.md](docs/esp32.md)):

1. Averigua la IP de tu PC en la red Wi-Fi (`ipconfig` en Windows, `ip a` en Linux).
2. Copia `firmware/esp32_bodega/secrets.example.h` → `secrets.h` y pon Wi-Fi (2,4 GHz),
   `SERVER_URL = http://<IP-de-tu-PC>:8000/api/lecturas` y la misma `API_KEY` del `.env`.
3. Sube el sketch con Arduino IDE y abre el monitor serie (115200): debe mostrar `-> 201`.

Si el ESP32 no llega al servidor, prueba desde el celular (misma Wi-Fi) abrir
`http://<IP-de-tu-PC>:8000`. Si no carga, abre el puerto en el firewall de Windows
(PowerShell **como administrador**):

```powershell
New-NetFirewallRule -DisplayName "Bodega cafe 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Any
```

## Verificar que los datos se guardan

Criterio de evaluación: *los datos deben verificarse en el CSV y en la base de datos.*

```bash
# Base de datos (dentro del contenedor, porque la BD no está expuesta)
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT * FROM lecturas ORDER BY id DESC LIMIT 10;"'

# Conteo por estado
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT estado, count(*) FROM lecturas GROUP BY estado;"'

# CSV
cat data/lecturas.csv                     # o abrirlo en Excel
curl http://localhost:8000/api/lecturas.csv
```

## API

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/lecturas` | Registra una lectura. Cabecera `X-API-Key`. Cuerpo: `{"dispositivo": "esp32-bodega-1", "temperatura": 21.3, "humedad": 58.2}` → `201` con `estado` y `motivos` |
| GET | `/api/lecturas?limite=50` | Últimas lecturas (más reciente primero) |
| GET | `/api/lecturas.csv` | Descarga el CSV |
| GET | `/api/umbrales` | Umbrales configurados |
| GET | `/health` | Estado de la app y conexión a la BD |
| GET | `/` | Tablero web |

La fecha la pone el servidor (zona `America/Bogota`), así el ESP32 no necesita reloj.

## Comandos útiles

```bash
docker compose logs -f web        # ver las lecturas que llegan
docker compose ps                 # estado de los contenedores
docker compose down               # parar (los datos se conservan)
docker compose down -v            # parar y BORRAR la base de datos
docker compose up -d --build      # reconstruir tras cambiar código
```

## Pruebas

```bash
cd app
python -m venv ../.venv && ../.venv/Scripts/activate     # Linux/Mac: source ../.venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

Las pruebas usan SQLite y un CSV temporal; no necesitan Docker.

## Problemas frecuentes

| Síntoma | Solución |
|---|---|
| Docker Desktop: *"rename ... .sock ... .sock.stale: The file cannot be accessed by the system"* | Quedaron sockets viejos de una ejecución anterior. Cierra Docker Desktop y renombra las carpetas `%LOCALAPPDATA%\Docker\run` y `%LOCALAPPDATA%\docker-secrets-engine` (p. ej. a `run.old`); Docker las vuelve a crear al arrancar. |
| `POSTGRES_PASSWORD` / `API_KEY` *required* al hacer `up` | Falta el archivo `.env` (copia `.env.example`). |
| El puerto 8000 está ocupado | Cambia `WEB_PORT` en `.env` (y la URL del ESP32). |
| El ESP32 da `-1` o `connection refused` | Misma red Wi-Fi de 2,4 GHz, IP correcta de la PC, firewall (ver arriba). Algunas redes de universidad aíslan clientes: usa el hotspot del celular. |
| El ESP32 da `401` | La `API_KEY` de `secrets.h` no coincide con la de `.env`. |
| `Error leyendo el DHT22` | Revisa cableado: VCC 3V3, GND, DATA a GPIO4 con resistencia de 10 kΩ a 3V3 (los módulos de 3 pines ya la traen). |

## Estado del proyecto

- [x] Parte 1: servidor web local (Docker), CSV + PostgreSQL, tablero, firmware ESP32, simulador
- [ ] Parte 2: despliegue en AWS (VPC, subred pública/privada, IP elástica, grupos de seguridad)
- [ ] Presentación
