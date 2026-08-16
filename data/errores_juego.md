# Errores de juego del motor

Informe del detector de errores de juego. No mide cartas mal leídas: mide **jugadas que un
jugador competente calificaría de error**, con las reglas de Magic en la mano.

## Cómo se obtuvo esto

- Trazas turno a turno (`src/trazar.py`, `TRACE=1`) y trazas JSON de tablero (`TRACE_JSON=N`,
  el mismo canal que usa `src/tablero.py`) sobre siete parejas de Pauper y Standard con varias
  semillas.
- Un banco de pruebas sintético que alimenta `./bin_sim` por stdin con mazos construidos a mano
  (criaturas vainilla, muros, hechizos de un solo efecto) para aislar **una** decisión a la vez.
  No recompila nada ni toca el árbol; solo escribe por la entrada estándar del binario ya
  compilado.
- Lectura de `src/sim.c` para localizar la decisión responsable.

**Advertencias que valen para todo el informe.** El objetivo mide **correlación de orden**, no
error absoluto: arreglar cualquiera de estos puntos puede empeorar el ajuste global si comprime
un arquetipo contra su vecino (ya pasó tres veces, ver `CLAUDE.md`). El ruido del objetivo es
±0,02. **Nada de lo que sigue está medido contra `src/obj_real.py`** — se pidió expresamente no
ocupar la máquina con eso. Esto es una lista de hipótesis con evidencia de reglas y de traza,
no una lista de cambios adoptables.

---

## 1. El atacante cuenta bloqueadores como si cada uno pudiera bloquear a todos

**Qué pasa.** Cada criatura decide atacar por su cuenta mirando si existe *algún* bloqueador
destapado que la mate. No se comprueba nunca cuántos bloqueadores hay frente a cuántos
atacantes. Con un único bloqueador grande, **todo un ejército se queda en casa**.

**Dónde lo vi.**
- Mono Red Rally vs Elves, semilla 8, **partida 40, turno 13**: Rally tiene listas Clockwork
  Percussionist 1/1, Voldaren Epicure 1/1, dos Goblin Tomb Raider 1/2 y Goblin Bushwhacker 1/1.
  Elves está a 14 vidas con **tres** bloqueadores destapados (Nyxborn Hydra 1/2, Priest of
  Titania 1/1, Generous Ent 5/7). Rally ataca con **cero** criaturas y hace 0 de daño.
  Cinco atacantes contra tres bloqueadores: al menos dos pasan sí o sí.
- Elves vs Tron, semilla 8, **partida 9, turno 8**: Elves tiene Llanowar Elves 1/1, Nyxborn
  Hydra 1/2 y Quirion Ranger 1/1 listos; Tron está a 23 vidas con un solo Boulderbranch Golem
  6/5 destapado. Elves no ataca. El Golem bloquea a uno; los otros dos pasan gratis.

**Cuánto pesa, medido.**
- Sintético: 24 criaturas 1/1 con prisa contra 16 muros 3/3 con **defensor** (que no pueden
  atacar nunca): winrate **0,0 %**, la partida llega al límite de turnos y **nunca se hace un
  punto de daño**. Con un muro 0/3 (que no mata al 1/1) el mismo mazo gana el 100 % en 7,4
  turnos. El interruptor es exactamente "¿existe un bloqueador que me mate?".

  | rival | winrate | turnos |
  |---|---|---|
  | 16x muro 0/3 (no mata al 1/1) | 100,0 % | 7,4 |
  | 16x muro 1/3 (mata al 1/1) | 100,0 % (por desempate, 0 daño) | 20 (límite) |
  | 16x muro 3/3 | 0,0 % | 20 (límite) |
  | 16x muro 5/5 | 0,0 % | 20 (límite) |

