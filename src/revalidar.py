# -*- coding: utf-8 -*-
"""Cada mazo v4 contra su semilla codiciosa, con el motor actual."""
import sys, json; sys.path.insert(0,'src'); sys.path.insert(0,'data')
from driver import build, run
from brawl import build_brawl, run_brawl
from search import objective, build_pool_index, greedy_counts, make_deck, load_util
from optimize import pool_for
NG=int(sys.argv[1]) if len(sys.argv)>1 else 2500
for fmt,arch in [('standard','out/standard_v4.json'),('pauper','out/pauper_v4.json')]:
    d=json.load(open(arch))
    R,opps=build(fmt)
    ids=[R.add_by_name(n) for n in d['names']]      # 'names' ya es el mazo completo (60)
    r=run(R,opps,[ids],ngames=NG,life=20,seed=31337)[0]
    info=build_pool_index(fmt,R); util=load_util(R)
    cols=list(d['colors']); cs=''.join(cols)
    nl=d['nland']; ns=60-nl
    g=greedy_counts(info,list(cols),ns,fmt)
    gd=make_deck(fmt,R,info,g,list(cols),nl,util)
    rg=run(R,opps,[gd],ngames=NG,life=20,seed=31337)[0]
    print(f"{fmt:<10} {cs:<5} mazo {objective(r)*100:6.2f}  semilla {objective(rg)*100:6.2f}  "
          f"delta {(objective(r)-objective(rg))*100:+6.2f}   wr {r['wr']*100:.1f}%")

# --- brawl ---
d=json.load(open('out/brawl_result.json'))
R,opps=build_brawl()
cmd=R.add_by_name(d['commander'])
ids=[R.add_by_name(n) for n in d['spells']]+[R.add_by_name(n) for n in d['lands']]
r=run_brawl(R,opps,[(cmd,ids)],ngames=NG,life=25,seed=31337)[0]
import brawl as BR
info=BR.pool_index() if hasattr(BR,'pool_index') else None
print(f"{'brawl':<10} {d['commander'][:18]:<19} mazo {objective(r)*100:6.2f}  wr {r['wr']*100:.1f}%  "
      f"(semilla: ver out/run_brawl4.out, {d['obj']:.2f} con el motor v4)")
