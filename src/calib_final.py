"""Calibracion final v4: guarda matriz completa + comparacion contra winrates reales."""
import sys, json, math; sys.path.insert(0,'src')
from calibrate import rr, report, report_real

NG = int(sys.argv[1]) if len(sys.argv)>1 else 1800
res={}
for f in ['standard','pauper','brawl']:
    life = 25 if f=='brawl' else 20
    print(f"\n{'='*70}\n{f.upper()}  ({NG} juegos/enfrentamiento)\n{'='*70}", flush=True)
    names, ws, M = rr(f, ngames=NG, life=life)
    rmse, spread, field = report(f, names, ws, M)
    rr_real = report_real(f, names, ws, M)
    if rr_real:
        print(f"  vs winrates REALES: desplazamiento {rr_real['offset']*100:+.1f} pts | residuo max {rr_real['resid_max']*100:.1f} pts")
        for n,fv,rv in rr_real['rows']:
            print(f"     {n:<30} motor {fv*100:5.1f}%   real {rv*100:5.1f}%")
    res[f]=dict(names=names, weights=ws, matrix=M, field=field, rmse=rmse, spread=spread,
                outside=sum(1 for x in field if x<0.4 or x>0.6), real=rr_real, ngames=NG)
    json.dump(res, open('out/calib_v4.json','w'), ensure_ascii=False, indent=1)
g = sum(r['rmse'] for r in res.values())/len(res)
res['global']=g
json.dump(res, open('out/calib_v4.json','w'), ensure_ascii=False, indent=1)
print(f"\n\nGLOBAL: RMSE medio {g*100:.2f} pts")
