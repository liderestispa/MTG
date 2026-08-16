"""Barrido de colores + beam search con racing. Salida: mejores listas por formato."""
import json, sys, itertools, random, time, os
sys.path.insert(0,'src'); sys.path.insert(0,'data')
from driver import build, run

def objective(r):
    return r['wr'] - 0.030*r['noplay14'] - 0.020*max(0.0, r['firstplay']-2.0)
from optimize import pool_for, lands_for, BASICS
from extract import convert

# tierras no-basicas utiles que TIENE (nombre scryfall, copias)
UTIL_LANDS = {}
def load_util(R):
    out={}
    for c in json.load(open('data/pool.json')):
        e=convert(c)
        if e['typ']!=6: continue
        if not e['produces']: continue          # descarta Hobbit Hole (no produce mana)
        cols=[k for k in 'WUBRG' if e['produces'] & (1<<'WUBRG'.index(k))]
        if len(cols)>=2: out[c['name']]=(c['qty'], cols, e)
    return out

def sc(e):
    s=0
    if e['typ']==1: s = e['power']*3 + e['tough']*2
    kw=e['kw']
    for bit,b in [(1,4),(2,4),(8,2),(4,2),(64,2),(256,2),(32,1),(2048,1)]:
        if kw & bit: s+=b
    bonus={7:14,21:14,8:12,9:18,3:6,20:14,12:14,10:10,11:8,2:6,16:4,13:12,24:5,25:4,27:5,26:4,28:3,15:11,17:2,23:9,22:6,5:5}
    s += bonus.get(e['eff'],0) + bonus.get(e['eff2'],0)//2
    return s - e['cmc']

def build_pool_index(fmt,R):
    cand=pool_for(fmt,R)
    info={}
    for i,mx,e,c in cand:
        info[i]=dict(maxc=mx, e=e, name=c['name'], score=sc(e),
                     pips={k for k in 'WUBRG' if e['pips'][k]},
                     hyb=[set(h) for h in e.get('hyb',[])], cmc=e['cmc'], qty=c['qty'])
    return info

def make_deck(fmt,R,info,counts,colors,nland,util):
    spells=[]
    for i,n in counts.items(): spells += [i]*n
    spec=[]
    for name,(q,cols,e) in util.items():
        if set(cols) <= set(colors): spec.append((name, min(q, 4 if fmt!='brawl' else 1)))
    lands = lands_for(fmt,R,colors,nland,spec)
    return spells+lands

CURVE = {1:0.10, 2:0.28, 3:0.26, 4:0.18, 5:0.10, 6:0.05, 7:0.03}
def greedy_counts(info,colors,nspell,fmt):
    """semilla que respeta una curva razonable en vez de apilar bombas"""
    cs=set(colors)
    by={}
    for i,d in info.items():
        if not d['pips'] <= cs: continue
        if any(not (h & cs) for h in d.get('hyb',[])): continue
        by.setdefault(min(d['cmc'],7), []).append((d['score'], i, d))
    for k in by: by[k].sort(key=lambda x:-x[0])
    counts={}; tot=0
    for band,frac in sorted(CURVE.items()):
        want=int(round(nspell*frac))
        for s_,i,d in by.get(band,[]):
            if want<=0 or tot>=nspell: break
            take = 1 if fmt=='brawl' else min(d['maxc'],4,want,nspell-tot)
            if take<=0: continue
            counts[i]=counts.get(i,0)+take; tot+=take; want-=take
    # rellenar lo que falte con lo mejor disponible
    allc=sorted([(d['score'],i,d) for i,d in info.items()
                 if d['pips']<=cs and all(h & cs for h in d.get('hyb',[]))], key=lambda x:-x[0])
    for s_,i,d in allc:
        if tot>=nspell: break
        mx = 1 if fmt=='brawl' else min(d['maxc'],4)
        add=min(mx-counts.get(i,0), nspell-tot)
        if add>0: counts[i]=counts.get(i,0)+add; tot+=add
    return counts

def greedy_counts_old(info,colors,nspell,fmt):
    cs=set(colors); ok=[]
    for i,d in info.items():
        if not d['pips'] <= cs: continue
        ok.append((d['score'],i,d))
    ok.sort(key=lambda x:(-x[0], x[2]['cmc']))
    counts={}; tot=0
    for s,i,d in ok:
        if tot>=nspell: break
        take = 1 if fmt=='brawl' else min(d['maxc'], 4, nspell-tot)
        counts[i]=take; tot+=take
    return counts

