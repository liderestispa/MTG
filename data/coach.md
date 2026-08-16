# Coach de Magic — lectura de jugador de los tres mazos

Fuentes: `out/report_v6.json` (listas, `mm`, `st`), `data/pool.json` (371 cartas físicas,
204 nombres), `data/meta_decks.py` (metajuegos al 15-ago-2026). Radiografía de modelado hecha
con `src/extract.py::convert` sobre las tres listas y sobre el pool entero (script temporal,
no se tocó nada del repo).

**Regla que me impuse:** no recomiendo ninguna carta sin haber leído su `qty` en `pool.json`.
Cada carta que aparece abajo lleva su cantidad física verificada.

**Nada de esto es una medición.** Son hipótesis de jugador. Ojo con una asimetría del proyecto:
`obj_real.py` mide el ajuste contra el banco de winrates reales y **no evalúa los mazos de
Ricardo**. Por eso los cambios de este informe no pueden romper la calibración — pero tampoco
se pueden declarar mejoras hasta pasarlos por `revalidar.py` / `laboratorio.py` con semillas
independientes, y con el ruido de ±0,02 encima.

---

## 0. El veredicto en una frase

Ricardo dice que juega **control de prisión** y el buscador le entregó **tres montones de
criaturas sin interacción**, porque el motor no sabe leer las cartas de prisión que tiene en la
caja. Su colección esconde un mazo de negación bastante decente; el motor lo ve como papel en
blanco y por eso nunca lo propone.

El número que lo resume está en su propio informe, en `st`:

| | cartas en su mano turno 9 | cartas en mano del rival turno 9 |
|---|---|---|
| Standard | 1,05 | 1,75 |
| Pauper | 0,61 | 2,35 |
| Brawl | 0,49 | 2,21 |

Los tres mazos se quedan sin recursos antes que el rival, en los tres formatos. Para un jugador
de control eso no es un detalle de afinación: es el diagnóstico entero.

---

## 1. Los tres mazos, uno por uno

### 1.1 Standard BG — 24 tierras / 36 hechizos / cmc medio 3,08

**¿Qué hace de los turnos 1 a 4?** Turno 1, nada: los únicos dos "unodrops" son Giant's Boulder,
que es un artefacto que no afecta el tablero. Turno 2 baja un Ravening Warg o unos
Stony-Voiced Goblins. Turno 3, un Mirkwood Pathmaker. Turno 4, un Head of the Hunt. Su propio
informe lo confirma: `firstplay` 1,99 y `noplay14` 1,42 — **de sus primeros cuatro turnos, uno y
medio se van en blanco.**

**¿Cómo gana?** Atacando con osos hasta que el rival se muera. No hay evasión (cero criaturas
voladoras), no hay alcance, no hay motor de cartas y **no hay una sola remoción incondicional en
las 36 ranuras**. Warg Tactics solo mata voladoras, Head of the Hunt es un reemplazo pasivo,
Crude Bent Blade es un edicto único y Giant's Boulder no es remoción (ver §4).

**Esto no es un plan, es una curva ordenada por coste.** Y la forma de la curva delata al
buscador: 21 hechizos distintos para 36 cartas, de los cuales **12 son de una sola copia**. Un
mazo de 60 con doce cartas sueltas no puede contar con dibujar ninguna en concreto. Eso es una
caja de herramientas, no una lista.

**Contra qué pierde y por qué.** Sus dos peores según `mm` son Mardu Discard (81,3) y Dimir
Excruciator (83,75) — precisamente los dos mazos negros con descarte y remoción. Un jugador
diría lo mismo: un mazo sin ventaja de cartas y con tres cartas de siete manás es el sueño de
un mazo con cuatro Duress. Y ese es el punto: los 7-drops son exactamente lo que castiga el
descarte.

**Lo que sobra**

| Fuera | Por qué |
|---|---|
| 4 Stony-Voiced Goblins | Un 1/1 por 2 con un descarte de una vez. El rival elige qué tira, y con la mano llena en el turno 2 le cuesta nada. |
| 2 Giant's Boulder | El motor lo cuenta como remoción de 1 maná. No lo es (§4.3). Es un scry 2 y una piedra mediocre. |
| 2 de los 3 Gigantic Big Bear | Siete manás, 24 tierras, cero rampa. Se casta el turno 8-9 y la partida media dura 7,59. Deja uno como remate. |
| Walltop Sentries, Attercop, Old Thrush, Hog-Monkey | Relleno de una copia. Ninguna cambia una partida. |

