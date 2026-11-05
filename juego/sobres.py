"""Tipos de sobre (precio y probabilidades) y apertura de sobres."""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

from .catalogo import Carta, Edicion, Ejemplar
from .comunes import Azar, ErrorMercado, Rareza


CARTAS_POR_SOBRE = 5


@dataclass
class TipoSobre:
    nombre: str
    precio: int
    probabilidades: dict  # Rareza -> probabilidad

    def __post_init__(self):
        if self.precio <= 0:
            raise ValueError("El precio del sobre debe ser positivo")
        if any(p < 0 for p in self.probabilidades.values()):
            raise ValueError("No puede haber probabilidades negativas")
        if abs(sum(self.probabilidades.values()) - 1) > 1e-9:
            raise ValueError("Las probabilidades deben sumar 1")
        # Copia de solo lectura: nadie puede cambiar las probabilidades después.
        self.probabilidades = MappingProxyType(dict(self.probabilidades))


@dataclass
class Sobre:
    id_sobre: int
    tipo: TipoSobre
    edicion: Edicion

    def abrir(self, azar: Azar) -> list:
        # El id de cada ejemplar sale del id del sobre, que es único:
        # dos sobres nunca pueden generar el mismo id_ejemplar.
        return [Ejemplar(self.id_sobre * CARTAS_POR_SOBRE + i, self._sortear_carta(azar))
                for i in range(CARTAS_POR_SOBRE)]

    def _sortear_carta(self, azar: Azar) -> Carta:
        # Paso 1: sortear la rareza (solo entre las que tienen cartas en la edición).
        probs = self.tipo.probabilidades
        rarezas = [r for r in Rareza if probs.get(r, 0) > 0 and self.edicion.cartas_de(r)]
        if not rarezas:
            raise ErrorMercado("La edición no tiene cartas para este sobre")
        rareza = azar.elegir(rarezas, [probs[r] for r in rarezas])
        # Paso 2: sortear la carta dentro de esa rareza, todas con el mismo peso.
        cartas = self.edicion.cartas_de(rareza)
        return azar.elegir(cartas, [1] * len(cartas))


SOBRE_COMUN = TipoSobre("Común", 50, {
    Rareza.COMUN: 0.75, Rareza.RARA: 0.20, Rareza.EPICA: 0.04,
    Rareza.LEGENDARIA: 0.009, Rareza.MITICA: 0.001})
SOBRE_PLATEADO = TipoSobre("Plateado", 150, {
    Rareza.COMUN: 0.40, Rareza.RARA: 0.38, Rareza.EPICA: 0.17,
    Rareza.LEGENDARIA: 0.045, Rareza.MITICA: 0.005})
SOBRE_DORADO = TipoSobre("Dorado", 500, {
    Rareza.COMUN: 0.0, Rareza.RARA: 0.30, Rareza.EPICA: 0.45,
    Rareza.LEGENDARIA: 0.20, Rareza.MITICA: 0.05})
