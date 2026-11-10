"""Núcleo puro: funciones que calculan sobre el estado del juego sin modificarlo.

Ninguna función de este archivo lee globales, imprime, ni modifica sus
argumentos: con la misma entrada devuelven siempre lo mismo.
"""
from __future__ import annotations

from functools import reduce
from itertools import count, islice
from typing import Callable, Iterable, Iterator, Optional

from .catalogo import Edicion, Ejemplar
from .comunes import Azar, Especie, Estacion, Rareza
from .reglas import ReglasEconomia
from .sobres import Sobre, TipoSobre

# Un criterio es cualquier función que recibe una publicación y devuelve True o False.
Criterio = Callable[[object], bool]


# ---------------------------------------------------------------- colección

def cartas_faltantes(ejemplares: Iterable[Ejemplar], edicion: Edicion) -> tuple:
    """Cartas de la edición que todavía no tiene (filter)."""
    tengo = {e.carta.id_carta for e in ejemplares}
    return tuple(filter(lambda c: c.id_carta not in tengo, edicion.cartas))


def progreso(ejemplares: Iterable[Ejemplar], edicion: Edicion) -> float:
    """Fracción de la edición completada, entre 0 y 1."""
    if not edicion.cartas:
        return 1.0
    faltan = len(cartas_faltantes(ejemplares, edicion))
    return 1 - faltan / len(edicion.cartas)


def contar_por_carta(ejemplares: Iterable[Ejemplar]) -> dict:
    """{id_carta: cantidad}. reduce sin mutar: cada paso devuelve un diccionario nuevo."""
    def sumar(cuenta: dict, ejemplar: Ejemplar) -> dict:
        clave = ejemplar.carta.id_carta
        return {**cuenta, clave: cuenta.get(clave, 0) + 1}
    return reduce(sumar, ejemplares, {})


def repetidos(ejemplares: Iterable[Ejemplar]) -> tuple:
    """Ejemplares que sobran: se queda el primero de cada carta, el resto se puede vender."""
    def acumular(estado: tuple, ejemplar: Ejemplar) -> tuple:
        vistos, sobran = estado
        clave = ejemplar.carta.id_carta
        if clave in vistos:
            return vistos, sobran + (ejemplar,)
        return vistos | {clave}, sobran
    _, sobran = reduce(acumular, ejemplares, (frozenset(), ()))
    return sobran


def valor_coleccion(ejemplares: Iterable[Ejemplar], estacion: Estacion) -> int:
    """Suma del precio de cada ejemplar en esa estación (map + sum)."""
    return sum(map(lambda e: ReglasEconomia.precio(e.carta, estacion), ejemplares))


# ---------------------------------------------------------------- historial verificable

def registro_operaciones(historial: Iterable) -> list:
    """Convierte el historial en datos simples (listas, dicts, strings, números)
    listos para guardar en JSON. No incluye las fotos del estado: el registro dice
    qué pasó y en qué orden, sin copiar todos los datos de los jugadores."""
    return [{"numero": n, "tipo": op.tipo, "datos": dict(op.datos)}
            for n, op in enumerate(historial, start=1)]


def contar_por_tipo(registro: Iterable[dict]) -> dict:
    """{tipo de operación: cantidad}, para verificar un registro guardado."""
    return reduce(lambda acc, r: {**acc, r["tipo"]: acc.get(r["tipo"], 0) + 1}, registro, {})


# ---------------------------------------------------------------- criterios del foro
# Fábricas de funciones (closures): cada una devuelve un criterio para Foro.buscar.

def de_especie(especie: Especie) -> Criterio:
    return lambda pub: pub.ejemplar.carta.especie == especie


def de_rareza(rareza: Rareza) -> Criterio:
    return lambda pub: pub.ejemplar.carta.rareza == rareza


def precio_hasta(maximo: int) -> Criterio:
    """Solo publicaciones con precio, y que no pasen el máximo."""
    return lambda pub: getattr(pub, "precio_pedido", None) is not None and pub.precio_pedido <= maximo


def faltantes_para(ejemplares: Iterable[Ejemplar], edicion: Edicion) -> Criterio:
    """Publicaciones de cartas que todavía me faltan."""
    ids = {c.id_carta for c in cartas_faltantes(ejemplares, edicion)}
    return lambda pub: pub.ejemplar.carta.id_carta in ids


def todos(*criterios: Criterio) -> Criterio:
    """Combina criterios: la publicación tiene que cumplirlos todos."""
    return lambda pub: all(c(pub) for c in criterios)


# ---------------------------------------------------------------- simulación (perezosa)

def aperturas(tipo: TipoSobre, edicion: Edicion, azar: Azar) -> Iterator[tuple]:
    """Generador infinito: cada next() abre un sobre nuevo y devuelve sus cartas.
    No calcula nada por adelantado; se consume de a poco con islice o next."""
    for id_sobre in count(1):
        yield tuple(e.carta for e in Sobre(id_sobre, tipo, edicion).abrir(azar))


def frecuencia_rarezas(tipo: TipoSobre, edicion: Edicion, azar: Azar, sobres: int) -> dict:
    """Proporción de cada rareza en `sobres` aperturas simuladas."""
    cartas = [c for sobre in islice(aperturas(tipo, edicion, azar), sobres) for c in sobre]
    cuenta = reduce(lambda acc, c: {**acc, c.rareza: acc.get(c.rareza, 0) + 1}, cartas, {})
    return {rareza: n / len(cartas) for rareza, n in cuenta.items()}

