# Contexto del proyecto para Claude Code

Lee esto antes de tocar nada. Resume cuatro campañas de calibración y, sobre todo,
**los errores que ya se cometieron** para no repetirlos.

## Qué es esto

Motor de simulación de Magic en C + buscador de mazos en Python. Objetivo: armar el mejor mazo
posible con la colección real de Ricardo (371 cartas físicas, `data/collection.csv`) y **declarar
honestamente cuánto hay que creerle al número**.

Ricardo juega en papel, en tienda local. Formatos que le importan, en orden:
**Standard Brawl** (lo que corre su tienda) > Pauper > Standard.
Estilo: control de prisión — negarle el juego al rival. Viene de Pokémon TCG.
Presupuesto declarado para mejorar: US$200-600.

## Reglas de trabajo que ya costaron caro aprender

1. **Nunca reportes un winrate del motor como predicción.** Da dos números: el índice bruto
   (sirve para comparar listas entre sí) y la estimación comprimida por `src/escala.py`.
2. **Toda mejora se mide contra `src/obj_real.py` antes de adoptarse.** "Es más correcto según
   las reglas" no es evidencia. El bloqueo en grupo era correcto y empeoraba el ajuste.
3. **Después de tocar el motor, revalida los mazos** (`src/revalidar.py`): si una lista dejó de
   ganarle a su semilla codiciosa, hay que rehacer la búsqueda.
4. **Un cambio de modelo reabre el espacio de parámetros.** Vuelve a correr `src/tune_real.py`.
5. **Verifica legalidad y armabilidad** con `src/check_legal.py` antes de entregar cualquier lista.
6. **Mide con semillas independientes.** Las búsquedas mienten con su propia semilla: la de Brawl
   decía +2,75 y con semillas nuevas era +0,35.

## Estado actual del motor — LEE ESTO ANTES QUE NADA

El 17-ago-2026 se cambio el banco de Pauper por dato de **77.000 partidas**
(mtgdecks.net, sin espejo, `data/wr_mtgdecks_sin_espejo.json`) en lugar de medias de
4-6 semanas de 180-640 listas. Eso reescribio lo que sabiamos:

```
$ bash scripts/build.sh          # SIEMPRE los dos binarios, ver la seccion del .exe viejo
$ python3 src/obj_real.py 2000
sta cal 0.01 (r=+1.00 x3.2) | pau cal 0.82 (r=+0.69 x8.2) | bra resid  0.03
OBJETIVO 0.608
```

El salto de 1,072 a 0,608 es entero de `ATAQUE_LETAL` (el ataque no sumaba el dano de
todos los atacantes) y entero en Brawl: el residuo pasa de 2,06 a 0,03. Validado en 5
semillas independientes: **0,603 con la bandera contra 1,091 sin ella, sd 0,084**, casi
seis veces el ruido. Pero leelo con la reserva que esta mas abajo: el dato real de Brawl
son DOS winrates de ladder.

| Formato | Correlación | ¿Le gana al modelo tonto? | Veredicto |
|---|---|---|---|
| Pauper | r=+0,68 (n=6) | **SÍ** — 1,11% contra 1,25% | **aporta informacion** (desde 18-ago) |
| Standard | r=+0,74 (n=4) | sí, apenas — 2,31% contra 2,44% | n=4 y dato pre-ban: no vale |
| Standard Brawl | 2 datos | sin muestra | solo desplazamiento |

> **EL OBJETIVO YA NO ES BUEN ÁRBITRO, Y HAY QUE SABERLO ANTES DE USARLO.**
> Tres arreglos de lectura de cartas (ver la sección de la auditoría) subieron el
> objetivo de **0,608 a 0,955** —o sea "empeoraron"— y a la vez:
>
> | | antes | después |
> |---|---|---|
> | residuo de campo en Pauper | 8,11 pts | **5,51 pts** |
> | desplazamiento en Pauper | −2,4 | **−1,2** |
> | LOOCV Pauper contra modelo tonto | **pierde** −0,17 | **gana** +0,14 |
> | sobredispersión de Pauper | ×8,2 | **×5,9** |
>
> El objetivo mide **correlación de ORDEN**. En Pauper el orden real está dentro de
> 1,04 puntos con ±1,2 a ±1,7 de error de medición: **el orden no es recuperable ni en
> principio**. En Standard son 4 mazos pre-ban dentro de 5 puntos. Así que el objetivo
> está optimizando un ranking que no existe, y premia errores grandes cuando conservan
> la posición: con el motor viejo, Mardu Discard erraba −8,4 puntos y Mono Red Rally
> −17,3, y el objetivo estaba más contento.
>
> **Mide con `calib_real.py` (residuo y desplazamiento) y `loocv.py`, no solo con
> `obj_real.py`.** El objetivo sigue sirviendo como control de reproducibilidad y para
> cambios de política, no para juzgar si una carta está bien leída.

**Pauper es un formato casi plano.** La dispersion real entre arquetipos es de **1,04
puntos** y el error de medir cada uno es de ±1,2 a ±1,7 al 95%: la separacion es del
mismo tamanio que el error. Con eso, "predice 50% para todos" es casi optimo, y el motor
no le gana. Es exactamente el caso que `docs/metodologia.md` llama formato imposible.

El suelo de ruido, ahora calculable en binomial directo, es **0,76 puntos**. El modelo
tonto esta en 1,25% y el motor en 1,31%.

