# -*- coding: utf-8 -*-
"""Busca cartas que el motor lee MAL. No las que no lee: esas ya las lista cobertura_texto.

POR QUE HACE FALTA, Y CUANTO COSTO NO TENERLO

src/cobertura_texto.py encuentra cartas en blanco: el extractor no les puso ningun efecto.
Eso es facil de ver y facil de arreglar. Lo que nadie estaba mirando es el caso contrario y
mas peligroso: la carta SI tiene efecto, el efecto es plausible, y esta mal.

El caso que lo destapo fue Dain, Lord of the Iron Hills, el comandante que el buscador
elegia para Standard Brawl. Su texto dice que las criaturas no pueden ATACARTE salvo que
paguen {1} por cada una, y solo mientras tengas Storied (tres artefactos, legendarias o
Sagas). El motor lo modelaba como un impuesto a los HECHIZOS del rival, y SIN la
condicion. Medido: quitando ese impuesto el mazo cae de 51,0% a 34,2%. Dos tercios de su
nota venian de un efecto que la carta no tiene.

Una carta en blanco te hace perder valor. Una carta mal leida te hace CONSTRUIR EL MAZO
EQUIVOCADO, y encima con confianza.

LAS SOSPECHAS QUE BUSCA

Ninguna es prueba: son motivos para ir a mirar. El juicio sigue siendo humano.

  COND_SIEMPRE   el efecto tiene condicion en el texto y el motor lo aplica siempre.
                 E_COND_BUFF se llama condicional y sim.c lo suma sin mirar nada
                 (lineas 1271, 1357, 1433). Lo mismo E_TAX (linea 1060).
  TAX_ATAQUE     el texto grava ATACAR y el motor grava LANZAR. Son efectos distintos:
                 uno castiga solo a los mazos agresivos, el otro a todo el mundo.
  SALIR_COMO_ENTRAR  el disparo es al morir o al irse y el motor lo pone al entrar. Cambia
                 el tempo entero, que es justo lo que el motor mide.
  MODAL_TODO     "elige uno" o "la primera vez / la segunda vez", y el motor lleno varias
                 ranuras: se disparan TODAS a la vez.
  ACTIVADA_GRATIS  hay un coste de activacion en el texto y el motor la ejecuta sola y
                 gratis. Es el error de Krark-Clan Shaman, que ya costo una campana.
  KW_PERDIDA     la palabra clave esta en el texto y no en el campo kw.
  SIMETRICO      el texto afecta a los dos jugadores y el motor solo castiga al rival.

    python3 src/auditoria_lectura.py             # banco + coleccion
    python3 src/auditoria_lectura.py banco       # solo el banco de calibracion
    python3 src/auditoria_lectura.py mazos       # solo las cartas de los mazos elegidos
"""
import sys, io, os, re, json
from collections import Counter
sys.path.insert(0, 'src'); sys.path.insert(0, 'data')
from driver import lookup, norm
from extract import convert, E, KWBIT

INV = {v: k for k, v in E.items()}

# efectos que el motor dispara AL ENTRAR
ETB = {E['ETB_DMG'], E['ETB_DRAIN'], E['ETB_DRAW'], E['ETB_DISCARD'], E['ETB_TOKEN'],
       E['ETB_COUNTERS'], E['ETB_MANA'], E['LIFEGAIN'], E['TREASURE']}
# efectos que el motor trata como estaticos y aplica sin condicion
ESTATICOS = {E['COND_BUFF'], E['TAX'], E['LORD']}

_COND = re.compile(
    r'as long as|if you control|whenever this creature attacks|storied|'
    r'metalcraft|threshold|delirium|as long as you|only if|'
    r'if there are|if you have|while you|for each ', re.I)
_SALE = re.compile(r'when(?:ever)? (?:this|[^,.]{0,28}) (?:leaves the battlefield|dies)', re.I)
_ENTRA = re.compile(r'when(?:ever)? (?:this|[^,.]{0,28}) enters', re.I)
_MODAL = re.compile(r'choose one|choose up to one|choose two|'
                    r'if this is the (?:first|second|third) time', re.I)
_ACTIVADA = re.compile(r'(?:^|\n)\s*(?:\{[^}]+\}[,\s]*)+[^:\n]{0,40}:', re.M)
_TAX_ATK = re.compile(r"can't attack .{0,40}unless|attacks? .{0,30}unless .{0,20}pays?|"
                      r"cost[s]? \{?\d?\}? more to attack", re.I)
_SIMETRICO = re.compile(r'each player|all creatures|each creature|players can\'t|'
                        r'no player|each opponent and you', re.I)


