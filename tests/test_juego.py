"""Tests del mercado de cartas. Cada sección protege una regla que el sistema
nunca debe violar (la lista completa está en REGLAS.md).

Correr desde la raíz del proyecto:  python3 -m pytest
"""
import json
from datetime import date

import pytest

from juego import (CARTAS_POR_SOBRE, SOBRE_COMUN, SOBRE_DORADO, SOBRE_PLATEADO, AzarFijo,
                   AzarReal, Carta, Edicion, Ejemplar, ErrorMercado, Especie, Estacion,
                   Intercambio, Jugador, Mercado, POLEN_INICIAL, PublicacionIntercambio,
                   PublicacionVenta, Rareza, Subasta, analisis, reglas)

E, R, S = Especie, Rareza, Estacion
HOY = date(2026, 11, 5)


# ---------------------------------------------------------------- preparación

@pytest.fixture
def edicion():
    return Edicion("test", (
        Carta(1, "Monstera", E.SELVA_TROPICAL, R.COMUN, S.VERANO),
        Carta(2, "Echeveria", E.DESIERTO_Y_SUCULENTAS, R.COMUN, S.INVIERNO),
        Carta(3, "Dionaea", E.PLANTAS_CARNIVORAS, R.RARA, S.VERANO),
        Carta(4, "Mburucuyá", E.MONTE_URUGUAYO, R.EPICA, S.VERANO),
        Carta(5, "Ceibo", E.MONTE_URUGUAYO, R.LEGENDARIA, S.PRIMAVERA),
        Carta(6, "Welwitschia", E.DESIERTO_Y_SUCULENTAS, R.MITICA, S.INVIERNO,
              intercambiable=False),
    ))


@pytest.fixture
def mercado(edicion):
    return Mercado(edicion)


@pytest.fixture
def ana(mercado):
    jugador = Jugador("Ana", "ana")
    mercado.registrar_jugador(jugador)
    return jugador


@pytest.fixture
def beto(mercado):
    jugador = Jugador("Beto", "beto")
    mercado.registrar_jugador(jugador)
    return jugador


def dar(jugador, carta, id_ejemplar):
    """Le da un ejemplar a un jugador sin pasar por un sobre (solo para preparar tests)."""
    ejemplar = Ejemplar(id_ejemplar, carta)
    jugador._agregar(ejemplar)
    return ejemplar


def foto(mercado):
    """Todo el estado observable, para comparar antes y después."""
    return ([j._capturar() for j in mercado.jugadores()], mercado.foro().publicaciones(),
            len(mercado.historial()))


# ---------------------------------------------------------------- R1: el polen nunca es negativo

def test_r1_no_se_puede_gastar_mas_polen_del_que_se_tiene(mercado, ana):
    mercado.comprar_sobre(ana, SOBRE_COMUN)          # 100 → 50
    with pytest.raises(ErrorMercado):
        mercado.comprar_sobre(ana, SOBRE_PLATEADO)   # cuesta 150
    assert ana.polen() == 50


def test_r1_los_getters_devuelven_copias_que_no_modifican_al_jugador(ana):
    # El polen y la colección son privados (_polen, _coleccion): desde afuera solo
    # se leen con getters, que devuelven valores que no tocan el estado real.
    coleccion = ana.coleccion()
    assert isinstance(coleccion, tuple)              # una tupla no tiene append ni remove
    with pytest.raises(AttributeError):
        coleccion.append("carta trucha")
    polen = ana.polen()
    polen += 9999                                    # cambia la variable local, no al jugador
    assert ana.polen() == POLEN_INICIAL


# ---------------------------------------------------------------- R2: una operación inválida no deja rastros

def test_r2_compra_fallida_no_cambia_nada(mercado, ana, beto):
    antes = foto(mercado)
    with pytest.raises(ErrorMercado):
        mercado.comprar_sobre(ana, SOBRE_DORADO)
    assert foto(mercado) == antes


