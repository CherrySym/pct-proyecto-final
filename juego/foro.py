"""Foro de publicaciones: ventas, intercambios y subastas."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from .catalogo import Ejemplar
from .comunes import ErrorMercado, TipoPublicacion
from .jugador import Jugador
from .reglas import ReglasEconomia


class Publicacion:
    def __init__(self, autor: Jugador, ejemplar: Ejemplar, tipo: TipoPublicacion,
                 precio_pedido: Optional[int] = None):
        # Restricción del UML: precio_pedido existe solo si tipo = Venta.
        if (tipo == TipoPublicacion.VENTA) != (precio_pedido is not None):
            raise ErrorMercado("precio_pedido es obligatorio en ventas y no va en intercambios")
        self.autor = autor
        self.ejemplar = ejemplar
        self.tipo = tipo
        self.precio_pedido = precio_pedido


@dataclass(frozen=True)
class Oferta:
    jugador: Jugador
    monto: int


class Subasta(Publicacion):
    """Subasta de una carta. precio_pedido funciona como precio mínimo."""

    def __init__(self, autor: Jugador, ejemplar: Ejemplar, precio_minimo: int, cierre: date):
        super().__init__(autor, ejemplar, TipoPublicacion.VENTA, precio_minimo)
        self.cierre = cierre
        self._ofertas: list = []

    @property
    def ofertas(self) -> tuple:
        return tuple(self._ofertas)

    def ofertar(self, jugador: Jugador, monto: int, fecha: date) -> Oferta:
        if fecha >= self.cierre:
            raise ErrorMercado("La subasta ya cerró")
        if jugador is self.autor:
            raise ErrorMercado("No se puede ofertar en la subasta propia")
        mejor = max((o.monto for o in self._ofertas), default=self.precio_pedido - 1)
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
        ejemplar = publicacion.ejemplar
        if not publicacion.autor.tiene(ejemplar):
            raise ErrorMercado("El autor no tiene ese ejemplar")
        if any(p.ejemplar == ejemplar for p in self._publicaciones):
            raise ErrorMercado("Ese ejemplar ya está publicado")
        if not ejemplar.carta.intercambiable:
            raise ErrorMercado("Esa carta no se puede vender ni intercambiar")
        if (publicacion.tipo == TipoPublicacion.VENTA
                and not ReglasEconomia.venta_valida(ejemplar.carta, publicacion.precio_pedido)):
            raise ErrorMercado("El precio está por debajo del valor base")
        self._publicaciones.append(publicacion)

    def retirar(self, publicacion: Publicacion) -> None:
        if publicacion not in self._publicaciones:
            raise ErrorMercado("Esa publicación no está en el foro")
        self._publicaciones.remove(publicacion)

    def _retirar_ejemplar(self, ejemplar: Ejemplar) -> None:
        """Si un ejemplar cambia de dueño, su publicación deja de tener sentido."""
        self._publicaciones = [p for p in self._publicaciones if p.ejemplar != ejemplar]

    def _capturar(self) -> list:
        return list(self._publicaciones)

    def _restaurar(self, publicaciones: list) -> None:
        self._publicaciones = list(publicaciones)
