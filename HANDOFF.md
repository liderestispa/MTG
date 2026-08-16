# Transcript de continuación — proyecto MTG

Pega esto como primer mensaje en Claude Code (o deja que lea `CLAUDE.md`, que tiene lo mismo
en formato de contexto permanente).

---

Estoy retomando un proyecto de optimización de mazos de Magic por simulación. Está en este repo
y ya tiene cuatro campañas de calibración encima. **Lee `CLAUDE.md` antes de tocar nada** — trae
las reglas de trabajo y las trampas que ya costaron caro.

## Contexto de una línea

Motor de simulación en C + buscador de mazos en Python, calibrado contra winrates realmente
publicados. Yo juego en papel, en tienda local, y lo que corre mi tienda es **Standard Brawl**.
Juego control de prisión: negarle el juego al rival.

## Dónde quedó

- Motor: **objetivo 0,978** contra dato real, medido sobre el árbol limpio. Le gana al modelo
  tonto en los **dos** formatos con dato: Pauper 0,95% contra 4,40% (r=+0,99) y Standard 0,11%
  contra 2,44% (r=+1,00). Global 0,67% contra 3,56%: baja el error un 81%. En Standard no está validado (r=+0,16, y 5,50% contra 2,44% del modelo tonto)
  y hay una razón de fondo: el único dato real disponible es de mayo 2026 y **hubo bans después**,
  así que estaríamos comparando listas de hoy contra winrates de otro formato.
- **Pero Standard NO está validado**, por mucho que el número lo parezca: son n=4 puntos y el
  dato es de mayo 2026, pre-13-bans. Una recta que pasa por cuatro puntos no demuestra nada.
  Lo que sí pasó es que se arregló un error grande y real: Four-Color Control estaba en −19,8
  porque la regla de pérdida de vida no cubría "its controller loses".
- Hay un bug de datos sin corregir: Mono Red Madness lleva 4 Sneaky Snacker, un Hada {U}{B}, en
  una lista con 19 Montañas. Son cuatro cartas inlanzables. Hace falta una fuente verificada de
  la lista real para arreglarlo; `src/chk_castable.py` lo detecta.
- El suelo de ruido estimado del banco de Pauper es 3,25% (`src/suelo_ruido.py`) y el motor está
  en 1,73%, o sea **por debajo**. Eso no significa que se haya superado un límite: significa que
  esa estimación es una cota superior, con pocos grados de libertad y muy sensible a una serie
  volátil. Úsala como orden de magnitud. Standard y Brawl no tienen suelo calculable: hace falta
  medir el mismo arquetipo varias veces y ninguno de los dos tiene series.
- Mis tres mazos actuales: Brawl mono-blanco con Dáin Lord of the Iron Hills, Standard BG,
  Pauper BR. Los tres legales y armables con mis 371 cartas, los tres revalidados y ganándole
  a su semilla codiciosa.
- Las tres últimas correcciones son de motor: el índice de Scryfall resolvía 88 nombres a su
  versión **ficha** en vez de a la carta real; el robo recurrente solo se leía en el mantenimiento
  (se perdía el del paso final, como The Arkenstone); y `upkeep()` en `sim.c` solo miraba la
  ranura `eff`, así que las cartas que traen el motor de robo en `eff2` quedaban etiquetadas pero
  nunca disparaban. Esa última mitad se había medido pero **no se había commiteado**, y por eso
  la documentación decía 2,540 mientras el repo daba 2,557.
- Ya está todo regenerado con el motor nuevo: `data/escala.json`, `out/report_v6.json` y el
  gráfico `out/avance.html`. Índices brutos vigentes: Standard 88,3%, Pauper 74,3%, Brawl 61,5%.
- El tuning (regla 4) se corrió y **no adoptó nada**. El único candidato, `SWEEP_MIN=3`, resultó
  ser ruido de semilla: parecía bajar el objetivo a 2,534 pero con 5 semillas queda peor que el
  default. El objetivo tiene un ruido de ±0,014, así que 2,543 hay que leerlo como 2,53 ± 0,01.

