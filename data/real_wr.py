# -*- coding: utf-8 -*-
"""Winrates REALES publicados. Recopilados el 16 ago 2026.

Calidad de las fuentes, de mejor a peor:
  A) magic.gg  - Regional Championships mayo 2026, PAPEL, no-espejo, miles de partidas.
                 Es el dato mas solido, pero tiene 3 meses.
  B) MTGGoldfish "Power of Pauper" - Challenge 32 de MTGO, no-espejo, semanal.
                 Muestras de 180-640 listas: una sola semana se mueve 17 puntos,
                 asi que aqui se promedian varias semanas.
  C) MTG Nexus  - enfrentamientos directos, 55-95 partidas => +-10 puntos al 95%.
                 Ruidoso, pero es el UNICO dato cabeza-a-cabeza que existe, y un
                 error de 20-30 puntos se ve igual a traves de ese ruido.
  D) untapped.gg - Arena Bo1, bronce-platino. Otra poblacion. NO se usa.
"""

FUENTES = {
 'std_rc':  'https://www.magic.gg/news/metagame-mentor-nineteen-standard-archetypes-deliver-players-to-the-pro-tour',
 'std_pt':  'https://magic.gg/news/metagame-mentor-standard-win-rates-and-lessons-from-pro-tour-secrets-of-strixhaven',
 'nexus':   'https://mtg-nexus.com/meta/standard',
 'pauper':  'https://www.mtggoldfish.com/articles/the-power-of-pauper-common-july-2026-review',
 'gf_std':  'https://www.mtggoldfish.com/metagame/standard',
 'gf_pau':  'https://www.mtggoldfish.com/metagame/pauper',
}

# --- winrate global contra el campo (no-espejo) ---
REAL_FIELD = {
 'standard': {          # magic.gg, Regional Championships mayo 2026 (papel)
   'Izzet Spellementals': 0.511,
   'Four-Color Control':  0.530,
   'Dimir Excruciator':   0.547,
   'Mardu Discard':       0.499,
   # 'Orzhov Lifegain'  -> sin dato publicado
   # 'Dimir Midrange'   -> solo Arena Bo1 (poblacion distinta), no se usa
 },
 'pauper': {            # MTGGoldfish, media de las semanas de MTGO jun-ago 2026
   'Blue Terror':      0.520,   # 50.7 53.7 50.0 50.9 54.6
   'Mono Red Madness': 0.530,   # 52.0 54.3 56.4 49.3   (papel Paupergeddon: 45.2)
   'Mono Red Rally':   0.464,   # 34.6 51.8 47.7 51.5
   'Jund Wildfire':    0.497,   # 52.6 51.5 51.0 50.7 42.5
   'Grixis Affinity':  0.572,   # una sola medicion (abr 2026)
   'Elves':            0.561,   # una sola medicion (jun 2026)
   # 'Tron' -> sin dato publicado en ningun periodo de 2026
 },
 'brawl': {             # winrates de ladder reportados
   'Elspeth Storm Slayer':   0.77,
   'Ketramose the New Dawn': 0.73,
 },
}

# --- mediciones SEMANALES del mismo arquetipo -------------------------------------
# Cada lista son winrates del mismo mazo en semanas distintas de MTGO. Estaban solo como
# comentario al lado de REAL_FIELD, y sin ellas no se puede estimar el suelo de ruido:
# la dispersion semana a semana es la vara contra la que hay que juzgar el error del motor.
# Ojo: 'n' es el numero de semanas, no de partidas. Las muestras semanales son de 180-640
# listas, lo que da un error binomial de 2,5 a 5 puntos por semana.
REAL_SEMANAL = {
 'pauper': {
   'Blue Terror':      [50.7, 53.7, 50.0, 50.9, 54.6],
   'Mono Red Madness': [52.0, 54.3, 56.4, 49.3],
   'Mono Red Rally':   [34.6, 51.8, 47.7, 51.5],
   'Jund Wildfire':    [52.6, 51.5, 51.0, 50.7, 42.5],
   'Grixis Affinity':  [57.2],              # una sola medicion (abr 2026)
   'Elves':            [56.1],              # una sola medicion (jun 2026)
 },
 # Brawl no tiene series: los dos winrates publicados son medidas unicas de ladder,
 # no hay recap semanal equivalente al "Power of Pauper". Por eso su suelo no se puede
 # estimar con este metodo.
 'brawl': {},
 # Standard tampoco: el dato es de los Regional Championships, un evento unico.
 'standard': {},
}

# --- enfrentamientos directos (fila gana a columna) ---
# MTG Nexus. Muestras chicas: usar para detectar errores GRANDES, no para afinar 2 puntos.
REAL_H2H = {
 'standard': [
   ('Izzet Spellementals', 'Dimir Excruciator', 0.538, 87),
   ('Izzet Spellementals', 'Four-Color Control', 0.526, 95),
   ('Izzet Spellementals', 'Dimir Midrange',     0.542, 55),
   ('Four-Color Control',  'Dimir Excruciator',  0.512, 71),
   ('Four-Color Control',  'Mardu Discard',      0.578, 75),
   ('Dimir Excruciator',   'Dimir Midrange',     0.552, 61),
 ],
 'pauper': [],   # no existe dato publicado cabeza-a-cabeza en Pauper
 'brawl':  [],
}
