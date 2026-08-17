# -*- coding: utf-8 -*-
"""Informe de Standard Brawl: el mazo, contra quien gana, y que hay que creerle.

Se separa de build_report_v6 a proposito. Aquel cubre los tres formatos y da un numero
calibrado; en Brawl la escala se NIEGA a calibrar el nivel —solo hay dos winrates reales
publicados, los dos entre 73% y 77%, y ajustar una recta con eso devuelve 90% para
cualquier cosa— asi que aqui no se inventa un porcentaje. Lo que si se puede afirmar es
la POSICION contra el campo, mazo por mazo, y eso es lo que se reporta.

    python3 src/informe_brawl.py            # a pantalla y a out/informe_brawl.md
"""
import sys, io, json
sys.path.insert(0, 'src'); sys.path.insert(0, 'data')
from brawl import build_brawl, run_brawl, objective
from driver import lookup
from calibrate import rr
from check_legal import check

NG = 3000
SEMILLAS = [31337, 606060, 8112024]


def main():
    b = json.load(io.open('out/brawl_result.json', encoding='utf-8'))
    R, opps = build_brawl()
    cmd = R.add_by_name(b['commander'])
    ids = [R.add_by_name(n) for n in b['spells']] + [R.add_by_name(n) for n in b['lands']]

    # winrate contra el campo, y contra cada mazo por separado
    vals = [run_brawl(R, opps, [(cmd, ids)], ngames=NG, life=25, seed=s)[0]
            for s in SEMILLAS]
    wr = sum(v['wr'] for v in vals) / len(vals) * 100
    turnos = sum(v['gamelen'] for v in vals) / len(vals)

    por_mazo = []
    for dn, w, cmd2, ids2 in opps:
        v = [run_brawl(R, [(dn, 1000, cmd2, ids2)], [(cmd, ids)], ngames=NG, life=25, seed=s)[0]
             for s in SEMILLAS]
        por_mazo.append((dn, sum(x['wr'] for x in v) / len(v) * 100))
    por_mazo.sort(key=lambda x: -x[1])

    # el campo entre si, para saber donde cae el nuestro
    names, ws, M = rr('brawl', ngames=2000, life=25, seed=31337)
    tot = sum(ws)
    campo = sorted(((n, sum(M[i][j] * ws[j] for j in range(len(names))) / tot * 100)
                    for i, n in enumerate(names)), key=lambda x: -x[1])

    from collections import Counter
    try:
        _cta = Counter(r['estado'] for r in
                       json.load(io.open('out/ficha_coleccion.json', encoding='utf-8')))
    except (OSError, ValueError):
        _cta = Counter()
    L = ["# Standard Brawl — el mazo para armar", ""]
    L += [f"**Comandante: {b['commander']}**  ({b['ci'] or 'incoloro'})", "",
          f"{len(b['spells'])} hechizos + {len(b['lands'])} tierras + comandante = 60", "",
          f"Indice bruto del motor: **{wr:.1f}%** contra el campo. Partida media "
          f"{turnos:.1f} turnos.", ""]

    L += ["## Donde cae contra el metajuego", "",
          "| mazo | motor |", "|---|---|"]
    puesto = 0
    for n, v in campo:
        if v < wr and not puesto:
            L.append(f"| **TU MAZO ({b['commander']})** | **{wr:.1f}%** |"); puesto = 1
        L.append(f"| {n} | {v:.1f}% |")
    if not puesto:
        L.append(f"| **TU MAZO ({b['commander']})** | **{wr:.1f}%** |")

    L += ["", "## Enfrentamiento por enfrentamiento", "",
          "| contra | ganas |", "|---|---|"]
    for dn, v in por_mazo:
        L.append(f"| {dn} | {v:.1f}% |")

    errs, warns = check(b['spells'] + b['lands'], 'brawl', commander=b['commander'],
                        deck_size=60, singleton=True)
    L += ["", f"## Legalidad y armabilidad: {'OK' if not errs else 'PROBLEMAS'}", ""]
    for e in errs:  L.append(f"- ERROR: {e}")
    for w in warns: L.append(f"- aviso: {w}")
    if not errs:
        L.append("Legal en Standard Brawl y armable con la coleccion, carta por carta.")

    # la lista
    L += ["", "## La lista", ""]
    filas = []
    for nm in b['spells']:
        c = lookup(nm)
        pt = f"{c.get('power')}/{c.get('toughness')}" if c.get('power') else \
             (c.get('type_line') or '').split('—')[0].strip()
        filas.append((c.get('cmc') or 0, nm, c.get('mana_cost') or '', pt))
    filas.sort()
    ult = None
    for cmc, nm, mc, pt in filas:
        if cmc != ult:
            L += ["", f"**{int(cmc)} mana**", ""]; ult = cmc
        L.append(f"- {nm} — `{mc}` {pt}")
    from collections import Counter
    L += ["", "**Tierras**", ""]
    for nm, n in Counter(b['lands']).most_common():
        L.append(f"- {n}x {nm}")

    L += ["", "## Que hay que creerle a esto", "",
          "- El **porcentaje bruto no es una prediccion**. `src/escala.py` se niega a "
          "calibrar el nivel de Brawl: solo hay dos winrates reales publicados y los dos "
          "estan entre 73% y 77%, asi que ajustar una recta con n=2 devuelve 90% para "
          "cualquier cosa.",
          "- Lo que **si** vale es la posicion relativa y los enfrentamientos: son "
          "comparaciones dentro del mismo motor, con semillas independientes.",
          f"- El motor lee bien {_cta['ok']} de las {sum(_cta.values())} cartas de la "
          f"coleccion, a medias {_cta['A_MEDIAS']}, mudas {_cta['MUDA']} y mal leidas "
          f"{_cta['MAL_LEIDA']}. Los mazos se buscan sobre esa lectura, asi que las mudas "
          f"estan INFRAvaloradas y pueden ser mejores de lo que el motor cree."]

    txt = '\n'.join(L)
    io.open('out/informe_brawl.md', 'w', encoding='utf-8').write(txt)
    print(txt)


if __name__ == '__main__':
    main()