**Lo que esto invalida.** Todo lo que se adopto contra el banco viejo se midio contra
ruido. Revalidado contra el nuevo:

| cambio | contra banco nuevo |
|---|---|
| Arreglo de combate (`BLOQ_LIBRE`) | **ayuda**, +0,074 al quitarlo |
| Las dos reglas del extractor (`REGLAS_OFF`) | **ayuda**, +0,054 al quitarlo |
| Ranura de cementerio (`MUERTE_ON`) | irrelevante, −0,004 |
| Habilidades activadas (`ACTIVADAS_ON`) | irrelevante, +0,003 |

Las dos primeras se sostienen. Las dos ranuras nuevas quedan encendidas porque son
modelos mas correctos y no cuestan nada, pero **su gran mejora aparente era ruido**: la
de cementerio parecia llevar el error de 1,32 a 0,58 contra el banco viejo.

**Lo que NO invalida, y conviene no perder de vista.** Que el motor no ordene bien seis
arquetipos separados por un punto NO significa que no sirva para lo que se construyo.
Comparar listas propias entre si —que es lo que hace `run_all.py`— es otro problema:
ahi las diferencias son de 10-13 puntos contra la semilla codiciosa, no de uno. El
indice bruto sigue valiendo para eso. Lo que hay que dejar de afirmar es que el motor
predice el metajuego de Pauper.

## El suelo de ruido de Pauper, y por qué no es un muro

`src/suelo_ruido.py` estima cuánto margen queda. Los winrates contra los que se mide el motor
no son la verdad: son medias de unas pocas semanas de MTGO, cada una con su ruido de muestreo.
Sobre las series de `REAL_SEMANAL`: dispersión semana a semana **4,68 puntos** (14 g.l.), que en
binomial equivale a N≈114 partidas no-espejo por semana. O sea, es muestreo, no metajuego.
De ahí sale un suelo de **3,25 puntos** (2,21 descartando la serie más volátil).

**El motor está hoy en 0,95%, por debajo de esa estimación.** No lo tomes como que está
sobreajustado ni como que el suelo se "superó": lo que dice es que **el suelo era una cota
superior**, por tres motivos que conviene tener presentes al volver a usarlo:

- la dispersión semanal mezcla ruido de muestreo con deriva real del metajuego;
- se calcula con muy pocos grados de libertad, y una sola serie volátil la domina;
- a los arquetipos con una sola medición se les asigna la sd entera, que es su error
  *esperado*, no el que realmente tienen. Aportan el 69% del total.

Y una advertencia que sí se sostiene: `loocv.py` deja un mazo fuera, pero **no** protege de
haber elegido los cambios mirando el banco entero. Contra eso solo sirve dato nuevo.

Standard y Brawl **no son calculables**: el suelo necesita mediciones repetidas del mismo
arquetipo, y ninguno de los dos las tiene. Standard viene de un evento único (los Regional
Championships) y Brawl solo tiene dos winrates sueltos de ladder. Es el mismo motivo por el que
`escala.py` se niega a calibrar el nivel de Brawl: con n=2, y siendo los dos del 73-77%, ajustar
una recta devolvería 90% para cualquier cosa.

### Dónde sigue equivocándose

| Arquetipo | Motor | Real | Error |
|---|---|---|---|
| Mono Red Rally (Pauper) | 32,1% | 46,4% | **−14,3** |
| Blue Terror (Pauper) | 43,5% | 52,0% | −8,5 |
| Mardu Discard (Standard) | 41,2% | 49,9% | −8,7 |
| Izzet Spellementals (Standard) | 45,2% | 51,1% | −5,9 |
| Mono Red Madness (Pauper) | 48,1% | 53,0% | −4,9 |

Ojo con leer esta tabla como una lista de tareas. El objetivo mide **orden**, no error
absoluto, y un análisis de la recta real=f(motor) mostró que varios de estos residuos son
compresión, no desorden: con el motor anterior, Mono Red Rally ya estaba en su posición
relativa correcta (−0,3 respecto de la recta) y Jund Wildfire era en realidad el mazo más
*sobre*valorado del banco. Antes de atacar un arquetipo, comprueba si su residuo rompe el
orden o solo refleja la sobredispersión que la escala ya perdona.

**Regla 4: el descenso no ha encontrado nada en dos campañas.** `tune_real.py` propone siempre
`SWEEP_MIN=3` y siempre se cae en la validación (+0,002 y +0,003 con sd de 0,015-0,029). Es un
fantasma de la semilla canónica. Los defaults compilados se quedan.

> **El objetivo tiene ruido de semilla de ±0,02.** El valor que imprime `obj_real.py` es el de
> la semilla canónica 1234567 y sirve como control de reproducibilidad, no como medida fina.
> Cualquier "mejora" menor que eso es ruido: pásala por `src/valida_semillas.py` antes de
> adoptarla. Ahí se han caído tres cambios que eran más correctos según las reglas.

## Seis cambios correctos que ajustan peor: el patron

Esto ya no es anecdota y conviene leerlo antes de proponer nada. Seis cambios que son
mas fieles a las reglas de Magic que el motor, implementados y medidos, y los seis
empeoran el ajuste contra dato real:

| cambio | ablacion | efecto |
|---|---|---|
| Bloqueo en grupo | `GANG_ON=1` | residuo 4,0 → 8,0 |
| Burning-Tree Emissary se paga sola | `ETBMANA_ON=1` | +0,015 |
| Recursion de cementerio | `RECUR_ON=1` | neutro |
| Politica aprendida por autojuego | `POLNET=…` | −0,066 antes de arreglar el motor, **+0,025 despues** |
| Fichas como criaturas de verdad | `FICHAS_REALES=1` | +0,94, y re-tunear solo recupera 0,12 |
| Sin objetivo legal no se lanza (601.2c) | `NOTARGET_DURO=1` | +1,54 |

Y en el otro lado, lo que SI funciona son siempre lecturas de texto que faltaban: costes
alternativos, locura, dano a cada oponente, drenaje de vida, el retroceso de Lava Dart.
Ninguna toca la politica de juego.

**La lectura, y es incomoda.** Cuando el motor deja de leer una carta a medias, gana. Cuando
se le corrige *como juega*, pierde. Eso sugiere que sus heuristicas de juego estan
ajustadas encima de sus propios errores, y que el ajuste global se sostiene por
compensacion mutua, no porque cada pieza sea correcta.

La hipotesis obvia —"basta con re-tunear encima"— se probo con el caso mas claro, las
fichas, y **quedo refutada**: el descenso completo sobre los diez parametros recupero
0,124 de 1,084, o sea el 11%.

Consecuencia practica: **antes de implementar una mejora de reglas, pregunta si toca
como se LEE una carta o como se JUEGA.** Lo primero suele pagar. Lo segundo casi nunca, y
conviene medirlo con una ablacion desde el principio en vez de adoptarlo y descubrirlo
despues.

## Que hace Jund Wildfire que el motor no ve, y por que no se arreglo

El nombre engaña: no es un mazo de tierras, es un **motor de sacrificar artefactos por
valor**, y el motor le ve la mitad a cada carta.

| carta | texto real | como lo lee el motor |
|---|---|---|
| Krark-Clan Shaman ×3 | sacrifica un artefacto: 1 daño a **cada** criatura sin volar | remoción de un objetivo |
| Ichor Wellspring ×2 | roba al entrar **o al ir al cementerio** | un solo robo |
| Nihil Spellbomb ×4 | roba **al morir**, no al entrar | robo al entrar |
| Blood Fountain ×2 | ficha de Sangre y recursión desde el cementerio | nada |

Las dos hipotesis obvias se probaron y las dos EMPEORAN (medido con `FICHAS_REALES=1`,
que es el mundo donde el hueco de Jund existe; referencia 2,266):

    krark_barredor_repetible    3,102   y Jund cae a 28,2%
    robo_al_entrar_y_al_morir   2,412

**Y el motivo es el mismo en las dos: la ranura, no la lectura.**

- `E_SWEEPER` se dispara al entrar y sin eleccion. El Shaman es un 1/1, asi que se
  suicida y arrasa su propio tablero, que lleva tres Shaman y una Nyxborn Hydra 1/2. En
  la realidad el jugador elige cuando activar, y paga un artefacto por vez.
- `E_ETB_DRAW` es inmediato. El segundo robo de Ichor Wellspring solo llega cuando el
  artefacto muere; adelantarlo lo convierte en un cantrip de dos cartas por dos mana,
  que no es la carta.

**La leccion, que vale mas que Jund:** una habilidad ACTIVADA no se puede aproximar con
un efecto de entrada, y un disparo DIFERIDO tampoco. No son aproximaciones conservadoras:
cambian el tempo, que es justo lo que el motor mide.

### Desenlace: las dos ranuras se construyeron, y funcionan

| ranura | campos | ablacion | efecto |
|---|---|---|---|
| Disparo al ir al cementerio | `die_eff`/`die_p1`, disparo en `rmbf()` | `MUERTE_ON=0` | 1,270 → **1,022** |
| Habilidad activada con coste | `act_eff`/`act_p1`/`act_cost`, `activar_habilidades()` | `ACTIVADAS_ON=0` | 1,022 → **0,978** |

La prueba de que el diagnostico era correcto: Krark-Clan Shaman, **la misma carta con la
misma lectura**, midio 3,102 como barredor de entrada y 0,978 como habilidad activada.
Lo que cambiaba era la ranura, no el texto.

Detalles que importan al ampliarlas:

- `apply_die` reutiliza el switch de `apply` copiando el `Def` a una entrada temporal con
  el efecto en la ranura primaria. No dupliques los cincuenta casos.
- El extractor separa *"enters **or** is put into a graveyard"* (dispara dos veces) de
  *"is put into a graveyard"* (solo al morir). En el segundo caso el robo que la regla
  generica daba al entrar estaba **mal puesto** y hay que MOVERLO, no sumar otro.
- Busca en la linea entera y no hasta el primer punto: Nihil Spellbomb parte el efecto en
  dos frases.
- Al pagar un coste de sacrificio el tablero se reordena, asi que hay que re-localizar la
  carta por su `Def` antes de aplicar el efecto.
- La ranura de activadas hoy solo cubre *"sacrifica un artefacto: N danio a cada
  criatura"*. Faltan costes de mana, girar y sacrificarse, que es media Pauper.

**Lo que NO desbloquearon.** Se reprobo `FICHAS_REALES` con las dos ranuras puestas y
sigue sin pagar: 0,978 → 2,488, con Jund todavia en −18,7. Su hueco es mayor que lo que
arreglan estas dos ranuras.

