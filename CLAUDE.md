# Instrucciones para agentes

Proyecto universitario: ESP32 + DHT22 → API FastAPI → PostgreSQL + CSV. Caso de uso: bodega de
café pergamino (umbrales en `docs/caso-de-uso.md`). Leer `README.md` primero.

## Reconstruir el entorno desde cero

```bash
cp .env.example .env            # y generar claves aleatorias para POSTGRES_PASSWORD y API_KEY
docker compose up -d --build
curl -s localhost:8000/health   # {"status":"ok","db":true}
python simulador/simular_esp32.py --cantidad 10 --intervalo 0.5 --picos   # todas deben dar 201
```

Verificar los datos: ver la sección "Verificar que los datos se guardan" del README.

## Reglas

- La BD **no** debe publicar puertos ni salir de la red `privada` (`internal: true`): es el requisito
  de "base de datos en subred privada". No añadir `ports:` al servicio `db`.
- El contrato con el firmware es `POST /api/lecturas` con `{dispositivo, temperatura, humedad}` y
  cabecera `X-API-Key`. Si cambia, actualizar a la vez `firmware/`, `simulador/` y los tests.
- Columnas del CSV (`bodega/csv_store.py:COLUMNAS`) y de la tabla son parte de la entrega: no
  renombrarlas sin avisar al equipo.
- Secretos solo en `.env` y `firmware/**/secrets.h` (ambos en `.gitignore`).
- Tests: `cd app && pytest` (SQLite, sin Docker). Lógica nueva → test primero.
- Documentación y mensajes en español.
- Windows: si Docker Desktop no arranca con un error de `*.sock ... .stale`, ver "Problemas
  frecuentes" en el README (renombrar `%LOCALAPPDATA%\Docker\run` y `%LOCALAPPDATA%\docker-secrets-engine`).
