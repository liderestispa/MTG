import csv, json, collections

prints = json.load(open('data/ricardo_sets2.json'))
byid = {c['id']: c for c in prints}
# best English print per oracle_id, for authoritative English text
en_by_oracle = {}
for c in prints:
    if c.get('lang') == 'en' and c.get('oracle_id'):
        en_by_oracle.setdefault(c['oracle_id'], c)

rows = list(csv.DictReader(open('data/collection.csv', encoding='utf-8-sig')))
G = lambda d, k: d.get(k) if d.get(k) is not None else None

pool = {}
for r in rows:
    c = byid[r['Scryfall ID'].strip()]
    oid = c.get('oracle_id')
    src = en_by_oracle.get(oid, c)          # English print wins for card data
    q = int(r['quantity'])
    if oid not in pool:
        pool[oid] = {
            'oracle_id': oid, 'name': src['name'], 'qty': 0,
            'mana_cost': G(src,'mana_cost'), 'cmc': G(src,'cmc'),
            'type_line': G(src,'type_line'), 'oracle_text': G(src,'oracle_text'),
            'power': G(src,'power'), 'toughness': G(src,'toughness'), 'loyalty': G(src,'loyalty'),
            'colors': G(src,'colors') or [], 'color_identity': G(src,'color_identity') or [],
            'keywords': G(src,'keywords') or [], 'produced_mana': G(src,'produced_mana'),
            'legalities': G(src,'legalities') or {}, 'layout': G(src,'layout'),
            'card_faces': G(src,'card_faces') or [], 'rarity': G(src,'rarity'),
            'usd': G(src,'usd'), 'rows': [],
        }
    pool[oid]['qty'] += q
    pool[oid]['rows'].append({'csv_name': r['Card name'], 'lang': c.get('lang'), 'set': c['set'], 'qty': q})

cards = sorted(pool.values(), key=lambda x: (-x['qty'], x['name']))
json.dump(cards, open('data/pool.json','w'), ensure_ascii=False, indent=0)

print(f"cartas distintas: {len(cards)}   copias fisicas: {sum(c['qty'] for c in cards)}")

merged = [c for c in cards if len({r['lang'] for r in c['rows']}) > 1]
print(f"\ncartas que tenias en ingles Y espanol (se fusionaron): {len(merged)}")
for c in merged[:12]:
    langs = '+'.join(sorted({r['lang'] for r in c['rows']}))
    print(f"   {c['name'][:44]:<46} x{c['qty']:<3} [{langs}]")

print("\n=== legalidad por formato (cartas distintas) ===")
for f in ['standard','pauper','brawl','commander','pioneer','modern']:
    n = sum(1 for c in cards if c['legalities'].get(f) == 'legal')
    print(f"   {f:<11} {n:>3} / {len(cards)}")

print("\n=== top 20 por copias ===")
for c in cards[:20]:
    t = c['type_line'].split('—')[0].strip() if c['type_line'] else '?'
    print(f"   x{c['qty']:<3} {c['name'][:40]:<42} {str(c['mana_cost']):<12} {t[:22]:<24} {c['rarity'][:1].upper()}")