def test_r2_intercambio_desbalanceado_no_cambia_nada(mercado, ana, beto, edicion):
    comun = dar(ana, edicion.cartas[0], 1001)
    epica = dar(beto, edicion.cartas[3], 1002)
    antes = foto(mercado)
    with pytest.raises(ErrorMercado):
        mercado.intercambiar(Intercambio(ana, beto, (comun,), (epica,)))
    assert foto(mercado) == antes


# ---------------------------------------------------------------- R3: el polen no aparece ni desaparece entre jugadores

def test_r3_una_venta_entre_jugadores_conserva_el_polen_total(mercado, ana, beto, edicion):
    ejemplar = dar(ana, edicion.cartas[2], 1001)          # rara, valor base 15
    publicacion = PublicacionVenta(ana, ejemplar, 20)
    mercado.publicar(publicacion)
    total = mercado.polen_total()
    mercado.aceptar_publicacion(publicacion, beto)
    assert mercado.polen_total() == total
    assert (ana.polen(), beto.polen()) == (POLEN_INICIAL + 20, POLEN_INICIAL - 20)


# ---------------------------------------------------------------- R4: cada ejemplar tiene un solo dueño y no se duplica

def test_r4_despues_de_una_venta_el_ejemplar_cambia_de_duenio(mercado, ana, beto, edicion):
    ejemplar = dar(ana, edicion.cartas[2], 1001)
    publicacion = PublicacionVenta(ana, ejemplar, 15)
    mercado.publicar(publicacion)
    mercado.aceptar_publicacion(publicacion, beto)
    assert beto.tiene(ejemplar) and not ana.tiene(ejemplar)
    assert mercado.foro().publicaciones() == ()


def test_r4_los_ids_de_ejemplar_nunca_se_repiten(mercado, edicion):
    rico = Jugador("Rico", "rico")
    mercado.registrar_jugador(rico)
    rico._acreditar(10_000)
    azar = AzarReal(semilla=1)
    for _ in range(50):
        mercado.abrir_sobre(rico, mercado.comprar_sobre(rico, SOBRE_COMUN), azar)
    ids = [e.id_ejemplar for e in rico.coleccion()]
    assert len(ids) == 50 * CARTAS_POR_SOBRE == len(set(ids))


# ---------------------------------------------------------------- R5: mismo azar, mismo resultado

def test_r5_misma_semilla_mismas_cartas(edicion):
    def abrir(semilla):
        from juego import Sobre
        return [e.carta.id_carta for e in Sobre(1, SOBRE_DORADO, edicion).abrir(AzarReal(semilla))]
    assert abrir(42) == abrir(42)


def test_r5_azar_fijo_da_exactamente_lo_pedido(mercado, ana):
    sobre = mercado.comprar_sobre(ana, SOBRE_COMUN)
    # cada carta: primero elige rareza (índice 0 = Común), después carta (índice 1 = Echeveria)
    cartas = mercado.abrir_sobre(ana, sobre, AzarFijo([0, 1] * CARTAS_POR_SOBRE))
    assert [e.carta.nombre for e in cartas] == ["Echeveria"] * CARTAS_POR_SOBRE


# ---------------------------------------------------------------- R6: deshacer vuelve exactamente al estado anterior

def test_r6_deshacer_una_venta(mercado, ana, beto, edicion):
    ejemplar = dar(ana, edicion.cartas[2], 1001)
    publicacion = PublicacionVenta(ana, ejemplar, 15)
    mercado.publicar(publicacion)
    antes = foto(mercado)
    mercado.aceptar_publicacion(publicacion, beto)
    mercado.deshacer()
    assert foto(mercado) == antes


def test_r6_no_hay_nada_para_deshacer_al_empezar(mercado):
    with pytest.raises(ErrorMercado):
        mercado.deshacer()


# ---------------------------------------------------------------- R7: precios y cartas no intercambiables

