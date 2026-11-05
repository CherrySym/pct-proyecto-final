"""Jugador: su polen, colección, sobres e insignias."""
from __future__ import annotations

from datetime import date
from typing import Optional

from .analisis import cartas_faltantes
from .catalogo import Edicion, Ejemplar, Insignia
from .comunes import Azar, ErrorMercado
from .sobres import Sobre


class Jugador:
    """El polen y la colección son privados: solo el Mercado los modifica,
    usando los métodos que empiezan con guion bajo."""

    def __init__(self, nombre_jugador: str, nickname: str, email: str):
        self.nombre_jugador = nombre_jugador
        self.nickname = nickname
        self.email = email
        self._polen = 0
        self._coleccion: list = []
        self._sobres: list = []
        self._insignias: list = []
        self._ultima_recompensa: Optional[date] = None

    @property
    def polen(self) -> int:
        return self._polen

    @property
    def coleccion(self) -> tuple:
        return tuple(self._coleccion)

    @property
    def sobres(self) -> tuple:
        return tuple(self._sobres)

    @property
    def insignias(self) -> tuple:
        return tuple(self._insignias)

    def tiene(self, ejemplar: Ejemplar) -> bool:
        return ejemplar in self._coleccion

    def coleccion_completa(self, edicion: Edicion) -> bool:
        return not cartas_faltantes(self._coleccion, edicion)

    def abrir_sobre(self, sobre: Sobre, azar: Azar) -> list:
        """Usar Mercado.abrir_sobre para que quede en el historial."""
        if sobre not in self._sobres:
            raise ErrorMercado("El jugador no tiene ese sobre")
        ejemplares = sobre.abrir(azar)  # primero se calcula; si falla, no se tocó nada
        self._sobres.remove(sobre)
        self._coleccion.extend(ejemplares)
        return ejemplares

    # --- usados solo por Mercado ---

    def _cobrar(self, monto: int) -> None:
        if monto < 0:
            raise ErrorMercado("Monto negativo")
        if monto > self._polen:
            raise ErrorMercado(f"{self.nickname} no tiene polen suficiente")
        self._polen -= monto

    def _acreditar(self, monto: int) -> None:
        if monto < 0:
            raise ErrorMercado("Monto negativo")
        self._polen += monto

    def _agregar(self, ejemplar: Ejemplar) -> None:
        self._coleccion.append(ejemplar)

    def _quitar(self, ejemplar: Ejemplar) -> None:
        if ejemplar not in self._coleccion:
            raise ErrorMercado(f"{self.nickname} no tiene ese ejemplar")
        self._coleccion.remove(ejemplar)

    def _agregar_sobre(self, sobre: Sobre) -> None:
        self._sobres.append(sobre)

    def _agregar_insignia(self, insignia: Insignia) -> None:
        self._insignias.append(insignia)

    def _marcar_recompensa(self, fecha: date) -> None:
        self._ultima_recompensa = fecha

    def _reiniciar(self, polen_inicial: int) -> None:
        """Nuevo año: se conservan solo las insignias."""
        self._polen = polen_inicial
        self._coleccion = []
        self._sobres = []
        self._ultima_recompensa = None

    def _capturar(self) -> dict:
        return {"polen": self._polen, "coleccion": list(self._coleccion),
                "sobres": list(self._sobres), "insignias": list(self._insignias),
                "ultima_recompensa": self._ultima_recompensa}

    def _restaurar(self, estado: dict) -> None:
        self._polen = estado["polen"]
        self._coleccion = list(estado["coleccion"])
        self._sobres = list(estado["sobres"])
        self._insignias = list(estado["insignias"])
        self._ultima_recompensa = estado["ultima_recompensa"]

    def __repr__(self):
        return f"Jugador({self.nickname!r}, polen={self._polen})"
