"""Datos inmutables que describen operaciones: venta, intercambio y registro del historial."""
from __future__ import annotations

from dataclasses import dataclass

from .catalogo import Ejemplar
from .jugador import Jugador


@dataclass(frozen=True)
class Venta:
    vendedor: Jugador
    ejemplar: Ejemplar
    precio: int


@dataclass(frozen=True)
class Intercambio:
    emisor: Jugador
    receptor: Jugador
    brinda: tuple  # ejemplares que da el emisor
    recibe: tuple  # ejemplares que da el receptor


@dataclass(frozen=True)
class Operacion:
    tipo: str
    datos: dict
    estado_previo: dict
