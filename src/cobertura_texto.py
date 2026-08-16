# -*- coding: utf-8 -*-
"""Genera la cola de trabajo: texto de carta que el extractor no entiende.

Todo lo que se gano en las ultimas campanas siguio el mismo bucle: encontrar una carta
cuyo texto el motor no lee, escribir la regla, medir, validar con semillas. Encontrar
esas cartas no necesita criterio, solo recorrer el banco y mirar quien salio en blanco.
Esto hace esa parte, y la deja ordenada por cuanto pesa.

Tres categorias, de mas grave a menos:

  BLANCA   la carta tiene texto de reglas y el extractor no le asigno NINGUN efecto.
           Es la trampa 8 de docs/trampas.md. En un mazo, cada copia es una carta que
           el motor juega como si no hiciera nada, y a veces peor: la lanza igual y
           gasta el mana.
  PARCIAL  tiene mas frases con verbo de juego que ranuras de efecto ocupadas. Puede
           ser agotamiento de ranuras (solo hay tres) o una mecanica que falta.
  RANURAS  ocupa las tres ranuras y aun le sobran frases: eso NO se arregla con una
           regla nueva, es un limite del formato. Se lista aparte para no perder tiempo.

    python3 src/cobertura_texto.py            # banco de calibracion
    python3 src/cobertura_texto.py coleccion  # las cartas de Ricardo
"""
import sys, re, json, io
sys.path.insert(0, 'src'); sys.path.insert(0, 'data')
from driver import lookup
from extract import convert, E

# Frases que no aportan mecanica y no cuentan como "sin cubrir".
# Las habilidades de mana van aqui a proposito: una tierra con "{T}: Add {R}" tiene
# eff=NONE y aun asi esta bien modelada, porque el motor la lee por 'produces' y
# 'mana_out', no por ranura de efecto. Sin este filtro la cola sale enterrada en
# tierras y no se ve lo que importa.
RUIDO = re.compile(
    r'^\s*(\(|flying$|first strike$|trample$|haste$|vigilance$|deathtouch$|lifelink$|'
    r'reach$|menace$|defender$|flash$|hexproof$|indestructible$|prowess$|ward\b)', re.I)
MANA_SOLO = re.compile(
    r'^\s*\{t\}\s*(,[^:]*)?:\s*add\b[^.]*\.?\s*$|'
    r'^\s*\{t\}\s*,\s*pay \d+ life\s*:\s*add\b[^.]*\.?\s*$', re.I)
VERBO = re.compile(
    r'\b(draw|deals?|destroy|exile|return|create|gain|lose|discard|search|counter|'
    r'sacrifice|add|untap|tap|put|target|whenever|when|at the beginning|prevent|'
    r'shuffle|reveal|mill|scry|surveil|copy|transform)\b', re.I)


def frases(txt):
    fuera = re.sub(r'\([^)]*\)', '', txt or '')
    out = []
    for linea in fuera.split('\n'):
        for f in re.split(r'(?<=[.;])\s+', linea):
            f = f.strip()
            if len(f) < 8 or RUIDO.match(f) or MANA_SOLO.match(f): continue
            if VERBO.search(f): out.append(f)
    return out


def analiza(nombre, copias, donde):
    c = lookup(nombre)
    if not c: return None
    txt = c.get('oracle_text') or ''
    tl = c.get('type_line') or ''
    if 'Basic Land' in tl: return None
    fs = frases(txt)
    if not fs: return None
    e = convert(c)
    usadas = sum(1 for k in ('eff', 'eff2', 'eff3') if e[k] != E['NONE'])
    if usadas == 0:      cat = 'BLANCA'
    elif usadas >= 3 and len(fs) > 3: cat = 'RANURAS'
    elif len(fs) > usadas:            cat = 'PARCIAL'
    else: return None
    return dict(carta=nombre, copias=copias, donde=sorted(donde), categoria=cat,
                frases=len(fs), ranuras=usadas, tipo=tl,
                texto=' | '.join(fs)[:220],
                efectos=[e['eff'], e['eff2'], e['eff3']])


def del_banco():
    from meta_decks import DECKS
    acc = {}
    for fmt, decks in DECKS.items():
        for dn, w, cs in decks:
            for n, name in cs:
                k = acc.setdefault(name, [0, set()])
                k[0] += n; k[1].add(f'{fmt}/{dn}')
    return [(name, v[0], v[1]) for name, v in acc.items()]


def de_coleccion():
    pool = json.load(io.open('data/pool.json', encoding='utf-8'))
    return [(c['name'], c.get('qty', 1), {'coleccion'}) for c in pool]


if __name__ == '__main__':
    fuente = sys.argv[1] if len(sys.argv) > 1 else 'banco'
    cartas = de_coleccion() if fuente.startswith('col') else del_banco()
    filas = [r for r in (analiza(*c) for c in cartas) if r]
    orden = {'BLANCA': 0, 'PARCIAL': 1, 'RANURAS': 2}
    filas.sort(key=lambda r: (orden[r['categoria']], -r['copias'], -r['frases']))

    for cat in ('BLANCA', 'PARCIAL', 'RANURAS'):
        sub = [r for r in filas if r['categoria'] == cat]
        if not sub: continue
        print(f"\n{'='*78}\n{cat}  ({len(sub)} cartas, {sum(r['copias'] for r in sub)} copias)\n{'='*78}")
        for r in sub[:25]:
            print(f"  {r['copias']:>3}x {r['carta'][:34]:<36} {r['frases']} frases / "
                  f"{r['ranuras']} ranuras   {','.join(r['donde'])[:34]}")
            print(f"        {r['texto'][:150]}")
        if len(sub) > 25: print(f"  ... y {len(sub)-25} mas")

    salida = f"out/cobertura_{'coleccion' if fuente.startswith('col') else 'banco'}.json"
    json.dump(filas, io.open(salida, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    blancas = sum(r['copias'] for r in filas if r['categoria'] == 'BLANCA')
    print(f"\nescrito {salida}")
    print(f"{blancas} copias del banco son cartas EN BLANCO para el motor. "
          f"Esa es la cola de trabajo, por orden.")
