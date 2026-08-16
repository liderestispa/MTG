# Trampas verificadas

Errores concretos encontrados en proyectos reales, con su síntoma y su arreglo.

## 1. Recomendar cartas que el jugador no tiene

**Síntoma:** el análisis produce una lista "optimizada" preciosa y el jugador no puede armarla.

**Caso real:** tres mazos optimizados incluían `Well-Worn Spatula`, celebrada como "el hallazgo
del método" con el mayor impacto medido de todo el registro. El jugador no tenía la carta. El
winrate reportado no era alcanzable.

**Arreglo:** antes de reportar cualquier lista, verificar carta por carta contra el CSV,
incluyendo **cantidades**:

```python
for need, name in lista:
    c = pool.get(norm(name))
    if c is None:        reportar("NO LA TIENES")
    elif c['qty'] < need: reportar(f"pide {need}, tienes {c['qty']}")
```

Hacerlo también con las listas heredadas de análisis anteriores.

## 2. Maná híbrido perdido al parsear

**Síntoma:** la búsqueda se enamora de ciertas cartas sin razón aparente.

**Causa:** `{B/G}` no es un símbolo de color ni un número. Un parser que solo maneja
`sym.isdigit()` y `sym in "WUBRG"` lo descarta silenciosamente. Un 5/5 por `{3}{B/G}{B/G}`
pasa a costar 3.

**Arreglo:** el híbrido cuesta 1 maná que **debe** ser de uno de sus colores. Súmalo al genérico
para que el coste total cuadre, y guarda su máscara de colores aparte para filtrar elegibilidad.

**Test de regresión:** para toda carta, `generico + suma(pips) == cmc` de Scryfall. Córrelo sobre
el pool completo y sobre las cartas del meta. Debe dar cero desajustes salvo:
- Costes con `{X}` (Scryfall cuenta X=0; para jugar conviene X≥1)
- Cartas partidas tipo `Down // Dirty` (Scryfall suma ambas mitades)

## 3. Cartas de doble cara

`mana_cost` de una Adventure o MDFC viene como `{W} // {1}{W}`. Sumar los dos lados da 3 cuando
la carta cuesta 1. Divide por `//` y usa la cara frontal. Lo mismo con `type_line`, `power`,
`toughness` y `oracle_text`.

## 4. Metajuego obsoleto

**Síntoma:** el análisis optimiza contra rivales que ya no se juegan.

**Caso real:** un ban borró el 54,8% del metagame de Standard cinco días antes del análisis.
Los cuatro rivales modelados habían dejado de existir.

**Arreglo:** primera consulta del proyecto, siempre: *fecha del último B&R y qué cambió*.
Si hay un ban reciente, cualquier dato de metagame anterior a esa fecha está contaminado —
incluidas las ventanas de "últimos 30 días", que lo atraviesan.

## 5. Tierras que no producen maná

Existen tierras cuyo único uso es sacrificarse para buscar otra. Contarlas como fuente de maná
infla la consistencia y produce recomendaciones absurdas (del tipo "juega 4 copias").

**Arreglo:** filtra por `produced_mana` no vacío. Y recuerda que en singleton el límite de 1
copia aplica a **toda** tierra que no sea básica — `Land` a secas no es `Basic Land`.

## 6. Perseguir ruido estadístico

**Síntoma:** una optimización "mejora" 1,8 puntos y al validar resulta ser −0,9.

**Arreglo:** Common Random Numbers durante la búsqueda, semillas independientes en la
validación, e intervalo de confianza reportado. Ver `metodologia.md`.

## 7. Confundir rareza del CSV con legalidad en Pauper

Un CSV dice "uncommon" para la copia que el jugador tiene, pero Pauper es legal si la carta se
imprimió en común **en cualquier set de su historia**. Usa `legalities.pauper` de Scryfall, no
el campo de rareza del CSV.

## 8. Cartas en blanco para el motor

Toda carta cuyo texto el extractor no entiende se convierte en un cuerpo vanilla o en un no-op.
Si el 35% de los hechizos de un arquetipo son no-ops, ese arquetipo pierde por construcción.

**Arreglo:** mide el porcentaje por arquetipo y repórtalo. Amplía el extractor hasta bajar del
10%. Patrones que rinden mucho por poco código:

- `look at the top N cards ... put X into your hand` → robo efectivo
- `(surveil|scry|mill) N, then draw` → robo
- `destroy target [adjetivo] creature` (ojo con "non-outlaw", "with mana value 3 or less")
- `deals N damage to (up to one )?(target creature|any target)`
- Mecánicas de set: úsalas como valor condicional aproximado, no las ignores

## 9. Identidad de color donde no aplica

En **Standard y Pauper la identidad de color no existe**. Solo importa poder pagar el coste, así
que un híbrido `{B/G}` entra en un mazo mono-negro. En **Brawl y Commander sí aplica** y ese
mismo híbrido queda fuera de un mono-negro. Confundirlo produce listas ilegales o pools
artificialmente pequeños.
