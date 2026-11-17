segunda version

que debe tener en general
ETICA.md es una página con cuatro partes: los datos que maneja la aplicación, un riesgo ético concreto junto con el cambio de diseño que lo mitiga, un marco legal o una licencia citados después de haberlos leído, y el uso de IA realizado.

que debe tener el tema de sobres
ETICA.md debe analizar la transparencia de las probabilidades de los sobres, la relación entre las mecánicas de azar y las apuestas (el juego de azar con dinero real está regulado por el Estado, y este mercado usa moneda ficticia) y el efecto sobre menores. Además del código y el UML, se entrega la lista de reglas que el sistema nunca debe violar, con el test que protege cada una.

(extracto de BITACORA_IA.md)

### Datos personales (Ley 18.331)

- Se eliminó `email` de `Jugador`: no tenía finalidad (art. 8). Esto cambia respecto del diseño original.
- `borrar_jugador` aplica el derecho de supresión (arts. 15 y 37). Lo saca de la lista de jugadores, del foro y de las ofertas, y vacía el historial, porque cada operación guarda una foto del estado. Se decidió que la supresión pesa más que el deshacer, y por eso lo anterior ya no se puede deshacer.

# Análisis Ético

## 1. Datos que maneja la aplicación

Desde el punto de vista ético y de protección de la privacidad (Ley N° 18.331), la aplicación se enfoca exclusivamente en los **datos personales y de actividad** de los jugadores:

- **Identificadores personales:** `nombre_jugador` (nombre de la persona) y `nickname` (alias público obligatorio dentro del sistema).
- **Datos patrimoniales y de actividad en el juego:** saldo en `polen` (moneda virtual), colección de cartas (`Ejemplar`, con identificadores únicos asignados al usuario), inventario de sobres comprados, insignias obtenidas, ofertas monetarias realizadas, publicaciones en el foro y registros de transacciones previas.

### Principio de minimización de datos (Art. 8, Ley 18.331)

- **Eliminación del correo electrónico (`email`):** En el diseño original se contemplaba almacenar el email del jugador. Sin embargo, se eliminó de la clase `Jugador` al constatar que el sistema no realiza autenticación remota, recuperación de cuenta ni comunicaciones externas. Retenerlo violaba el principio de finalidad (art. 8), ya que se estaría guardando un dato identificatorio sensible sin un propósito funcional real.
- **Datos no recolectados:** La aplicación prescinde por completo de contraseñas, datos biométricos, geolocalización, identificadores de red (IP) e información financiera o bancaria, operando con el mínimo de datos indispensable para jugar.
- **Garantía de supresión:** Todos los datos anteriores son los que se eliminan de forma irreversible al invocar el derecho de supresión (`borrar_jugador`).

---

## 2. Riesgo ético y cambio de diseño que lo mitiga

### Riesgo identificado: Mecánicas de azar (_loot boxes_) y protección de menores

El juego incorpora la apertura de sobres de cartas con distribución aleatoria de ejemplares. En la industria de los videojuegos, las cajas de botín (_loot boxes_) han sido ampliamente cuestionadas por psicólogos y reguladores internacionales debido a su funcionamiento basado en esquemas de **refuerzo de razón variable**, los cuales reproducen los patrones conductuales de las máquinas tragamonedas y generan riesgo de adicción o conductas compulsivas, con un impacto especialmente lesivo en niñas, niños y adolescentes.

A esto se suma la distinción legal respecto a las **apuestas y juegos de azar**: en el ordenamiento uruguayo, las apuestas con dinero real están reguladas y monopolizadas por el Estado (Dirección Nacional de Loterías y Quinielas). Si un sistema permite adquirir ítems aleatorios con dinero real o monetizarlos hacia el exterior, se desnaturaliza el entretenimiento y se incurre en una práctica de juego de azar encubierta.

### Cambios de diseño y mitigaciones implementadas

1. **Circuito económico 100% cerrado y sin dinero real:**  
   El `polen` es una moneda exclusivamente ficticia. No existen pasarelas de pago para adquirir polen ni mecanismos para retirar o transferir valor económico fuera del sistema (_cash-out_).
2. **Transparencia absoluta en probabilidades de sobres (Regla R10):**  
   Las probabilidades de obtención de cada rareza son públicas, verificables y suman exactamente 1.0. En `sobres.py`, las probabilidades se exponen mediante tuplas y objetos de solo lectura, impidiendo algoritmos opacos de "retención" o manipulación dinámica de probabilidades orientadas a inducir frustración o gasto compulsivo.
