"""Mercado de cartas coleccionables de plantas.

Modelo basado en el UML del hito 1. Reglas generales:
- La única clase que crea, quema o mueve polen es Mercado.
- Toda operación del Mercado se ejecuta con `_ejecutar`: si falla a la mitad,
  se restaura el estado anterior (no deja rastros) y, si sale bien, se guarda
  en el historial para poder deshacerla.
- El azar entra por la interfaz Azar, así que con el mismo AzarFijo (o la
  misma semilla) el resultado es siempre el mismo.
"""
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from enum import Enum
from itertools import count
from types import MappingProxyType
from typing import Callable, Optional, Sequence, TypeVar

T = TypeVar("T")


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


# ---------------------------------------------------------------- catálogo

@dataclass(frozen=True)
class Carta:
    """Carta del catálogo. Lo que tiene un jugador es un Ejemplar de ella."""
    id_carta: int
    nombre: str
    especie: Especie
    rareza: Rareza
    estacion: Estacion
    intercambiable: bool = True


@dataclass(frozen=True)
class Edicion:
    """Colección de un año. Completarla primero da la insignia."""
    nombre: str
    cartas: tuple

    def __post_init__(self):
        ids = [c.id_carta for c in self.cartas]
        if len(ids) != len(set(ids)):
            raise ValueError("Una edición no puede repetir id_carta")

    def cartas_de(self, rareza: Rareza) -> tuple:
        return tuple(c for c in self.cartas if c.rareza == rareza)


@dataclass(frozen=True)
class Ejemplar:
    id_ejemplar: int
    carta: Carta


@dataclass(frozen=True)
class Insignia:
    fecha_obtenida: date
    edicion: Edicion


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


# ---------------------------------------------------------------- sobres

CARTAS_POR_SOBRE = 5


@dataclass(frozen=True)
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
        object.__setattr__(self, "probabilidades",
                           MappingProxyType(dict(self.probabilidades)))


@dataclass(frozen=True)
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


# ---------------------------------------------------------------- reglas (puras)

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


# ---------------------------------------------------------------- jugador

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
        tengo = {e.carta.id_carta for e in self._coleccion}
        return all(c.id_carta in tengo for c in edicion.cartas)

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


# ---------------------------------------------------------------- operaciones

@dataclass(frozen=True)
class Venta:
    vendedor: Jugador
    ejemplar: Ejemplar
    precio: int


@dataclass(frozen=True)
class Intercambio:
    emisor: Jugador
    receptor: Jugador
    brinda: tuple  # ejemplares que da el emisor
    recibe: tuple  # ejemplares que da el receptor


@dataclass(frozen=True)
class Operacion:
    tipo: str
    datos: dict
    estado_previo: dict


# ---------------------------------------------------------------- foro

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


# ---------------------------------------------------------------- mercado

POLEN_INICIAL = 100
RECOMPENSA_DIARIA = 20
UMBRAL_RECOMPENSA = 50


