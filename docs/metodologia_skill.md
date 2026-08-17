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

> **Rutas.** En el repo de referencia los scripts están en `src/` y los documentos largos en
> `docs/`. Si estás leyendo esto como skill empaquetada, los documentos te llegan bajo
> `references/` con el mismo nombre. Los comandos de abajo usan las rutas del repo.

```bash
python3 src/build_pool.py     # lee data/collection.csv + data/ricardo_sets2.json -> data/pool.json
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

`src/sim.c` es un motor en C (~70.000 partidas/s) que modela maná con colores reales,
mulligan, curva, combate evaluado, contrahechizos e interacción a velocidad de instantáneo.

```bash
gcc -O3 -w -o bin_sim src/sim.c -lm
python3 src/run_all.py        # búsqueda de mazos (Standard + Pauper)
```

Es C puro —solo `stdio/stdlib/string/stdint`— así que compila con MinGW en Windows sin tocar
nada. En Windows corre todo con `PYTHONUTF8=1` por delante: los `open()` sin `encoding` toman
la codificación local y revientan con los nombres acentuados de las cartas.

**Calibra contra dato REAL, no contra el 50%.** Corre primero `src/calibrate.py` (round-robin
del meta, mide desviación respecto al 50%) para detectar sesgos gruesos. Pero **esa vara esconde los
errores que se compensan entre sí**: en un caso real daba 9,56 puntos de error cuando el error contra
enfrentamientos reales publicados era 20,66. Busca los winrates que se publican —magic.gg para papel,
los recaps semanales de MTGGoldfish para MTGO, los agregadores de enfrentamientos— cárgalos en
`data/real_wr.py` y calibra con `src/calib_real.py`. Media hora de búsqueda vale más que otra
semana de código. En el repo el objetivo único vive en `src/obj_real.py` y es lo que se minimiza.

**Da por hecho que tu motor sobredispersa, y mídelo.** Un simulador hecho a mano no modela sideboard,
ni segunda y tercera partida, ni la habilidad del jugador — y todo eso comprime los resultados hacia
el 50%. Medido: ×2,9 en Pauper, ×5,3 en Standard, ×7 en enfrentamientos directos. `src/escala.py`
ajusta el factor de compresión por igualación de varianza y **se niega a calibrar** cuando la muestra
real no es representativa. Ojo: `data/escala.json` se queda viejo en cuanto tocas el motor, y el
informe lo usa para la estimación honesta. Regenéralo antes de publicar números.

**Declara la confianza por formato, no en global.** El mismo motor dio r=+0,73 en Pauper (el orden es
utilizable) y r=+0,16 en Standard (no validado). Pauper es comunes, cuerpos y combate: lo que un motor
así modela bien. Standard es raras con texto largo, modos y sideboard. Ver `references/calibracion.md`
— trae el banco, el detector de cartas mal modeladas, y las cuatro campañas de bugs.

**Cuidado con el peso que le das a un formato con pocos datos.** El objetivo compuesto pondera los
formatos, y un formato con 2 winrates reales aporta un *residuo*, no una correlación. En una corrida
real un cambio bajó el objetivo global de 2,543 a 2,534 —parecía mejora— pero la ganancia entera
venía del residuo de Brawl, calculado sobre 2 puntos, mientras la correlación de Standard caía de
+0,16 a +0,07. Mira siempre los componentes, no el número agregado.

**Ajusta la política de juego de la IA por barrido, no a ojo.** Los umbrales que deciden cuándo
bloquear, intercambiar o reservar maná son parte del modelo. `src/tune_real.py` hace descenso
coordenada a coordenada contra el dato real: en un caso bajó el RMSE global de 11,07 a 10,35 solo
con eso. Los parámetros viajan al motor por variables de entorno, y **nada los lee de vuelta**: el
resultado queda en `out/tuned_real.json` y hay que hornearlo a mano como default en `sim.c`. Si no
lo horneas, la próxima medición no los usa.

**Y valida el resultado del tuning con semillas independientes.** El descenso mide todo con la
misma semilla, así que una ganancia de milésimas puede ser ruido de esa corrida.
`src/valida_semillas.py` vuelve a medir cada variante con cinco semillas y compara la ventaja
contra la dispersión: si la diferencia cabe dentro del ruido, no se adopta.

Después de ajustar, **revalida los mazos** (Paso 6): si dejaron de ganarle a su semilla greedy,
ajustaste al banco y no al juego.

**Una regla más fiel no siempre da un motor más fiel, y hay un patrón detrás.** Sobre un
motor real, ocho cambios más fieles a las reglas se midieron y **todos empeoraron el
ajuste**: bloqueo en grupo, criaturas que se pagan solas, recursión de cementerio, fichas
como criaturas de verdad, "sin objetivo legal no se lanza" (regla 601.2c), y una política
de juego aprendida por autojuego. En cambio, **todo lo que sí pagó fueron lecturas de
texto que faltaban**: costes alternativos, locura, daño a cada oponente, drenaje de vida,
el retroceso de una carta con flashback.

La regla práctica que sale de ahí, y que ahorra días: **antes de implementar, pregúntate
si el cambio toca cómo se LEE una carta o cómo se JUEGA.** Lo primero suele pagar. Lo
segundo casi nunca, porque las heurísticas de juego del motor están ajustadas encima de
sus propios errores y el ajuste global se sostiene por compensación mutua. La salida
obvia —"pues re-tuneo encima"— también se midió: recuperó el 11%.

**Pero el sitio donde pones un efecto importa tanto como leerlo.** Este es el matiz que
convierte lo anterior en algo accionable. Un mismo texto, leído igual, medido en dos
ranuras distintas:

| Krark-Clan Shaman, "sacrifica un artefacto: 1 daño a cada criatura" | objetivo |
|---|---|
| como efecto de entrada | 3,102 — es un 1/1, se suicida y arrasa su propio tablero |
| como habilidad **activada** con su coste y su decisión | 0,978 |

Una habilidad **activada** no se aproxima con un efecto de entrada, y un disparo
**diferido** (al morir, al final del turno) tampoco: adelantarlo cambia el *tempo*, que es
justo lo que el motor mide. Si tu motor no tiene ranura para eso, construirla paga: las
dos juntas bajaron el objetivo de 1,270 a 0,978.

**Mide la sensibilidad del objetivo a cada arquetipo antes de elegir qué arreglar.** Si tu
objetivo mide correlación de orden, el residuo crudo de un mazo NO dice si conviene
subirlo: puede estar 13 puntos por debajo y aun así en su sitio relativo, y subirlo
entonces rompe el orden. Perturba el campo medido de a un arquetipo por vez, suma cero, y
mira el signo. En un caso real, tres arreglos correctos fracasaron por atacar arquetipos
cuya subida empeoraba el ajuste.

**Valida contra un modelo tonto, o no has validado nada.** Haz validación cruzada dejando un mazo
fuera y compara contra "predecir siempre la media real, sin simular". Si tu motor no le gana a eso,
no aporta información. Y acepta que hay formatos imposibles: si los winrates reales del formato
varían menos de 2 puntos, la señal es más chica que el ruido y ningún modelo gana. `src/loocv.py`.

**Revisa cómo quedó modelada cada carta, no solo los agregados.** `src/xray.py` imprime la lista
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

`src/audit_cards.py` marca cartas cuyo modelado es implausible (estadísticas imposibles para
el coste, keywords de más, reducciones agresivas, hechizos sin efecto). Córrelo cada vez que
amplíes el extractor: cada carta marcada es un bug potencial, y uno solo puede inflar un
arquetipo entero veinte puntos.

`src/check_legal.py` verifica que una lista sea legal **y armable** con la colección real:
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
- **Fichas y art series en el bulk de Scryfall**: trae ~910 entradas de ficha y ~2.243 de art
  series, y hay nombres que existen a la vez como ficha y como carta real (88 en una medición).
  Un índice por nombre que se queda con la primera coincidencia puede quedarse con la ficha, y
  entonces la carta sale `not_legal` y con estadísticas que no son suyas. La carta real manda.
- **Un disparo recurrente no siempre es en el mantenimiento.** Si tu regla busca solo
  `at the beginning of your upkeep`, se te escapan las que disparan en el paso final, en el de
  robo o en las fases principales. Enumera los pasos antes de dar por cerrado un patrón.
- **Si tu motor tiene varias ranuras de efecto por carta, comprueba que las lea todas.** Una carta
  con dos habilidades pone la segunda en la ranura secundaria; si el bucle que ejecuta el efecto
  solo mira la primaria, el extractor etiqueta y el simulador ignora. Pasó con el robo recurrente:
  `LORD` ocupaba la ranura primaria, el motor de robo caía en la secundaria y no disparaba nunca.
  Es la versión estructural de "keywords parseadas que nadie lee".
- **Un arreglo repartido entre dos lenguajes hay que commitearlo entero, o no existe.** Si la mitad
  en Python entra y la mitad en C se queda fuera, no hay error: hay un número documentado que ya no
  se reproduce. Corre el objetivo **justo después de commitear**, sobre el árbol limpio, y confirma
  que da lo que dice la documentación. Un `git status` limpio no prueba que midieras lo commiteado.

## Dos preguntas distintas: ¿funciona? y ¿conviene adoptarlo?

Es fácil confundirlas, y confundirlas cuesta días. Necesitas **dos bancos de prueba
separados**, porque responden cosas distintas y ninguno sustituye al otro.

- **¿El arreglo funciona?** Se responde con mazos sintéticos que aíslan un solo
  comportamiento: 24 criaturas con amenaza contra 16 muros, y nada más. Ahí el efecto o
  aparece o no aparece, sin ruido de metajuego. Si el arreglo es correcto, el sintético lo
  grita: en una medición real, dar visibilidad a la amenaza al declarar ataques llevó el
  winrate de 24,3% a 98,0%.
- **¿Conviene adoptarlo?** Se responde midiendo contra winrates reales publicados, con
  números aleatorios comunes, corrección por comparaciones múltiples y semillas de
  confirmación.

**Cuenta la materia antes de medir.** Un cambio correcto sobre material que tu banco no
tiene mide exactamente cero, y ese cero se lee como "no sirve" cuando en realidad es "no
medible". Pasó con tres arreglos verificados: el banco de 19 mazos tenía 8 criaturas con
amenaza, 1 con daño primero, 1 indestructible y 4 copias de un solo lord — y las 19
indestructibles que parecía haber eran una tierra que no ataca nunca. Escribe el contador
de material *antes* de escribir el experimento: es media hora y te ahorra interpretar mal
el resultado. Además, cada hipótesis medida endurece el umbral de Bonferroni para todas las
demás, así que gastar medidas en preguntas que el banco no puede responder tiene un coste
real sobre las que sí puede.

## Un máximo sobre una serie ruidosa no es una medida

Si informas del progreso de una búsqueda o un entrenamiento como *el mejor resultado hasta
ahora*, estás informando de una marca personal, no de una medida. El máximo de N tiradas
ruidosas queda por encima de la media aunque no haya ningún progreso, y el sesgo crece con
N: eso significa que **el número mejora solo con dejarlo corriendo más tiempo**.

Un entrenador evolutivo reportaba +2,135 puntos sobre su heurística de base. Re-medido en
12 semillas limpias y emparejadas, el valor real era **+1,251 ± 0,056**: el 41% era
selección sobre ruido. La causa era estructural — comparaba el máximo de ~1.000
evaluaciones contra **una sola** evaluación de referencia.

Las tres cosas que lo arreglan:

1. **Semillas de validación que no participan en ninguna selección.** Reserva unas pocas y
   no las uses jamás para elegir.
2. **Emparejamiento.** Mide la referencia y el candidato en las mismas semillas y compara
   diferencias. Quita del medio la varianza del escenario.
3. **Reporta el centro, no el máximo.** En un método de entropía cruzada, informa de lo que
   vale `mu` — que es lo que se ha aprendido de verdad —, no del mejor individuo que salió
   alguna vez.

Y una pista para detectarlo sin instrumentar nada: **si tu métrica alterna con periodo dos,
la está moviendo la semilla, no el aprendizaje.** En el caso real la élite y la media
alternaban casi un punto entre generaciones pares e impares y el centro alternaba en
anti-fase, porque la semilla era `900000+g*7919` (paridad alternante) y el centro se
evaluaba en `semilla+1`, siempre en la paridad contraria.

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
