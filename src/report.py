import sys, json; sys.path.insert(0,'src'); sys.path.insert(0,'data')
from driver import lookup

def fmt_deck(counts_by_name, lands, title):
    rows=[]
    for name,n in counts_by_name.items():
        c=lookup(name)
        tl=(c.get('type_line') or '')
        mc=c.get('mana_cost') or (c.get('card_faces') or [{}])[0].get('mana_cost') or ''
        cmc=int(c.get('cmc') or 0)
        rows.append((cmc, name, n, mc, tl))
    rows.sort(key=lambda r:(r[0], r[1]))
    out=[f"### {title}\n", "| Cant | Coste | Carta | Tipo |","|---|---|---|---|"]
    cur=None
    for cmc,name,n,mc,tl in rows:
        if cmc!=cur:
            out.append(f"| | | **— {cmc} maná —** | |"); cur=cmc
        t=tl.split('—')[0].strip()
        out.append(f"| {n} | {mc} | **{name}** | {t} |")
    from collections import Counter
    lc=Counter(lands)
    out.append("")
    out.append("**Tierras (%d):** " % len(lands) + " · ".join(f"{v} {k}" for k,v in lc.most_common()))
    return "\n".join(out)
