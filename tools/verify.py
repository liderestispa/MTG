import json,sys,re
P=json.load(open('/home/claude/mtg/tools/sb_pool.json'))
byname={c['name']:c for c in P}
# also index by front face name
front={}
for c in P:
    front.setdefault(c['name'].split(' // ')[0],c)
def check(path):
    lines=[l.strip() for l in open(path) if l.strip() and not l.startswith('#')]
    tot=0; bad=[]; ok=[]
    for l in lines:
        m=re.match(r'^(\d+)x?\s+(.*)$',l)
        n,nm=(int(m.group(1)),m.group(2).strip()) if m else (1,l)
        tot+=n
        c=byname.get(nm) or front.get(nm)
        if c: ok.append((n,c))
        else: bad.append(nm)
    print(f"=== {path}: TOTAL {tot} cards ===")
    if bad:
        print("!! NOT IN STANDARD BRAWL POOL:")
        for b in bad: print("   -",b)
    else: print("all names verified in pool")
    # price
    tp=0
    for n,c in ok:
        try: tp+=float(c['usd'] or 0)*n
        except: pass
    print(f"verified {len(ok)} entries; approx USD (paper) ${tp:.2f}")
    return bad
for p in sys.argv[1:]: check(p)
