# -*- coding: utf-8 -*-
"""Banco de pruebas sintetico: mazos artificiales que aislan UN comportamiento.

Para que existe. El objetivo contra dato real solo puede medir lo que el banco tiene.
Cuando se midieron los tres hallazgos que quedaban de data/errores_juego.md salio que en
los 19 mazos del banco hay 8 criaturas con amenaza, 1 con dano primero, 1 indestructible
y 4 copias de un solo lord. Un arreglo correcto sobre esa materia mide exactamente cero,
y "cero" ahi no significa "no sirve": significa "no medible con este banco".

Un sintetico separa las dos cosas. Aqui el arreglo o cambia el resultado o no lo cambia,
sin ruido de metajuego. Lo que el sintetico NO dice es si conviene adoptarlo: eso lo
sigue diciendo src/laboratorio.py contra dato real. Son preguntas distintas y hay que
responder las dos.

    python3 src/sintetico.py                 # corre todas las pruebas
    python3 src/sintetico.py amenaza         # solo las que empiecen por eso
"""
import sys, io, os
sys.path.insert(0, 'src'); sys.path.insert(0, 'data')
import driver
from driver import Registry, run
from extract import E, KWBIT

NG = 400
SEMILLA = 4242


def carta(**kw):
    """Def con todos los campos por defecto; se sobreescribe lo que interese."""
    d = dict(cmc=0, typ=1, colors=0, produces=0, gen=0, hybrid=False,
             pips=dict(W=0, U=0, B=0, R=0, G=0), kw=0, eff=0, eff2=0, eff3=0,
             p1=0, p2=0, p3=0, q1=0, q2=0, r1=0, r2=0, power=0, tough=0,
             mana_out=0, dyn=0, no_untap=0, alt=0, altn=0,
             die_eff=0, die_p1=0, act_eff=0, act_p1=0, act_cost=0, score=0)
    d.update(kw)
    return d


class Banco:
    """Registry sin Scryfall: las cartas se declaran a mano."""
    def __init__(self):
        self.defs = []
        self.meta = {}

    def add(self, nombre, **kw):
        i = len(self.defs)
        self.defs.append(carta(**kw))
        self.meta[i] = nombre
        return i

    line = Registry.line


MONTANA = dict(typ=6, produces=1 << 3, cmc=0)   # T_LAND, produce R


def mazo(*partes):
    ids = []
    for n, i in partes:
        ids += [i] * n
    return ids


def duelo(B, a, b, ng=NG, life=20, maxturn=20, seed=SEMILLA):
    """Winrate de 'a' contra 'b' y estadisticas del motor."""
    return run(B, [('rival', 1000, b)], [a], ng, life, maxturn, seed)[0]


def con(flags, fn):
    """Corre fn con esas variables de entorno puestas, y las deja como estaban."""
    viejo = {k: os.environ.get(k) for k in flags}
    os.environ.update({k: str(v) for k, v in flags.items()})
    try:
        return fn()
    finally:
        for k, v in viejo.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v


# --------------------------------------------------------------------------------
def prueba_amenaza():
    """Una criatura con amenaza frente a UN bloqueador es imbloqueable por reglas.
    Y en este motor, con GANG_ON=0, es imbloqueable frente a cualquier numero: la
    rama de bloqueo simple exige minb==1. Aun asi se quedaba en casa."""
    B = Banco()
    tierra = B.add('Montania', **MONTANA)
    simple = B.add('2/2 prisa', typ=1, cmc=2, gen=2, power=2, tough=2,
                   kw=KWBIT['Haste'])
    amenaza = B.add('2/2 prisa amenaza', typ=1, cmc=2, gen=2, power=2, tough=2,
                    kw=KWBIT['Haste'] | KWBIT['Menace'])
    muro = B.add('3/3', typ=1, cmc=3, gen=3, power=3, tough=3)
    rival = mazo((16, muro), (44, tierra))
    fila = []
    for nombre, cre in [('sin amenaza', simple), ('con amenaza', amenaza)]:
        for ka in (0, 1):
            r = con({'KW_ATAQUE': ka},
                    lambda: duelo(B, mazo((24, cre), (36, tierra)), rival))
            fila.append((nombre, ka, r['wr'], r['gamelen']))
    return 'amenaza: 2/2 prisa contra 16 muros 3/3', fila


