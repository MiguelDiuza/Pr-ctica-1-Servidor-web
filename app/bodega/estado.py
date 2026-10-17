"""Clasifica una lectura de la bodega de café pergamino como OK o ALERTA."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Umbrales:
    temp_min: float = 15.0
    temp_max: float = 25.0
    hum_min: float = 50.0
    hum_max: float = 65.0  # por encima, el pergamino absorbe humedad y aparece moho


def clasificar(temperatura: float, humedad: float, u: Umbrales) -> tuple[str, list[str]]:
    """Devuelve ("OK" | "ALERTA", motivos). Los bordes del rango cuentan como OK."""
    motivos = []
    if temperatura < u.temp_min:
        motivos.append("temperatura baja")
    elif temperatura > u.temp_max:
        motivos.append("temperatura alta")
    if humedad > u.hum_max:
        motivos.append("humedad alta (riesgo de moho)")
    elif humedad < u.hum_min:
        motivos.append("humedad baja (grano se reseca)")
    return ("ALERTA" if motivos else "OK"), motivos