def texto(c):
    t = c.get('oracle_text') or ''
    if c.get('card_faces'):
        t = '\n'.join(f.get('oracle_text', '') for f in c['card_faces'])
    return t


def sospechas(c, e):
    """Lista de (etiqueta, explicacion) para una carta."""
    t = texto(c)
    if not t:
        return []
    low = re.sub(r'\([^)]*\)', '', t.lower())     # fuera el texto recordatorio
    ranuras = [e['eff'], e['eff2'], e.get('eff3', 0)]
    llenas = [x for x in ranuras if x]
    out = []

    # Ojo: estas dos ya NO son sospechas si el extractor las etiqueto. Sin esta guarda,
    # el detector seguia listando a Dain y a Ori despues de arreglarlos, y la cola de
    # trabajo mentia diciendo que quedaba trabajo hecho.
    if set(ranuras) & ESTATICOS and not e.get('cond'):
        m = _COND.search(low)
        if m:
            cual = ', '.join(INV[x] for x in ranuras if x in ESTATICOS)
            out.append(('COND_SIEMPRE',
                        f"{cual} lo aplica siempre, pero el texto lo condiciona "
                        f"a \"{m.group(0).strip()}\""))

    if E['TAX'] in ranuras and _TAX_ATK.search(low) and not e.get('tax_atk'):
        out.append(('TAX_ATAQUE',
                    "el texto grava ATACAR y E_TAX grava LANZAR hechizos"))

    # disparo al atacar que quedo en ranura de entrada, ahora que existe atk_eff
    if not e.get('atk_eff'):
        _ma = re.search(r'whenever (?:this creature|this|[\w\' ]{1,24}) attacks[^.\n]*', low)
        if _ma and set(llenas) & ETB:
            out.append(('ATACAR_COMO_ENTRAR',
                        f"el disparo es AL ATACAR y {', '.join(INV[x] for x in llenas if x in ETB)}"
                        f" esta en ranura de entrada"))

    if _SALE.search(low) and not e.get('die_eff'):
        if set(llenas) & ETB:
            cual = ', '.join(INV[x] for x in llenas if x in ETB)
            out.append(('SALIR_COMO_ENTRAR',
                        f"el disparo es al morir/irse y {cual} esta en ranura de entrada"))

    if _MODAL.search(low) and len(llenas) >= 2:
        out.append(('MODAL_TODO',
                    f"texto modal y {len(llenas)} ranuras llenas "
                    f"({', '.join(INV[x] for x in llenas)}): se disparan todas juntas"))

    # COSTE ADICIONAL: no es una habilidad activada, asi que el filtro de activadas no lo
    # ve, y el efecto queda leido a precio de tapa. Stir Up Trouble pide sacrificar un
    # artefacto o criatura O pagar {4} ademas de su {B}, y el motor tenia un Doom Blade
    # de un mana. Tres copias, en el mazo de Pauper que se le recomendo a Ricardo.
    # "you may blight 1" / "you may collect evidence 6" son OPCIONALES: no pagarlas
    # es legal, asi que leerlas gratis no es un error. Solo cuentan las obligatorias.
    if re.search(r'as an additional cost to cast(?![^.]*you may)', low) and llenas:
        _m = re.search(r'as an additional cost to cast[^.]{0,80}', low)
        out.append(('COSTE_ADICIONAL',
                    f"el coste adicional no se cobra: \"{_m.group(0)[:70].strip()}\""))

    if _ACTIVADA.search(t) and llenas and not e.get('act_eff'):
        # las de solo mana ya se descartan en cobertura_texto; aqui filtramos igual
        if not re.search(r':\s*add \{', low):
            out.append(('ACTIVADA_GRATIS',
                        "hay coste de activacion en el texto y el efecto esta en ranura "
                        "libre: el motor lo ejecuta solo y sin pagar"))

    for nombre, bit in KWBIT.items():
        if re.search(r'\b' + re.escape(nombre.lower()) + r'\b', low) and not (e['kw'] & bit):
            # "flying" aparece en "creatures with flying" sin que la carta vuele
            if re.search(r'(with|without|gains?|have|has) ' + re.escape(nombre.lower()), low):
                continue
            out.append(('KW_PERDIDA', f"'{nombre}' esta en el texto y no en kw"))

    if _SIMETRICO.search(low) and llenas:
        unilaterales = {E['SWEEPER'], E['ETB_DISCARD'], E['ETB_DMG'], E['DMG_SPELL'],
                        E['LAND_KILL'], E['EDICT'], E['TAPDOWN']}
        if set(llenas) & unilaterales and not re.search(r'all other creatures', low):
            out.append(('SIMETRICO',
                        "el texto toca a los dos lados y el efecto solo castiga al rival"))
    return out


