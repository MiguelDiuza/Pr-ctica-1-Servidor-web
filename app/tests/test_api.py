import csv

import pytest
from fastapi.testclient import TestClient

from bodega.config import Settings
from bodega.main import create_app

CLAVE = "clave-de-prueba"


@pytest.fixture
def entorno(tmp_path):
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        csv_path=str(tmp_path / "datos" / "lecturas.csv"),
        api_key=CLAVE,
    )
    with TestClient(create_app(settings)) as client:
        yield client, settings


def enviar(client, temperatura=21.5, humedad=58.0, clave=CLAVE):
    return client.post(
        "/api/lecturas",
        json={"dispositivo": "esp32-test", "temperatura": temperatura, "humedad": humedad},
        headers={"X-API-Key": clave},
    )


def test_guarda_lectura_ok_en_bd_y_csv(entorno):
    client, settings = entorno
    r = enviar(client)
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["estado"] == "OK"
    assert cuerpo["temperatura"] == 21.5

    # Base de datos: aparece en el listado
    lista = client.get("/api/lecturas").json()
    assert [l["id"] for l in lista] == [cuerpo["id"]]

    # CSV: cabecera + una fila con fecha, temperatura, humedad y estado
    with open(settings.csv_path, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    assert len(filas) == 1
    assert filas[0]["estado"] == "OK"
    assert float(filas[0]["humedad"]) == 58.0
    assert filas[0]["fecha"].endswith("-05:00")  # hora de Colombia, no UTC


def test_humedad_alta_queda_en_alerta(entorno):
    client, _ = entorno
    cuerpo = enviar(client, humedad=72).json()
    assert cuerpo["estado"] == "ALERTA"
    assert "humedad alta (riesgo de moho)" in cuerpo["motivos"]


def test_sin_api_key_es_rechazada(entorno):
    client, settings = entorno
    assert enviar(client, clave="otra").status_code == 401
    assert client.get("/api/lecturas").json() == []


def test_valores_imposibles_dan_422(entorno):
    client, _ = entorno
    assert enviar(client, humedad=120).status_code == 422


def test_listado_mas_reciente_primero_y_limite(entorno):
    client, _ = entorno
    ids = [enviar(client, temperatura=20 + i).json()["id"] for i in range(3)]
    lista = client.get("/api/lecturas", params={"limite": 2}).json()
    assert [l["id"] for l in lista] == [ids[2], ids[1]]


def test_descarga_csv(entorno):
    client, _ = entorno
    enviar(client)
    r = client.get("/api/lecturas.csv")
    assert r.status_code == 200
    assert r.text.splitlines()[0] == "fecha,dispositivo,temperatura,humedad,estado,motivos"


def test_health(entorno):
    client, _ = entorno
    assert client.get("/health").json() == {"status": "ok", "db": True}
