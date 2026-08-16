"""Banco de calibracion: round-robin entre mazos del meta.
Si el motor esta afinado, todos deben caer cerca del 50% contra el campo."""
import sys, json, math, statistics; sys.path.insert(0,'src')
from driver import build, run
from brawl import build_brawl, run_brawl

def rr(fmt, ngames=1200, life=20, seed=1234567):
    if fmt=='brawl':
        R,opps=build_brawl()
        names=[o[0] for o in opps]; ws=[o[1] for o in opps]
        M=[[None]*len(opps) for _ in opps]
        for i,(dn,w,cmd,ids) in enumerate(opps):
            for j,(dn2,w2,cmd2,ids2) in enumerate(opps):
                if i==j: M[i][j]=0.5; continue
                r=run_brawl(R,[(dn2,1000,cmd2,ids2)],[(cmd,ids)],ngames=ngames,life=life,seed=seed)[0]
                M[i][j]=r['wr']
    else:
        R,opps=build(fmt)
        names=[o[0] for o in opps]; ws=[o[1] for o in opps]
        M=[[None]*len(opps) for _ in opps]
        for i,(dn,w,ids) in enumerate(opps):
            for j,(dn2,w2,ids2) in enumerate(opps):
                if i==j: M[i][j]=0.5; continue
                r=run(R,[(dn2,1000,ids2)],[ids],ngames=ngames,life=life,seed=seed)[0]
                M[i][j]=r['wr']
    return names, ws, M

# winrates REALES reportados donde existen (para no exigir 50% donde el meta no es plano)
REAL_WR = {
  'brawl': {'Elspeth Storm Slayer':0.77, 'Ketramose the New Dawn':0.73},
}

def report_real(fmt, names, ws, M):
    """Compara contra winrates reales publicados en vez de contra el 50%."""
    real = REAL_WR.get(fmt, {})
    if not real: return None
    tot=sum(ws); rows=[]
    for i,n in enumerate(names):
        f=sum(M[i][j]*ws[j] for j in range(len(names)))/tot
        if n in real: rows.append((n, f, real[n]))
    if not rows: return None
    errs=[f-r for _,f,r in rows]
    # el orden importa mas que el nivel: un desplazamiento constante es esperable
    import statistics
    off = statistics.mean(errs)
    resid = [e-off for e in errs]
    return dict(offset=off, resid_max=max(abs(x) for x in resid), rows=rows)

def report(fmt, names, ws, M, quiet=False):
    tot=sum(ws)
    field=[]
    for i in range(len(names)):
        s=sum(M[i][j]*ws[j] for j in range(len(names)))/tot
        field.append(s)
    dev=[abs(f-0.5) for f in field]
    rmse=math.sqrt(sum(d*d for d in dev)/len(dev))
    if not quiet:
        w=max(len(n) for n in names)+1
        print(f"\n{'':<{w}}" + "".join(f"{n[:8]:>9}" for n in names) + f"{'CAMPO':>9}")
        for i,n in enumerate(names):
            print(f"{n:<{w}}" + "".join(f"{M[i][j]*100:8.1f}%" for j in range(len(names))) +
                  f"{field[i]*100:8.1f}%")
    print(f"\n  RMSE respecto a 50%: {rmse*100:.2f} pts   |   dispersion: {(max(field)-min(field))*100:.1f} pts"
          f"   |   fuera de 40-60%: {sum(1 for f in field if f<0.4 or f>0.6)}/{len(field)}")
    return rmse, max(field)-min(field), field

if __name__=='__main__':
    fmts = sys.argv[1:] or ['standard','pauper','brawl']
    res={}
    for f in fmts:
        life = 25 if f=='brawl' else 20
        print(f"\n{'='*70}\n{f.upper()}\n{'='*70}")
        names, ws, M = rr(f, ngames=1000, life=life)
        rmse, spread, field = report(f, names, ws, M)
        res[f]=dict(names=names, field=field, rmse=rmse, spread=spread)
    json.dump(res, open('out/calib.json','w'), ensure_ascii=False, indent=1)
    print(f"\n\nGLOBAL: RMSE medio {sum(r['rmse'] for r in res.values())/len(res)*100:.2f} pts")
