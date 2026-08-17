#!/usr/bin/env bash
# Recompila LOS DOS binarios. Usa esto y no gcc a mano.
#
# bin_brawl no sale de sim.c: sale de src/sim_brawl.c, que gen_brawl.py genera a partir
# de sim.c. Compilar solo bin_sim deja Brawl corriendo con el motor de antes, y eso no da
# ningun error: da numeros. El 17-ago escondio la mejora mas grande del proyecto durante
# medio dia (residuo de Brawl clavado en 2,06 cuando lo cierto era 0,04).
#
#     bash scripts/build.sh
set -e
cd "$(dirname "$0")/.."

gcc -O3 -w -o bin_sim src/sim.c -lm
echo "bin_sim ok"

PYTHONUTF8=1 python src/gen_brawl.py
# gen_brawl deja los comandantes sin inicializar y en C eso es 0, que es un indice de
# carta valido: hay que dejarlos en -1 o el motor cree que todo el mundo tiene comandante.
sed -i 's/^static int CMD_A, CMD_B;$/static int CMD_A=-1, CMD_B=-1;/' src/sim_brawl.c
gcc -O3 -w -o bin_brawl src/sim_brawl.c -lm
echo "bin_brawl ok"

PYTHONUTF8=1 python src/salud.py
