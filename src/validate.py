"""Revalida los ganadores con semillas NUEVAS e independientes y muestra grande."""
import sys, json; sys.path.insert(0,'src')
from driver import build, run
from search import build_pool_index, load_util, greedy_counts, make_deck, objective

def ci95(p, n):
    import math
    return 1.96*math.sqrt(max(p*(1-p),1e-9)/n)

def validate(fmt, colors, nland, counts_by_name, ngames=3000, seeds=(80021,90031,100003)):
    life = 20
    R,opps = build(fmt); info=build_pool_index(fmt,R); util=load_util(R)
    name2i = {info[i]['name']: i for i in info}
    counts = {name2i[n]:c for n,c in counts_by_name.items() if n in name2i}
    deck = make_deck(fmt,R,info,counts,colors,nland,util)
    base = greedy_counts(info,colors,60-nland,fmt)
    dbase = make_deck(fmt,R,info,base,colors,nland,util)
    out=[]
    for s in seeds:
        r = run(R,opps,[deck,dbase],ngames=ngames,life=life,seed=s)
        out.append((r[0],r[1]))
    return out, R, opps, info, util, deck, counts

def per_matchup(fmt, R, opps, deck, ngames=2500, life=20, seed=555001):
    res=[]
    for dn,w,ids in opps:
        r=run(R,opps and [(dn,1000,ids)],[deck],ngames=ngames,life=life,seed=seed)[0]
        res.append((dn,w,r))
    return res
