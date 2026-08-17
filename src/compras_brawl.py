# -*- coding: utf-8 -*-
"""Lista de compras para el mazo de Standard Brawl: que carta comprar y cuanto sube.

Distinto de src/upgrade.py, que solo cubre Standard y Pauper y no sabe de comandantes ni
de singleton. Aqui:

  1. Se mide QUE CARTA DEL MAZO SOBRA, dejando cada una fuera por turno (leave-one-out).
     Sin eso no se sabe contra que comparar: una carta candidata no "suma", SUSTITUYE.
  2. Se barre el universo legal de Standard Brawl con identidad de color compatible, sin
     las que Ricardo ya tiene, y se prueba cada una en el hueco mas barato.
  3. Se ordena por mejora y por mejora POR DOLAR, que no dan el mismo orden.

Lo que NO hace: prometer que el numero se traduce en winrate real. En Brawl la escala se
niega a calibrar el nivel (n=2), asi que la mejora es una comparacion dentro del mismo
motor. Sirve para ordenar compras, no para predecir la tienda.

    python3 src/compras_brawl.py               # barrido completo, tope 25 USD
    python3 src/compras_brawl.py 8             # solo cartas de hasta 8 USD
    python3 src/compras_brawl.py 25 --rapido   # menos partidas, para tantear
"""
import sys, io, json, time
sys.path.insert(0, 'src'); sys.path.insert(0, 'data')
from driver import lookup, norm
from brawl import build_brawl, run_brawl, objective, my_pool

TOPE_USD = float(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1][0].isdigit() else 25.0
RAPIDO = '--rapido' in sys.argv
NG_SCAN = 500 if RAPIDO else 1200
NG_FINAL = 3000
SEMILLAS = [31337, 606060, 8112024]


def precio(c):
    p = (c.get('prices') or {})
    for k in ('usd', 'usd_foil'):
        if p.get(k):
            try: return float(p[k])
            except ValueError: pass
    return None


def candidatas(ci_mazo, tengo):
    """Legales en Standard Brawl, identidad compatible, que NO tenga ya, con precio."""
    out = []
    for linea in io.open('data/oracle.jsonl', encoding='utf-8'):
        c = json.loads(linea)
        if (c.get('legalities') or {}).get('standardbrawl') != 'legal': continue
        lay = (c.get('layout') or '')
        if 'token' in lay or lay in ('art_series', 'vanguard'): continue
        if (c.get('type_line') or '').startswith('Token'): continue
        if 'Land' in (c.get('type_line') or ''): continue      # la base de mana va aparte
        if not set(c.get('color_identity') or []) <= ci_mazo: continue
        if norm(c['name']) in tengo: continue
        p = precio(c)
        if p is None or p > TOPE_USD: continue
        out.append((c, p))
    # una entrada por nombre, la mas barata
    mejor = {}
    for c, p in out:
        k = norm(c['name'])
        if k not in mejor or p < mejor[k][1]: mejor[k] = (c, p)
    return list(mejor.values())


def main():
    b = json.load(io.open('out/brawl_result.json', encoding='utf-8'))
    R, opps = build_brawl()
    cmd = R.add_by_name(b['commander'])
    tierras = [R.add_by_name(n) for n in b['lands']]
    hechizos = list(b['spells'])

    def mide(nombres, ng, semillas):
        ids = [R.add_by_name(n) for n in nombres] + tierras
        v = [run_brawl(R, opps, [(cmd, ids)], ngames=ng, life=25, seed=s)[0]
             for s in semillas]
        return sum(objective(x) for x in v) / len(v) * 100

    t0 = time.time()
    base = mide(hechizos, NG_FINAL, SEMILLAS)
    print(f"mazo actual: {base:.2f}   ({b['commander']})\n")

    # ---- que carta sobra ----
    # Una candidata no suma, SUSTITUYE. Sin saber cual es el hueco mas barato no hay con
    # que comparar, y probar contra un hueco caro esconde mejoras reales.
    print("midiendo que carta sobra (leave-one-out)...", flush=True)
    fuera = []
    for nm in hechizos:
        resto = [x for x in hechizos if x != nm]
        # 34 cartas: se repite una para mantener el tamanio y no medir el efecto de
        # jugar con 59 en vez de 60
        v = mide(resto + [resto[0]], NG_SCAN, SEMILLAS[:1])
        fuera.append((v - base, nm))
    fuera.sort(reverse=True)
    print("  las que menos se echan de menos:")
    for d, nm in fuera[:6]:
        print(f"     {d:+6.2f}  {nm}")
    hueco = fuera[0][1]
    resto = [x for x in hechizos if x != hueco]
    print(f"\n  hueco de prueba: {hueco}\n")

    # ---- barrido ----
    tengo = {norm(p['name']) for p in my_pool(R)}
    cands = candidatas(set(b['ci']), tengo)
    print(f"{len(cands)} cartas candidatas hasta {TOPE_USD:.0f} USD. Barriendo...\n", flush=True)

    filas = []
    for i, (c, p) in enumerate(cands):
        try:
            v = mide(resto + [c['name']], NG_SCAN, SEMILLAS[:1])
        except Exception:
            continue
        filas.append((v - base, p, c['name'], c.get('mana_cost') or '',
                      (c.get('type_line') or '').split('—')[0].strip()))
        if (i + 1) % 50 == 0:
            print(f"   {i+1}/{len(cands)}  ({(time.time()-t0)/60:.0f} min)", flush=True)

    filas.sort(reverse=True)
    json.dump([dict(delta=d, usd=p, carta=n, coste=mc, tipo=t)
               for d, p, n, mc, t in filas],
              io.open('out/compras_brawl.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    print(f"\n{'='*74}\nLAS 25 QUE MAS SUBEN\n{'='*74}")
    print(f"{'mejora':>7} {'USD':>7} {'por USD':>8}  carta")
    for d, p, n, mc, t in filas[:25]:
        print(f"{d:+7.2f} {p:7.2f} {d/max(p,0.01):8.2f}  {n[:34]:<36} {mc}")

    print(f"\n{'='*74}\nMEJOR RELACION MEJORA/PRECIO (solo las que suben)\n{'='*74}")
    porusd = sorted([f for f in filas if f[0] > 0], key=lambda x: -x[0]/max(x[1], 0.01))
    for d, p, n, mc, t in porusd[:15]:
        print(f"{d:+7.2f} {p:7.2f} {d/max(p,0.01):8.2f}  {n[:34]:<36} {mc}")
    print(f"\nescrito out/compras_brawl.json   ({(time.time()-t0)/60:.0f} min)")


if __name__ == '__main__':
    main()
