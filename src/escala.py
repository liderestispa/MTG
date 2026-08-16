# -*- coding: utf-8 -*-
"""Traduce el indice bruto del motor a una estimacion honesta.

El motor esta SOBREDISPERSO: separa a los mazos mucho mas de lo que los separa la
realidad. Eso no invalida el orden (para buscar mazos el orden es lo unico que hace
falta), pero si invalida el numero. Aqui se mide el factor de compresion contra los
winrates publicados y se guarda para reportar.

  calibrado = media_real + k * (bruto - media_motor),   k = sd_real / sd_motor

Se usa igualacion de varianza y no minimos cuadrados: con 4-6 puntos y +-10 pts de
ruido, la pendiente por minimos cuadrados es puro ruido (en Standard sale NEGATIVA).
La igualacion de varianza solo asume que el motor separa de mas, que es lo unico que
el dato sostiene con holgura.
"""
import sys, json, math, statistics; sys.path.insert(0,'src'); sys.path.insert(0,'data')
from real_wr import REAL_FIELD

def ajustar(medida):
    """medida: {fmt: {'names':[...], 'field':[...]}}  ->  {fmt: parametros de escala}"""
    esc={}
    for f,o in medida.items():
        real=REAL_FIELD.get(f,{})
        idx={n:i for i,n in enumerate(o['names'])}
        pares=[(o['field'][idx[n]], real[n]) for n in real if n in idx]
        if len(pares)<2: continue
        em=[a for a,_ in pares]; rm=[b for _,b in pares]
        mx=statistics.mean(em); my=statistics.mean(rm)
        sx=statistics.pstdev(em); sy=statistics.pstdev(rm)
        k = (sy/sx) if sx>1e-9 else 0.0
        r=None
        if len(pares)>2 and sx>1e-9 and sy>1e-9:
            cov=sum((a-mx)*(b-my) for a,b in pares)/len(pares); r=cov/(sx*sy)
        # cuanta confianza merece el ORDEN que da el motor en este formato
        if r is None:            conf='solo desplazamiento (2 datos)'
        elif r >= 0.6:           conf='el orden es utilizable'
        elif r >= 0.3:           conf='orden debil'
        else:                    conf='el orden NO esta validado'
        # GUARDA: con pocos datos, o con datos que solo cubren la parte alta de la
        # tabla, la recta se ajusta a una muestra sesgada y devolveria 90% para todo.
        # En ese caso NO se calibra el nivel: se declara y punto.
        usable = (len(pares) >= 4) and (max(rm)-min(rm) >= 0.03) and (min(rm) <= 0.60)
        if not usable:
            conf += ' — muestra no representativa: NO se calibra el nivel'
        esc[f]=dict(k=(k if usable else None), media_motor=mx, media_real=my,
                    sd_motor=sx, sd_real=sy, r=r, n=len(pares),
                    rango_real=[min(rm),max(rm)], usable=usable, confianza=conf)
    return esc

def aplicar(esc, fmt, bruto):
    e=esc.get(fmt)
    if not e or not e.get('usable') or e.get('k') is None: return None
    v = e['media_real'] + e['k']*(bruto - e['media_motor'])
    return min(0.95, max(0.05, v))

if __name__=='__main__':
    from obj_real import medir
    ng=int(sys.argv[1]) if len(sys.argv)>1 else 1500
    d=medir(ng)
    esc=ajustar({f:{'names':o['names'],'field':o['field']} for f,o in d.items()})
    json.dump(esc, open('data/escala.json','w'), ensure_ascii=False, indent=1)
    print(f"{'formato':<12}{'k':>7}{'media motor':>13}{'media real':>12}{'r':>7}{'n':>4}  confianza")
    for f,e in esc.items():
        rr = f"{e['r']:+.2f}" if e['r'] is not None else '  --'
        kk = f"{e['k']:.3f}" if e['k'] is not None else 'n/d'
        print(f"{f:<12}{kk:>7}{e['media_motor']*100:>12.1f}%{e['media_real']*100:>11.1f}%{rr:>7}{e['n']:>4}  {e['confianza']}")
    print("\nejemplo: que significa un indice bruto del motor")
    print(f"{'bruto':>8}" + "".join(f"{f[:8]:>12}" for f in esc))
    for b in (0.60,0.70,0.80,0.90):
        cel=[]
        for f in esc:
            v=aplicar(esc,f,b)
            cel.append(f"{v*100:>11.1f}%" if v is not None else f"{'n/d':>12}")
        print(f"{b*100:>7.0f}%" + "".join(cel))
