"""Foro de publicaciones: ventas, intercambios y subastas.

Publicacion es abstracta. Cada tipo de publicación sabe validarse y resolverse
a su manera (polimorfismo), así que ni el Foro ni el Mercado preguntan
"¿de qué tipo es?". Para agregar un tipo nuevo alcanza con una subclase nueva.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Callable, Iterator, Sequence

from .catalogo import Ejemplar
from .comunes import ErrorMercado
from .jugador import Jugador
from .operaciones import Intercambio, Venta
from .reglas import ReglasEconomia

if TYPE_CHECKING:  # solo para las anotaciones; evita un import circular
    from .mercado import Mercado


class Publicacion(ABC):
    def __init__(self, autor: Jugador, ejemplar: Ejemplar):
        self.autor = autor
        self.ejemplar = ejemplar

    def validar(self) -> None:
        """Reglas comunes a todas las publicaciones. Las subclases agregan las suyas."""
        if not self.autor.tiene(self.ejemplar):
            raise ErrorMercado("El autor no tiene ese ejemplar")
        if not self.ejemplar.carta.intercambiable:
            raise ErrorMercado("Esa carta no se puede vender ni intercambiar")

    @abstractmethod
    def resolver(self, mercado: Mercado, comprador: Jugador,
                 ofrece: Sequence[Ejemplar]) -> None:
        """Lo que pasa cuando alguien acepta la publicación."""


class PublicacionVenta(Publicacion):
    def __init__(self, autor: Jugador, ejemplar: Ejemplar, precio_pedido: int):
        super().__init__(autor, ejemplar)
        self.precio_pedido = precio_pedido

    def validar(self) -> None:
        super().validar()
        if not ReglasEconomia.venta_valida(self.ejemplar.carta, self.precio_pedido):
            raise ErrorMercado("El precio está por debajo del valor base")

    def resolver(self, mercado, comprador, ofrece):
        mercado._hacer_venta(Venta(self.autor, self.ejemplar, self.precio_pedido), comprador)


class PublicacionIntercambio(Publicacion):
    def __init__(self, autor: Jugador, ejemplar: Ejemplar, busca: str = ""):
        super().__init__(autor, ejemplar)
        self.busca = busca  # texto libre: qué quiere a cambio

    def resolver(self, mercado, comprador, ofrece):
        mercado._hacer_intercambio(
            Intercambio(self.autor, comprador, (self.ejemplar,), tuple(ofrece)))


@dataclass
class Oferta:
    jugador: Jugador
    monto: int


class Subasta(Publicacion):
    """La carta se la lleva la oferta más alta al cierre. Se resuelve con
    Mercado.cerrar_subasta, no aceptándola directamente."""

    def __init__(self, autor: Jugador, ejemplar: Ejemplar, precio_minimo: int, cierre: date):
        super().__init__(autor, ejemplar)
        self.precio_minimo = precio_minimo
        self.cierre = cierre
        self._ofertas: list = []  # composición: la subasta crea sus ofertas

    @property
    def ofertas(self) -> tuple:
        return tuple(self._ofertas)

    def validar(self) -> None:
        super().validar()
        if not ReglasEconomia.venta_valida(self.ejemplar.carta, self.precio_minimo):
            raise ErrorMercado("El precio mínimo está por debajo del valor base")

    def resolver(self, mercado, comprador, ofrece):
        raise ErrorMercado("Las subastas no se aceptan: se cierran con cerrar_subasta")

    def ofertar(self, jugador: Jugador, monto: int, fecha: date) -> Oferta:
        if fecha >= self.cierre:
            raise ErrorMercado("La subasta ya cerró")
        if jugador is self.autor:
            raise ErrorMercado("No se puede ofertar en la subasta propia")
        mejor = max((o.monto for o in self._ofertas), default=self.precio_minimo - 1)
        if monto <= mejor:
            raise ErrorMercado(f"La oferta debe superar {mejor}")
        if monto > jugador.polen:
            raise ErrorMercado("No tiene polen para cubrir la oferta")
        oferta = Oferta(jugador, monto)
        self._ofertas.append(oferta)
        return oferta

    def cerrar(self, fecha: date) -> tuple:
        """Devuelve las ofertas de mayor a menor. No mueve polen: eso lo hace el Mercado."""
        if fecha < self.cierre:
            raise ErrorMercado("La subasta todavía no cerró")
        return tuple(sorted(self._ofertas, key=lambda o: o.monto, reverse=True))


class Foro:
    def __init__(self):
        self._publicaciones: list = []

    @property
    def publicaciones(self) -> tuple:
        return tuple(self._publicaciones)

    def publicar(self, publicacion: Publicacion) -> None:
        """Usar Mercado.publicar para que quede en el historial."""
        if any(p.ejemplar == publicacion.ejemplar for p in self._publicaciones):
            raise ErrorMercado("Ese ejemplar ya está publicado")
        publicacion.validar()  # polimorfismo: cada tipo sabe qué revisar
        self._publicaciones.append(publicacion)

    def retirar(self, publicacion: Publicacion) -> None:
        if publicacion not in self._publicaciones:
            raise ErrorMercado("Esa publicación no está en el foro")
        self._publicaciones.remove(publicacion)

    def buscar(self, criterio: Callable[[Publicacion], bool]) -> Iterator[Publicacion]:
        """Función de orden superior: recibe el criterio como función.
        Devuelve un iterador perezoso (filter): no recorre nada hasta que se lo pide."""
        return filter(criterio, tuple(self._publicaciones))

    def _retirar_ejemplar(self, ejemplar: Ejemplar) -> None:
        """Si un ejemplar cambia de dueño, su publicación deja de tener sentido."""
        self._publicaciones = [p for p in self._publicaciones if p.ejemplar != ejemplar]

    def _capturar(self) -> list:
        return list(self._publicaciones)

    def _restaurar(self, publicaciones: list) -> None:
        self._publicaciones = list(publicaciones)
