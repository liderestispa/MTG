# -*- coding: utf-8 -*-
"""Objetivo unico contra datos reales. Se minimiza esto."""
import sys, math, statistics; sys.path.insert(0,'src'); sys.path.insert(0,'data')
from calibrate import rr
from real_wr import REAL_FIELD, REAL_H2H
from salud import exige_binarios_al_dia

_REVISADO = False

def medir(ng=900, fmts=('standard','pauper','brawl'), seed=1234567):
    # Un binario viejo no da error: da numeros. bin_brawl estuvo desincronizado medio dia
    # y congelo el residuo de Brawl en 2,06, escondiendo la mejora mas grande del
    # proyecto y produciendo media pagina de conclusiones falsas. Se revisa UNA vez por
    # proceso: el laboratorio llama a medir() cientos de veces.
    global _REVISADO
    if not _REVISADO:
        exige_binarios_al_dia(); _REVISADO = True
    d={}
    for f in fmts:
        names,ws,M=rr(f,ngames=ng,life=25 if f=='brawl' else 20,seed=seed)
        idx={n:i for i,n in enumerate(names)}; tot=sum(ws)
        field=[sum(M[i][j]*ws[j] for j in range(len(names)))/tot for i in range(len(names))]
        real=REAL_FIELD.get(f,{})
        pares=[(field[idx[n]], real[n]) for n in real if n in idx]
        o={'pares':pares,'field':field,'names':names}
        if pares:
            errs=[a-b for a,b in pares]
            off=statistics.mean(errs)
            o['rmse']=math.sqrt(sum(e*e for e in errs)/len(errs))
            o['resid']=math.sqrt(sum((e-off)**2 for e in errs)/len(errs))
            o['off']=off
            if len(pares)>2:
                em=[a for a,_ in pares]; rm=[b for _,b in pares]
                sx=statistics.pstdev(em); sy=statistics.pstdev(rm)
                mx=statistics.mean(em); my=statistics.mean(rm)
                cov=sum((a-mx)*(b-my) for a,b in pares)/len(pares)
                o['r']=cov/(sx*sy) if sx*sy>0 else 0.0
                o['disp']=sx/sy if sy>0 else float('inf')
                o['sd_real']=sy; o['sd_motor']=sx
                o['resid_cal']=sy*math.sqrt(max(0.0,2*(1-o['r'])))
        h=[(M[idx[a]][idx[b]],r) for a,b,r,_ in REAL_H2H.get(f,[]) if a in idx and b in idx]
        if h: o['h2h']=math.sqrt(sum((a-b)**2 for a,b in h)/len(h))
        d[f]=o
    return d

def objetivo(d):
    """Error DESPUES de aplicar la compresion de escala.

    CORRECCION METODOLOGICA (campana 4b): el objetivo anterior era el residuo crudo,
    que penaliza la sobredispersion. Pero la sobredispersion ya la corrige la capa de
    escala (escala.py), asi que penalizarla aqui castiga cambios que mejoran el motor.

    Con igualacion de varianza (k = sd_real/sd_motor) el error calibrado sale en cerrado:

        RMSE_calibrado = sd_real * sqrt(2*(1-r))

    O sea: minimizar el error calibrado es EXACTAMENTE maximizar la correlacion de orden.
    Que es lo unico que se le puede pedir al motor: que ordene bien.
    Donde no hay suficientes mazos para calcular r (Brawl, 2 datos), se usa el residuo crudo.
    """
    W={'pauper':3.0,'standard':1.5,'brawl':1.0}
    num=0.0; den=0.0
    for f,o in d.items():
        w=W.get(f,1.0)
        if 'r' in o and o.get('sd_real') is not None:
            e = o['sd_real']*math.sqrt(max(0.0, 2*(1-o['r'])))
        elif 'resid' in o:
            e = o['resid']
        else:
            continue
        num += w*e*e; den += w
    return math.sqrt(num/den) if den else None

def linea(d):
    p=[]
    for f in ('standard','pauper','brawl'):
        o=d.get(f)
        if not o or 'resid' not in o: continue
        if 'r' in o:
            p.append(f"{f[:3]} cal {o['resid_cal']*100:4.2f} (r={o['r']:+.2f} x{o['disp']:.1f})")
        else:
            p.append(f"{f[:3]} resid {o['resid']*100:5.2f}")
    return " | ".join(p)

if __name__=='__main__':
    d=medir(int(sys.argv[1]) if len(sys.argv)>1 else 900)
    print(linea(d)); print(f"OBJETIVO {objetivo(d)*100:.3f}")
