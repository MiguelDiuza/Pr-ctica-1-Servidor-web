"""Simula el ESP32 de la bodega: envía lecturas a la API igual que el firmware.

Solo usa la biblioteca estándar de Python.

    python simulador/simular_esp32.py --url http://localhost:8000 --api-key <API_KEY>
    python simulador/simular_esp32.py --cantidad 20 --intervalo 1 --picos

Sin --api-key intenta leer API_KEY del archivo .env de la raíz del repo.
"""

import argparse
import json
import random
import time
import urllib.error
import urllib.request
from pathlib import Path


def api_key_de_env() -> str | None:
    env = Path(__file__).resolve().parent.parent / ".env"
    if env.exists():
        for linea in env.read_text(encoding="utf-8").splitlines():
            if linea.startswith("API_KEY="):
                return linea.split("=", 1)[1].strip()
    return None


def enviar(url: str, api_key: str, dispositivo: str, temp: float, hum: float) -> tuple[int, dict]:
    cuerpo = json.dumps({"dispositivo": dispositivo, "temperatura": round(temp, 1), "humedad": round(hum, 1)})
    req = urllib.request.Request(
        url.rstrip("/") + "/api/lecturas",
        data=cuerpo.encode(),
        headers={"Content-Type": "application/json", "X-API-Key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, {"detail": e.read().decode()}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", default="http://localhost:8000")
    p.add_argument("--api-key", default=None)
    p.add_argument("--dispositivo", default="esp32-simulado")
    p.add_argument("--intervalo", type=float, default=10, help="segundos entre lecturas")
    p.add_argument("--cantidad", type=int, default=0, help="0 = sin fin")
    p.add_argument("--picos", action="store_true", help="provoca de vez en cuando humedad > 65 %% (ALERTA)")
    args = p.parse_args()

    api_key = args.api_key or api_key_de_env()
    if not api_key:
        p.error("falta --api-key (o API_KEY en .env)")

    temp, hum = 21.0, 58.0
    n = 0
    while args.cantidad == 0 or n < args.cantidad:
        # Paseo aleatorio suave alrededor de condiciones normales de bodega
        temp = min(max(temp + random.uniform(-0.3, 0.3), 17), 27)
        hum = min(max(hum + random.uniform(-0.8, 0.8), 52), 63)
        hum_enviada = hum + (random.uniform(4, 10) if args.picos and random.random() < 0.2 else 0)

        codigo, resp = enviar(args.url, api_key, args.dispositivo, temp, hum_enviada)
        estado = resp.get("estado", resp.get("detail"))
        print(f"{codigo} {temp:5.1f} C {hum_enviada:5.1f} % -> {estado}", flush=True)
        n += 1
        if args.cantidad == 0 or n < args.cantidad:
            time.sleep(args.intervalo)


if __name__ == "__main__":
    main()
