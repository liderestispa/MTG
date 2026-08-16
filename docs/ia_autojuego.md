# IA de autojuego: que aprende, que no, y por que

Objetivo: que el motor mejore solo, con la CPU de la maquina, sin gastar tokens. Los
tokens se reservan para lo unico que no se automatiza — leer los informes, decidir que
mecanica falta y escribir la regla — y para mejorar esta misma IA.

## La distincion que decide todo el diseno

Hay dos cosas muy distintas que se pueden "aprender", y confundirlas arruinaria el
proyecto:

**1. Predecir winrates reales. NO se puede aprender.** Existen diez winrates publicados
en total. Cualquier red entrenada contra diez numeros los memoriza y no generaliza. Este
es el muro de datos: ninguna cantidad de computo local crea dato real nuevo. Toda la
sesion del 16-ago-2026 choco contra el, y `src/suelo_ruido.py` lo mide.

**2. Aprender a JUGAR. Si se puede, y ahi esta el margen.** El motor decide con umbrales
escritos a mano: cuando bloquear, cuando cambiar criaturas, cuanto mana reservar, que
hechizo lanzar primero. Esos umbrales se ajustaron por descenso coordenada contra los
diez winrates, y **se demostro dos veces que eso es ajustar ruido** (`SWEEP_MIN=3`).
Pero una politica de juego no necesita dato externo: se entrena por **autojuego**, que
genera partidas infinitas en local.

Y hay una razon de fondo para creer que ahi queda margen: buena parte del error del motor
no es que el modelo de las cartas este mal, es que **el piloto juega mal**. Un piloto
mejor deberia beneficiar mas a los mazos cuyo valor depende de jugar bien —control,
tempo— que a los mazos lineales, y justo esos son los que siguen desviados.

## El riesgo, y como se controla

El autojuego optimiza **ganarle a si mismo**, que no es lo mismo que **jugar como un
humano**. El motor se calibra contra winrates de humanos, asi que una politica
superhumana pero rara podria empeorar el ajuste aunque gane mas partidas.

Por eso la regla no se negocia: **una politica aprendida no se adopta por ganar mas
partidas.** Se adopta si y solo si baja el objetivo contra dato real, medido con
`src/obj_real.py` y validado con `src/valida_semillas.py` contra semillas independientes.
El autojuego propone; el dato real dispone. Si la politica gana un 60% contra la
heuristica y empeora el objetivo, se descarta.

## Lo que midio la primera campana, y que cambia el diseno

Seis horas de maquina, 1810 generaciones, cero intervencion. Dos resultados y el segundo
importa mas que el primero.

**Uno: el autojuego SI transfiere, y bastante.** La politica llego a +2,29 puntos de
winrate sobre la heuristica y, medida contra dato real, dio negativo NUEVE veces
seguidas, de -0,035 a -0,070, con las semillas de confirmacion acompanando. Eso no es
casualidad: aprender a jugar mejor mejoraba el ajuste.

**Dos: y aun asi no se adopto, porque cambio de signo.** En la misma sesion el
laboratorio encontro dos reglas de extractor que si valian —el retroceso de Lava Dart y
la ganancia de vida de Reckoner's Bargain, juntas -0,216—, y una vez adoptadas se
remidio la politica contra el motor corregido: **+0,025, empeora**.

La lectura es la que incomoda: **la politica no estaba jugando mejor, estaba compensando
errores del modelo.** Lava Dart valia el doble de lo que el motor creia y la mitad de
vida de Reckoner's Bargain no se contaba; la red aprendio a jugar alrededor de esos
huecos y eso mejoraba el ajuste. Tapados los huecos como corresponde, su compensacion
sobra y estorba.

Consecuencias practicas, que no son opinables:

- **Una politica aprendida caduca cada vez que se toca el modelo.** No es como una regla
  de extractor, que se mide una vez y queda. Hay que remedirla despues de CADA cambio de
  motor, y la respuesta puede invertirse.
- **El orden correcto es: primero las reglas, despues la politica.** Entrenar sobre un
  motor con huecos ensena a explotar los huecos. Cada regla adoptada invalida el
  entrenamiento anterior.
