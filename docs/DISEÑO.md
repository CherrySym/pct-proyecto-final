# **Idea del Juego**

# Idea general

El juego consiste en completar una colección de cartas de plantas. Todos los jugadores compiten para ser los primeros en completar la colección y obtener un premio. El premio será una carta especial que no forma parte de la colección, sino que funciona como una insignia de reconocimiento.

El juego se reinicia todos los años para que los jugadores que ya completaron la colección tengan un incentivo para seguir jugando. Lo único que se conserva de los años anteriores son las insignias obtenidas por completar las colecciones.

El juego se divide en cuatro estaciones: otoño, invierno, primavera y verano. Las plantas cambian de valor según la época del año. Por ejemplo, las plantas de verano tienen un valor mayor durante el verano.

# Cartas y colecciones

Existen cartas que no se pueden intercambiar y otras que solamente se pueden conseguir abriendo sobres. Estas condiciones se establecen individualmente para cada carta.  
Las cartas tienen diferentes especies de plantas y rarezas, se dividen en las siguientes categorias:

Especies:

* Selva tropical.  
* Desierto y suculentas.  
* Plantas carnívoras.  
* Flores de primavera.  
* Hierbas aromáticas.  
* Monte uruguayo.

Rarezas:

* Común.  
* Rara.  
* Épica.  
* Legendaria.  
* Mítica.

Cada carta del catálogo representa una especie que puede salir en los sobres. Sin embargo, el jugador recibe un ejemplar de esa carta, que puede guardar en su colección, intercambiar o vender a otros jugadores, dependiendo de las restricciones que tenga esa carta.

# Obtención de cartas y monedas

Los métodos para obtener cartas son:

* Compra y apertura de sobres.  
* Compra de cartas individuales a otros jugadores.  
* Intercambio de cartas con otros jugadores.

Las monedas del juego se llaman polen. Se utilizan para comprar sobres y cartas a otros jugadores.

También existen recompensas diarias para los jugadores que tienen menos de 50 de polen, con el objetivo de ayudarlos a reintegrarse al juego. Para evitar que esta recompensa se convierta en una forma de generar polen ilimitadamente, se establece un límite de una recompensa cada 24 horas, siempre que el jugador tenga menos de 50 de polen al momento de reclamarla. La recompensa será de 10 polen y no se acumulará si el jugador no la reclama.

# Mercado e intercambios

Los jugadores pueden vender sus cartas a otros jugadores o al mercado del sistema.

Cuando se vende una carta al mercado del sistema, el jugador recibe el 40% de su valor base, teniendo en cuenta el multiplicador de la estación correspondiente. La carta se elimina de su colección y vuelve a estar disponible para otros jugadores mediante los mecanismos de obtención que correspondan.  
Los precios de las cartas se calculan a partir de su rareza y de un precio base establecido para cada una. Las cartas de mayor rareza tienen un valor más alto.

En las ventas entre jugadores, el precio puede ser superior o inferior al valor base. El valor base funciona como referencia para los jugadores, pero el precio final depende de lo que acuerden ambas partes.

Para intercambiar cartas, cada una tiene un valor según su rareza. Por ejemplo, si una carta A tiene un valor de 3 y una carta B tiene un valor de 1, el jugador que ofrece la carta A puede solicitar la carta B y otras dos cartas de valor 1 para completar el intercambio.

Existe un foro donde los jugadores pueden publicar qué cartas desean vender o intercambiar. También se pueden realizar subastas, especialmente para las cartas de mayor rareza.

# Sobres y posibilidades

Existen sobres de diferentes tipos, con precios y probabilidades distintas de obtener cartas de determinadas rarezas.  
Al abrir un sobre se obtienen cinco cartas. Cada carta se genera en dos pasos: primero se sortea su rareza y después se selecciona una carta dentro de esa rareza.  
De esta manera, cuanto mejor es el sobre, mayores son las probabilidades de obtener cartas de rareza alta.  
Los precios de los sobres son:

* Común: 50 polen.  
* Plateado: 150 polen.  
* Dorado: 500 polen.

## Valores base por rareza

Este es el punto de partida para calcular el precio de las cartas.

| Rareza | Valor base (polen) |
| :---- | :---- |
| Común | 5 |
| Rara | 15 |
| Epica | 50 |
| Legendaria | 200 |
| Mítica | 800 |

## Probabilidades por carta

Cada tirada utiliza la siguiente distribución:

| Rareza | Común | Plateado | Dorado |
| :---- | :---- | :---- | :---- |
| Común | 75% | 40% | 0% |
| Rara | 20% | 38% | 30% |
| Épica | 4% | 17% | 45% |
| Legendaria | 0,9% | 4,5% | 20% |
| Mítica | 0,1% | 0,5% | 5% |
| Epica o mejor | 5% | 22% | 70% |

