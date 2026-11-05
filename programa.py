"""Demo del mercado de cartas. El código del juego está en el paquete juego/.

Este archivo es el "borde impuro": acá viven los efectos (azar real, fecha de hoy
y pantalla). Toda la lógica está en el paquete y no imprime nada."""
import json
from datetime import date
from pathlib import Path

from juego import (SOBRE_COMUN, SOBRE_DORADO, AzarReal, Carta, Edicion, ErrorMercado,
                   Especie, Estacion, Jugador, Mercado, PublicacionVenta, Rareza,
                   ReglasEconomia, analisis)


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


ARCHIVO_REGISTRO = Path("registro_historial.json")


def guardar_registro(registro: list, ruta: Path) -> None:
    """Efecto: escribe en disco. Siempre UTF-8, nunca el encoding por defecto del sistema."""
    ruta.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")


def leer_registro(ruta: Path) -> list:
    return json.loads(ruta.read_text(encoding="utf-8"))


def main() -> None:
    azar = AzarReal(semilla=42)  # semilla fija: la demo da siempre lo mismo
    hoy = date.today()
    edicion = edicion_demo()
    mercado = Mercado(edicion)
    ana = Jugador("Ana", "ana_flora")
    beto = Jugador("Beto", "beto_cactus")
    mercado.registrar_jugador(ana)
    mercado.registrar_jugador(beto)

    # Abrir un sobre
    sobre = mercado.comprar_sobre(ana, SOBRE_COMUN)
    for ej in mercado.abrir_sobre(ana, sobre, azar):
        print(f"Ana sacó #{ej.id_ejemplar}: {ej.carta.nombre} ({ej.carta.rareza.value})")
    print(f"Progreso de Ana: {analisis.progreso(ana.coleccion, edicion):.0%}")
    print("Repetidas para vender:", [e.carta.nombre for e in analisis.repetidos(ana.coleccion)])

    # Publicar una repetida y buscarla en el foro con criterios combinados
    repetida = analisis.repetidos(ana.coleccion)[0]
    precio = ReglasEconomia.valor_base(repetida.carta.rareza)
    mercado.publicar(PublicacionVenta(ana, repetida, precio))
    criterio = analisis.todos(analisis.faltantes_para(beto.coleccion, edicion),
                              analisis.precio_hasta(10))
    encontradas = list(mercado.foro.buscar(criterio))
    print(f"Beto encuentra {len(encontradas)} publicación(es) que le sirven")
    mercado.aceptar_publicacion(encontradas[0], beto)
    print(ana, beto, "| polen total:", mercado.polen_total())

    # Una operación inválida no deja rastros
    try:
        mercado.comprar_sobre(beto, SOBRE_DORADO)
    except ErrorMercado as e:
        print("Rechazado:", e, "|", beto)

    # Deshacer: vuelve atrás la compra de la Monstera (la compra fallida nunca entró al historial)
    mercado.deshacer()
    print("Después de deshacer:", ana, beto)

    # Guardar el historial en JSON: lo ocurrido queda verificable fuera del programa
    guardar_registro(analisis.registro_operaciones(mercado.historial), ARCHIVO_REGISTRO)
    print(f"Registro guardado en {ARCHIVO_REGISTRO}:",
          analisis.contar_por_tipo(leer_registro(ARCHIVO_REGISTRO)))

    # Simulación perezosa: cuántos sobres hacen falta para completar la edición
    estacion = ReglasEconomia.estacion_de(hoy)
    print(f"Estación de hoy: {estacion.value}")
    n = analisis.sobres_hasta_completar(SOBRE_COMUN, edicion, AzarReal(semilla=1))
    print(f"Con sobres comunes, completar la edición llevó {n} sobres en esta simulación")


if __name__ == "__main__":
    main()
