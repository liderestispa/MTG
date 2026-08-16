# Informe del 2026-08-16 06:06 — 39 ciclos en 356 min

Objetivo de control: **1.547**

## Cola de trabajo

70 cartas en blanco (145 copias). Las que mas pesan:

- 6x Restless Reef
- 5x Deep-Cavern Bat
- 4x Superior Spider-Man
- 4x Blood Fountain
- 4x Masked Vandal
- 4x Eddymurk Crab
- 4x Sunderflock
- 4x Great Hall of the Biblioplex

*Lo unico que necesita tokens: leer estas cartas y escribir la regla en `data/reglas_extra.json` con `activo:false`.*

## Laboratorio

23 hipotesis en total: MEJORA 7, empeora 7, irrelevante 3, ruido 6

- **MEJORA** `POLNET=out/politica_probando.txt POLNET_LADO=1` -0.066
- **MEJORA** `POLNET=out/politica_probando.txt POLNET_LADO=1` -0.066
- **MEJORA** `REGLA_SOLO=retro_lava_dart` -0.133
- **MEJORA** `REGLA_SOLO=vida_por_permanente_sacrificado` -0.054
- **MEJORA** `POLNET=out/politica_probando.txt POLNET_LADO=1` -0.045
- **MEJORA** `POLNET=out/politica_probando.txt POLNET_LADO=1` -0.048
- **MEJORA** `POLNET=out/politica_probando.txt POLNET_LADO=1` -0.042

## Politica de juego

- generacion **1810**, 40 reinicios, sigma 0.0425
- autojuego: **+2.286** puntos sobre la heuristica

---
*`src/orquestador.py`. Estado en vivo: `out/estado.json`.*