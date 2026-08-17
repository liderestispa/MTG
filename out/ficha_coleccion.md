# Ficha de la coleccion: carta contra motor

## 7x Ravening Warg — MAL_LEIDA **[en mazo: standard, pauper, brawl]**

`{1}{B}` Creature — Wolf 2/2

> Deathtouch | Ferocious — Whenever this creature attacks while you control a creature with power 4 or greater, you gain 2 life.

- motor: **LIFEGAIN/COND_BUFF**   cond=2
- frases con efecto: 1, ranuras usadas: 2
- COND_SIEMPRE: COND_BUFF lo aplica siempre, pero el texto lo condiciona a "whenever this creature attacks"

## 5x Warg Tactics — MAL_LEIDA **[en mazo: standard]**

`{1}{G}` Instant 

> Choose one — | • Destroy target creature with flying. | • Put a +1/+1 counter on target creature you control. It gains trample and hexproof until end of turn. (It can't be the target of spells or abilities your opponents control.)

- motor: **DESTROY** 
- frases con efecto: 3, ranuras usadas: 1
- KW_PERDIDA: 'Hexproof' esta en el texto y no en kw

## 2x Gollum the Abandoned — MAL_LEIDA **[en mazo: standard, brawl]**

`{1}{B}` Legendary Creature — Halfling Horror 2/2

> Gollum can't block. | When Gollum enters, exile up to one target card from an opponent's graveyard. Each opponent loses 2 life. | {2}, Sacrifice an artifact or creature: Return this card from your graveyard to your hand. Activate only as a sorcery.

- motor: **ETB_DRAIN** 
- frases con efecto: 3, ranuras usadas: 1
- ACTIVADA_GRATIS: hay coste de activacion en el texto y el efecto esta en ranura libre: el motor lo ejecuta solo y sin pagar

## 1x Along the Crooked Way — MAL_LEIDA **[en mazo: brawl]**

`{2}{B}` Enchantment 

> When this enchantment enters, return target creature card from your graveyard to your hand. | Whenever a creature card leaves your graveyard, amass Goblins 1. | {1}{B}: Goblins and Orcs you control gain menace until end of turn.

- motor: **REANIMATE/AMASS** 
- frases con efecto: 3, ranuras usadas: 2
- ACTIVADA_GRATIS: hay coste de activacion en el texto y el efecto esta en ranura libre: el motor lo ejecuta solo y sin pagar

## 1x Foggy Swamp Hunters — MAL_LEIDA **[en mazo: brawl]**

`{3}{B}` Creature — Human Ranger Ally 3/4

> As long as you've drawn two or more cards this turn, this creature has lifelink and menace. (It can't be blocked except by two or more creatures.)

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0
- KW_PERDIDA: 'Menace' esta en el texto y no en kw

## 1x Smaug's Fury — MAL_LEIDA **[en mazo: pauper]**

`{1}{R}` Instant 

> Target creature gets +3/+0 and gains reach and first strike until end of turn.

- motor: **PUMP** 
- frases con efecto: 1, ranuras usadas: 1
- KW_PERDIDA: 'First strike' esta en el texto y no en kw

## 1x Thrór's Map — MAL_LEIDA **[en mazo: standard]**

`{2}` Legendary Artifact 

> When Thrór's Map enters, search your library for a basic land card, reveal it, put it into your hand, then shuffle. | {2}, {T}: Draw a card, then discard a card.

- motor: **RAMP/RAMP** 
- frases con efecto: 2, ranuras usadas: 2
- ACTIVADA_GRATIS: hay coste de activacion en el texto y el efecto esta en ranura libre: el motor lo ejecuta solo y sin pagar

## 5x Bofur, Reliable Guardian // Concerted Care — MAL_LEIDA

`{W} // {1}{W}` Legendary Creature — Dwarf Scout // Instant — Adventure 1/1

> Lifelink | Target artifact or creature you control gains hexproof and indestructible until end of turn. (Then exile this card. You may cast the creature later from exile.)

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0
- KW_PERDIDA: 'Indestructible' esta en el texto y no en kw

## 3x Bombur, Gentle Dreamer — MAL_LEIDA

`{2}{R}` Legendary Creature — Dwarf Bard 5/3

> Storied (If you control three or more artifacts, legendaries, and/or Sagas, you have an enduring story for the rest of the game.) | Bombur doesn't untap during your untap step unless you have an enduring story.

- motor: **COND_BUFF**   cond=1
- frases con efecto: 1, ranuras usadas: 1
- COND_SIEMPRE: COND_BUFF lo aplica siempre, pero el texto lo condiciona a "storied"

## 3x Ori, Keeper of Songs — MAL_LEIDA

`{2}{W}` Legendary Creature — Dwarf Bard 3/3

> Storied (If you control three or more artifacts, legendaries, and/or Sagas, you have an enduring story for the rest of the game.) | As long as you have an enduring story, Ori gets +1/+0 and has vigilance.

- motor: **COND_BUFF**   cond=1
- frases con efecto: 1, ranuras usadas: 1
- COND_SIEMPRE: COND_BUFF lo aplica siempre, pero el texto lo condiciona a "storied"

## 3x Wargling — MAL_LEIDA

`{1}{G}` Creature — Wolf 2/2

> Ferocious — Whenever this creature attacks while you control a creature with power 4 or greater, until end of turn, this creature gets +1/+0 and creatures you control gain trample.

- motor: **COND_BUFF**   cond=2
- frases con efecto: 1, ranuras usadas: 1
- COND_SIEMPRE: COND_BUFF lo aplica siempre, pero el texto lo condiciona a "whenever this creature attacks"

## 3x Óin the Brave — MAL_LEIDA

`{1}{R}` Legendary Creature — Dwarf Warrior 1/3

> Storied (If you control three or more artifacts, legendaries, and/or Sagas, you have an enduring story for the rest of the game.) | As long as you have an enduring story, Óin gets +1/+0 and has haste. | {1}, {T}, Discard a card: Draw a card.

- motor: **COND_BUFF**   cond=1
- frases con efecto: 2, ranuras usadas: 1
- COND_SIEMPRE: COND_BUFF lo aplica siempre, pero el texto lo condiciona a "storied"
- ACTIVADA_GRATIS: hay coste de activacion en el texto y el efecto esta en ranura libre: el motor lo ejecuta solo y sin pagar

## 2x Dáin, Lord of the Iron Hills — MAL_LEIDA

`{1}{W}` Legendary Creature — Dwarf Noble 2/2

> Vigilance | Storied (If you control three or more artifacts, legendaries, and/or Sagas, you have an enduring story for the rest of the game.) | As long as you have an enduring story, creatures can't attack you unless their controller pays {1} for each of those creatures.

- motor: **TAX/COND_BUFF**   cond=1  tax_atk
- frases con efecto: 1, ranuras usadas: 2
- COND_SIEMPRE: TAX, COND_BUFF lo aplica siempre, pero el texto lo condiciona a "storied"
- TAX_ATAQUE: el texto grava ATACAR y E_TAX grava LANZAR hechizos

## 2x Eagle's Rescue — MAL_LEIDA

`{2}{W/U}{W/U}` Enchantment — Aura 

