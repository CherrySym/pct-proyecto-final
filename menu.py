from datetime import date, timedelta
from pathlib import Path

from juego import (CARTAS_POR_SOBRE, SOBRE_COMUN, SOBRE_DORADO, SOBRE_PLATEADO, AzarReal, ErrorMercado,
                   Especie, Jugador, Mercado, PublicacionIntercambio, PublicacionVenta,
                   Rareza, Subasta, analisis, reglas)
from programa import edicion_demo, guardar_registro

TIPOS_DE_SOBRE = [SOBRE_COMUN, SOBRE_PLATEADO, SOBRE_DORADO]
ARCHIVO_REGISTRO = Path("registro_menu.json")


class Salir(Exception):
    """El usuario pidió salir (opción 0, Ctrl+C o Ctrl+D)."""


# ---------------------------------------------------------------- pedir datos

def pedir(mensaje: str) -> str:
    try:
        return input(mensaje).strip()
    except (EOFError, KeyboardInterrupt):
        raise Salir() from None


def pedir_numero(mensaje: str, minimo: int = 0, por_defecto=None) -> int:
    texto = pedir(mensaje)
    if texto == "" and por_defecto is not None:
        return por_defecto
    if not texto.isdigit() or int(texto) < minimo:
        raise ErrorMercado(f"Tiene que ser un número entero mayor o igual a {minimo}")
    return int(texto)


def elegir(opciones, describir, mensaje: str = "Número: "):
    """Muestra una lista numerada y devuelve el elemento elegido."""
    opciones = list(opciones)
    if not opciones:
        raise ErrorMercado("No hay nada para elegir")
    for i, opcion in enumerate(opciones, start=1):
        print(f"  {i}. {describir(opcion)}")
    numero = pedir_numero(mensaje, minimo=1)
    if numero > len(opciones):
        raise ErrorMercado("Ese número no está en la lista")
    return opciones[numero - 1]


def elegir_varios(opciones, describir) -> tuple:
    """Como elegir, pero acepta varios números separados por coma (ej: 1,3)."""
    opciones = list(opciones)
    if not opciones:
        raise ErrorMercado("No hay nada para elegir")
    for i, opcion in enumerate(opciones, start=1):
        print(f"  {i}. {describir(opcion)}")
    partes = [p.strip() for p in pedir("Números separados por coma: ").split(",")]
    if not all(p.isdigit() and 1 <= int(p) <= len(opciones) for p in partes):
        raise ErrorMercado("Hay números que no están en la lista")
    if len(set(partes)) != len(partes):
        raise ErrorMercado("Elegiste el mismo número dos veces")
    return tuple(opciones[int(p) - 1] for p in partes)


# ---------------------------------------------------------------- mostrar cosas

def ejemplar_texto(ejemplar) -> str:
    carta = ejemplar.carta
    extra = "" if carta.intercambiable else ", no intercambiable"
    return f"#{ejemplar.id_ejemplar} {carta.nombre} ({carta.rareza.value}{extra})"


def publicacion_texto(pub) -> str:
    """Cada tipo de publicación se muestra a su manera."""
    base = f"{ejemplar_texto(pub.ejemplar)} de {pub.autor.nickname}"
    if isinstance(pub, Subasta):
        mejor = max((o.monto for o in pub.ofertas()), default=None)
        oferta = f"mejor oferta {mejor}" if mejor is not None else "sin ofertas"
        return f"[Subasta] {base} - mínimo {pub.precio_minimo}, {oferta}, cierra {pub.cierre:%d/%m}"
    if isinstance(pub, PublicacionIntercambio):
        busca = f" - busca: {pub.busca}" if pub.busca else ""
        return f"[Intercambio] {base} (vale {reglas.valor_intercambio(pub.ejemplar.carta.rareza)}){busca}"
    return f"[Venta] {base} - {pub.precio_de_referencia()} de polen"