- **Ganar mas partidas de autojuego dejo de correlacionar con ajustar mejor.** Mientras
  el autojuego subia de +1,76 a +2,29, el beneficio contra dato real se encogia de -0,070
  a -0,042 y acabo en +0,025. La divergencia que este documento avisaba como riesgo esta
  ahora medida.

Por eso la regla de no adoptar por winrate de autojuego no era prudencia excesiva: era
exactamente el filtro que hacia falta. Sin ella se habria desplegado una politica que
hoy empeora el motor.

## Arquitectura

No hay numpy ni torch en la maquina y no hacen falta. La red vive **en C, dentro de
sim.c**, y se entrena por evolucion: solo hace falta la pasada hacia delante y el
resultado de la partida, nunca gradientes.

```
  sim.c            MLP diminuta que puntua decisiones. Pesos desde archivo (POLNET=ruta).
                   Sin archivo, se usa la heuristica de siempre: por defecto no cambia nada.
  entrenar_politica.py   Metodo de entropia cruzada (CEM) sobre los pesos. Reparte la
                   poblacion entre los 20 nucleos, cada candidato juega N partidas contra
                   la heuristica actual, se queda con la elite y reajusta la distribucion.
  valida_semillas.py     El filtro final contra dato real. Sin esto no se adopta nada.
```

Por que evolucion y no descenso de gradiente: la senal es el resultado de la partida, que
no es derivable respecto de los pesos sin montar toda la maquinaria de RL. CEM necesita
unicamente evaluar candidatos, y evaluar es justo lo que esta maquina hace rapido: 70.000
partidas por segundo y por nucleo.

### Que decide la red

Se empieza por la decision de mayor palanca: **que hechizo lanzar**. Hoy `cast_phase`
calcula un valor `v` a mano para cada carta jugable y elige el mayor. La red no lo
reemplaza, lo **corrige**: `v_final = v_heuristico + escala * red(rasgos)`. Arrancando
con pesos en cero el comportamiento es identico al de hoy, asi que el punto de partida
del entrenamiento es exactamente el motor actual y solo se puede mejorar desde ahi.

Rasgos de entrada (todos ya disponibles en el momento de decidir, sin coste extra):
coste convertido, tipo, fuerza, resistencia, codigo de efecto y sus parametros, si es
criatura, si tiene prisa, vida propia y del rival, criaturas propias y del rival, poder
total en mesa de cada lado, turno, cartas en mano, mana sin gastar.

Despues, por orden de palanca: bloqueo y cambios en combate, y cuanto mana reservar.

### Bucle diario

```
  1. cobertura_texto.py  -> cola de cartas que el motor no entiende  (sin tokens)
  2. laboratorio.py      -> mide y valida reglas candidatas          (sin tokens)
  3. entrenar_politica.py-> entrena la politica por autojuego        (sin tokens)
  4. informe del dia     -> que se probo, que sobrevivio, que sigue roto
  5. tokens              -> leer el informe, escribir las reglas que faltan,
                            mejorar esta IA
```

Los pasos 1-3 son los que consumen la maquina. El 5 es el unico que consume tokens.

## Disciplina estadistica, que aqui es lo que mas importa

Un proceso que prueba cientos de hipotesis al dia contra diez winrates **va a encontrar
mejoras falsas**, con total seguridad. Es el mismo error que `SWEEP_MIN=3` pero
multiplicado. Guardas obligatorias:

- **Semillas independientes siempre.** Nunca adoptar por una sola corrida.
- **Correccion por comparaciones multiples.** El umbral se endurece con el numero de
  hipotesis probadas: el registro lleva la cuenta y `laboratorio.py` la aplica.
- **Reserva.** Un subconjunto de arquetipos no participa del ajuste y solo se usa para
  confirmar.
- **Registro completo.** Toda hipotesis probada queda escrita con su medicion, tambien
  las que fallan. Sin eso no se puede corregir por comparaciones multiples, y ademas
  evita volver a perseguir un fantasma ya descartado.

## Lo que esto NO va a conseguir

Conviene decirlo para no perseguirlo:

- No va a validar Standard. El dato es de mayo 2026, pre-bans. Ningun computo lo arregla.
- No va a bajar el suelo de ruido del banco. Eso solo se baja con mas semanas de dato.
- No va a inventar mecanicas que no esten en el texto de las cartas. Leer texto nuevo y
  proponer la regla sigue siendo trabajo de criterio.
