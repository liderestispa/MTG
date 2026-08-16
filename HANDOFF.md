# Transcript de continuación — proyecto MTG

Pegá esto como primer mensaje en Claude Code (o dejá que lea `CLAUDE.md`, que tiene lo mismo
en formato de contexto permanente).

---

Estoy retomando un proyecto de optimización de mazos de Magic por simulación. Está en este repo
y ya tiene cuatro campañas de calibración encima. **Leé `CLAUDE.md` antes de tocar nada** — trae
las reglas de trabajo y las trampas que ya costaron caro.

## Contexto de una línea

Motor de simulación en C + buscador de mazos en Python, calibrado contra winrates realmente
publicados. Yo juego en papel, en tienda local, y lo que corre mi tienda es **Standard Brawl**.
Juego control de prisión: negarle el juego al rival.

## Dónde quedó

- Motor: objetivo 2,56 contra dato real. En **Pauper el motor le gana a no simular nada**
  (3,93% de error contra 4,40% del modelo tonto) — es el único formato validado, r=+0,72.
  En Standard no está validado (r=+0,12) y hay una razón de fondo: el único dato real disponible
  es de mayo 2026 y **hubo bans después**, así que estaríamos comparando listas de hoy contra
  winrates de otro formato.
- Mis tres mazos actuales: Brawl mono-blanco con Dáin Lord of the Iron Hills, Standard BG,
  Pauper BR. Los tres legales y armables con mis 371 cartas.
- Última corrección: el índice de Scryfall resolvía 88 nombres a su versión **ficha** en vez de
  a la carta real.

## Lo primero que quiero que verifiques

```bash
bash scripts/bootstrap.sh
gcc -O3 -w -o bin_sim src/sim.c -lm
python3 src/gen_brawl.py && sed -i 's/^static int CMD_A, CMD_B;$/static int CMD_A=-1, CMD_B=-1;/' src/sim_brawl.c
gcc -O3 -w -o bin_brawl src/sim_brawl.c -lm
python3 src/obj_real.py 2000     # esperado: ~2,56
python3 src/loocv.py 2500        # esperado: Pauper 3,93% vs 4,40% del modelo tonto
```

Si esos números no salen, algo se rompió en el camino y hay que arreglarlo antes de seguir.

## Lo que quiero hacer a continuación, en orden

1. **Calcular el suelo de ruido de Pauper.** Los recaps semanales de MTGGoldfish dan medidas
   repetidas del mismo arquetipo (Mono Red Madness: 47,4 / 47,3 / 49,6 / 50,8 / 49,3 / 56,4 / 52).
   Esa variación semana a semana es ruido de muestreo puro. Quiero saber **cuánto margen real
   queda** antes de seguir invirtiendo: si el suelo es 2,5% y el motor está en 3,93%, queda poco.
2. **Ampliar el banco de Pauper** con Dimir Faeries y Gruul Ponza (listas ya validadas a 60 cartas
   en `data/nuevos/listas.txt`) y sus winrates semanales. Pasar de n=6 a n=8 mejora todo:
   la estimación de k, la de r, y el objetivo de ajuste.
3. **Cuatro Colores Control** marca 33,9% contra 53% real — el peor error que queda. Trazalo con
   `python3 src/trazar.py standard "Four-Color" "Mardu"` y mirá qué hace turno a turno.
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
- Medí con semillas independientes: las búsquedas mienten con la suya.
