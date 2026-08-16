---
name: mtg-optimizador
description: Optimiza mazos de Magic: The Gathering a partir de una colección real, por simulación contra el metajuego vigente. Úsalo cuando el usuario pida armar, mejorar o comparar mazos con las cartas que tiene; evaluar qué comprar; verificar si un mazo es legal o armable; o analizar un CSV de colección (CollectiDeal, Moxfield, Archidekt, Deckbox). Cubre Standard, Pauper, Standard Brawl y Commander en papel.
---

# Optimizador de mazos de Magic

Construye el mejor mazo posible con una colección concreta, lo valida contra el metajuego
real del formato, y calcula la ruta de compra más rentable.

## Qué lo hace distinto

La mayoría de los análisis de mazos fallan por tres razones, y este flujo las ataca de frente:

1. **Recomiendan cartas que el jugador no tiene.** Aquí *todo* se verifica contra el CSV real
   antes de reportar nada.
2. **Corren contra un metajuego viejo.** Un ban puede borrar la mitad del formato en un día.
   Aquí se verifica la fecha del último B&R antes de modelar rivales.
3. **Reportan winrates de simulador como si fueran predicciones.** No lo son. Aquí el número
   absoluto se declara como índice relativo y se acompaña de métricas que sí son confiables.

## Flujo

### Paso 1 — Cargar la colección y resolverla contra Scryfall

El CSV del usuario trae nombres (posiblemente en varios idiomas) y a veces Scryfall IDs.
**Si trae Scryfall ID, úsalo**: elimina toda ambigüedad de idioma y de edición.

```bash
python3 scripts/build_pool.py --csv coleccion.csv --cards ricardo_cards.json --out pool.json
```

Colapsa por `oracle_id`: la misma carta en inglés y en español es **una carta con N copias**,
no dos cartas. Esto suele cambiar los conteos en un 20-30%.

**Si el contenedor no alcanza `api.scryfall.com`** (proxy corporativo, sandbox), lee
`references/puente_scryfall.md`. Hay una receta con el navegador del usuario que funciona.

### Paso 2 — Verificar el metajuego ANTES de simular

No asumas que el meta que recuerdas sigue vigente. Busca:

- La fecha del último **Banned & Restricted** de Wizards y qué cambió.
- Los sets legales hoy en el formato (rotación).
- Las cuotas de metagame y decklists completas de los 5-7 arquetipos más jugados.

Fuentes que responden: `mtggoldfish.com/metagame/<formato>`, `mtgtop8.com`, `magic.gg`,
`aetherhub.com`. Ojo: `mtgdecks.net` devuelve 403 y las páginas de mazo de MTGGoldfish
cargan por JavaScript. `mtgtop8.com` sí entrega listas en texto plano.

**Verifica que cada decklist sume exactamente 60** (o 100 en Commander) antes de usarla.
Las páginas de arquetipo agregadas mezclan "cartas más jugadas" y no suman.

### Paso 3 — Construir el pool jugable por formato

Filtra por `legalities[formato] == "legal"` de Scryfall. Cuidado con:

- **Pauper**: legal si la carta se imprimió en común *en cualquier set*, no según la rareza del CSV.
- **Brawl / Commander**: singleton, y la **identidad de color** manda (un híbrido `{B/G}` tiene
  identidad BG, así que no entra en un mazo mono-negro).
- **Standard y Pauper**: la identidad de color **no existe**. Solo importa poder pagar el coste,
  así que los híbridos sí entran.

### Paso 4 — Simular

`scripts/sim.c` es un motor en C (~70.000 partidas/s) que modela maná con colores reales,
mulligan, curva, combate evaluado, contrahechizos e interacción a velocidad de instantáneo.

```bash
gcc -O3 -w -o bin_sim scripts/sim.c -lm
python3 scripts/search.py --fmt standard --pool pool.json --meta meta.json
```

