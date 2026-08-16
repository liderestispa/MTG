# Calibración: cómo saber si el motor sirve

Un simulador de Magic hecho a mano **siempre** tiene error de modelo. La pregunta no es si lo
tiene, sino cuánto y en qué dirección. Esto se mide, no se supone.

## El banco

`scripts/calibrate.py` enfrenta a todos los mazos del metajuego entre sí (round-robin) y mide
cuánto se desvía cada uno del 50% contra el campo ponderado.

```bash
python3 scripts/calibrate.py standard pauper brawl
```

**Por qué el 50% es el objetivo:** cada mazo juega contra un campo del que él mismo forma parte.
Si el motor fuera perfecto y el metajuego estuviera equilibrado, todos rondarían el 50%.

Dos métricas:

- **RMSE respecto al 50%**: cuánto se desvía el conjunto. Por debajo de 8 puntos el motor es
  utilizable para predicciones aproximadas; por encima de 15, solo sirve para comparaciones
  relativas dentro de un mismo arquetipo.
- **Dispersión** (máximo − mínimo): si el mejor da 90% y el peor 25%, hay un sesgo estructural,
  no ruido.

**Salvedad:** no todos los metajuegos están equilibrados. En un formato donde un mazo tiene el
23% de cuota y 77% de winrate reportado, el objetivo correcto no es 50% para él. Ajusta el
objetivo con los winrates reales publicados cuando existan.

## El sesgo que aparece siempre

**Los motores hechos a mano sobrevaloran los mazos de criaturas frente a los de hechizos.** El
combate es fácil de modelar; la ventaja de cartas acumulada y la inevitabilidad no.

Si tu matriz muestra que los mazos de puras criaturas ganan 85-90% y los de control 20-25%, no
tienes un metajuego desequilibrado: tienes un motor sesgado.

## Cómo cazar los bugs: el detector de implausibilidad

`scripts/audit_cards.py` marca cartas cuyo modelado no cuadra:

- Criatura con `poder + resistencia > 2·coste_efectivo + 5`
- Tres o más keywords por dos maná o menos
- Coste efectivo cuatro o más por debajo del cmc (reducción demasiado agresiva)
- P/T en una no-criatura
- Hechizo con texto largo y ningún efecto parseado

Cada carta que marca es un bug potencial. En un proyecto real esto encontró:

| Carta | Síntoma | Causa |
|---|---|---|
| Moonshadow | 7/7 por 1 maná | Entra con seis contadores −1/−1, ignorados |
| Hardened Academic | Vínculo vital estático | Es condicional: "Descarta una carta: gana vínculo vital" |
| Myr Enforcer | Costaba 7 | Afinidad no modelada |
| Tolarian Terror | Costaba 7 | "Cuesta {1} menos por cada instantáneo en tu cementerio" |

**Regla para keywords:** léelas **solo de líneas que contengan exclusivamente keywords**. Escanear
el texto entero convierte cada mención condicional en una habilidad estática, y eso infla mazos
enteros sin que se note.

## Bugs de motor que la calibración destapa

Ninguno de estos se ve leyendo el código; solo aparecen cuando mides.

**1. El defensor que nunca intercambia.** Si tu heurística de bloqueo es
`kills*10 - dies*8 - coste`, un bloqueo que mata y muere puntúa 0 con un bloqueador de coste 2,
y si la condición es `> 0`, **nunca se intercambia**. Atacar sale gratis y el agro arrasa.
Un intercambio debe valorarse claramente positivo: cuesta una carta a cada lado y frena daño.

**2. El control que no lanza nada.** Si reservas maná para instantáneos con un `break` del bucle
de lanzamiento, un mazo con un instantáneo en mano **jamás lanza sus conjuros**. Diagnóstico:
traza una partida e imprime el tamaño de mano por turno. Ocho cartas en mano al turno 4 con la
mesa vacía es la firma. La reserva debe ser una penalización en la puntuación, no un bloqueo.

**3. Mulligan sin penalización.** Robar siete cartas nuevas hasta que la mano guste, sin devolver
ninguna al fondo, infla la consistencia de todos los mazos y sobre todo la de los codiciosos.

**4. Límite de turnos que favorece al agro.** Si al agotarse el tiempo gana quien tenga más vida,
todo mazo de control pierde por definición. El desempate debe pesar tablero, cartas en mano y
biblioteca restante, no solo vidas.

## Traza una partida cuando no entiendas un número