# ---------------------------------------------------------------- la partida

class Partida:
    """Junta lo que el menú necesita recordar: el mercado, quién juega y qué día es."""

    def __init__(self, semilla: int):
        self.azar = AzarReal(semilla)
        self.fecha = date.today()
        self.edicion = edicion_demo()
        self.mercado = Mercado(self.edicion)
        for nombre, nickname in (("Ana", "ana_flora"), ("Beto", "beto_cactus")):
            self.mercado.registrar_jugador(Jugador(nombre, nickname))
        self.actual = self.mercado.jugadores()[0]

    def estacion(self):
        return reglas.estacion_de(self.fecha)

    def panel(self) -> str:
        j = self.actual
        insignias = f" | Insignias: {len(j.insignias())}" if j.insignias() else ""
        return (f"{self.fecha:%d/%m/%Y} ({self.estacion().value}) | Jugador: {j.nickname} | "
                f"Polen: {j.polen()} | Sobres: {len(j.sobres())} | "
                f"Colección: {analisis.progreso(j.coleccion(), self.edicion):.0%}{insignias}")


# ---------------------------------------------------------------- acciones: sobres

def comprar_sobre(p: Partida) -> None:
    tipo = elegir(TIPOS_DE_SOBRE, lambda t: f"{t.nombre} ({t.precio} de polen)")
    sobre = p.mercado.comprar_sobre(p.actual, tipo)
    print(f"Compraste el sobre {tipo.nombre} #{sobre.id_sobre}.")


def abrir_sobre(p: Partida) -> None:
    sobre = elegir(p.actual.sobres(), lambda s: f"Sobre {s.tipo.nombre} #{s.id_sobre}")
    for ejemplar in p.mercado.abrir_sobre(p.actual, sobre, p.azar):
        print("  Sacaste " + ejemplar_texto(ejemplar))


def ver_probabilidades(p: Partida) -> None:
    """Las probabilidades son públicas (R10 y ETICA.md)."""
    for tipo in TIPOS_DE_SOBRE:
        esperado = reglas.valor_esperado_sobre(tipo, CARTAS_POR_SOBRE)
        print(f"\nSobre {tipo.nombre} - {tipo.precio} de polen (valor esperado {esperado:.1f})")
        for rareza, prob in tipo.probabilidades.items():
            print(f"  {rareza.value:<11} {prob:>7.1%}")


# ---------------------------------------------------------------- acciones: colección

def ver_coleccion(p: Partida) -> None:
    coleccion = p.actual.coleccion()
    if not coleccion:
        print("Todavía no tenés cartas. Comprá y abrí un sobre.")
        return
    for ejemplar in coleccion:
        precio = reglas.precio(ejemplar.carta, p.estacion())
        print(f"  {ejemplar_texto(ejemplar)} - vale {precio}")
    print(f"Valor total hoy: {analisis.valor_coleccion(coleccion, p.estacion())} de polen")
    faltan = [c.nombre for c in analisis.cartas_faltantes(coleccion, p.edicion)]
    print("Te faltan:", ", ".join(faltan) if faltan else "nada, ¡colección completa!")
    repetidas = analisis.repetidos(coleccion)
    if repetidas:
        print("Repetidas:", ", ".join(ejemplar_texto(e) for e in repetidas))


def vender_al_mercado(p: Partida) -> None:
    def con_pago(e):
        return f"{ejemplar_texto(e)} - el mercado paga {reglas.precio_venta_sistema(e.carta, p.estacion())}"
    ejemplar = elegir(p.actual.coleccion(), con_pago)
    pago = p.mercado.vender_al_mercado(p.actual, ejemplar, p.fecha)
    print(f"El mercado te pagó {pago} de polen.")


def reclamar_premio(p: Partida) -> None:
    insignia = p.mercado.reclamar_premio(p.actual, p.fecha)
    print(f"¡Completaste la edición {insignia.edicion.nombre}! Ganaste la insignia.")


