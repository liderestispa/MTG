# -*- coding: utf-8 -*-
import sys, re, collections; sys.path.insert(0,'src'); sys.path.insert(0,'data')
from driver import lookup
from extract import convert, KWBIT
import meta_decks as MD
KW_TEST = {'hexproof':'hexproof','ward':'ward','indestructible':'indestructible',
           'trample':'trample','flying':'flying','deathtouch':'deathtouch',
           'lifelink':'lifelink','first strike':'first strike','vigilance':'vigilance',
           'menace':'menace','haste':'haste','reach':'reach','flash':'flash','defender':'defender'}
BIT = {'hexproof':1<<12,'indestructible':1<<13,'ward':1<<14,'trample':1<<3,'flying':1<<0,
       'deathtouch':1<<1,'lifelink':1<<2,'first strike':1<<8,'vigilance':1<<4,
       'menace':1<<6,'haste':1<<5,'reach':1<<7,'flash':1<<11,'defender':1<<10}
txt_n=collections.Counter(); got_n=collections.Counter(); miss=collections.defaultdict(list)
seen=set()
for decks in (MD.STANDARD, MD.PAUPER, MD.BRAWL):
    for tup in decks:
        for n,nm in MD.parse(tup[-1]):
            c=lookup(nm)
            if not c: continue
            t=(c.get('oracle_text') or '')
            if c.get('card_faces'): t=' '.join(f.get('oracle_text','') for f in c['card_faces'])
            e=convert(c)
            for k in KW_TEST:
                if re.search(r'\b'+k+r'\b', t, re.I):
                    txt_n[k]+=n
                    if e['kw'] & BIT[k]: got_n[k]+=n
                    elif len(miss[k])<5 and nm not in seen:
                        line=[l for l in t.split('\n') if re.search(r'\b'+k+r'\b',l,re.I)]
                        miss[k].append((nm, (line[0] if line else t)[:88])); seen.add(nm)
print(f"{'keyword':<16}{'en texto':>10}{'parseada':>10}{'perdidas':>10}")
for k in sorted(KW_TEST, key=lambda x:-(txt_n[x]-got_n[x])):
    if txt_n[k]: print(f"{k:<16}{txt_n[k]:>10}{got_n[k]:>10}{txt_n[k]-got_n[k]:>10}")
print("\n--- perdidas (ejemplos) ---")
for k in sorted(miss, key=lambda x:-(txt_n[x]-got_n[x])):
    if miss[k]:
        print(f"\n[{k}]")
        for nm,l in miss[k]: print(f"   {nm}: {l}")