Es la herramienta más rentable del proyecto. Un `fprintf` por turno con vidas, tamaño de mano,
tierras y permanentes de cada lado te dice en diez segundos lo que media hora de leer código no.

## Qué no se arregla (declaralo)

El descarte y la prisión se simulan mal en cualquier motor cuya IA vacíe la mano cada turno:
quitarle cartas a un rival que ya lo jugó todo no duele. Si mides un mazo de descarte al 20%
cuando su winrate real es 55%, no es que el mazo sea malo — es que tu motor no puede verlo.
Dilo, y para esos arquetipos pesa más el dato real del metajuego que tu índice.


## Los 16 bugs de un caso real (por si te sirven de checklist)

Una campaña de calibración completa bajó el RMSE global de 19,0 a 11,1. Esto es lo que encontró,
en orden de impacto:

| # | Bug | Efecto medido |
|---|---|---|
| 1 | Barredores matando criaturas **indestructibles** | −30 pts al mazo afectado |
| 2 | Contrahechizos **nunca usados**: se lanzaban proactivamente y los cantrips se comían el maná reservado | el mazo azul veía 24 contras por partida y usaba 0 |
| 3 | El **defensor nunca intercambiaba** en combate (la fórmula daba 0 y se exigía >0) | atacar era gratis |
| 4 | El **comandante** solo volvía a la zona de mando si moría en combate | 15 turnos sin comandante |
| 5 | Contadores de entrada ignorados | 7/7 por 1 maná |
| 6 | Reducción de coste sin modelar (afinidad, delve) | Myr Enforcer a 7 en vez de 3 |
| 7 | Tierras con producción fija de 1 maná | Tron injugable |
| 8 | Keywords condicionales como estáticas | +3 vidas por turno de la nada |
| 9 | Control paralizado por la reserva de maná (`break` en vez de `continue`) | 8 cartas en mano al turno 4 |
| 10 | Maná híbrido perdiendo su pip | 5/5 costando 3 |
| 11 | Doble cara sumando ambos costes | 1 maná contado como 3 |
| 12 | P/T característica (`*/*`) leída como cero | 0/1 en vez de 5/5 |
| 13 | Mulligan sin penalización de cartas | consistencia inflada para todos |
| 14 | Límite de turnos decidido por vidas | el control perdía por definición |
| 15 | Legalidad de Brawl con el campo `brawl` en vez de `standardbrawl` | pool 3× más grande de lo legal |
| 16 | Drawbacks ignorados ("no se endereza") | criaturas sin su desventaja |

**Mecánicas que hubo que añadir:** robo selectivo, criaturas de maná, motores de "cada vez que
lanzas un hechizo", fichas exponenciales y duplicadores, motores de exilio, y buffs condicionales
aplicados en combate.

## El techo que no se rompe, y cómo cuantificarlo

Tras corregir todo, un mazo de cartas de **Limited** seguía marcando 89% contra un meta de
**Constructed**. La causa se mide en una línea:

```
estadisticas por mana = (poder + resistencia) / coste, promediado sobre las criaturas
```

Las cartas de Limited dan ~2,0. Las de Constructed dan 1,3-1,9, porque cambian estadísticas por
habilidades. **Un motor que mide cuerpos y no habilidades premia sistemáticamente al pool de
Limited.** Cuando midas esa diferencia, sabrás cuánto descontar — y sabrás que el número absoluto
no es utilizable aunque la calibración meta-contra-meta esté bien.


---

# Segunda campaña: lo que aparece cuando el RMSE ya bajó

Tras corregir los 16 bugs obvios (RMSE 19,0 → 11,1), estos son los que quedan escondidos.

## 1. La remoción por daño apuntando mal

Si tu remoción apunta siempre a "la mayor amenaza", un hechizo de 2 daño apuntará al 5/5 y no
matará nada. **Mide la tasa de acierto**: `muertes / piezas de remoción lanzadas`. Si está por
debajo del 50%, tienes este bug. En un caso real estaba en el 22%.

El arreglo es una función `mejor_objetivo_matable(rival, dano)` que devuelve la criatura más
valiosa cuya resistencia sea menor o igual al daño. Subió la tasa al 32-99%.

## 2. El acantilado de la política de juego

Al hacer que la IA **nunca malgaste remoción** (que es la jugada correcta), la calibración
empeoró de 10 a 19 puntos. Hay un salto brusco, no una pendiente:

| Penalización por "sin objetivo" | RMSE Standard |
|---|---|
| 10 | 10,43 |
| 20 | 10,07 |
| **30** | **9,90** |
| 45 | 19,08 |
| 60 | 19,08 |