def reclamar_recompensa(p: Partida) -> None:
    monto = p.mercado.reclamar_recompensa(p.actual, p.fecha)
    print(f"Recibiste {monto} de polen.")


# ---------------------------------------------------------------- acciones: foro

def ver_foro(p: Partida) -> None:
    publicaciones = p.mercado.foro().publicaciones()
    if not publicaciones:
        print("El foro está vacío.")
    for pub in publicaciones:
        print("  " + publicacion_texto(pub))


def buscar_en_foro(p: Partida) -> None:
    """Arma un criterio combinando filtros (funciones de orden superior de analisis.py)."""
    criterios = []
    if pedir("¿Solo cartas que te faltan? (s/n): ").lower() == "s":
        criterios.append(analisis.faltantes_para(p.actual.coleccion(), p.edicion))
    maximo = pedir("Precio máximo (Enter = sin límite): ")
    if maximo:
        if not maximo.isdigit():
            raise ErrorMercado("El precio máximo tiene que ser un número")
        criterios.append(analisis.precio_hasta(int(maximo)))
    if pedir("¿Filtrar por rareza? (s/n): ").lower() == "s":
        criterios.append(analisis.de_rareza(elegir(Rareza, lambda r: r.value)))
    if pedir("¿Filtrar por especie? (s/n): ").lower() == "s":
        criterios.append(analisis.de_especie(elegir(Especie, lambda e: e.value)))
    encontradas = list(p.mercado.foro().buscar(analisis.todos(*criterios)))
    print(f"\n{len(encontradas)} publicación(es):")
    for pub in encontradas:
        print("  " + publicacion_texto(pub))


def publicar_venta(p: Partida) -> None:
    ejemplar = elegir(p.actual.coleccion(), ejemplar_texto)
    minimo = reglas.valor_base(ejemplar.carta.rareza)
    sugerido = reglas.precio(ejemplar.carta, p.estacion())
    precio = pedir_numero(f"Precio (mínimo {minimo}, Enter = {sugerido}): ", por_defecto=sugerido)
    p.mercado.publicar(PublicacionVenta(p.actual, ejemplar, precio))
    print("Publicada.")


def publicar_intercambio(p: Partida) -> None:
    ejemplar = elegir(p.actual.coleccion(), ejemplar_texto)
    busca = pedir("¿Qué buscás a cambio? (texto libre, opcional): ")
    p.mercado.publicar(PublicacionIntercambio(p.actual, ejemplar, busca))
    print(f"Publicada. Vale {reglas.valor_intercambio(ejemplar.carta.rareza)} en intercambios: "
          "quien la quiera tiene que ofrecer cartas que sumen lo mismo.")


def publicar_subasta(p: Partida) -> None:
    ejemplar = elegir(p.actual.coleccion(), ejemplar_texto)
    minimo_permitido = reglas.valor_base(ejemplar.carta.rareza)
    minimo = pedir_numero(f"Precio mínimo (al menos {minimo_permitido}): ")
    dias = pedir_numero("¿Cuántos días dura? (Enter = 1): ", minimo=1, por_defecto=1)
    p.mercado.publicar(Subasta(p.actual, ejemplar, minimo, p.fecha + timedelta(days=dias)))
    print(f"Subasta publicada. Cierra el {p.fecha + timedelta(days=dias):%d/%m}.")


def ajenas(p: Partida, tipo) -> list:
    return [pub for pub in p.mercado.foro().publicaciones()
            if isinstance(pub, tipo) and pub.autor is not p.actual]


def comprar_del_foro(p: Partida) -> None:
    pub = elegir(ajenas(p, PublicacionVenta), publicacion_texto)
    p.mercado.aceptar_publicacion(pub, p.actual)
    print("¡Compra hecha!")


