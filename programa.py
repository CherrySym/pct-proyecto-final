"""Demo del mercado de cartas. El código del juego está en el paquete juego/."""
from juego import (SOBRE_COMUN, SOBRE_DORADO, AzarReal, Carta, Edicion, ErrorMercado,
                   Especie, Estacion, Jugador, Mercado, Rareza)


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
