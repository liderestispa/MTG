import json, sys, unicodedata
sys.path.insert(0,'src'); sys.path.insert(0,'data')
from extract import convert
from meta_decks import DECKS

def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii','ignore').decode().lower()
    return ''.join(ch for ch in s if ch.isalnum())

ORACLE = {}
FRONT  = {}
for line in open('data/oracle.jsonl'):
    c = json.loads(line)
    ORACLE.setdefault(norm(c['name']), c)
    if '//' in c['name']:
        FRONT.setdefault(norm(c['name'].split('//')[0]), c)

def lookup(name):
    k = norm(name)
    return ORACLE.get(k) or FRONT.get(k)

missing = []
need = {}
for fmt, ds in DECKS.items():
    for dn, w, cs in ds:
        for n, name in cs:
            c = lookup(name)
            if c is None: missing.append((fmt, dn, name))
            else: need[c['oracle_id']] = c

print(f"cartas del meta resueltas: {len(need)}  |  sin resolver: {len(missing)}")
for f,d,n in missing: print(f"   ❌ {f}/{d}: {n}")
json.dump({'ok':len(need),'missing':missing}, open('data/registry_check.json','w'))