def aceptar_intercambio(p: Partida) -> None:
    pub = elegir(ajenas(p, PublicacionIntercambio), publicacion_texto)
    objetivo = reglas.valor_intercambio(pub.ejemplar.carta.rareza)
    print(f"Elegí cartas tuyas que sumen {objetivo}:")

    def con_valor(e):
        return f"{ejemplar_texto(e)} - vale {reglas.valor_intercambio(e.carta.rareza)}"
    ofrece = elegir_varios(p.actual.coleccion(), con_valor)
    p.mercado.aceptar_publicacion(pub, p.actual, ofrece)
    print("¡Intercambio hecho!")


def ofertar_en_subasta(p: Partida) -> None:
    subasta = elegir(ajenas(p, Subasta), publicacion_texto)
    monto = pedir_numero("¿Cuánto ofertás?: ", minimo=1)
    subasta.ofertar(p.actual, monto, p.fecha)
    print("Oferta registrada. El polen se cobra recién cuando cierra la subasta.")


def cerrar_subasta(p: Partida) -> None:
    propias = [pub for pub in p.mercado.foro().publicaciones()
               if isinstance(pub, Subasta) and pub.autor is p.actual]
    subasta = elegir(propias, publicacion_texto)
    ganadora = p.mercado.cerrar_subasta(subasta, p.fecha)
    if ganadora is None:
        print("Nadie pudo pagar: la subasta se retiró y la carta sigue siendo tuya.")
    else:
        print(f"La ganó {ganadora.jugador.nickname} con {ganadora.monto} de polen.")


def retirar_publicacion(p: Partida) -> None:
    propias = [pub for pub in p.mercado.foro().publicaciones() if pub.autor is p.actual]
    p.mercado.retirar(elegir(propias, publicacion_texto))
    print("Publicación retirada.")


# ---------------------------------------------------------------- acciones: historial

def ver_historial(p: Partida) -> None:
    registro = analisis.registro_operaciones(p.mercado.historial())
    if not registro:
        print("El historial está vacío.")
    for r in registro:
        datos = ", ".join(f"{k}={v}" for k, v in r["datos"].items())
        print(f"  {r['numero']:>3}. {r['tipo']} ({datos})")


def deshacer(p: Partida) -> None:
    historial = p.mercado.historial()
    if historial and historial[-1].tipo == "registrar_jugador" and len(p.mercado.jugadores()) == 1:
        raise ErrorMercado("No se puede deshacer: el juego quedaría sin jugadores")
    operacion = p.mercado.deshacer()
    print(f"Se deshizo: {operacion.tipo}")
    if p.actual not in p.mercado.jugadores():  # se deshizo el registro del jugador actual
        p.actual = p.mercado.jugadores()[0]
        print(f"Ahora juega {p.actual.nickname}.")


def guardar_json(p: Partida) -> None:
    registro = analisis.registro_operaciones(p.mercado.historial())
    guardar_registro(registro, ARCHIVO_REGISTRO)
    print(f"Guardado en {ARCHIVO_REGISTRO}: {analisis.contar_por_tipo(registro)}")


# ---------------------------------------------------------------- acciones: jugadores y tiempo

def cambiar_jugador(p: Partida) -> None:
    p.actual = elegir(p.mercado.jugadores(), lambda j: f"{j.nickname} ({j.polen()} de polen)")


def registrar_jugador(p: Partida) -> None:
    nombre = pedir("Nombre: ")
    nickname = pedir("Nickname: ")
    if any(j.nickname == nickname for j in p.mercado.jugadores()):
        raise ErrorMercado("Ese nickname ya está en uso")
    jugador = Jugador(nombre, nickname)
    p.mercado.registrar_jugador(jugador)
    p.actual = jugador
    print(f"Bienvenido/a, {nickname}. Empezás con {jugador.polen()} de polen.")