**Lo que falta y YA TIENE** (cantidades verificadas en `pool.json`)

| Dentro | Tengo | Por qué |
|---|---|---|
| 2 Bilbo's Deadly Slice `{1}{B}{B}` | **2** | *Destroy target creature*, sin condiciones. Están en la caja sin usar. |
| 1 Heartless Act `{1}{B}` | **1** | Mata casi todo por 2. |
| 1 Gnashing of Teeth `{1}{B}{B}` | **1** | −5/−5, o −1/−1 a todo lo del rival: barre fichas. |
| 4 Great Fierce Bee `{2}{B}` 2/2 volador | **4** | La evasión que el mazo no tiene, y scry 1 cada vez que muere algo — en un mazo que se pasa la partida cambiando criaturas, es un motor pequeño gratis. |
| 2 Quarrel `{1}{G}` | **2** | Pelea. Con un Ordinary Bear 4/5, un Large Bear 5/5 o el Gigantic Big Bear es remoción de verdad. |
| 2 Wood Elves `{2}{G}` | **2** | Rampa con cuerpo, si decide quedarse con el remate de 7. Alternativa: 4 Little Bear (**4**), un 3/2 con destello que emboscar bloquea bien. |

Doce entran, doce salen. El mazo pasa de cero remociones incondicionales a cuatro, y de cero
voladoras a cuatro.

**Curva y tierras.** 24 tierras para cmc 3,08 está bien de cantidad; el problema es la forma.
Y ojo con algo que **no se puede arreglar**: en BG, dentro de su colección, no existe ninguna
criatura de 1 maná legal en Standard que valga la pena (solo Turtle-Duck 0/4). El agujero del
turno 1 es estructural. La conclusión de jugador no es "buscar unodrops", es **aceptar que el
mazo empieza en el turno 2 y recortar la parte de arriba**, no intentar rampar hasta ella.

Fuentes de color: 14 negras y 13 verdes de 60. Para el `{2}{B}{B}` de Head of the Hunt está por
debajo de lo que uno querría (17-18), pero la carta tiene destello y se puede lanzar tarde. Al
cortar dos Gigantic Big Bear desaparece el problema de `{5}{G}{G}` con 13 fuentes.

---

### 1.2 Pauper BR — 23 tierras / 37 hechizos / cmc medio 2,43

**Este es el mazo más coherente de los tres.** Curva baja, cuatro Crude Bent Blade (un edicto
pegado a un equipo de +2/+1 por 3 manás es una carta real en Pauper) y criaturas que atacan.
Turno 2 Ravening Warg o Goblin-town Flunkies, turno 3 Crude Bent Blade o Dori, turno 4 Gundabad
Opportunist. Gana peleando el tablero y ganando los cambios.

**Lo que sobra**

| Fuera | Por qué |
|---|---|
| 3 Stir Up Trouble | Es la carta más sobrevalorada del mazo. Su texto real es *"como coste adicional, sacrifica un artefacto o criatura, **o paga {4}**"*. El motor no cobra costes adicionales: la ve como un Doom Blade de un maná. En la mesa es un Doom Blade de cinco, o desventaja de cartas. |
| 2 Giant's Boulder | Lo mismo que en Standard. |
| 1 Cunning Maneuver, 1 Smaug's Fury | Trucos de pump sueltos. Cambian un combate; no cambian una partida. |
| 1 Ragged Short Spear | Equipo de +2/+0 con equipar {3} en un mazo que ya tiene cuatro Crude Bent Blade. |
| 1 Mongoose Lizard | Seis manás en un mazo de cmc 2,43. |

**Lo que falta y YA TIENE**