Con penalización alta, los mazos de criaturas *con* remoción juegan perfecto y se vuelven
dominantes; con penalización baja malgastan su remoción, lo que actuaba de contrapeso accidental.

**Lección:** la política de juego de la IA es parte del modelo, no una constante. Ajústala por
barrido empírico y déjalo declarado. Un jugador real tampoco juega óptimo.

## 3. El disparo equivocado

Es fácil asignarle a "cada vez que esta criatura ataca, hace daño" el mismo código de efecto que
"cada vez que lanzas un hechizo". El resultado es una criatura que pega al lanzar hechizos.
**Cada condición de disparo necesita su propio código**, aunque el efecto sea idéntico.

## 4. La recursión que nunca termina

Modelar "vuelve del cementerio a tu mano al morir" como un retorno garantizado crea bucles de
valor infinito. O lo limitas (probabilidad, contador de usos) o lo descartas: la carta ya está
en el mazo y se va a robar de nuevo.

## 5. Los mazos de una sola criatura grande

Voltron y tempo mueren siempre en un motor donde toda remoción apunta a la mayor amenaza. En la
realidad esos mazos llevan **protección** (hexproof, indestructible hasta el fin del turno) justo
para eso. Modélala como **reactiva**: nunca se lanza proactivamente, se consume cuando la
remoción rival apunta a tu criatura. Es un contrahechizo para criaturas.

## 6. Estudios de ablación

Cuando añadas varios efectos de golpe y el resultado empeore, no adivines: mete un flag
`DISABLE_EFF=<codigo>` que anule un efecto concreto en tiempo de ejecución y mide uno a uno.
Descubre dos cosas: cuál estorba, y cuáles ya son **estructurales** (al quitarlos empeora mucho).

**Cuidado:** si tienes más de un binario (p. ej. uno por formato), verifica que todos reciban la
variable de entorno. Una ablación que da exactamente el mismo número en todas las filas es la
señal de que el flag no está llegando.

## 7. El objetivo de 50% no vale para todos los formatos

Si un metajuego tiene un mazo con 23% de cuota y 77% de victorias reportadas, **un motor correcto
debe mostrar dispersión** y su RMSE-contra-50 será alto por construcción.

Para esos formatos, mide contra los **winrates reales publicados** y separa dos cosas:

- **Desplazamiento** (todos altos o todos bajos): esperable. Los winrates de ladder se miden
  contra un campo que incluye mazos malos; tu round-robin solo enfrenta a los mejores. Un
  desplazamiento constante de −10 a −15 puntos es normal.
- **Residuo** tras descontar el desplazamiento: esto sí mide tu error. Por debajo de 3 puntos,
  el motor ordena bien aunque el nivel absoluto esté corrido.

## 8. Revalida tus mazos cada vez que cambies el motor

Una lista optimizada está ajustada a la versión del motor que la produjo. Tras una campaña de
correcciones, compárala contra su semilla greedy: **si quedó por debajo, hay que rehacerla.**
Pasó exactamente eso con un mazo que terminó 1,58 puntos por debajo de la construcción simple.


---

# Tercera campaña: cuando ya no quedan bugs, quedan decisiones

Tras la segunda campaña (RMSE global 11,1) el motor ya no tenía errores obvios. Lo que queda a
partir de ahí no son bugs sino **elecciones de modelado**, y la única forma de decidirlas es
medirlas. Resultado de la campaña: global **11,06 → 10,55**.

| Formato | RMSE antes | RMSE después | Nota |
|---|---|---|---|
| Standard | 11,70 | **9,57** | |
| Pauper | 8,70 | **8,08** | |
| Brawl | 12,90 | 14,01 | métrica equivocada: ver punto 7 de la 2.ª campaña; residuo real 4,5 |
| **Global** | 11,06 | **10,55** | |

## 1. Una regla más fiel puede dar un motor menos fiel

El motor solo permitía un bloqueador por atacante. Implementé el bloqueo en grupo completo —
varios bloqueadores, orden de asignación de daño, desborde por arrollar — y además hice que el
atacante lo **anticipara** antes de decidir atacar. Es indiscutiblemente más correcto según las
reglas.

Empeoró la calibración: el residuo contra winrates reales subió de **4,0 a 8,0 puntos**, de forma
monótona conforme subía el peso de la regla.

