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
from extract import convert
from auditoria_lectura import sospechas, texto
import re as _re

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




def bien_leida(c):
    """¿El motor entiende esta carta lo bastante como para fiarse de la medicion?

    Sin este filtro el barrido recomienda las cartas MAS MAL LEIDAS, no las mejores:
    ordena por mejora medida y el error de medida es maximo donde la lectura es
    equivocada y generosa. Se rechaza si el auditor tiene alguna sospecha, si quedan
    frases de juego sin ranura, o si el texto tiene marcas de inconveniente que el motor
    no modela."""
    try:
        e = convert(c)
    except Exception:
        return False, 'no se pudo convertir'
    if sospechas(c, e):
        return False, 'el auditor la marca'
    t = _re.sub(r'\([^)]*\)', '', texto(c) or '').lower()

    # inconvenientes que el motor NO modela y que lo harian sobrevalorarla
    CONTRAS = [
        (r'target opponent creates|opponent creates',   'le regala criaturas al rival'),
        (r'\bdecayed\b',                                'Decayed: no bloquea y se sacrifica'),
        (r"can't block\b",                              'no puede bloquear'),
        (r'activate only if you control',               'condicion de activacion no modelada'),
        (r'\bkicker\b|if it was kicked',                'kicker: el motor no paga el extra'),
        (r'as an additional cost',                      'coste adicional no cobrado'),
        (r'enters tapped',                              'entra girada, y eso esta apagado'),
        (r'\bflashback\b|from your graveyard',          'cementerio: se lee de mas'),
        (r'sacrifice it at end of combat|at end of combat, sacrifice', 'se sacrifica sola'),
        (r'you lose \d+ life|lose \d+ life at',          'coste en vidas no modelado'),
        (r'\bvoid\b —|\bvoid\b -',                      'Void: condicion no modelada'),
        (r'charge counter',                             'contadores de carga no modelados'),
    ]
    for rx, motivo in CONTRAS:
        if _re.search(rx, t):
            return False, motivo

    # ---- mana con coste: el motor lo regala ----
    # mana_out no distingue "{T}: anade" de "{1},{T}: anade" ni de "gira una criatura".
    # Springleaf Drum y Prophetic Prism salian como fuentes de 2 mana gratis.
    if e.get('mana_out'):
        _linea = next((l for l in t.split('\n') if _re.search(r':\s*add ', l)), '')
        _coste = _linea.split(':')[0] if ':' in _linea else ''
        if _re.search(r'\{\d+\}|tap an untapped|sacrifice|discard|pay ', _coste):
            return False, 'su mana tiene coste y el motor lo da gratis'

    # ---- disparo de ataque contado dos veces ----
    # Si la carta dispara AL ATACAR, su ranura de entrada tiene que estar vacia. Pulse
    # Tracker drenaba al entrar Y al atacar.
    if _re.search(r'whenever [^.\n]{0,30}attacks', t) and e.get('eff'):
        return False, 'dispara al atacar y ademas ocupa la ranura de entrada'

    # frases con verbo de juego que no tienen ranura: la carta hace mas de lo que se lee.
    # OJO: las lineas de palabras clave ya se excluyen del recuento de frases, asi que kw
    # NO puede sumar como ranura; si sumaba, el 'volar' de Desecration Demon tapaba la
    # frase de su inconveniente y la carta pasaba el filtro.
    ranuras = sum(1 for k in ('eff', 'eff2', 'eff3') if e.get(k))
    ranuras += sum(1 for k in ('die_eff', 'act_eff', 'atk_eff', 'adv_eff', 'saga_n',
                               'dyn', 'alt', 'cred', 'cond', 'mana_out') if e.get(k))
    frases = 0
    for l in t.split('\n'):
        l = l.strip()
        if not l: continue
        if _re.match(r"^[\w\s,'-]+$", l) and len(l.split()) <= 6 and ':' not in l: continue
        frases += 1
    if frases > ranuras:
        return False, f'{frases} frases y {ranuras} ranuras: se lee a medias'
    return True, ''


RECHAZADAS = []


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
        ok, _motivo = bien_leida(c)
        if not ok:
            RECHAZADAS.append((c['name'], _motivo)); continue
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

    # ---- validacion ----
    # El barrido mide con UNA semilla: sirve para ordenar, no para decidir. El top se
    # re-mide con tres y mas partidas, igual que hace el laboratorio con las hipotesis.
    print(f"\n{'='*74}\nVALIDACION DEL TOP 15 (3 semillas, {NG_FINAL} partidas)\n{'='*74}")
    print(f"{'barrido':>8} {'validado':>9} {'USD':>7}  carta")
    validadas = []
    for d, p, n, mc, t in filas[:15]:
        v = mide(resto + [n], NG_FINAL, SEMILLAS) - base
        validadas.append((v, p, n, mc))
        marca = '' if abs(v - d) < 1.5 else '   <- el barrido exageraba'
        print(f"{d:+8.2f} {v:+9.2f} {p:7.2f}  {n[:32]:<34}{marca}")
    validadas.sort(reverse=True)
    json.dump([dict(mejora=v, usd=p, carta=n, coste=mc) for v, p, n, mc in validadas],
              io.open('out/compras_validadas.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    print(f"\n{'='*74}\nMEJOR RELACION MEJORA/PRECIO (solo las que suben)\n{'='*74}")
    porusd = sorted([f for f in filas if f[0] > 0], key=lambda x: -x[0]/max(x[1], 0.01))
    for d, p, n, mc, t in porusd[:15]:
        print(f"{d:+7.2f} {p:7.2f} {d/max(p,0.01):8.2f}  {n[:34]:<36} {mc}")
    print(f"\n{len(RECHAZADAS)} cartas descartadas por no leerse bien. Las mas caras que se pierden:")
    for nm, mv in RECHAZADAS[:8]:
        print(f"   {nm[:36]:<38} {mv}")
    print(f"\nescrito out/compras_brawl.json y out/compras_validadas.json"
          f"   ({(time.time()-t0)/60:.0f} min)")


if __name__ == '__main__':
    main()