- Mazos reales, 60 partidas por pareja, contando turnos en que el jugador activo tenía poder
  destapado y sin invocación en mesa y aun así hizo 0 de daño:

  | pareja | turnos con poder | sin hacer daño | con bloqueador rival |
  |---|---|---|---|
  | Mono Red Rally vs Elves | 192 | **62 (32,3 %)** | 62 (100 %) |
  | Elves vs Jund Wildfire | 205 | 48 (23,4 %) | 48 (100 %) |
  | Tron vs Grixis Affinity | 124 | 35 (28,2 %) | 32 |
  | Blue Terror vs Mono Red Madness | 85 | 12 (14,1 %) | 12 (100 %) |

  En el 100 % (o casi) de los turnos perdidos había un bloqueador rival: no es que no hubiera
  a quién atacar, es esta regla.

**Por qué es error.** En Magic cada criatura bloquea a **un** atacante. Atacar en masa contra
menos bloqueadores es la jugada básica de cualquier mazo agresivo, y el defensor está obligado
a elegir. El motor razona como si el defensor pudiera bloquear a todos.

**Dónde está.** `src/sim.c:894-938`, bucle de elección de atacantes; la regla es
`if(lethalblk>0 && !racing) continue;` (línea 934). El propio código delata que la lógica
faltante estaba prevista: en `src/sim.c:896-897` se calcula `def_untapped` (número de
bloqueadores destapados) y **no se usa en ninguna parte**.

**Sospecha de por qué importa aquí.** Los tres arquetipos más infravalorados del banco
(Mono Red Rally −13,1, Mono Red Madness −7,7, y en Standard Mardu Discard −8,7) son
precisamente los que ganan atacando con varias criaturas pequeñas. Ojo con la trampa
documentada: subir a Rally sin subir antes a Madness empeora el orden.

---

## 2. Remoción dirigida que se lanza sin objetivo, y la carta se pierde

**Qué pasa.** La penalización por no tener objetivo (`PEN_NOTARGET=15`) es más pequeña que la
distancia hasta el suelo de lanzamiento (`CAST_FLOOR=-20`). Una remoción típica puntúa 12-14,
menos 15 queda en torno a −3: sigue por encima del suelo, así que **se lanza igual**. En
`apply`, `biggest_threat` devuelve −1 y no pasa nada: la carta desaparece de la mano.

**Dónde lo vi.**
- Four-Color Control vs Mardu Discard, semilla 8: **partida 1, turno 2**, A lanza Firebending
  Lesson con cero criaturas rivales en mesa. **Partida 1, turno 7**, B lanza Requiting Hex con
  la mesa rival vacía. **Partida 2, turno 4**, B lanza Erode igual.
- Izzet vs Dimir Midrange: **partida 2, turno 4**, Shoot the Sheriff sin objetivo;
  **partida 3, turno 17**, Nowhere to Run sin objetivo.
- Jund Wildfire vs Blue Terror: **partida 1, turno 2**, Snuff Out sin objetivo — ver punto 2b.

**Cuánto pesa, medido** (40 partidas por pareja, solo hechizos NO criatura; una criatura con
efecto de entrada al menos deja un cuerpo, así que no cuenta):

| pareja | cartas tiradas sin efecto | por partida |
|---|---|---|
| Four-Color vs Mardu | 114 | **2,85** |
| Izzet vs Dimir Midrange | 91 | **2,27** |
| Jund Wildfire vs Blue Terror | 24 | 0,60 |
| Mono Red Madness vs Tron | 24 | 0,60 |
| Mardu vs Orzhov | 18 | 0,45 |

Los peores casos individuales:

| carta | lanzamientos | sin criatura rival |
|---|---|---|
| Requiting Hex (Mardu) | 29 | **28 (97 %)** |
| Erode (Mardu) | 22 | 20 (91 %) |
| Requiting Hex (Dimir Midrange) | 47 | 36 (77 %) |
| Shoot the Sheriff (Dimir) | 22 | 16 (73 %) |
| Bitter Triumph (Dimir) | 21 | 14 (67 %) |
| Barrels of Blasting Jelly (Tron) | 42 | 21 (50 %) |
| Inevitable Defeat (Four-Color) | 70 | 18 (26 %) |
| Firebending Lesson (Four-Color) | 59 | 19 sin objetivo + 8 sin poder matar nada |

