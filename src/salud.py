# -*- coding: utf-8 -*-
"""Se niega a medir con binarios viejos.

EL ERROR QUE ESTE ARCHIVO EXISTE PARA EVITAR

bin_brawl no se compila de sim.c: se compila de src/sim_brawl.c, que src/gen_brawl.py
GENERA a partir de sim.c. O sea que tocar el motor NO llega a Brawl hasta que alguien
se acuerda de regenerar, y nada avisaba de la diferencia.

El 17-ago costo medio dia. Se implementaron cuatro cambios, se midieron contra dato real
y los cuatro dieron cero clavado, asi que se documentaron como "no medibles con este
banco" y se escribio media pagina de teoria explicando por que. Al regenerar bin_brawl
por otro motivo, el residuo de Brawl paso de 2,06 a 0,04 y el objetivo de 1,072 a 0,609:
uno de los cuatro era la mejora mas grande del proyecto y estaba tapada por un .exe
viejo. Las conclusiones de esa media pagina eran todas falsas.

No es un despiste tonto: es la misma trampa que "un fix repartido entre Python y C hay
que commitearlo entero", con un eslabon mas. Y no da error, da NUMEROS, que es peor.

    from salud import exige_binarios_al_dia
    exige_binarios_al_dia()        # revienta con instrucciones si algo esta viejo
    exige_binarios_al_dia(avisar=True)   # solo advierte por stderr

    python3 src/salud.py           # comprobar a mano
"""
import os, sys, subprocess

# binario -> fuentes de las que depende
CADENA = {
    'bin_sim':   ['src/sim.c'],
    # sim_brawl.c se genera de sim.c, asi que bin_brawl depende de LOS DOS
    'bin_brawl': ['src/sim.c', 'src/gen_brawl.py', 'src/sim_brawl.c'],
}

ARREGLO = """  gcc -O3 -w -o bin_sim src/sim.c -lm
  python3 src/gen_brawl.py && sed -i 's/^static int CMD_A, CMD_B;$/static int CMD_A=-1, CMD_B=-1;/' src/sim_brawl.c
  gcc -O3 -w -o bin_brawl src/sim_brawl.c -lm"""


def _mtime(ruta):
    for cand in (ruta, ruta + '.exe'):
        if os.path.exists(cand):
            return os.path.getmtime(cand)
    return None


def revisa():
    """Devuelve la lista de problemas encontrados, vacia si todo esta al dia."""
    problemas = []
    for binario, fuentes in CADENA.items():
        tb = _mtime(binario)
        if tb is None:
            problemas.append(f"{binario} no existe")
            continue
        for f in fuentes:
            tf = _mtime(f)
            if tf is None:
                problemas.append(f"falta {f}")
            elif tf > tb:
                problemas.append(f"{binario} es mas viejo que {f} "
                                 f"({(tf - tb) / 60:.0f} min de diferencia)")
    return problemas


def exige_binarios_al_dia(avisar=False):
    p = revisa()
    if not p:
        return True
    msg = ("BINARIOS DESINCRONIZADOS. Medir asi da numeros que parecen buenos y no lo son:\n"
           + '\n'.join(f"  - {x}" for x in p)
           + "\n\nRecompila:\n" + ARREGLO
           + "\n\n(SALUD_OFF=1 lo salta, bajo tu responsabilidad)")
    if os.environ.get('SALUD_OFF') == '1':
        sys.stderr.write('[salud] ' + msg.splitlines()[0] + '  (SALUD_OFF=1, sigo)\n')
        return False
    if avisar:
        sys.stderr.write(msg + '\n')
        return False
    raise SystemExit(msg)


if __name__ == '__main__':
    p = revisa()
    if not p:
        print("binarios al dia")
    else:
        print("PROBLEMAS:")
        for x in p: print("  -", x)
        print("\nRecompila:\n" + ARREGLO)
        sys.exit(1)
