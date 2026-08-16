# -*- coding: utf-8 -*-
"""Cuanto del meta es INVISIBLE para el motor: cartas sin ningun efecto modelado."""
import sys, collections; sys.path.insert(0,'src'); sys.path.insert(0,'data')
from driver import lookup
from extract import convert, E
import meta_decks as MD
INV={v:k for k,v in E.items()}
tot=0; ciegas=0; cre_ciegas=0; nocre_ciegas=0
lista=collections.Counter(); txt={}
for decks in (MD.STANDARD, MD.PAUPER, MD.BRAWL):
    for tup in decks:
        for cnt,nm in MD.parse(tup[-1]):
            c=lookup(nm)
            if not c: continue
            e=convert(c)
            if e['typ']==6: continue          # tierras aparte
            tot+=cnt
            t=(c.get('oracle_text') or '')
            if c.get('card_faces'): t=' '.join(f.get('oracle_text','') for f in c['card_faces'])
            has_eff = any(e.get(k,0) for k in ('eff','eff2','eff3'))
            has_mana = e.get('mana_out',0) or (e['typ']!=6 and e.get('produces',0))
            has_red  = e.get('gen',0) and e.get('gen',0) < e['cmc']   # reduccion de coste aplicada
            has_dyn  = e.get('dyn',0)
            # una criatura vainilla con keywords SI esta modelada (cuerpo + keywords)
            vanilla_ok = (e['typ']==1 and (e['kw'] or not t.strip()))
            if not (has_eff or has_mana or has_red or has_dyn or vanilla_ok):
                ciegas+=cnt; lista[nm]+=cnt; txt[nm]=(t.replace('\n',' / ')[:100], e['typ'], e['cmc'])
                if e['typ']==1: cre_ciegas+=cnt
                else: nocre_ciegas+=cnt
print(f"cartas no-tierra en el meta: {tot}")
print(f"INVISIBLES para el motor:    {ciegas}  ({100*ciegas/tot:.1f}%)   "
      f"[criaturas {cre_ciegas}, no-criaturas {nocre_ciegas}]\n")
TN={0:'?',1:'criatura',2:'instant',3:'sorcery',4:'artefacto',5:'encant',6:'tierra',7:'planeswalker'}
print(f"{'n':>3} {'carta':<30}{'tipo':<12}{'cmc':>4}  texto")
for nm,n in lista.most_common(45):
    t,ty,cmc = txt[nm]
    print(f"{n:>3} {nm[:29]:<30}{TN.get(ty,ty):<12}{cmc:>4}  {t}")