| Dentro | Tengo | Por qué |
|---|---|---|
| 3 Pinecone Strike `{1}{R}` | **3** | 3 de daño y **exilia** si iba a morir. En Pauper mata a Refurbished Familiar, Krark-Clan Shaman, Voldaren Epicure, Priest of Titania, casi todos los duendes de Rally. Es la mejor común de remoción que tiene y no la juega. |
| 1 Firebending Lesson `{R}` | **1** | Mata un elfo de maná en el turno 1. Con el kicker de {4}, cinco de daño tarde. |
| 2 Bilbo's Deadly Slice `{1}{B}{B}` | **2** | Mata un Myr Enforcer o un Tolarian Terror. |
| 3-4 Great Fierce Bee `{2}{B}` | **4** | Volador por 3 con scry en cada muerte. Encaja perfecto en un mazo de cambios. |

Y bajaría a **22 tierras**: cmc 2,43 sin robo no necesita 23.

**Contra qué pierde.** Sus tres peores son Grixis Affinity (59,0), Elves (63,7) y Jund Wildfire
(68,4). Los tres son mazos de criaturas, y a los tres se les gana con remoción barata y
eficiente — que es justo lo que tiene guardado. Contra Elves la partida entera es matar al
Priest of Titania o al Timberwatch Elf en cuanto aparecen: Firebending Lesson por `{R}` hace
eso el turno 1. Contra Affinity, Bilbo's Deadly Slice se lleva al Myr Enforcer y Pinecone Strike
al resto.

**El agujero que no puede tapar:** en BR no tiene **ninguna** remoción de artefactos (Pinecone
Strike solo destruye *fichas* de artefacto). Contra Grixis Affinity y Jund Wildfire eso es
media guerra perdida de entrada. Si va a comprar algo para Pauper, que sea eso, no criaturas.

**Un plan alternativo que sí existe en la caja.** Tiene un subtema de *amass* completo y sin
explotar: 3 Goblin-town Flunkies, 4 Tidings of War, 5 Rage into the Valley, 2 Clap! Snap!
(la aventura de Great Ugly-Looking Goblin), 1 Goblin Plate Mail y 3 tierras Goblin-town que
ponen dos contadores en el Ejército. Un Ejército gordo con Crude Bent Blade encima es un reloj
real. El riesgo es evidente —todos los huevos en una criatura que muere a cualquier remoción—
pero es *un plan*, y lo que hay hoy no lo es. Merece una corrida del buscador forzando ese eje.

---

### 1.3 Standard Brawl mono-blanco, Dáin — 24 tierras / 35 hechizos + comandante

**Es el mazo que más se parece a lo que Ricardo dice que quiere jugar**, y no por casualidad:
Dáin, Lord of the Iron Hills es **la única carta de prisión de su colección que el motor sabe
leer** (§4.1). El buscador la encontró y construyó alrededor de ella.

**Plan T1-T4:** unodrop, turno 2 Dáin, turno 3-4 desplegar y encender *Storied* (tres o más
artefactos / legendarias / Sagas). A partir de ahí el rival paga {1} por cada criatura que
quiera atacar y el tablero se congela a favor de Ricardo. La lista soporta el plan: siete
artefactos y cinco legendarias más el comandante, doce activadores para una condición que pide
tres.

**Pero solo tiene 1,96 remociones por partida** (contra 3,65 y 3,43 de los otros dos) **y ni un
solo barrido**. Y ahí está el problema, porque su metajuego dice esto:

| Rival | Cuota | Motor |
|---|---|---|
| **Elspeth Storm Slayer** (31 Hare Apparent + fichas) | **23,0%** | 68,8 |
| Tifa Lockhart | 9,5% | 78,2 |
| Sephiroth Fabled SOLDIER | 9,5% | 42,7 |
| **Ketramose the New Dawn** (control WB) | 7,0% | **13,3** |
| Eluge the Shoreless Sea | 6,2% | 75,6 |
| Kona Rescue Beastie | 5,0% | 67,3 |

**Casi un cuarto del metajuego es un mazo de fichas de conejo que se multiplican.** El único
barrido blanco de toda su colección es **Avatar's Wrath** (tengo **1**) — y no está en el mazo,
porque el motor lo lee como una carta que no hace absolutamente nada (§4.2). Contra Hare
Apparent, Avatar's Wrath es un barrido unilateral: las fichas exiliadas dejan de existir,
mientras que sus propias criaturas vuelven por {2}. Es, literalmente, la mejor carta que tiene
contra el mazo más jugado, y está fuera de la lista por un agujero de parseo.

**Lo que sobra**