La razón es que los errores restantes del motor **se estaban compensando entre sí**. Añadir
realismo en un solo punto rompe ese equilibrio accidental, y el error que antes se cancelaba
ahora aparece entero.

**Qué hacer:** no borres el código. Déjalo tras un flag (`GANG_ON=0`) con un comentario que diga
qué midió y cuándo. Si más adelante corriges el error que lo compensaba, querrás volver a
encenderlo — y querrás no haber perdido dos días reimplementándolo.

**Regla general:** toda mejora de fidelidad de reglas se mide contra el banco antes de adoptarse.
"Es más correcto" no es evidencia de que el motor prediga mejor.

## 2. Ajusta los umbrales de la IA por descenso coordenada a coordenada

Los números que gobiernan cuándo la IA bloquea, intercambia, levanta un muro o guarda maná
suelen estar puestos a ojo. Exponlos como constantes y bárrelos uno a uno contra el banco
(`scripts/tune.py`): fija todos menos uno, prueba una rejilla de valores, quédate con el mejor,
pasa al siguiente, repite hasta que ninguna coordenada mejore.

En un caso real: **11,07 → 10,35**, con dos cambios que cuentan una historia:

| Parámetro | Antes | Después | Qué significa |
|---|---|---|---|
| `TH_TRADE` | 10 | **4** | intercambiar es mejor de lo que suponía el autor |
| `TH_BADBLOCK` | −14 | **−22** | bloquear mal es peor de lo que suponía el autor |

**Riesgo de sobreajuste.** El banco tiene 6-7 mazos por formato: es una muestra chica. Dos
protecciones baratas:

- Limita el ajuste a un puñado de parámetros (5-8), no a todos los que tengas.
- Después de ajustar, **revalida los mazos contra su semilla greedy** (punto 8 de la 2.ª
  campaña). Si el ajuste rompió esa relación, ajustaste al banco y no al juego.

## 3. Mide la cobertura antes de modelar algo nuevo

Antes de gastar un día implementando planeswalkers, cuenta qué fracción del metajuego los usa.
En un caso real: planeswalkers **1,7%**, sagas **0,7%**, equipo **0,3%**, auras **0,6%** de las
cartas del meta. Menos del 4% entre todos.

Ese trabajo no podía mover el RMSE. Una consulta de diez minutos ahorró un día.

## 4. Un diagnóstico correcto no garantiza que el arreglo obvio sirva

La traza mostró que un mazo de control llegaba al turno 7 con la mesa vacía: guardaba maná para
instantáneos que nunca usaba. Diagnóstico correcto. El arreglo obvio — si no tenés nada en mesa,
ignorá la reserva y jugá algo — dio **11,06 → 11,42**. Peor. Revertido.

**Anota los intentos fallidos con su número.** Sin una bitácora vas a volver a intentar lo mismo
en la campaña siguiente, y va a volver a fallar.

## Bitácora de la campaña (formato sugerido)

| Cambio | Medición | Decisión |
|---|---|---|
| Bloqueo en grupo + anticipación | residuo real 4,0 → 8,0 | apagado tras flag |
| Segunda pasada de lanzamiento sin reserva | global 11,06 → 11,42 | revertido |
| Ajuste coordenada a coordenada de umbrales | 11,07 → 10,35 | adoptado |
| Modelar planeswalkers/sagas/equipo/auras | <4% del meta | no se hizo |


---

# Cuarta campaña: la vara estaba mal

Las tres campañas anteriores midieron el motor contra una **suposición**: "si el meta está
equilibrado, cada mazo debería quedar cerca del 50% contra el campo". Es una vara razonable
cuando no hay nada mejor. Pero esconde una clase entera de error.

## 1. Un promedio contra el campo cancela los errores que se compensan

Si el motor infla el mazo A y desinfla el mazo B, el promedio del campo apenas se mueve. La
única forma de ver ese error es mirar **enfrentamientos directos**.

Caso real, mismo motor, mismo día:

| Vara | Error de Standard |
|---|---|
| RMSE contra el 50% (la suposición) | **9,56** |
| RMSE contra enfrentamientos reales publicados | **20,66** |

El motor no había empeorado. La vara vieja mentía. **Antes de celebrar un RMSE bajo, pregúntate
contra qué lo estás midiendo.**

## 2. Buscar el dato real es trabajo de calibración, no un extra

Existe dato publicado y es gratis. Vale la pena media hora de búsqueda antes de otra semana de
código:

- **magic.gg / Metagame Mentor** — winrates de papel de Regional Championships y Pro Tour,
  no-espejo, miles de partidas. Es el mejor dato que hay. Suele tener 2-3 meses de retraso.
