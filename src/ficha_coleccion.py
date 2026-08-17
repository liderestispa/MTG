# -*- coding: utf-8 -*-
"""Ficha de TODAS las cartas de la coleccion: que dice la carta y que entiende el motor.

Es la union de las dos auditorias, que hasta ahora vivian separadas y solo cubrian la
mitad del problema cada una:

    cobertura_texto.py    encuentra las cartas que el motor NO lee (quedan mudas)
    auditoria_lectura.py  encuentra las que lee MAL (efecto plausible y equivocado)

Las dos direcciones importan y se compensan entre si de forma enganosa. Al arreglar las
sobre-lecturas del 18-ago, Giant's Boulder paso de ser un Vindicate de 1 mana a no hacer
absolutamente nada —su "scry 2" al entrar tampoco esta modelado— y el buscador la siguio
metiendo en el mazo, ahora por barata. Corregir en una sola direccion mueve el error de
sitio en vez de quitarlo.

Ordena por cuanto pesa: copias que tiene Ricardo, y si la carta esta en alguno de los
mazos que hoy se le recomiendan.

    python3 src/ficha_coleccion.py              # todas
    python3 src/ficha_coleccion.py --malas      # solo las que necesitan trabajo
    python3 src/ficha_coleccion.py --md         # a out/ficha_coleccion.md
"""
import sys, io, os, json, re
sys.path.insert(0, 'src'); sys.path.insert(0, 'data')
from driver import lookup
from extract import convert, E, KWBIT
from auditoria_lectura import sospechas, texto

INV = {v: k for k, v in E.items()}
BIT = {v: k for k, v in KWBIT.items()}


def en_mazos():
    dentro = {}
    try:
        for fmt, d in json.load(io.open('out/results.json', encoding='utf-8')).items():
            for nm in d['counts']: dentro.setdefault(nm, []).append(fmt)
    except (OSError, ValueError, KeyError): pass
    try:
        b = json.load(io.open('out/brawl_result.json', encoding='utf-8'))
        for nm in [b['commander']] + b['spells']: dentro.setdefault(nm, []).append('brawl')
    except (OSError, ValueError, KeyError): pass
    return dentro


def frases_de_juego(t):
    """Cuantas frases del texto hacen algo, sin contar recordatorios ni palabras clave."""
    t = re.sub(r'\([^)]*\)', '', t or '')
    n = 0
    for l in t.split('\n'):
        l = l.strip()
        if not l: continue
        if re.match(r'^[\w\s,\'-]+$', l) and len(l.split()) <= 6 and ':' not in l:
            continue                      # linea de palabras clave sueltas
        n += 1
    return n


def ficha(nombre, copias, dentro):
    c = lookup(nombre)
    if not c: return None
    try: e = convert(c)
    except Exception as ex: return dict(carta=nombre, copias=copias, estado='ERROR', nota=str(ex))
    t = texto(c)
    ranuras = [x for x in (e['eff'], e['eff2'], e.get('eff3', 0)) if x]
    extra = [k for k in ('die_eff', 'act_eff') if e.get(k)]
    nf = frases_de_juego(t)
    sos = sospechas(c, e)
    if sos:                                   estado = 'MAL_LEIDA'
    elif nf and not ranuras and not extra:    estado = 'MUDA'
    elif nf > len(ranuras) + len(extra):      estado = 'A_MEDIAS'
    else:                                     estado = 'ok'
    return dict(carta=nombre, copias=copias, estado=estado,
                coste=c.get('mana_cost') or '', tipo=c.get('type_line') or '',
                pt=(f"{c.get('power')}/{c.get('toughness')}" if c.get('power') else ''),
                en_mazo=dentro.get(nombre, []),
                frases=nf, ranuras=len(ranuras) + len(extra),
                motor='/'.join(INV.get(x, '?') for x in ranuras) or 'NADA',
                motor_extra=','.join(f"{k}={INV.get(e[k],'?')}" for k in extra),
                kw=[BIT[b] for b in BIT if e['kw'] & b],
                cond=e.get('cond', 0), tax_atk=e.get('tax_atk', 0),
                sospechas=[f"{a}: {b}" for a, b in sos],
                texto=t.replace('\n', ' | '))


def main():
    dentro = en_mazos()
    p = json.load(io.open('data/pool_eng.json', encoding='utf-8'))
    cartas = p if isinstance(p, list) else list(p.values())[0]
    filas = []
    for c in cartas:
        f = ficha(c.get('name'), c.get('qty', 1), dentro)
        if f: filas.append(f)

    ORDEN = {'MAL_LEIDA': 0, 'MUDA': 1, 'A_MEDIAS': 2, 'ERROR': 3, 'ok': 4}
    filas.sort(key=lambda r: (ORDEN[r['estado']], not r['en_mazo'], -r['copias']))
    json.dump(filas, io.open('out/ficha_coleccion.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    from collections import Counter
    cta = Counter(r['estado'] for r in filas)
    print(f"{len(filas)} cartas de la coleccion\n")
    for k in ('MAL_LEIDA', 'MUDA', 'A_MEDIAS', 'ok', 'ERROR'):
        if cta[k]:
            cop = sum(r['copias'] for r in filas if r['estado'] == k)
            enm = sum(1 for r in filas if r['estado'] == k and r['en_mazo'])
            print(f"   {k:<11} {cta[k]:>3} cartas  {cop:>3} copias  ({enm} en algun mazo nuestro)")

    if '--md' in sys.argv:
        out = ["# Ficha de la coleccion: carta contra motor", ""]
        for r in filas:
            if r['estado'] == 'ok' and '--todas' not in sys.argv: continue
            m = ' **[en mazo: ' + ', '.join(r['en_mazo']) + ']**' if r['en_mazo'] else ''
            out += [f"## {r['copias']}x {r['carta']} — {r['estado']}{m}", "",
                    f"`{r['coste']}` {r['tipo']} {r['pt']}", "",
                    f"> {r['texto']}", "",
                    f"- motor: **{r['motor']}** {r['motor_extra']}"
                    f"{'  cond=' + str(r['cond']) if r['cond'] else ''}"
                    f"{'  tax_atk' if r['tax_atk'] else ''}",
                    f"- frases con efecto: {r['frases']}, ranuras usadas: {r['ranuras']}"]
            out += [f"- {s}" for s in r['sospechas']]
            out.append("")
        io.open('out/ficha_coleccion.md', 'w', encoding='utf-8').write('\n'.join(out))
        print("\nescrito out/ficha_coleccion.md")
    print("escrito out/ficha_coleccion.json")


if __name__ == '__main__':
    main()
