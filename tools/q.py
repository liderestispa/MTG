import json, re, sys, os
CUT="2026-08-15"
IDX="/home/claude/mtg/tools/sb_pool.json"

def build():
    best={}
    for line in open('/home/claude/mtg/data/oracle.jsonl'):
        c=json.loads(line)
        if c['legalities'].get('standardbrawl')!='legal': continue
        if (c.get('released_at') or '9999') > CUT: continue
        if 'arena' not in (c.get('games') or []): continue
        nm=c['name']
        rec={'name':nm,'mc':c.get('mana_cost',''),'cmc':c.get('cmc',0),
             'type':c.get('type_line',''),'text':c.get('oracle_text',''),
             'colors':''.join(c.get('color_identity',[])),'set':c.get('set'),
             'setname':c.get('set_name'),'rarity':c.get('rarity'),
             'power':c.get('power'),'tough':c.get('toughness'),
             'rel':c.get('released_at'),'usd':(c.get('prices') or {}).get('usd')}
        if 'card_faces' in c and not rec['text']:
            f=c['card_faces']
            rec['text']='\n//\n'.join(x.get('oracle_text','') for x in f)
            rec['mc']=' // '.join(x.get('mana_cost','') for x in f if x.get('mana_cost'))
            rec['type']=' // '.join(x.get('type_line','') for x in f)
        if nm not in best or rec['rel']<best[nm]['rel']: best[nm]=rec
    json.dump(list(best.values()),open(IDX,'w'))
    return list(best.values())

def load():
    if not os.path.exists(IDX): return build()
    return json.load(open(IDX))

if __name__=='__main__':
    P=load()
    if sys.argv[1]=='build': print('built',len(P)); sys.exit()
    mode=sys.argv[1]; pat=sys.argv[2]
    ci=sys.argv[3] if len(sys.argv)>3 else None
    rx=re.compile(pat,re.I)
    out=[]
    for c in P:
        hay=c['text'] if mode=='text' else (c['name'] if mode=='name' else c['text']+' '+c['type']+' '+c['name'])
        if not rx.search(hay or ''): continue
        if ci and not set(c['colors'])<=set(ci): continue
        out.append(c)
    out.sort(key=lambda x:(x['cmc'],x['name']))
    for c in out:
        t=(c['text'] or '').replace('\n',' | ')
        print(f"[{c['mc']:12}] {c['name']}  ({c['type']}) <{c['set']} {c['rarity'][:1]} ${c['usd']}>\n    {t[:300]}")
    print(f"--- {len(out)} results")
