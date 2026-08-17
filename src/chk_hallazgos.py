# -*- coding: utf-8 -*-
"""Cuenta cuantas cartas del banco toca cada uno de los tres hallazgos del detector.

Un cambio que mide exactamente 0.000 puede significar dos cosas MUY distintas: que la
correccion no sirve, o que no se dispara nunca. Ya paso con REGLA_SOLO, que apagaba las
reglas adoptadas y hacia que seis candidatas midieran +0,000 clavado. Antes de gastar el
laboratorio en una hipotesis conviene comprobar que el banco tiene material donde
aplicarla; si no lo tiene, el veredicto correcto es "no medible aqui", no "no funciona".

    python3 src/chk_hallazgos.py
"""
import sys, io
sys.path.insert(0, 'src'); sys.path.insert(0, 'data')
from driver import build
from extract import E, KWBIT

FORMATOS = ['standard', 'pauper', 'brawl']
T_CREA = 1   # mismo codigo que en sim.c / extract.py

# hallazgo -> que campos del encoding lo activan
CARA = {E['BURN_FACE'], E['ETB_DRAIN']}


def main():
    tot = {'lord': 0, 'cara': 0, 'men': 0, 'fs': 0, 'ind': 0}
    for fmt in FORMATOS:
        try:
            R, opps = build(fmt)
        except Exception as ex:
            print(f"{fmt}: no se pudo construir ({ex})"); continue
        print(f"\n=== {fmt} ===")
        for dn, w, ids in opps:
            c = {'lord': 0, 'cara': 0, 'men': 0, 'fs': 0, 'ind': 0}
            quien = {}
            for i in ids:
                e = R.defs[i]
                efs = {e['eff'], e['eff2'], e.get('eff3', 0)}
                if E['LORD'] in efs: c['lord'] += 1; quien.setdefault('lord', set()).add(R.meta[i])
                if efs & CARA:       c['cara'] += 1
                # Las palabras clave solo importan al DECLARAR ATAQUES, asi que solo
                # cuentan en criaturas. Sin este filtro, las 10 "indestructibles" de
                # Grixis Affinity son Darksteel Citadel, que es una tierra y no ataca.
                if e['typ'] != T_CREA: continue
                kw = e['kw']
                if kw & KWBIT['Menace']:          c['men'] += 1; quien.setdefault('men', set()).add(R.meta[i])
                # doble golpe implica dano primero: cuenta para el mismo arreglo
                if kw & (KWBIT['First strike'] | KWBIT['Double strike']): c['fs'] += 1
                if kw & KWBIT['Indestructible']:  c['ind'] += 1; quien.setdefault('ind', set()).add(R.meta[i])
            for k in tot: tot[k] += c[k]
            marca = ' <--' if (c['lord'] or c['men'] or c['fs'] or c['ind']) else ''
            print(f"  {dn:<26} lord {c['lord']:>2}  cara {c['cara']:>2}  "
                  f"amenaza {c['men']:>2}  dano1o {c['fs']:>2}  indes {c['ind']:>2}{marca}")
            for k, v in sorted(quien.items()):
                print(f"       {k}: {', '.join(sorted(v))}")

    print(f"\nTOTAL copias en el banco entero:")
    print(f"  hallazgo 4 (remate letal)   cartas que pegan a la cara : {tot['cara']}")
    print(f"  hallazgo 5 (kw al atacar)   amenaza {tot['men']} / dano primero {tot['fs']} "
          f"/ indestructible {tot['ind']}")
    print(f"  hallazgo 6 (lords)          cartas con E_LORD          : {tot['lord']}")


if __name__ == '__main__':
    main()