| Fuera | Por qué |
|---|---|
| Key to the Side-Door | Su habilidad de robo pide *"descarta una carta legendaria con el mismo nombre que una legendaria que controlas"*. En Brawl, que es singleton, **eso es imposible por regla**. Queda una piedra de "{2},{T}: hazlo imbloqueable". (Nota justa: cuenta para Storied. Aun así, con once activadores restantes, sobra.) |
| Troop of Ponies | Un Rampant Growth que cuesta 2, más {2}, más la criatura, en un mazo de un solo color. |
| Avatar Enthusiasts | Un 2/2 que crece solo con Allies, y el mazo tiene ocho. |
| Long-Bodied Grey Dog | 2/2 por 3. Relleno. |
| Jasmine Dragon Tea Shop | Ver §4.6: en un mazo monoblanco es casi un Yermo. Cámbiala por la 24.ª Llanura. |

**Lo que falta y YA TIENE**

| Dentro | Tengo | Por qué |
|---|---|---|
| Razor Rings `{1}{W}` | **4** | 4 de daño a una criatura atacante o bloqueadora, y ganas la vida sobrante. Es la mejor carta defensiva blanca de la caja. El motor la lee como **nada** (§4.2). |
| **Avatar's Wrath** `{2}{W}{W}` | **1** | Su único barrido. Contra el 23% del metajuego. Prioridad uno. |
| Celebrate the Mountain-king `{3}{W}` | **1** | Exilia un permanente del rival mientras siga en juego, y encima roba/hace ficha. Un Banishing Light con carta. |
| Thorin's Last Stand `{2}{W}{W}` | **2** | Modal: destruye artefacto o encantamiento (los Banishing Light, Sheltered by Ghosts y Agatha's Soul Cauldron de Ketramose) o +2/+1 al equipo. |

Cuatro por cuatro, más el cambio de tierra.

**Curva y tierras.** 24 tierras para cmc 2,80 en singleton está bien; la curva (7/9/8/6/5) es
sana y `screw` 0,119 confirma que la base de maná no falla. El único defecto es que una de esas
24 no produce blanco.

**Ketramose: no lo pelees.** 13,3% es horrible, y en parte es real: un mazo monoblanco de
criaturas sin ventaja de cartas contra WB control con tres barridos y quince remociones pierde,
y no hay carta en su colección que lo arregle. Es el 7% del metajuego. **Gastar ranuras ahí
para arreglar un 7% mientras el 23% se queda sin barrido es el error clásico.** Dicho eso, el
13,3% en sí mismo me huele mal como número (§4.7).

---

## 2. Resumen de cambios propuestos

Todos verificados contra `pool.json`. Ninguno pide comprar nada.

| Mazo | Fuera | Dentro |
|---|---|---|
| **Standard BG** | 4 Stony-Voiced Goblins, 2 Giant's Boulder, 2 Gigantic Big Bear, Walltop Sentries, Attercop, Old Thrush, Hog-Monkey | 2 Bilbo's Deadly Slice, 1 Heartless Act, 1 Gnashing of Teeth, 4 Great Fierce Bee, 2 Quarrel, 2 Wood Elves |
| **Pauper BR** | 3 Stir Up Trouble, 2 Giant's Boulder, Cunning Maneuver, Smaug's Fury, Ragged Short Spear, Mongoose Lizard, 1 tierra | 3 Pinecone Strike, 1 Firebending Lesson, 2 Bilbo's Deadly Slice, 4 Great Fierce Bee |
| **Brawl W** | Key to the Side-Door, Troop of Ponies, Avatar Enthusiasts, Long-Bodied Grey Dog, Jasmine Dragon Tea Shop | Razor Rings, Avatar's Wrath, Celebrate the Mountain-king, Thorin's Last Stand, 1 Llanura |

**Predicción honesta:** medidos con el motor de hoy, estos cambios probablemente **bajen** el
índice bruto de los tres mazos, porque cambian cartas que el motor sobrevalora por cartas que
lee como cero. Eso no los invalida — indica que la comparación no se puede hacer hasta arreglar
§4.1 y §4.2. Es el mismo patrón documentado en `CLAUDE.md`: "es más correcto según las reglas"
no es evidencia, pero aquí el desacuerdo no está en la política del motor sino en que **no ve
el texto de las cartas**.

---