## Los tres hallazgos que quedaban, y el .exe viejo que casi los entierra

Quedaban tres puntos de `data/errores_juego.md` sin probar. Se implementaron los cuatro
arreglos (el 4 se partio en dos) y se midieron de uno en uno. Contra la base de 1,072:

| bandera | que arregla | sintetico | contra dato real |
|---|---|---|---|
| **`ATAQUE_LETAL`** | el ataque no suma el dano de todos los atacantes | 57,5% → **99,3%** | **0,609 (−0,463)** |
| `REMATE_LETAL` | `E_BURN_FACE`/`E_ETB_DRAIN` no saben que rematan | 3,22 → **2,23** turnos | 1,073 (+0,001) |
| `LORD_VE` | remocion y barridos ven el bono de lord | 1,74 → **0,16** muertes | 1,072 (+0,000) |
| `KW_ATAQUE` | amenaza / dano primero / indestructible al atacar | 24,3% → **98,0%** | 1,204 (**+0,132**) |

**El ataque letal agregado es la mejora mas grande del proyecto: 23 veces el ruido de
semilla.** Se adopta. `REMATE_LETAL` y `LORD_VE` se dejan encendidas por ser modelos mas
correctos y gratis. `KW_ATAQUE` queda **apagada**.

### El error que produjo media pagina de conclusiones falsas

La primera medicion de las cuatro dio **cero clavado en todas**, y se documento aqui una
teoria elaborada sobre por que el banco no tenia materia para medirlas. Era falso de
principio a fin: **`bin_brawl` estaba viejo.**

`bin_brawl` no se compila de `sim.c`. Se compila de `src/sim_brawl.c`, que `gen_brawl.py`
**genera** a partir de `sim.c`. Tocar el motor y recompilar solo `bin_sim` deja Brawl
corriendo con el codigo de antes, y eso **no da ningun error: da numeros**. El residuo de
Brawl estaba congelado en 2,06, y como estos cuatro cambios actuan casi solo en Brawl,
ninguno se veia. Al regenerar el binario por otro motivo, el residuo cayo a 0,04.

> **Guarda puesta.** `src/salud.py` compara fechas de binarios y fuentes, y
> `obj_real.medir()` **se niega a medir** si algo esta viejo (`SALUD_OFF=1` lo salta).
> Recompila siempre con `bash scripts/build.sh`, que hace los dos. Y cuando cambies el
> protocolo de cable, `bin_brawl` **tiene** que regenerarse o `run_brawl` devuelve listas
> vacias.

### Lo que sigue siendo verdad de aquella pagina

- **Cuenta la materia antes de medir.** `src/chk_hallazgos.py` cuenta en los 19 mazos: 8
  criaturas con amenaza, 1 con dano primero, 1 indestructible y 4 copias de un solo lord.
  Las 19 "indestructibles" que parecia haber eran Darksteel Citadel, que es una tierra y
  no ataca jamas. Para `LORD_VE` y `KW_ATAQUE` el banco de verdad da poco.
- **Dos bancos, dos preguntas.** `src/sintetico.py` responde *¿el arreglo funciona?* con
  mazos artificiales que aislan un comportamiento; `src/laboratorio.py` responde *¿conviene
  adoptarlo?* contra dato real. Ninguno sustituye al otro.

### Lo que hay que leer con cuidado

**Toda la ganancia de `ATAQUE_LETAL` esta en Brawl, cuyo dato real son DOS winrates de
ladder.** Standard y Pauper no se mueven. Con n=2 no se puede separar "el motor mejoro" de
"el motor ahora acierta dos numeros". Lo que si es independiente del ajuste: los dos mazos
de Brawl marcaban 62% de motor contra 75% real —partidas demasiado lentas— y esto es justo
lo que hace que un mazo cierre las que ya iba ganando.

Y `KW_ATAQUE` es el **noveno** cambio mas-correcto-que-ajusta-peor, esta vez con aviso
previo: `sensibilidad.py` dice que subir a Ketramose cuesta +0,449, y Ketramose es
indestructible **y** tiene amenaza, o sea que la bandera lo habilita por partida doble. Ese
numero estaba delante y no se miro. **Consulta `sensibilidad.py` ANTES de implementar.**

## Costes que bajan con el tablero: correcto, y ajusta peor (el decimo)

Izzet Spellementals lleva 4 Eddymurk Crab y 4 Sunderflock, las dos con rebaja de coste. El
extractor ya tenia `cost_reduction()`, que aplica una rebaja **plana** estimada a ojo, pero
su patron exige `{N}` con digitos: `{X} less to cast, where X is the greatest mana value
among Elementals you control` no casa, y **Sunderflock se quedaba a 9 mana, muerta**.

Se construyo la rebaja **dinamica** (`Def.cred`, `P.gy_is`, `pay_gen`), que la calcula
mirando el tablero y reemplaza a la plana. Medido contra la base 0,608:

| | objetivo | delta |
|---|---|---|
| `cred=1` Eddymurk dinamico en vez de −4 plano | 0,675 | +0,067 |
| `cred=2` Sunderflock deja de estar muerta | 0,846 | **+0,238** |
| las dos | 0,854 | +0,246 |

**Apagado** (`CRED_ON=1` para activarlo). Dos cosas que aprender:

- `cred=1` no toca solo a Eddymurk: **Cryptic Serpent**, la amenaza de Blue Terror en
  Pauper, lleva el mismo texto, y el dano de esa mitad esta en Pauper (0,82 → 0,91), no en
  Standard. Comprueba **todas** las cartas que casa un patron, no solo la que te llevo a el.
- `cred=2` rompe el orden de Standard (r=+1,00 → +0,81). La leccion no es que Sunderflock
  deba seguir muerta: es que **el motor sobrevalora volador gordo + rebote masivo**, y al
  darle acceso a esa carta el error se hace visible. Eso es un hallazgo sobre el motor.

El codigo se queda, con `P.gy_is` contando instantaneos y conjuros que van al cementerio.
Es lo primero parecido a un cementerio que tiene el motor y sirve para umbral y delirio.

## El entrenador se estaba mintiendo: +2,135 eran +1,25

El orquestador reportaba que la politica aprendida ganaba **+2,135 puntos** en autojuego.
Es falso, y el error es estructural, no un bug de una linea:

```
base    = UNA evaluacion de la heuristica, en la semilla 1234567
mejor_f = el MAXIMO de ~1.000 evaluaciones, una por generacion
```

El maximo de mil tiradas ruidosas queda muy por encima de la media aunque no se haya
aprendido nada. Re-medido con `src/audita_politica.py` en 12 semillas limpias y
**emparejadas** (la heuristica y la politica juegan las mismas partidas):

| | reportado | real |
|---|---|---|
| politica guardada | +2,135 | **+1,251 ± 0,056** |
| mu (el centro de lo aprendido) | — | +1,187 ± 0,042 |

O sea **el 41% del numero era seleccion sobre ruido**, y el maximo ni siquiera compro una
politica mejor que su propio centro (+1,251 contra +1,187, indistinguible).

La pista estaba en el log a simple vista: `elite` y `media` alternaban casi un punto entre
generaciones pares e impares y `mu` alternaba en **anti-fase**. La semilla es
`900000+g*7919`, cuya paridad alterna con `g`, y mu se evalua en `semilla+1`, siempre en la
paridad contraria. El efecto de paridad medido sobre la MISMA heuristica es −0,169 puntos.

Arreglado: `entrenar_politica.py` ahora valida cada 20 generaciones contra semillas que no
participan en ninguna seleccion y reporta la ganancia emparejada. **Cuando un numero es el
maximo de una serie ruidosa, no es una medida: es una marca personal.**

Y lo que no cambia: ese +1,25 real en autojuego **sigue sin transferirse** al dato real.
Los ciclos 13 al 23 dan entre −0,004 y +0,012, todo ruido. Ojo al leer ese log: el banco
nuevo entro a las 19:26, entre el ciclo 4 y el 5, asi que los primeros ciclos se midieron
contra el banco viejo y no son comparables con los siguientes.

## Standard Brawl, 18-ago: el blanco NO era el camino

La pregunta era "¿el blanco es mi camino?". El buscador decía que sí y estaba apoyado en
cartas mal leídas. Con el motor corregido, **los seis mejores comandantes de la colección
son negros** y el blanco cae al puesto 10:

| | obj | | obj |
|---|---|---|---|
| The Sackville-Bagginses (B) | 32,69 | Bolg of the North (BR) | 22,10 |
| Gollum, Silent Slinker (B) | 31,62 | Belladonna Took (W) | 21,85 |
| Gollum the Abandoned (B) | 29,34 | Momo, Playful Pet (W) | 21,65 |
| Tom, Bert, and William (BG) | 28,98 | Thorin Oakenshield (RW) | 19,92 |

**Dáin ni aparece en el top 14**, y antes marcaba 51,44. Su nota venía de que el motor
gravaba lanzar hechizos en vez de atacar, y sin exigir Storied.

Gana **Gollum, Silent Slinker // Meager Meal** con 33,2% contra el campo: cuarto de siete,
por encima de Tifa, Kona y Eluge y por debajo de Sephiroth, Ketramose y Elspeth. Informe
completo en `out/informe_brawl.md`, que lo genera `src/informe_brawl.py`.

**Dos avisos sobre esa búsqueda.** La ventaja sobre la semilla codiciosa es de solo
**+1,56** (31,62 → 33,18), muy lejos de los +13/+14 de Standard y Pauper: en Brawl,
singleton y con un pool chico, el buscador casi no tiene margen. Y el motor lee bien 77 de
las 204 cartas de la colección, así que las 51 mudas están **infravaloradas** y el
buscador las descarta por defecto.

## Trampas ya encontradas (no las repitas)

- **"Add one mana of any color. Spend this mana only to cast X" se lee sin la
  restricción.** Jasmine Dragon Tea Shop queda con `produces=31`, o sea una tierra de
  cinco colores perfecta. En un mazo mono-color da igual —medido, 33,22% con ella y con un
  pantano— pero le haría creer al buscador que puede armar cinco colores con una tierra
  que en realidad solo paga Aliados.

La lista larga, con síntoma y arreglo de cada una, está en `docs/trampas.md`. Ese archivo manda;
esto es el resumen.

- **"Its controller loses N life" no lo cubría nadie, y ahí estaba el peor error del proyecto.**
  La regla de pérdida de vida leía `each opponent loses` y `target player/opponent loses`, pero
  no la forma que usan las remociones con drenaje. Inevitable Defeat —*"Exile target nonland
  permanent. Its controller loses 3 life and you gain 3 life"*— se modelaba como exilio a secas:
  cuatro copias, 24 puntos de swing de vida invisibles. **Four-Color Control pasó de 33,2% a
  51,5%.** Ablación: `DRAIN_CTRL=0`.