Sintético puro: un mazo de 20 "destruye la criatura objetivo" contra un rival sin ninguna
criatura lanza **13,12 remociones por partida**, mata 0 y termina con **0,00 cartas en mano**.
Vacía la mano al vacío.

**Por qué es error.** Por reglas, un hechizo que exige objetivo **no se puede lanzar** si no hay
objetivo legal (regla 601.2c). Aquí no solo se puede: se hace de forma sistemática, y cuesta una
carta y el maná.

**Dónde está.** `src/sim.c:812-816` (la penalización), `src/sim.c:59` y `68` (los dos valores que
no encajan), `src/sim.c:862` (el corte por suelo), y `src/sim.c:587-594` (`apply` para
`E_DESTROY`/`E_EXILE`, que simplemente no hace nada si `t<0`).

**Ojo al arreglarlo.** El mismo bloque de líneas 830-836 sí tiene penalizaciones que funcionan
(`-40` para edicto/inmovilizar sin criaturas, `-45` para pelea, `-35` para rebote): esos casos
sí caen por debajo del suelo. La incoherencia es solo con la remoción dirigida.

### 2b. El coste alternativo se paga aunque el hechizo no haga nada

Snuff Out se puede lanzar pagando 4 vidas. `paycost` (`src/sim.c:310-312`) recurre a la vía
alternativa en cuanto el maná no alcanza, **sin comprobar que el hechizo tenga objetivo**.

Jund Wildfire vs Blue Terror, semilla 8, medido sobre las fotos de fin de turno:

```
partida 1  turno 2 : lanza Snuff Out sin objetivo, con 0 tierras -> vida 20 -> 16
partida 3  turno 4 : lanza Snuff Out sin objetivo, con 1 tierra  -> vida 20 -> 16
partida 2  turno 11: lanza Snuff Out sin objetivo                -> vida 23 -> 19
partida 6  turno 13: lanza Snuff Out sin objetivo                -> vida 23 -> 19
```

14 de 23 Snuff Out de esa pareja se lanzan con la mesa rival vacía. **Pagar 4 vidas en el turno
2 para destruir nada** no es una jugada subóptima, es tirar la partida. `alt_ok` ya condiciona
Fireblast a que el daño mate (`src/sim.c:241-253`); la vía de vidas no tiene condición alguna.

---

## 3. Las fichas de una fuente que no es criatura son permanentes inertes

**Qué pasa.** `mk_tokens` **ignora los parámetros `pwr` y `tou`** que recibe y crea copias del
`Def` de la carta que las generó. Si esa carta es un conjuro o un artefacto, las "fichas" entran
al campo con `typ` de conjuro/artefacto y 0/0: **no cuentan como criaturas, no atacan, no
bloquean, no reciben bonos de lord y no mueren nunca**. Solo inflan el contador de permanentes.

**Dónde lo vi.** Mono Red Rally vs Elves, cualquier semilla. En la traza de `src/trazar.py`
semilla 12 se lee directamente:

```
t10  A | A vida 12 mano 0 tierras 5 cri 2(3 pod) perm  6 | ...
t11  B | A vida  7 mano 0 tierras 5 cri 0(0 pod) perm  4 | ...
```

Seis permanentes y dos criaturas; cuatro permanentes que no hacen absolutamente nada.
Promediado sobre 60 partidas: el tablero de Rally tiene **1,69 criaturas y 1,02
no-criaturas** por foto de fin de turno.

**Cuánto pesa, medido.** Rally lanza 0,67 Rally at the Hornburg (2 fichas 1/1) y 0,60
Experimental Synthesizer (1 ficha 2/2) por partida: cerca de **2 cuerpos por partida que
deberían existir y no existen**, en el mazo que da nombre al arquetipo.

Sintético: un mazo de 20 conjuros "crea dos fichas 2/2" contra un rival vacío gana el
**0,0 %** y no hace daño jamás. El mismo maná gastado en criaturas 2/2 de verdad (la mitad de
cuerpos) gana el **76,2 %**.

