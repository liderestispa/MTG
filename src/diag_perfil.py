"""Perfil completo de cada mazo del meta contra el campo."""
import sys; sys.path.insert(0,'src')
from driver import build, run
from brawl import build_brawl, run_brawl
H=['wr','cast','removal','kills','sweep','counters','cseen','gamelen','noplay14','handend','win_dmg','lose_dmg','timeout']
def go(fmt, ng=800):
    life=25 if fmt=='brawl' else 20
    print(f"\n{'='*118}\n{fmt.upper()}\n{'='*118}")
    print(f"{'mazo':<26}"+''.join(f"{h:>8}" for h in H))
    if fmt=='brawl':
        R,opps=build_brawl()
        it=[(o[0],[(x[0],1000,x[2],x[3]) for j,x in enumerate(opps) if j!=i],(o[2],o[3])) for i,o in enumerate(opps)]
        for dn,others,me in it:
            r=run_brawl(R,others,[me],ngames=ng,life=life,seed=777)[0]; row(dn,r)
    else:
        R,opps=build(fmt)
        for i,(dn,w,ids) in enumerate(opps):
            others=[(o[0],1000,o[2]) for j,o in enumerate(opps) if j!=i]
            r=run(R,others,[ids],ngames=ng,life=life,seed=777)[0]; row(dn,r)
def row(dn,r):
    print(f"{dn[:25]:<26}"+''.join(f"{r[h]*100:7.1f}%" if h=='wr' else f"{r[h]:8.2f}" for h in H))
for f in (sys.argv[1:] or ['standard','pauper','brawl']): go(f)
