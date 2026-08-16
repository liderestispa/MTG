"""Verifica que una lista sea LEGAL y ARMABLE con la coleccion real."""
import sys, json; sys.path.insert(0,'src')
from driver import lookup
from collections import Counter

def check(cards, fmt, commander=None, deck_size=60, singleton=False):
    pool={c['name']:c for c in json.load(open('data/pool.json'))}
    front={}
    for c in json.load(open('data/pool.json')):
        front[c['name'].split('//')[0].strip()]=c
    cnt=Counter(cards)
    if commander: cnt[commander]+=1
    errs=[]; warns=[]
    BASIC={'Plains','Island','Swamp','Mountain','Forest','Wastes'}
    total=sum(cnt.values())
    if total!=deck_size: errs.append(f"TAMAÑO: {total} cartas, deben ser {deck_size}")
    ci_cmd=None
    if commander:
        c=lookup(commander)
        ci_cmd=set(c.get('color_identity') or [])
        tl=c.get('type_line') or ''
        if 'Legendary' not in tl: errs.append(f"COMANDANTE: {commander} no es legendaria")
    for name,n in cnt.items():
        c=lookup(name)
        if c is None: errs.append(f"NO EXISTE: {name}"); continue
        leg=(c.get('legalities') or {}).get(fmt)
        if leg!='legal': errs.append(f"ILEGAL en {fmt}: {name} ({leg})")
        if name not in BASIC:
            lim = 1 if singleton else 4
            if n>lim: errs.append(f"COPIAS: {n}x {name} (máximo {lim})")
            own = pool.get(name) or front.get(name)
            have = own['qty'] if own else 0
            if have<n: errs.append(f"NO LA TIENES: {name} pide {n}, tienes {have}")
        if ci_cmd is not None:
            ci=set(c.get('color_identity') or [])
            if not ci <= ci_cmd:
                errs.append(f"IDENTIDAD: {name} es {''.join(sorted(ci))}, comandante es {''.join(sorted(ci_cmd))}")
    return errs, warns

if __name__=='__main__':
    d=json.load(open('out/brawl_result.json'))
    errs,_=check(d['spells']+d['lands'], 'standardbrawl', commander=d['commander'], deck_size=60, singleton=True)
    print(f"BRAWL — {d['commander']}")
    print(f"  {len(d['spells'])} hechizos + {len(d['lands'])} tierras + comandante = {len(d['spells'])+len(d['lands'])+1}")
    if errs:
        print(f"  ❌ {len(errs)} problemas:")
        for e in errs[:20]: print("     ", e)
    else:
        print("  ✅ LEGAL Y ARMABLE — sin errores")
