# -*- coding: utf-8 -*-
"""Que fraccion del meta usa mecanicas de negacion, y cuantas las modela el extractor."""
import sys, re, json, collections; sys.path.insert(0,'src'); sys.path.insert(0,'data')
from driver import lookup, Registry
from extract import convert
import meta_decks as MD

PAT = {
 'descarte':        r'discard(s)? (a|an|that|two|three|\w+) card|discards? (their|his or her) hand',
 'impuesto':        r"cost(s)? \{[^}]+\} more|unless (that|its|the) (player|controller) pays",
 'no_atacar':       r"can't attack|can't block|attacks? each combat if able.*unless|doesn't untap",
 'tap_down':        r'tap target|becomes? tapped|remains? tapped',
 'edicto':          r'sacrifices? a creature|sacrifices? (a|an) (permanent|artifact|enchantment)',
 'niega_robo':      r"can't draw|skip (your|their) draw|draws? no cards",
 'destruye_tierra': r'destroy target land|sacrifices? a land',
 'roba_extra':      r'draw(s)? (a|two|three|\w+) card',
 'contrahechizo':   r'counter target',
 'proteccion':      r'hexproof|indestructible|ward|protection from',
 'exilia_cementerio': r'exile .* graveyard',
}
# efectos que el motor SI modela, por categoria
COVER = {
 'descarte': {4}, 'contrahechizo': {15}, 'roba_extra': {3,12,26,36,43},
 'proteccion': {47}, 'exilia_cementerio': {21,35},
 'edicto': {49}, 'tap_down': {50}, 'impuesto': {51},
 'destruye_tierra': {52}, 'no_atacar': {50,51},
}

tot=collections.Counter(); cov=collections.Counter(); ejem=collections.defaultdict(list)
ncards=0; seen=set()
for fmt, decks in [('standard',MD.STANDARD), ('pauper',MD.PAUPER), ('brawl',MD.BRAWL)]:
    for tup in decks:
        name, _w, txt = tup[0], tup[1], tup[-1]
        for n, nm in MD.parse(txt):
            c = lookup(nm)
            if not c: continue
            ncards += n
            txt = (c.get('oracle_text') or '')
            if '//' in (c.get('type_line') or '') and c.get('card_faces'):
                txt = ' '.join(f.get('oracle_text','') for f in c['card_faces'])
            e = convert(c)
            effs = {e['eff'], e.get('eff2',0), e.get('eff3',0)}
            for cat, pat in PAT.items():
                if re.search(pat, txt, re.I):
                    tot[cat]+=n
                    if effs & COVER.get(cat,set()):
                        cov[cat]+=n
                    elif len(ejem[cat])<4 and nm not in seen:
                        ejem[cat].append((nm, txt.replace('\n',' / ')[:95])); seen.add(nm)

print(f"cartas totales en los 19 mazos del meta: {ncards}\n")
print(f"{'mecanica':<20}{'cartas':>8}{'% meta':>8}{'modelada':>10}{'hueco':>8}")
for cat,_ in sorted(PAT.items(), key=lambda kv:-tot[kv[0]]):
    if not tot[cat]: continue
    print(f"{cat:<20}{tot[cat]:>8}{100*tot[cat]/ncards:>7.1f}%{cov[cat]:>10}{tot[cat]-cov[cat]:>8}")
print("\n--- ejemplos NO modelados ---")
for cat in PAT:
    if ejem[cat]:
        print(f"\n[{cat}]")
        for nm,t in ejem[cat]: print(f"   {nm}: {t}")
