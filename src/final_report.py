"""Genera las listas finales validadas + diagnostico + ruta de compra."""
import sys, json, math; sys.path.insert(0,'src'); sys.path.insert(0,'data')
from driver import build, run, lookup
from search import build_pool_index, load_util, greedy_counts, make_deck, objective
from meta_decks import DECKS
from collections import Counter

def ci95(p,n): return 1.96*math.sqrt(max(p*(1-p),1e-9)/n)

def price(c):
    p=(c.get('prices') or {})
    for k in ('usd','usd_foil'):
        if p.get(k):
            try: return float(p[k])
            except: pass
    return 0.0

def deck_table(counts_by_name):
    rows=[]
    for name,n in counts_by_name.items():
        c=lookup(name)
        mc=c.get('mana_cost') or ''
        if '//' in mc: mc=mc.split('//')[0].strip()
        if not mc and c.get('card_faces'): mc=c['card_faces'][0].get('mana_cost') or ''
        tl=(c.get('type_line') or '').split('//')[0]
        pt=''
        if c.get('power') is not None: pt=f"{c.get('power')}/{c.get('toughness')}"
        elif c.get('card_faces') and c['card_faces'][0].get('power') is not None:
            f=c['card_faces'][0]; pt=f"{f.get('power')}/{f.get('toughness')}"
        rows.append((int(c.get('cmc') or 0), name, n, mc, tl.split('—')[0].strip(), pt))
    rows.sort(key=lambda r:(r[0], -r[2], r[1]))
    return rows

def curve_of(counts_by_name):
    cv=Counter()
    for name,n in counts_by_name.items():
        c=lookup(name); cv[int(c.get('cmc') or 0)]+=n
    return cv

def validate_deck(fmt, colors, nland, counts_by_name, life=20, ngames=3000):
    R,opps=build(fmt); info=build_pool_index(fmt,R); util=load_util(R)
    n2i={info[i]['name']:i for i in info}
    counts={n2i[n]:c for n,c in counts_by_name.items() if n in n2i}
    deck=make_deck(fmt,R,info,counts,colors,nland,util)
    seedy=greedy_counts(info,colors,60-nland,fmt)
    dseed=make_deck(fmt,R,info,seedy,colors,nland,util)
    res={}
    for s in (700001, 800011, 900007):
        r=run(R,opps,[deck,dseed],ngames=ngames,life=life,seed=s)
        res[s]=(r[0],r[1])
    # por emparejamiento
    mm=[]
    for dn,w,ids in opps:
        r=run(R,[(dn,1000,ids)],[deck],ngames=2500,life=life,seed=555001)[0]
        mm.append((dn,w,r['wr']))
    lands=[R.meta[i] for i in deck[len([x for x in deck if True])-nland:]] if False else None
    return res, mm, R, info, util, counts, deck