def prueba_dano_primero():
    """Un 3/3 con dano primero gana el combate contra un 3/3 sin sufrir nada. El lado
    del bloqueo ya lo tenia en cuenta; el del ataque no, asi que el motor creia que iba
    a morir en un combate que el mismo resolveria a su favor."""
    B = Banco()
    tierra = B.add('Montania', **MONTANA)
    simple = B.add('3/3', typ=1, cmc=3, gen=3, power=3, tough=3)
    fs = B.add('3/3 dano primero', typ=1, cmc=3, gen=3, power=3, tough=3,
               kw=KWBIT['First strike'])
    muro = B.add('3/3 rival', typ=1, cmc=3, gen=3, power=3, tough=3)
    rival = mazo((16, muro), (44, tierra))
    fila = []
    for nombre, cre in [('sin dano primero', simple), ('con dano primero', fs)]:
        for ka in (0, 1):
            r = con({'KW_ATAQUE': ka},
                    lambda: duelo(B, mazo((24, cre), (36, tierra)), rival))
            fila.append((nombre, ka, r['wr'], r['gamelen']))
    return 'dano primero: 3/3 contra 16 criaturas 3/3', fila


def prueba_indestructible():
    """Una criatura indestructible no muere en combate nunca, asi que atacar con ella
    no puede costar la carta."""
    B = Banco()
    tierra = B.add('Montania', **MONTANA)
    simple = B.add('4/4', typ=1, cmc=4, gen=4, power=4, tough=4)
    ind = B.add('4/4 indestructible', typ=1, cmc=4, gen=4, power=4, tough=4,
                kw=KWBIT['Indestructible'])
    muro = B.add('6/6 rival', typ=1, cmc=6, gen=6, power=6, tough=6)
    rival = mazo((16, muro), (44, tierra))
    fila = []
    for nombre, cre in [('sin indestructible', simple), ('con indestructible', ind)]:
        for ka in (0, 1):
            r = con({'KW_ATAQUE': ka},
                    lambda: duelo(B, mazo((24, cre), (36, tierra)), rival))
            fila.append((nombre, ka, r['wr'], r['gamelen']))
    return 'indestructible: 4/4 contra 16 criaturas 6/6', fila


def prueba_lord():
    """A lanza "1 de dano a la criatura objetivo"; B tiene 1/1 con un lord +2/+2, o sea
    son 3/3. Deberia matar CERO. Se mira la estadistica 'kills', no el winrate: la
    pregunta es si la remocion se cree capaz de matar lo que no puede.

    El lord es un ENCANTAMIENTO a proposito. Como criatura se lo llevaba la propia
    remocion y entonces los 1/1 volvian a ser 1/1 y morian con razon, asi que la prueba
    medía una mezcla de las dos cosas. De encantamiento entra y se queda."""
    B = Banco()
    bosque = B.add('Bosque', typ=6, produces=1 << 4, cmc=0)
    dardo = B.add('1 dano a criatura', typ=2, cmc=1, gen=1,
                  eff=E['DMG_SPELL'], p1=1, score=10)
    peon = B.add('1/1', typ=1, cmc=1, gen=1, power=1, tough=1)
    lord = B.add('encantamiento lord +2/+2', typ=4, cmc=1, gen=1,
                 eff=E['LORD'], p1=2, p2=2, score=30)
    atacante = mazo((20, dardo), (40, bosque))
    defensor = mazo((14, peon), (14, lord), (32, bosque))
    fila = []
    for lv in (0, 1):
        r = con({'LORD_VE': lv}, lambda: duelo(B, atacante, defensor))
        fila.append(('remocion de 1 contra 1/1 con lord +2/+2', lv, r['wr'], r['kills']))
    return "lord: 'kills' deberia ser 0 (son 3/3)", fila