> Enchant creature | Enchanted creature gets +2/+2 and has flying. | {2}{W/U}{W/U}: Return this card from your graveyard to the battlefield attached to target creature you control with power 1 or less. Activate only as a sorcery.

- motor: **EQUIP** 
- frases con efecto: 2, ranuras usadas: 1
- ACTIVADA_GRATIS: hay coste de activacion en el texto y el efecto esta en ranura libre: el motor lo ejecuta solo y sin pagar

## 2x Elven Raft-Steerer — MAL_LEIDA

`{2}{U}` Creature — Elf Pilot 3/2

> Landfall — Whenever a land you control enters, choose one — | • Tap target creature an opponent controls. | • Untap target creature you control.

- motor: **TAPDOWN/COND_BUFF** 
- frases con efecto: 3, ranuras usadas: 2
- MODAL_TODO: texto modal y 2 ranuras llenas (TAPDOWN, COND_BUFF): se disparan todas juntas

## 2x Thorin Oakenshield — MAL_LEIDA

`{R}{W}` Legendary Creature — Dwarf Noble 3/2

> Trample | Storied (If you control three or more artifacts, legendaries, and/or Sagas, you have an enduring story for the rest of the game.) | As long as you have an enduring story, artifacts and creatures you control have ward {1}.

- motor: **COND_BUFF**   cond=1
- frases con efecto: 1, ranuras usadas: 1
- COND_SIEMPRE: COND_BUFF lo aplica siempre, pero el texto lo condiciona a "storied"

## 2x Thranduil's Company — MAL_LEIDA

`{2}{G}{U}` Creature — Elf Soldier 3/4

> As long as you control another Elf, you may play an additional land on each of your turns. | Landfall — Whenever a land you control enters, put two +1/+1 counters on target creature you control. It gains vigilance until end of turn.

- motor: **COND_BUFF/ETB_COUNTERS** 
- frases con efecto: 2, ranuras usadas: 2
- COND_SIEMPRE: COND_BUFF lo aplica siempre, pero el texto lo condiciona a "as long as"

## 1x Bard's Company — MAL_LEIDA

`{2}{W}{U}` Creature — Human Citizen 2/3

> You may cast this spell as though it had flash if you control a Human. | Other creatures you control get +1/+1. | Whenever this creature enters or attacks, recruit. (Draw a card, then discard a card. If you discarded a nonland card, create a 1/1 white Human Soldier creature token.)

- motor: **LORD/LOOT_TOKEN** 
- frases con efecto: 3, ranuras usadas: 2
- COND_SIEMPRE: LORD lo aplica siempre, pero el texto lo condiciona a "if you control"
- KW_PERDIDA: 'Flash' esta en el texto y no en kw

## 1x Belladonna Took — MAL_LEIDA

`{1}{W}` Legendary Creature — Halfling Citizen 2/2

> Whenever a token you control enters, you gain 1 life if this is the first time this ability has resolved this turn. If it's the second time, draw a card. If it's the third time, put a +1/+1 counter on each creature you control.

- motor: **ETB_DRAW/LIFEGAIN/ETB_COUNTERS** 
- frases con efecto: 1, ranuras usadas: 3
- MODAL_TODO: texto modal y 3 ranuras llenas (ETB_DRAW, LIFEGAIN, ETB_COUNTERS): se disparan todas juntas

## 1x Beorn's Hospitality — MAL_LEIDA

`{1}{G}` Enchantment 