- **Un candado `if out['eff']==NONE` esconde efectos en cartas multimodo.** La ganancia de vida
  solo se leía en cartas que no hicieran nada más, cuando `setp` ya elige la primera de tres
  ranuras libres. Jeskai Revelation e Inevitable Defeat perdían su mitad de vida por eso.
  Cuando veas ese candado, pregúntate si está protegiendo algo o solo tapando efectos.
  Ablación: `LIFEGAIN_ANY=0`. Ojo aparte: Jeskai Revelation tiene **cinco** modos y solo hay
  tres ranuras, así que sigue perdiendo el rebote. Ese es un límite del formato, no un bug.
- **Las listas del banco también pueden estar mal, y eso no da ningún error.** Mono Red Madness
  llevaba 4 Sneaky Snacker, un Hada `{U}{B}`, en una lista con 19 Montañas: cuatro cartas que el
  motor no puede lanzar jamás y que hunden al arquetipo en silencio. No es colisión de nombres,
  la lista está mal. Corre `src/chk_castable.py` cada vez que toques `data/meta_decks.py`.
- **Una regla de daño que no cubre "each opponent" borra medio hechizo.** La regla general
  cubría `target creature`, `any target` y `target player`, pero no `each opponent`. Grab the
  Prize —*"discard a card. Draw two cards. If the discarded card wasn't a land, deals 2 damage
  to each opponent"*— se modelaba como robar dos cartas y nada más. Añadir la rama bajó el
  objetivo de 2,256 a 1,959, doce veces el ruido. Ablación: `BURNEACH=0`. Ojo al añadirla: hay
  que excluir las líneas que empiezan por `when`/`whenever` o se cuentan dos veces las criaturas
  con disparo (Guttersnipe, Kessig Flamebreather, Voldaren Epicure).
- **La locura es un coste alternativo con otro nombre.** Fiery Temper vale `{1}{R}{R}` y se lanza
  por `{R}` al descartarla; Mono Red Madness lleva once formas de descartar, así que en la
  práctica es un Rayo de un maná. Cobrarla a 3 es el mismo error que cobrar Fireblast a 6.
  Reescribir su coste al de locura bajó el objetivo de 1,959 a 1,799. Ablación: `MADNESS=0`.
  Se asume que hay descarte disponible: si algún día entra una carta con locura en un mazo sin
  descarte, hay que condicionarlo.
- **Arreglar un arquetipo aislado puede empeorar el ajuste, aunque el arreglo sea correcto.**
  El objetivo mide correlación de ORDEN. Modelar bien a Burning-Tree Emissary sube a Mono Red
  Rally y aun así empeora el total, porque lo comprime contra su vecino en la tabla. Se probó
  tres veces —antes y después de arreglar Madness— y las tres empeoró. Mira siempre el desglose
  por arquetipo antes de culpar al cambio. Apagados: `ETBMANA_ON=1`, `RECUR_ON=1`.
- **Los costes alternativos no son un detalle: son el hechizo entero.** Fireblast se juega
  sacrificando dos Montañas y Snuff Out pagando 4 vidas. Cobrarlos a 6 y a 4 de maná hacía que el
  motor **no los lanzara nunca**, y eso solo dejaba a Mono Red Madness 17,7 puntos por debajo de
  su winrate real. Modelado en `extract.py::alt_cost` + `sim.c::alt_ok/alt_pay`, el objetivo bajó
  de 2,543 a 2,271 y la r de Pauper subió de +0,73 a +0,82. Ablación: `ALTCOST=0`.
  **Pero la política importa tanto como el coste:** dejar que sacrifique tierras cuando quiera da
  2,580 —peor que no tenerlo— porque se mutila la base de maná en el turno 3. Fireblast se lanza
  para rematar, así que solo se permite si el daño mata. Medir la regla, no solo la carta.
- **El robo recurrente no dispara solo en el mantenimiento.** La regla leía únicamente
  `at the beginning of your upkeep ... draw`. The Arkenstone // Seek the Heart roba en el **paso
  final**, así que quedaba modelada como un lord pelado de 5 maná, sin motor de robo. Corregido en
  `src/extract.py`: cubre mantenimiento, paso final, paso de robo y ambas fases principales.
  Cuando agregues una rama de texto, revisa **todos** los pasos en que puede dispararse.
- **Un fix repartido entre Python y C hay que commitearlo entero, o no existe.** El arreglo
  anterior tiene dos mitades: `extract.py` etiqueta la carta y `sim.c` tiene que leer la etiqueta.
  `upkeep()` solo miraba `d->eff` y estas cartas traen el motor de robo en `d->eff2` (LORD ocupa
  la ranura primaria), así que el extractor etiquetaba y el simulador ignoraba. Del commit
  `8ac8adc` salió solo la mitad en Python: el árbol daba 2,557 mientras la documentación decía
  2,540. **Es la misma trampa de "keywords parseadas que nadie lee", una campaña después.**
  Al tocar una ranura, revisa si el motor la lee en `eff`, `eff2` y `eff3` — `E_LORD` y `E_TAX`
  se leen en dos, `E_UPKEEP_DRAW` se leía en una sola.
