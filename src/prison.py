import sys, json; sys.path.insert(0,'src'); sys.path.insert(0,'data')
from brawl import build_brawl, run_brawl, objective
from driver import lookup

ERIETTE = ("Eriette of the Charmed Apple", """
Pacifism / Cooped Up / Spiral into Solitude / Petrify / Cracked Skull / Sheltered by Ghosts
Hardlight Containment / Dimensional Exile / Authority of the Consuls / Dáin, Lord of the Iron Hills
Grand Abolisher / Clarion Conqueror / Sorcerous Spyglass / Aven Interrupter / Archangel of Tithes
Duress / Pilfer / Hopeless Nightmare / Bandit's Talent / Virus Beetle / Deep-Cavern Bat
Unscrupulous Agent / Glass Casket / Makeshift Binding / Banishing Light / Stasis Snare
Get Lost / The End / Day of Judgment / Deadly Cover-Up / Starfall Invocation
Ketramose, the New Dawn / Kaya, Spirits' Justice / Liliana, Dreadhorde General / Virtue of Persistence
8 Plains / 7 Swamp / Concealed Courtyard / Bleachbone Verge / Restless Fortress / Shattered Sanctum
Scoured Barrens / Temple of Silence / Forlorn Flats / Orzhov Guildgate / Command Tower""")

TINYBONES = ("Tinybones, Bauble Burglar", """
Burglar Rat / Virus Beetle / Gastal Raider / Tinybones, the Pickpocket / Deep-Cavern Bat
Skullcap Snail / Unscrupulous Agent / Emeritus of Woe / Overlord of the Balemurk
Aclazotz, Deepest Betrayal / Duress / Binding Negotiation / Bitter Triumph / Pilfer
Cerebral Confiscation / Seeker's Folly / Rankle's Prank / Temporal Intervention
Shredder's Revenge / Locust Spray / Ruthless Negotiation / Stab / Feed the Swarm
Bandit's Talent / Momentum Breaker / Grim Bauble / Hopeless Nightmare / Dai Li Indoctrination
Send in the Pest / Intimidation Tactics / Aggressive Negotiations / Archenemy's Charm
Cracked Skull / Heraldic Banner / Fell / Auntie's Sentence / 22 Swamp / Mudflat Village""")

def parse(txt):
    out=[]
    for ch in txt.replace('\n','/').split('/'):
        ch=ch.strip()
        if not ch: continue
        p=ch.split(' ',1)
        if p[0].isdigit(): out.append((int(p[0]), p[1].strip()))
        else: out.append((1, ch))
    return out

R,opps=build_brawl()
tests=[]
for cname, txt in [ERIETTE, TINYBONES]:
    cards=parse(txt); ids=[]; miss=[]
    for n,name in cards:
        c=lookup(name)
        if c is None: miss.append(name); continue
        i=R.add(c); ids += [i]*n
    cmd=R.add(lookup(cname))
    tot=len(ids)+1
    leg=[]
    for n,name in cards:
        c=lookup(name)
        if c and (c.get('legalities') or {}).get('standardbrawl')!='legal': leg.append(name)
    print(f"{cname}: {tot} cartas | sin resolver: {miss} | ILEGALES en standardbrawl: {leg}")
    tests.append((cname, cmd, ids))

# Ketramose ya esta en el meta
ket=[o for o in opps if 'Ketramose' in o[0]][0]
tests.append(("Ketramose (lista meta)", ket[2], ket[3]))

print(f"\n{'mazo':<34}{'indice':>9}{'sinjug':>9}{'1a jug':>9}")
for name, cmd, ids in tests:
    r=run_brawl(R,opps,[(cmd,ids)],ngames=1500,life=25,seed=808080)[0]
    print(f"{name:<34}{r['wr']*100:8.1f}%{r['noplay14']:>9.2f}{r['firstplay']:>9.2f}")
print()
for name, cmd, ids in tests:
    print(f"  {name}:")
    for dn,w,c2,i2 in opps:
        x=run_brawl(R,[(dn,1000,c2,i2)],[(cmd,ids)],ngames=1200,life=25,seed=717171)[0]
        print(f"     vs {dn:<26} {w/10:4.1f}% meta   {x['wr']*100:5.1f}%")