**El error también va al revés.** Si la fuente **sí** es criatura, la ficha es una copia
completa de ella. Writhing Chrysalis (2/3 por 4, `ETB_TOKEN(2,...)`) genera dos 2/3 adicionales
en vez de dos fichas pequeñas: Jund Wildfire recibe un regalo de 4 poder.

**Dónde está.** `src/sim.c:470-476` (`mk_tokens`, con `pwr`/`tou` sin usar) y la llamada en
`src/sim.c:521` (`case E_ETB_TOKEN`). Hay que crear una entrada `Def` para la ficha, no clonar
la fuente. Afecta también a `E_MOBILIZE` (`src/sim.c:579`) y `E_TOKEN_SCALE` (522-526).

**Contexto.** Mono Red Rally es el arquetipo peor ajustado del banco (33,3 % motor contra 46,4 %
real). `CLAUDE.md` culpa a Burning-Tree Emissary, Goblin Tomb Raider y Galvanic Blast; esto es un
cuarto agujero, y no está documentado.

---

## 4. El remate a la cara no sabe que es letal (pero "a cualquier objetivo" sí)

**Qué pasa.** En `cast_phase` hay un bonus explícito de `+60` cuando un `E_DMG_ANY` mata al rival
(`src/sim.c:810`). **`E_BURN_FACE` y `E_ETB_DRAIN` no tienen nada equivalente.** Un hechizo que
gana la partida ahí mismo compite con una criatura por su puntuación normal, y suele perder.

**Cuánto pesa, medido.** El mismo hechizo (6 de daño por 2 de maná), etiquetado de las dos
formas, contra un rival que empieza a 6 vidas (o sea, letal desde el primer turno en que se
puede pagar), compitiendo con una criatura 4/4 con prisa por 2:

```
BURN_FACE : [lanzar] mana libre 2 | #3(criatura 4/4 v=22) #2(remate letal v=10) => juega la criatura
            wr 100,0 %  turnos 2,94
DMG_ANY   : [lanzar] mana libre 2 | #3(criatura 4/4 v=22) #2(remate letal v=80) => remata
            wr 100,0 %  turnos 2,07
```

Casi un turno entero de diferencia con exactamente el mismo hechizo. Contra un rival que también
está corriendo, ese turno es la partida.

**Por qué es error.** "Si esto gana ahora, se lanza ahora" no admite discusión.

**Dónde está.** `src/sim.c:800-831` (el bloque de valoración de remoción/quemar); falta la rama
para `E_BURN_FACE` y `E_ETB_DRAIN`. La puntuación base está en `src/sim.c:653`
(`case E_BURN_FACE: s+=2*d->p1;`), que ni siquiera mira las vidas del rival.

**Relacionado.** La decisión de atacar tampoco suma el daño de todos los atacantes: `racing` se
evalúa criatura a criatura contra `opp->life <= P_*2` (`src/sim.c:932`). Cinco criaturas de 2 de
poder contra un rival a 9 vidas es letal, y ninguna de las cinco lo ve. En el lado del bloqueo sí
existe la variable agregada (`lethal_now`, `src/sim.c:958`); en el del ataque, no.

---

## 5. Amenaza, daño primero e indestructible son invisibles al declarar ataques

**Qué pasa.** El bucle de ataque calcula `kills_me = (op>=T_) || deathtouch` e
`i_kill = (P_>=ot) || deathtouch` (`src/sim.c:912-913`). No mira daño primero, no mira
indestructible, y `minb_atk` (el mínimo de bloqueadores que exige la amenaza, línea 920) solo se
usa dentro de la rama de bloqueo en grupo, que está apagada por defecto (`GANG_ON=0`).

**Cuánto pesa, medido.** Winrate con y sin cada palabra clave, mismo mazo, misma semilla,
400 partidas:

