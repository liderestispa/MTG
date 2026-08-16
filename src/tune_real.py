# -*- coding: utf-8 -*-
"""Descenso coordenada a coordenada contra los winrates REALES publicados."""
import sys, os, json; sys.path.insert(0,'src')
from obj_real import medir, objetivo, linea

REJILLA = {
 'W_PRESSURE': [0,20,40,70],
 'W_TARGET':   [0,25,50,100],
 'TH_TRADE':   [-4,0,4,10,16],
 'TH_PERFECT': [16,24,32],
 'TH_WALL':    [0,7,14],
 'TH_BADBLOCK':[-30,-22,-14],
 'RESERVE_MAX':[1,2,3,4],
 'SWEEP_MIN':  [2,3,4],
 'PEN_NOTARGET':[15,30,45],
 'WARD_COST':  [1,2,3],
}
NG=int(os.environ.get('NG','900'))
estado={k:None for k in REJILLA}
for k,v in list(estado.items()):
    if k in os.environ: estado[k]=os.environ[k]

def prueba():
    for k,v in estado.items():
        if v is None: os.environ.pop(k,None)
        else: os.environ[k]=str(v)
    d=medir(NG); return objetivo(d), d

base,d0=prueba()
print(f"base {base*100:.3f}   {linea(d0)}", flush=True)
mejor=base
for ronda in range(2):
    cambio=False
    for var,vals in REJILLA.items():
        prev=estado[var]; local=(mejor,prev)
        for v in vals:
            if str(v)==str(prev): continue
            estado[var]=v
            g,d=prueba()
            marca='*' if g<local[0] else ' '
            print(f"  r{ronda+1} {var:<13}={str(v):>5}  {g*100:7.3f} {marca}  {linea(d)}", flush=True)
            if g<local[0]: local=(g,v)
        estado[var]=local[1]
        if local[0]<mejor: mejor=local[0]; cambio=True
        print(f"  -> {var} = {local[1]}   (mejor {mejor*100:.3f})", flush=True)
    if not cambio: break
print(f"\nFINAL {mejor*100:.3f}")
print(json.dumps({k:v for k,v in estado.items() if v is not None}, indent=1))
json.dump({k:v for k,v in estado.items() if v is not None}, open('out/tuned_real.json','w'), indent=1)
