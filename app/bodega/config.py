from pydantic_settings import BaseSettings

from bodega.estado import Umbrales


class Settings(BaseSettings):
    """Se lee de variables de entorno (ver .env.example en la raíz del repo)."""

    database_url: str = "sqlite:///./bodega.db"
    csv_path: str = "./data/lecturas.csv"
    api_key: str = "cambia-esta-clave"
    zona_horaria: str = "America/Bogota"

    temp_min: float = 15.0
    temp_max: float = 25.0
    hum_min: float = 50.0
    hum_max: float = 65.0

    @property
    def umbrales(self) -> Umbrales:
        return Umbrales(self.temp_min, self.temp_max, self.hum_min, self.hum_max)
