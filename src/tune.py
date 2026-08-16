"""Ajuste coordenada-a-coordenada de los umbrales de la IA contra la calibracion."""
import sys, os, json, random; sys.path.insert(0,'src')
for k in ['DISABLE_EFF','GANG_ON','GANG_BASE']: os.environ.pop(k,None)
from calibrate import rr, report

PARAMS = {
 'TH_TRADE':    [4, 7, 10, 14, 18],
 'TH_PERFECT':  [16, 20, 24, 30],
 'TH_WALL':     [2, 5, 7, 11],
 'TH_BADBLOCK': [-22, -18, -14, -10],
 'RESERVE_MAX': [1, 2, 3],
 'SWEEP_MIN':   [2, 3, 4],
 'PEN_NOTARGET2':[20, 30, 40],
}
CUR = {'TH_TRADE':10,'TH_PERFECT':24,'TH_WALL':7,'TH_BADBLOCK':-14,
       'RESERVE_MAX':3,'SWEEP_MIN':2,'PEN_NOTARGET2':30}

def score(ng=600):
    for k,v in CUR.items(): os.environ[k]=str(v)
    tot=0
    for f,life in [('standard',20),('pauper',20),('brawl',25)]:
        n,w,M=rr(f,ngames=ng,life=life)
        r,sp,fld=report(f,n,w,M,quiet=True); tot+=r
    return tot/3

import io, contextlib
def quiet_score(ng=600):
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf): return score(ng)

base=quiet_score()
print(f"base: {base*100:.3f}\n")
for ronda in range(2):
    print(f"--- ronda {ronda+1} ---")
    for k, vals in PARAMS.items():
        best=(base, CUR[k])
        for v in vals:
            if v==CUR[k]: continue
            old=CUR[k]; CUR[k]=v
            sc=quiet_score()
            if sc<best[0]-0.0005: best=(sc,v)
            CUR[k]=old
        if best[1]!=CUR[k]:
            print(f"  {k}: {CUR[k]} -> {best[1]}   ({base*100:.3f} -> {best[0]*100:.3f})")
            CUR[k]=best[1]; base=best[0]
        else:
            print(f"  {k}: se queda en {CUR[k]}")
print(f"\nfinal: {base*100:.3f}")
print("parametros:", json.dumps(CUR))
json.dump(CUR, open('out/tuned.json','w'))