def del_banco():
    from meta_decks import DECKS
    acc = Counter(); donde = {}
    for fmt, mazos in DECKS.items():
        for dn, w, cs in mazos:
            for n, nombre in cs:
                acc[nombre] += n
                donde.setdefault(nombre, set()).add(f"{fmt}/{dn}")
    return acc, donde


def de_mazos():
    """Las cartas de los mazos que hoy le recomendamos a Ricardo."""
    acc = Counter(); donde = {}
    try:
        r = json.load(io.open('out/results.json', encoding='utf-8'))
        for fmt, d in r.items():
            for nombre, n in d['counts'].items():
                acc[nombre] += n; donde.setdefault(nombre, set()).add(f"mazo/{fmt}")
    except (OSError, ValueError, KeyError):
        pass
    try:
        b = json.load(io.open('out/brawl_result.json', encoding='utf-8'))
        for nombre in [b['commander']] + b['spells']:
            acc[nombre] += 1; donde.setdefault(nombre, set()).add('mazo/brawl')
    except (OSError, ValueError, KeyError):
        pass
    return acc, donde


def de_coleccion():
    acc = Counter(); donde = {}
    p = json.load(io.open('data/pool_eng.json', encoding='utf-8'))
    for c in (p if isinstance(p, list) else list(p.values())[0]):
        nombre = c.get('name')
        if nombre:
            acc[nombre] += c.get('qty', 1); donde.setdefault(nombre, set()).add('coleccion')
    return acc, donde


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else 'todo'
    fuentes = []
    if modo in ('todo', 'banco'):     fuentes.append(del_banco())
    if modo in ('todo', 'mazos'):     fuentes.append(de_mazos())
    if modo == 'todo':                fuentes.append(de_coleccion())

    acc = Counter(); donde = {}
    for a, d in fuentes:
        acc.update(a)
        for k, v in d.items(): donde.setdefault(k, set()).update(v)

    filas = []
    for nombre, copias in acc.items():
        c = lookup(nombre)
        if not c: continue
        try:
            e = convert(c)
        except Exception:
            continue
        s = sospechas(c, e)
        if s:
            filas.append(dict(carta=nombre, copias=copias, donde=sorted(donde[nombre]),
                              sospechas=[{'tipo': a, 'nota': b} for a, b in s],
                              texto=texto(c).replace('\n', ' | ')[:240],
                              motor=f"{INV.get(e['eff'])}/{INV.get(e['eff2'])}/"
                                    f"{INV.get(e.get('eff3',0))}"))

    # ordena por gravedad y despues por cuantas copias hay en juego
    GRAVEDAD = {'TAX_ATAQUE': 0, 'COND_SIEMPRE': 1, 'SALIR_COMO_ENTRAR': 2,
                'ATACAR_COMO_ENTRAR': 2, 'COSTE_ADICIONAL': 1,
                'ACTIVADA_GRATIS': 3, 'MODAL_TODO': 4, 'SIMETRICO': 5, 'KW_PERDIDA': 6}
    def clave(r):
        g = min(GRAVEDAD.get(x['tipo'], 9) for x in r['sospechas'])
        en_mazo = any(d.startswith('mazo/') for d in r['donde'])
        return (g, not en_mazo, -r['copias'])
    filas.sort(key=clave)

    porti = Counter(x['tipo'] for r in filas for x in r['sospechas'])
    print(f"{len(filas)} cartas con alguna sospecha, sobre {len(acc)} revisadas\n")
    for t, n in sorted(porti.items(), key=lambda kv: GRAVEDAD.get(kv[0], 9)):
        print(f"   {t:<20} {n}")
    print()
    for r in filas[:40]:
        marca = ' *EN UN MAZO NUESTRO*' if any(d.startswith('mazo/') for d in r['donde']) else ''
        print(f"{'='*78}\n{r['copias']}x {r['carta']}   [{r['motor']}]{marca}")
        print(f"   {', '.join(sorted(set(d for d in r['donde'])))[:100]}")
        for x in r['sospechas']:
            print(f"   -> {x['tipo']}: {x['nota']}")
        print(f"   texto: {r['texto'][:200]}")
    if len(filas) > 40:
        print(f"\n... y {len(filas)-40} mas en el JSON")

    salida = f"out/auditoria_lectura_{modo}.json"
    json.dump(filas, io.open(salida, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"\nescrito {salida}")


if __name__ == '__main__':
    main()
