"""Mercado: la única clase que mueve polen. Cada operación es atómica y queda en el historial."""
from __future__ import annotations

from datetime import date
from itertools import count
from typing import Callable, Optional, Sequence, TypeVar

from .catalogo import Edicion, Ejemplar, Insignia
from .comunes import Azar, ErrorMercado
from .foro import Foro, Oferta, Publicacion, Subasta
from .jugador import Jugador
from .operaciones import Intercambio, Operacion, Transaccion, Venta
from . import reglas
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
        self._premio_otorgado = False  # basta saber si ya se entregó, no hace falta guardar a quién
        self._ids_sobre = count(1)  # nunca se reinicia: los ids no se reutilizan

    # --- getters: dejan leer el estado privado sin poder modificarlo
    #     (las listas se devuelven como tuplas, que son inmutables) ---

    def historial(self) -> tuple:
        return tuple(self._historial)

    def edicion(self) -> Edicion:
        return self._edicion

    def foro(self) -> Foro:
        return self._foro

    def jugadores(self) -> tuple:
        return tuple(self._jugadores)

    def polen_total(self) -> int:
        return sum(map(lambda j: j.polen(), self._jugadores))

    # --- motor: atomicidad + historial ---

    def _capturar(self) -> dict:
        return {"edicion": self._edicion,
                "premio_otorgado": self._premio_otorgado,
                "foro": self._foro._capturar(),
                "jugadores": [(j, j._capturar()) for j in self._jugadores]}

    def _restaurar(self, estado: dict) -> None:
        self._edicion = estado["edicion"]
        self._premio_otorgado = estado["premio_otorgado"]
        self._foro._restaurar(estado["foro"])
        self._jugadores = [j for j, _ in estado["jugadores"]]
        for jugador, estado_jugador in estado["jugadores"]:
            jugador._restaurar(estado_jugador)

    def _ejecutar(self, tipo: str, datos: Callable[[], dict], accion: Callable[[], T]) -> T:
        """Función de orden superior: corre `accion` de forma atómica.

        - Si falla, restaura el estado anterior: una operación inválida no deja rastros.
        - Un error de tipo inesperado (por ejemplo, None en lugar de un ejemplar) se
          informa como ErrorMercado, con el error original encadenado.
        - `datos` es una función: se evalúa recién cuando la operación salió bien,
          así armar el registro nunca falla por culpa de una entrada inválida."""
        previo = self._capturar()
        try:
            resultado = accion()
        except ErrorMercado:
            self._restaurar(previo)
            raise
        except (TypeError, AttributeError, ValueError) as error:
            self._restaurar(previo)
            raise ErrorMercado(f"Datos inválidos en {tipo}: {error}") from error
        self._historial.append(Operacion(tipo, datos(), previo))
        return resultado

    def _verificar(self, *jugadores: Jugador) -> None:
        for j in jugadores:
            if not isinstance(j, Jugador) or j not in self._jugadores:
                raise ErrorMercado(f"{j!r} no es un jugador registrado")

    # --- paso interno: ejecutar una transacción ---

    def _ejecutar_transaccion(self, transaccion: Transaccion) -> None:
        """Sirve para cualquier Transaccion (Venta, Intercambio...): el Mercado verifica
        lo que solo él sabe (quién está registrado) y cada transacción se aplica a su
        manera (polimorfismo). Después, sus ejemplares ya no pueden seguir en el foro."""
        self._verificar(*transaccion.participantes())
        transaccion.aplicar()
        for ejemplar in transaccion.ejemplares():
            self._foro._retirar_ejemplar(ejemplar)

    # --- operaciones públicas ---

    def registrar_jugador(self, jugador: Jugador) -> None:
        def accion():
            if not isinstance(jugador, Jugador):
                raise ErrorMercado(f"{jugador!r} no es un Jugador")
            if jugador in self._jugadores:
                raise ErrorMercado("El jugador ya está registrado")
            self._jugadores.append(jugador)
            jugador._acreditar(POLEN_INICIAL)
        self._ejecutar("registrar_jugador", lambda: {"jugador": jugador.nickname}, accion)

    def comprar_sobre(self, jugador: Jugador, tipo: TipoSobre) -> Sobre:
        def accion():
            self._verificar(jugador)
            jugador._cobrar(tipo.precio)
            sobre = Sobre(next(self._ids_sobre), tipo, self._edicion)
            jugador._agregar_sobre(sobre)
            return sobre
        return self._ejecutar("comprar_sobre",
                              lambda: {"jugador": jugador.nickname, "tipo": tipo.nombre}, accion)

    def abrir_sobre(self, jugador: Jugador, sobre: Sobre, azar: Azar) -> list:
        def accion():
            self._verificar(jugador)
            return jugador.abrir_sobre(sobre, azar)
        return self._ejecutar("abrir_sobre",
                              lambda: {"jugador": jugador.nickname, "sobre": sobre.id_sobre}, accion)

    def comprar_carta(self, venta: Venta) -> None:
        self._ejecutar("comprar_carta",
                       lambda: {"vendedor": venta.vendedor.nickname,
                        "comprador": venta.comprador.nickname,
                        "ejemplar": venta.ejemplar.id_ejemplar, "precio": venta.precio},
                       lambda: self._ejecutar_transaccion(venta))

    def vender_al_mercado(self, jugador: Jugador, ejemplar: Ejemplar, fecha: date) -> int:
        def accion():
            self._verificar(jugador)
            estacion = reglas.estacion_de(fecha)
            pago = reglas.precio_venta_sistema(ejemplar.carta, estacion)
            jugador._quitar(ejemplar)
            jugador._acreditar(pago)
            self._foro._retirar_ejemplar(ejemplar)
            return pago
        return self._ejecutar("vender_al_mercado",
                              lambda: {"jugador": jugador.nickname, "ejemplar": ejemplar.id_ejemplar,
                               "fecha": fecha.isoformat()}, accion)

    def intercambiar(self, intercambio: Intercambio) -> None:
        self._ejecutar("intercambiar",
                       lambda: {"emisor": intercambio.emisor.nickname,
                        "receptor": intercambio.receptor.nickname,
                        "brinda": [e.id_ejemplar for e in intercambio.brinda],
                        "recibe": [e.id_ejemplar for e in intercambio.recibe]},
                       lambda: self._ejecutar_transaccion(intercambio))

    def publicar(self, publicacion: Publicacion) -> None:
        def accion():
            self._verificar(publicacion.autor)
            self._foro.publicar(publicacion)
        self._ejecutar("publicar", lambda: {"autor": publicacion.autor.nickname,
                                    "ejemplar": publicacion.ejemplar.id_ejemplar}, accion)

    def retirar(self, publicacion: Publicacion) -> None:
        self._ejecutar("retirar", lambda: {"ejemplar": publicacion.ejemplar.id_ejemplar},
                       lambda: self._foro.retirar(publicacion))

    def aceptar_publicacion(self, publicacion: Publicacion, comprador: Jugador,
                            ofrece: Sequence[Ejemplar] = ()) -> None:
        """La publicación describe la operación (polimorfismo: una venta devuelve
        una Venta, un intercambio un Intercambio) y el Mercado la ejecuta."""
        def accion():
            if publicacion not in self._foro.publicaciones():
                raise ErrorMercado("Esa publicación no está en el foro")
            self._ejecutar_transaccion(publicacion.resolver(comprador, ofrece))
        self._ejecutar("aceptar_publicacion",
                       lambda: {"autor": publicacion.autor.nickname, "comprador": comprador.nickname,
                        "ejemplar": publicacion.ejemplar.id_ejemplar}, accion)

    def cerrar_subasta(self, subasta: Subasta, fecha: date) -> Optional[Oferta]:
        """Gana la oferta más alta cuyo jugador todavía tenga el polen."""
        def accion():
            if subasta not in self._foro.publicaciones():
                raise ErrorMercado("Esa subasta no está en el foro")
            for oferta in subasta.cerrar(fecha):
                if oferta.jugador in self._jugadores and oferta.jugador.polen() >= oferta.monto:
                    self._ejecutar_transaccion(
                        Venta(subasta.autor, oferta.jugador, subasta.ejemplar, oferta.monto))
                    return oferta
            self._foro.retirar(subasta)  # nadie pudo pagar
            return None
        return self._ejecutar("cerrar_subasta",
                              lambda: {"ejemplar": subasta.ejemplar.id_ejemplar,
                               "fecha": fecha.isoformat()}, accion)

    def reclamar_recompensa(self, jugador: Jugador, fecha: date) -> int:
        def accion():
            self._verificar(jugador)
            if jugador.polen() >= UMBRAL_RECOMPENSA:
                raise ErrorMercado(f"Solo se reclama con menos de {UMBRAL_RECOMPENSA} de polen")
            if jugador._ultima_recompensa == fecha:
                raise ErrorMercado("La recompensa de hoy ya fue reclamada")
            jugador._marcar_recompensa(fecha)
            jugador._acreditar(RECOMPENSA_DIARIA)
            return RECOMPENSA_DIARIA
        return self._ejecutar("reclamar_recompensa",
                              lambda: {"jugador": jugador.nickname, "fecha": fecha.isoformat()}, accion)

    def reclamar_premio(self, jugador: Jugador, fecha: date) -> Insignia:
        """El primero que completa la edición se lleva la insignia."""
        def accion():
            self._verificar(jugador)
            if self._premio_otorgado:
                raise ErrorMercado("La insignia de esta edición ya fue otorgada")
            if not jugador.coleccion_completa(self._edicion):
                raise ErrorMercado("La colección no está completa")
            insignia = Insignia(fecha, self._edicion)
            jugador._agregar_insignia(insignia)
            self._premio_otorgado = True
            return insignia
        return self._ejecutar("reclamar_premio",
                              lambda: {"jugador": jugador.nickname, "fecha": fecha.isoformat()}, accion)

    def reiniciar_anio(self, edicion: Edicion) -> None:
        def accion():
            for jugador in self._jugadores:
                jugador._reiniciar(POLEN_INICIAL)
            self._foro._restaurar([])
            self._edicion = edicion
            self._premio_otorgado = False
        self._ejecutar("reiniciar_anio", lambda: {"edicion": edicion.nombre}, accion)

    def borrar_jugador(self, jugador: Jugador) -> None:
        """Derecho de supresión (Ley 18.331, arts. 15 y 37).

        El jugador se borra de todos los lugares donde vive una copia de sus datos:
        la lista de jugadores, el foro y el historial (cada operación guarda una foto
        del estado). Por eso el historial se vacía y lo anterior ya no se puede
        deshacer: decidimos que la supresión pesa más que el deshacer.
        Su polen y sus cartas salen de circulación."""
        self._verificar(jugador)
        self._jugadores.remove(jugador)
        self._foro._restaurar([p for p in self._foro.publicaciones() if p.autor is not jugador])
        for publicacion in self._foro.publicaciones():
            publicacion._olvidar_jugador(jugador)  # polimorfismo: cada tipo sabe qué borrar
        self._historial.clear()

    def deshacer(self) -> Operacion:
        if not self._historial:
            raise ErrorMercado("No hay operaciones para deshacer")
        operacion = self._historial.pop()
        self._restaurar(operacion.estado_previo)
        return operacion
