# -*- coding: utf-8 -*-
"""Radiografia: como quedo modelada cada carta de un mazo."""
import sys, re; sys.path.insert(0,'src'); sys.path.insert(0,'data')
from driver import lookup
from extract import convert, E
import meta_decks as MD
INV={v:k for k,v in E.items()}
KWN=[(1<<0,'vol'),(1<<1,'tox'),(1<<2,'vin'),(1<<3,'arr'),(1<<4,'vig'),(1<<5,'pri'),
     (1<<6,'ame'),(1<<7,'alc'),(1<<8,'gpi'),(1<<9,'gdo'),(1<<10,'def'),(1<<11,'des'),
     (1<<12,'HEX'),(1<<13,'IND'),(1<<14,'WARD'),(1<<15,'PRO'),(1<<16,'pro')]
target=' '.join(sys.argv[1:]).lower()
for decks in (MD.STANDARD, MD.PAUPER, MD.BRAWL):
    for tup in decks:
        if target not in tup[0].lower(): continue
        print(f"\n===== {tup[0]} =====")
        print(f"{'n':>2} {'carta':<30}{'cmc':>4}{'P/T':>7} {'tipo':<5}{'efecto':<14}{'ef2':<12}{'ef3':<10}kw")
        for cnt,nm in MD.parse(tup[-1]):
            c=lookup(nm)
            if not c: print(f"{cnt:>2} {nm:<30}  *** NO ENCONTRADA ***"); continue
            e=convert(c)
            if e['typ']==6: continue
            kws=','.join(n for b,n in KWN if e['kw']&b)
            t=(c.get('type_line') or '')[:5]
            print(f"{cnt:>2} {nm[:29]:<30}{e['cmc']:>4}{str(e['power'])+'/'+str(e['tough']):>7} {t:<5}"
                  f"{INV.get(e['eff'],'?'):<14}{INV.get(e.get('eff2',0),''):<12}{INV.get(e.get('eff3',0),''):<10}{kws}")
