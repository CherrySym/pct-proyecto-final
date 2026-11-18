"""Foro de publicaciones: ventas, intercambios y subastas.

Publicacion es abstracta. Cada tipo de publicación sabe validarse, resolverse
y decir su precio de referencia a su manera (polimorfismo), así que ni el Foro,
ni el Mercado, ni los criterios de búsqueda preguntan "¿de qué tipo es?".
Para agregar un tipo nuevo alcanza con una subclase nueva.

Este archivo no conoce al Mercado: resolver() solo describe la operación
(devuelve una Venta o un Intercambio) y el Mercado es quien la ejecuta.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Callable, Iterator, Optional, Sequence

from .catalogo import Ejemplar
from .comunes import ErrorMercado
from .jugador import Jugador
from .operaciones import Intercambio, Transaccion, Venta
from . import reglas


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

    def _olvidar_jugador(self, jugador: Jugador) -> None:
        """Borra los datos de un jugador que la publicación tenga guardados.
        Por defecto no hay ninguno; Subasta lo redefine porque guarda ofertas."""

    def _capturar(self):
        """Foto del estado que puede cambiar adentro de la publicación.
        Por defecto no hay nada que guardar; Subasta lo redefine porque guarda ofertas."""
        return None

    def _restaurar(self, estado) -> None:
        """Vuelve al estado de _capturar. Por defecto no hay nada que restaurar."""

    @abstractmethod
    def precio_de_referencia(self) -> Optional[int]:
        """El precio con el que se compara la publicación, o None si no tiene."""

    @abstractmethod
    def resolver(self, comprador: Jugador, ofrece: Sequence[Ejemplar]) -> Transaccion:
        """Describe la operación que ocurre si `comprador` acepta la publicación.
        No modifica nada: devuelve el dato y el Mercado la ejecuta."""

    @abstractmethod
    def descripcion(self) -> str:
        """Texto con el tipo de publicación y sus datos propios. No imprime:
        quien la muestra decide dónde (polimorfismo: el menú no pregunta el tipo)."""


class PublicacionVenta(Publicacion):
    def __init__(self, autor: Jugador, ejemplar: Ejemplar, precio_pedido: int):
        if not reglas.es_monto(precio_pedido):
            raise ErrorMercado(f"Precio inválido: {precio_pedido!r}")
        super().__init__(autor, ejemplar)
        self.precio_pedido = precio_pedido

    def validar(self) -> None:
        super().validar()
        if not reglas.venta_valida(self.ejemplar.carta, self.precio_pedido):
            raise ErrorMercado("El precio está por debajo del valor base")

    def precio_de_referencia(self) -> int:
        return self.precio_pedido

    def resolver(self, comprador, ofrece) -> Venta:
        return Venta(self.autor, comprador, self.ejemplar, self.precio_pedido)

    def descripcion(self) -> str:
        return f"Venta: {self.precio_pedido} de polen"


class PublicacionIntercambio(Publicacion):
    def __init__(self, autor: Jugador, ejemplar: Ejemplar, busca: str = ""):
        super().__init__(autor, ejemplar)
        self.busca = busca  # texto libre: qué quiere a cambio

    def precio_de_referencia(self) -> None:
        return None  # un intercambio no tiene precio

    def resolver(self, comprador, ofrece) -> Intercambio:
        return Intercambio(self.autor, comprador, (self.ejemplar,), tuple(ofrece))

    def descripcion(self) -> str:
        busca = f", busca: {self.busca}" if self.busca else ""
        return f"Intercambio: vale {reglas.valor_intercambio(self.ejemplar.carta.rareza)}{busca}"


@dataclass
class Oferta:
    jugador: Jugador
    monto: int


class Subasta(Publicacion):
    """La carta se la lleva la oferta más alta al cierre. Se resuelve con
    Mercado.cerrar_subasta, no aceptándola directamente."""

    def __init__(self, autor: Jugador, ejemplar: Ejemplar, precio_minimo: int, cierre: date):
        if not reglas.es_monto(precio_minimo):
            raise ErrorMercado(f"Precio mínimo inválido: {precio_minimo!r}")
        if not isinstance(cierre, date):
            raise ErrorMercado("El cierre tiene que ser una fecha")
        super().__init__(autor, ejemplar)
        self.precio_minimo = precio_minimo
        self.cierre = cierre
        self._ofertas: list = []  # composición: la subasta crea sus ofertas

    def ofertas(self) -> tuple:
        return tuple(self._ofertas)

    def validar(self) -> None:
        super().validar()
        if not reglas.venta_valida(self.ejemplar.carta, self.precio_minimo):
            raise ErrorMercado("El precio mínimo está por debajo del valor base")

    def precio_de_referencia(self) -> int:
        return self.precio_minimo

    def resolver(self, comprador, ofrece):
        raise ErrorMercado("Las subastas no se aceptan: se cierran con cerrar_subasta")

    def descripcion(self) -> str:
        mejor = max((o.monto for o in self._ofertas), default=None)
        oferta = f"mejor oferta {mejor}" if mejor is not None else "sin ofertas"
        return f"Subasta: mínimo {self.precio_minimo}, {oferta}, cierra {self.cierre:%d/%m}"

    def ofertar(self, jugador: Jugador, monto: int, fecha: date) -> Oferta:
        if not reglas.es_monto(monto):
            raise ErrorMercado(f"Monto inválido: {monto!r}")
        if fecha >= self.cierre:
            raise ErrorMercado("La subasta ya cerró")
        if jugador is self.autor:
            raise ErrorMercado("No se puede ofertar en la subasta propia")
        mejor = max((o.monto for o in self._ofertas), default=self.precio_minimo - 1)
        if monto <= mejor:
            raise ErrorMercado(f"La oferta debe superar {mejor}")
        if monto > jugador.polen():
            raise ErrorMercado("No tiene polen para cubrir la oferta")
        oferta = Oferta(jugador, monto)
        self._ofertas.append(oferta)
        return oferta

    def _olvidar_jugador(self, jugador: Jugador) -> None:
        self._ofertas = [o for o in self._ofertas if o.jugador is not jugador]

    def _capturar(self) -> list:
        return list(self._ofertas)

    def _restaurar(self, ofertas: list) -> None:
        self._ofertas = list(ofertas)

    def cerrar(self, fecha: date) -> tuple:
        """Devuelve las ofertas de mayor a menor. No mueve polen: eso lo hace el Mercado."""
        if fecha < self.cierre:
            raise ErrorMercado("La subasta todavía no cerró")
        return tuple(sorted(self._ofertas, key=lambda o: o.monto, reverse=True))


class Foro:
    def __init__(self):
        self._publicaciones: list = []

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
        """Lista de pares (publicación, su estado). Cada publicación sabe qué
        guardar de sí misma (polimorfismo): una subasta guarda sus ofertas."""
        return [(p, p._capturar()) for p in self._publicaciones]

    def _restaurar(self, estado: list) -> None:
        self._publicaciones = [p for p, _ in estado]
        for publicacion, estado_publicacion in estado:
            publicacion._restaurar(estado_publicacion)
