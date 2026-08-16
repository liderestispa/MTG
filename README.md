# MTG — optimizador de mazos por simulación

Motor de simulación de Magic: The Gathering escrito en C, más un buscador de mazos en Python,
calibrado contra winrates **realmente publicados** en vez de contra supuestos.

Construye el mejor mazo posible con una colección concreta y dice **cuánto hay que creerle al número**.

## Qué hay aquí

```
src/sim.c            motor de simulación (~1.100 líneas, ~70.000 partidas/s)
src/extract.py       texto de oráculo de Scryfall -> códigos de efecto
src/search.py        beam search con racing sobre listas completas
src/calib_real.py    calibración contra winrates reales publicados
src/escala.py        traduce el índice bruto del motor a una estimación honesta
src/loocv.py         validación cruzada contra un modelo tonto
data/real_wr.py      winrates publicados, con fuente y calidad de cada uno
data/meta_decks.py   decklists del metajuego, verificadas a 60 cartas
```

## Arranque

```bash
bash scripts/bootstrap.sh      # descarga el bulk de Scryfall (~200 MB)
gcc -O3 -w -o bin_sim src/sim.c -lm
python3 src/gen_brawl.py && sed -i 's/^static int CMD_A, CMD_B;$/static int CMD_A=-1, CMD_B=-1;/' src/sim_brawl.c
gcc -O3 -w -o bin_brawl src/sim_brawl.c -lm
python3 src/calib_real.py 1500      # ¿el motor reproduce los winrates reales?
python3 src/loocv.py 2500           # ¿le gana a no simular nada?
python3 src/run_all.py              # busca los mejores mazos de la colección
```

## Lo que se aprendió (cuatro campañas de calibración)

| Campaña | Qué se corrigió | Error global |
|---|---|---|
| 1 | 16 bugs de motor (barredores, contrahechizos, combate, comandante) | 19,0 → 11,1 |
| 2 | Remoción mal apuntada, política de juego, ablaciones | 11,1 → 10,6 |
| 3 | Bloqueo en grupo (descartado), umbrales por descenso coordenada | 10,6 → 10,55 |
| 4 | **Calibración contra dato real**, capa de escala, daño flexible, negación | −27% |

Detalle completo en `docs/`.

### Las tres cosas que más importan

1. **Medir contra el 50% supuesto esconde los errores que se compensan.** El mismo motor daba
   9,56 de error contra esa vara y 20,66 contra enfrentamientos reales publicados.
2. **Todo motor hecho a mano sobredispersa** — separa más de lo que separa la realidad (×2,2 a ×7),
   porque no modela sideboard, segunda y tercera partida ni la habilidad del jugador.
   `src/escala.py` mide el factor y lo corrige; y **se niega a calibrar** cuando la muestra real
   no es representativa.
3. **Valida contra un modelo tonto.** Si tu motor no le gana a "predecir siempre la media",
   no aporta información. `src/loocv.py`.

## Confianza por formato

| Formato | Correlación de orden | Veredicto |
|---|---|---|
| Pauper | r=+0,72 (n=6) | el orden es utilizable |
| Standard | r=+0,12 (n=4) | no validado |
| Standard Brawl | 2 datos reales | solo desplazamiento |

## Licencia

Uso personal. Los datos de cartas vienen de [Scryfall](https://scryfall.com) bajo sus términos.
Magic: The Gathering es marca de Wizards of the Coast; este proyecto no está afiliado.