## Lo primero que quiero que verifiques

```bash
bash scripts/bootstrap.sh
gcc -O3 -w -o bin_sim src/sim.c -lm
python3 src/gen_brawl.py && sed -i 's/^static int CMD_A, CMD_B;$/static int CMD_A=-1, CMD_B=-1;/' src/sim_brawl.c
gcc -O3 -w -o bin_brawl src/sim_brawl.c -lm
python3 src/obj_real.py 2000     # esperado: OBJETIVO 0.978, sta r=+1.00, pau r=+0.99
python3 src/loocv.py 2500        # esperado: pauper 0,95% vs 4,40% | standard 0,11% vs 2,44%
python3 src/revalidar.py 2500    # esperado: sta +13,13 | pau +11,08 | brawl wr 60,6%
```

Los tres son control duro: están medidos sobre este árbol y salen de `out/obj_activadas.txt`. Si no dan eso, algo se rompió y hay que arreglarlo antes de seguir.

En **Windows** pon `PYTHONUTF8=1` delante de cada `python3` o vas a ver `UnicodeDecodeError` y
`KeyError: "Thrór's Map"`: hay 45 `open()` sin `encoding` declarado en 27 archivos. Y para
compilar sirve MinGW, porque `sim.c` no usa nada de POSIX.

## Herramientas que hay que conocer antes de tocar nada

    python src/sensibilidad.py      cuanto cambia el objetivo si sube cada arquetipo. El
                                    objetivo mide ORDEN, asi que el residuo crudo NO dice
                                    si conviene subir un mazo. Recalcularlo tras cada
                                    cambio de motor.
    python src/laboratorio.py       mide hipotesis con semillas emparejadas, correccion
                                    por comparaciones multiples y semillas de
                                    confirmacion. Nada se adopta sin pasar por aqui.
    python src/cobertura_texto.py   cola de cartas cuyo texto el motor no lee.
    python src/chk_castable.py      que ninguna carta del banco sea inlanzable.
    python src/tablero.py           reproduce partidas en 2D: para ver POR QUE pierde.
    python src/orquestador.py       encadena todo y escribe out/informe_dia.md.
    python src/vigilar.py --seguir  mira como va sin esperar a que acabe.

## Lo que quiero hacer a continuación, en orden

1. **Más dato de Pauper**, que ahora vale más que cualquier cambio de modelo: el motor está en
   el suelo. Primero, más semanas para Grixis Affinity y Elves, que tienen una sola medición y
   aportan el 69% del ruido. Después, ampliar el banco con Dimir Faeries y Gruul Ponza (listas
   ya validadas a 60 cartas en `data/nuevos/listas.txt`): pasar de n=6 a n=8 mejora la estimación
   de k, la de r y el objetivo. Las series van en `REAL_SEMANAL` de `data/real_wr.py`.
2. **Cuatro Colores Control** marca 33,9% contra 53% real — el peor error que queda, y está muy
   por encima de cualquier suelo de ruido. Míralo con `python3 src/tablero.py standard
   "Four-Color" "Mardu" 8 12`, que ahora reproduce las partidas y canta cada jugada.
3. **Sin sideboard.** Los winrates reales son al mejor de tres y el motor juega una sola partida.
   Explica buena parte de la sobredispersión que queda.

## Reglas que no se negocian

- Toda mejora se mide con `src/obj_real.py` **antes** de adoptarse. "Es más correcto según las
  reglas" no es evidencia — el bloqueo en grupo era correcto y empeoraba el ajuste.
- Después de tocar el motor, `src/revalidar.py`: si un mazo dejó de ganarle a su semilla
  codiciosa, hay que rehacer la búsqueda.
- Un cambio de modelo reabre el espacio de parámetros: volver a correr `src/tune_real.py`.
- Nunca me des un winrate del motor como predicción. Dame el índice bruto **y** la estimación
  comprimida por `src/escala.py`.
- Mide con semillas independientes: las búsquedas mienten con la suya.
