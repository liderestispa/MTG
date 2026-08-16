import sys, json, time, os; sys.path.insert(0,'src')
from driver import build, run
from search import (build_pool_index, load_util, greedy_counts, make_deck,
                    beam_search, objective, color_sweep)
import itertools

OUT={}
LOG=open('out/search.log','a',buffering=1)
def log(*a):
    m=' '.join(str(x) for x in a); print(m); LOG.write(m+'\n')

CFG = {
 'standard': dict(life=20, nland=24, nspell=36, topk=3),
 'pauper'  : dict(life=20, nland=23, nspell=37, topk=3),
}

def name_of(R,i): return R.meta[i]

for fmt in ['standard','pauper']:
    cfg=CFG[fmt]; life=cfg['life']
    R,opps=build(fmt); info=build_pool_index(fmt,R); util=load_util(R)
    log(f"\n########## {fmt.upper()} ##########")
    # 1) barrido de identidades con semilla de curva
    rows=[]
    for r in (1,2,3):
        for cc in itertools.combinations('WUBRG', r):
            cols=list(cc)
            c=greedy_counts(info,cols,cfg['nspell'],fmt)
            if sum(c.values())<cfg['nspell']: continue
            d=make_deck(fmt,R,info,c,cols,cfg['nland'],util)
            rr=run(R,opps,[d],ngames=500,life=life,seed=31337)[0]
            rows.append((objective(rr),''.join(cols),cols,rr))
    rows.sort(key=lambda x:-x[0])
    log("  barrido de identidades (top 8):")
    for o,cn,_,rr in rows[:8]:
        log(f"    {cn:<5} obj {o*100:6.2f} | wr {rr['wr']*100:5.1f}% | sin jugada T1-4 {rr['noplay14']:.2f} | 1a jugada T{rr['firstplay']:.2f}")
    best=[]
    for o,cn,cols,rr in rows[:cfg['topk']]:
        log(f"  --- beam search en {cn} ---")
        t=time.time()
        w,counts = beam_search(fmt,R,opps,info,util,cols,life,cfg['nland'],cfg['nspell'],
                               rounds=12, beam=10, cand_per=240, screen=120, deep=600,
                               seed0=911, log=log)
        log(f"      {cn}: {w*100:.2f} en {time.time()-t:.0f}s")
        best.append((w,cn,cols,counts))
    best.sort(key=lambda x:-x[0])
    # 2) afinar cuenta de tierras del ganador
    w,cn,cols,counts=best[0]
    log(f"  ganador: {cn}. afinando tierras...")
    bl=(w,cfg['nland'],counts)
    for nl in range(cfg['nland']-2, cfg['nland']+3):
        ns=60-nl
        cc=dict(counts); tot=sum(cc.values())
        # ajustar cantidad de hechizos
        while tot>ns:
            k=min(cc, key=lambda x: info[x]['score']); cc[k]-=1; tot-=1
            if cc[k]==0: del cc[k]
        while tot<ns:
            k=max((x for x in info if info[x]['pips']<=set(cols) and cc.get(x,0)<min(info[x]['maxc'],4)),
                  key=lambda x: info[x]['score'], default=None)
            if k is None: break
            cc[k]=cc.get(k,0)+1; tot+=1
        d=make_deck(fmt,R,info,cc,cols,nl,util)
        rr=run(R,opps,[d],ngames=800,life=life,seed=4242)[0]
        o=objective(rr)
        log(f"      {nl} tierras: obj {o*100:.2f} wr {rr['wr']*100:.1f}% sinjugada {rr['noplay14']:.2f}")
        if o>bl[0]: bl=(o,nl,cc)
    OUT[fmt]=dict(colors=cols, cname=cn, nland=bl[1], obj=bl[0],
                  counts={name_of(R,i):n for i,n in bl[2].items()},
                  util=[k for k,(q,cs,e) in util.items() if set(cs)<=set(cols)])
    json.dump(OUT, open('out/results.json','w'), ensure_ascii=False, indent=1)
    log(f"  >>> {fmt}: {cn}, {bl[1]} tierras, obj {bl[0]*100:.2f}")
log("\nFIN")
