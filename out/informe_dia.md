# Informe del 2026-08-16 04:23

## Control

- objetivo medido **1.547**, esperado 1.547 (desvio 0.000)

## Cola de trabajo

70 cartas en blanco para el motor (145 copias). Las diez que mas pesan:

- **6x Restless Reef** — Whenever this land attacks, target player mills four cards.
- **5x Deep-Cavern Bat** — When this creature enters, look at target opponent's hand. | You may exile a nonland card from it until this c
- **4x Superior Spider-Man** — Mind Swap — You may have Superior Spider-Man enter as a copy of any creature card in a graveyard, except his n
- **4x Blood Fountain** — When this artifact enters, create a Blood token. | {3}{B}, {T}, Sacrifice this artifact: Return up to two targ
- **4x Masked Vandal** — When this creature enters, you may exile a creature card from your graveyard. | If you do, exile target artifa
- **4x Eddymurk Crab** — When this creature enters, tap up to two target creatures.
- **4x Sunderflock** — When this creature enters, if you cast it, return all non-Elemental creatures to their owners' hands.
- **4x Great Hall of the Biblioplex** — {5}: If this land isn't a creature, it becomes a 2/4 Wizard creature with "Whenever you cast an instant or sor
- **4x Undercity Sewers** — When this land enters, surveil 1.
- **4x Spyglass Siren** — When this creature enters, create a Map token.

*Esto es lo unico que necesita tokens: leer estas cartas y escribir la regla en `data/reglas_extra.json`.*

## Laboratorio

| hipotesis | delta | veredicto |
|---|---|---|
| `REGLA_SOLO=tapdown_multiple` | +0.000 | **ruido** |
| `REGLA_SOLO=rebote_masivo_no_tipo` | +0.000 | **ruido** |
| `REGLA_SOLO=exilia_artefacto_rival` | +0.000 | **ruido** |
| `REGLA_SOLO=vida_igual_a_su_fuerza` | +0.000 | **ruido** |
| `REGLA_SOLO=mirar_y_exiliar_de_la_mano` | +0.000 | **ruido** |
| `REGLA_SOLO=contadores_por_descarte` | +0.000 | **ruido** |

0 candidatas superaron el contraste. **No estan adoptadas**: revisa el desglose por arquetipo antes de encender nada, porque el objetivo mide orden.

---
*Generado por `src/orquestador.py` en 5 minutos.*