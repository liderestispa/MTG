import sys, json, time, random; sys.path.insert(0,'src')
from brawl import (build_brawl, my_pool, run_brawl, objective, seed_deck,
                   lands_brawl, sc, CI)
LOG=open('out/brawl.log','a',buffering=1)
def log(*a):
    m=' '.join(str(x) for x in a); print(m); LOG.write(m+'\n')

R,opps=build_brawl(); P=my_pool(R)
byidx={p['idx']:p for p in P}
NLAND=24; NSPELL=59-NLAND
log(f"pool brawl: {len(P)} cartas | 59 cartas + comandante | 24 tierras")

legs=[p for p in P if p['legend'] and (p['iscrea'] or p['ispw'])]
log(f"\n=== BARRIDO DE COMANDANTES ({len(legs)}) ===")
rows=[]
batch=[]; keys=[]
for L in legs:
    ci=L['ci']
    avail=[p for p in P if p['ci']<=ci and p['typ']!=6 and p['idx']!=L['idx']]
    if len(avail)<NSPELL: 
        log(f"    {L['name'][:34]:<36} descartado: solo {len(avail)} hechizos distintos (necesita {NSPELL})")
        continue
    sp=[i for i in seed_deck([p for p in P if p['idx']!=L['idx']], ci, NSPELL)]
    la=lands_brawl(R,P,ci,NLAND)
    batch.append((L['idx'], sp+la)); keys.append(L)
res=run_brawl(R,opps,batch,ngames=400,life=25,seed=2024)
for L,r in zip(keys,res): rows.append((objective(r),L,r))
rows.sort(key=lambda x:-x[0])
log(f"\n  {'comandante':<36}{'obj':>8}{'wr':>8}{'sinjug':>8}{'1a jug':>8}")
for o,L,r in rows[:14]:
    log(f"  {L['name'][:34]:<36}{o*100:7.2f}{r['wr']*100:7.1f}%{r['noplay14']:>8.2f}{r['firstplay']:>8.2f}")

# beam search sobre los 3 mejores comandantes
def neighbors(cur, ci, rng, k=200, cmd=None):
    pool=[p['idx'] for p in P if p['ci']<=ci and p['typ']!=6
          and p['idx'] not in cur and p['idx']!=cmd]
    out=[]
    cl=list(cur)
    for _ in range(k):
        c=set(cl)
        for _ in range(1 if rng.random()<0.6 else 2):
            if not c or not pool: break
            c.discard(rng.choice(list(c)))
            c.add(rng.choice(pool))
        if len(c)==len(cl): out.append(sorted(c))
    seen=set(); u=[]
    for c in out:
        t=tuple(c)
        if t in seen: continue
        seen.add(t); u.append(c)
    return u

log("\n=== BEAM SEARCH ===")
finals=[]
for o0,L,_ in rows[:3]:
    ci=L['ci']; rng=random.Random(4242)
    cur=[x for x in seed_deck([p for p in P if p['idx']!=L['idx']], ci, NSPELL) if x!=L['idx']]
    la=lands_brawl(R,P,ci,NLAND)
    B=[(o0, cur)]
    log(f"  --- {L['name'][:34]} ({''.join(sorted(ci))}) semilla {o0*100:.2f} ---")
    best=(o0,cur)
    for rd in range(10):
        cands=[]
        for _,c in B: cands += neighbors(c, ci, rng, k=220, cmd=L['idx'])
        seen=set(); uc=[]
        for c in cands:
            t=tuple(sorted(c))
            if t in seen: continue
            seen.add(t); uc.append(c)
        if not uc: break
        s=[objective(x) for x in run_brawl(R,opps,[(L['idx'], c+la) for c in uc],ngames=110,life=25,seed=700+rd)]
        top=sorted(range(len(uc)), key=lambda i:-s[i])[:40]
        s2=[objective(x) for x in run_brawl(R,opps,[(L['idx'], uc[i]+la) for i in top],ngames=550,life=25,seed=700+rd)]
        sc2=sorted(zip(s2,[uc[i] for i in top]), key=lambda x:-x[0])
        allp=sc2+B; allp.sort(key=lambda x:-x[0])
        seen=set(); B=[]
        for w,c in allp:
            t=tuple(sorted(c))
            if t in seen: continue
            seen.add(t); B.append((w,c))
            if len(B)>=8: break
        if B[0][0]>best[0]: best=B[0]
        log(f"      ronda {rd+1}: {B[0][0]*100:.2f}  ({len(uc)} cand.)")
    finals.append((best[0], L, best[1], la))
finals.sort(key=lambda x:-x[0])
w,L,sp,la=finals[0]
out=dict(commander=L['name'], ci=''.join(sorted(L['ci'])), obj=w,
         spells=[R.meta[i] for i in sp], lands=[R.meta[i] for i in la])
json.dump(out, open('out/brawl_result.json','w'), ensure_ascii=False, indent=1)
log(f"\n>>> GANADOR: {L['name']} ({''.join(sorted(L['ci']))}) obj {w*100:.2f}")
