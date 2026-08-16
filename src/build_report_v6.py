# -*- coding: utf-8 -*-
"""Reconstruye las tres listas nuevas, las verifica y arma out/report_v6.json"""
import sys, json; sys.path.insert(0,'src'); sys.path.insert(0,'data')
from driver import build, run, lookup
from brawl import build_brawl, run_brawl
from search import (build_pool_index, load_util, greedy_counts, make_deck, objective)
from optimize import lands_for
from check_legal import check
from escala import aplicar
from extract import convert
NG=2500
esc=json.load(open('data/escala.json'))
R6=json.load(open('out/results.json'))
BR=json.load(open('out/brawl_result.json'))
TIT={'standard':'Standard','pauper':'Pauper','brawl':'Standard Brawl'}
OUT={}

def ficha(nm, n):
    c=lookup(nm); e=convert(c)
    mc=(c.get('mana_cost') or '')
    if '//' in mc: mc=mc.split('//')[0].strip()
    tl=(c.get('type_line') or '')
    if 'Creature' in tl: pt=f"{c.get('power','?')}/{c.get('toughness','?')}"
    else: pt=tl.split('—')[0].strip()[:14]
    return dict(cmc=e['cmc'], name=nm, n=n, mc=mc or '{0}', pt=pt)

for fmt in ('standard','pauper'):
    d=R6[fmt]; cols=list(d['colors']); nl=d['nland']
    R,opps=build(fmt); info=build_pool_index(fmt,R); util=load_util(R)
    idx={R.meta[i]:i for i in R.meta}
    counts={idx[nm]:n for nm,n in d['counts'].items() if nm in idx}
    for nm,n in d['counts'].items():
        if nm not in idx: counts[R.add_by_name(nm)]=n
    deck=make_deck(fmt,R,info,counts,cols,nl,util)
    r=run(R,opps,[deck],ngames=NG,life=20,seed=31337)[0]
    ns=sum(d['counts'].values())
    g=greedy_counts(info,cols,ns,fmt)
    rg=run(R,opps,[make_deck(fmt,R,info,g,cols,nl,util)],ngames=NG,life=20,seed=31337)[0]
    # lista de tierras
    spec=[(k, min(q,4)) for k,(q,cs,e) in util.items() if set(cs)<=set(cols)]
    lands=lands_for(fmt,R,cols,nl,spec)
    from collections import Counter
    la=Counter(R.meta[i] for i in lands)
    cards=[]
    for nm,n in d['counts'].items(): cards += [nm]*n
    cards += list(la.elements())
    errs,_=check(cards, fmt, deck_size=60)
    mm=[]
    for dn,w,ids in opps:
        rr=run(R,[(dn,1000,ids)],[deck],ngames=1200,life=20,seed=999)[0]
        mm.append([dn, w/10.0, rr['wr']*100])
    cal=aplicar(esc,fmt,r['wr'])
    OUT[fmt]=dict(t=TIT[fmt], col=''.join(cols),
                  sp=sorted([ficha(nm,n) for nm,n in d['counts'].items()], key=lambda x:(x['cmc'],-x['n'],x['name'])),
                  la=dict(la), nl=nl, ns=ns,
                  gain=f"{(objective(r)-objective(rg))*100:+.2f}".replace('.',','),
                  obj=objective(r)*100, wr=r['wr']*100,
                  cal=(cal*100 if cal else None), legal=(not errs), errs=errs[:3],
                  mm=sorted(mm, key=lambda x:-x[1]))
    print(f"{fmt}: {''.join(cols)} {ns}+{nl}={ns+nl} obj {objective(r)*100:.2f} wr {r['wr']*100:.1f}% "
          f"gain {OUT[fmt]['gain']} legal={not errs}", flush=True)

# brawl
R,opps=build_brawl(); cmd=R.add_by_name(BR['commander'])
ids=[R.add_by_name(n) for n in BR['spells']]+[R.add_by_name(n) for n in BR['lands']]
r=run_brawl(R,opps,[(cmd,ids)],ngames=NG,life=25,seed=31337)[0]
errs,_=check(BR['spells']+BR['lands'],'standardbrawl',commander=BR['commander'],deck_size=60,singleton=True)
from collections import Counter
la=Counter(BR['lands'])
mm=[]
for o in opps:
    rr=run_brawl(R,[(o[0],1000,o[2],o[3])],[(cmd,ids)],ngames=1200,life=25,seed=999)[0]
    mm.append([o[0], o[1]/10.0, rr['wr']*100])
sc=Counter(BR['spells'])
OUT['brawl']=dict(t=TIT['brawl'], col=''.join(BR['ci']) if isinstance(BR['ci'],(list,str)) else str(BR['ci']),
                  cmd=BR['commander'],
                  sp=sorted([ficha(nm,n) for nm,n in sc.items()], key=lambda x:(x['cmc'],x['name'])),
                  la=dict(la), nl=len(BR['lands']), ns=len(BR['spells']),
                  gain='n/d', obj=objective(r)*100, wr=r['wr']*100, cal=None,
                  legal=(not errs), errs=errs[:3], mm=sorted(mm,key=lambda x:-x[1]))
print(f"brawl: {BR['commander']} {len(BR['spells'])}+{len(BR['lands'])} obj {objective(r)*100:.2f} "
      f"wr {r['wr']*100:.1f}% legal={not errs}")
json.dump(OUT, open('out/report_v6.json','w'), ensure_ascii=False, indent=1)
print('escrito out/report_v6.json')