**Calibra contra dato REAL, no contra el 50%.** Corre primero `scripts/calibrate.py` (round-robin
del meta, mide desviación respecto al 50%) para detectar sesgos gruesos. Pero **esa vara esconde los
errores que se compensan entre sí**: en un caso real daba 9,56 puntos de error cuando el error contra
enfrentamientos reales publicados era 20,66. Busca los winrates que se publican —magic.gg para papel,
los recaps semanales de MTGGoldfish para MTGO, los agregadores de enfrentamientos— cárgalos en
`data/real_wr.py` y calibra con `scripts/calib_real.py`. Media hora de búsqueda vale más que otra
semana de código.

**Da por hecho que tu motor sobredispersa, y mídelo.** Un simulador hecho a mano no modela sideboard,
ni segunda y tercera partida, ni la habilidad del jugador — y todo eso comprime los resultados hacia
el 50%. Medido: ×2,2 en Pauper, ×4,5 en Standard, ×7 en enfrentamientos directos. `scripts/escala.py`
ajusta el factor de compresión por igualación de varianza y **se niega a calibrar** cuando la muestra
real no es representativa.

**Declara la confianza por formato, no en global.** El mismo motor dio r=+0,70 en Pauper (el orden es
utilizable) y r=−0,03 en Standard (no validado). Pauper es comunes, cuerpos y combate: lo que un motor
así modela bien. Standard es raras con texto largo, modos y sideboard. Ver `references/calibracion.md`
— trae el banco, el detector de cartas mal modeladas, y las cuatro campañas de bugs.

**Ajusta la política de juego de la IA por barrido, no a ojo.** Los umbrales que deciden cuándo
bloquear, intercambiar o reservar maná son parte del modelo. `scripts/tune.py` hace descenso
coordenada a coordenada contra el banco de calibración: en un caso real bajó el RMSE global de
11,07 a 10,35 solo con eso. Después de ajustar, **revalida los mazos** (Paso 6): si dejaron de
ganarle a su semilla greedy, ajustaste al banco y no al juego.

**Una regla más fiel no siempre da un motor más fiel.** Los errores restantes se compensan entre
sí, así que añadir realismo en un punto puede desbalancear lo que ya estaba cuadrado. Mide toda
mejora de reglas contra el banco antes de adoptarla, y si no ayuda, déjala tras un flag apagado
con un comentario que diga qué midió. Caso documentado en `references/calibracion.md`: el bloqueo
en grupo, implementado correctamente, empeoró el residuo de 4,0 a 8,0 puntos.

**Valida contra un modelo tonto, o no has validado nada.** Haz validación cruzada dejando un mazo
fuera y compara contra "predecir siempre la media real, sin simular". Si tu motor no le gana a eso,
no aporta información. Y acepta que hay formatos imposibles: si los winrates reales del formato
varían menos de 2 puntos, la señal es más chica que el ruido y ningún modelo gana. `scripts/loocv.py`.

**Revisa cómo quedó modelada cada carta, no solo los agregados.** `scripts/xray.py` imprime la lista
con el efecto, el coste y las keywords que le asignó el extractor. Los errores más caros no dan
excepción, dan números: `deals N damage to any target` mandado a "quemar a la cara" deja a todos los
mazos rojos sin interacción; `untap target creature` contiene la subcadena `tap target creature`.

**Mide la cobertura antes de modelar algo nuevo.** Antes de implementar planeswalkers, cuenta qué
fracción del meta los usa. En un caso real planeswalkers, sagas, equipo y auras sumaban menos del
4% de las cartas: ese trabajo no podía mover el RMSE.

**Lee `references/metodologia.md` antes de interpretar cualquier número.** Resumen mínimo:

- Usa **Common Random Numbers** (semillas fijas). Sin esto el ruido supera las diferencias reales.
- El motor **sobrevalora mazos de criaturas** frente a mazos de hechizos. Corre la prueba de
  cordura (cada mazo del meta contra el meta): si el reparto no es razonablemente plano, el
  winrate absoluto no es utilizable como predicción.
- Optimiza con objetivo compuesto, no con winrate solo:
  `wr − 0.030·turnos_sin_jugada(T1-4) − 0.020·max(0, turno_primera_jugada − 2)`
  Esas dos métricas dependen solo del barajado, el maná y la curva — son confiables aunque
  el modelo de combate no lo sea.

