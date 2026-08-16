"""Diagnostico: tamano de mano por turno y eficacia del descarte, por mazo del meta."""
import sys; sys.path.insert(0,'src')
from driver import build, run
from brawl import build_brawl, run_brawl

def go(fmt, ng=600):
    life = 25 if fmt=='brawl' else 20
    print(f"\n{'='*84}\n{fmt.upper()}\n{'='*84}")
    print(f"{'mazo':<28}{'mano T3':>9}{'T6':>7}{'T9':>7} | {'riv T3':>8}{'T6':>7}{'T9':>7} | {'desc':>6}{'acier':>7}{'manoRiv':>8}")
    if fmt=='brawl':
        R,opps=build_brawl()
        for i,(dn,w,cmd,ids) in enumerate(opps):
            others=[(o[0],1000,o[2],o[3]) for j,o in enumerate(opps) if j!=i]
            r=run_brawl(R,others,[(cmd,ids)],ngames=ng,life=life,seed=4242)[0]
            row(dn,r)
    else:
        R,opps=build(fmt)
        for i,(dn,w,ids) in enumerate(opps):
            others=[(o[0],1000,o[2]) for j,o in enumerate(opps) if j!=i]
            r=run(R,others,[ids],ngames=ng,life=life,seed=4242)[0]
            row(dn,r)

def row(dn,r):
    print(f"{dn[:27]:<28}{r['hA3']:9.2f}{r['hA6']:7.2f}{r['hA9']:7.2f} | "
          f"{r['hB3']:8.2f}{r['hB6']:7.2f}{r['hB9']:7.2f} | "
          f"{r['disc_try']:6.2f}{r['disc_hit']:7.2f}{r['disc_handsz']:8.2f}")

for f in (sys.argv[1:] or ['standard','pauper','brawl']): go(f)
