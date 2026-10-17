import csv
import threading
from pathlib import Path

COLUMNAS = ["fecha", "dispositivo", "temperatura", "humedad", "estado", "motivos"]


class CsvStore:
    """Añade una fila por lectura; escribe la cabecera si el archivo es nuevo."""

    def __init__(self, ruta: str):
        self.ruta = Path(ruta)
        self._lock = threading.Lock()

    def agregar(self, fila: dict) -> None:
        with self._lock:
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
            nuevo = not self.ruta.exists() or self.ruta.stat().st_size == 0
            with self.ruta.open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=COLUMNAS)
                if nuevo:
                    writer.writeheader()
                writer.writerow({k: fila[k] for k in COLUMNAS})
