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

## Estado actual del motor

Todo lo de abajo está **medido sobre este árbol** y es reproducible. `out/obj_eff2.txt`,
`out/loocv_eff2.txt`.

```
$ python3 src/obj_real.py 2000
sta cal 2.37 (r=+0.16 x5.3) | pau cal 2.69 (r=+0.73 x2.9) | bra resid  2.31
OBJETIVO 2.543
```

| Formato | Correlación de orden | ¿Le gana al modelo tonto? | Veredicto |
|---|---|---|---|
| Pauper | r=+0,73 (n=6) | **sí** — 3,93% vs 4,40% | el orden es utilizable |
| Standard | r=+0,16 (n=4) | no — 5,50% vs 2,44% | no validado |
| Standard Brawl | 2 datos reales | sin datos suficientes | solo desplazamiento |

`loocv.py 2500` global: 4,78% el motor contra 3,56% el modelo tonto.

Los tres mazos revalidados con `revalidar.py 2500`, los tres siguen ganándole a su semilla
codiciosa (no hay que rehacer búsquedas):

| Formato | Mazo | Semilla | Delta | Índice bruto |
|---|---|---|---|---|
| Standard WBG | 83,94 | 73,22 | +10,72 | 88,3% |
| Pauper BR | 70,03 | 59,09 | +10,94 | 73,7% |
| Brawl Dáin | 59,63 | — | — | 61,5% |

> **Pendiente de la regla 4:** el fix de `eff2` es un cambio de modelo, así que reabre el espacio
> de parámetros. Falta correr `src/tune_real.py`.

## Trampas ya encontradas (no las repitas)

La lista larga, con síntoma y arreglo de cada una, está en `docs/trampas.md`. Ese archivo manda;
esto es el resumen.

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

1. **Re-tunear, regla 4.** El fix de `eff2` es un cambio de modelo y reabre el espacio de
   parámetros: falta `src/tune_real.py`. Los mazos ya están revalidados y los tres le ganan a su
   semilla; lo que **no** se regeneró es `out/report_v6.json`, así que los índices brutos que
   aparecen ahí y en la página de Notion siguen siendo los de antes del fix.
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
gcc -O3 -w -o bin_sim src/sim.c -lm
python3 src/gen_brawl.py && sed -i 's/^static int CMD_A, CMD_B;$/static int CMD_A=-1, CMD_B=-1;/' src/sim_brawl.c
gcc -O3 -w -o bin_brawl src/sim_brawl.c -lm

python3 src/obj_real.py 2000        # objetivo contra dato real (menor = mejor)
python3 src/loocv.py 2500           # ¿le gana a no simular nada?
python3 src/calib_real.py 2000      # informe detallado por formato
python3 src/xray.py "Mono Red"      # cómo quedó modelada cada carta de un mazo
python3 src/trazar.py standard "Four-Color" "Mardu"   # traza una partida turno a turno
python3 src/revalidar.py 2500       # mazos vs su semilla codiciosa
python3 src/tune_real.py            # descenso coordenada a coordenada
python3 src/run_all.py              # búsqueda de mazos (Standard + Pauper)
python3 src/run_brawl.py            # búsqueda de Brawl
```

Variables de ablación (para medir un cambio con y sin él):
`DISABLE_EFF=<codigo>`, `NEG_ON=0`, `DMG_ANY_FACE=1`, `HEXWARD_ON=0`, `GANG_ON=1`, `TRACE=1`.
