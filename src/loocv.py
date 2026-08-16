# -*- coding: utf-8 -*-
"""Validacion cruzada dejando uno fuera.

El objetivo basado en correlacion ajusta k sobre los mismos puntos con los que se
evalua: con 4-6 mazos eso es optimista. Aqui, para cada mazo, se ajusta la escala con
los OTROS y se predice ese. Es el numero honesto: cuanto se equivocaria el motor con
un mazo que no vio.

Referencia obligatoria: el modelo TONTO (predecir siempre la media real). Si el motor
no le gana a eso, no aporta informacion.
"""
import sys, math, statistics, json; sys.path.insert(0,'src'); sys.path.insert(0,'data')
from calibrate import rr
from real_wr import REAL_FIELD

def loo(pares):
    """pares: [(motor, real)] -> (rmse del motor calibrado, rmse del modelo tonto)"""
    n=len(pares)
    if n<4: return None
    err=[]; err0=[]
    for i in range(n):
        tr=[p for j,p in enumerate(pares) if j!=i]
        te=pares[i]
        em=[a for a,_ in tr]; rm=[b for _,b in tr]
        mx=statistics.mean(em); my=statistics.mean(rm)
        sx=statistics.pstdev(em); sy=statistics.pstdev(rm)
        k=(sy/sx) if sx>1e-9 else 0.0
        pred = my + k*(te[0]-mx)
        err.append(pred-te[1])
        err0.append(my-te[1])          # modelo tonto: la media de los demas
    return (math.sqrt(sum(e*e for e in err)/n), math.sqrt(sum(e*e for e in err0)/n))

if __name__=='__main__':
    ng=int(sys.argv[1]) if len(sys.argv)>1 else 2500
    print(f"{'formato':<12}{'motor calibrado':>17}{'modelo tonto':>15}{'gana el motor?':>17}")
    tot=[]
    for f in ['standard','pauper']:
        names,ws,M=rr(f,ngames=ng,life=20)
        idx={n:i for i,n in enumerate(names)}; t=sum(ws)
        field=[sum(M[i][j]*ws[j] for j in range(len(names)))/t for i in range(len(names))]
        real=REAL_FIELD[f]
        pares=[(field[idx[n]], real[n]) for n in real if n in idx]
        r=loo(pares)
        if not r: print(f"{f:<12}   muestra insuficiente"); continue
        a,b=r
        veredicto = f"SI  {(b-a)*100:+.2f}" if a<b else f"NO  {(b-a)*100:+.2f}"
        print(f"{f:<12}{a*100:>16.2f}%{b*100:>14.2f}%{veredicto:>17}")
        tot.append((f,a,b))
    if tot:
        A=math.sqrt(sum(a*a for _,a,_ in tot)/len(tot)); B=math.sqrt(sum(b*b for _,_,b in tot)/len(tot))
        print(f"\n{'GLOBAL':<12}{A*100:>16.2f}%{B*100:>14.2f}%")
        print(("El motor aporta informacion: baja el error un %.0f%% sobre no saber nada." % (100*(B-A)/B))
              if A<B else "AVISO: el motor NO le gana a predecir la media. No aporta informacion.")