- **MTGGoldfish "Power of Pauper"** y equivalentes semanales — MTGO Challenge, muestras de
  180-640 listas. Una sola semana se mueve 17 puntos: **promedia varias semanas o no lo uses**.
- **Agregadores de enfrentamientos** (MTG Nexus y similares) — 55-95 partidas por cruce, o sea
  ±10 puntos al 95%. Sirven para detectar errores de 20-30 puntos, no para afinar 2.
- Cuidado con mezclar poblaciones: ladder Bo1 de Arena, MTGO Bo3 y papel son formatos distintos
  a efectos estadísticos. No los promedies juntos.

## 3. La sobredispersión es lo que se mide con robustez

Con 4-6 puntos de dato real y ±10 de ruido, **la correlación no se puede medir bien pero la
amplitud sí**. Compara rangos:

| | Amplitud real | Amplitud del motor | Sobredispersión |
|---|---|---|---|
| Standard, campo | 4,8 pts | 21,5 pts | **×4,5** |
| Standard, cara a cara | 6,6 pts | 45,2 pts | **×7** |
| Pauper, campo | 10,8 pts | 22,6 pts | **×2,2** |

Un motor hecho a mano **siempre** separa de más: no modela sideboard, ni juego de segunda y
tercera partida, ni la habilidad del jugador, y todas esas cosas comprimen los resultados hacia
el 50%. Da por hecho que tu motor sobredispersa y **mídelo**.

## 4. Comprime por igualación de varianza, no por mínimos cuadrados

```
calibrado = media_real + k · (bruto − media_motor),   k = sd_real / sd_motor
```

Con esa muestra, la pendiente por mínimos cuadrados es puro ruido — en un caso real salió
**negativa** (k=−0,16), lo que implicaría que el motor predice al revés. La igualación de
varianza solo asume que el motor separa de más, que es lo único que el dato sostiene con holgura.

**Pon un freno explícito.** No calibres el nivel si la muestra no es representativa. Regla que
funcionó: exige al menos 4 mazos con dato, que el rango real cubra ≥3 puntos, y que **algún**
mazo esté por debajo del 60%. En un formato donde los únicos dos winrates publicados eran los de
los dos mejores mazos (77% y 73%), ajustar una recta a eso y aplicarla a todo devolvía "90% para
cualquier cosa". Es mejor que el sistema diga *no sé*.

## 5. Declara la confianza por formato, no en global

El mismo motor puede ser bueno en un formato y no estar validado en otro:

| Formato | Correlación de orden | Veredicto |
|---|---|---|
| Pauper | **r=+0,70** (n=6) | el orden es utilizable |
| Standard | r=−0,03 (n=4) | el orden NO está validado |
| Brawl | solo 2 datos | solo desplazamiento |

La explicación es estructural y probablemente se repita en cualquier motor de este tipo: **Pauper
es un formato de comunes — cuerpos y combate — que es justo lo que un motor hecho a mano modela
bien. Standard es de raras con texto largo, modos, planeswalkers y sideboard.** El motor mide
músculo, no astucia.

Ojo con la humildad estadística: en Standard el rango real era de 4,8 puntos y el ruido de la
medición de ±10. **Ese dato no puede ni confirmar ni desmentir al motor** — "no validado" no es
lo mismo que "refutado", y decir la diferencia es parte del trabajo.

## 6. Bug encontrado en esta campaña: keywords leídas y nunca usadas

`hexproof`, `ward` e `indestructible` estaban correctamente parseadas, pero la función de
selección de objetivo de la remoción solo miraba `indestructible`. **Toda la remoción dirigida
mataba criaturas con antimaleficio.** Los mazos de una sola amenaza grande perdían por un bug.

Vale la pena una prueba explícita: por cada keyword que parsees, **comprueba que algún camino del
código la lea**. Una keyword parseada y no usada no da error, no aparece en la calibración si
ningún mazo del meta la lleva, y está mal igual.

## 7. Cuando los parámetros se saturan, deja de apretar

Barrido de diez parámetros de política de juego, dos rondas completas de descenso coordenada a
coordenada: ganancia total **1,4%**. Esa es la señal de que el error que queda es de **modelo**,
no de ajuste. Seguir tuneando a partir de ahí es sobreajustar al banco.


---

# Campaña 4b: mejorar el modelo cuando los parámetros ya no dan

