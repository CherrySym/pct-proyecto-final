 Les pido dos cambios de diseño sobre lo que ya tienen.

1) Que cada publicación diga su precio (polimorfismo, sin getattr)
Hoy precio_hasta (analisis.py) usa getattr(pub, "precio_pedido", None) para saber si una publicación tiene precio.
Es preguntar "¿de qué tipo sos?" por la puerta de atrás, justo lo que el resto de su diseño evita.
Una consecuencia: las subastas nunca aparecen en una búsqueda por precio, aunque tienen precio_minimo.
Agreguen un método a Publicacion (por ejemplo, precio_de_referencia()) que cada subclase responda a su manera (venta: el precio pedido; subasta: el mínimo; intercambio: ninguno),
y hagan que precio_hasta lo use. Agreguen un test que cubra el caso de la subasta.

3) Que resolver devuelva la operación en vez de ejecutarla
Hoy PublicacionVenta.resolver y PublicacionIntercambio.resolver llaman a mercado._hacer_venta y mercado._hacer_intercambio, que son métodos "privados" (con guion bajo) de otra clase.
Por eso foro.py tiene que importar Mercado "solo para las anotaciones, para evitar un import circular".
 Ya tienen las clases Venta e Intercambio, que son datos.
Hagan que resolver(comprador, ofrece) devuelva una Venta o un Intercambio, y que Mercado.aceptar_publicacion sea quien la ejecute.
Así el foro deja de depender del mercado, desaparece el import circular, y resolver se puede testear sin armar un Mercado.
