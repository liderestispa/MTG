"""Busqueda de mazos: cribado por carta -> beam search sobre listas completas -> validacion."""
import json, sys, random, itertools, time
sys.path.insert(0,'src'); sys.path.insert(0,'data')
from driver import build, run, Registry, lookup
from extract import convert

BASICS = {'W':'Plains','U':'Island','B':'Swamp','R':'Mountain','G':'Forest'}

def pool_for(fmt, R):
    """devuelve [(defidx, maxcopias, cardinfo)] jugables en el formato"""
    key = {'standard':'legal_std','pauper':'legal_pau','brawl':'legal_brawl'}[fmt]
    out=[]
    for c in json.load(open('data/pool.json')):
        e = convert(c)
        if not e[key]: continue
        if e['typ']==6: continue                     # tierras aparte
        i = R.add(c)
        mx = min(c['qty'], 1 if fmt=='brawl' else 4)
        out.append((i, mx, e, c))
    return out

def lands_for(fmt, R, colors, n, specials):
    """base de mana: duales/utilitarias que tiene + basicas"""
    ids=[]
    for name,cnt in specials:
        try: ids += [R.add_by_name(name)]*cnt
        except KeyError: pass
    rest = n - len(ids)
    if rest<0: ids=ids[:n]; rest=0
    if not colors: colors=['B']
    per = rest//len(colors); extra = rest - per*len(colors)
    for k,col in enumerate(colors):
        ids += [R.add_by_name(BASICS[col])]*(per + (1 if k<extra else 0))
    return ids

def deck_colors(spells, R):
    cnt={'W':0,'U':0,'B':0,'R':0,'G':0}
    for i in spells:
        e=R.defs[i]
        for k,c in enumerate('WUBRG'):
            if e['pips'][c]: cnt[c]+=e['pips'][c]
    return [c for c in 'WUBRG' if cnt[c]>0], cnt

def legal(counts, maxc):
    return all(v<=maxc[k] for k,v in counts.items())

def greedy_deck(fmt, R, cand, colors, nland, nspell, landspec):
    """mazo semilla: mejores cartas por puntuacion heuristica dentro de los colores dados"""
    cs=set(colors)
    ok=[]
    for i,mx,e,c in cand:
        pips={k for k in 'WUBRG' if e['pips'][k]}
        if not pips <= cs: continue
        ok.append((R.defs[i]['score'] if 'score' in R.defs[i] else 0, i, mx, e, c))
    # puntuacion: reusa defscore replicado en python
    def sc(e):
        s=0
        if e['typ']==1: s = e['power']*3 + e['tough']*2
        kw=e['kw']
        for bit,b in [(1,4),(2,4),(8,2),(4,2),(64,2),(256,2),(32,1)]:
            if kw & bit: s+=b
        bonus={7:14,21:14,8:12,9:18,3:6,20:14,12:14,10:10,11:8,2:6,16:4,13:12,24:5,25:4,27:5,26:4,28:3}
        s += bonus.get(e['eff'],0)
        return s - e['cmc']
    ok=[(sc(e), i, mx, e, c) for _,i,mx,e,c in ok]
    ok.sort(key=lambda x:-x[0])
    spells=[]; used={}
    for s,i,mx,e,c in ok:
        if len(spells)>=nspell: break
        take=min(mx, nspell-len(spells), 4)
        if fmt=='brawl': take=1
        spells += [i]*take; used[i]=take
    lands = lands_for(fmt,R,colors,nland,landspec)
    return spells, lands, used

def evaluate(R,opps,decks,ng,life,seed):
    return run(R,opps,decks,ngames=ng,life=life,seed=seed)