- **El descenso mide con una sola semilla, así que encuentra mejoras que no existen.**
  `SWEEP_MIN=3` bajaba el objetivo de 2,543 a 2,534 y era ruido: con 5 semillas queda peor que
  el default. **Lo propuso otra vez en la campaña siguiente** (2,271 → 2,262) y volvió a caer
  en la validación (+0,003, sd 0,029). Es un fantasma sistemático de la semilla canónica, no
  un hallazgo: si `tune_real.py` te ofrece `SWEEP_MIN=3`, ya está descartado dos veces. Peor todavía, la "ganancia" venía entera del residuo de Brawl —2 datos reales—
  mientras la correlación de Standard caía de +0,16 a +0,07. **Mira los componentes, no el
  agregado, y pasa todo candidato por `src/valida_semillas.py`.**
- **`out/tuned_real.json` guardaba solo los overrides, y se autoborraba.** Como el descenso deja
  `None` cuando se queda con el default compilado, en cuanto horneas un valor en `sim.c` la
  corrida siguiente lo saca del archivo: pasó de seis parámetros a uno. Ahora guarda el set
  **efectivo** además del override, leyendo los defaults de `sim.c`.
- **Verifica que el número documentado se reproduzca desde el árbol limpio.** Un `git status`
  limpio no garantiza que lo medido sea lo commiteado: si mediste con el working tree sucio y
  después commiteaste solo una parte, el número queda huérfano. Corre `obj_real.py` justo
  después de commitear.
- **Identidad de color donde no aplica.** En Standard y Pauper la identidad de color **no existe**:
  basta con poder pagar la mitad que lanzas. Solo aplica en Brawl y Commander. The Arkenstone
  cuesta `{5}` el artefacto y `{2}{W}` la aventura, así que su identidad es blanca y aun así entra
  en cualquier mazo de Standard. Auditada la colección: 28 cartas con cara frontal incolora e
  identidad de color, y las otras 27 son híbridas o duales, que sí se filtran bien.
- **Fichas en el bulk de Scryfall.** 910 entradas de ficha y 2.243 de art series; 88 nombres
  existen a la vez como ficha y como carta real. Si gana la ficha, la carta queda `not_legal` con
  estadísticas de ficha. Corregido en `src/driver.py::oracle()`.
- **`deals N damage to any target` no es quemar a la cara.** Modelarlo así deja a todos los mazos
  rojos sin interacción.
- **`untap target creature` contiene `tap target creature`.** Usa `\b` siempre.
- **`sacrifice a land` casi siempre es un coste propio**, no un ataque al rival.
- **Maná híbrido:** `{B/G}` cuesta 1 maná que debe ser B o G. Contrasta `generico+pips` contra el
  `cmc` de Scryfall.
- **Cartas de doble cara:** `mana_cost` viene `{W} // {1}{W}`. Usa la cara frontal.
- **Legalidad de Brawl:** el campo es `standardbrawl` (4.902 cartas legales), no `brawl`, que es
  Historic Brawl (15.722 cartas legales; el 100 es el tamaño del mazo, no el pool).
  Standard Brawl tiene banlist propia y hoy está **vacía**: los 13 bans son solo de Standard.

## Lo que sigue pendiente

1. **Conseguir más dato de Pauper, que ahora vale más que cualquier cambio de modelo.** El motor
   está en el suelo (3,13% contra 3,25%), así que lo único que mueve la aguja es bajar el suelo.
   Dos vías, en orden de rentabilidad: **(a)** más semanas para Grixis Affinity y Elves, que
   tienen una sola medición y aportan el 69% del ruido; **(b)** integrar Dimir Faeries y Gruul
   Ponza al banco (listas ya validadas en `data/nuevos/listas.txt`), que sube n de 6 a 8.
   Las series semanales van en `REAL_SEMANAL` de `data/real_wr.py`, no en un comentario.
2. **Estimar el suelo de ruido.** Los recaps semanales de Pauper dan medidas repetidas del mismo
   arquetipo (Mono Red Madness: 47,4 / 47,3 / 49,6 / 50,8 / 49,3 / 56,4 / 52). La desviación
   semana a semana es ruido de muestreo puro: ~2-3 puntos. **Ningún modelo puede bajar de ahí.**
   El error del motor en Pauper es 3,93%. Queda poco margen — conviene calcularlo bien antes de
   invertir más esfuerzo. **Esta es la prioridad de Ricardo.**
