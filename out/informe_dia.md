# Informe del 2026-08-17 00:55 — 0 ciclos en 0 min

Objetivo de control: **1.069**

## Cola de trabajo

71 cartas en blanco (151 copias). Las que mas pesan:

- 6x Nihil Spellbomb
- 6x Restless Reef
- 5x Deep-Cavern Bat
- 4x Superior Spider-Man
- 4x Blood Fountain
- 4x Masked Vandal
- 4x Eddymurk Crab
- 4x Sunderflock

*Lo unico que necesita tokens: leer estas cartas y escribir la regla en `data/reglas_extra.json` con `activo:false`.*

## Laboratorio

43 hipotesis en total: MEJORA 9, empeora 15, irrelevante 6, ruido 13

- **MEJORA** `POLNET=out/politica_probando.txt POLNET_LADO=1` -0.054  ← **medida contra OTRO banco** (`sin marcar`), no comparable
- **MEJORA** `REGLA_SOLO=retro_lava_dart` -0.133  ← **medida contra OTRO banco** (`sin marcar`), no comparable
- **MEJORA** `REGLA_SOLO=vida_por_permanente_sacrificado` -0.054  ← **medida contra OTRO banco** (`sin marcar`), no comparable

---
*`src/orquestador.py`. Estado en vivo: `out/estado.json`.*