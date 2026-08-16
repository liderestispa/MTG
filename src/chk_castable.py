# -*- coding: utf-8 -*-
"""Comprueba que cada carta del banco de calibracion se pueda LANZAR en su mazo.

check_legal.py verifica que las listas de Ricardo sean legales y armables con su
coleccion. Esto es lo de al lado y faltaba: que los mazos del META, que son la vara
contra la que se mide el motor, no lleven cartas que su propia base de mana no puede
pagar. Un ladrillo asi no da error: da un mazo que juega con menos cartas y un
arquetipo que parece peor de lo que es.

Se encontro asi: Mono Red Madness llevaba 4 Sneaky Snacker, que es un Hada {U}{B},
en una lista con 19 Montanas y nada mas.

    python3 src/chk_castable.py
"""
import sys
sys.path.insert(0, 'src'); sys.path.insert(0, 'data')
from meta_decks import DECKS
from driver import lookup
from extract import convert

COL = 'WUBRG'


def produce(carta):
    """Colores que esta carta puede producir: tierras y criaturas de mana."""
    c = lookup(carta)
    if not c: return set()
    pm = c.get('produced_mana') or []
    tl = (c.get('type_line') or '')
    if 'Land' in tl or 'Add ' in (c.get('oracle_text') or ''):
        return {x for x in pm if x in COL}
    return set()


def revisa(fmt, nombre, cartas):
    disponibles = set()
    for n, name in cartas:
        disponibles |= produce(name)
    problemas = []
    for n, name in cartas:
        c = lookup(name)
        if not c:
            problemas.append((n, name, 'no existe en el bulk', ''))
            continue
        e = convert(c)
        if 'Land' in (c.get('type_line') or ''): continue
        faltan = {k for k, v in e['pips'].items() if v and k not in disponibles}
        if faltan:
            problemas.append((n, name, f"pide {{{'}{'.join(sorted(faltan))}}}",
                              c.get('mana_cost') or ''))
    return disponibles, problemas


if __name__ == '__main__':
    total = 0
    for fmt, decks in DECKS.items():
        for nombre, peso, cartas in decks:
            disp, probs = revisa(fmt, nombre, cartas)
            if not probs: continue
            total += sum(p[0] for p in probs)
            print(f"\n{fmt}/{nombre}  — el mazo produce {{{''.join(sorted(disp)) or '—'}}}")
            for n, name, motivo, mc in probs:
                print(f"    {n}x {name:<28} {mc:<12} {motivo}  <-- INLANZABLE")
    if total:
        print(f"\n{total} copias inlanzables en el banco. Cada una es una carta muerta que "
              f"hunde a su arquetipo\nsin dar ningun error: el motor simplemente nunca las juega.")
    else:
        print("Todas las cartas del banco son lanzables con la base de mana de su mazo.")
