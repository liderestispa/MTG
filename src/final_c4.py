# -*- coding: utf-8 -*-
"""Medicion final de la campana 4: todo en un JSON."""
import sys, json, math, statistics; sys.path.insert(0,'src'); sys.path.insert(0,'data')
from calibrate import rr
from calib_real import evaluar
from obj_real import objetivo
from escala import ajustar
from real_wr import REAL_FIELD, REAL_H2H, FUENTES
NG=int(sys.argv[1]) if len(sys.argv)>1 else 2000
res={}; med={}
for f in ['standard','pauper','brawl']:
    names,ws,M=rr(f,ngames=NG,life=25 if f=='brawl' else 20)
    o=evaluar(f,names,ws,M)
    med[f]={'names':names,'field':o['field']}
    res[f]={k:v for k,v in o.items() if k!='names'}
    res[f]['names']=names; res[f]['matrix']=M; res[f]['weights']=ws; res[f]['ngames']=NG
    # dispersion vs realidad
    real=REAL_FIELD.get(f,{}); idx={n:i for i,n in enumerate(names)}
    pares=[(o['field'][idx[n]],real[n]) for n in real if n in idx]
    if len(pares)>2:
        em=[a for a,_ in pares]; rm=[b for _,b in pares]
        sx=statistics.pstdev(em); sy=statistics.pstdev(rm)
        mx=statistics.mean(em); my=statistics.mean(rm)
        cov=sum((a-mx)*(b-my) for a,b in pares)/len(pares)
        res[f]['disp']=sx/sy if sy else None
        res[f]['r']=cov/(sx*sy) if sx*sy else None
esc=ajustar(med)
obj=math.sqrt(sum(w*res[f]['campo_resid']**2 for f,w in (('pauper',3.0),('standard',1.5),('brawl',1.0)))/5.5)
d={'fmts':res,'escala':esc,'objetivo':obj,'fuentes':FUENTES,'ngames':NG}
json.dump(d, open('out/final_c4.json','w'), ensure_ascii=False, indent=1, default=str)
print(f"\nOBJETIVO FINAL (residuo de campo ponderado): {d['objetivo']*100:.3f} pts")
for f,e in esc.items():
    print(f"  {f:<10} k={e['k'] if e['k'] is not None else 'n/d'}  r={e['r']}  {e['confianza']}")