| criatura de A | rival | wr sin la palabra clave | wr con ella |
|---|---|---|---|
| 2/2 prisa (+ amenaza) por 2 | 16x muro 3/3 | 35,2 % | **35,2 %** |
| 3/3 por 4 (+ daño primero) | 16x muro 3/3 | 68,8 % | **68,8 %** |
| 4/4 por 4 (+ indestructible) | 16x muro 6/6 | 3,0 % | **3,0 %** |

Idénticas hasta la décima: las tres palabras clave **no cambian ni una sola partida** en el
lado del ataque.

**Por qué es error.**
- Un 2/2 con **amenaza** frente a un solo bloqueador es imbloqueable por reglas; declina un
  ataque que no puede salir mal. Y aquí es doblemente absurdo porque el defensor tampoco puede
  bloquear en grupo (`src/sim.c:1021`, la rama de bloqueo simple exige `minb==1`), así que en
  este motor una criatura con amenaza es literalmente imbloqueable... y aun así no ataca.
- Un 3/3 con **daño primero** contra un 3/3 gana el combate sin sufrir un rasguño. El lado del
  bloqueo sí lo tiene en cuenta (`src/sim.c:978`); el del ataque, no. La asimetría hace que el
  motor crea que va a morir en un combate que el propio motor resolvería a su favor.
- Un **indestructible** no muere en combate nunca.

**Dónde está.** `src/sim.c:906-935`. Los tres arreglos son de una línea cada uno en el cálculo
de `kills_me`/`lethalblk`.

---

## 6. La remoción y los barridos no ven los bonos de lord

**Qué pasa.** `pw()`/`th()` (`src/sim.c:216-219`) devuelven poder y resistencia **sin** el bono
estático de los lords: `lordbonus()` (`src/sim.c:222-227`) solo se llama dentro de `combat()`.
Todo lo que decide fuera del combate ve los cuerpos en su tamaño base.

**Cuánto pesa, medido.** Sintético: A lanza "inflige 1 de daño a la criatura objetivo"; B tiene
criaturas 1/1 con un lord que da +2/+2, o sea **son 3/3**. Resultado: **5,24 muertes por
partida**. Debería ser cero.

**Por qué es error.** Matar a un 3/3 con 1 punto de daño no es una decisión discutible, es una
regla rota. Y arrastra a cuatro sitios más:

- `best_killable` (`src/sim.c:410-423`): elige objetivo y decide qué muere.
- `E_SWEEPER` (`src/sim.c:599-606`): `th(opp,i)<=a` barre criaturas que en la mesa real
  sobreviven. Un barrido de 2 limpia un tablero de Elves con lord.
- `biggest_threat` (`src/sim.c:436-444`): elige mal la amenaza mayor.
- `board_pressure` (`src/sim.c:446-452`): infravalora el reloj rival, lo que a su vez desajusta
  `turnos_de_vida` y todo el término `W_PRESSURE`.

**Dónde está.** Lo limpio es que `pw()`/`th()` incluyan el bono, o un par de helpers
`pw_eff()`/`th_eff()` usados en esos cuatro sitios.

**Nota aparte del mismo `board_pressure`.** Suma el poder de **todas** las criaturas del rival,
incluidas las que tienen defensor, las giradas y las que acaban de entrar con invocación. El
motor cree que un muro le está pegando. En el lado del bloqueador sí filtra `K_DEF`
(`src/sim.c:449`), en el del atacante no.

---

## 7. "Inflige N daño a la criatura objetivo" pega a la cara

**Qué pasa.** `apply` para `E_ETB_DMG`/`E_DMG_SPELL` tiene un `else if(ncreat(opp)==0)
opp->life-=a;` (`src/sim.c:487`). El comentario lo admite: *"sin objetivos: a la cara"*.

**Cuánto pesa, medido.** Un mazo de 20 hechizos "inflige 2 a la criatura objetivo", nada más,
contra un rival **sin ninguna criatura**: gana el **100 %** de las partidas **por daño**
(`win_dmg` = 0,99). Por reglas ese mazo no puede ganar jamás.

