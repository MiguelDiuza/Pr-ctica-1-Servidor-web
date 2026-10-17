"""API de monitoreo de la bodega de café pergamino.

El ESP32 hace POST /api/lecturas con la cabecera X-API-Key; cada lectura se
clasifica (OK/ALERTA) y se guarda en PostgreSQL y en un CSV.
"""

import logging
import secrets
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from bodega.config import Settings
from bodega.csv_store import COLUMNAS, CsvStore
from bodega.db import Base, Lectura, crear_engine
from bodega.estado import clasificar

log = logging.getLogger("bodega")
STATIC = Path(__file__).parent / "static"


class LecturaEntrada(BaseModel):
    dispositivo: str = Field("esp32", max_length=64)
    temperatura: float = Field(ge=-40, le=80)  # rango de medida del DHT22
    humedad: float = Field(ge=0, le=100)


class LecturaSalida(BaseModel):
    id: int
    fecha: datetime
    dispositivo: str
    temperatura: float
    humedad: float
    estado: str
    motivos: list[str]


def a_salida(l: Lectura) -> LecturaSalida:
    return LecturaSalida(
        id=l.id,
        fecha=l.fecha,
        dispositivo=l.dispositivo,
        temperatura=l.temperatura,
        humedad=l.humedad,
        estado=l.estado,
        motivos=l.motivos.split("; ") if l.motivos else [],
    )


def esperar_bd(engine, intentos: int = 30) -> None:
    """La BD puede tardar en aceptar conexiones al arrancar el stack."""
    for i in range(intentos):
        try:
            Base.metadata.create_all(engine)
            return
        except OperationalError:
            log.warning("BD no disponible, reintento %d/%d", i + 1, intentos)
            time.sleep(2)
    raise RuntimeError("No se pudo conectar a la base de datos")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    engine = crear_engine(settings.database_url)
    csv_store = CsvStore(settings.csv_path)
    tz = ZoneInfo(settings.zona_horaria)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        esperar_bd(engine)
        yield
        engine.dispose()

    app = FastAPI(title="Bodega de café — monitoreo IoT", lifespan=lifespan)

    def sesion():
        with Session(engine) as s:
            yield s

    def verificar_clave(x_api_key: str = Header(default="")):
        if not secrets.compare_digest(x_api_key, settings.api_key):
            raise HTTPException(status_code=401, detail="API key inválida")

    @app.post("/api/lecturas", status_code=201, response_model=LecturaSalida,
              dependencies=[Depends(verificar_clave)])
    def crear_lectura(datos: LecturaEntrada, request: Request, s: Session = Depends(sesion)):
        estado, motivos = clasificar(datos.temperatura, datos.humedad, settings.umbrales)
        ahora = datetime.now(tz).replace(microsecond=0)
        lectura = Lectura(
            fecha=ahora,
            dispositivo=datos.dispositivo,
            temperatura=round(datos.temperatura, 1),
            humedad=round(datos.humedad, 1),
            estado=estado,
            motivos="; ".join(motivos),
        )
        s.add(lectura)
        s.commit()
        s.refresh(lectura)
        csv_store.agregar({
            "fecha": ahora.isoformat(),  # la BD devuelve UTC; el CSV va en hora local
            "dispositivo": lectura.dispositivo,
            "temperatura": lectura.temperatura,
            "humedad": lectura.humedad,
            "estado": lectura.estado,
            "motivos": lectura.motivos,
        })
        log.info("Lectura %s desde %s: %.1f °C %.1f %% -> %s", lectura.id,
                 request.client.host if request.client else "?",
                 lectura.temperatura, lectura.humedad, estado)
        return a_salida(lectura)

    @app.get("/api/lecturas", response_model=list[LecturaSalida])
    def listar(limite: int = Query(50, ge=1, le=1000), s: Session = Depends(sesion)):
        filas = s.scalars(select(Lectura).order_by(Lectura.id.desc()).limit(limite))
        return [a_salida(l) for l in filas]

    @app.get("/api/lecturas.csv")
    def descargar_csv():
        ruta = Path(settings.csv_path)
        if not ruta.exists():
            return PlainTextResponse(",".join(COLUMNAS) + "\n", media_type="text/csv")
        return FileResponse(ruta, media_type="text/csv", filename="lecturas.csv")

    @app.get("/api/umbrales")
    def umbrales():
        return settings.umbrales.__dict__

    @app.get("/health")
    def health(s: Session = Depends(sesion)):
        s.execute(text("SELECT 1"))
        return {"status": "ok", "db": True}

    @app.get("/", include_in_schema=False)
    def tablero():
        return FileResponse(STATIC / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
# Se arranca con: uvicorn --factory bodega.main:create_app
