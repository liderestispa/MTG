"""Convierte texto oracle de Scryfall -> codigos de efecto para el motor en C."""
import json, re, sys, os

_REGLAS = None
def reglas_extra(ruta='data/reglas_extra.json'):
    """Reglas del extractor guardadas como DATOS, no como codigo.

    Cada entrada: {nombre, patron, efecto, p1, p2, tipo_linea, activo, nota}.
    Si p1 falta y el patron tiene un grupo, se usa el numero capturado. El laboratorio
    las enciende y apaga para medirlas, asi que el motor puede ganar reglas nuevas sin
    que nadie escriba Python. REGLAS_OFF=1 las desactiva todas de golpe.
    """
    global _REGLAS
    if _REGLAS is None:                       # el archivo se lee y compila una sola vez
        try:
            with open(ruta, encoding='utf-8') as f:
                _REGLAS = json.load(f).get('reglas', [])
        except (OSError, ValueError):
            _REGLAS = []
        for r in _REGLAS:
            r['_rx'] = re.compile(r['patron'], re.I)
            r['_activo_archivo'] = bool(r.get('activo'))
    # OJO: el filtro se aplica en CADA llamada, no al cachear. Cachearlo hacia que
    # REGLA_SOLO no tuviera efecto si el modulo ya se habia usado antes de fijarlo, que
    # es justo lo que hace el laboratorio al medir: las seis primeras candidatas dieron
    # +0,000 exacto por esto.
    if os.environ.get('REGLAS_OFF') == '1': return []
    # REGLA_SOLO ANADE la regla nombrada a las que ya estan activas en el archivo; NO
    # apaga las demas. Apagarlas era inofensivo cuando ninguna estaba adoptada, pero en
    # cuanto hay reglas encendidas convierte cada medicion en "esta regla contra un motor
    # distinto del real", y el numero deja de ser comparable con el objetivo vigente.
    solo = os.environ.get('REGLA_SOLO')
    for r in _REGLAS:
        r['activo'] = r['_activo_archivo'] or (r['nombre'] == solo)
    return _REGLAS


# coste alternativo: "You may [hacer X] rather than pay this spell's mana cost".
# Cobrar estas cartas a su coste nominal hace que el motor no las lance NUNCA:
# Fireblast se veia a 6 mana en un mazo que juega 4 tierras. Devuelve (tipo, cantidad),
# con tipo 1 = sacrificar N tierras y tipo 2 = pagar N vidas.
_ALT_COST = re.compile(r"rather than pay (?:this spell's|its) mana cost", re.I)
_ALT_SAC  = re.compile(r"sacrific(?:e|ing) (a|an|one|two|three|four|\d+) ", re.I)
_ALT_LIFE = re.compile(r"pay (\d+) life", re.I)
_NUM = {'a': 1, 'an': 1, 'one': 1, 'two': 2, 'three': 3, 'four': 4}

def alt_cost(txt):
    if not txt: return 0, 0
    for linea in txt.split('\n'):
        if not _ALT_COST.search(linea): continue
        m = _ALT_SAC.search(linea)
        if m:
            v = m.group(1).lower()
            return 1, _NUM.get(v, int(v) if v.isdigit() else 1)
        m = _ALT_LIFE.search(linea)
        if m: return 2, int(m.group(1))
    return 0, 0

KW = ['Flying','Deathtouch','Lifelink','Trample','Vigilance','Haste','Menace','Reach',
      'First strike','Double strike','Defender','Flash','Hexproof','Indestructible',
      'Ward','Protection','Prowess','Skulk','Intimidate','Shadow','Horsemanship','Fear']
KWBIT = {k: 1 << i for i, k in enumerate(KW)}

E = dict(NONE=0, ETB_DMG=1, ETB_DRAIN=2, ETB_DRAW=3, ETB_DISCARD=4, ETB_TOKEN=5,
         DESTROY=7, DMG_SPELL=8, SWEEPER=9, LORD=10, EQUIP=11, DRAW_ON_DMG=12,
         UPKEEP_DRAIN=13, RAMP=14, COUNTER=15, BURN_FACE=16, LIFEGAIN=17, PUMP=18,
         REANIMATE=19, ENGINE=20, EXILE=21, BOUNCE=22, FIGHT=23, ETB_COUNTERS=24,
         COND_BUFF=25, LOOT_TOKEN=26, AMASS=27, TREASURE=28, SAGA=29, PW_TICK=30,
         SPELL_DMG=31, PROWESS_ENG=32, TOKEN_SCALE=33, TOKEN_DOUBLE=34, EXILE_ENGINE=35,
         UPKEEP_DRAW=36, REPEAT_PUMP=37, TEAM_PUMP=38, FOG_BOUNCE=39, MOBILIZE=40,
         MASS_CHEAT=41, DEATH_DMG=42, ATTACK_DRAW=43, RECURSIVE=44, TEAM_MANA=45,
         ATTACK_DMG=46, PROTECT=47, DMG_ANY=48,
         EDICT=49, TAPDOWN=50, TAX=51, LAND_KILL=52, MASS_BOUNCE=53, ETB_MANA=54)

