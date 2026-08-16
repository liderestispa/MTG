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

# --- AVISO SERIO SOBRE REAL_FIELD DE PAUPER --------------------------------------
# El 17-ago-2026 se encontro mtgdecks.net/Pauper/winrates, que agrega ~77.000 partidas
# entre 2026-02-18 y 2026-08-17. Dos ordenes de magnitud mas que las 180-640 listas
# semanales que se estan usando aqui. Sus numeros estan en data/wr_mtgdecks_ago2026.json.
#
#   arquetipo           banco    mtgdecks   partidas
#   Grixis Affinity     57,2%     52,0%       6.042
#   Elves               56,1%     51,0%       4.138
#   Mono Red Rally      46,4%     50,0%       3.576
#   Blue Terror         52,0%     49,0%       4.266
#   Mono Red Madness    53,0%     51,0%       8.107
#   Jund Wildfire       49,7%     50,0%       4.167
#
# Lo grave no son las diferencias: es que la DISPERSION cae de 3,66 puntos a 0,96.
# Comprobado que no es artefacto de espejos: el espejo de Madness son 792 de 8.107
# partidas, y al 50% arrastra el total de 51,1% a 51,0%, una decima.
#
# Si Pauper es de verdad un formato plano de +-1 punto, entonces el spread de este banco
# es en buena parte RUIDO de muestras chicas, y la correlacion r=+0,99 que el motor
# presume esta correlacionando contra ese ruido. Es exactamente el caso que docs/
# metodologia.md llama "formato imposible": si los winrates reales varian menos de 2
# puntos, la senal es mas chica que el ruido y ningun modelo gana.
#
# YA SE SACO LA MATRIZ Y SE CALCULO SIN ESPEJO (data/wr_mtgdecks_sin_espejo.json).
# Excluir espejos apenas mueve nada, ~0,1 puntos: el espejo es el 5-10% de las partidas
# y esta al 50%. La compresion es REAL.
#
#   arquetipo           banco   sin espejo   partidas   error 95%
#   Mono Red Madness    53,0%     51,11%       7.315     +-1,15
#   Grixis Affinity     57,2%     52,19%       5.526     +-1,32
#   Blue Terror         52,0%     48,94%       4.014     +-1,55
#   Jund Wildfire       49,7%     50,00%       3.949     +-1,56
#   Elves               56,1%     51,07%       3.884     +-1,57
#   Mono Red Rally      46,4%     50,00%       3.398     +-1,68
#
#   dispersion real: 1,04 puntos. Error de medicion de cada punto: +-1,2 a +-1,7.
#   La separacion entre arquetipos es del MISMO TAMANIO que el error con que se mide.
#
# Y LO QUE ESO LE HACE AL MOTOR, medido:
#
#   contra el banco viejo    r=+0,987   error calibrado 0,58
#   contra mtgdecks (77k)    r=+0,677   error calibrado 0,83
#
# El r=+0,99 que el motor presumia era correlacion contra el RUIDO de muestras chicas.
#
# Revalidacion de lo adoptado el 17-ago contra el dato bueno (error calibrado de Pauper):
#
#   motor de hoy                    0,83
#   sin las dos reglas de datos     0,96   <- unico cambio con efecto claro
#   sin ranura de cementerio        0,81   <- su gran mejora era ruido: DESAPARECE
#   sin habilidades activadas       0,84   <- dentro del ruido
#   sin arreglo de combate          0,83   <- sin efecto en Pauper (ayudaba a Brawl)
#
# O sea: de todo lo adoptado ese dia, lo unico que se sostiene contra dato solido son las
# dos reglas del extractor (retroceso de Lava Dart y vida de Reckoner's Bargain). El
# resto cae dentro del ruido. Ojo igual: n=6, asi que diferencias de r de 0,02 no
# significan nada tampoco en esta tabla.
#
# NO se ha cambiado REAL_FIELD todavia, por dos motivos honestos:
#   1. Son poblaciones distintas. mtgdecks mezcla MTGO y papel y todos los tamanios de
#      evento; el banco usa Challenge de MTGO, no-espejo. La pagina tiene filtros
#      (MTGO/TABLETOP, 32+ jugadores, excluir baneadas) que hay que aplicar antes.
#   2. Hay que sacar la matriz de enfrentamientos completa y calcular el winrate SIN
#      espejo, que es lo que este banco define.
#
# Es probablemente el trabajo mas valioso que queda en todo el proyecto: si el dato nuevo
# se sostiene, baja el suelo de ruido de 3,25 a menos de 1 punto Y obliga a revisar todo
# lo que se adopto contra el banco viejo.

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