class Mercado:
    def __init__(self, edicion: Edicion, foro: Optional[Foro] = None):
        self._edicion = edicion
        self._foro = foro if foro is not None else Foro()
        self._jugadores: list = []
        self._historial: list = []
        self._ganador: Optional[Jugador] = None
        self._ids_sobre = count(1)  # nunca se reinicia: los ids no se reutilizan

    @property
    def historial(self) -> tuple:
        return tuple(self._historial)

    @property
    def edicion(self) -> Edicion:
        return self._edicion

    @property
    def foro(self) -> Foro:
        return self._foro

    @property
    def jugadores(self) -> tuple:
        return tuple(self._jugadores)

    def polen_total(self) -> int:
        return sum(j.polen for j in self._jugadores)

    # --- motor: atomicidad + historial ---

    def _capturar(self) -> dict:
        return {"edicion": self._edicion,
                "ganador": self._ganador,
                "foro": self._foro._capturar(),
                "jugadores": [(j, j._capturar()) for j in self._jugadores]}

    def _restaurar(self, estado: dict) -> None:
        self._edicion = estado["edicion"]
        self._ganador = estado["ganador"]
        self._foro._restaurar(estado["foro"])
        self._jugadores = [j for j, _ in estado["jugadores"]]
        for jugador, estado_jugador in estado["jugadores"]:
            jugador._restaurar(estado_jugador)

    def _ejecutar(self, tipo: str, datos: dict, accion: Callable[[], T]) -> T:
        """Función de orden superior: corre `accion` de forma atómica."""
        previo = self._capturar()
        try:
            resultado = accion()
        except Exception:
            self._restaurar(previo)  # una operación inválida no deja rastros
            raise
        self._historial.append(Operacion(tipo, datos, previo))
        return resultado

    def _verificar(self, *jugadores: Jugador) -> None:
        for j in jugadores:
            if j not in self._jugadores:
                raise ErrorMercado(f"{j.nickname} no está registrado")

    # --- pasos internos (validan primero, después modifican) ---

    def _hacer_venta(self, venta: Venta, comprador: Jugador) -> None:
        self._verificar(venta.vendedor, comprador)
        if comprador is venta.vendedor:
            raise ErrorMercado("No se puede comprar una carta propia")
        if not ReglasEconomia.venta_valida(venta.ejemplar.carta, venta.precio):
            raise ErrorMercado("Venta inválida (precio bajo el valor base o carta no intercambiable)")
        if not venta.vendedor.tiene(venta.ejemplar):
            raise ErrorMercado("El vendedor no tiene ese ejemplar")
        comprador._cobrar(venta.precio)
        venta.vendedor._quitar(venta.ejemplar)
        comprador._agregar(venta.ejemplar)
        venta.vendedor._acreditar(venta.precio)
        self._foro._retirar_ejemplar(venta.ejemplar)

    def _hacer_intercambio(self, inter: Intercambio) -> None:
        self._verificar(inter.emisor, inter.receptor)
        if inter.emisor is inter.receptor:
            raise ErrorMercado("No se puede intercambiar con uno mismo")
        todos = list(inter.brinda) + list(inter.recibe)
        if len(set(todos)) != len(todos):
            raise ErrorMercado("Un ejemplar aparece repetido en el intercambio")
        if not all(inter.emisor.tiene(e) for e in inter.brinda):
            raise ErrorMercado("El emisor no tiene todos los ejemplares que ofrece")
        if not all(inter.receptor.tiene(e) for e in inter.recibe):
            raise ErrorMercado("El receptor no tiene todos los ejemplares que ofrece")
        if not all(e.carta.intercambiable for e in todos):
            raise ErrorMercado("Hay cartas que no se pueden intercambiar")
        if not ReglasEconomia.intercambio_balanceado(inter.brinda, inter.recibe):
            raise ErrorMercado("El intercambio no está balanceado")
        for e in inter.brinda:
            inter.emisor._quitar(e)
            inter.receptor._agregar(e)
        for e in inter.recibe:
            inter.receptor._quitar(e)
            inter.emisor._agregar(e)
        for e in todos:
            self._foro._retirar_ejemplar(e)

    # --- operaciones públicas ---

    def registrar_jugador(self, jugador: Jugador) -> None:
        def accion():
            if jugador in self._jugadores:
                raise ErrorMercado("El jugador ya está registrado")
            self._jugadores.append(jugador)
            jugador._acreditar(POLEN_INICIAL)
        self._ejecutar("registrar_jugador", {"jugador": jugador.nickname}, accion)

    def comprar_sobre(self, jugador: Jugador, tipo: TipoSobre) -> Sobre:
        def accion():
            self._verificar(jugador)
            jugador._cobrar(tipo.precio)
            sobre = Sobre(next(self._ids_sobre), tipo, self._edicion)
            jugador._agregar_sobre(sobre)
            return sobre
        return self._ejecutar("comprar_sobre",
                              {"jugador": jugador.nickname, "tipo": tipo.nombre}, accion)

    def abrir_sobre(self, jugador: Jugador, sobre: Sobre, azar: Azar) -> list:
        def accion():
            self._verificar(jugador)
            return jugador.abrir_sobre(sobre, azar)
        return self._ejecutar("abrir_sobre",
                              {"jugador": jugador.nickname, "sobre": sobre.id_sobre}, accion)

    def comprar_carta(self, venta: Venta, comprador: Jugador) -> None:
        self._ejecutar("comprar_carta",
                       {"vendedor": venta.vendedor.nickname, "comprador": comprador.nickname,
                        "ejemplar": venta.ejemplar.id_ejemplar, "precio": venta.precio},
                       lambda: self._hacer_venta(venta, comprador))

    def vender_al_mercado(self, jugador: Jugador, ejemplar: Ejemplar, estacion: Estacion) -> int:
        def accion():
            self._verificar(jugador)
            pago = ReglasEconomia.precio_venta_sistema(ejemplar.carta, estacion)
            jugador._quitar(ejemplar)
            jugador._acreditar(pago)
            self._foro._retirar_ejemplar(ejemplar)
            return pago
        return self._ejecutar("vender_al_mercado",
                              {"jugador": jugador.nickname, "ejemplar": ejemplar.id_ejemplar,
                               "estacion": estacion.value}, accion)

    def intercambiar(self, intercambio: Intercambio) -> None:
        self._ejecutar("intercambiar",
                       {"emisor": intercambio.emisor.nickname,
                        "receptor": intercambio.receptor.nickname,
                        "brinda": [e.id_ejemplar for e in intercambio.brinda],
                        "recibe": [e.id_ejemplar for e in intercambio.recibe]},
                       lambda: self._hacer_intercambio(intercambio))

    def publicar(self, publicacion: Publicacion) -> None:
        def accion():
            self._verificar(publicacion.autor)
            self._foro.publicar(publicacion)
        self._ejecutar("publicar", {"autor": publicacion.autor.nickname,
                                    "ejemplar": publicacion.ejemplar.id_ejemplar}, accion)

    def retirar(self, publicacion: Publicacion) -> None:
        self._ejecutar("retirar", {"ejemplar": publicacion.ejemplar.id_ejemplar},
                       lambda: self._foro.retirar(publicacion))

    def aceptar_publicacion(self, publicacion: Publicacion, comprador: Jugador,
                            ofrece: Sequence[Ejemplar] = ()) -> None:
        """Venta: el comprador paga precio_pedido. Intercambio: entrega `ofrece`."""
        def accion():
            if isinstance(publicacion, Subasta):
                raise ErrorMercado("Las subastas se resuelven con cerrar_subasta")
            if publicacion not in self._foro.publicaciones:
                raise ErrorMercado("Esa publicación no está en el foro")
            if publicacion.tipo == TipoPublicacion.VENTA:
                venta = Venta(publicacion.autor, publicacion.ejemplar, publicacion.precio_pedido)
                self._hacer_venta(venta, comprador)
            else:
                self._hacer_intercambio(Intercambio(publicacion.autor, comprador,
                                                    (publicacion.ejemplar,), tuple(ofrece)))
        self._ejecutar("aceptar_publicacion",
                       {"autor": publicacion.autor.nickname, "comprador": comprador.nickname,
                        "ejemplar": publicacion.ejemplar.id_ejemplar}, accion)

    def cerrar_subasta(self, subasta: Subasta, fecha: date) -> Optional[Oferta]:
        """Gana la oferta más alta cuyo jugador todavía tenga el polen."""
        def accion():
            if subasta not in self._foro.publicaciones:
                raise ErrorMercado("Esa subasta no está en el foro")
            for oferta in subasta.cerrar(fecha):
                if oferta.jugador in self._jugadores and oferta.jugador.polen >= oferta.monto:
                    self._hacer_venta(Venta(subasta.autor, subasta.ejemplar, oferta.monto),
                                      oferta.jugador)
                    return oferta
            self._foro.retirar(subasta)  # nadie pudo pagar
            return None
        return self._ejecutar("cerrar_subasta",
                              {"ejemplar": subasta.ejemplar.id_ejemplar,
                               "fecha": fecha.isoformat()}, accion)

    def reclamar_recompensa(self, jugador: Jugador, fecha: date) -> int:
        def accion():
            self._verificar(jugador)
            if jugador.polen >= UMBRAL_RECOMPENSA:
                raise ErrorMercado(f"Solo se reclama con menos de {UMBRAL_RECOMPENSA} de polen")
            if jugador._ultima_recompensa == fecha:
                raise ErrorMercado("La recompensa de hoy ya fue reclamada")
            jugador._marcar_recompensa(fecha)
            jugador._acreditar(RECOMPENSA_DIARIA)
            return RECOMPENSA_DIARIA
        return self._ejecutar("reclamar_recompensa",
                              {"jugador": jugador.nickname, "fecha": fecha.isoformat()}, accion)

    def reclamar_premio(self, jugador: Jugador, fecha: date) -> Insignia:
        """El primero que completa la edición se lleva la insignia."""
        def accion():
            self._verificar(jugador)
            if self._ganador is not None:
                raise ErrorMercado(f"La insignia ya la ganó {self._ganador.nickname}")
            if not jugador.coleccion_completa(self._edicion):
                raise ErrorMercado("La colección no está completa")
            insignia = Insignia(fecha, self._edicion)
            jugador._agregar_insignia(insignia)
            self._ganador = jugador
            return insignia
        return self._ejecutar("reclamar_premio",
                              {"jugador": jugador.nickname, "fecha": fecha.isoformat()}, accion)

    def reiniciar_anio(self, edicion: Edicion) -> None:
        def accion():
            for jugador in self._jugadores:
                jugador._reiniciar(POLEN_INICIAL)
            self._foro._restaurar([])
            self._edicion = edicion
            self._ganador = None
        self._ejecutar("reiniciar_anio", {"edicion": edicion.nombre}, accion)

    def deshacer(self) -> Operacion:
        if not self._historial:
            raise ErrorMercado("No hay operaciones para deshacer")
        operacion = self._historial.pop()
        self._restaurar(operacion.estado_previo)
        return operacion


