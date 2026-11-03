"""Mercado de cartas coleccionables de plantas.

Archivos del paquete (en orden de dependencia):
- comunes.py     ErrorMercado, enumeraciones (Rareza, Especie, Estacion,
                 TipoPublicacion) y azar (Azar, AzarReal, AzarFijo)
- catalogo.py    Carta, Edicion, Ejemplar, Insignia
- sobres.py      TipoSobre, Sobre y los tres sobres del juego
- reglas.py      ReglasEconomia (funciones puras)
- jugador.py     Jugador
- operaciones.py Venta, Intercambio, Operacion
- foro.py        Publicacion, Subasta, Oferta, Foro
- mercado.py     Mercado

Reglas generales:
- La única clase que crea, quema o mueve polen es Mercado.
- Toda operación del Mercado se ejecuta con `_ejecutar`: si falla a la mitad,
  se restaura el estado anterior (no deja rastros) y, si sale bien, se guarda
  en el historial para poder deshacerla.
- El azar entra por la interfaz Azar, así que con el mismo AzarFijo (o la
  misma semilla) el resultado es siempre el mismo.
"""
from .catalogo import Carta, Edicion, Ejemplar, Insignia
from .comunes import Azar, AzarFijo, AzarReal, ErrorMercado, Especie, Estacion, Rareza, TipoPublicacion
from .foro import Foro, Oferta, Publicacion, Subasta
from .jugador import Jugador
from .mercado import POLEN_INICIAL, RECOMPENSA_DIARIA, UMBRAL_RECOMPENSA, Mercado
from .operaciones import Intercambio, Operacion, Venta
from .reglas import ReglasEconomia
from .sobres import CARTAS_POR_SOBRE, SOBRE_COMUN, SOBRE_DORADO, SOBRE_PLATEADO, Sobre, TipoSobre
