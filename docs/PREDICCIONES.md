# Predicciones

Antes de ejecutar cada función clave anotamos qué esperábamos que devolviera, leyendo solo el código. Después la ejecutamos y comparamos.

## 1. Reglas de precio (`reglas.py`)

| # | Llamada | Predicción | Resultado | ¿Coincide? |
|---|---------|------------|-----------|------------|
| 1 | `precio(Ceibo, PRIMAVERA)` | 300 (legendaria 200 × 1.5 por ser su estación) | 300 | Sí |
| 2 | `precio_venta_sistema(Ceibo, PRIMAVERA)` | 120 (`int(300 × 0.4)`) | 120 | Sí |
| 3 | `precio(Dionaea, VERANO)` | 22 (15 × 1.5 = 22.5; `round` de Python redondea al par) | 22 | Sí |
| 4 | `estacion_de` para 17/11, 10/01 y 21/06 | PRIMAVERA, VERANO, INVIERNO (hemisferio sur) | PRIMAVERA, VERANO, INVIERNO | Sí |
| 5 | `valor_esperado_sobre` de Común, Plateado y Dorado (5 cartas) | 56.75, 146.0, 535.0 | 56.75000000000001, 146.0, 535.0 | Sí, salvo el error de coma flotante |

**Qué aprendimos:**
- En el punto 3, a primera vista uno diría 23. Python usa redondeo bancario: `round(22.5)` da 22 y `round(7.5)` da 8. No rompe ninguna regla, pero hay que saberlo para explicar los precios.
- En el punto 5, el valor esperado del sobre común (56.75) supera su precio (50). Igual no es una "máquina de dinero" (R9): al mercado se le vende al 40 %, o sea que un sobre común devuelve en promedio unos 22 de polen.

## 2. Sobres y azar (`sobres.py`)

| # | Llamada | Predicción | Resultado | ¿Coincide? |
|---|---------|------------|-----------|------------|
| 6 | `Sobre(3, SOBRE_COMUN, ed).abrir(AzarFijo([0,0, 1,1, 0,3, 2,0, 4,0]))` | Ids 15 a 19: Monstera, Lavanda, Romero, Mburucuyá, Welwitschia | Igual | Sí |
| 7 | `Sobre(3, ...).abrir(AzarFijo([0]))` | `ValueError: AzarFijo se quedó sin resultados` | Igual | Sí |

En el punto 6, cada carta usa dos valores del azar: primero la rareza y después la carta dentro de esa rareza. Los ids salen de `id_sobre × 5 + i`, así que el sobre 3 genera los ids 15 a 19 y nunca se pisan con otro sobre (R4).

## 3. Mercado: una partida paso a paso (`mercado.py`)

Ana y Beto se registran y seguimos el estado después de cada operación.

| # | Llamada | Predicción | Resultado | ¿Coincide? |
|---|---------|------------|-----------|------------|
| 8 | `registrar_jugador(ana)`, `registrar_jugador(beto)` | 100 de polen cada uno, `polen_total()` = 200 | 100, 100, 200 | Sí |
| 9 | `comprar_sobre(ana, SOBRE_COMUN)` | Sobre con id 1, Ana queda con 50 | id 1, 50 | Sí |
| 10 | `abrir_sobre(ana, sobre, AzarFijo([0,0, 0,0, 1,1, 0,3, 2,0]))` | Ids 5 a 9: Monstera, Monstera, Lavanda, Romero, Mburucuyá | Igual | Sí |
| 13 | `reclamar_recompensa(ana, ...)` con 50 de polen | `ErrorMercado`: se pide tener **menos** de 50 | `ErrorMercado: Solo se reclama con menos de 50 de polen`; sigue con 50 | Sí |
| 15 | `aceptar_publicacion(venta de #6 a 5, beto)` | `None`; Ana 55, Beto 95, total 150; Beto tiene el #6; quedan 2 publicaciones en el foro | None, 55, 95, 150, True, 2 | Sí |
| 16 | `aceptar_publicacion(subasta, beto)` | `ErrorMercado`; no cambia nada | `ErrorMercado: Las subastas no se aceptan...`; 55, 95; el historial no crece | Sí |
| 17 | `comprar_sobre(beto, SOBRE_DORADO)` | `ErrorMercado` (95 < 500); Beto sigue con 95; el historial no crece | Igual | Sí |
| 18 | `deshacer()` con 8 operaciones en el historial | Devuelve la operación `aceptar_publicacion`; Ana 50, Beto 100; el #6 vuelve a Ana y la venta vuelve al foro | Igual | Sí |
| 19 | `vender_al_mercado(ana, #9 Mburucuyá, 10/01/2026)` | 30 (épica en su estación: 75 × 0.4); Ana queda con 80 | 30, 80 | Sí |

