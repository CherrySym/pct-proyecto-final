"""Catálogo: cartas, ediciones, ejemplares e insignias."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .comunes import Especie, Estacion, Rareza


@dataclass
class Carta:
    """Carta del catálogo. Lo que tiene un jugador es un Ejemplar de ella."""
    id_carta: int
    nombre: str
    especie: Especie
    rareza: Rareza
    estacion: Estacion
    intercambiable: bool = True


class Edicion:
    """Colección de un año. Completarla primero da la insignia.

    Es una clase común (no dataclass) porque tiene una invariante que se
    revisa en el constructor: no puede haber dos cartas con el mismo id_carta.
    """

    def __init__(self, nombre: str, cartas: tuple):
        ids = [c.id_carta for c in cartas]
        if len(ids) != len(set(ids)):
            raise ValueError("Una edición no puede repetir id_carta")
        self.nombre = nombre
        self.cartas = tuple(cartas)

    def cartas_de(self, rareza: Rareza) -> tuple:
        return tuple(c for c in self.cartas if c.rareza == rareza)


@dataclass
class Ejemplar:
    id_ejemplar: int
    carta: Carta


@dataclass
class Insignia:
    fecha_obtenida: date
    edicion: Edicion