def borrar_jugador(p: Partida) -> None:
    """Derecho de supresión (Ley 18.331). Borra al jugador de todos lados y vacía el historial."""
    if len(p.mercado.jugadores()) == 1:
        raise ErrorMercado("Tiene que quedar al menos un jugador")
    jugador = elegir(p.mercado.jugadores(), lambda j: j.nickname)
    if pedir(f"Se borra {jugador.nickname} y el historial ya no se podrá deshacer. ¿Seguro? (s/n): ").lower() != "s":
        print("Cancelado.")
        return
    p.mercado.borrar_jugador(jugador)
    if p.actual is jugador:
        p.actual = p.mercado.jugadores()[0]
    print(f"{jugador.nickname} fue borrado.")


def avanzar_dia(p: Partida) -> None:
    p.fecha += timedelta(days=1)
    print(f"Ahora es {p.fecha:%d/%m/%Y} ({p.estacion().value}).")


# ---------------------------------------------------------------- menú

SECCIONES = [
    ("Sobres", [("Comprar sobre", comprar_sobre),
                ("Abrir sobre", abrir_sobre),
                ("Ver probabilidades de los sobres", ver_probabilidades)]),
    ("Colección", [("Ver mi colección", ver_coleccion),
                   ("Vender una carta al mercado", vender_al_mercado),
                   ("Reclamar recompensa diaria", reclamar_recompensa),
                   ("Reclamar insignia (colección completa)", reclamar_premio)]),
    ("Foro", [("Ver foro", ver_foro),
              ("Buscar en el foro", buscar_en_foro),
              ("Publicar en venta", publicar_venta),
              ("Publicar para intercambio", publicar_intercambio),
              ("Publicar en subasta", publicar_subasta),
              ("Comprar una venta", comprar_del_foro),
              ("Aceptar un intercambio", aceptar_intercambio),
              ("Ofertar en una subasta", ofertar_en_subasta),
              ("Cerrar una subasta mía", cerrar_subasta),
              ("Retirar una publicación mía", retirar_publicacion)]),
    ("Historial", [("Ver historial", ver_historial),
                   ("Deshacer última operación", deshacer),
                   ("Guardar historial en JSON", guardar_json)]),
    ("Jugadores y tiempo", [("Cambiar de jugador", cambiar_jugador),
                            ("Registrar jugador nuevo", registrar_jugador),
                            ("Borrar jugador (Ley 18.331)", borrar_jugador),
                            ("Avanzar un día", avanzar_dia)]),
]

# Opción número -> función. Las opciones se numeran solas en el orden de SECCIONES.
ACCIONES = [accion for _, opciones in SECCIONES for _, accion in opciones]


def mostrar_menu(p: Partida) -> None:
    print("\n" + "=" * 70)
    print(p.panel())
    print("=" * 70)
    numero = 1
    for titulo, opciones in SECCIONES:
        print(f"{titulo}:")
        for texto, _ in opciones:
            print(f"  {numero:>2}. {texto}")
            numero += 1
    print("   0. Salir")


def main() -> None:
    print("Mercado de cartas de plantas")
    try:
        semilla = pedir_numero("Semilla para el azar (Enter = 42): ", por_defecto=42)
    except ErrorMercado:
        print("Semilla inválida, se usa 42.")
        semilla = 42
    except Salir:
        return
    partida = Partida(semilla)

    while True:
        mostrar_menu(partida)
        try:
            opcion = pedir("> ")
            if opcion == "0":
                break
            if not opcion.isdigit() or not 1 <= int(opcion) <= len(ACCIONES):
                print("Opción inválida.")
                continue
            print()
            try:
                ACCIONES[int(opcion) - 1](partida)
            except ErrorMercado as error:
                # El Mercado ya dejó todo como estaba (R2): solo hay que avisar.
                print("Rechazado:", error)
            pedir("\n(Enter para seguir)")
        except Salir:
            break

    print("\n¡Hasta la próxima!")


if __name__ == "__main__":
    main()
