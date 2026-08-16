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

- Motor: **objetivo 2,543** contra dato real, medido sobre el árbol limpio. En **Pauper el motor
  le gana a no simular nada** (3,93% de error contra 4,40% del modelo tonto) — es el único formato
  validado, r=+0,73. En Standard no está validado (r=+0,16, y 5,50% contra 2,44% del modelo tonto)
  y hay una razón de fondo: el único dato real disponible es de mayo 2026 y **hubo bans después**,
  así que estaríamos comparando listas de hoy contra winrates de otro formato.
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
  gráfico `out/avance.html`. Índices brutos vigentes: Standard 88,3%, Pauper 76,0%, Brawl 61,5%.
- El tuning (regla 4) se corrió y **no adoptó nada**. El único candidato, `SWEEP_MIN=3`, resultó
  ser ruido de semilla: parecía bajar el objetivo a 2,534 pero con 5 semillas queda peor que el
  default. El objetivo tiene un ruido de ±0,014, así que 2,543 hay que leerlo como 2,53 ± 0,01.

## Lo primero que quiero que verifiques

```bash
bash scripts/bootstrap.sh
gcc -O3 -w -o bin_sim src/sim.c -lm
python3 src/gen_brawl.py && sed -i 's/^static int CMD_A, CMD_B;$/static int CMD_A=-1, CMD_B=-1;/' src/sim_brawl.c
gcc -O3 -w -o bin_brawl src/sim_brawl.c -lm
python3 src/obj_real.py 2000     # esperado: OBJETIVO 2.543, sta r=+0.16, pau r=+0.73
python3 src/loocv.py 2500        # esperado: pauper 3,93% vs 4,40% | standard 5,50% vs 2,44%
python3 src/revalidar.py 2500    # esperado: sta +10,72 | pau +10,94 | brawl wr 61,5%
```

Los tres son control duro: están medidos sobre este árbol y salen de `out/obj_eff2.txt` y
`out/loocv_eff2.txt`. Si no dan eso, algo se rompió y hay que arreglarlo antes de seguir.

En **Windows** pon `PYTHONUTF8=1` delante de cada `python3` o vas a ver `UnicodeDecodeError` y
`KeyError: "Thrór's Map"`: hay 45 `open()` sin `encoding` declarado en 27 archivos. Y para
compilar sirve MinGW, porque `sim.c` no usa nada de POSIX.

## Lo que quiero hacer a continuación, en orden

1. **Calcular el suelo de ruido de Pauper.** Los recaps semanales de MTGGoldfish dan medidas
   repetidas del mismo arquetipo (Mono Red Madness: 47,4 / 47,3 / 49,6 / 50,8 / 49,3 / 56,4 / 52).
   Esa variación semana a semana es ruido de muestreo puro. Quiero saber **cuánto margen real
   queda** antes de seguir invirtiendo: si el suelo es 2,5% y el motor está en 3,93%, queda poco.
2. **Ampliar el banco de Pauper** con Dimir Faeries y Gruul Ponza (listas ya validadas a 60 cartas
   en `data/nuevos/listas.txt`) y sus winrates semanales. Pasar de n=6 a n=8 mejora todo:
   la estimación de k, la de r, y el objetivo de ajuste.
3. **Cuatro Colores Control** marca 33,9% contra 53% real — el peor error que queda. Trázalo con
   `python3 src/trazar.py standard "Four-Color" "Mardu"` y mira qué hace turno a turno.
4. **Costes alternativos**: Fireblast se juega sacrificando dos montañas, el motor lo ve a 6 maná
   y no lo lanza nunca.

## Reglas que no se negocian

- Toda mejora se mide con `src/obj_real.py` **antes** de adoptarse. "Es más correcto según las
  reglas" no es evidencia — el bloqueo en grupo era correcto y empeoraba el ajuste.
- Después de tocar el motor, `src/revalidar.py`: si un mazo dejó de ganarle a su semilla
  codiciosa, hay que rehacer la búsqueda.
- Un cambio de modelo reabre el espacio de parámetros: volver a correr `src/tune_real.py`.
- Nunca me des un winrate del motor como predicción. Dame el índice bruto **y** la estimación
  comprimida por `src/escala.py`.
- Mide con semillas independientes: las búsquedas mienten con la suya.