def color_sweep(fmt,R,opps,info,util,life,nland,nspell,ng=250,seed=101):
    combos=[]
    for r in (1,2,3):
        for cc in itertools.combinations('WUBRG', r): combos.append(list(cc))
    res=[]
    batch=[]; keys=[]
    for cols in combos:
        counts=greedy_counts(info,cols,nspell,fmt)
        if sum(counts.values())<nspell*0.9: continue
        batch.append(make_deck(fmt,R,info,counts,cols,nland,util)); keys.append((cols,counts))
    wrs=[objective(x) for x in run(R,opps,batch,ngames=ng,life=life,seed=seed)]
    for (cols,counts),w in zip(keys,wrs): res.append((w,cols,counts))
    res.sort(key=lambda x:-x[0])
    return res

def neighbors(counts,info,colors,fmt,nspell,rng,k=180):
    """genera variantes: quitar 1 / poner 1, y algunos swaps dobles"""
    cs=set(colors)
    pool=[i for i,d in info.items() if d['pips']<=cs and all(h & cs for h in d.get('hyb',[]))]
    out=[]
    present=[i for i,n in counts.items() if n>0]
    for _ in range(k):
        c=dict(counts)
        nsw = 1 if rng.random()<0.6 else 2
        okk=True
        for _ in range(nsw):
            if not present: okk=False; break
            rm=rng.choice(present)
            c[rm]-=1
            if c[rm]<=0: del c[rm]
            for _try in range(12):
                ad=rng.choice(pool)
                mx = 1 if fmt=='brawl' else info[ad]['maxc']
                if c.get(ad,0) < mx:
                    c[ad]=c.get(ad,0)+1; break
            else: okk=False; break
            present=[i for i,n in c.items() if n>0]
        if okk and sum(c.values())==nspell: out.append(c)
        present=[i for i,n in counts.items() if n>0]
    # dedup
    seen=set(); uniq=[]
    for c in out:
        k2=tuple(sorted(c.items()))
        if k2 in seen: continue
        seen.add(k2); uniq.append(c)
    return uniq

def beam_search(fmt,R,opps,info,util,colors,life,nland,nspell,
                rounds=8, beam=8, cand_per=160, screen=70, deep=350, seed0=555, log=print):
    rng=random.Random(seed0)
    start=greedy_counts(info,colors,nspell,fmt)
    B=[(None,start)]
    # evalua semilla
    w=objective(run(R,opps,[make_deck(fmt,R,info,start,colors,nland,util)],ngames=deep,life=life,seed=seed0)[0])
    B=[(w,start)]
    log(f"    semilla greedy: {w*100:.2f}%")
    best=(w,start)
    for rd in range(rounds):
        cands=[]
        for _,c in B:
            cands += neighbors(c,info,colors,fmt,nspell,rng,k=cand_per)
        # dedup global
        seen=set(); uc=[]
        for c in cands:
            k2=tuple(sorted(c.items()))
            if k2 in seen: continue
            seen.add(k2); uc.append(c)
        if not uc: break
        decks=[make_deck(fmt,R,info,c,colors,nland,util) for c in uc]
        s=[objective(x) for x in run(R,opps,decks,ngames=screen,life=life,seed=seed0+rd*13)]     # criba barata
        order=sorted(range(len(uc)), key=lambda i:-s[i])[:max(beam*4,40)]
        decks2=[make_deck(fmt,R,info,uc[i],colors,nland,util) for i in order]
        s2=[objective(x) for x in run(R,opps,decks2,ngames=deep,life=life,seed=seed0+rd*13)]     # evaluacion profunda
        scored=sorted(zip(s2,[uc[i] for i in order]), key=lambda x:-x[0])
        pool_all = scored + B
        pool_all.sort(key=lambda x:-x[0])
        # dedup por contenido
        seen=set(); B=[]
        for w2,c in pool_all:
            k2=tuple(sorted(c.items()))
            if k2 in seen: continue
            seen.add(k2); B.append((w2,c))
            if len(B)>=beam: break
        if B[0][0]>best[0]: best=B[0]
        log(f"    ronda {rd+1}: mejor {B[0][0]*100:.2f}%  (candidatos {len(uc)})")
    return best
