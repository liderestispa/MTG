# Léxico de habilidades: qué sabe leer el motor y qué no

Catálogo canónico de patrones de texto → ranura del motor. **Antes de escribir una regla
nueva en `src/extract.py`, búscala aquí.** Antes lo único que había era el código y
`data/reglas_extra.json`, así que cada campaña volvía a derivar las mismas conclusiones —
y dos veces se implementó algo que ya estaba descartado por medición.

Cada entrada dice **qué la dispara**, **a qué ranura va** y **en qué estado está**:

| estado | significa |
|---|---|
| `LEÍDA` | implementada y activa |
| `APAGADA` | implementada, medida, y ajusta peor. No la vuelvas a encender sin dato nuevo |
| `PENDIENTE` | se puede modelar con las ranuras que hay, falta escribirla |
| `NO MODELABLE` | necesitaría una ranura nueva o un concepto que el motor no tiene |

Las ranuras del motor hoy: `eff`/`eff2`/`eff3` (al entrar o al resolver), `die_eff` (al ir
al cementerio), `act_eff` (activada con coste), `atk_eff` (al atacar), `cond` (condición
estática), `alt` (coste alternativo), `cred` (coste que baja), `dyn` (fuerza variable),
`kw` (palabras clave), `coste_extra` (coste adicional obligatorio).

---

## Momento del disparo

La lección más cara del proyecto, aprendida tres veces: **el momento importa tanto como el
efecto**. Un mismo texto en la ranura equivocada cambia el tempo, que es justo lo que el
motor mide. Krark-Clan Shaman midió 3,102 como barredor de entrada y 0,978 como habilidad
activada — la misma carta, la misma lectura, distinta ranura.

| patrón | ranura | estado |
|---|---|---|
| `when ~ enters` | `eff` | LEÍDA |
| `when ~ dies` · `is put into a graveyard` · `leaves the battlefield` | `die_eff` | LEÍDA |
| `whenever ~ attacks` | `atk_eff` | LEÍDA |
| `{coste}: efecto` | `act_eff` (o se descarta) | LEÍDA |
| `at the beginning of your upkeep/end step/draw step` | `eff` (UPKEEP_DRAW) | LEÍDA |
| `whenever you cast` · `whenever an opponent casts` | — | NO MODELABLE |
| `at the beginning of combat on your turn` | — | NO MODELABLE — *Lake-town Toymaker, Hog-Monkey* |
| `whenever another ~ you control enters` | — | NO MODELABLE — *Avatar Enthusiasts, Belladonna Took* |
| `whenever a nonland creature you control dies` | — | NO MODELABLE — *Beifong's Bounty Hunters, Great Fierce Bee* |

## Costes

| patrón | ranura | estado |
|---|---|---|
| `rather than pay this spell's mana cost` + sacrificar tierras / pagar vidas | `alt` | LEÍDA — *Fireblast, Snuff Out* |
| locura (`madness {coste}`) | reescribe el coste | LEÍDA |
| `costs {N} less to cast for each` | `cost_reduction`, plano | LEÍDA |
| `costs {X} less, where X is the greatest mana value among` | `cred=2` | **APAGADA** — correcta y rompe el orden de Standard (+0,238). El motor sobrevalora volador gordo + rebote |
| `as an additional cost to cast this spell,` (obligatorio) | `coste_extra` | **APAGADA** — correcta y tumba Pauper por debajo del modelo tonto |
| `as an additional cost ... you may` (opcional) | ninguna | correcto: no pagarla es legal |

## Condiciones estáticas

`E_COND_BUFF` y `E_TAX` se aplicaban **siempre** hasta el 18-ago. Ahora llevan `cond`.

| patrón | `cond` | estado |
|---|---|---|
| `storied` (3+ artefactos/legendarias/Sagas, y no se pierde) | 1 | LEÍDA |
| `ferocious` · `creature with power 4 or greater` | 2 | LEÍDA |
| `metalcraft` | 3 | LEÍDA |
| `as long as an opponent has N or less life` | — | PENDIENTE — *Bloodghast* |
| `as long as you control another <tipo>` | — | NO MODELABLE: no hay subtipos |
| `threshold` · `delirium` · `if you've drawn two or more cards` | — | NO MODELABLE |

## Remoción y control

