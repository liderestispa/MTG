import json, sys, subprocess, random, time, itertools
sys.path.insert(0,'src'); sys.path.insert(0,'data')
from driver import Registry, lookup, norm
from extract import convert
from meta_decks import DECKS

BASICS={'W':'Plains','U':'Island','B':'Swamp','R':'Mountain','G':'Forest'}
CI = lambda e: {c for k,c in enumerate('WUBRG') if e['ci'] & (1<<k)}

def build_brawl():
    R=Registry(); opps=[]
    for dn,w,cs in DECKS['brawl']:
        ids=[]; cmd=-1
        for n,name in cs:
            c=lookup(name); i=R.add(c)
            if cmd<0 and 'Legendary' in (c.get('type_line') or '') and ('Creature' in (c.get('type_line') or '') or 'Planeswalker' in (c.get('type_line') or '')):
                cmd=i; continue          # el primero listado es el comandante
            ids += [i]*n
        opps.append((dn,w,cmd,ids))
    return R,opps

def run_brawl(R,opps,variants,ngames=250,life=25,maxturn=16,seed=555):
    inp=[str(len(R.defs))]
    for e in R.defs: inp.append(R.line(e))
    inp.append(str(len(opps)))
    for dn,w,cmd,ids in opps:
        inp.append(f"{w} {cmd} {len(ids)} " + ' '.join(map(str,ids)))
    inp.append(f"{ngames} {life} {maxturn} {seed}")
    inp.append(str(len(variants)))
    for cmd,v in variants:
        inp.append(f"{cmd} {len(v)} " + ' '.join(map(str,v)))
    import os as _os
    o=subprocess.run(['./bin_brawl'],input='\n'.join(inp),capture_output=True,text=True,env=dict(_os.environ))
    if o.returncode!=0: raise RuntimeError(o.stderr[:400])
    rows=[l.split() for l in o.stdout.strip().split('\n') if l.strip()]
    K=['wr','noplay14','screw','spells6','firstplay','gamelen','cast','removal','kills',
       'sweep','counters','handend','manascrew','cseen','untap_at_counter','res_avg',
       'win_dmg','lose_dmg','timeout',
       'hA3','hA6','hA9','hB3','hB6','hB9','disc_try','disc_hit','disc_handsz']
    out=[]
    for r in rows:
        d={'wr':int(r[0])/1e6}
        for i,k in enumerate(K[1:],start=1): d[k]=float(r[i]) if i<len(r) else 0.0
        out.append(d)
    return out

def objective(r): return r['wr'] - 0.030*r['noplay14'] - 0.020*max(0.0,r['firstplay']-2.0)

def my_pool(R):
    """cartas propias legales en brawl, con su identidad de color"""
    out=[]
    for c in json.load(open('data/pool.json')):
        e=convert(c)
        if not e['legal_brawl']: continue
        i=R.add(c)
        out.append(dict(idx=i, e=e, name=c['name'], ci=CI(e), typ=e['typ'], cmc=e['cmc'],
                        legend='Legendary' in (c['type_line'] or ''),
                        iscrea=e['typ']==1, ispw=e['typ']==5))
    return out

def sc(e):
    s=0
    if e['typ']==1: s=e['power']*3+e['tough']*2
    kw=e['kw']
    for bit,b in [(1,4),(2,4),(8,2),(4,2),(64,2),(256,2),(32,1)]:
        if kw&bit: s+=b
    bonus={7:14,21:14,8:12,9:18,3:6,20:14,12:14,10:10,11:8,2:6,16:4,13:12,24:5,25:4,27:5,26:4,28:3,15:11,23:9,22:6,5:5,17:2}
    s+=bonus.get(e['eff'],0)+bonus.get(e['eff2'],0)//2
    return s-e['cmc']

CURVE={1:0.08,2:0.26,3:0.26,4:0.20,5:0.11,6:0.06,7:0.03}
def seed_deck(pool, cmdci, nspell):
    ok=[p for p in pool if p['ci']<=cmdci and p['typ']!=6]
    by={}
    for p in ok: by.setdefault(min(p['cmc'],7),[]).append(p)
    for k in by: by[k].sort(key=lambda p:-sc(p['e']))
    chosen=[]; used=set()
    for band,frac in sorted(CURVE.items()):
        want=int(round(nspell*frac))
        for p in by.get(band,[]):
            if want<=0 or len(chosen)>=nspell: break
            if p['idx'] in used: continue
            chosen.append(p); used.add(p['idx']); want-=1
    rest=sorted([p for p in ok if p['idx'] not in used], key=lambda p:-sc(p['e']))
    for p in rest:
        if len(chosen)>=nspell: break
        chosen.append(p); used.add(p['idx'])
    return [p['idx'] for p in chosen]

def lands_brawl(R, pool, cmdci, n):
    ids=[]
    for p in pool:
        if p['typ']!=6: continue
        if not p['ci']<=cmdci: continue
        if not p['e']['produces']: continue          # Hobbit Hole no produce mana
        ids.append(p['idx'])
    ids=ids[:max(0,n-len(cmdci))]
    cols=sorted(cmdci) or ['B']
    rest=n-len(ids); per=rest//len(cols); ex=rest-per*len(cols)
    for k,c in enumerate(cols): ids += [R.add_by_name(BASICS[c])]*(per+(1 if k<ex else 0))
    return ids
