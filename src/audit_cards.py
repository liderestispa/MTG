"""Detecta cartas del meta cuyo modelado es implausible."""
import sys, json; sys.path.insert(0,'src'); sys.path.insert(0,'data')
from driver import lookup
from extract import convert
from meta_decks import DECKS
KW=['Flying','Deathtouch','Lifelink','Trample','Vigilance','Haste','Menace','Reach','FS','DS','Defender','Flash']

flags=[]
seen=set()
for f,ds in DECKS.items():
    for dn,w,cs in ds:
        for n,name in cs:
            if name in seen: continue
            seen.add(name)
            c=lookup(name); e=convert(c)
            if e['typ']==6: continue
            eff_cmc=e['gen']+sum(e['pips'].values())
            txt=' '.join((c.get('oracle_text') or '').split()).lower()
            why=[]
            if e['typ']==1:
                stat=e['power']+e['tough']
                if stat > 2*max(eff_cmc,1)+5: why.append(f"estadisticas {e['power']}/{e['tough']} para coste {eff_cmc}")
                nk=bin(e['kw']).count('1')
                if nk>=3 and eff_cmc<=2: why.append(f"{nk} keywords por {eff_cmc} mana")
            if eff_cmc <= e['cmc']-4: why.append(f"coste {e['cmc']}->{eff_cmc} (reduccion agresiva)")
            if e['typ']!=1 and (e['power'] or e['tough']): why.append("P/T en no-criatura")
            # texto con condicionales que podrian estar mal leidos
            if e['eff']==0 and e['typ'] in (2,3) and len(txt)>40: why.append("hechizo sin efecto parseado")
            if why: flags.append((f,dn,name,e['cmc'],eff_cmc,e['power'],e['tough'],why))

print(f"{len(flags)} cartas marcadas\n")
for f,dn,name,cmc,ec,p,t,why in sorted(flags,key=lambda x:-len(x[7]))[:34]:
    print(f"  [{f[:3]}] {name[:30]:<32} {'; '.join(why)}")