Punto de partida: los parámetros saturados (dos rondas de descenso ganaban 1,4%). Resultado de
esta campaña: **−27% de error**, y el motor cruzó por primera vez la línea de aportar información.

## 1. Corrige el objetivo antes de optimizar contra él

Si tienes una capa de compresión de escala (y deberías, ver campaña 4), **no penalices la
sobredispersión en el objetivo**: la estás castigando dos veces, y así descartas cambios que en
realidad mejoran el motor.

Con igualación de varianza el error calibrado sale en cerrado:

```
error_calibrado = sd_real · sqrt( 2 · (1 − r) )
```

Minimizar eso es **exactamente** maximizar la correlación de orden. Un simulador solo puede
aspirar a ordenar bien; el nivel lo pone la escala. En un caso real, el mismo cambio medía
"empeora" con el objetivo viejo (6,60 → 7,58) y "mejora" con el correcto (3,20 → 2,95).

## 2. Valida con dejar-uno-fuera contra un modelo tonto

Ajustar la escala con los mismos mazos con los que luego te evalúas es optimista con n=4-6.
Validación cruzada: para cada mazo, ajusta con los otros y predice ese. Y compáralo siempre
contra el **modelo tonto** — predecir la media real, sin simular nada.

| | Motor antes | Motor después | Modelo tonto |
|---|---|---|---|
| Pauper | 4,86% | **3,93%** | 4,40% |
| Standard | 7,69% | 5,94% | **2,44%** |

Sin esta prueba, "mi RMSE bajó" no significa nada. **Si el motor no le gana al modelo tonto, no
aporta información, por bonito que sea el código.**

Y hay formatos **imposibles por construcción**: si los winrates reales del formato van de 49,9% a
54,7% (desviación típica 1,85 puntos), ningún modelo le gana a decir la media, porque la señal es
más chica que el ruido. Eso no es un fallo del motor: es un límite del problema. Dilo y deja de
tunear.

## 3. El error de modelado más caro: daño "a cualquier objetivo"

`deals N damage to any target` **no es quemar a la cara**. Un Rayo mata criaturas la mayor parte
del tiempo. Si lo mandas a un código de "daño a la cara", **todos los mazos rojos se quedan sin
interacción** y el arquetipo entero se hunde.

Eran 41 cartas, el 3,6% del meta, incluyendo Lightning Bolt, Fiery Temper, Lava Dart, Chain
Lightning, Galvanic Blast. Arreglarlo subió la correlación de Pauper de +0,66 a +0,76.

**Detección barata:** mide `piezas de remoción lanzadas / partida` por mazo. Un mazo de quemar que
lleva doce hechizos de daño y marca 0,98 tiene este bug.

El código correcto es **flexible**, no binario: mata la criatura si vale la pena, va a la cara si
con eso gana la partida, y va a la cara si no hay nada que matar.

## 4. Las trampas de subcadena en las expresiones regulares

`untap target creature` **contiene** `tap target creature`. Una carta que endereza criaturas se
estaba leyendo como una que las gira. Usa límites de palabra (`\btap`) sistemáticamente.

Esta clase de error **no da excepción, da números**. Nunca la vas a ver leyendo el código; solo
aparece en un ablation o en una radiografía del mazo. Ten un script que imprima cómo quedó
modelada cada carta de una lista concreta (`scripts/xray.py`) y míralo cada vez que toques el
extractor.

## 5. Cuidado con confundir un coste propio con un ataque al rival

`sacrifice a land` casi siempre es un **coste que paga quien lanza** (Crop Rotation, Highway
Robbery). Y hasta `destroy target land` se usa sobre tierra propia para buscar y robar —
Cleansing Wildfire, que da nombre a un arquetipo entero de Pauper.

Modelarlo como destrucción de tierras del rival empeoró el objetivo de 2,86 a 3,14. La regla
general: **antes de asumir a quién apunta un efecto, mira quién es el sujeto de la frase**, y si
el texto no lo dice sin ambigüedad, mídelo antes de adoptarlo.

## 6. Un cambio de modelo reabre el espacio de parámetros

Después de arreglar el daño flexible y añadir el bloque de negación, el mismo descenso coordenada
a coordenada que antes ganaba 1,4% ganó **14%** (2,892 → 2,491), y movió parámetros que llevaban
tres campañas clavados (`W_TARGET` de 0 a 50: con remoción flexible, ahora sí importa el tamaño
del objetivo).

**Vuelve a tunear después de cada cambio de modelo.** Los parámetros estaban en un óptimo local
del modelo viejo.
