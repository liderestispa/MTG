"""Barre un parametro contra el objetivo real (cara-a-cara + residuo de campo)."""
import sys, os, subprocess, json; sys.path.insert(0,'src'); sys.path.insert(0,'data')
from calibrate import rr
from calib_real import evaluar, score_global
var=sys.argv[1]; vals=[v for v in sys.argv[2].split(',')]
ng=int(sys.argv[3]) if len(sys.argv)>3 else 900
fmts=sys.argv[4].split(',') if len(sys.argv)>4 else ['standard','pauper','brawl']
base=dict(os.environ)
print(f"{var:>14} | objetivo | h2h std | resid std | resid pau | resid brawl")
best=(None,9e9)
for v in vals:
    os.environ[var]=str(v)
    res=[]
    for f in fmts:
        names,ws,M = rr(f, ngames=ng, life=25 if f=='brawl' else 20)
        res.append(evaluar(f,names,ws,M,quiet=True))
    g=score_global(res)
    d={o['fmt']:o for o in res}
    def gv(f,k): return d[f].get(k,float('nan'))*100 if f in d else float('nan')
    print(f"{v:>14} | {g*100:8.2f} | {gv('standard','h2h_rmse'):7.2f} | {gv('standard','campo_resid'):9.2f} | "
          f"{gv('pauper','campo_resid'):9.2f} | {gv('brawl','campo_resid'):11.2f}", flush=True)
    if g<best[1]: best=(v,g)
os.environ.pop(var,None)
print(f"\nmejor {var}={best[0]}  ({best[1]*100:.2f})")