def prueba_barrido_lord():
    """Un barrido de 2 contra 1/1 con lord +2/+2 no deberia limpiar nada. Se mira
    'sweep', que cuenta barridos lanzados, junto al largo de la partida."""
    B = Banco()
    bosque = B.add('Bosque', typ=6, produces=1 << 4, cmc=0)
    barrido = B.add('barrido 2', typ=3, cmc=3, gen=3, eff=E['SWEEPER'], p1=2, score=20)
    guardia = B.add('2/2 propia', typ=1, cmc=2, gen=2, power=2, tough=2)
    peon = B.add('1/1', typ=1, cmc=1, gen=1, power=1, tough=1)
    lord = B.add('encantamiento lord +2/+2', typ=4, cmc=1, gen=1,
                 eff=E['LORD'], p1=2, p2=2, score=30)
    atacante = mazo((14, barrido), (10, guardia), (36, bosque))
    defensor = mazo((14, peon), (14, lord), (32, bosque))
    fila = []
    for lv in (0, 1):
        r = con({'LORD_VE': lv}, lambda: duelo(B, atacante, defensor))
        fila.append(('barrido de 2 contra 1/1 con lord +2/+2', lv, r['wr'], r['gamelen']))
    return "barrido + lord: los 3/3 no deberian morir (columna = turnos)", fila


def prueba_remate():
    """El mismo hechizo letal, etiquetado BURN_FACE. Con el bonus deberia lanzarse antes
    y por tanto ganar en menos turnos."""
    B = Banco()
    tierra = B.add('Montania', **MONTANA)
    remate = B.add('6 a la cara por 2', typ=3, cmc=2, gen=2, eff=E['BURN_FACE'], p1=6)
    bicho = B.add('4/4 prisa por 2', typ=1, cmc=2, gen=2, power=4, tough=4,
                  kw=KWBIT['Haste'])
    muro = B.add('0/4 defensor', typ=1, cmc=2, gen=2, power=0, tough=4,
                 kw=KWBIT['Defender'])
    fila = []
    for rl in (0, 1):
        r = con({'REMATE_LETAL': rl},
                lambda: duelo(B, mazo((12, remate), (12, bicho), (36, tierra)),
                              mazo((20, muro), (40, tierra)), life=6))
        fila.append(('rival a 6 vidas, remate de 6 por 2', rl, r['wr'], r['gamelen']))
    return 'remate letal: deberia ganar en menos turnos', fila


def prueba_ataque_letal():
    """Criaturas que mueren a cualquier bloqueador pero que JUNTAS rematan.

    Hace falta que el defensor tenga cuerpos de sobra: si le sobran bloqueadores,
    BLOQ_LIBRE no salva al atacante (siempre queda alguien libre) y cada criatura
    decide por su cuenta contra opp->life <= P_*2. El 3/1 muere con cualquier bloqueo
    y no mata al 2/4, asi que lethalblk>0 para todos y ninguno ataca."""
    B = Banco()
    tierra = B.add('Montania', **MONTANA)
    peon = B.add('3/1 prisa', typ=1, cmc=1, gen=1, power=3, tough=1,
                 kw=KWBIT['Haste'])
    muro = B.add('2/4 rival', typ=1, cmc=2, gen=2, power=2, tough=4)
    fila = []
    for al in (0, 1):
        r = con({'ATAQUE_LETAL': al},
                lambda: duelo(B, mazo((40, peon), (20, tierra)),
                              mazo((30, muro), (30, tierra)), life=12))
        fila.append(('40x 3/1 prisa contra 30x muro 2/4', al, r['wr'], r['gamelen']))
    return 'ataque letal agregado (rival a 12 vidas)', fila


PRUEBAS = [prueba_amenaza, prueba_dano_primero, prueba_indestructible,
           prueba_lord, prueba_barrido_lord, prueba_remate, prueba_ataque_letal]


def main():
    filtro = [a for a in sys.argv[1:] if not a.startswith('-')]
    for fn in PRUEBAS:
        nombre = fn.__name__.replace('prueba_', '')
        if filtro and not any(nombre.startswith(f) for f in filtro):
            continue
        titulo, filas = fn()
        print(f"\n=== {titulo} ===")
        for etiqueta, flag, wr, extra in filas:
            print(f"  {etiqueta:<38} flag={flag}  wr {wr*100:6.2f}%   {extra:8.3f}")


if __name__ == '__main__':
    main()
