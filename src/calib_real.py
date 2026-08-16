# -*- coding: utf-8 -*-
"""Calibracion contra datos REALES en vez de contra el 50% supuesto.

Dos errores distintos, y el segundo es el que importa:
  - error de CAMPO: cada mazo contra el campo ponderado vs su winrate publicado.
    Un desplazamiento comun no es error del motor (el ladder incluye mazos malos).
  - error CABEZA-A-CABEZA: cada enfrentamiento vs el publicado. Aqui no hay
    desplazamiento que valga: si el motor dice 70% y la realidad dice 53%, se equivoca.
"""
import sys, json, math, statistics; sys.path.insert(0,'src'); sys.path.insert(0,'data')
from calibrate import rr
from real_wr import REAL_FIELD, REAL_H2H

def evaluar(fmt, names, ws, M, quiet=False):
    tot=sum(ws)
    field=[sum(M[i][j]*ws[j] for j in range(len(names)))/tot for i in range(len(names))]
    out={'fmt':fmt}
    # --- campo ---
    real=REAL_FIELD.get(fmt,{})
    rows=[(n, field[i], real[n]) for i,n in enumerate(names) if n in real]
    if rows:
        errs=[f-r for _,f,r in rows]
        off=statistics.mean(errs)
        resid=[e-off for e in errs]
        out['campo_off']=off
        out['campo_resid']=math.sqrt(sum(x*x for x in resid)/len(resid))
        out['campo_rows']=rows
    # --- cabeza a cabeza ---
    h2h=REAL_H2H.get(fmt,[])
    idx={n:i for i,n in enumerate(names)}
    hr=[]
    for a,b,r,ns in h2h:
        if a not in idx or b not in idx: continue
        hr.append((a,b,M[idx[a]][idx[b]],r,ns))
    if hr:
        e=[m-r for _,_,m,r,_ in hr]
        out['h2h_rmse']=math.sqrt(sum(x*x for x in e)/len(e))
        out['h2h_bias']=statistics.mean(e)
        out['h2h_max']=max(abs(x) for x in e)
        out['h2h_rows']=hr
    # --- clasico: distancia al 50% ---
    dev=[abs(f-0.5) for f in field]
    out['rmse50']=math.sqrt(sum(d*d for d in dev)/len(dev))
    out['field']=field; out['names']=names
    if not quiet: imprimir(out)
    return out

def imprimir(o):
    print(f"\n--- {o['fmt'].upper()} ---")
    if 'campo_rows' in o:
        print(f"  CAMPO   desplazamiento {o['campo_off']*100:+5.1f} pts | residuo {o['campo_resid']*100:5.2f} pts")
        for n,f,r in o['campo_rows']:
            print(f"     {n:<24} motor {f*100:5.1f}%  real {r*100:5.1f}%  err {(f-r)*100:+6.1f}")
    if 'h2h_rows' in o:
        print(f"  CARA A CARA  RMSE {o['h2h_rmse']*100:5.2f} pts | sesgo {o['h2h_bias']*100:+5.1f} | peor {o['h2h_max']*100:5.1f}")
        for a,b,m,r,ns in o['h2h_rows']:
            print(f"     {a[:20]:<21} vs {b[:20]:<21} motor {m*100:5.1f}%  real {r*100:5.1f}% (n={ns})  err {(m-r)*100:+6.1f}")
    print(f"  (clasico: RMSE vs 50% = {o['rmse50']*100:.2f})")

def score_global(res):
    """Objetivo unico a minimizar. El cara-a-cara pesa doble: no tiene confusion de campo."""
    partes=[]
    for o in res:
        if 'h2h_rmse' in o: partes.append(('h2h', o['h2h_rmse'], 2.0))
        if 'campo_resid' in o: partes.append(('campo', o['campo_resid'], 1.0))
    if not partes: return None
    num=sum(w*v*v for _,v,w in partes); den=sum(w for _,_,w in partes)
    return math.sqrt(num/den)

if __name__=='__main__':
    ng=int(sys.argv[1]) if len(sys.argv)>1 else 1200
    fmts=sys.argv[2:] or ['standard','pauper','brawl']
    res=[]
    for f in fmts:
        life=25 if f=='brawl' else 20
        names,ws,M = rr(f, ngames=ng, life=life)
        res.append(evaluar(f,names,ws,M))
    g=score_global(res)
    print(f"\n{'='*70}\nOBJETIVO GLOBAL (cara-a-cara x2 + residuo de campo): {g*100:.2f} pts\n{'='*70}")
    json.dump({'objetivo':g,'fmts':[{k:v for k,v in o.items() if k!='names'} for o in res]},
              open('out/calib_real.json','w'), ensure_ascii=False, indent=1, default=str)