def test_r7_no_se_publica_por_debajo_del_valor_base(mercado, ana, edicion):
    ejemplar = dar(ana, edicion.cartas[3], 1001)    # épica, valor base 50
    with pytest.raises(ErrorMercado):
        mercado.publicar(PublicacionVenta(ana, ejemplar, 49))


def test_r7_una_carta_no_intercambiable_no_se_publica(mercado, ana, edicion):
    mitica = dar(ana, edicion.cartas[5], 1001)
    with pytest.raises(ErrorMercado):
        mercado.publicar(PublicacionVenta(ana, mitica, 10_000))


def test_r7_una_carta_no_intercambiable_si_se_puede_vender_al_mercado(mercado, ana, edicion):
    mitica = dar(ana, edicion.cartas[5], 1001)
    pago = mercado.vender_al_mercado(ana, mitica, date(2026, 7, 1))   # invierno: en temporada
    assert pago == int(800 * 1.5 * 0.4)
    assert not ana.tiene(mitica)


# ---------------------------------------------------------------- R8: los intercambios son balanceados

def test_r8_tres_comunes_por_una_rara(mercado, ana, beto, edicion):
    comunes = tuple(dar(ana, edicion.cartas[i % 2], 1000 + i) for i in range(3))
    rara = dar(beto, edicion.cartas[2], 2000)
    mercado.intercambiar(Intercambio(ana, beto, comunes, (rara,)))
    assert ana.tiene(rara) and all(beto.tiene(c) for c in comunes)


def test_r8_no_se_puede_intercambiar_el_mismo_ejemplar_dos_veces(mercado, ana, beto, edicion):
    comun = dar(ana, edicion.cartas[0], 1001)
    rara = dar(beto, edicion.cartas[2], 2000)
    with pytest.raises(ErrorMercado):
        mercado.intercambiar(Intercambio(ana, beto, (comun, comun, comun), (rara,)))


# ---------------------------------------------------------------- R9: no hay máquina de dinero

@pytest.mark.parametrize("tipo", [SOBRE_COMUN, SOBRE_PLATEADO, SOBRE_DORADO])
def test_r9_vender_todo_al_mercado_nunca_recupera_el_precio(tipo):
    peor_caso = (reglas.valor_esperado_sobre(tipo, CARTAS_POR_SOBRE)
                 * reglas.FRACCION_SISTEMA * reglas.MULTIPLICADOR_TEMPORADA)
    assert peor_caso < tipo.precio


def test_r9_la_recompensa_diaria_es_una_por_dia_y_solo_con_poco_polen(mercado, ana):
    with pytest.raises(ErrorMercado):
        mercado.reclamar_recompensa(ana, HOY)        # tiene 100
    mercado.comprar_sobre(ana, SOBRE_COMUN)          # queda con 50
    ana._cobrar(1)                                   # 49: ya puede reclamar
    assert mercado.reclamar_recompensa(ana, HOY) > 0
    ana._cobrar(ana.polen())                           # vuelve a estar por debajo del umbral
    with pytest.raises(ErrorMercado):
        mercado.reclamar_recompensa(ana, HOY)        # pero ya reclamó hoy


# ---------------------------------------------------------------- R10: probabilidades transparentes y coherentes

@pytest.mark.parametrize("tipo", [SOBRE_COMUN, SOBRE_PLATEADO, SOBRE_DORADO])
def test_r10_las_probabilidades_suman_uno_y_no_son_negativas(tipo):
    assert abs(sum(tipo.probabilidades.values()) - 1) < 1e-9
    assert all(p >= 0 for p in tipo.probabilidades.values())


def test_r10_mejor_sobre_mas_chance_de_epica_o_mejor():
    def epica_o_mejor(tipo):
        return sum(tipo.probabilidades[r] for r in (R.EPICA, R.LEGENDARIA, R.MITICA))
    assert epica_o_mejor(SOBRE_COMUN) < epica_o_mejor(SOBRE_PLATEADO) < epica_o_mejor(SOBRE_DORADO)