Las probabilidades se aplican individualmente a cada una de las cinco cartas del sobre.

## Verificación del valor esperado

El valor esperado se calcula multiplicando la probabilidad de obtener cada rareza por su valor base y sumando los resultados.  
Como cada sobre contiene cinco cartas, el resultado se multiplica por cinco.

| Sobre | Precio | Valor base esperado | Ratio | Vendido al sistema (40%) |
| :---- | :---- | :---- | :---- | :---- |
| Común | 50 | 56,75 | 1,14 | 22,7 |
| Plateado | 150 | 146 | 0,97 | 58,4 |
| Dorado | 500 | 535 | 1,07 | 214 |

Estos resultados permiten verificar dos aspectos de la economía:

* No existe una forma de generar polen ilimitadamente comprando sobres y vendiendo las cartas al sistema. El jugador recupera solamente el 40% del valor esperado de las cartas, por lo que siempre pierde polen en promedio.  
* Los valores esperados de las cartas son relativamente cercanos al precio de los sobres. Esto permite que las cartas tengan valor dentro del mercado sin que el sistema genere una cantidad excesiva de cartas baratas.

El 40% se aplica a las ventas realizadas al mercado del sistema. No limita los precios de las ventas entre jugadores.

## Efecto de las estaciones

El valor de las cartas puede aumentar según la estación del año. El multiplicador máximo será de 1,5 sobre el valor base.  
Para comprobar que esto no genere una forma de obtener polen comprando sobres y vendiendo todas las cartas al sistema, se calcula el peor caso posible:

| Sobre | Recuperación esperada al sistema | Con multiplicador 1,5 | Precios del sobre |
| :---- | :---- | :---- | :---- |
| Común | 22,70 | 34,05 | 50 |
| Plateado | 58,40 | 87,60 | 150 |
| Dorado | 214 | 321 | 500 |

Incluso en la estación más favorable, el jugador no puede recuperar mediante la venta al sistema el polen invertido en los sobres.

## Probabilidades de obtener una carta mítica

La probabilidad de obtener al menos una carta mítica en un sobre se calcula teniendo en cuenta que se reciben cinco cartas.

| Sobre | Chance de al menos una Mítica por sobre | Polen esperado por Mítica |
| :---- | :---- | :---- |
| Común | ≈ 0,5% | ≈10.000 |
| Plateado | ≈ 2,5% | ≈6.000 |
| Dorado | ≈ 22,6% | ≈2.200 |

El sobre dorado es el más eficiente para conseguir cartas de rareza alta. Sin embargo, las cartas míticas siguen siendo difíciles de conseguir, lo que incentiva a los jugadores a utilizar el mercado y los intercambios.

# Problemas tenidos en cuenta

Estos problemas fueron pensados, pero para está primer versión, como el sistema funciona sin ellos son ideas para implementar en versiones futuras.

## Cartas repetidas y completar la colección

Completar la colección tiene un problema conocido como el problema del coleccionista de cupones. A medida que el jugador consigue más cartas, aumenta la posibilidad de que las nuevas cartas sean repetidas.  
Por este motivo, el mercado, los intercambios y la venta de cartas repetidas son importantes para poder completar la colección.  
También hay que tener en cuenta el tamaño de la colección. Si hay demasiadas cartas, completar el catálogo puede volverse demasiado difícil. Por eso, se debe realizar una simulación para estimar cuántos sobres necesita abrir un jugador para completar la colección, teniendo en cuenta las probabilidades de cada sobre.

## Cartas garantizadas en los sobres

Para evitar la frustración de abrir sobres y no conseguir cartas de rareza alta, se podría implementar un sistema de cartas garantizadas.  
Por ejemplo:

* El sobre plateado garantiza al menos una carta rara.  
* El sobre dorado garantiza al menos una carta épica.

Sin embargo, esta opción modifica las probabilidades originales, ya que las cinco cartas dejan de generarse de manera independiente. Por este motivo, no se implementará en la primera versión. Si se agrega en el futuro, se deberán recalcular los valores esperados y volver a ejecutar las pruebas de economía.

## Cartas que solamente se consiguen en sobres

Algunas cartas solamente se pueden conseguir abriendo sobres. Esta condición pertenece a cada carta y determina si puede participar en intercambios o ventas entre jugadores.  
Estas cartas se deben incluir en el sorteo correspondiente a su rareza, pero no deben aparecer en las ofertas del mercado ni en los intercambios.

## Sobres temáticos

Se pueden implementar sobres que contengan cartas de una especie determinada. Por ejemplo, un sobre de Desierto y suculentas.  
En estos casos, se mantienen las mismas probabilidades de rareza del sobre original, pero la selección de la carta se realiza únicamente entre las cartas de esa especie.

