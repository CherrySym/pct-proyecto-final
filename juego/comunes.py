"""Piezas comunes que no son entidades: el error del juego, las enumeraciones y el azar."""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Sequence, TypeVar

T = TypeVar("T")


# ---------------------------------------------------------------- error

class ErrorMercado(Exception):
    """Operación inválida. Cuando se lanza, el sistema queda como estaba."""


# ---------------------------------------------------------------- enumeraciones

class Rareza(Enum):
    COMUN = "Común"
    RARA = "Rara"
    EPICA = "Épica"
    LEGENDARIA = "Legendaria"
    MITICA = "Mítica"


class Especie(Enum):
    SELVA_TROPICAL = "Selva tropical"
    DESIERTO_Y_SUCULENTAS = "Desierto y suculentas"
    PLANTAS_CARNIVORAS = "Plantas carnívoras"
    FLORES_DE_PRIMAVERA = "Flores de primavera"
    HIERBAS_AROMATICAS = "Hierbas aromáticas"
    MONTE_URUGUAYO = "Monte uruguayo"


class Estacion(Enum):
    OTONO = "Otoño"
    INVIERNO = "Invierno"
    PRIMAVERA = "Primavera"
    VERANO = "Verano"


class TipoPublicacion(Enum):
    VENTA = "Venta"
    INTERCAMBIO = "Intercambio"


# ---------------------------------------------------------------- azar

class Azar(ABC):
    @abstractmethod
    def elegir(self, opciones: Sequence[T], pesos: Sequence[float]) -> T:
        """Elige una opción según los pesos."""


class AzarReal(Azar):
    """Azar con random. Con semilla fija es reproducible."""

    def __init__(self, semilla: Optional[int] = None):
        self._rng = random.Random(semilla)

    def elegir(self, opciones, pesos):
        return self._rng.choices(list(opciones), weights=list(pesos), k=1)[0]


class AzarFijo(Azar):
    """Para tests: devuelve la opción en la posición indicada, en orden."""

    def __init__(self, indices: Sequence[int]):
        self._indices = iter(indices)

    def elegir(self, opciones, pesos):
        try:
            return opciones[next(self._indices)]
        except StopIteration:
            raise ValueError("AzarFijo se quedó sin resultados") from None
