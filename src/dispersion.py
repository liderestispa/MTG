# -*- coding: utf-8 -*-
"""Cuanto MAS disperso es el motor que la realidad, y si al menos ORDENA bien."""
import sys, math, statistics; sys.path.insert(0,'src'); sys.path.insert(0,'data')
from calibrate import rr
from real_wr import REAL_FIELD, REAL_H2H
ng=int(sys.argv[1]) if len(sys.argv)>1 else 1500
out={}
for f in ['standard','pauper']:
    names,ws,M=rr(f,ngames=ng,life=20)
    idx={n:i for i,n in enumerate(names)}
    tot=sum(ws)
    field=[sum(M[i][j]*ws[j] for j in range(len(names)))/tot for i in range(len(names))]
    # --- campo ---
    real=REAL_FIELD[f]
    pares=[(field[idx[n]], real[n]) for n in real if n in idx]
    em=[p[0] for p in pares]; rm=[p[1] for p in pares]
    print(f"\n=== {f.upper()} — CAMPO ({len(pares)} mazos con dato real) ===")
    print(f"  rango motor  {min(em)*100:5.1f}% .. {max(em)*100:5.1f}%   (amplitud {(max(em)-min(em))*100:5.1f} pts)")
    print(f"  rango real   {min(rm)*100:5.1f}% .. {max(rm)*100:5.1f}%   (amplitud {(max(rm)-min(rm))*100:5.1f} pts)")
    if len(pares)>2:
        sx=statistics.pstdev(em); sy=statistics.pstdev(rm)
        mx=statistics.mean(em); my=statistics.mean(rm)
        cov=sum((a-mx)*(b-my) for a,b in pares)/len(pares)
        r = cov/(sx*sy) if sx*sy>0 else float('nan')
        print(f"  sobredispersion  x{sx/sy:.1f}    correlacion de orden r={r:+.2f}")
    # --- cara a cara ---
    h2h=[(a,b,M[idx[a]][idx[b]],r) for a,b,r,_ in REAL_H2H[f] if a in idx and b in idx]
    if h2h:
        em=[x[2] for x in h2h]; rm=[x[3] for x in h2h]
        sx=statistics.pstdev(em); sy=statistics.pstdev(rm)
        mx=statistics.mean(em); my=statistics.mean(rm)
        cov=sum((a-mx)*(b-my) for a,b in zip(em,rm))/len(em)
        r=cov/(sx*sy) if sx*sy>0 else float('nan')
        print(f"  --- CARA A CARA ({len(h2h)} enfrentamientos) ---")
        print(f"  rango motor  {min(em)*100:5.1f}% .. {max(em)*100:5.1f}%   (amplitud {(max(em)-min(em))*100:5.1f} pts)")
        print(f"  rango real   {min(rm)*100:5.1f}% .. {max(rm)*100:5.1f}%   (amplitud {(max(rm)-min(rm))*100:5.1f} pts)")
        print(f"  sobredispersion  x{sx/sy:.1f}    correlacion r={r:+.2f}")
        # factor de compresion optimo: minimiza |0.5+k(x-0.5) - y|
        num=sum((a-0.5)*(b-0.5) for a,b in zip(em,rm)); den=sum((a-0.5)**2 for a in em)
        k=num/den if den else float('nan')
        rmse0=math.sqrt(sum((a-b)**2 for a,b in zip(em,rm))/len(em))
        rmsek=math.sqrt(sum((0.5+k*(a-0.5)-b)**2 for a,b in zip(em,rm))/len(em))
        print(f"  factor de compresion optimo k={k:+.3f}   RMSE {rmse0*100:.2f} -> {rmsek*100:.2f} pts")
