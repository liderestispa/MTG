# -*- coding: utf-8 -*-
import sys, re; sys.path.insert(0,'src'); sys.path.insert(0,'data')
from driver import lookup
from extract import convert, E
import meta_decks as MD
INV = {v:k for k,v in E.items()}
PROT = r"gains? (hexproof|indestructible|protection)|gains? \w+ and (hexproof|indestructible)|can't be the target|hexproof and indestructible"
seen=set()
print(f"{'carta':<32}{'eff':<14}{'eff2':<12} texto")
n_prot=0; n_ok=0
for decks in (MD.STANDARD, MD.PAUPER, MD.BRAWL):
    for tup in decks:
        for cnt,nm in MD.parse(tup[-1]):
            if nm in seen: continue
            c=lookup(nm)
            if not c: continue
            t=(c.get('oracle_text') or '')
            if c.get('card_faces'): t=' '.join(f.get('oracle_text','') for f in c['card_faces'])
            if not re.search(PROT, t, re.I): continue
            seen.add(nm); n_prot+=cnt
            e=convert(c)
            ok = 47 in (e['eff'], e.get('eff2',0), e.get('eff3',0))
            if ok: n_ok+=cnt
            print(f"{nm[:31]:<32}{INV.get(e['eff'],'?'):<14}{INV.get(e.get('eff2',0),''):<12}"
                  f"{'OK' if ok else '--'} {t.replace(chr(10),' / ')[:70]}")
print(f"\ncartas con proteccion: {n_prot}   modeladas como E_PROTECT: {n_ok}")
