# Standard Brawl — el mazo para armar

**Comandante: Tom, Bert, and William**  (BG)

35 hechizos + 24 tierras + comandante = 60

Indice bruto del motor: **40.0%** contra el campo. Partida media 7.9 turnos.

## Donde cae contra el metajuego

| mazo | motor |
|---|---|
| Elspeth Storm Slayer | 66.4% |
| Ketramose the New Dawn | 61.7% |
| Sephiroth Fabled SOLDIER | 44.3% |
| **TU MAZO (Tom, Bert, and William)** | **40.0%** |
| Tifa Lockhart | 28.7% |
| Kona Rescue Beastie | 26.3% |
| Eluge the Shoreless Sea | 23.9% |

## Enfrentamiento por enfrentamiento

| contra | ganas |
|---|---|
| Eluge the Shoreless Sea | 75.5% |
| Tifa Lockhart | 71.8% |
| Kona Rescue Beastie | 59.1% |
| Sephiroth Fabled SOLDIER | 46.4% |
| Ketramose the New Dawn | 39.2% |
| Elspeth Storm Slayer | 10.0% |

## Legalidad y armabilidad: OK

Legal en Standard Brawl y armable con la coleccion, carta por carta.

## La lista


**1 mana**

- Giant's Boulder — `{1}` Artifact
- Stir Up Trouble — `{B}` Sorcery
- Turtle-Duck — `{G}` 0/4

**2 mana**

- Attercop — `{1}{G}` 2/1
- Corrupt Court Official — `{1}{B}` 1/1
- Dai Li Indoctrination — `{1}{B}` Sorcery
- Front Porch Sentries — `{1}{B}` 2/2
- Gollum the Abandoned — `{1}{B}` 2/2
- Heartless Act — `{1}{B}` Instant
- Old Thrush — `{2}` 1/2
- Quarrel — `{1}{G}` Instant
- Ravening Warg — `{1}{B}` 2/2
- Stony-Voiced Goblins — `{1}{B}` 1/1
- The Sackville-Bagginses — `{1}{B}` 2/2
- Warg Tactics — `{1}{G}` Instant
- Wargling — `{1}{G}` 2/2

**3 mana**

- Bilbo's Deadly Slice — `{1}{B}{B}` Instant
- Crude Bent Blade — `{2}{B}` Artifact
- Duskwatch Hunter — `{2}{B/G}` 3/1
- Gnashing of Teeth — `{1}{B}{B}` Sorcery
- Hog-Monkey — `{2}{B}` 3/2
- Mirkwood Pathmaker — `{2}{G}` */*
- Walltop Sentries — `{2}{G}` 2/3

**4 mana**

- Beifong's Bounty Hunters — `{2}{B}{G}` 4/4
- Foggy Swamp Hunters — `{3}{B}` 3/4
- Head of the Hunt — `{2}{B}{B}` 4/3
- Troll Negotiations — `{2}{G}{G}` Sorcery

**5 mana**

- Beetle-Headed Merchants — `{4}{B}` 5/4
- Beorn, Reluctant Host // Till and Tend — `{4}{G} // {1}{G}` 5/5
- Dreaded Bat-Cloud — `{4}{B}` 4/2
- Large Bear — `{3}{B/G}{B/G}` 5/5
- Wilderland Scrounger — `{4}{G}` 3/6

**6 mana**

- Boughside Wanderers — `{4}{G}{G}` 4/4
- Old Fat Spider — `{4}{G}{G}` 6/7

**7 mana**

- Gigantic Big Bear — `{5}{G}{G}` 10/7

**Tierras**

- 11x Swamp
- 10x Forest
- 1x Mirkwood
- 1x Foggy Bottom Swamp
- 1x Jasmine Dragon Tea Shop

## Que hay que creerle a esto

- El **porcentaje bruto no es una prediccion**. `src/escala.py` se niega a calibrar el nivel de Brawl: solo hay dos winrates reales publicados y los dos estan entre 73% y 77%, asi que ajustar una recta con n=2 devuelve 90% para cualquier cosa.
- Lo que **si** vale es la posicion relativa y los enfrentamientos: son comparaciones dentro del mismo motor, con semillas independientes.
- El motor lee bien 77 de las 204 cartas de la coleccion, a medias 61 y mal 15. Los mazos se buscan sobre esa lectura, asi que las cartas mudas estan INFRAvaloradas y pueden ser mejores de lo que el motor cree.