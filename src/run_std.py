import sys, json, time; sys.path.insert(0,'src')
from driver import build, run
from search import build_pool_index, load_util, color_sweep, beam_search, make_deck
t0=time.time()
fmt='standard'; life=20
R,opps=build(fmt); info=build_pool_index(fmt,R); util=load_util(R)
print(f"tierras duales utiles que tienes: {list(util.keys())}")
best_overall=None
print("\n=== BARRIDO DE COLORES (24 tierras / 36 hechizos) ===")
sw=color_sweep(fmt,R,opps,info,util,life,24,36,ng=250)
for w,cols,_ in sw[:10]: print(f"    {''.join(cols):<5} {w*100:5.2f}%")
top=[(w,cols,c) for w,cols,c in sw[:3]]
print("\n=== BARRIDO DE CUENTA DE TIERRAS (mejor identidad) ===")
w0,cols0,cnt0=top[0]
for nl in (22,23,24,25,26):
    ns=60-nl
    from search import greedy_counts
    c=greedy_counts(info,cols0,ns,fmt)
    d=make_deck(fmt,R,info,c,cols0,nl,util)
    w=run(R,opps,[d],ngames=350,life=life,seed=77)[0]
    print(f"    {nl} tierras / {ns} hechizos: {w*100:5.2f}%")
print(f"\ntiempo: {time.time()-t0:.0f}s")
json.dump([[w,cols] for w,cols,_ in sw], open('out/std_colorsweep.json','w'))