## 3. La pregunta grande de Brawl: no tiene comandante para su propio estilo

Esto es lo más importante del informe y no aparece en ningún número.

Su mejor material de prisión está en **azul-blanco**:

| Carta | Tengo | Qué hace |
|---|---|---|
| Enchanted River's Grasp `{2}{U}` | **4** | Gira la criatura, le quita todos los contadores, **le quita todas las habilidades y no se endereza nunca más**. Es un Pacifism duro. |
| Confusticate and Bebother `{2}{U}` | **4** | Contrahechizo suave o robar 2 y descartar 1. Nunca es carta muerta. |
| Honest Work `{U}` | **1** | Convierte la mejor criatura del rival en un 1/1 sin habilidades que produce maná. |
| Watery Grasp `{U}` | **1** | No se endereza; por waterbend {5} se baraja. |
| Old Fat Spider Can't See Me `{2}{U}` | **2** | Anula todo el daño de una criatura, permanente mientras siga en mesa, y luego roba dos. |
| Thranduil's Decree `{4}{U}{U}` | **1** | Contra y te quedas la carta. |
| Uneasy Partings / Lost Days | 1 / 1 | Remoción "a la biblioteca". |
| Earth Kingdom Jailer, Celebrate the Mountain-king, Avatar's Wrath, Razor Rings, Magnificent End | 1/1/1/**4**/2 | La mitad blanca: exilio, barrido y remoción. |

Ese es un mazo de prisión de verdad. **Y no lo puede jugar en Brawl**, por una razón dura:
en su colección **no hay ninguna criatura legendaria de identidad azul-blanca legal en Standard
Brawl**. Comprobado sobre las 204 cartas: los diez "posibles comandantes" WU que salen del
filtro son todos monoblancos o monoazules, y el comandante fija la identidad del mazo.

Sus opciones reales:

1. **Quedarse en monoblanco con Dáin.** Es el pool más profundo (44 hechizos únicos legales) y
   Dáin es su mejor carta de prisión. Es lo que hay hoy y está bien.
2. **Monoazul con uno de los Bilbo o Gandalf, Wandering Wizard.** Buildable, pero justo: 38
   hechizos únicos legales para 35 ranuras. Entra todo, no se corta nada, y eso siempre sale mal.
3. **Comprar un comandante WU legal en Standard Brawl.** Es, con diferencia, la compra que más
   colección le desbloquea: pasa de 44 a **77 hechizos únicos** disponibles, y desbloquea
   exactamente el eje que dice querer jugar.

No doy nombre de carta a propósito: recomendar algo que no tiene es el error más caro y más
documentado del proyecto, y verificar el pool de comandantes WU de Standard Brawl vigente
requiere consultar la legalidad actual, no mi memoria. Lo que sí puedo decir con precisión es
**el requisito**: criatura legendaria, `legalities.standardbrawl == "legal"`, identidad de color
exactamente `{W,U}`, barata. Que el agente de compras lo cotice con ese filtro.

Nota de simetría: WB (75 hechizos únicos) también le abriría un tipo distinto de prisión
—descarte y remoción— y tampoco tiene comandante WB. WR sí tiene cuatro comandantes propios
(Thorin Oakenshield, Dwalin, Nori, Bifur) pero ese eje es equipo y agresión, no prisión.

---

## 4. Lo que le chirriaría a un jugador del motor

Radiografiadas las 190 cartas no-tierra del pool: **75 nombres (124 copias, el 36% de sus
cartas físicas) llegan al simulador con `eff = NONE`, o sea, sin hacer absolutamente nada.**
Están ordenadas abajo por impacto × riesgo. Para cada una comprobé cuántas cartas del **banco de
calibración** (373 nombres distintos) tocaría el arreglo, que es lo que determina si el cambio
puede mover `obj_real` o no.

### 4.1 El eje de prisión entero es invisible — **0 cartas del banco afectadas**

Ninguna de estas produce ningún efecto en el motor:

- `Enchanted River's Grasp` ×4, `Honest Work` ×1, `Watery Grasp` ×1 — auras que **inmovilizan
  permanentemente** una criatura. `extract.py` línea 240 solo mira `enchanted creature gets
  +N/+N`; una aura que anula no encaja en ningún patrón. La rama `TAPDOWN` de la línea 201 pide
  literalmente `tap target creature ... it doesn't untap`, y estas dicen `tap **enchanted**
  creature`.