**Por qué importa aunque parezca cosmético.** Convierte toda la remoción roja de coste bajo en
quemar a la cara cuando el rival juega control, que es justo el emparejamiento en que la
diferencia decide. Y se suma al punto 2: la carta se lanza sin objetivo *y además* hace daño
que no debería.

**Dónde está.** `src/sim.c:483-488`. Es una rama de tres palabras; conviene medir su quita, no
solo quitarla, porque puede estar tapando el hueco de "los mazos rojos no tienen alcance".

---

## 8. La reserva de maná para contrahechizos guarda una cantidad que nunca alcanza

**Qué pasa.** `reserve_for_instants` (`src/sim.c:688-698`) busca el contrahechizo más barato de
la mano y **lo recorta a `RESERVE_MAX`, que vale 1** (`src/sim.c:68`). Con Counterspell ({U}{U},
coste 2) el motor deja **una** tierra abierta: paga el coste de tempo de no desarrollar y aun
así no puede contrarrestar.

Y la válvula de escape documentada **no existe**: el comentario de `src/sim.c:768-771` describe
dos pasadas, la segunda ignorando la reserva. Hay una etiqueta `REINTENTO:` en `src/sim.c:777`
y **ningún `goto REINTENTO` en todo el archivo** (`grep -n "goto" src/sim.c` no devuelve nada).
`ignora_reserva` es siempre 0. La única forma de saltarse la reserva es bajar a 6 vidas.

**Cuánto pesa, medido.** Blue Terror (11 contrahechizos: 4 Counterspell, 1 Deprive, 3 Dispel)
contra el resto del meta de Pauper, 400 partidas:

| RESERVE_MAX | contras usados | de N ocasiones | tierras libres en la ocasión | índice bruto |
|---|---|---|---|---|
| 0 | 1,03 | 17,15 | 0,26 | 48,1 % |
| **1 (por defecto)** | **2,19** | 12,42 | **0,79** | **41,6 %** |
| 2 | 2,43 | 10,02 | 0,88 | 47,5 % |
| 3 | 2,43 | 10,02 | 0,88 | 47,5 % |

Con el valor por defecto, cuando el rival lanza un hechizo y Blue Terror tiene un contrahechizo
en la mano, tiene **0,79 tierras destapadas de media**. Un Counterspell cuesta 2. En la práctica
solo funcionan los Dispel de 1.

El defecto (1) es peor en el índice bruto que sus dos vecinos: paga el peaje sin comprar nada.
**Esto es un diagnóstico, no una propuesta**: el índice bruto no es el objetivo de calibración y
Blue Terror es solo uno de siete arquetipos. Cualquier cambio aquí tiene que pasar por
`obj_real.py` y `valida_semillas.py`.

**Segundo defecto en la misma comprobación.** El filtro es
`untapped_count(me) - d->cmc < res` (`src/sim.c:797`) y usa **`cmc`, no el coste real**. Para
las cartas con reducción de coste (Cryptic Serpent, Tolarian Terror: `cmc` 7, `gen` mucho menor)
resta 7 aunque cuesten 2, así que la reserva las bloquea casi siempre. Son las dos únicas
condiciones de victoria del mazo.

---

## 9. Bloqueos que regalan material a plena vida

**Qué pasa.** El valor de un bloqueo malo (muero sin matar) es
`TH_BADBLOCK(-14) + (cmc_atacante - cmc_bloqueador)*2 + presión + poder_del_atacante`
(`src/sim.c:983-984`). Los dos últimos términos crecen con el tamaño del atacante, así que
**cuanto más grande es lo que ataca, más ganas tiene el motor de tirarle criaturas encima**.
Contra un 6/6 de coste 6, un bloqueador de coste 1 puntúa `-14 + 10 + 0 + 6 = +2 > 0`: bloquea
a 20 vidas.

**Cuánto pesa, medido.** Sintético, 60 partidas: A ataca con 6/6 por 6, B tiene 1/1 por 1 (que
podrían atacar en vez de morir). Salen del campo **241 criaturas de B y 0 de A**: B pierde
**4,02 criaturas por partida** bloqueando a un 6/6 que no muere nunca.

