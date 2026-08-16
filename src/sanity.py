import sys; sys.path.insert(0,'src')
from driver import build, run, per_matchup
for fmt,life in [('standard',20),('pauper',20),('brawl',25)]:
    R,opps=build(fmt)
    print(f"\n=== {fmt.upper()} — prueba de cordura: cada mazo del meta contra el meta completo ===")
    print(f"    (registro: {len(R.defs)} cartas distintas)")
    tot=0
    for dn,w,ids in opps:
        wr=run(R,opps,[ids],ngames=300,life=life,seed=4242)[0]
        tot+=wr*w
        print(f"    {dn:<28} {wr*100:5.1f}%")
    print(f"    promedio ponderado (deberia dar ~50%): {tot/sum(w for _,w,_ in opps)*100:.1f}%")
