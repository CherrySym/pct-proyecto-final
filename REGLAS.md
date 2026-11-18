# Reglas que el sistema nunca debe violar

Cada regla tiene al menos un test en [tests/test_juego.py](tests/test_juego.py) que la protege.
Para correrlos: `python3 -m pytest` desde la raíz del proyecto.

| # | Regla | Dónde se garantiza | Test(s) |
|---|-------|--------------------|---------|
| R1 | El polen de un jugador nunca es negativo | `Jugador._cobrar`, y `polen` es de solo lectura | `test_r1_*` |
| R2 | Una operación inválida no deja rastros | `Mercado._ejecutar` restaura el estado si algo falla | `test_r2_*` |
| R3 | El polen no aparece ni desaparece entre jugadores | `Venta.aplicar` cobra y acredita lo mismo | `test_r3_*` |
| R4 | Cada ejemplar tiene un solo dueño y su id es único | `Sobre.abrir` deriva el id del id del sobre; `Jugador._quitar` / `_agregar` | `test_r4_*` |
| R5 | Con el mismo azar, el resultado es siempre el mismo | El azar entra por la interfaz `Azar` (`AzarReal` con semilla, `AzarFijo`) | `test_r5_*` |
| R6 | Deshacer vuelve exactamente al estado anterior, incluidas las ofertas de las subastas | `Operacion.estado_previo` + `Mercado.deshacer`; cada publicación guarda su propio estado (`Publicacion._capturar` / `_restaurar`) | `test_r6_*` |
| R7 | No se vende por debajo del valor base; las cartas no intercambiables no circulan entre jugadores | `reglas.venta_valida`, `Publicacion.validar` | `test_r7_*` |
| R8 | Los intercambios están balanceados por valor de rareza | `reglas.intercambio_balanceado` | `test_r8_*` |
| R9 | No existe una "máquina de dinero" | `FRACCION_SISTEMA`; tope de la recompensa diaria | `test_r9_*` |
| R10 | Las probabilidades de los sobres son públicas, suman 1 y no se pueden modificar | `TipoSobre` (copia de solo lectura) | `test_r10_*` |
| R11 | La insignia se entrega una sola vez por edición y sobrevive al reinicio | `Mercado.reclamar_premio`, `Jugador._reiniciar` | `test_r11_*` |
| R12 | Las estaciones son las del hemisferio sur | `reglas.estacion_de` | `test_r12_*` |
| R13 | Las funciones del núcleo puro no modifican lo que reciben | `analisis.py` (reduce con diccionarios nuevos) | `test_r13_*` |
| R14 | Una entrada inválida (None, negativos, texto, tipos raros, un nickname repetido o un jugador no registrado) se rechaza con `ErrorMercado` | `reglas.es_monto`, constructores, `_ejecutar`, `Mercado._verificar`, `Mercado.registrar_jugador` | `test_r14_*` |
| R15 | Cada tipo de publicación se resuelve y se describe a su manera | Polimorfismo: `Publicacion.validar` / `precio_de_referencia` / `resolver` / `descripcion`; `Transaccion.aplicar` | `test_r15_*` |
| R16 | Un jugador borrado desaparece de todos lados y, si se lo vuelve a registrar, arranca de cero | `Mercado.borrar_jugador` (Ley 18.331, derecho de supresión): también vacía los datos del jugador | `test_r16_*` |
| R17 | Lo ocurrido se puede verificar fuera del programa, incluidas las ofertas | `Mercado.ofertar` (las ofertas pasan por el Mercado y quedan en el historial), `analisis.registro_operaciones` + JSON en `programa.py` | `test_r17_*`, `test_r6_deshacer_una_oferta_la_saca_de_la_subasta` |



