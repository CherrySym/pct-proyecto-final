"""Operaciones entre jugadores (venta, intercambio) y el registro del historial.

Transaccion es abstracta: Venta e Intercambio saben validarse y aplicarse a su
manera (polimorfismo), así el Mercado las ejecuta sin preguntar "¿de qué tipo es?".
No conocen al Mercado: solo mueven polen y cartas entre los jugadores que tienen
adentro. El Mercado es quien las ejecuta, siempre dentro de `_ejecutar` (atómico).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from .catalogo import Ejemplar
from .comunes import ErrorMercado
from .jugador import Jugador
from . import reglas


class Transaccion(ABC):
    @abstractmethod
    def participantes(self) -> tuple:
        """Jugadores involucrados (el Mercado verifica que estén registrados)."""

    @abstractmethod
    def ejemplares(self) -> tuple:
        """Ejemplares que cambian de dueño (el Mercado los saca del foro)."""

    @abstractmethod
    def aplicar(self) -> None:
        """Valida sus reglas y después mueve polen y cartas.
        Llamar solo a través del Mercado, para que sea atómico y quede en el historial."""


@dataclass
class Venta(Transaccion):
    vendedor: Jugador
    comprador: Jugador
    ejemplar: Ejemplar
    precio: int

    def participantes(self) -> tuple:
        return (self.vendedor, self.comprador)

    def ejemplares(self) -> tuple:
        return (self.ejemplar,)

    def aplicar(self) -> None:
        if self.comprador is self.vendedor:
            raise ErrorMercado("No se puede comprar una carta propia")
        if not reglas.venta_valida(self.ejemplar.carta, self.precio):
            raise ErrorMercado("Venta inválida (precio bajo el valor base o carta no intercambiable)")
        if not self.vendedor.tiene(self.ejemplar):
            raise ErrorMercado("El vendedor no tiene ese ejemplar")
        self.comprador._cobrar(self.precio)
        self.vendedor._quitar(self.ejemplar)
        self.comprador._agregar(self.ejemplar)
        self.vendedor._acreditar(self.precio)


@dataclass
class Intercambio(Transaccion):
    emisor: Jugador
    receptor: Jugador
    brinda: tuple  # ejemplares que da el emisor
    recibe: tuple  # ejemplares que da el receptor

    def participantes(self) -> tuple:
        return (self.emisor, self.receptor)

    def ejemplares(self) -> tuple:
        return tuple(self.brinda) + tuple(self.recibe)

    def aplicar(self) -> None:
        if self.emisor is self.receptor:
            raise ErrorMercado("No se puede intercambiar con uno mismo")
        todos = self.ejemplares()
        ids = [e.id_ejemplar for e in todos]
        if len(set(ids)) != len(ids):
            raise ErrorMercado("Un ejemplar aparece repetido en el intercambio")
        if not all(self.emisor.tiene(e) for e in self.brinda):
            raise ErrorMercado("El emisor no tiene todos los ejemplares que ofrece")
        if not all(self.receptor.tiene(e) for e in self.recibe):
            raise ErrorMercado("El receptor no tiene todos los ejemplares que ofrece")
        if not all(e.carta.intercambiable for e in todos):
            raise ErrorMercado("Hay cartas que no se pueden intercambiar")
        if not reglas.intercambio_balanceado(self.brinda, self.recibe):
            raise ErrorMercado("El intercambio no está balanceado")
        for e in self.brinda:
            self.emisor._quitar(e)
            self.receptor._agregar(e)
        for e in self.recibe:
            self.receptor._quitar(e)
            self.emisor._agregar(e)


@dataclass
class Operacion:
    tipo: str
    datos: dict
    estado_previo: dict