3. **Tope a la recompensa diaria y prevención de acumulación (Regla R9):**  
   Para evitar la explotación del tiempo del usuario y mecánicas abusivas de retención (_grinding_ o FOMO), la recompensa diaria (10 polen) solo se habilita si el jugador posee menos de 50 polen y con un límite estricto de una vez cada 24 horas.
4. **Protección contra especulación y mercado negro (Reglas R7 y R8):**  
   Determinadas cartas de máxima rareza (ej. _Welwitschia_) poseen `intercambiable = False`, impidiendo que los ejemplares más codiciados circulen en transacciones entre usuarios que pudieran dar lugar a acuerdos o pagos externos por fuera del software. Los trueques exigen equivalencia estricta de rareza para evitar transacciones asimétricas o predatorias entre jugadores novatos y avanzados.

---

## 3. Marco legal citado: Ley N° 18.331 (Protección de Datos Personales)

Se analizó y aplicó la **Ley N° 18.331** de la República Oriental del Uruguay sobre Protección de Datos Personales y Acción de _Habeas Data_:

- **Artículo 8 (Principio de finalidad y pertinencia):**  
  _«Los datos personales que se recaben a los efectos de su tratamiento deben ser ciertos, adecuados, pertinentes y no excesivos en relación al ámbito y finalidad para los que se hubieren obtenido»_.  
  Este artículo fundamentó la decisión arquitectónica de suprimir el atributo `email` de la clase `Jugador`.

- **Artículos 15 y 37 (Derecho de supresión / cancelación):**  
  Regulan el derecho fundamental del titular a solicitar la eliminación total de sus datos personales.

### Conflicto de diseño resuelto en el código

En el sistema, el `Mercado` implementa un patrón transaccional (`_ejecutar` y `deshacer`) que guarda instantáneas (_snapshots_) completas del estado anterior de cada operación.  
Al implementar `Mercado.borrar_jugador(jugador)` (protegido por la regla **R16** y el test `test_r16_*`):

- Se remueve al jugador del registro activo.
- Se retiran todas sus publicaciones y ofertas en el foro mediante polimorfismo (`_olvidar_jugador`).
- Sus ejemplares y polen se retiran de circulación.
- **Se vacía por completo el historial de operaciones (`_historial.clear()`):** Dado que las instantáneas previas contenían copias del estado del jugador borrado, conservarlas violaría el derecho de supresión. Se tomó la decisión explícita de que **el derecho a la privacidad y eliminación de datos prevalece sobre la trazabilidad técnica de la función deshacer**.

---

## 4. Uso de Inteligencia Artificial realizado

Se incorporó herramientas de Inteligencia Artificial generativa bajo una metodología de asistencia supervisada, documentada en detalle en la bitácora del proyecto (BITACORA_IA.md):

1. **Diseño conceptual y modelado inicial:**  
   La concepción temática del mercado de plantas, la dinámica de estaciones y la primera iteración del diagrama UML fueron elaboradas de manera autónoma por el equipo. La IA se utilizó con posterioridad para contrastar decisiones de diseño y validar posibles omisiones en las relaciones entre entidades.
2. **Calibración de la economía y detección de alucinaciones:**  
   Se consultó a la IA para calcular probabilidades equilibradas en los sobres y relaciones de costos. En este proceso se identificaron errores y asunciones incorrectas del modelo (por ejemplo, la IA asumió una comisión arbitraria del 40% en ventas al sistema que contradecía la especificación del equipo). La discrepancia fue corregida manualmente.
3. **Refactorización y adecuación pedagógica:**  
   El código generado inicialmente por la IA incluía construcciones avanzadas o ajenas al alcance del curso y sobrepasaba la limitacion impuesta en la consigna (como `frozenset`, `@property`, `@staticmethod` o `__post_init__`). Se solicitó reescribir y simplificar dichas secciones para garantizar un código mas legible, mantenible y comprensible para todo el equipo.
4. **Cambio de Diseño (Cambio docente):**  
   Ante el requerimiento de cambio en el diseño, se empleó la IA como apoyo para comprender el desacople entre `Foro` y `Mercado`, logrando que las publicaciones devuelvan objetos `Transaccion` polimórficos (`precio_de_referencia` y `resolver`) en lugar de invocar métodos privados.