**Por qué es error.** El bloqueo de sacrificio solo se justifica cuando el daño es letal o
cuando se está estabilizando. A 20 vidas contra un solo 6/6 se toman los 6 y punto.

**Cuidado especial aquí.** `TH_BADBLOCK`, `TH_TRADE`, `TH_PERFECT` y `TH_WALL` están ajustados
por descenso contra la calibración (11,07 → 10,35 según el comentario de `src/sim.c:64-67`).
Tocarlos reabre el espacio de parámetros entero (regla 4 de `CLAUDE.md`). Lo que sí parece un
error de forma y no de calibración es el término `(d->cmc - o->cmc)*2` **en la rama de bloqueo
malo**: premia perder una carta barata contra una cara, cuando en un bloqueo malo el coste del
atacante es irrelevante porque el atacante no muere.

---

## 10. Inmovilizar criaturas que ya están giradas

**Qué pasa.** `E_TAPDOWN` elige objetivo con `biggest_threat` (`src/sim.c:436-444`), que **no
mira el estado de giro**. Sobre una criatura ya girada, `opp->tap[t]=1` no hace nada; solo
sobrevive el congelado si `p1>=2`.

**Cuánto pesa, medido** (40 partidas por pareja, comparando el lanzamiento contra la foto de
tablero previa):

| carta | p1 | lanzamientos | objetivo probable ya girado |
|---|---|---|---|
| Kaito, Bane of Nightmares | 1 | 31 | **18 (58 %)** |
| Sleep of the Dead | 2 | 34 | 15 (44 %) |
| Floodpits Drowner | 1 | 12 | 5 (42 %) |

Con `p1=1` (Kaito, Floodpits Drowner) el efecto es un **no-op completo**: 18 de 31 activaciones
de Kaito no hacen nada. Con `p1=2` (Sleep of the Dead) queda el congelado, así que el
desperdicio es parcial.

**Por qué es error.** Girar lo ya girado no es una jugada. Un jugador apunta a la criatura
destapada más peligrosa, y si no hay ninguna, guarda el efecto.

**Dónde está.** `src/sim.c:556-562`. La corrección natural es un `biggest_threat_untapped()`, o
filtrar `!p->tap[i]` en `biggest_threat` cuando quien llama es `E_TAPDOWN`. Lo mismo aplica a
`E_MASS_BOUNCE`/`E_FOG_BOUNCE`, que solo devuelven criaturas **giradas** (`src/sim.c:541-544`,
`575-578`) y por tanto no hacen nada si el rival no atacó.

---

## Errores menores, agrupados

Verificados en código y visibles en traza, pero de peso claramente inferior a los diez de
arriba.

1. **`defender_instants` no valora el objetivo.** En el turno rival la elección es
   `int v=d->score;` a secas (`src/sim.c:736`), sin ninguno de los ajustes por calidad de
   objetivo que sí tiene `cast_phase` (líneas 800-831). El único filtro es que exista *alguna*
   criatura rival. Consecuencia: se gasta la remoción cara en un acelerador de maná, y un
   hechizo de 1 de daño se lanza contra un tablero de 5/5 y no mata nada (Firebending Lesson:
   8 de 59 lanzamientos sin poder matar nada; Krark-Clan Shaman: 39 de 106).
2. **Los hechizos de pump dan contadores permanentes.** `E_PUMP` hace
   `me->ctr[m] += max(p1,p2)` (`src/sim.c:622-623`). Un Crecimiento Gigante es un +3/+3 para
   siempre y acumulable. Sintético: 10 pumps + 10 criaturas 1/1 contra 5/5 gana el 91,2 %, y en
   la traza se ve una sola criatura pasando de 1 a 7 y a 13 de poder. Se lanza además en la
   fase principal 1 sobre la criatura de más poder, sin comprobar que vaya a atacar.