# ---------------------------------------------------------------- demo

def edicion_demo() -> Edicion:
    E, R, S = Especie, Rareza, Estacion
    return Edicion("2026", (
        Carta(1, "Monstera", E.SELVA_TROPICAL, R.COMUN, S.VERANO),
        Carta(2, "Echeveria", E.DESIERTO_Y_SUCULENTAS, R.COMUN, S.VERANO),
        Carta(3, "Tulipán", E.FLORES_DE_PRIMAVERA, R.COMUN, S.PRIMAVERA),
        Carta(4, "Romero", E.HIERBAS_AROMATICAS, R.COMUN, S.INVIERNO),
        Carta(5, "Dionaea", E.PLANTAS_CARNIVORAS, R.RARA, S.VERANO),
        Carta(6, "Lavanda", E.HIERBAS_AROMATICAS, R.RARA, S.PRIMAVERA),
        Carta(7, "Mburucuyá", E.MONTE_URUGUAYO, R.EPICA, S.VERANO),
        Carta(8, "Nepenthes", E.PLANTAS_CARNIVORAS, R.EPICA, S.OTONO),
        Carta(9, "Ceibo", E.MONTE_URUGUAYO, R.LEGENDARIA, S.PRIMAVERA),
        Carta(10, "Welwitschia", E.DESIERTO_Y_SUCULENTAS, R.MITICA, S.INVIERNO,
              intercambiable=False),
    ))


if __name__ == "__main__":
    mercado = Mercado(edicion_demo())
    ana = Jugador("Ana", "ana_flora", "ana@ejemplo.com")
    beto = Jugador("Beto", "beto_cactus", "beto@ejemplo.com")
    mercado.registrar_jugador(ana)
    mercado.registrar_jugador(beto)

    sobre = mercado.comprar_sobre(ana, SOBRE_COMUN)
    for ej in mercado.abrir_sobre(ana, sobre, AzarReal(semilla=42)):
        print(f"Ana sacó #{ej.id_ejemplar}: {ej.carta.nombre} ({ej.carta.rareza.value})")
    print(ana, beto, "| polen total:", mercado.polen_total())

    try:
        mercado.comprar_sobre(beto, SOBRE_DORADO)
    except ErrorMercado as e:
        print("Rechazado:", e, "|", beto)

    mercado.deshacer()
    print(f"Después de deshacer la apertura: {len(ana.sobres)} sobre sin abrir, {len(ana.coleccion)} cartas")