**Qué aprendimos:**
- En el punto 13, la recompensa diaria pide tener *menos* de 50 de polen, y con exactamente 50 se rechaza. `test_r9_*` prueba con 100 y con 49, pero no con 50, que es justo el límite.
- Los puntos 16 y 17 confirman R2: una operación que falla no cambia el polen ni deja una entrada en el historial.
- En el punto 15, el polen total baja de 200 a 150 por el sobre que compró Ana, no por la venta: la venta mueve 5 de Beto a Ana sin crear ni perder polen (R3).
- El punto 18 confirma R6: `deshacer` devuelve las cartas, el polen y también la publicación del foro.

## 4. Núcleo puro (`analisis.py`)

Estas funciones se ejecutaron sobre la colección de Ana del punto 10 y sobre el foro de la partida.

| # | Llamada | Predicción | Resultado | ¿Coincide? |
|---|---------|------------|-----------|------------|
| 11 | `repetidos`, `contar_por_carta`, `progreso` | `(#6,)`; `{1: 2, 6: 1, 4: 1, 7: 1}`; 0.4 (4 de 10 cartas) | Igual | Sí |
| 12 | `valor_coleccion(coleccion, VERANO)` | 8 + 8 + 15 + 5 + 75 = 111 | 111 | Sí |
| 14 | `foro.buscar(precio_hasta(10))` y `precio_hasta(20)`, con una venta a 5, una subasta con mínimo 15 y un intercambio publicados | `[venta]` y `[venta, subasta]`; el intercambio nunca aparece | `['PublicacionVenta']` y `['PublicacionVenta', 'Subasta']` | Sí |
| 20 | `contar_por_tipo(registro_operaciones(historial))` | `{registrar_jugador: 2, comprar_sobre: 1, abrir_sobre: 1, publicar: 3, vender_al_mercado: 1}` | Igual | Sí |
| 21 | Dos corridas de `islice(aperturas(SOBRE_COMUN, ed, AzarReal(42)), 3)` | Dan las mismas cartas (`True`) | True | Sí |
| 22 | `frecuencia_rarezas(SOBRE_COMUN, ed, AzarReal(7), 2000)` | Cerca de 0.75 / 0.20 / 0.04 / 0.009 / 0.001 (±0.02) | 0.7518 / 0.1959 / 0.0431 / 0.0081 / 0.0011 | Sí |

**Qué aprendimos:**
- El punto 14 muestra el cambio de diseño pedido por el profesor: con `precio_de_referencia()` la subasta aparece en las búsquedas por precio, y el intercambio, que devuelve `None`, queda afuera.
- En el punto 20 no aparece `aceptar_publicacion`, porque se deshizo en el punto 18. El registro muestra lo que quedó, no todo lo que se intentó.
- En el punto 22, como `aperturas` es un generador infinito, solo se abren los 2000 sobres que pide `islice`. Las proporciones obtenidas confirman que las probabilidades publicadas son las que se usan de verdad (R10).

## Resumen
Las 22 predicciones coincidieron. La única diferencia fue el error de coma flotante del punto 5 (56.75000000000001 en lugar de 56.75), que ya esperábamos.

Las predicciones mostraron tres cosas que vale la pena tener presentes:
1. El redondeo bancario de `round`.
2. El límite exacto de la recompensa diaria (50 no alcanza).
3. El valor esperado del sobre común es mayor que su precio, pero no genera polen porque al mercado se le vende al 40 %.