NUMW = {'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'X':1}
def num(s, d=1):
    s = (s or '').strip()
    if s.isdigit(): return int(s)
    return NUMW.get(s.lower(), d)

def parse_card(c):
    t = (c.get('type_line') or '')
    txt = (c.get('oracle_text') or '')
    # cara frontal para adventure/mdfc/transformables
    faces = c.get('card_faces') or []
    if faces and not txt.strip():
        txt = faces[0].get('oracle_text') or ''
        t = faces[0].get('type_line') or t
    tl = t.lower()
    low = txt.lower().replace('—', '-')
    # quitar texto recordatorio
    low = re.sub(r'\([^)]*\)', '', low)

    # ---- fuera las HABILIDADES ACTIVADAS ----
    # Las reglas de efecto barren el texto entero, asi que un efecto que en la carta
    # cuesta activarlo caia en una ranura libre y el motor lo ejecutaba SOLO, GRATIS y
    # AL ENTRAR. No es teorico y no era raro: src/auditoria_lectura.py encontro 36 cartas
    # asi, varias en los mazos que se le recomendaron a Ricardo.
    #
    #   Giant's Boulder     artefacto de {1}, "{7}, {T}, Sacrificar: destruye el
    #                       permanente objetivo"  ->  el motor tenia un Vindicate de 1 mana
    #   Dwarven Provisioner "{3}{W}: las criaturas ganan +1/+1 hasta el final del turno"
    #                       ->  el motor tenia un lord estatico permanente y gratis
    #
    # Es la leccion de Krark-Clan Shaman otra vez: una habilidad ACTIVADA no se puede
    # aproximar con un efecto de entrada. La ranura act_eff existe para las que se pueden
    # modelar; el resto se DESCARTA, que es conservador y no regala nada.
    #
    # No se filtran las que solo producen mana ("{T}: Add {G}"), que mana_ability lee
    # aparte, ni la palabra clave equipar, que tiene su propia ranura.
    # Ablacion: ACTIVADAS_GRATIS=1 vuelve al comportamiento viejo.
    low_todo = low          # con las activadas dentro: lo necesita el parser de act_eff
    if os.environ.get('ACTIVADAS_GRATIS') != '1':
        # Un coste de activacion es una secuencia de partes separadas por coma, terminada
        # en ':'. Cada parte puede ser mana ({3}{W} van pegados, sin coma), girar, o
        # sacrificar/descartar/exiliar algo.
        _PARTE = (r'(?:\{[^}]+\}\s*)+|sacrifice [^,:]{1,30}|tap [^,:]{1,30}|'
                  r'discard [^,:]{1,30}|exile [^,:]{1,30}|pay \d+ life|remove [^,:]{1,30}')
        _ACT = re.compile(r'^\s*(?:' + _PARTE + r')(?:\s*,\s*(?:' + _PARTE + r'))*\s*:')
        _lineas = []
        for _l in low.split('\n'):
            if (_ACT.match(_l) and not re.search(r':\s*add \{', _l)
                    and not _l.strip().startswith('equip')):
                continue                      # es una habilidad activada: no se lee
            _lineas.append(_l)
        low = '\n'.join(_lineas)

    out = {'eff': E['NONE'], 'p1': 0, 'p2': 0, 'p3': 0, 'eff2': E['NONE'], 'q1': 0, 'q2': 0,
           'eff3': E['NONE'], 'r1': 0, 'r2': 0}
    # Las palabras clave estaticas viven en su propia linea al principio del texto
    # ("Flying, lifelink"). Si aparecen dentro de una frase con ':' , 'when', 'whenever',
    # 'gains' o 'until end of turn', son CONDICIONALES y no deben aplicarse como estaticas.
    kw = 0
    raw = txt or ''
    for line in raw.split('\n'):
        ln = re.sub(r'\([^)]*\)', '', line).strip().rstrip('.')
        if not ln: continue
        toks = [t.strip().lower() for t in ln.split(',')]
        # una linea de keywords es solo keywords (permite "ward {2}", "protection from X")
        okline = True
        for t in toks:
            base = re.sub(r'\s*\{.*', '', t)
            base = re.sub(r'^(protection from|ward).*', lambda m: m.group(0).split()[0], base)
            if base not in [k.lower() for k in KW] and base not in ('ward','protection'):
                okline = False; break
        if not okline: continue
        for k in KW:
            if re.search(r'\b' + k.lower() + r'\b', ln.lower()): kw |= KWBIT[k]
    out['kw'] = kw

    def setp(code, p1=0, p2=0, p3=0):
        if out['eff'] == E['NONE']:
            out.update(eff=code, p1=p1, p2=p2, p3=p3)
        elif out['eff2'] == E['NONE']:
            out.update(eff2=code, q1=p1, q2=p2)
        elif out['eff3'] == E['NONE']:
            out.update(eff3=code, r1=p1, r2=p2)

    # ---- REMOCION ----
    if re.search(r'destroy target [\w-]*\s?(creature|permanent)', low) or re.search(r'destroy those creatures', low):
        cond = 0
        if 'without' in low or "can't" in low or 'unless' in low or 'with mana value' in low: cond = 1
        setp(E['DESTROY'], cond)
    if re.search(r'exile target [\w-]*\s?(creature|permanent|nonland)', low) or re.search(r'exiles? a creature they control', low):
        setp(E['EXILE'], 0)
    m = re.search(r'deals? (\w+) damage to (?:up to \w+ )?(target creature|any target|target player|target creature or planeswalker|each creature)', low)
    if m:
        d = num(m.group(1), 2)
        # "any target" NO es quemar a la cara: es dano flexible. Un Rayo mata una
        # criatura cuando conviene y va a la cara cuando remata. Modelarlo como
        # BURN_FACE le quitaba toda la interaccion a los mazos rojos.
        if 'any target' in m.group(2):        setp(E['DMG_ANY'], d)
        elif 'creature' in m.group(2):        setp(E['DMG_SPELL'], d)
        else:                                 setp(E['BURN_FACE'], d)
    # ---- el hechizo quema a cada oponente por si mismo (Grab the Prize) ----
    # La regla de dano de arriba cubre "target creature", "any target" y "target player",
    # pero no "each opponent", asi que estos hechizos perdian entera su mitad agresiva:
    # Grab the Prize se modelaba como robar dos cartas y nada mas.
    # Se excluyen las lineas con disparo, que ya las cogen las reglas de SPELL_DMG
    # (Guttersnipe, Kessig Flamebreather) y de ETB (Voldaren Epicure). Sin esa exclusion
    # se contaria dos veces.
    # Ablacion: BURNEACH=0.
    if os.environ.get('BURNEACH') != '0':
        for _lin in low.split('\n'):
            if re.match(r'\s*(when|whenever)\b', _lin): continue
            _m = re.search(r'deals? (\w+) damage to each opponent', _lin)
            if _m:
                setp(E['BURN_FACE'], num(_m.group(1), 1)); break
    if re.search(r'(destroy all creatures|each creature gets -|destroy all other creatures)', low):
        mm = re.search(r'gets -\d+/-(\d+)', low)
        setp(E['SWEEPER'], int(mm.group(1)) if mm else 99)
    if re.search(r'return target (creature|nonland permanent) .*to (its owner|their owner)', low):
        setp(E['BOUNCE'], 0)
    if 'fights' in low: setp(E['FIGHT'], 0)
    if re.search(r'counter target', low): setp(E['COUNTER'], 0)

    # ---- ETB / disparos ----
    trig = 'enters' in low or 'when' in low or 'whenever' in low
    # "its controller loses N life" es la forma que usan las remociones con drenaje
    # (Inevitable Defeat: exilia un permanente Y drena 3). Faltaba, y con ella se perdia
    # el drenaje entero: el motor solo veia el exilio. Ablacion: DRAIN_CTRL=0.
    _pat_drain = (r'(?:each opponent loses|target (?:player|opponent) loses) (\w+) life'
                  if os.environ.get('DRAIN_CTRL') == '0' else
                  r'(?:each opponent loses|target (?:player|opponent) loses|its controller loses) (\w+) life')
    m = re.search(_pat_drain, low)
    if m: setp(E['ETB_DRAIN'], num(m.group(1), 2))
    m = re.search(r'draws? (\w+) cards?', low)
    # "Roba 3, luego pon 2 de tu mano encima de tu biblioteca": la ventaja NETA es 1, no 3.
    # Brainstorm es seleccion, no robo, y cobrarlo como tres cartas por un mana infla al
    # arquetipo entero. Se deja en 1 y no en 0 porque la seleccion vale algo.
    # APAGADO POR DEFECTO: NETDRAW=1 para activarlo. Medido +0,289, claramente peor.
    # Tiene sentido: Blue Terror esta INFRAvalorado (-7,4), asi que quitarle valor a su
    # motor de robo lo hunde mas. Seria el freno correcto solo si antes se sube el resto
    # del mazo (coste efectivo de Cryptic Serpent y Tolarian Terror, ciclado de Lorien
    # Revealed); suelto, empeora. Ablacion: NETDRAW=1.
    if m and os.environ.get('NETDRAW') == '1':
        _dev = re.search(r'put (\w+) cards? from your hand on top of your library', low)
        if _dev:
            _neto = max(1, num(m.group(1), 1) - num(_dev.group(1), 0))
            low = re.sub(r'draws? \w+ cards?', f'draw {_neto} cards', low, count=1)
            m = re.search(r'draws? (\w+) cards?', low)
    if m and 'opponent draws' not in low:
        if re.search(r'whenever .*(deals combat damage|attacks)', low): setp(E['DRAW_ON_DMG'], 1)
        elif trig or 'sorcery' in tl or 'instant' in tl: setp(E['ETB_DRAW'], num(m.group(1), 1))
    m = re.search(r'(?:target player|each opponent|target opponent) discards? (\w+) cards?', low)
    if m: setp(E['ETB_DISCARD'], num(m.group(1), 1))
    # exiliar de la mano rival es descarte con otro nombre
    m = re.search(r'(?:target opponent|each opponent|target player) exiles? (\w+) cards? from (?:their|his or her) hand', low)
    if m: setp(E['ETB_DISCARD'], num(m.group(1), 1))
    if re.search(r'(?:target opponent|each opponent) discards? (?:their|his or her) hand', low):
        setp(E['ETB_DISCARD'], 4)

    # ---- BLOQUE DE NEGACION (antes sin modelar: ~7% del meta) ----
    # edicto: el rival sacrifica. No apunta, asi que atraviesa el antimaleficio.
    if re.search(r'(?:target player|each opponent|target opponent|each player) sacrifices? an? '
                 r'(?:creature|nonland permanent|permanent)', low):
        setp(E['EDICT'], 1)
    # inmovilizar: girar y que no se enderece
    if re.search(r"\btap target creature[^.]*\.\s*it doesn't untap", low):
        setp(E['TAPDOWN'], 2)                       # 2 = se pierde dos turnos
    elif re.search(r'\btap target creature(?: an opponent controls)?', low) and 'untap target' not in low:
        setp(E['TAPDOWN'], 1)
    # impuesto: los hechizos del rival cuestan mas
    m = re.search(r'(?:spells?|creature spells?|noncreature spells?) your opponents cast cost \{(\d)\} more', low)
    if m: setp(E['TAX'], int(m.group(1)))
    m2 = re.search(r"creatures? (?:your opponents control )?can't attack (?:you|unless)", low)
    if m2 and out['eff']==E['NONE']: setp(E['TAX'], 1)
    # DESTRUCCION DE TIERRAS: MEDIDA Y DESCARTADA.
    # "sacrifice a land" casi siempre es un coste que paga QUIEN LANZA (Crop Rotation,
    # Highway Robbery), y hasta "destroy target land" se usa sobre tierra propia para
    # buscar y robar (Cleansing Wildfire, que da nombre a Jund Wildfire en Pauper).
    # Modelarlo como ataque al rival empeoraba el ajuste: objetivo 2,86 -> 3,14.
    # El codigo E_LAND_KILL sigue en el motor por si aparece destruccion real de tierras.
    pass
    # rebote masivo (niebla + tempo)
    if re.search(r'return all (?:attacking )?creatures[^.]* to (?:their|its) owner', low):
        setp(E['MASS_BOUNCE'], 1)
    m = re.search(r'creates? (\w+) ([\dx]+)/([\dx]+) .*?(?:creature )?tokens?', low)
    if m:
        p, tg = m.group(2), m.group(3)
        if p.isdigit() and tg.isdigit():
            # bit 8: la ficha produce mana al sacrificarse (Eldrazi Spawn/Scion,
            # "Sacrifice this token: Add {C}"). Sin esto la ficha es un 0/1 vainilla y
            # se pierde su valor entero, que es rampa, no cuerpo. Es lo que hundia a
            # Jund Wildfire al activar FICHAS_REALES.
            mana = 0x100 if re.search(
                r'sacrifice this (?:token|creature)[^.]*:\s*add', low) else 0
            setp(E['ETB_TOKEN'], num(m.group(1), 1), (int(p) << 4) | int(tg) | mana)
    # El candado 'out[eff]==NONE' hacia que la ganancia de vida solo existiera en cartas
    # que no hicieran nada mas. Jeskai Revelation gana 4 vidas y las perdia por tener el
    # slot ocupado por el dano; Inevitable Defeat igual. setp ya elige la primera ranura
    # libre de las tres, asi que el candado sobra. Ablacion: LIFEGAIN_ANY=0.
    m = re.search(r'you gain (\w+) life', low)
    if m and (out['eff'] == E['NONE'] or os.environ.get('LIFEGAIN_ANY') != '0'):
        setp(E['LIFEGAIN'], num(m.group(1), 2))
    if re.search(r'at the beginning of (your|each) upkeep', low) and re.search(r'lose[s]? \d+ life', low):
        mm = re.search(r'lose[s]? (\d+) life', low); setp(E['UPKEEP_DRAIN'], int(mm.group(1)))
    if re.search(r'search your library for a .*land', low): setp(E['RAMP'], 1)
    if re.search(r'return target creature card from your graveyard', low): setp(E['REANIMATE'], 0)

    # ---- estaticos ----
    m = re.search(r'(?:other )?creatures you control get \+(\d+)/\+(\d+)', low)
    if m: setp(E['LORD'], int(m.group(1)), int(m.group(2)))
    if 'aura' in tl or 'enchant creature' in low:
        m = re.search(r'enchanted creature gets \+(\d+)/\+(\d+)', low)
        if m: setp(E['EQUIP'], int(m.group(1)), int(m.group(2)), 0)
        elif re.search(r'enchanted creature gets \+x/\+x', low): setp(E['EQUIP'], 4, 4, 0)
        elif re.search(r'enchanted creature gets \+1/\+1 for each', low): setp(E['EQUIP'], 5, 5, 0)
    if 'equipment' in tl:
        m = re.search(r'equipped creature gets \+(\d+)/\+(\d+)', low)
        eq = re.search(r'equip \{?(\d+)', low)
        setp(E['EQUIP'], int(m.group(1)) if m else 1, int(m.group(2)) if m else 1,
             int(eq.group(1)) if eq else 2)
    m = re.search(r'target creature gets \+(\d+)/\+(\d+)', low)
    if m and ('instant' in tl or 'sorcery' in tl): setp(E['PUMP'], int(m.group(1)), int(m.group(2)))
    m = re.search(r'(?:enters|with) (\w+) \+1/\+1 counters?', low)
    if m: setp(E['ETB_COUNTERS'], num(m.group(1), 1))
    # motores de robo persistentes
    if re.search(r'whenever .*(you draw|creature you control (deals combat damage|enters))', low) and 'draw a card' in low:
        setp(E['ENGINE'], 1)








    # ---- hechizos de proteccion: responden a la remocion ----
    if re.search(r'(gains?|gain) (hexproof|indestructible|protection from)', low) and \
       ('target creature you control' in low or 'this creature' in low):
        out.update(eff=E['PROTECT'], p1=1)
    if re.search(r'gains? (deathtouch and )?indestructible until end of turn', low):
        out.update(eff=E['PROTECT'], p1=1)
    # ---- disparos al morir ----
    m = re.search(r'when(ever)? this creature dies,? .*deals? (\w+) damage', low)
    if m: setp(E['DEATH_DMG'], num(m.group(2),1))
    m = re.search(r'when(ever)? this creature dies,? .*(each opponent loses|target player loses) (\w+) life', low)
    if m: setp(E['DEATH_DMG'], num(m.group(3),1))
    # ---- disparos al atacar que dan cartas ----
    if re.search(r'whenever this creature attacks,? .*(reveal the top card of your library and put it into your hand|draw a card)', low):
        setp(E['ATTACK_DRAW'], 1)
    m = re.search(r'whenever this creature attacks,? .*deals? (\w+) damage to (each opponent|any target)', low)
    if m: setp(E['ATTACK_DMG'], num(m.group(1),1))
    # ---- recursion desde el cementerio: valor extra ----
    # (la recursion desde el cementerio se descarto: creaba bucles de valor irreales)
    # ---- todo el equipo produce mana ----
    if re.search(r'creatures you control have ["“]?\{t\}: add', low):
        setp(E['TEAM_MANA'], 1)
    # ---- pierde la mitad de la vida ----
    if re.search(r'they lose half their life', low):
        setp(E['DEATH_DMG'], 6)
    # ---- motores de robo recurrente (Dark Confidant, The Arkenstone y similares) ----
    # OJO: no todos disparan en el mantenimiento. "al comienzo de tu paso final" es
    # igual de bueno y se estaba perdiendo (The Arkenstone robaba una carta por turno
    # y el motor no la veia).
    if re.search(r'at the beginning of (?:your|each) (?:upkeep|end step|draw step|'
                 r'precombat main phase|postcombat main phase)[^.]*?'
                 r'(?:put that card into your hand|draw)', low):
        setp(E['UPKEEP_DRAW'], 1)
    # ---- habilidad activada repetible de pump (Timberwatch Elf) ----
    if re.search(r'\{t\}:\s*target creature gets \+', low):
        m = re.search(r'gets \+(\w+)/\+(\w+)', low)
        v = 3 if (m and not m.group(1).isdigit()) else (int(m.group(1)) if m else 2)
        setp(E['REPEAT_PUMP'], v)
    # ---- remate masivo (Craterhoof): todo el equipo +X/+X ----
    if re.search(r'creatures you control (gain|get) .*\+x/\+x', low) or \
       re.search(r'creatures you control get \+x/\+x', low):
        setp(E['TEAM_PUMP'], 4)
    # ---- fog / rebote masivo de atacantes ----
    if re.search(r'return all attacking creatures to their owners? hand', low):
        setp(E['FOG_BOUNCE'], 0)
    if re.search(r'return up to two .*nonland permanents? to (their|its) owners?', low):
        setp(E['BOUNCE'], 2)
    # ---- mobilize: fichas atacantes ----
    m = re.search(r'mobilize (\d+)', low)
    if m: setp(E['MOBILIZE'], int(m.group(1)))
    # ---- poner criaturas de la mano al campo ----
    if re.search(r'put any number of creature cards from your hand onto the battlefield', low):
        setp(E['MASS_CHEAT'], 2)
    # ---- comida / vida menor ----
    if re.search(r'create a food token', low) and out['eff']==E['NONE']:
        setp(E['LIFEGAIN'], 3)
    # ---- motores que se disparan al exiliar (Ketramose y similares) ----
    if re.search(r'whenever one or more cards? (are|is) put into exile', low) and 'draw' in low:
        out.update(eff=E['EXILE_ENGINE'], p1=1)
    if re.search(r'whenever .* exiled? .*, draw a card', low) and out['eff']==E['NONE']:
        out.update(eff=E['EXILE_ENGINE'], p1=1)
    # ---- fichas que escalan con copias propias, y duplicadores ----
    if re.search(r'create a number of .*tokens? equal to the number of other creatures you control named', low):
        setp(E['TOKEN_SCALE'], 1)
    if re.search(r'if one or more tokens would be created under your control, twice that many', low):
        out.update(eff=E['TOKEN_DOUBLE'], p1=2, p2=0)   # sobrescribe: es su funcion principal
    # ---- motores de "cada vez que lanzas un hechizo" ----
    m = re.search(r'whenever you cast (?:an? )?(?:instant or sorcery|noncreature|instant|sorcery)[^.]*?deals? (\w+) damage to each opponent', low)
    if m: setp(E['SPELL_DMG'], num(m.group(1),1))
    m = re.search(r'deals? (\w+) damage to each opponent', low)
    if m and out['eff']==E['NONE'] and 'whenever' not in low: setp(E['BURN_FACE'], num(m.group(1),1))
    if re.search(r'whenever you cast a noncreature spell.*(\+1/\+1|\+2/\+0)', low):
        setp(E['COND_BUFF'], 1, 1)
    # ---- seleccion de cartas = robo efectivo ----
    m = re.search(r'look at the top \w+ cards? of your library\.? (?:you may reveal|put) (\w+)', low)
    if m and out['eff']==E['NONE']:
        setp(E['ETB_DRAW'], num(m.group(1),1))
    if re.search(r'(surveil|scry|mill) \w+,? (then )?draw', low) and out['eff']==E['NONE']:
        setp(E['ETB_DRAW'], 1)
    if re.search(r'that player discards that card', low) and out['eff']==E['NONE']:
        setp(E['ETB_DISCARD'], 1)
    if re.search(r'each creature .* loses all abilities.*destroy', low):
        setp(E['SWEEPER'], 99)
    if re.search(r'mill a card\. you may play that card', low) and out['eff']==E['NONE']:
        setp(E['ETB_DRAW'], 1)

    # ---- patrones adicionales (auditoria de cartas del meta) ----
    if re.search(r'destroy all (tapped |untapped )?(artifacts and )?creatures', low):
        setp(E['SWEEPER'], 99)
    if re.search(r'return all nonland permanents target player controls', low):
        setp(E['SWEEPER'], 99)
    if re.search(r'exile target [\w, ]*(artifact|enchantment|creature)[\w, ]*with power', low):
        setp(E['EXILE'], 0)
    m = re.search(r'deals (\w+) damage to each opponent and each creature', low)
    if m: setp(E['SWEEPER'], num(m.group(1),1))
    if re.search(r'exile the top (\w+) cards? of your library.*you may play', low):
        mm=re.search(r'exile the top (\w+) cards?', low); setp(E['ETB_DRAW'], num(mm.group(1),1))
    if re.search(r'reveal the top \w+ cards of your library', low) and out['eff']==E['NONE']:
        setp(E['ETB_DRAW'], 2)
    if re.search(r'target creature you control gets \+\d+/\+\d+ and gains hexproof', low):
        setp(E['PUMP'], 1, 1)
    if re.search(r'each player discards|each player loses \d+ life|each player sacrifices', low):
        mm=re.search(r'each player loses (\d+) life', low)
        setp(E['ETB_DRAIN'], int(mm.group(1)) if mm else 2)
    if re.search(r'you choose an? [\w ]*card from it\. exile that card', low):
        setp(E['ETB_DISCARD'], 1)
    if re.search(r'target creature gains deathtouch and lifelink', low):
        setp(E['PUMP'], 1, 0)
    if re.search(r"tap target creature\. it doesn't untap", low):
        setp(E['BOUNCE'], 0)
    if re.search(r'puts? (it|them) on (their|the) (choice of the )?(top|bottom)', low) and out['eff']==E['NONE']:
        setp(E['BOUNCE'], 0)
    if 'kicker' in low and out['eff']==E['NONE']:
        setp(E['ETB_DRAW'], 2)
    # ---- mecanicas de set (HOB / TLA) ----
    if 'recruit' in low and ('enters' in low or 'dies' in low):
        setp(E['LOOT_TOKEN'], 1)
    m = re.search(r'amass \w+ (\d+)', low)
    if m: setp(E['AMASS'], int(m.group(1)))
    if re.search(r'creates? (a|one|two|\d+) .*treasure token', low) or 'create a treasure token' in low:
        mm = re.search(r'creates? (\w+) .*treasure', low)
        setp(E['TREASURE'], num(mm.group(1),1) if mm else 1)
    # ---- vuelve sola del cementerio (Sneaky Snacker, Bloodghast, Forsaken Miner) ----
    # APAGADO POR DEFECTO: RECUR_ON=1 para activarlo. E_RECURSIVE estaba implementado en
    # sim.c y ninguna regla lo activaba nunca, o sea codigo muerto — la trampa de
    # "keywords parseadas que nadie lee", al reves.
    #
    # Medido: 2,271 -> 2,296. Pero el desglose importa mas que el total. En PAUPER no
    # cambia nada (2,20 y r=+0,82, identico), asi que las 4 Sneaky Snacker de Mono Red
    # Madness no explican su -14. Toda la degradacion esta en STANDARD, donde r cae de
    # +0,16 a +0,08 por Bloodghast en Mardu Discard — y el dato de Standard es pre-ban,
    # o sea que empeorar contra el no significa gran cosa. Queda apagado porque la regla
    # es no adoptar lo que no se puede demostrar, no porque este claro que sea peor.
    if os.environ.get('RECUR_ON') == '1' and \
       re.search(r'return (this card|it) from your graveyard to (the battlefield|your hand)', low):
        setp(E['RECURSIVE'], 1)
    # ---- al entrar produce mana (Burning-Tree Emissary) ----
    # APAGADO POR DEFECTO: ETBMANA_ON=1 para activarlo.
    # "When this creature enters, add {R}{G}": la criatura se paga sola y deja encadenar
    # otra el mismo turno; sin esto es un 2/2 vainilla. Modelarla bien sube a Mono Red
    # Rally de 36,4% a 37,5% (su real es 46,4%) y aun asi EMPEORA el objetivo global,
    # 2,256 -> 2,311, el doble del ruido.
    #
    # El motivo es de orden, no de la carta. El objetivo mide correlacion de orden, y
    # Rally ya estaba correctamente ultimo. Subirlo lo comprime contra Mono Red Madness,
    # que esta MAS infravalorado (-14) y deberia ir por encima. Arreglar un arquetipo
    # aislado, cuando su vecino en la tabla esta peor modelado, rompe el orden.
    # Para que esto pague hay que arreglar antes a Madness, cuyo motor de valor
    # —descartar y sacar provecho de lo descartado: locura, cementerio— no esta modelado.
    m = re.search(r'(?:when|whenever) [^.]*enters[^.]*?,\s*add ((?:\{[^}]+\}\s*)+)', low)
    if m and os.environ.get('ETBMANA_ON') == '1':
        setp(E['ETB_MANA'], len(re.findall(r'\{[^}]+\}', m.group(1))))
    if 'ferocious' in low:                      # +1/+0 y trample condicional
        setp(E['COND_BUFF'], 1, 0)
    if 'storied' in low:
        mm = re.search(r'gets \+(\d+)/\+(\d+)', low)
        setp(E['COND_BUFF'], int(mm.group(1)) if mm else 1, int(mm.group(2)) if mm else 0)
    if 'landfall' in low:
        if re.search(r'double .*power', low): setp(E['COND_BUFF'], 5, 0)   # duplicar poder
        else: setp(E['COND_BUFF'], 1, 1)
    m = re.search(r'put (\w+) \+1/\+1 counters? on (target|each|up to one)', low)
    if m: setp(E['ETB_COUNTERS'], num(m.group(1),1))
    m = re.search(r'deals damage equal to its power to target creature', low)
    if m: setp(E['FIGHT'], 0)
    m = re.search(r'gets? -(\d+)/-(\d+)', low)
    if m and ('target creature' in low) and int(m.group(2))>=3: setp(E['DESTROY'], 0)
    if re.search(r'exile the top card of your library.*you may (play|cast)', low):
        setp(E['ETB_DRAW'], 1)
    if re.search(r'search your library for a (forest|island|swamp|mountain|plains|basic land)', low):
        setp(E['RAMP'], 1)
    if 'prowess' in low: out['kw'] |= KWBIT.get('Prowess',0)
    m = re.search(r"creates? (\w+) \d+/\d+ .*?token", low)
    if m and out['eff']==E['NONE']: setp(E['ETB_TOKEN'], num(m.group(1),1), (1<<4)|1)
    if re.search(r'whenever .* attacks?, .*(add \{r\}|draw)', low) and out['eff']==E['NONE']:
        setp(E['COND_BUFF'], 1, 0)
    # sagas y planeswalkers: valor recurrente aproximado
    if 'saga' in tl.lower(): setp(E['ENGINE'], 1)
    if 'planeswalker' in tl.lower(): setp(E['ENGINE'], 1)
    # ---- disparo AL IR AL CEMENTERIO ----
    # Ranura propia (die_eff/die_p1), porque adelantarlo a la entrada no es una
    # aproximacion: cambia el tempo, que es justo lo que el motor mide. Medido: dar el
    # segundo robo de Ichor Wellspring al entrar empeoraba de 2,266 a 2,412.
    # Dos casos distintos y hay que separarlos:
    #   "enters OR is put into a graveyard"  -> dispara las DOS veces (Ichor Wellspring)
    #   "is put into a graveyard"            -> SOLO al morir (Nihil Spellbomb), y
    #      entonces el robo que la regla generica le dio al entrar esta MAL puesto y hay
    #      que quitarselo, no sumarle otro.
    # Ablacion: MUERTE_OFF=1.
    if os.environ.get('MUERTE_OFF') != '1':
        # se busca en la LINEA entera, no hasta el primer punto: Nihil Spellbomb parte el
        # efecto en dos frases ("you may pay {B}. If you do, draw a card").
        # Se reconocen las TRES formas de decirlo. Antes solo casaba "is put into a
        # graveyard", que es la rara; la comun es "when this creature dies", y por eso
        # src/auditoria_lectura.py encontro 14 cartas con el disparo de muerte metido en
        # la ranura de entrada. Cuatro de ellas —Pretending Poxbearers— estaban en el
        # mazo de Pauper que se le recomendo a Ricardo, regalandole una ficha al entrar.
        _cl, _tambien_al_entrar = None, False
        for _lin in low.split('\n'):
            if not re.search(r'is put into a graveyard from the battlefield|'
                             r'\bdies\b|leaves the battlefield', _lin): continue
            if not re.match(r'\s*when', _lin): continue      # "whenever a creature dies"
            _tambien_al_entrar = bool(re.search(r'enters or (?:is put into|leaves)', _lin))
            _cl = _lin
            break
        if _cl:
            # orden de preferencia: el efecto mas "duro" primero. Solo hay una ranura.
            _cands = [
                (r'draw (\w+) cards?',            'ETB_DRAW',  1),
                (r'create (\w+) .{0,40}token',    'ETB_TOKEN', 1),
                (r'deals? (\w+) damage to any target|deals? (\w+) damage to target player',
                                                  'BURN_FACE', 1),
                (r'you gain (\w+) life',          'LIFEGAIN',  2),
            ]
            for _rx, _ef, _def in _cands:
                _m = re.search(_rx, _cl)
                if not _m: continue
                _val = num(next(g for g in _m.groups() if g), _def)
                out['die_eff'] = E[_ef]; out['die_p1'] = _val
                if not _tambien_al_entrar:
                    # estaba contado como efecto DE ENTRADA: se MUEVE, no se suma
                    for _s, _p in (('eff', 'p1'), ('eff2', 'q1'), ('eff3', 'r1')):
                        if out[_s] == E[_ef]:
                            out[_s] = E['NONE']; out[_p] = 0
                            break
                break

    # ---- habilidad ACTIVADA con coste de sacrificio ----
    # Ranura propia (act_eff/act_p1/act_cost) porque el jugador ELIGE cuando activarla y
    # paga cada vez. Meterlo como efecto de entrada hacia que Krark-Clan Shaman, que es
    # un 1/1, se suicidara al entrar arrasando su propio tablero: medido, 2,266 -> 3,102.
    # Hoy solo se cubre el caso "sacrifica un artefacto: N danio a cada criatura", que es
    # el motor de Jund Wildfire. Ablacion: ACTIVADAS_OFF=1.
    if os.environ.get('ACTIVADAS_OFF') != '1':
        # low_todo y no low: el filtro de habilidades-gratis quita justo estas lineas.
        _a = re.search(r'sacrifice an artifact:[^.]*deals? (\w+) damage to each creature',
                       low_todo)
        if _a:
            out['act_eff'] = E['SWEEPER']
            out['act_p1'] = num(_a.group(1), 1)
            out['act_cost'] = 1          # 1 = sacrificar un artefacto

    # ---- coste que baja con el tablero, DE VERDAD y no de media ----
    # Ojo: cost_reduction() ya abarata estas cartas, pero con un numero FIJO estimado a
    # ojo ("costs {N} less for each" -> N*4, tope 5). Eso tiene dos problemas:
    #
    #   1. El patron pide {N} con digitos, asi que "{X} less to cast, where X is the
    #      greatest mana value among Elementals you control" NO CASA. Sunderflock se
    #      queda a 9 mana en un mazo de cantrips y el motor no la lanza jamas: son 4
    #      cartas muertas en Izzet Spellementals, que esta 5,9 puntos por debajo de su
    #      winrate real.
    #   2. Donde si casa, la rebaja es incondicional. Eddymurk Crab queda pagable por
    #      {1}{U}{U} en el turno 3 con el cementerio vacio, que es media carta distinta.
    #      La rebaja de verdad EXIGE haber gastado hechizos antes.
    #
    # Con cred el motor calcula la rebaja mirando el tablero, y por eso REEMPLAZA a la
    # estimacion plana en vez de sumarse: si se aplicaran las dos, Eddymurk Crab pasaria
    # de gen 5 a gen 1 y de ahi a gratis.
    #
    # APAGADO POR DEFECTO: CRED_ON=1 para activarlo. Es mas correcto y ajusta PEOR, que
    # ya es el decimo caso. Medido contra la base 0,608:
    #
    #     cred=1  Eddymurk Crab dinamico en vez de -4 plano   0,675  +0,067
    #     cred=2  Sunderflock deja de estar muerta a 9 mana   0,846  +0,238
    #     las dos                                             0,854  +0,246
    #
    # Ojo con cred=1: no toca solo a Eddymurk. Cryptic Serpent, que es la amenaza de
    # Blue Terror en Pauper, lleva el mismo texto, y el dano de esa mitad esta en Pauper
    # (0,82 -> 0,91), no en Standard.
    # El de cred=2 se entiende mirando que hace: un 5/5 volador de 9 mana con rebote
    # masivo, al volverse lanzable, dispara a Izzet Spellementals muy por encima de su
    # winrate real y rompe el ORDEN de Standard (r=+1,00 -> +0,81). La leccion no es que
    # la carta deba seguir muerta, es que el motor sobrevalora volador gordo + rebote.
    #
    # CRED_SOLO=1 o 2 mide una de las dos mitades por separado; la otra vuelve al
    # modelo plano. Hace falta porque son cartas y arquetipos distintos y el agregado
    # no dice cual es la que rompe.
    if os.environ.get('CRED_ON') == '1' and 'less to cast' in low:
        _solo = os.environ.get('CRED_SOLO')
        if re.search(r'less to cast for each instant and sorcery', low):
            if _solo in (None, '1'): out['cred'] = 1
        elif re.search(r'less to cast,? where x is the greatest mana value among', low):
            if _solo in (None, '2'): out['cred'] = 2

    # ---- reglas de datos (data/reglas_extra.json) ----
    # Se aplican al final, sobre las ranuras que hayan quedado libres. Estan en un JSON y
    # no en codigo para que src/laboratorio.py pueda proponerlas, activarlas y medirlas
    # sin tocar Python: es el mecanismo por el que el motor puede mejorarse solo.
    for _r in reglas_extra():
        if not _r.get('activo'): continue
        if _r.get('tipo_linea') and _r['tipo_linea'].lower() not in tl.lower(): continue
        _mm = _r['_rx'].search(low)
        if not _mm: continue
        _v = _r.get('p1')
        if _v is None and _mm.groups():
            _v = num(_mm.group(1), 1)
        setp(E[_r['efecto']], _v if _v is not None else 1, _r.get('p2', 0))
    return out

def color_mask(cols):
    B = {'W':1,'U':2,'B':4,'R':8,'G':16}
    return sum(B.get(x, 0) for x in (cols or []))

def type_code(tl):
    tl = tl.lower()
    if 'land' in tl: return 6
    if 'creature' in tl: return 1
    if 'instant' in tl: return 2
    if 'sorcery' in tl: return 3
    if 'planeswalker' in tl: return 5
    if 'battle' in tl: return 8
    if 'enchantment' in tl and 'artifact' not in tl: return 4
    if 'artifact' in tl: return 7
    return 0

def dyn_pt(v, txt=''):
    """1 = poder/resistencia = numero de tierras; 2 = numero de criaturas;
       3 = cartas en cementerio. 0 = fijo."""
    if v is None or '*' not in str(v): return 0
    low = (txt or '').lower()
    if re.search(r'equal to the number of (islands|swamps|mountains|forests|plains|lands)', low): return 1
    if re.search(r'equal to the number of creatures', low): return 2
    if re.search(r'equal to the number of cards in (your|a) graveyard', low): return 3
    return 0

def pt(v, txt='', default_star=4):
    """Las P/T definidas por caracteristica ('*') valen 0 si se leen literal.
    Se estiman por lo que cuentan: tierras, criaturas, cartas en cementerio..."""
    if v is None: return 0
    sv = str(v)
    if '*' in sv:
        low = (txt or '').lower()
        if re.search(r'equal to the number of (islands|swamps|mountains|forests|plains|lands)', low):
            return 5
        if re.search(r'equal to the number of creatures', low): return 4
        if re.search(r'equal to the number of cards in (your|a) graveyard', low): return 5
        return default_star
    try: return int(sv)
    except: return 0

def mana_pips(mc):
    """(generico, {color: pips}, mascaras de hibridos).
    Un hibrido {B/G} cuesta 1 mana que DEBE ser B o G: se suma al generico para que el
    coste TOTAL cuadre con el cmc de Scryfall, y su mascara se guarda aparte para
    filtrar elegibilidad segun los colores del mazo."""
    mc = mc or ''
    gen = 0; pips = {'W':0,'U':0,'B':0,'R':0,'G':0}; hyb = []
    for sym in re.findall(r'\{([^}]+)\}', mc):
        if sym.isdigit(): gen += int(sym)
        elif sym in pips: pips[sym] += 1
        elif sym == 'X': gen += 1
        elif '/' in sym:
            parts = [q for q in sym.split('/') if q in pips]
            if 'P' in sym.split('/') and len(parts) == 1:
                pips[parts[0]] += 1                  # mana phyrexiano
            elif len(parts) >= 2:
                gen += 1; hyb.append(set(parts))     # hibrido de dos colores
            elif len(parts) == 1:
                gen += 1; hyb.append({parts[0]})     # {2/B} y similares
            else:
                gen += 1
        else: gen += 1
    return gen, pips, hyb


def entering_counters(txt):
    """'enters with N -1/-1 counters' o '+1/+1 counters' cambian la P/T real."""
    low = re.sub(r'\([^)]*\)', '', (txt or '').lower())
    m = re.search(r'enters with (\w+) ([+-])1/[+-]1 counters?', low)
    if not m: return 0
    n = num(m.group(1), 1)
    return n if m.group(2) == '+' else -n

def cost_reduction(c, txt):
    """Estima cuanto se abarata la carta en el mazo para el que fue disenada."""
    low = (txt or '').lower()
    tl  = (c.get('type_line') or '').lower()
    red = 0
    if 'affinity for artifacts' in low: red = max(red, 3)
    elif 'affinity for' in low:         red = max(red, 3)
    if re.search(r'\bdelve\b', low):    red = max(red, 3)
    if re.search(r'\bconvoke\b', low):  red = max(red, 3)
    if re.search(r'\bimprovise\b', low):red = max(red, 3)
    m = re.search(r'costs? \{(\d+)\} less to cast for each', low)
    if m: red = max(red, min(int(m.group(1))*4, 5))
    m = re.search(r'costs? \{(\d+)\} less to cast if', low)
    if m: red = max(red, int(round(int(m.group(1))*0.6)))
    m = re.search(r'this spell costs? \{(\d+)\} less to cast', low)
    if m and not re.search(r'for each|if ', low): red = max(red, int(m.group(1)))
    return red

def mana_ability(c, txt):
    """Criaturas y artefactos que producen mana. Devuelve cuanto (aprox)."""
    low = re.sub(r'\([^)]*\)', '', (txt or '').lower())
    tl = (c.get('type_line') or '').lower()
    if 'land' in tl: return 0
    if not re.search(r'\{t\}[^.]*:\s*add', low): return 0
    m = re.search(r'add \{[wubrgc]\}\{[wubrgc]\}', low)
    if m: return 2
    if re.search(r'add \{[wubrgc]\} for each', low): return 3
    if re.search(r'add [x\w]+ mana', low) or 'equal to the number' in low: return 2
    return 1

def convert(c):
    tl = c.get('type_line') or ''
    faces = c.get('card_faces') or []
    ff = faces[0] if faces else {}
    mc = c.get('mana_cost') or ff.get('mana_cost') or ''
    if '//' in mc: mc = mc.split('//')[0].strip()   # Adventure/MDFC: solo la cara frontal
    e = parse_card(c)
    hybrid = bool(re.search(r'\{[WUBRG]/[WUBRG]\}', mc))
    gen, pips, hyb = mana_pips(mc)
    _txt = (c.get('oracle_text') or '').strip() or ((ff.get('oracle_text') if ff else '') or '')
    _red = cost_reduction(c, _txt)
    # Si la carta tiene rebaja DINAMICA, esa manda y la estimacion plana no se aplica:
    # son dos modelos del mismo coste, no dos rebajas distintas.
    if e.get('cred'): _red = 0
    if _red: gen = max(0, gen - _red)
    _cmc = int(c.get('cmc') or ff.get('cmc') or 0)
    # APAGADO POR DEFECTO: CMCRED=1 para activarlo.
    # La reduccion baja 'gen' —lo que se paga— pero no 'cmc', que es lo que el motor usa
    # para DECIDIR: Cryptic Serpent queda pagable por 3 y valorado como un hechizo de 7.
    # Propagarlo es mas coherente y aun asi mide +0,027 (peor) y, lo que mas pesa,
    # DUPLICA la varianza entre semillas: sd 0,036 -> 0,061. Tiene sentido, porque esos
    # bichos enormes salen mucho antes y las partidas se vuelven mas extremas. Queda
    # apagado por la regla de no adoptar lo que no se puede demostrar.
    if _red and os.environ.get('CMCRED') == '1':
        _cmc = gen + sum(pips.values())
    # ---- locura: el coste que importa es el de locura, no el nominal ----
    # Fiery Temper vale {1}{R}{R} pero se lanza por {R} al descartarla, y Mono Red Madness
    # lleva once formas de descartar (Faithless Looting, Grab the Prize, Highway Robbery,
    # las fichas de Sangre del Epicure). Cobrarla a 3 es el mismo error que cobrar
    # Fireblast a 6. Ablacion: MADNESS=0.
    # Se asume que hay descarte disponible, que en este mazo es cierto por construccion.
    # Si algun dia entra al banco una carta con locura en un mazo SIN descarte, hay que
    # condicionarlo en vez de aplicarlo siempre.
    _mad = re.search(r'madness ((?:\{[^}]+\})+)', _txt or '', re.I)
    if _mad and os.environ.get('MADNESS') != '0':
        _g, _p, _h = mana_pips(_mad.group(1))
        gen, pips = _g, _p
        _cmc = _g + sum(_p.values())
    _alt, _altn = alt_cost(_txt)
    if os.environ.get('ALTCOST') == '0': _alt = _altn = 0   # ablacion
    return dict(
        alt=_alt, altn=_altn,
        name=c['name'], oracle_id=c.get('oracle_id'),
        cmc=_cmc,
        typ=type_code(tl if 'land' in tl.lower() or not faces else (ff.get('type_line') or tl)),
        colors=color_mask(c.get('colors') or ff.get('colors')),
        ci=color_mask(c.get('color_identity')),
        power=max(0, pt(c.get('power') or ff.get('power'), _txt) + entering_counters(_txt)),
        tough=max(1, pt(c.get('toughness') or ff.get('toughness'), _txt) + entering_counters(_txt))
               if (c.get('toughness') or ff.get('toughness')) is not None else 0,
        gen=gen, pips=pips, hybrid=hybrid, hyb=[sorted(h) for h in hyb],
        mana_out=mana_ability(c, _txt),
        produces=color_mask(c.get('produced_mana')),
        rarity=c.get('rarity'), usd=c.get('usd'),
        dyn=dyn_pt(c.get('power') or ff.get('power'), _txt),
        no_untap=1 if re.search(r"doesn't untap during (your|its controller's) untap step", (_txt or '').lower()) else 0,
        legal_std=(c.get('legalities') or {}).get('standard') == 'legal',
        legal_pau=(c.get('legalities') or {}).get('pauper') == 'legal',
        legal_brawl=(c.get('legalities') or {}).get('standardbrawl') == 'legal',
        **e)

if __name__ == '__main__':
    pool = json.load(open('data/pool.json'))
    conv = [dict(convert(c), qty=c['qty']) for c in pool]
    json.dump(conv, open('data/pool_eng.json','w'), ensure_ascii=False, indent=0)
    nonland = [c for c in conv if c['typ'] != 6]
    withfx = [c for c in nonland if c['eff'] != 0]
    print(f"total {len(conv)}  |  no-tierra {len(nonland)}  |  con efecto parseado {len(withfx)} ({100*len(withfx)/len(nonland):.0f}%)")
    import collections
    inv = {v:k for k,v in E.items()}
    print("\nefectos detectados:")
    for k,v in collections.Counter(inv[c['eff']] for c in nonland).most_common():
        print(f"   {k:<14} {v}")
    print("\nCRIATURAS SIN EFECTO parseado (revisar si alguna importa):")
    vanilla = [c for c in nonland if c['eff']==0 and c['typ']==1 and c['qty']>=2]
    for c in sorted(vanilla, key=lambda x:-x['qty'])[:25]:
        print(f"   x{c['qty']} {c['name'][:34]:<36} {c['cmc']}mv {c['power']}/{c['tough']} kw={c['kw']}")
    print("\nNO-CRIATURAS SIN EFECTO parseado:")
    nc = [c for c in nonland if c['eff']==0 and c['typ']!=1]
    for c in sorted(nc, key=lambda x:-x['qty'])[:25]:
        print(f"   x{c['qty']} {c['name'][:34]:<36} {c['cmc']}mv typ={c['typ']}")
