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

**Caso límite verificado:** The Arkenstone // Seek the Heart cuesta `{5}` el artefacto y `{2}{W}`
la aventura. Su identidad de color es **blanca** por la mitad que nunca vas a lanzar, pero en
Standard basta con poder pagar la mitad que sí lanzas, así que entra en cualquier mazo. Auditada
la colección completa: **28 cartas con cara frontal incolora e identidad de color**; las otras 27
son híbridas o tierras duales y esas sí se filtran bien.

## 10. Fichas y art series en el bulk de Scryfall

**Síntoma:** cartas reales que salen `not_legal` y con estadísticas que no son las suyas.

**Causa:** el bulk trae **910 entradas de ficha y 2.243 de art series**, y **88 nombres existen a
la vez como ficha y como carta real** — Starscape Cleric, Darkstar Augur, Ajani's Pridemate. Un
índice por nombre que se queda con la primera coincidencia se puede quedar con la ficha.

**Arreglo:** la carta real siempre pisa a la ficha al construir el índice
(`src/driver.py::oracle()`). Dos mazos del banco de calibración estaban marcados como ilegales
por esto.

## 11. Ramas de texto que faltan: el robo recurrente

**Síntoma:** una carta buena rinde como si le faltara la mitad del texto, y no hay ningún error.

**Causa:** la regla de robo recurrente leía únicamente `at the beginning of your upkeep ... draw`.
The Arkenstone roba **al comienzo de tu paso final**, y esa rama no existía: el motor la tenía
como un lord pelado de 5 maná.

**Arreglo:** cubrir todos los pasos en que la habilidad puede dispararse — mantenimiento, paso
final, paso de robo y ambas fases principales. Cada vez que agregues un patrón de disparo,
enumerá los pasos antes de darlo por cerrado.

## 12. Keywords parseadas que nadie lee

Antimaleficio y vigilia estaban parseadas y **ningún camino del código las leía**: toda la
remoción dirigida mataba criaturas con antimaleficio. Por cada keyword que parsees, comprueba que
exista al menos un camino que la consulte. Un test que cuente usos por keyword lo detecta solo.

## 13. `untap target creature` contiene `tap target creature`

Quirion Ranger, que *endereza*, se leía como carta que gira. Faltaba un `\b`. Esta clase de error
no da excepción: da números.

## 14. `sacrifice a land` casi siempre es un coste propio

Crop Rotation y Highway Robbery sacrifican **tu** tierra para pagar. Hasta `destroy target land`
se usa a menudo sobre tierra propia (Cleansing Wildfire, que da nombre a Jund Wildfire).
Modelarlo como ataque al rival empeoró el ajuste.

## 15. Lo correcto según las reglas puede empeorar el ajuste

El bloqueo en grupo se implementó bien y **empeoró el residuo de 4,0 a 8,0**: los errores que
quedaban se estaban compensando entre sí. Quedó en el código, apagado y comentado. Regla general:
"es más correcto según las reglas" no es evidencia. Mide con `src/obj_real.py` antes de adoptar.