3. **La remoción se anula contra indestructible en vez de cambiar de objetivo.**
   `biggest_threat` no filtra `K_IND` pero `apply` sí lo comprueba después
   (`src/sim.c:587-589`): si la amenaza mayor es indestructible, el hechizo se pierde en lugar
   de apuntar a la siguiente.
4. **`E_FIGHT` es unilateral.** `src/sim.c:596-598`: mi criatura mata a la suya si tiene más
   poder, pero **nunca recibe daño**. Pelear es daño mutuo.
5. **Contrahechizo y protección solo se detectan en la ranura `eff`.** `cast_phase:788`,
   `try_counter:703`, `has_counter_in_hand:720` y `reserve_for_instants:691` comprueban
   `d->eff` y no `eff2`/`eff3`. Es la trampa ya documentada en `CLAUDE.md` con `E_UPKEEP_DRAW`,
   en otras cuatro funciones.
6. **La traza miente al imprimir.** `src/sim.c:860` imprime `=> lanza` mirando solo `best<0`,
   pero el corte real es `if(best<0 || bv<CAST_FLOOR) break;` en la línea 862. En las trazas
   aparecen líneas como `#14(cmc1 pag v=-38) => lanza` que en realidad **no lanzan nada**. Es
   fácil sacar conclusiones falsas leyendo `trazar.py`; conviene arreglarlo antes de que otro
   agente lo lea.
7. **La elección de tierra no hace lo que dice.** El comentario de `src/sim.c:762` promete
   "prefiere la que da colores que faltan" y el código elige la de **más colores**
   (`popcount` mayor), sin mirar qué colores tiene ya en mesa ni cuáles pide la mano.

---

## Lo que busqué y NO encontré

- **Maná sin gastar teniendo cartas jugables.** Revisadas todas las decisiones de lanzamiento
  de trazas completas de Blue Terror y Tron: 0 casos de "queda maná libre y hay una carta
  pagable que no se lanza" fuera de los cortes deliberados (`CAST_FLOOR` y la reserva del punto
  8). El bucle de `cast_phase` sí exprime el maná.
- **Criaturas que atacan a la muerte.** El sesgo va claramente en el otro sentido (punto 1). En
  el sintético de 60 partidas contra un 6/6, el atacante perdió 0 criaturas y el defensor 241.
- **Hechizos buenos que se quedan en la mano por puntuación baja.** Salvo el caso concreto de
  los contrahechizos (punto 8) y de las cartas con reducción de coste bloqueadas por la reserva,
  no aparece un patrón general de cartas de valor alto sin lanzar.

## Orden sugerido de ataque, y por qué

1. **Punto 1 (declaración de ataques).** Es el que más partidas cambia, el más barato de
   arreglar (usar `def_untapped`, que ya está calculado y sin usar) y el que afecta a más
   arquetipos a la vez. Cuidado: sube a *todos* los mazos agresivos, y el objetivo mide orden.
2. **Punto 3 (fichas inertes).** Es un agujero de modelado puro, sin ambigüedad de política, y
   golpea de lleno al arquetipo peor ajustado del banco.
3. **Punto 2 (+2b) (remoción sin objetivo).** Hasta 2,85 cartas por partida en Standard, y el
   arreglo es un número (`PEN_NOTARGET` por encima de `CAST_FLOOR`) más un `if` en `alt_ok`.
   Beneficia sobre todo a Four-Color Control, que es el error grande que queda abierto.
4. **Punto 4 (remate letal)** y **punto 5 (palabras clave en el ataque)**: baratos, locales, con
   evidencia sintética limpia.
5. **Punto 6 (bonos de lord)**: correcto por reglas y con efecto amplio, pero toca cuatro
   funciones y mueve la valoración de la remoción en todo el banco. Medir con ablación.

Y la regla que manda sobre todo lo anterior: **ninguno de estos se adopta por ser correcto según
las reglas.** Se adopta si baja `obj_real.py` y sobrevive a `valida_semillas.py`. En este
proyecto ya se cayeron tres cambios que eran más correctos que el motor y ajustaban peor.
