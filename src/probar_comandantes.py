# -*- coding: utf-8 -*-
"""Evalua comandantes que NO tiene, armando el resto con su coleccion."""
import sys, json, random; sys.path.insert(0,'src')
from brawl import build_brawl, my_pool, run_brawl, objective, seed_deck, lands_brawl
from driver import lookup
LOG=open('out/comandantes_hobbit.log','w',buffering=1)
def log(*a):
    m=' '.join(str(x) for x in a); print(m,flush=True); LOG.write(m+'\n')

R,opps=build_brawl(); P=my_pool(R)
NLAND=24; NSPELL=59-NLAND
CAND=['Thranduil, the Elvenking','Smaug the Magnificent','Beorn the Fierce']
NG_FINAL=2500; SEED_FINAL=31337

def beam(name, rounds=10):
    c=lookup(name); ci=set(c.get('color_identity') or [])
    cmd=R.add_by_name(name)
    avail=[p for p in P if p['ci']<=ci and p['typ']!=6]
    if len(avail)<NSPELL: log(f"  {name}: pool insuficiente"); return None
    rng=random.Random(4242)
    cur=[x for x in seed_deck(P, ci, NSPELL)]
    la=lands_brawl(R,P,ci,NLAND)
    o0=objective(run_brawl(R,opps,[(cmd,cur+la)],ngames=550,life=25,seed=4242)[0])
    log(f"  --- {name} ({''.join(sorted(ci)) or 'C'}) semilla {o0*100:.2f} ---")
    B=[(o0,cur)]; best=(o0,cur)
    pool=[p['idx'] for p in P if p['ci']<=ci and p['typ']!=6]
    for rd in range(rounds):
        cands=[]
        for _,cc in B:
            for _ in range(220):
                s=set(cc)
                for _ in range(1 if rng.random()<0.6 else 2):
                    if not s or not pool: break
                    s.discard(rng.choice(list(s))); s.add(rng.choice(pool))
                if len(s)==len(cc): cands.append(sorted(s))
        seen=set(); uc=[]
        for cc in cands:
            t=tuple(cc)
            if t in seen: continue
            seen.add(t); uc.append(cc)
        if not uc: break
        s1=[objective(x) for x in run_brawl(R,opps,[(cmd,cc+la) for cc in uc],ngames=110,life=25,seed=700+rd)]
        top=sorted(range(len(uc)), key=lambda i:-s1[i])[:40]
        s2=[objective(x) for x in run_brawl(R,opps,[(cmd,uc[i]+la) for i in top],ngames=550,life=25,seed=700+rd)]
        sc=sorted(zip(s2,[uc[i] for i in top]), key=lambda x:-x[0])
        allp=sc+B; allp.sort(key=lambda x:-x[0])
        seen=set(); B=[]
        for w,cc in allp:
            t=tuple(sorted(cc))
            if t in seen: continue
            seen.add(t); B.append((w,cc))
            if len(B)>=8: break
        if B[0][0]>best[0]: best=B[0]
        log(f"      ronda {rd+1}: {B[0][0]*100:.2f}  ({len(uc)} cand.)")
    # medicion final independiente
    rf=run_brawl(R,opps,[(cmd,best[1]+la)],ngames=NG_FINAL,life=25,seed=SEED_FINAL)[0]
    # semilla codiciosa con la misma vara
    rs=run_brawl(R,opps,[(cmd,cur+la)],ngames=NG_FINAL,life=25,seed=SEED_FINAL)[0]
    mm=[]
    for o in opps:
        r=run_brawl(R,[(o[0],1000,o[2],o[3])],[(cmd,best[1]+la)],ngames=1200,life=25,seed=999)[0]
        mm.append([o[0], o[1]/10.0, r['wr']*100])
    pr=(c.get('prices') or {}).get('usd') or '?'
    return dict(name=name, ci=''.join(sorted(ci)) or 'C', obj=objective(rf)*100, wr=rf['wr']*100,
                seed_obj=objective(rs)*100, gain=objective(rf)*100-objective(rs)*100,
                precio=pr, spells=[R.meta[i] for i in best[1]], lands=[R.meta[i] for i in la],
                mm=sorted(mm,key=lambda x:-x[1]))

# referencia: su mazo actual medido con la misma vara
BR=json.load(open('out/brawl_result.json'))
cmd0=R.add_by_name(BR['commander'])
ids0=[R.add_by_name(n) for n in BR['spells']]+[R.add_by_name(n) for n in BR['lands']]
r0=run_brawl(R,opps,[(cmd0,ids0)],ngames=NG_FINAL,life=25,seed=SEED_FINAL)[0]
log(f"REFERENCIA — {BR['commander']}: obj {objective(r0)*100:.2f} wr {r0['wr']*100:.1f}%\n")

OUT={'referencia':dict(name=BR['commander'], obj=objective(r0)*100, wr=r0['wr']*100)}
for n in CAND:
    res=beam(n)
    if res:
        OUT[n]=res
        log(f"  >>> {n}: obj {res['obj']:.2f}  wr {res['wr']:.1f}%  "
            f"(semilla {res['seed_obj']:.2f}, ventaja {res['gain']:+.2f})  US${res['precio']}\n")
        json.dump(OUT, open('out/comandantes_hobbit.json','w'), ensure_ascii=False, indent=1)
json.dump(OUT, open('out/comandantes_hobbit.json','w'), ensure_ascii=False, indent=1)
log("FIN")
