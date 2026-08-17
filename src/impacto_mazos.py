# -*- coding: utf-8 -*-
"""Cuanto mueve un cambio del motor a los mazos YA elegidos (los de out/results.json).

Regla 3 del proyecto: despues de tocar el motor hay que revalidar los mazos. revalidar.py
lo hace contra out/*_v4.json, que son los de una campana anterior. Esto mira los vigentes
y, sobre todo, compara CON y SIN el cambio, que es la pregunta que importa antes de
adoptar: un arreglo puede medir cero contra el dato real y aun asi mover el indice de la
lista propia, porque la coleccion de Ricardo si tiene la materia que al banco le falta
(The Arkenstone es un lord y esta en el mazo de Standard).

    python3 src/impacto_mazos.py "KW_ATAQUE=1 LORD_VE=1"
    python3 src/impacto_mazos.py "LORD_VE=1" 3000
"""
import sys, os, io, json
sys.path.insert(0, 'src'); sys.path.insert(0, 'data')
from driver import build, run
from search import objective, build_pool_index, load_util, greedy_counts, make_deck

SPEC = sys.argv[1] if len(sys.argv) > 1 else ''
NG = int(sys.argv[2]) if len(sys.argv) > 2 else 2500
SEMILLAS = [31337, 606060, 8112024]


def con(spec, fn):
    previo = {}
    for par in spec.split():
        if '=' not in par: continue
        k, v = par.split('=', 1)
        previo[k] = os.environ.get(k); os.environ[k] = v
    try:
        return fn()
    finally:
        for k, v in previo.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v


def mide(fmt, d):
    """El mazo COMPLETO de 60. out/results.json guarda solo los hechizos: las tierras
    las pone make_deck a partir de nland y las utilitarias. Medirlo sin eso daba un
    mazo de 36 cartas sin base de mana, que no lanza nada y por eso salia identico
    bit a bit con cualquier bandera."""
    R, opps = build(fmt)
    info = build_pool_index(fmt, R); util = load_util(R)
    idx = {R.meta[i]: i for i in R.meta}
    counts = {}
    for nm, n in d['counts'].items():
        counts[idx[nm] if nm in idx else R.add_by_name(nm)] = n
    cols = list(d['colors']); nl = d['nland']
    deck = make_deck(fmt, R, info, counts, cols, nl, util)
    semilla = make_deck(fmt, R, info,
                        greedy_counts(info, cols, sum(d['counts'].values()), fmt),
                        cols, nl, util)
    vals, valsg = [], []
    for s in SEMILLAS:
        vals.append(objective(run(R, opps, [deck], ngames=NG, life=20, seed=s)[0]) * 100)
        valsg.append(objective(run(R, opps, [semilla], ngames=NG, life=20, seed=s)[0]) * 100)
    return vals, valsg


def main():
    res = json.load(io.open('out/results.json', encoding='utf-8'))
    print(f"spec: {SPEC or '(defaults)'}   {NG} partidas x {len(SEMILLAS)} semillas")
    print("(indice bruto del mazo, y su ventaja sobre la semilla codiciosa)\n")
    print(f"{'formato':<10} {'mazo sin':>10} {'mazo con':>10} {'delta':>8}   "
          f"{'vs semilla sin':>15} {'vs semilla con':>15}")
    for fmt, d in res.items():
        base, baseg = con('', lambda: mide(fmt, d))
        var,  varg  = con(SPEC, lambda: mide(fmt, d))
        mb, mv = sum(base) / len(base), sum(var) / len(var)
        vb = mb - sum(baseg) / len(baseg)
        vv = mv - sum(varg) / len(varg)
        print(f"{fmt:<10} {mb:>10.2f} {mv:>10.2f} {mv-mb:>+8.2f}   "
              f"{vb:>+15.2f} {vv:>+15.2f}")


if __name__ == '__main__':
    main()