- **Airbend** (exiliar, con rescate por {2}) no existe como concepto: `Avatar's Wrath` (un
  barrido), `Aang, the Last Airbender`, `Airbender's Reversal`, `Glider Staff`,
  `Airbending Lesson` (solo se le lee el robo). Es una mecánica de remoción blanca completa,
  invisible.
- **Contadores de aturdimiento**: `Vengeful Villagers`.

Es el hallazgo grande. Ricardo se declara jugador de prisión y el motor tiene ciego justo ese
eje de su colección, así que el buscador nunca se lo va a proponer. La regla de la línea 201 ya
existe (`E_TAPDOWN` con `p1=2` = "pierde dos turnos"); estas auras piden lo mismo con un `p1`
mucho mayor porque el bloqueo es permanente. **Cero exposición al banco: no puede mover el
objetivo, solo cambia qué mazos encuentra el buscador para Ricardo.**

### 4.2 Razor Rings ×4 vale cero — **0 cartas del banco afectadas**

*"Razor Rings deals 4 damage to target attacking or blocking creature."* La regex de daño
(línea 127) cubre `target creature`, `any target`, `target player`, `target creature or
planeswalker` y `each creature`. No cubre `target attacking or blocking creature`. Resultado:
`eff = NONE`. Es exactamente la misma trampa que la de `each opponent` ya documentada en
`CLAUDE.md` con Grab the Prize — una campaña después, en otra rama de la misma regex. Cuatro
copias de una remoción premium leídas como papel en blanco.

### 4.3 Giant's Boulder es un "destruye permanente" de 1 maná — **3 cartas del banco**

Texto real: *"{7}, {T}, Sacrifica este artefacto: destruye el permanente objetivo."* La regex de
la línea 122 (`destroy target ... permanent`) no distingue entre el texto de un hechizo y el de
una **habilidad activada con coste**. El motor cree que tiene una remoción incondicional de un
maná, y por eso metió dos copias en Standard, dos en Pauper y una en Brawl.

Este es el que más ensucia sus tres listas a la vez. Del banco solo toca `Demolition Field`,
`Volatile Fault` y `District Mascot` (las tres tierras, y las dos primeras destruyen tierras,
que ya está desactivado), así que el riesgo es bajo — pero hay que medirlo.

### 4.4 Destroy condicionado leído como incondicional — **0 cartas del banco afectadas**

La bandera `cond` de la línea 123 solo se activa con `without`, `can't`, `unless` o
`with mana value`. No cubre restricciones de estado ni de estadística:

| Carta | Texto real | Cómo la ve el motor |
|---|---|---|
| Warg Tactics ×**5** (3 en el mazo de Standard) | Destruye criatura **con vuelo** | Destroy incondicional por 2 |
| Airbender's Reversal | Destruye criatura **atacante** | Destroy incondicional por 2 |
| Sandbenders' Storm | Destruye criatura **con fuerza 4 o más** | Destroy incondicional por 4 |

Tres Warg Tactics ocupando ranuras de remoción en el mazo de Standard es la consecuencia directa.

### 4.5 Dáin está modelado como otra carta — y apunta al recurso equivocado

El comandante sobre el que gira todo el mazo de Brawl:

- Texto real: *"Storied. **Mientras tengas una historia perdurable**, las criaturas no pueden
  atacarte a menos que su controlador pague {1} por cada una."*
- Modelado: `E_TAX` con `p1=1`, y en `sim.c` (`pay_gen`, línea 231) eso **encarece {1} todos los
  hechizos del rival**, desde el turno 2, **sin exigir la condición de Storied**.

Son dos errores en direcciones opuestas: (a) se le regala la condición, y (b) el impuesto se
cobra al **lanzar hechizos** en vez de al **atacar**. Contra Elspeth Hare Apparent, que lanza un
hechizo por turno y ataca con veinte criaturas, el Dáin real es **mucho mejor** que el modelado;
contra Eluge, que lanza muchos hechizos y ataca poco, es mucho peor. O sea: el error no infla
un número, **desordena los emparejamientos**, que es justo lo que mide el objetivo. Predicción
comprobable: modelar el impuesto como tasa de ataque debería **subir** el emparejamiento contra
Elspeth y **bajar** el de Eluge.

