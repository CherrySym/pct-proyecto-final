"""Mercado: la única clase que mueve polen. Cada operación es atómica y queda en el historial."""
from __future__ import annotations

from datetime import date
from itertools import count
from typing import Callable, Optional, Sequence, TypeVar

from .catalogo import Edicion, Ejemplar, Insignia
from .comunes import Azar, ErrorMercado, Estacion, TipoPublicacion
from .foro import Foro, Oferta, Publicacion, Subasta
from .jugador import Jugador
from .operaciones import Intercambio, Operacion, Venta
from .reglas import ReglasEconomia
from .sobres import Sobre, TipoSobre

T = TypeVar("T")


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
        ids = [e.id_ejemplar for e in todos]
        if len(set(ids)) != len(ids):
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