def test_r10_las_frecuencias_simuladas_coinciden_con_la_tabla(edicion):
    frecuencias = analisis.frecuencia_rarezas(SOBRE_DORADO, edicion, AzarReal(5), sobres=20_000)
    for rareza, esperada in SOBRE_DORADO.probabilidades.items():
        assert abs(frecuencias.get(rareza, 0) - esperada) < 0.01


def test_r10_las_probabilidades_no_se_pueden_modificar():
    with pytest.raises(TypeError):
        SOBRE_COMUN.probabilidades[R.MITICA] = 0.5


# ---------------------------------------------------------------- R11: el premio se entrega una sola vez por edición

def test_r11_premio_unico_y_las_insignias_sobreviven_al_reinicio(mercado, ana, beto, edicion):
    for i, carta in enumerate(edicion.cartas):
        dar(ana, carta, 5000 + i)
        dar(beto, carta, 6000 + i)
    insignia = mercado.reclamar_premio(ana, HOY)
    with pytest.raises(ErrorMercado):
        mercado.reclamar_premio(beto, HOY)
    mercado.reiniciar_anio(Edicion("siguiente", edicion.cartas))
    assert ana.insignias() == (insignia,)
    assert ana.coleccion() == () and ana.polen() == POLEN_INICIAL


# ---------------------------------------------------------------- R12: estaciones del hemisferio sur

@pytest.mark.parametrize("fecha, estacion", [
    (date(2026, 1, 15), S.VERANO), (date(2026, 4, 1), S.OTONO),
    (date(2026, 7, 9), S.INVIERNO), (date(2026, 10, 20), S.PRIMAVERA),
])
def test_r12_estacion_segun_la_fecha(fecha, estacion):
    assert reglas.estacion_de(fecha) == estacion


# ---------------------------------------------------------------- R13: las funciones puras no modifican lo que reciben

def test_r13_contar_y_repetidos_no_mutan_y_repiten_resultado(edicion):
    coleccion = [Ejemplar(1, edicion.cartas[0]), Ejemplar(2, edicion.cartas[0]),
                 Ejemplar(3, edicion.cartas[1])]
    copia = list(coleccion)
    assert analisis.contar_por_carta(coleccion) == {1: 2, 2: 1}
    assert analisis.repetidos(coleccion) == (coleccion[1],)
    assert analisis.repetidos(coleccion) == analisis.repetidos(coleccion)
    assert coleccion == copia


def test_r13_reduce_con_lista_vacia_no_falla():
    assert analisis.contar_por_carta([]) == {}
    assert analisis.repetidos([]) == ()


# ---------------------------------------------------------------- R14: entradas hostiles no rompen el sistema

HOSTILES = [None, -5, "abc", 3.5, True, [], 10**30 * -1]


@pytest.mark.parametrize("precio", HOSTILES)
def test_r14_precio_invalido_en_venta(ana, edicion, precio):
    ejemplar = dar(ana, edicion.cartas[2], 1001)
    with pytest.raises(ErrorMercado):
        PublicacionVenta(ana, ejemplar, precio)


@pytest.mark.parametrize("monto", HOSTILES)
def test_r14_oferta_invalida_en_subasta(mercado, ana, beto, edicion, monto):
    ejemplar = dar(ana, edicion.cartas[2], 1001)
    subasta = Subasta(ana, ejemplar, 15, date(2026, 12, 1))
    with pytest.raises(ErrorMercado):
        subasta.ofertar(beto, monto, HOY)


@pytest.mark.parametrize("jugador", [None, "ana", 42])
def test_r14_operar_con_algo_que_no_es_jugador(mercado, jugador):
    antes = foto(mercado)
    with pytest.raises(ErrorMercado):
        mercado.comprar_sobre(jugador, SOBRE_COMUN)
    assert foto(mercado) == antes


