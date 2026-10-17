import pytest

from bodega.estado import Umbrales, clasificar

U = Umbrales()  # 15-25 °C, 50-65 % HR


@pytest.mark.parametrize(
    "temp, hum",
    [(20, 60), (15, 50), (25, 65)],  # dentro y en los bordes
)
def test_dentro_de_rango_es_ok(temp, hum):
    estado, motivos = clasificar(temp, hum, U)
    assert estado == "OK"
    assert motivos == []


def test_humedad_alta_es_alerta_por_moho():
    estado, motivos = clasificar(20, 70, U)
    assert estado == "ALERTA"
    assert motivos == ["humedad alta (riesgo de moho)"]


def test_humedad_baja_es_alerta():
    estado, motivos = clasificar(20, 45, U)
    assert estado == "ALERTA"
    assert motivos == ["humedad baja (grano se reseca)"]


@pytest.mark.parametrize(
    "temp, motivo",
    [(14.9, "temperatura baja"), (25.1, "temperatura alta")],
)
def test_temperatura_fuera_de_rango_es_alerta(temp, motivo):
    estado, motivos = clasificar(temp, 60, U)
    assert estado == "ALERTA"
    assert motivos == [motivo]


def test_varios_motivos_a_la_vez():
    estado, motivos = clasificar(30, 80, U)
    assert estado == "ALERTA"
    assert motivos == ["temperatura alta", "humedad alta (riesgo de moho)"]
