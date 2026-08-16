"""Barrido del universo legal: que cartas comprables mejoran mas el mazo."""
import sys, json, re; sys.path.insert(0,'src'); sys.path.insert(0,'data')
from driver import build, run, lookup
from search import build_pool_index, load_util, make_deck, objective
from extract import convert
from meta_decks import DECKS

fmt=sys.argv[1] if len(sys.argv)>1 else 'standard'
MAXP=float(sys.argv[2]) if len(sys.argv)>2 else 3.0
res=json.load(open('out/results.json'))[fmt]
cols=set(res['colors']); nland=res['nland']
R,opps=build(fmt); info=build_pool_index(fmt,R); util=load_util(R)
n2i={info[i]['name']:i for i in info}
counts={n2i[n]:c for n,c in res['counts'].items()}
base=make_deck(fmt,R,info,counts,res['colors'],nland,util)
life=20
b=run(R,opps,[base],ngames=1200,life=life,seed=515151)[0]
BASE=objective(b)
print(f"{fmt.upper()} {res['cname']} — base obj {BASE*100:.2f} (wr {b['wr']*100:.1f}%)")

# cartas del meta real, para cruzar
meta_names=set()
for f,ds in DECKS.items():
    for dn,w,cs in ds:
        for n,name in cs: meta_names.add(name)

def price(c):
    p=(c.get('prices') or {})
    for k in ('usd','usd_foil'):
        if p.get(k):
            try: return float(p[k])
            except: pass
    return None

legkey={'standard':'standard','pauper':'pauper','brawl':'brawl'}[fmt]
mine={c['name'] for c in json.load(open('data/pool.json'))}
cands=[]
for line in open('data/oracle.jsonl'):
    c=json.loads(line)
    if (c.get('legalities') or {}).get(legkey)!='legal': continue
    if c['name'] in mine: continue
    if 'Land' in (c.get('type_line') or ''): continue
    pr=price(c)
    if pr is None or pr>MAXP: continue
    e=convert(c)
    if e['typ'] in (0,6): continue
    if not {k for k in 'WUBRG' if e['pips'][k]} <= cols: continue
    if any(not (set(h)&cols) for h in e.get('hyb',[])): continue
    if e['cmc']>5: continue
    cands.append((c,e,pr))
print(f"candidatos comprables (<=US${MAXP:.0f}, en tus colores, legales): {len(cands)}")

# cada candidato entra como 4 copias (1 en brawl) sacando las peores del mazo
worst=sorted(counts.items(), key=lambda kv: info[kv[0]]['score'])
variants=[]; keys=[]
NC = 1 if fmt=='brawl' else 4
for c,e,pr in cands:
    idx=R.add(c)
    cc=dict(counts); need=NC
    for i,n in worst:
        if need<=0: break
        take=min(n,need); cc[i]=cc.get(i,0)-take
        if cc[i]<=0: del cc[i]
        need-=take
    cc[idx]=cc.get(idx,0)+NC
    if sum(cc.values())!=60-nland: continue
    variants.append(make_deck(fmt,R,info if idx in info else {**info, idx:{'name':c['name']}},cc,res['colors'],nland,util) if False else None)
    keys.append((c,e,pr,cc))
# construir mazos manualmente (make_deck necesita info; evitamos dependencia)
def build_deck(cc):
    sp=[]
    for i,n in cc.items(): sp+=[i]*n
    lands=[x for x in base if x not in counts and True]
    return sp+lands_only
lands_only=[x for x in base][-nland:]
decks=[]
for c,e,pr,cc in keys:
    sp=[]
    for i,n in cc.items(): sp+=[i]*n
    decks.append(sp+lands_only)
print("evaluando...")
out=[]
CH=400
for s in range(0,len(decks),CH):
    rr=run(R,opps,decks[s:s+CH],ngames=250,life=life,seed=515151)
    for (c,e,pr,cc),x in zip(keys[s:s+CH],rr):
        out.append((objective(x)-BASE, c['name'], pr, e['cmc'], c.get('type_line','').split('—')[0].strip(), c['name'] in meta_names))
out.sort(reverse=True)
print(f"\n{'delta':>7}  {'US$':>6}  {'mv':>2}  {'carta':<34} {'tipo':<22} meta?")
for d,n,pr,cmc,tl,inmeta in out[:25]:
    print(f"{d*100:+7.2f}  {pr:6.2f}  {cmc:2d}  {n[:32]:<34} {tl[:20]:<22} {'SI' if inmeta else ''}")
json.dump([{'delta':d,'name':n,'usd':pr,'cmc':cmc,'meta':m} for d,n,pr,cmc,tl,m in out[:60]],
          open(f'out/upgrade_{fmt}.json','w'), ensure_ascii=False)