> Landfall — Whenever a land you control enters, put a +1/+1 counter on target creature you control. | {5}{G}{G}: This enchantment becomes a Bear creature in addition to its other types and gains "This creature's power and toughness are each equal to the number of lands you control." (This effect doesn't end.)

- motor: **COND_BUFF/ETB_COUNTERS** 
- frases con efecto: 2, ranuras usadas: 2
- ACTIVADA_GRATIS: hay coste de activacion en el texto y el efecto esta en ranura libre: el motor lo ejecuta solo y sin pagar

## 1x Bifur, Melodic Rider — MAL_LEIDA

`{4}{R/W}{R/W}` Legendary Creature — Dwarf Bard 4/5

> Storied (If you control three or more artifacts, legendaries, and/or Sagas, you have an enduring story for the rest of the game.) | Whenever Bifur enters or attacks, put a +1/+1 counter on target creature. | As long as you have an enduring story, if a triggered ability of a Dwarf you control triggers, that ability triggers an additional time.

- motor: **COND_BUFF/ETB_COUNTERS**   cond=1
- frases con efecto: 2, ranuras usadas: 2
- COND_SIEMPRE: COND_BUFF lo aplica siempre, pero el texto lo condiciona a "storied"

## 1x Momo, Playful Pet — MAL_LEIDA

`{W}` Legendary Creature — Lemur Bat Ally 1/1

> Flying, vigilance | When Momo leaves the battlefield, choose one — | • Create a Food token. (It's an artifact with "{2}, {T}, Sacrifice this token: You gain 3 life.") | • Put a +1/+1 counter on target creature you control. | • Scry 2.

- motor: **LIFEGAIN** 
- frases con efecto: 4, ranuras usadas: 1
- SALIR_COMO_ENTRAR: el disparo es al morir/irse y LIFEGAIN esta en ranura de entrada

## 1x Wilderland Scrounger — MAL_LEIDA

`{4}{G}` Creature — Wolf 3/6

> Ferocious — Whenever this creature attacks while you control a creature with power 4 or greater, put a +1/+1 counter on each creature you control.

- motor: **COND_BUFF/ETB_COUNTERS**   cond=2
- frases con efecto: 1, ranuras usadas: 2
- COND_SIEMPRE: COND_BUFF lo aplica siempre, pero el texto lo condiciona a "whenever this creature attacks"

## 4x Great Fierce Bee — MUDA **[en mazo: brawl]**

`{2}{B}` Creature — Insect 2/2

> Flying | Whenever one or more other creatures die, scry 1. (Look at the top card of your library. You may put that card on the bottom.)

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 3x Gigantic Big Bear — MUDA **[en mazo: standard]**

`{5}{G}{G}` Creature — Bear 10/7

> This spell can't be countered. | Hexproof, haste

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 2x Front Porch Sentries — MUDA **[en mazo: brawl]**

`{1}{B}` Creature — Goblin Soldier 2/2

> When this creature dies, target creature an opponent controls gets -1/-1 until end of turn.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 2x Giant's Boulder — MUDA **[en mazo: standard, pauper, brawl]**

`{1}` Artifact 

> When this artifact enters, scry 2. (Look at the top two cards of your library, then put any number of them on the bottom and the rest on top in any order.) | {1}, {T}: Add one mana of any color. | {7}, {T}, Sacrifice this artifact: Destroy target permanent.

- motor: **NADA** 
- frases con efecto: 3, ranuras usadas: 0

## 2x Gollum, Silent Slinker // Meager Meal — MUDA **[en mazo: brawl]**

`{3}{B} // {B}` Legendary Creature — Halfling Horror // Sorcery — Adventure 4/3

> Menace (This creature can't be blocked except by two or more creatures.) | Put a +1/+1 counter on up to one target creature. Target player gains 2 life. (Then exile this card. You may cast the creature later from exile.)

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 2x Mirkwood Pathmaker — MUDA **[en mazo: standard]**

`{2}{G}` Creature — Elf Ranger */*

> Mirkwood Pathmaker's power and toughness are each equal to the number of lands you control.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 2x Smaug, the Great Calamity // Spew Flame — MUDA **[en mazo: pauper]**

`{5}{R}{R} // {4}{R}` Legendary Creature — Dragon // Sorcery — Adventure 5/5

> Flying | Spew Flame deals 5 damage to target creature. (Then exile this card. You may cast the creature later from exile.)

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Bender's Waterskin — MUDA **[en mazo: brawl]**

`{3}` Artifact 

> Untap this artifact during each other player's untap step. | {T}: Add one mana of any color.

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 1x Boiling Rock Rioter — MUDA **[en mazo: brawl]**

`{2}{B}` Creature — Human Rogue Ally 3/3

> Firebending 1 (Whenever this creature attacks, add {R}. This mana lasts until end of combat.) | Tap an untapped Ally you control: Exile target card from a graveyard. | Whenever this creature attacks, you may cast an Ally spell from among cards you own exiled with this creature.

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 1x Desolation Prowler — MUDA **[en mazo: brawl]**

`{1}{B}` Creature — Wolf 2/2

> Pay 2 life: This creature gets +2/+2 until end of turn. Activate only once each turn.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Dreaded Bat-Cloud — MUDA **[en mazo: standard, brawl]**

`{4}{B}` Creature — Bat 4/2

> This spell costs {3} less to cast if a creature died this turn. | Flying, deathtouch

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Gollum, Riddle Master — MUDA **[en mazo: standard, brawl]**

`{1}{B}` Legendary Creature — Halfling Horror 3/1

> As Gollum enters, choose odd or even. (Zero is even.) | Whenever an opponent casts a spell with mana value of the chosen quality, choose one that hasn't been chosen — | • Put a +1/+1 counter on Gollum. | • Each opponent loses 2 life and you gain 2 life. | • Draw a card.

- motor: **NADA** 
- frases con efecto: 5, ranuras usadas: 0

## 1x Iron Hills Stalwart — MUDA **[en mazo: pauper]**

`{4}{R}` Creature — Dwarf Warrior 4/5

> Reach, trample | When this creature enters, attach target Equipment you control to up to one target creature you control.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Joo Dee, One of Many — MUDA **[en mazo: brawl]**

`{1}{B}` Creature — Human Advisor 2/2

> {B}, {T}: Surveil 1. Create a token that's a copy of this creature, then sacrifice an artifact or creature. Activate only as a sorcery. (To surveil 1, look at the top card of your library. You may put it into your graveyard.)

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Key to the Side-Door — MUDA **[en mazo: brawl]**

`{1}` Artifact 

> {2}, {T}: Target creature can't be blocked this turn. | {1}, {T}, Discard a legendary card with the same name as a legendary permanent you control: Draw two cards.

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 1x Merchant of Many Hats — MUDA **[en mazo: brawl]**

`{1}{B}` Creature — Human Peasant Ally 2/2

> {2}{B}: Return this card from your graveyard to your hand.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Troop of Ponies — MUDA **[en mazo: brawl]**

`{2}` Creature — Horse 2/1

> {2}, {T}, Sacrifice this creature: Search your library for up to two basic land cards, reveal them, put one onto the battlefield tapped and the other into your hand, then shuffle.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 6x Lake-town — MUDA

`` Land 

> This land enters tapped. | {T}: Add {W} or {U}. | {2}{W}{U}, {T}, Sacrifice this land: Put two +1/+1 counters on target Human you control. Activate only as a sorcery.

- motor: **NADA** 
- frases con efecto: 3, ranuras usadas: 0

## 5x Hobbit Hole — MUDA

`` Land 

> {T}, Sacrifice this land: Search your library for a basic land card, put it onto the battlefield tapped, then shuffle. | Halflingcycling {4} ({4}, Discard this card: Search your library for a Halfling card, reveal it, put it into your hand, then shuffle.)

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 4x Beorn, Reluctant Host // Till and Tend — MUDA

`{4}{G} // {1}{G}` Legendary Creature — Human Bear Shapeshifter // Sorcery — Adventure 5/5

> Trample | You may play an additional land this turn. (Then exile this card. You may cast the creature later from exile.)

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 4x Enchanted River's Grasp — MUDA

`{2}{U}` Enchantment — Aura 

> Enchant creature | When this Aura enters, tap enchanted creature and remove all counters from it. | Enchanted creature loses all abilities and doesn't untap during its controller's untap step.

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 4x Little Bear — MUDA

`{2}{G}` Creature — Bear 3/2

> Flash | When this creature enters, untap another target creature you control. If that creature is a Bear, put a +1/+1 counter on it.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 4x Mirkwood Nurturer — MUDA

`{2}{G/U}` Creature — Elf Ranger 3/2

> When this creature enters, return up to one other target permanent you control to its owner's hand. If you do, put a +1/+1 counter on this creature.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 4x Razor Rings — MUDA

`{1}{W}` Instant 

> Razor Rings deals 4 damage to target attacking or blocking creature. You gain life equal to the excess damage dealt this way.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 3x Elvenking's Harper — MUDA

`{1}{U}` Creature — Elf Bard 2/2

> {4}{U}: Target creature can't be blocked this turn.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 3x Gandalf, Wandering Wizard — MUDA

`{4}{U}` Legendary Creature — Avatar Wizard 4/5

> Ward {3} (Whenever this creature becomes the target of a spell or ability an opponent controls, counter it unless that player pays {3}.) | {6}: Gandalf's owner shuffles him into their library and draws three cards.

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 3x Goblin-town — MUDA

`` Land 

> This land enters tapped. | {T}: Add {B} or {R}. | {2}{B}{R}, {T}, Sacrifice this land: Put two +1/+1 counters on target Goblin or Orc you control. Activate only as a sorcery.

- motor: **NADA** 
- frases con efecto: 3, ranuras usadas: 0

## 3x Lakeshore Apothecary — MUDA

`{1}{U}` Creature — Human Cleric 1/2

> Vigilance | Whenever you draw your second card each turn, put a +1/+1 counter on this creature.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 3x Master's Councillors — MUDA

`{1}{U}` Creature — Human Advisor 1/3

> Vigilance | This creature gets +2/+0 for each graveyard with seven or more cards in it. | Whenever you draw your second card each turn, target player mills three cards. (They put the top three cards of their library into their graveyard.)

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 3x Vow to Erebor — MUDA

`{1}{W}` Instant 

> Untap target creature you control. It gets +2/+2 until end of turn. If it's a Dwarf, you may attach an Equipment you control to it.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 2x Dwarven Provisioner — MUDA

`{1}{W}` Creature — Dwarf Citizen 2/2

> {3}{W}: Creatures you control get +1/+1 until end of turn.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 2x Eagle of the Great Shelf — MUDA

`{4}{W}` Creature — Bird Soldier 2/5

> Flying | Whenever this creature attacks, it gets +1/+1 until end of turn for each other creature you control.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 2x Galion, Elvenking's Butler — MUDA

`{2}{G}{G}` Legendary Creature — Elf Advisor 4/4

> Whenever Galion attacks, choose up to one other target creature you control. Its base power and toughness become equal to Galion's power and toughness until end of turn.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 2x Gandalf, Spark Starter — MUDA

`{4}{R}{R}` Legendary Creature — Avatar Wizard 4/3

> Reach | When Gandalf enters, he deals 3 damage divided as you choose among one, two, or three targets.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 2x Glóin the Mighty // Easy Pickings — MUDA

`{3}{R} // {2}{R}` Legendary Creature — Dwarf Warrior // Sorcery — Adventure 4/3

> At the beginning of your first main phase, add {R}{R}. | Easy Pickings deals 1 damage to each creature your opponents control. (Then exile this card. You may cast the creature later from exile.)

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 2x Mirkwood — MUDA

`` Land 

> This land enters tapped. | {T}: Add {B} or {G}. | {2}{B}{G}, {T}, Sacrifice this land: Put two +1/+1 counters on target Bear, Spider, or Wolf you control. Activate only as a sorcery.

- motor: **NADA** 
- frases con efecto: 3, ranuras usadas: 0

## 2x Velvetwing Butterflies // Gaze in Wonder — MUDA

`{2}{W} // {1}{W}` Creature — Insect // Instant — Adventure 2/2

> Flying | Tap one or two target creatures. (Then exile this card. You may cast the creature later from exile.)

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 2x Vengeful Villagers — MUDA

`{3}{W}` Creature — Human Citizen 3/3

> Whenever this creature attacks, choose target creature an opponent controls. Tap it, then you may sacrifice an artifact or creature. If you do, put a stun counter on the chosen creature. (If a permanent with a stun counter would become untapped, remove one from it instead.)

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Aang, the Last Airbender — MUDA

`{3}{W}` Legendary Creature — Human Avatar Ally 3/2

> Flying | When Aang enters, airbend up to one other target nonland permanent. (Exile it. While it's exiled, its owner may cast it for {2} rather than its mana cost.) | Whenever you cast a Lesson spell, Aang gains lifelink until end of turn.

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 1x Avatar Enthusiasts — MUDA

`{2}{W}` Creature — Human Peasant Ally 2/2

> Whenever another Ally you control enters, put a +1/+1 counter on this creature.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Avatar's Wrath — MUDA

`{2}{W}{W}` Sorcery 

> Choose up to one target creature, then airbend all other creatures. (Exile them. While each one is exiled, its owner may cast it for {2} rather than its mana cost.) | Until your next turn, your opponents can't cast spells from anywhere other than their hands. | Exile Avatar's Wrath.

- motor: **NADA** 
- frases con efecto: 3, ranuras usadas: 0

## 1x Beifong's Bounty Hunters — MUDA

`{2}{B}{G}` Creature — Human Mercenary 4/4

> Whenever a nonland creature you control dies, earthbend X, where X is that creature's power. (Target land you control becomes a 0/0 creature with haste that's still a land. Put X +1/+1 counters on it. When it dies or is exiled, return it to the battlefield tapped.)

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Bilbo, Thief in the Night — MUDA

`{1}{U}` Legendary Creature — Halfling Rogue 2/2

> Spells you cast from anywhere other than your hand cost {1} less to cast. | Whenever Bilbo attacks, you may cast an artifact, instant, or sorcery spell from your graveyard. If an instant or sorcery spell cast this way would be put into your graveyard, exile it instead.

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 1x Boiling Rock Prison — MUDA

`` Land 

> This land enters tapped. | {T}: Add {B} or {R}. | {4}, {T}, Sacrifice this land: Draw a card.

- motor: **NADA** 
- frases con efecto: 3, ranuras usadas: 0

## 1x Bolg of the North — MUDA

`{3}{B}{R}` Legendary Creature — Goblin Soldier 5/5

> When Bolg enters, you may sacrifice another creature. When you do, Bolg deals damage equal to that creature's power to another target creature. If excess damage was dealt this way, amass Goblins X, where X is that excess damage. (Put X +1/+1 counters on an Army you control. It's also a Goblin. If you don't control an Army, create a 0/0 black Goblin Army creature token first.)

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Desert Were-Worm — MUDA

`{4}{R}{R}` Creature — Dragon Wurm 0/5

> This creature gets +2/+0 for each Mountain you control. | Whenever you attack with creatures with total power 12 or greater for the first time each turn, untap all attacking creatures. After this phase, there is an additional combat phase.

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 1x Dragon-Cursed Halls — MUDA

`` Land 

> {T}: Add {C}. | {1}, {T}: Until end of turn, target creature gains "Whenever this creature deals combat damage to a player, create a Treasure token."

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 1x Dwalin, Weaponmaster — MUDA

`{1}{R/W}` Legendary Creature — Dwarf Warrior 2/1

> First strike | Whenever Dwalin enters or attacks, put a hone counter on each Equipment you control. (Each hone counter on an Equipment grants +1/+0 to equipped creature.)

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Dwarven Mauler — MUDA

`{R}` Creature — Dwarf Warrior 2/1

> Equip abilities you activate that target this creature cost {2} less to activate.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Earth Kingdom Jailer — MUDA

`{2}{W}` Creature — Human Soldier Ally 3/3

> When this creature enters, exile up to one target artifact, creature, or enchantment an opponent controls with mana value 3 or greater until this creature leaves the battlefield.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Earth Rumble Wrestlers — MUDA

`{3}{R/G}` Creature — Human Warrior Performer 3/4

> Reach | This creature gets +1/+0 and has trample as long as you control a land creature or a land entered the battlefield under your control this turn.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Earth Village Ruffians — MUDA

`{2}{B/G}` Creature — Human Soldier Rogue 3/1

> When this creature dies, earthbend 2. (Target land you control becomes a 0/0 creature with haste that's still a land. Put two +1/+1 counters on it. When it dies or is exiled, return it to the battlefield tapped.)

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Elvenking's Halls — MUDA

`` Land 

> This land enters tapped. | {T}: Add {G} or {U}. | {2}{G}{U}, {T}, Sacrifice this land: Put two +1/+1 counters on target Elf you control. Activate only as a sorcery.

- motor: **NADA** 
- frases con efecto: 3, ranuras usadas: 0

## 1x Ember Island Production — MUDA

`{3}{U}{U}` Sorcery 

> Choose one — | • Create a token that's a copy of target creature you control, except it's not legendary and it's a 4/4 Hero in addition to its other types. | • Create a token that's a copy of target creature an opponent controls, except it's not legendary and it's a 2/2 Coward in addition to its other types.

- motor: **NADA** 
- frases con efecto: 3, ranuras usadas: 0

## 1x Fire Nation Raider — MUDA

`{3}{R}` Creature — Human Soldier 4/2

> Raid — When this creature enters, if you attacked this turn, create a Clue token. (It's an artifact with "{2}, Sacrifice this token: Draw a card.")

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Fire Sages — MUDA

`{1}{R}` Creature — Human Cleric 2/2

> Firebending 1 (Whenever this creature attacks, add {R}. This mana lasts until end of combat.) | {1}{R}{R}: Put a +1/+1 counter on this creature.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Firebending Student — MUDA

`{1}{R}` Creature — Human Monk 1/2

> Prowess (Whenever you cast a noncreature spell, this creature gets +1/+1 until end of turn.) | Firebending X, where X is this creature's power. (Whenever this creature attacks, add X {R}. This mana lasts until end of combat.)

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x First-Time Flyer — MUDA

`{1}{U}` Creature — Human Pilot Ally 1/2

> Flying | This creature gets +1/+1 as long as there's a Lesson card in your graveyard.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Flexible Waterbender — MUDA

`{3}{U}` Creature — Human Warrior Ally 2/5

> Vigilance | Waterbend {3}: This creature has base power and toughness 5/2 until end of turn. (While paying a waterbend cost, you can tap your artifacts and creatures to help. Each one pays for {1}.)

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Foggy Bottom Swamp — MUDA

`` Land 

> This land enters tapped. | {T}: Add {B} or {G}. | {4}, {T}, Sacrifice this land: Draw a card.

- motor: **NADA** 
- frases con efecto: 3, ranuras usadas: 0

## 1x Glider Kids — MUDA

`{2}{W}` Creature — Human Pilot Ally 2/3

> Flying | When this creature enters, scry 1. (Look at the top card of your library. You may put it on the bottom.)

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Guardian of the Halls — MUDA

`{1}{G}` Creature — Elf Soldier 2/2

> Trample | {5}{G}{G}: Put three +1/+1 counters on this creature.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Honest Work — MUDA

`{U}` Enchantment — Aura 

> Enchant creature an opponent controls | When this Aura enters, tap enchanted creature and remove all counters from it. | Enchanted creature loses all abilities and is a Citizen with base power and toughness 1/1 and "{T}: Add {C}" named Humble Merchant. (It loses all other creature types and names.)

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 1x How to Start a Riot — MUDA

`{2}{R}` Instant — Lesson 

> Target creature gains menace until end of turn. (It can't be blocked except by two or more creatures.) | Creatures target player controls get +2/+0 until end of turn.

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 1x Jasmine Dragon Tea Shop — MUDA

`` Land 

> {T}: Add {C}. | {T}: Add one mana of any color. Spend this mana only to cast an Ally spell or activate an ability of an Ally source. | {5}, {T}: Create a 1/1 white Ally creature token.

- motor: **NADA** 
- frases con efecto: 3, ranuras usadas: 0

## 1x Jeong Jeong, the Deserter — MUDA

`{2}{R}` Legendary Creature — Human Rebel Ally 2/3

> Firebending 1 (Whenever this creature attacks, add {R}. This mana lasts until end of combat.) | Exhaust — {3}: Put a +1/+1 counter on Jeong Jeong. When you next cast a Lesson spell this turn, copy it and you may choose new targets for the copy. (Activate each exhaust ability only once.)

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Kyoshi Village — MUDA

`` Land 

> This land enters tapped. | {T}: Add {G} or {W}. | {4}, {T}, Sacrifice this land: Draw a card.

- motor: **NADA** 
- frases con efecto: 3, ranuras usadas: 0

## 1x Lake-town Mariners // Gone Fishing — MUDA

`{4}{U}{U} // {3}{U}` Creature — Human Citizen // Instant — Adventure 6/5

> Vigilance | Ward {2} (Whenever this creature becomes the target of a spell or ability an opponent controls, counter it unless that player pays {2}.) | Exile two target creatures and/or lands you control, then return them to the battlefield under their owner's control.

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 1x Lake-town Toymaker — MUDA

`{3}{W}` Creature — Human Artificer 3/4

> At the beginning of combat on your turn, if you've drawn two or more cards this turn, another target creature you control gets +3/+0 and gains first strike until end of turn.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Lost Days — MUDA

`{4}{U}` Instant — Lesson 

> The owner of target creature or enchantment puts it into their library second from the top or on the bottom. You create a Clue token. (It's an artifact with "{2}, Sacrifice this token: Draw a card.")

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Misty Palms Oasis — MUDA

`` Land 

> This land enters tapped. | {T}: Add {W} or {B}. | {4}, {T}, Sacrifice this land: Draw a card.

- motor: **NADA** 
- frases con efecto: 3, ranuras usadas: 0

## 1x Most Decrepit Old Bird // Speak Secrets — MUDA

`{U} // {1}{U}` Creature — Bird // Sorcery — Adventure 1/1

> Flying | Threshold — This creature gets +1/+1 as long as there are seven or more cards in your graveyard. | Mill four cards, then put an instant or sorcery card from among them into your hand.

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 1x Nori, Teller of Tales — MUDA

`{1}{R/W}` Legendary Creature — Dwarf Bard 2/2

> Whenever Nori attacks, target attacking creature gains first strike until end of turn.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x North Pole Gates — MUDA

`` Land 

> This land enters tapped. | {T}: Add {W} or {U}. | {4}, {T}, Sacrifice this land: Draw a card.

- motor: **NADA** 
- frases con efecto: 3, ranuras usadas: 0

## 1x Origin of Metalbending — MUDA

`{1}{G}` Instant — Lesson 

> Choose one — | • Destroy target artifact or enchantment. | • Put a +1/+1 counter on target creature you control. It gains indestructible until end of turn. (Damage and effects that say "destroy" don't destroy it.)

- motor: **NADA** 
- frases con efecto: 3, ranuras usadas: 0

## 1x Phoenix Fleet Airship — MUDA

`{2}{B}{B}` Artifact — Vehicle 4/4

> Flying | At the beginning of your end step, if you sacrificed a permanent this turn, create a token that's a copy of this Vehicle. | As long as you control eight or more permanents named Phoenix Fleet Airship, this Vehicle is an artifact creature. | Crew 1

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 1x Platypus-Bear — MUDA

`{1}{G/U}` Creature — Platypus Bear 2/3

> Defender | When this creature enters, mill two cards. (Put the top two cards of your library into your graveyard.) | As long as there is a Lesson card in your graveyard, this creature can attack as though it didn't have defender.

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 1x Rebellious Captives — MUDA

`{1}{G}` Creature — Human Peasant Ally 2/2

> Exhaust — {6}: Put two +1/+1 counters on this creature, then earthbend 2. (Target land you control becomes a 0/0 creature with haste that's still a land. Put two +1/+1 counters on it. When it dies or is exiled, return it to the battlefield tapped. Activate each exhaust ability only once.)

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Secret Tunnel — MUDA

`` Land — Cave 

> This land can't be blocked. | {T}: Add {C}. | {4}, {T}: Two target creatures you control that share a creature type can't be blocked this turn.

- motor: **NADA** 
- frases con efecto: 3, ranuras usadas: 0

## 1x Snowslope Hunter — MUDA

`{2}{R}` Creature — Goblin Ranger 2/3

> Sacrifice another creature or artifact: Exile the top card of your library. You may play it until the end of your next turn. Activate only during your turn and only once each turn.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Solstice Revelations — MUDA

`{2}{R}` Instant — Lesson 

> Exile cards from the top of your library until you exile a nonland card. You may cast that card without paying its mana cost if the spell's mana value is less than the number of Mountains you control. If you don't cast that card this way, put it into your hand. | Flashback {6}{R} (You may cast this card from your graveyard for its flashback cost. Then exile it.)

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 1x Team Avatar — MUDA

`{2}{W}` Enchantment 

> Whenever a creature you control attacks alone, it gets +X/+X until end of turn, where X is the number of creatures you control. | {2}{W}, Discard this card: It deals damage equal to the number of creatures you control to target creature.

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 1x The Lonely Mountain — MUDA

`` Land — Mountain 

> ({T}: Add {R}.) | This land enters tapped unless you control an Equipment. | {4}{R}, {T}: Create a 2/2 red Dwarf creature token. This ability costs {1} less to activate for each Equipment you control. Activate only as a sorcery.

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 1x The Lord of Pain — MUDA

`{3}{B}{R}` Legendary Creature — Human Assassin 5/5

> Menace | Your opponents can't gain life. | Whenever a player casts their first spell each turn, choose another target player. The Lord of Pain deals damage equal to that spell's mana value to the chosen player.

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 1x Thorin, Mountain-king — MUDA

`{3}{R}` Legendary Creature — Dwarf Noble 3/4

> Trample | When Thorin enters, attach any number of target Equipment you control to target creature you control. When one or more Equipment become attached to that creature this way, that creature deals damage equal to its power to up to one target creature.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Tom, Bert, and William — MUDA

`{3}{B}{G}` Legendary Creature — Troll 5/5

> {1}, Sacrifice another creature: Draw cards equal to the sacrificed creature's power, then discard a card. | When Tom, Bert, and William die, if they were a creature, return them to the battlefield. They're an artifact. (They're no longer a creature.)

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 1x Turtle-Duck — MUDA

`{G}` Creature — Turtle Bird 0/4

> {3}: Until end of turn, this creature has base power 4 and gains trample.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Vindictive Warden — MUDA

`{2}{B/R}` Creature — Human Soldier 2/3

> Menace (This creature can't be blocked except by two or more creatures.) | Firebending 1 (Whenever this creature attacks, add {R}. This mana lasts until end of combat.) | {3}: This creature deals 1 damage to each opponent.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 1x Watery Grasp — MUDA

`{U}` Enchantment — Aura 

> Enchant creature | Enchanted creature doesn't untap during its controller's untap step. | Waterbend {5}: Enchanted creature's owner shuffles it into their library. (While paying a waterbend cost, you can tap your artifacts and creatures to help. Each one pays for {1}.)

- motor: **NADA** 
- frases con efecto: 2, ranuras usadas: 0

## 1x Yip Yip! — MUDA

`{W}` Instant — Lesson 

> Target creature you control gets +2/+2 until end of turn. If that creature is an Ally, it also gains flying until end of turn.

- motor: **NADA** 
- frases con efecto: 1, ranuras usadas: 0

## 5x Crude Bent Blade — A_MEDIAS **[en mazo: pauper, brawl]**

`{2}{B}` Artifact — Equipment 

> When this Equipment enters, target opponent sacrifices a creature of their choice. | Equipped creature gets +2/+1. | Equip {2} ({2}: Attach to target creature you control. Equip only as a sorcery.)

- motor: **EDICT/EQUIP** 
- frases con efecto: 3, ranuras usadas: 2

## 3x Duskwatch Hunter — A_MEDIAS **[en mazo: pauper]**

`{2}{B/G}` Creature — Wolf 3/1

> This creature can't be blocked by tokens. | When this creature enters, put a +1/+1 counter on target creature.

- motor: **ETB_COUNTERS** 
- frases con efecto: 2, ranuras usadas: 1

## 3x Stir Up Trouble — A_MEDIAS **[en mazo: pauper, brawl]**

`{B}` Sorcery 

> As an additional cost to cast this spell, sacrifice an artifact or creature or pay {4}. | Destroy target creature.

- motor: **DESTROY** 
- frases con efecto: 2, ranuras usadas: 1

## 2x Great Ugly-Looking Goblin // Clap! Snap! — A_MEDIAS **[en mazo: brawl]**

`{5}{B} // {1}{B}` Creature — Goblin Soldier // Sorcery — Adventure 4/4

> Each creature you control with a +1/+1 counter on it has menace. (It can't be blocked except by two or more creatures.) | Amass Goblins 2. (Then exile this card. You may cast the creature later from exile.)

- motor: **ETB_COUNTERS** 
- frases con efecto: 2, ranuras usadas: 1

## 1x Dai Li Indoctrination — A_MEDIAS **[en mazo: brawl]**

`{1}{B}` Sorcery — Lesson 

> Choose one — | • Target opponent reveals their hand. You choose a nonland permanent card from it. That player discards that card. | • Earthbend 2. (Target land you control becomes a 0/0 creature with haste that's still a land. Put two +1/+1 counters on it. When it dies or is exiled, return it to the battlefield tapped.)

- motor: **ETB_DISCARD** 
- frases con efecto: 3, ranuras usadas: 1

## 1x Dwarven Mattock — A_MEDIAS **[en mazo: brawl]**

`{2}` Artifact — Equipment 

> When this Equipment enters, attach it to target Dwarf you control. | Equipped creature gets +2/+2 and has ward {1}. (Whenever equipped creature becomes the target of a spell or ability an opponent controls, counter it unless that player pays {1}.) | Equip {3} ({3}: Attach to target creature you control. Equip only as a sorcery.)

- motor: **EQUIP** 
- frases con efecto: 3, ranuras usadas: 1

## 1x Gathering of Darkness — A_MEDIAS **[en mazo: brawl]**

`{3}{B}` Sorcery 

> Return up to one target creature card from your graveyard to your hand. | Amass Goblins 3. (Put three +1/+1 counters on an Army you control. It's also a Goblin. If you don't control an Army, create a 0/0 black Goblin Army creature token first.)

- motor: **AMASS** 
- frases con efecto: 2, ranuras usadas: 1

## 1x Gnashing of Teeth — A_MEDIAS **[en mazo: brawl]**

`{1}{B}{B}` Sorcery 

> Choose one — | • Target creature gets -5/-5 until end of turn. If that creature would die this turn, exile it instead. | • Creatures target player controls get -1/-1 until end of turn.

- motor: **DESTROY** 
- frases con efecto: 3, ranuras usadas: 1

## 1x Heartless Act — A_MEDIAS **[en mazo: brawl]**

`{1}{B}` Instant 

> Choose one — | • Destroy target creature with no counters on it. | • Remove up to three counters from target creature.

- motor: **DESTROY** 
- frases con efecto: 3, ranuras usadas: 1

## 1x Hog-Monkey — A_MEDIAS **[en mazo: pauper, brawl]**

`{2}{B}` Creature — Boar Monkey 3/2

> At the beginning of combat on your turn, target creature you control with a +1/+1 counter on it gains menace until end of turn. (It can't be blocked except by two or more creatures.) | Exhaust — {5}: Put two +1/+1 counters on this creature. (Activate each exhaust ability only once.)

- motor: **ETB_COUNTERS** 
- frases con efecto: 2, ranuras usadas: 1

## 1x Mongoose Lizard — A_MEDIAS **[en mazo: pauper]**

`{4}{R}{R}` Creature — Mongoose Lizard 5/6

> Menace (This creature can't be blocked except by two or more creatures.) | When this creature enters, it deals 1 damage to any target. | Mountaincycling {2} ({2}, Discard this card: Search your library for a Mountain card, reveal it, put it into your hand, then shuffle.)

- motor: **DMG_ANY** 
- frases con efecto: 2, ranuras usadas: 1

## 1x Old Fat Spider — A_MEDIAS **[en mazo: standard]**

`{4}{G}{G}` Creature — Spider 6/7

> Reach | This creature can't be blocked by creatures with power 2 or less. | Whenever this creature becomes the target of a spell or ability an opponent controls, draw a card.

- motor: **ETB_DRAW** 
- frases con efecto: 2, ranuras usadas: 1

## 1x Ragged Short Spear — A_MEDIAS **[en mazo: pauper]**

`{1}{R}` Artifact — Equipment 

> When this Equipment enters, you may discard a card. If you do, draw two cards. | Equipped creature gets +2/+0. | Equip {3} ({3}: Attach to target creature you control. Equip only as a sorcery.)

- motor: **ETB_DRAW/EQUIP** 
- frases con efecto: 3, ranuras usadas: 2

## 1x Reverent Howl — A_MEDIAS **[en mazo: standard, pauper, brawl]**

`{2}{B}` Instant 

> Choose one — | • Target player draws two cards and loses 2 life. | • Target creature gets +2/+2 and gains lifelink until end of turn.

- motor: **ETB_DRAW** 
- frases con efecto: 3, ranuras usadas: 1

## 1x The Arkenstone // Seek the Heart — A_MEDIAS **[en mazo: standard]**

`{5} // {2}{W}` Legendary Artifact // Sorcery — Adventure 

> Creatures you control get +1/+1. | At the beginning of your end step, draw a card. | Search your library for a legendary creature card, reveal it, put it into your hand, then shuffle. (Then exile this card. You may cast the artifact later from exile.)

- motor: **LORD/UPKEEP_DRAW** 
- frases con efecto: 3, ranuras usadas: 2

## 1x The Great Goblin — A_MEDIAS **[en mazo: standard]**

`{1}{B/R}{B/R}` Legendary Creature — Goblin Noble 3/2

> Whenever you put one or more counters on a Goblin, Orc, or Army you control, The Great Goblin deals 2 damage to target opponent. | Whenever another Goblin, Orc, or Army you control dies, exile the top card of your library. You may play it until the end of your next turn.

- motor: **ETB_DRAW** 
- frases con efecto: 2, ranuras usadas: 1

## 6x Dwarven Shortsword — A_MEDIAS

`{3}{W}` Artifact — Equipment 

> When this Equipment enters, create a 2/2 red Dwarf creature token, then attach this Equipment to it. | Equipped creature gets +1/+2. | Equip {2} ({2}: Attach to target creature you control. Equip only as a sorcery.)

- motor: **ETB_TOKEN/EQUIP** 
- frases con efecto: 3, ranuras usadas: 2

## 4x Confusticate and Bebother — A_MEDIAS

`{2}{U}` Instant 

> Choose one — | • Counter target spell unless its controller pays {4}. | • Draw two cards, then discard a card.

- motor: **COUNTER** 
- frases con efecto: 3, ranuras usadas: 1

## 4x Moment of Glory — A_MEDIAS

`{W}` Sorcery 

> Put a +1/+1 counter on target creature you control. If this spell was cast from a graveyard, also put a +1/+1 counter on each other creature you control. | Flashback {4}{W} (You may cast this card from your graveyard for its flashback cost. Then exile it.)

- motor: **ETB_COUNTERS** 
- frases con efecto: 2, ranuras usadas: 1

## 4x Tidings of War — A_MEDIAS

`{R}` Sorcery 

> Amass Goblins 1. If this spell was cast from a graveyard, amass Goblins 3 instead. (To amass Goblins X, put X +1/+1 counters on an Army you control. It's also a Goblin. If you don't control an Army, create a 0/0 black Goblin Army creature token first.) | Flashback {3}{R} (You may cast this card from your graveyard for its flashback cost. Then exile it.)

- motor: **AMASS** 
- frases con efecto: 2, ranuras usadas: 1

## 3x Bilbo, Luckwearer // Burglar's Plot — A_MEDIAS

`{1}{U} // {4}{U}` Legendary Creature — Halfling Rogue // Sorcery — Adventure 1/1

> Bilbo can't be blocked. | Whenever Bilbo deals combat damage to a player, draw a card, then discard a card. | Exchange control of two target nonland permanents that share a card type. (Then exile this card. You may cast the creature later from exile.)

- motor: **DRAW_ON_DMG** 
- frases con efecto: 3, ranuras usadas: 1

## 3x Pinecone Strike — A_MEDIAS

`{1}{R}` Instant 

> Choose one or both — | • Pinecone Strike deals 3 damage to target creature. If that creature would die this turn, exile it instead. | • Destroy target artifact token.

- motor: **DMG_SPELL** 
- frases con efecto: 3, ranuras usadas: 1

## 3x Plunder the Trollshaws — A_MEDIAS

`{1}{U}` Instant 

> Draw a card. If this spell was cast from a graveyard, draw two cards instead. | Flashback {3}{U} (You may cast this card from your graveyard for its flashback cost. Then exile it.)

- motor: **ETB_DRAW** 
- frases con efecto: 2, ranuras usadas: 1

## 2x Burn, Burn, Tree and Fern — A_MEDIAS

`{3}{R}` Enchantment — Saga 

> (As this Saga enters and after your draw step, add a lore counter. Sacrifice after IV.) | I — This Saga deals 6 damage to target creature an opponent controls. | II — Destroy target artifact an opponent controls. | III, IV — Add {R}.

- motor: **DMG_SPELL/ENGINE** 
- frases con efecto: 3, ranuras usadas: 2

## 2x Curious Farm Animals — A_MEDIAS

`{W}` Creature — Boar Elk Bird Ox 1/1

> When this creature dies, you gain 3 life. | {2}, Sacrifice this creature: Destroy up to one target artifact or enchantment.

- motor: **NADA** die_eff=LIFEGAIN
- frases con efecto: 2, ranuras usadas: 1

## 2x Down // Dirty — A_MEDIAS

`{3}{B} // {2}{G}` Sorcery // Sorcery 

> Target player discards two cards. | Fuse (You may cast one or both halves of this card from your hand.) | Return target card from your graveyard to your hand. | Fuse (You may cast one or both halves of this card from your hand.)

- motor: **ETB_DISCARD** 
- frases con efecto: 2, ranuras usadas: 1

## 2x Dáin's Company — A_MEDIAS

`{R}{W}` Creature — Dwarf Warrior 2/2

> This creature has lifelink as long as you control another Dwarf. | When this creature enters, look at the top four cards of your library. You may reveal a Dwarf or Equipment card from among them and put it into your hand. Put the rest on the bottom of your library in a random order.

- motor: **ETB_DRAW** 
- frases con efecto: 2, ranuras usadas: 1

## 2x Esgaroth Garrison — A_MEDIAS

`{4}{W}` Creature — Human Soldier */5

> Esgaroth Garrison's power is equal to the number of creatures you control. | When this creature enters, recruit. (Draw a card, then discard a card. If you discarded a nonland card, create a 1/1 white Human Soldier creature token.)

- motor: **LOOT_TOKEN** 
- frases con efecto: 2, ranuras usadas: 1

## 2x Magnificent End — A_MEDIAS

`{4}{W}` Instant 

> This spell costs {3} less to cast if it targets a tapped creature. | Magnificent End deals 5 damage to target creature.

- motor: **DMG_SPELL** 
- frases con efecto: 2, ranuras usadas: 1

## 2x Old Fat Spider Can't See Me — A_MEDIAS

`{2}{U}` Enchantment — Saga 

> (As this Saga enters and after your draw step, add a lore counter. Sacrifice after IV.) | I — Target creature you control gains hexproof for as long as this Saga remains on the battlefield. | II — Prevent all damage that would be dealt by up to one target creature for as long as this Saga remains on the battlefield. | III, IV — Draw a card.

- motor: **PROTECT/ENGINE** 
- frases con efecto: 3, ranuras usadas: 2

## 2x Thorin's Last Stand — A_MEDIAS

`{2}{W}{W}` Instant 

> Choose one — | • Creatures you control get +2/+1 until end of turn. | • Destroy target artifact or enchantment. You gain 2 life.

- motor: **LORD** 
- frases con efecto: 3, ranuras usadas: 1

## 2x Thranduil, Sindarin Liege // Silvan Rally — A_MEDIAS

`{2}{G/U}{G/U} // {1}{G/U}{G/U}` Legendary Creature — Elf Noble // Sorcery — Adventure 2/3

> Other Elves you control get +1/+1. | Landfall — Whenever a land you control enters, create a 1/1 green Elf creature token. | Mill four cards, then put up to two land cards from among them into your hand. (Then exile this card. You may cast the creature later from exile.)

- motor: **ETB_TOKEN/COND_BUFF** 
- frases con efecto: 3, ranuras usadas: 2

## 1x Airbender's Reversal — A_MEDIAS

`{1}{W}` Instant — Lesson 

> Choose one — | • Destroy target attacking creature. | • Airbend target creature you control. (Exile it. While it's exiled, its owner may cast it for {2} rather than its mana cost.)

- motor: **DESTROY** 
- frases con efecto: 3, ranuras usadas: 1

## 1x Airbending Lesson — A_MEDIAS

`{2}{W}` Instant — Lesson 

> Airbend target nonland permanent. (Exile it. While it's exiled, its owner may cast it for {2} rather than its mana cost.) | Draw a card.

- motor: **ETB_DRAW** 
- frases con efecto: 2, ranuras usadas: 1

## 1x Bilbo Baggins, Burglar // Take a Glance — A_MEDIAS

`{2}{U} // {U}` Legendary Creature — Halfling Rogue // Sorcery — Adventure 2/1

> When Bilbo Baggins enters, draw a card. | Scry 2. (Then exile this card. You may cast the creature later from exile.)

- motor: **ETB_DRAW** 
- frases con efecto: 2, ranuras usadas: 1

## 1x Celebrate the Mountain-king — A_MEDIAS

`{3}{W}` Enchantment 

> When this enchantment enters, for each opponent, exile up to one target nonland permanent that player controls until this enchantment leaves the battlefield. | When this enchantment enters, recruit. (Draw a card, then discard a card. If you discarded a nonland card, create a 1/1 white Human Soldier creature token.)

- motor: **LOOT_TOKEN** 
- frases con efecto: 2, ranuras usadas: 1

## 1x Cunning Maneuver — A_MEDIAS

`{1}{R}` Instant 

> Target creature gets +3/+1 until end of turn. | Create a Clue token. (It's an artifact with "{2}, Sacrifice this token: Draw a card.")

- motor: **PUMP** 
- frases con efecto: 2, ranuras usadas: 1

## 1x Firebending Lesson — A_MEDIAS

`{R}` Instant — Lesson 

> Kicker {4} (You may pay an additional {4} as you cast this spell.) | Firebending Lesson deals 2 damage to target creature. If this spell was kicked, it deals 5 damage to that creature instead.

- motor: **DMG_SPELL** 
- frases con efecto: 2, ranuras usadas: 1

## 1x Flopsie, Bumi's Buddy — A_MEDIAS

`{4}{G}{G}` Legendary Creature — Ape Goat 4/4

> When Flopsie enters, put a +1/+1 counter on each creature you control. | Each creature you control with power 4 or greater can't be blocked by more than one creature.

- motor: **ETB_COUNTERS** 
- frases con efecto: 2, ranuras usadas: 1

## 1x Glider Staff — A_MEDIAS

`{2}{W}` Artifact — Equipment 

> When this Equipment enters, airbend up to one target creature. (Exile it. While it's exiled, its owner may cast it for {2} rather than its mana cost.) | Equipped creature gets +1/+1 and has flying. | Equip {2}

- motor: **EQUIP** 
- frases con efecto: 3, ranuras usadas: 1

## 1x Goblin Plate Mail — A_MEDIAS

`{1}{B/R}` Artifact — Equipment 

> When this Equipment enters, amass Goblins 1, then attach this Equipment to the amassed Army. (To amass Goblins 1, put a +1/+1 counter on an Army you control. It's also a Goblin. If you don't control an Army, create a 0/0 black Goblin Army creature token first.) | Equipped creature gets +1/+0 and has menace. | Equip {4}

- motor: **EQUIP/AMASS** 
- frases con efecto: 3, ranuras usadas: 2

## 1x Sandbenders' Storm — A_MEDIAS

`{3}{W}` Instant 

> Choose one — | • Destroy target creature with power 4 or greater. | • Earthbend 3. (Target land you control becomes a 0/0 creature with haste that's still a land. Put three +1/+1 counters on it. When it dies or is exiled, return it to the battlefield tapped.)

- motor: **DESTROY**   cond=2
- frases con efecto: 3, ranuras usadas: 1

## 1x The Last Agni Kai — A_MEDIAS

`{1}{R}` Instant 

> Target creature you control fights target creature an opponent controls. If the creature the opponent controls is dealt excess damage this way, add that much {R}. | Until end of turn, you don't lose unspent red mana as steps and phases end.

- motor: **FIGHT** 
- frases con efecto: 2, ranuras usadas: 1

## 1x Twin Blades — A_MEDIAS

`{2}{R}` Artifact — Equipment 

> Flash | When this Equipment enters, attach it to target creature you control. That creature gains double strike until end of turn. | Equipped creature gets +1/+1. | Equip {2} ({2}: Attach to target creature you control. Equip only as a sorcery.)

- motor: **EQUIP** 
- frases con efecto: 3, ranuras usadas: 1

## 1x Uneasy Partings — A_MEDIAS

`{3}{U}` Instant 

> This spell costs {1} less to cast if it targets an attacking nontoken creature. | Target creature's owner puts it on their choice of the top or bottom of their library.

- motor: **BOUNCE** 
- frases con efecto: 2, ranuras usadas: 1

## 1x Wizard's Staff — A_MEDIAS

`{1}{U}` Artifact — Equipment 

> Equipped creature has prowess. (Whenever its controller casts a noncreature spell, that creature gets +1/+1 until end of turn.) | If a triggered ability of equipped creature triggers, that ability triggers an additional time. | Equip Wizard {1} | Equip {3}

- motor: **EQUIP** 
- frases con efecto: 4, ranuras usadas: 1