### 4.6 Cosas menores pero reales

- **`Jasmine Dragon Tea Shop` se lee como una tierra de cinco colores sin entrar girada.** Su
  `produced_mana` de Scryfall lista `B C G R U W` porque la restricción *"solo para hechizos
  Ally"* no cabe en ese campo. En un mazo monoblanco es un Yermo con un rider. Por eso aparece
  en todos los mazos de Brawl que genera el buscador.
- **`entra girada` no está modelado en ninguna parte** (`grep` sobre `src/`: cero resultados).
  Todas las tierras duales de su colección son duales perfectas y sin coste para el motor. Aquí
  la exposición al banco es enorme (Verges, shocklands, Raceways, Fabled Passage), así que es
  un cambio caro de validar, pero conviene saberlo antes de creerse cualquier recomendación de
  base de maná a dos o tres colores.
- **`Stir Up Trouble`: los costes adicionales no se cobran.** El proyecto ya modeló los costes
  *alternativos* (Fireblast, Snuff Out) y midió que valía. Los **adicionales** son el caso
  simétrico y siguen sin cubrir. Aquí sí hay exposición seria: **16 cartas del banco** (Bitter
  Triumph, Deadly Cover-Up, Grab the Prize, Reckoner's Bargain, Requiting Hex, Worthy Cost,
  Crop Rotation…). No lo toques sin `valida_semillas.py`.
- **`Mirkwood Pathmaker` se fija en 5/5.** `pt()` estima las P/T variables por número de tierras
  en 5. En el turno 3, que es cuando se juega, es un 3/3.
- **`Head of the Hunt`** se lee como un 4/3 que hace una ficha al entrar. Su texto real es un
  efecto de reemplazo que solo funciona cuando muere una criatura del rival.

### 4.7 Números del informe que un jugador no se creería

No son bugs identificados, son avisos de dónde mirar:

- **Standard, 91,8% contra Four-Color Control.** Es el mejor mazo de control del formato y su
  montón de osos sin remociones lo barre nueve de cada diez. Encaja con el pendiente ya
  documentado ("el motor no sabe que acumular cartas es un plan de victoria") y con el hecho de
  que el dato de Standard es pre-bans. Ese 91,8 no significa nada.
- **Pauper, 82,8% contra Blue Terror**, que juega cuatro Counterspell, tres Dispel, dos Vapor
  Snag y bichos de 5/5 por dos manás tarde. Un BR sin alcance no debería estar ahí.
- **Brawl, 13,3% contra Ketramose.** El emparejamiento es genuinamente malo, pero 13% es un
  atípico gigante contra los otros cinco (42-78). `sim.c` premia cada exilio del rival con
  `draw_select(...,3)` vía `E_EXILE_ENGINE`, y la lista de Ketramose exilia en casi todas sus
  cartas. Huele a motor de robo que se desboca. Vale la pena mirar cuatro partidas con
  `src/tablero.py` antes de aceptar ese número.

---

## 5. Orden de trabajo que propondría

1. **Arreglar §4.2 (Razor Rings) y §4.1 (auras de prisión + airbend).** Cero exposición al
   banco: `obj_real` no se puede mover, así que se pueden adoptar mirando solo la coherencia,
   y desbloquean el estilo que Ricardo quiere jugar. Es el mejor cambio por unidad de riesgo
   de toda la lista.
2. **Arreglar §4.4 (destroy condicionado).** También cero exposición al banco.
3. **Arreglar §4.3 (Giant's Boulder).** Tres cartas del banco, todas tierras; medir igual.
4. **Volver a correr `run_all.py` / `run_brawl.py` con eso arreglado**, y comparar las listas
   nuevas con los cambios manuales de §2. Si el buscador llega solo a las remociones y a
   Avatar's Wrath, es que los arreglos funcionaron.
5. **§4.5 (Dáin) y §4.6 (costes adicionales, tierras giradas)** son campañas aparte, con
   exposición al banco y con `valida_semillas.py` obligatorio.
6. **Fuera del motor:** cotizar un comandante WU legal en Standard Brawl (§3). Es la única
   compra de este informe y es la que más colección desbloquea.