| patrón | ranura | estado |
|---|---|---|
| `destroy target creature` | `E_DESTROY` | LEÍDA |
| `exile target creature` | `E_EXILE` | LEÍDA |
| `deals N damage to target creature` | `E_DMG_SPELL` | LEÍDA |
| `deals N damage to any target` | `E_DMG_ANY` | LEÍDA |
| `deals N damage to target attacking or blocking creature` | `E_DMG_SPELL` | LEÍDA |
| `deals N damage divided as you choose` | `E_DMG_SPELL` | LEÍDA |
| `deals N damage to each creature` | `E_SWEEPER` | LEÍDA |
| `sacrifices a creature` | `E_EDICT` | LEÍDA |
| `tap target creature` | `E_TAPDOWN` | LEÍDA |
| **Aura que traba**: `enchanted creature doesn't untap` · `loses all abilities` | `E_TAPDOWN` | PENDIENTE — *Enchanted River's Grasp ×4, Honest Work, Watery Grasp* |
| `exile ... an opponent controls with mana value N or greater` | `E_EXILE` | PENDIENTE — *Earth Kingdom Jailer* |
| `airbend all other creatures` (exilio masivo con rebaja) | `E_SWEEPER` | PENDIENTE — *Avatar's Wrath* |
| `puts it into their library second from the top` | `E_BOUNCE` | **APAGADA** — medido +0,026 |
| `can't be blocked` | — | NO MODELABLE: el motor no tiene inbloqueable dirigido |

## Ganancia y pérdida de vida

| patrón | ranura | estado |
|---|---|---|
| `you gain N life` | `E_LIFEGAIN` | LEÍDA |
| `each opponent loses N life` · `target player loses` | `E_ETB_DRAIN` | LEÍDA |
| **`its controller loses N life`** | `E_ETB_DRAIN` | LEÍDA — fue el peor error del proyecto: Four-Color Control pasó de 33,2% a 51,5% al arreglarlo |

## Cartas y cementerio

| patrón | ranura | estado |
|---|---|---|
| `draw N cards` | `E_ETB_DRAW` | LEÍDA |
| `look at the top N ... put ... into your hand` | `E_ETB_DRAW` selectivo | LEÍDA |
| `return target creature card from your graveyard` | `E_REANIMATE` | LEÍDA |
| `scry N` · `surveil N` | — | NO MODELABLE: no hay calidad de robo separada del robo |
| `flashback` · `if this spell was cast from a graveyard` | — | NO MODELABLE |
| `create a Clue/Food/Blood token` | — | NO MODELABLE sin fichas-artefacto reales |

## Cuerpos y pump

| patrón | ranura | estado |
|---|---|---|
| `+N/+N until end of turn` | `E_PUMP` | LEÍDA |
| `creatures you control get +N/+N` (estático) | `E_LORD` | LEÍDA |
| `creatures target player controls get +N/+0` | `E_TEAM_PUMP` | PENDIENTE — *How to Start a Riot* |
| `target creature you control gets +N/+N` (instantáneo) | `E_PUMP` | PENDIENTE — *Yip Yip!, Smaug's Fury, Vow to Erebor* |
| `power and toughness are each equal to` | `dyn` | LEÍDA |
| `gets +N/+0 for each Mountain you control` | — | NO MODELABLE: no hay conteo por subtipo de tierra |
| `base power and toughness become equal to` | — | NO MODELABLE — *Galion* |

## Lo que el motor no tiene, y por qué las cartas que lo usan quedan mudas

No es pereza: cada una necesitaría un concepto nuevo, y el proyecto tiene doce casos
medidos de "más correcto y ajusta peor". Añadir conceptos sin dato que los valide es
exactamente lo que ha fallado.

- **Subtipos de criatura.** No existen. Todo lo que diga *Aliado*, *Enano*, *Elfo*, *Oso*
  o *Halfling* es invisible. Afecta a ~15 cartas de la colección.
- **Fichas-artefacto con habilidad** (Pista, Comida, Sangre, Tesoro con texto). Solo hay
  Tesoro como maná.
- **Cementerio de verdad.** Hay `gy_is`, un contador de instantáneos y conjuros. No hay
  zona con cartas, así que flashback, aventura, escapar y recursión selectiva no se pueden.
- **Caras de Aventura y MDFC.** Se lee solo la cara frontal. Son 14 copias de la colección,
  entre ellas Smaug, the Great Calamity y Beorn, Reluctant Host.
- **Contadores que no sean +1/+1** (aturdir, veneno, lore de Saga parcialmente).
- **Elección de modo en tiempo real.** Un modal se lee por su primer modo.
- **Habilidades otorgadas** (`gains flying until end of turn`, `gains "cuando esto haga
  daño..."`).

---

## Cómo se decide si una regla nueva entra

1. **Cuenta la materia** (`src/chk_hallazgos.py`): si el banco no tiene cartas que la
   activen, mide cero y ese cero no significa nada.
2. **Comprueba que funciona** (`src/sintetico.py`): mazos artificiales que aíslan el
   comportamiento.
3. **Comprueba que conviene** (`src/calib_real.py` para el residuo y `src/loocv.py` para
   ver si le gana al modelo tonto). **No** `obj_real.py`: mide correlación de orden y en
   Pauper el orden real cabe en 1,04 puntos, así que premia errores grandes que conserven
   el ranking.
4. **Mira la sensibilidad ANTES** (`src/sensibilidad.py`): si subir ese arquetipo no mueve
   el objetivo, no hay nada que ganar por ahí.