3. **Ampliar el banco de Pauper.** Es el formato con dato fresco y semanal (MTGGoldfish "Power of
   Pauper", el último es del 6-9 agosto) y donde el motor funciona. Listas ya validadas y sin
   integrar: Dimir Faeries, Gruul Ponza (ver `data/nuevos/listas.txt`). Pasar de n=6 a n=8 mejora
   la estimación de k, la de r y el objetivo de ajuste.
4. **El dato de Standard es pre-ban** — contexto, no tarea. Los winrates reales que hay son de los
   Regional Championships del 17-18 mayo 2026. Después hubo 13 bans (Badgermole Cub, Gran-Gran,
   Stormchaser's Talent y 10 más). **Estamos comparando listas de hoy contra winrates de otro
   formato.** No hay winrates de Standard publicados entre junio y agosto 2026 — se buscó.
   Mientras eso siga así, no tiene sentido intentar mejorar el ajuste de Standard.
5. **Cuatro Colores Control**: 33,9% en el motor contra 53% real. El peor error que queda.
   El motor no sabe que acumular cartas es un plan de victoria.
6. **Costes alternativos**: Fireblast se juega sacrificando dos montañas; el motor lo ve a 6 maná
   y no lo lanza nunca.
7. **Sin sideboard.** Los winrates reales son de partidas al mejor de tres; el motor juega un
   juego. Explica buena parte de la sobredispersión que queda.

## Comandos

En **Windows** hay dos cosas que saber. Una: `python3` usa la codificación local (cp1252) para
`open()` y 45 llamadas en 27 archivos no declaran `encoding`, así que los nombres con acento
—`Thrór's Map`, `Dáin`— revientan con `UnicodeDecodeError` o dan `KeyError`. Corre todo con
**`PYTHONUTF8=1`** por delante y funciona. Dos: `sim.c` es C puro (solo `stdio/stdlib/string/
stdint`, cero POSIX), así que compila con MinGW sin tocar nada; los binarios salen `.exe` y
`subprocess.run(['./bin_sim'])` los resuelve igual.

```bash
bash scripts/bootstrap.sh                     # bulk de Scryfall
bash scripts/build.sh               # LOS DOS binarios. No compiles a mano: bin_brawl se
                                    # genera de sim.c y olvidarlo no da error, da numeros
python3 src/salud.py                # ¿hay algun binario mas viejo que su fuente?

python3 src/obj_real.py 2000        # objetivo contra dato real (menor = mejor)
python3 src/loocv.py 2500           # ¿le gana a no simular nada?
python3 src/calib_real.py 2000      # informe detallado por formato
python3 src/xray.py "Mono Red"      # cómo quedó modelada cada carta de un mazo
python3 src/trazar.py standard "Four-Color" "Mardu"   # traza una partida turno a turno
python3 src/revalidar.py 2500       # mazos vs su semilla codiciosa
python3 src/tune_real.py            # descenso coordenada a coordenada (NG=2000 recomendado)
python3 src/valida_semillas.py 2000 "" "SWEEP_MIN=3"   # ¿sobrevive a semillas nuevas?
python3 src/escala.py 2000          # regenera data/escala.json (hazlo tras tocar el motor)
python3 src/build_report_v6.py      # regenera out/report_v6.json
python3 src/grafico.py              # out/avance.html: vista referencial del informe
python3 src/sintetico.py            # ¿el arreglo FUNCIONA? (mazos artificiales aislados)
python3 src/chk_hallazgos.py        # ¿tiene el banco materia para medir esta hipótesis?
python3 src/sensibilidad.py         # ¿subir este arquetipo ayuda o estorba? MÍRALO ANTES
python3 src/impacto_mazos.py "FLAG=1"   # ¿mueve el cambio a los mazos ya elegidos?
python3 src/audita_politica.py      # ¿la ganancia de la IA es real o máximo sobre ruido?
python3 src/suelo_ruido.py 3.13 4.40                       # ¿cuánto margen queda de verdad?
python3 src/tablero.py pauper "Mono Red" "Blue Terror" 8 12 # out/tablero.html: mira las partidas
python3 src/run_all.py              # búsqueda de mazos (Standard + Pauper)
python3 src/run_brawl.py            # búsqueda de Brawl
```

Variables de ablación (para medir un cambio con y sin él):
`DISABLE_EFF=<codigo>`, `NEG_ON=0`, `DMG_ANY_FACE=1`, `HEXWARD_ON=0`, `GANG_ON=1`, `TRACE=1`,
`ALTCOST=0`, `ETBMANA_ON=1`, `RECUR_ON=1`, `TRACE_JSON=<n>`.

## Mono Red Rally: por qué no se puede arreglar solo

Rally marca 36,4% contra 46,4% real. Tiene tres agujeros de modelado reales y verificados:
**Burning-Tree Emissary** (al entrar añade `{R}{G}`, se paga sola y encadena — el motor la ve
como un 2/2 vainilla), **Goblin Tomb Raider** (+1/+0 y prisa si controlas un artefacto, y el
mazo lleva 11 contando las tierras-artefacto) y **Galvanic Blast** (4 de daño con metalcraft,
el motor siempre le pone 2).

Se implementó el primero, que es el que define el arquetipo. Sube a Rally de 36,4% a 37,5%
y **empeora el objetivo global de 2,271 a 2,311**, el doble del ruido. Queda apagado
(`ETBMANA_ON=1`).

El motivo no es la carta, es el orden. El objetivo mide correlación de orden, y Rally **ya
estaba correctamente último** en el motor y en la realidad. Subirlo lo comprime contra Mono Red
Madness, que está infravalorado en −14 y debería quedar por encima:

| | Real | Motor |
|---|---|---|
| Mono Red Madness | 53,0% | 39,0% |
| Mono Red Rally | 46,4% | 36,4% |

**Para que arreglar Rally pague, hay que arreglar antes a Madness**, y su hueco es más grande:
todo su motor de valor es descartar y sacar provecho de lo descartado —locura, cementerio— y
eso no está modelado. Ojo: la recursión de cementerio ya se probó (`RECUR_ON=1`) y en Pauper
**no mueve nada**, así que las 4 Sneaky Snacker no son la explicación. El candidato que queda
es la locura (Fiery Temper) y el valor de los efectos de descarte.