### Paso 5 — Buscar

Beam search sobre listas completas: mantiene las K mejores en cada ronda en vez de una sola
(el hill climbing puro se estanca en óptimos locales). Con racing: criba barata a ~100 partidas,
evaluación profunda solo a los supervivientes.

Antes del beam, haz un **barrido de identidades de color** con semilla que respete una curva
razonable. Si la semilla se arma por "mejor puntuación" sin curva, se llena de bombas caras
y el barrido miente.

### Paso 6 — Validar

Re-evalúa a los ganadores con **semillas nuevas e independientes** y muestra grande (3.000+).
Una mejora que no sobrevive a semillas nuevas era ruido. Este paso no es opcional.

**Y compara cada mazo contra su propia semilla greedy.** Una lista optimizada está ajustada a la
versión del motor que la produjo; si tocaste el motor después, puede haber quedado por debajo de
la construcción simple. Cuando eso pasa hay que rehacer la búsqueda, no publicar la lista. Pasó
con un mazo que terminó 1,58 puntos por debajo de su semilla tras una campaña de correcciones.

### Paso 7 — Ruta de compra

Precio de mercado desde el campo `prices.usd` del bulk de Scryfall. Calcula el costo **neto**:
descuenta las cartas que el usuario ya tiene y las tierras básicas (que son gratis).

Reporta el costo por arquetipo **junto a su cuota de metagame**. Suele aparecer que el mazo
más jugado del formato no es el más caro.

## Auditoría de cartas

`scripts/audit_cards.py` marca cartas cuyo modelado es implausible (estadísticas imposibles para
el coste, keywords de más, reducciones agresivas, hechizos sin efecto). Córrelo cada vez que
amplíes el extractor: cada carta marcada es un bug potencial, y uno solo puede inflar un
arquetipo entero veinte puntos.

`scripts/check_legal.py` verifica que una lista sea legal **y armable** con la colección real:
tamaño, legalidad por formato, límite de copias, identidad de color, y cantidades poseídas.

## Trampas verificadas

Están en `references/trampas.md` con el detalle. Las que más daño hacen:

- **Maná híbrido**: `{B/G}` cuesta 1 maná que debe ser B o G. Si tu parser lo ignora, cartas
  como un 5/5 por `{3}{B/G}{B/G}` pasan a costar 3 y la búsqueda entera se lanza sobre ellas.
  Contrasta siempre `generico + pips` contra el `cmc` de Scryfall: deben cuadrar.
- **Cartas de doble cara** (Adventure, MDFC): `mana_cost` viene como `{W} // {1}{W}`. Usa solo
  la cara frontal.
- **Tierras que no producen maná**: existen (p. ej. las que solo se sacrifican para buscar).
  Filtra por `produced_mana` no vacío antes de contarlas como fuente.
- **Verifica que el mazo propuesto sea armable** carta por carta contra la colección, incluyendo
  cantidades. Es el error más caro y el más fácil de cometer.

## Reglas de formato

`references/formatos.md` tiene las reglas verificadas contra el Comprehensive Rules, incluidos
los puntos donde las fuentes populares se equivocan (vidas en Brawl 1v1, si la banlist de
Standard aplica a Standard Brawl, tamaño de mazo de Standard Brawl vs Brawl).

## Cómo reportar

- Da la lista completa, ordenada por coste de maná, con cantidades.
- Da **dos números**: el índice bruto (sirve para comparar listas entre sí, que es lo único que la
  búsqueda necesita) y la estimación comprimida por el factor de sobredispersión medido. Si la muestra
  real no da para calibrar el nivel, dilo — es mejor un *no sé* que un 90% inventado.
- Acompáñalo de: turnos sin jugada, turno de primera jugada, y % de partidas con screw de color.
- Si el mazo no es competitivo, dilo. Un jugador que aprende gana más con un mazo consistente
  y barato que con uno "optimizado" que no hace nada hasta el turno cuatro.