@pytest.mark.parametrize("ejemplar, fecha", [(None, HOY), ("carta", HOY), ("REAL", "hoy"), ("REAL", None)])
def test_r14_vender_al_mercado_con_datos_invalidos(mercado, ana, edicion, ejemplar, fecha):
    real = dar(ana, edicion.cartas[0], 1001)
    antes = foto(mercado)
    with pytest.raises(ErrorMercado):
        mercado.vender_al_mercado(ana, real if ejemplar == "REAL" else ejemplar, fecha)
    assert foto(mercado) == antes


@pytest.mark.parametrize("cosa", [None, "beto", 3.14])
def test_r14_registrar_algo_que_no_es_jugador(mercado, cosa):
    with pytest.raises(ErrorMercado):
        mercado.registrar_jugador(cosa)
    assert mercado.jugadores() == () and mercado.historial() == ()


# ---------------------------------------------------------------- R15: polimorfismo de publicaciones

def test_r15_intercambio_por_el_foro(mercado, ana, beto, edicion):
    mia = dar(ana, edicion.cartas[0], 1001)
    suya = dar(beto, edicion.cartas[1], 2001)
    publicacion = PublicacionIntercambio(ana, mia, busca="cualquier común")
    mercado.publicar(publicacion)
    mercado.aceptar_publicacion(publicacion, beto, [suya])
    assert ana.tiene(suya) and beto.tiene(mia)


def test_r15_una_subasta_no_se_acepta_directo(mercado, ana, beto, edicion):
    ejemplar = dar(ana, edicion.cartas[2], 1001)
    subasta = Subasta(ana, ejemplar, 15, date(2026, 12, 1))
    mercado.publicar(subasta)
    with pytest.raises(ErrorMercado):
        mercado.aceptar_publicacion(subasta, beto)


def test_r15_gana_la_oferta_mas_alta_que_todavia_puede_pagar(mercado, ana, beto, edicion):
    carla = Jugador("Carla", "carla")
    mercado.registrar_jugador(carla)
    ejemplar = dar(ana, edicion.cartas[2], 1001)
    subasta = Subasta(ana, ejemplar, 15, date(2026, 12, 1))
    mercado.publicar(subasta)
    subasta.ofertar(beto, 30, HOY)
    subasta.ofertar(carla, 90, HOY)
    carla._cobrar(carla.polen())                       # Carla se queda sin polen antes del cierre
    ganadora = mercado.cerrar_subasta(subasta, date(2026, 12, 1))
    assert ganadora.jugador is beto and beto.tiene(ejemplar)


# ---------------------------------------------------------------- R16: derecho de supresión

def test_r16_borrar_jugador_lo_quita_de_todos_lados(mercado, ana, beto, edicion):
    ejemplar = dar(beto, edicion.cartas[2], 1001)
    subasta = Subasta(beto, ejemplar, 15, date(2026, 12, 1))
    mercado.publicar(subasta)
    subasta.ofertar(ana, 20, HOY)
    mercado.publicar(PublicacionVenta(ana, dar(ana, edicion.cartas[3], 1002), 50))

    mercado.borrar_jugador(ana)

    assert ana not in mercado.jugadores()
    assert all(p.autor is not ana for p in mercado.foro().publicaciones())
    assert all(o.jugador is not ana for o in subasta.ofertas())
    assert mercado.historial() == ()                   # las fotos del estado también la contenían


# ---------------------------------------------------------------- R17: el historial se puede verificar afuera del programa

def test_r17_el_registro_se_guarda_y_se_lee_en_json(mercado, ana, beto, tmp_path):
    mercado.comprar_sobre(ana, SOBRE_COMUN)
    registro = analisis.registro_operaciones(mercado.historial())
    archivo = tmp_path / "registro.json"
    archivo.write_text(json.dumps(registro, ensure_ascii=False), encoding="utf-8")
    leido = json.loads(archivo.read_text(encoding="utf-8"))
    assert leido == registro
    assert analisis.contar_por_tipo(leido) == {"registrar_jugador": 2, "comprar_sobre": 1}
