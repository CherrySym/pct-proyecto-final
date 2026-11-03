"""Reglas de la economía como funciones puras."""
from __future__ import annotations

from typing import Sequence

from .catalogo import Carta, Ejemplar
from .comunes import Estacion, Rareza


class ReglasEconomia:
    """Funciones puras: solo calculan, no modifican nada."""

    VALOR_BASE = {Rareza.COMUN: 5, Rareza.RARA: 15, Rareza.EPICA: 50,
                  Rareza.LEGENDARIA: 200, Rareza.MITICA: 800}
    VALOR_INTERCAMBIO = {Rareza.COMUN: 1, Rareza.RARA: 3, Rareza.EPICA: 10,
                         Rareza.LEGENDARIA: 40, Rareza.MITICA: 160}
    MULTIPLICADOR_TEMPORADA = 1.5
    FRACCION_SISTEMA = 0.4  # parte del precio que paga el mercado al comprarte una carta

    @staticmethod
    def valor_base(rareza: Rareza) -> int:
        return ReglasEconomia.VALOR_BASE[rareza]

    @staticmethod
    def multiplicador(carta: Carta, estacion: Estacion) -> float:
        return ReglasEconomia.MULTIPLICADOR_TEMPORADA if carta.estacion == estacion else 1.0

    @staticmethod
    def precio(carta: Carta, estacion: Estacion) -> int:
        return round(ReglasEconomia.valor_base(carta.rareza)
                     * ReglasEconomia.multiplicador(carta, estacion))

    @staticmethod
    def precio_venta_sistema(carta: Carta, estacion: Estacion) -> int:
        return int(ReglasEconomia.precio(carta, estacion) * ReglasEconomia.FRACCION_SISTEMA)

    @staticmethod
    def venta_valida(carta: Carta, precio_pedido: int) -> bool:
        """No se puede vender por debajo del valor base, ni vender cartas no intercambiables."""
        return carta.intercambiable and precio_pedido >= ReglasEconomia.valor_base(carta.rareza)

    @staticmethod
    def valor_intercambio(rareza: Rareza) -> int:
        return ReglasEconomia.VALOR_INTERCAMBIO[rareza]

    @staticmethod
    def intercambio_balanceado(da: Sequence[Ejemplar], recibe: Sequence[Ejemplar]) -> bool:
        def total(ejemplares):
            return sum(ReglasEconomia.valor_intercambio(e.carta.rareza) for e in ejemplares)
        return bool(da) and bool(recibe) and total(da) == total(recibe)
