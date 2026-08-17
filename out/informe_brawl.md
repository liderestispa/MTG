# Standard Brawl — el mazo para armar

**Comandante: The Sackville-Bagginses**  (B)

35 hechizos + 24 tierras + comandante = 60

Indice bruto del motor: **38.6%** contra el campo. Partida media 7.4 turnos.

## Donde cae contra el metajuego

| mazo | motor |
|---|---|
| Elspeth Storm Slayer | 66.4% |
| Ketramose the New Dawn | 62.2% |
| Sephiroth Fabled SOLDIER | 44.4% |
| **TU MAZO (The Sackville-Bagginses)** | **38.6%** |
| Tifa Lockhart | 28.8% |
| Eluge the Shoreless Sea | 24.4% |
| Kona Rescue Beastie | 24.2% |

## Enfrentamiento por enfrentamiento

| contra | ganas |
|---|---|
| Eluge the Shoreless Sea | 78.2% |
| Tifa Lockhart | 74.3% |
| Kona Rescue Beastie | 62.1% |
| Sephiroth Fabled SOLDIER | 36.9% |
| Ketramose the New Dawn | 29.2% |
| Elspeth Storm Slayer | 12.3% |

## Legalidad y armabilidad: OK

Legal en Standard Brawl y armable con la coleccion, carta por carta.

## La lista


**1 mana**

- Giant's Boulder — `{1}` Artifact
- Key to the Side-Door — `{1}` Artifact
- Stir Up Trouble — `{B}` Sorcery

**2 mana**

- Corrupt Court Official — `{1}{B}` 1/1
- Dai Li Indoctrination — `{1}{B}` Sorcery
- Desolation Prowler — `{1}{B}` 2/2
- Dwarven Mattock — `{2}` Artifact
- Front Porch Sentries — `{1}{B}` 2/2
- Gollum the Abandoned — `{1}{B}` 2/2
- Gollum, Riddle Master — `{1}{B}` 3/1
- Heartless Act — `{1}{B}` Instant
- Joo Dee, One of Many — `{1}{B}` 2/2
- Merchant of Many Hats — `{1}{B}` 2/2
- Old Thrush — `{2}` 1/2
- Ravening Warg — `{1}{B}` 2/2
- Stony-Voiced Goblins — `{1}{B}` 1/1
- Thrór's Map — `{2}` Legendary Artifact

**3 mana**

- Along the Crooked Way — `{2}{B}` Enchantment
- Bender's Waterskin — `{3}` Artifact
- Bilbo's Deadly Slice — `{1}{B}{B}` Instant
- Boiling Rock Rioter — `{2}{B}` 3/3
- Crude Bent Blade — `{2}{B}` Artifact
- Gnashing of Teeth — `{1}{B}{B}` Sorcery
- Hog-Monkey — `{2}{B}` 3/2
- Long-Bodied Grey Dog — `{3}` 2/2
- Rage into the Valley — `{2}{B}` Sorcery
- Reverent Howl — `{2}{B}` Instant

**4 mana**

- Foggy Swamp Hunters — `{3}{B}` 3/4
- Gathering of Darkness — `{3}{B}` Sorcery
- Gollum, Silent Slinker // Meager Meal — `{3}{B} // {B}` 4/3
- Head of the Hunt — `{2}{B}{B}` 4/3
- Phoenix Fleet Airship — `{2}{B}{B}` 4/4

**5 mana**

- Beetle-Headed Merchants — `{4}{B}` 5/4
- Dreaded Bat-Cloud — `{4}{B}` 4/2

**6 mana**

- Great Ugly-Looking Goblin // Clap! Snap! — `{5}{B} // {1}{B}` 4/4

**Tierras**

- 23x Swamp
- 1x Jasmine Dragon Tea Shop

## Que hay que creerle a esto

- El **porcentaje bruto no es una prediccion**. `src/escala.py` se niega a calibrar el nivel de Brawl: solo hay dos winrates reales publicados y los dos estan entre 73% y 77%, asi que ajustar una recta con n=2 devuelve 90% para cualquier cosa.
- Lo que **si** vale es la posicion relativa y los enfrentamientos: son comparaciones dentro del mismo motor, con semillas independientes.
- El motor lee bien 93 de las 204 cartas de la coleccion, a medias 76, mudas 30 y mal leidas 5. Los mazos se buscan sobre esa lectura, asi que las mudas estan INFRAvaloradas y pueden ser mejores de lo que el motor cree.