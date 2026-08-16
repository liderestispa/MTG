import json,re,sys
P=json.load(open('/home/claude/mtg/tools/sb_pool.json'))
pat=re.compile(sys.argv[1],re.I)
for c in sorted(P,key=lambda x:(x['cmc'],x['name'])):
    t=c['type']
    if 'Legendary' not in t: continue
    if not ('Creature' in t or 'Planeswalker' in t): continue
    if not pat.search(c['text'] or ''): continue
    print(f"[{c['mc']:12}] {c['name']} ({c['colors'] or 'C'}) <{c['set']} ${c['usd']}>\n    {(c['text'] or '').replace(chr(10),' | ')[:340]}")
