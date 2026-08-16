import json,sys,re
P=json.load(open('/home/claude/mtg/tools/sb_pool.json'))
byname={c['name']:c for c in P}
front={}
for c in P: front.setdefault(c['name'].split(' // ')[0],c)
BASICS={'Plains','Swamp','Island','Mountain','Forest','Wastes'}
def get(nm): return byname.get(nm) or front.get(nm)
def check(path,ci):
    lines=[l.strip() for l in open(path) if l.strip() and not l.startswith('#')]
    tot=0;bad=[];ciBad=[];fut=[];price=0.0;cmcs=[];lands=0
    cmdr=None
    for i,l in enumerate(lines):
        m=re.match(r'^(\d+)x?\s+(.*)$',l)
        n,nm=(int(m.group(1)),m.group(2).strip()) if m else (1,l)
        tot+=n
        c=get(nm)
        if not c: bad.append(nm); continue
        if i==0: cmdr=c
        if not set(c['colors'])<=set(ci): ciBad.append((nm,c['colors']))
        if c['future_only'] and nm not in BASICS: fut.append(nm)
        try: price+=float(c['usd'] or 0)*n
        except: pass
        if 'Land' in c['type']: lands+=n
        elif i>0: cmcs.extend([c['cmc']]*n)
    print(f"### {path}")
    print(f"  TOTAL CARDS: {tot}  {'OK (60)' if tot==60 else '*** WRONG, must be 60 ***'}")
    print(f"  lands={lands}  nonland spells={tot-lands-1}  avg CMC(spells)={sum(cmcs)/len(cmcs):.2f}")
    print(f"  approx paper USD: ${price:.2f}")
    if bad: print("  !! NAMES NOT IN POOL:",bad)
    if ciBad: print("  !! COLOR IDENTITY VIOLATION (outside "+ci+"):",ciBad)
    if fut: print("  !! only printing is a post-Aug-2026 set (verify):",fut)
    if not bad and not ciBad: print("  >> all names legal & within color identity")
check(sys.argv[1],sys.argv[2])
