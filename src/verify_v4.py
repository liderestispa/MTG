"""Verificacion final de las tres listas v4 a partir de report_v4.json."""
import json, sys; sys.path.insert(0,'src')
from check_legal import check
D=json.load(open('out/report_v4.json'))
CFG={'standard':('standard',60,False,None),'pauper':('pauper',60,False,None),
     'brawl':('standardbrawl',60,True,'cmd')}
ok=True
for k,(fmt,size,single,cmdkey) in CFG.items():
    d=D[k]; cards=[]
    for c in d['sp']: cards += [c['name']]*c['n']
    for nm,n in d['la'].items(): cards += [nm]*n
    cmd = d.get('cmd') if cmdkey else None
    print(f"\n### {d['t']} ({d['col']}) — {len(cards)} cartas" + (f" + {cmd}" if cmd else ""))
    r=check(cards, fmt, commander=cmd, deck_size=size, singleton=single)
    if r is not None and r is not True: ok = ok and bool(r)
print("\nFIN")
