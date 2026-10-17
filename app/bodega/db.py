from datetime import datetime

from sqlalchemy import DateTime, Float, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Lectura(Base):
    __tablename__ = "lecturas"

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    dispositivo: Mapped[str] = mapped_column(String(64))
    temperatura: Mapped[float] = mapped_column(Float)
    humedad: Mapped[float] = mapped_column(Float)
    estado: Mapped[str] = mapped_column(String(10))
    motivos: Mapped[str] = mapped_column(String(200), default="")  # separados por "; "


def crear_engine(url: str):
    return create_engine(url, pool_pre_ping=True)
