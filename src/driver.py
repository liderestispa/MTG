import json, subprocess, sys, unicodedata, os
sys.path.insert(0,'src'); sys.path.insert(0,'data')
from extract import convert
from meta_decks import DECKS

# ---- prioridad de los procesos del simulador ----
# Sin esto, lanzar el motor en muchos nucleos deja la maquina inusable: Windows reparte
# CPU por igual y el escritorio se queda sin turno. Con prioridad IDLE el sistema solo
# les da los ciclos que nadie mas quiere, asi que puedes seguir trabajando mientras
# corre. Cuesta muy poco rendimiento cuando la maquina esta libre, porque entonces
# "los ciclos que nadie quiere" son todos.
# PRIORIDAD_NORMAL=1 lo desactiva.
_FLAGS = 0
if os.name == 'nt' and os.environ.get('PRIORIDAD_NORMAL') != '1':
    _FLAGS = getattr(subprocess, 'IDLE_PRIORITY_CLASS', 0x00000040)

def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii','ignore').decode().lower()
    return ''.join(ch for ch in s if ch.isalnum())

_ORACLE=None; _FRONT=None
def oracle():
    global _ORACLE,_FRONT
    if _ORACLE is None:
        _ORACLE={}; _FRONT={}
        # BUG CORREGIDO: el bulk trae 910 entradas de FICHA y 2.243 de art series.
        # 88 nombres existen a la vez como ficha y como carta real (Starscape Cleric,
        # Darkstar Augur, Ajani's Pridemate...). Si gana la ficha, la carta queda con
        # legalidad 'not_legal' y estadisticas de ficha. La carta real manda siempre.
        def _es_basura(c):
            lay=(c.get('layout') or '')
            return ('token' in lay or lay=='art_series' or lay=='vanguard'
                    or (c.get('type_line') or '').startswith('Token'))
        buenas={}; fichas={}
        for line in open('data/oracle.jsonl', encoding='utf-8'):
            c=json.loads(line)
            (fichas if _es_basura(c) else buenas).setdefault(norm(c['name']), c)
            if '//' in c['name'] and not _es_basura(c):
                _FRONT.setdefault(norm(c['name'].split('//')[0]), c)
        _ORACLE=dict(fichas); _ORACLE.update(buenas)   # la carta real pisa a la ficha
    return _ORACLE,_FRONT
def lookup(name):
    O,F=oracle(); k=norm(name); return O.get(k) or F.get(k)

LAST_STDERR = ''   # stderr del ultimo run(): lo consume src/tablero.py

# Que binario se usa. En Windows no se puede reenlazar bin_sim.exe mientras haya un
# proceso usandolo: si el orquestador esta corriendo, gcc falla con "Permission denied"
# y no hay forma de probar un build nuevo sin parar el trabajo de horas. Con esto se
# compila a otro nombre y se prueba en paralelo:
#     gcc -O3 -w -o bin_prueba src/sim.c -lm
#     BIN_SIM=./bin_prueba python3 src/obj_real.py 2000
BIN = os.environ.get('BIN_SIM') or './bin_sim'

URZA = {"Urza's Mine","Urza's Power Plant","Urza's Tower"}

class Registry:
    def __init__(self):
        self.defs=[]; self.idx={}; self.meta={}
    def add(self, card):
        oid=card.get('oracle_id') or card['name']
        if oid in self.idx: return self.idx[oid]
        e=convert(card)
        if card['name'] in URZA:
            # Tron ensamblado da 7 mana incoloro con 3 tierras -> ~2.3 cada una
            e = dict(e, produces=0, mana_out=2)
        i=len(self.defs); self.idx[oid]=i; self.defs.append(e); self.meta[i]=card['name']
        return i
    def add_by_name(self,name):
        c=lookup(name)
        if c is None: raise KeyError(name)
        return self.add(c)
    def line(self,e):
        P=e['pips']
        return ' '.join(str(x) for x in [
            e['cmc'], e['typ'], e['colors'], e['produces'], e['gen'], 1 if e['hybrid'] else 0,
            P['W'],P['U'],P['B'],P['R'],P['G'], e['kw'], e['eff'], e['eff2'],
            e['p1'],e['p2'],e['p3'],e['q1'],e['q2'], e['power'], e['tough'],
            e.get('mana_out', 0), e.get('dyn', 0), e.get('no_untap', 0),
            e.get('eff3', 0), e.get('r1', 0), e.get('r2', 0),
            e.get('alt', 0), e.get('altn', 0),
            e.get('die_eff', 0), e.get('die_p1', 0),
            e.get('act_eff', 0), e.get('act_p1', 0), e.get('act_cost', 0),
            e.get('cred', 0), e.get('cond', 0), e.get('es_leg', 0),
            e.get('tax_atk', 0), e.get('entra_girada', 0),
            e.get('atk_eff', 0), e.get('atk_p1', 0),
            e.get('coste_extra', 0)])

def build(fmt):
    R=Registry()
    opps=[]
    for dn,w,cs in DECKS[fmt]:
        ids=[]
        for n,name in cs:
            i=R.add_by_name(name)
            ids += [i]*n
        opps.append((dn,w,ids))
    return R,opps

def run(R, opps, variants, ngames=200, life=20, maxturn=14, seed=12345):
    inp=[str(len(R.defs))]
    for e in R.defs: inp.append(R.line(e))
    inp.append(str(len(opps)))
    for dn,w,ids in opps:
        inp.append(f"{w} {len(ids)} " + ' '.join(map(str,ids)))
    inp.append(f"{ngames} {life} {maxturn} {seed}")
    inp.append(str(len(variants)))
    for v in variants:
        inp.append(f"{len(v)} " + ' '.join(map(str,v)))
    import os as _os
    out = subprocess.run([_os.environ.get('BIN_SIM') or BIN], input='\n'.join(inp), capture_output=True,
                         text=True, env=dict(_os.environ), creationflags=_FLAGS)
    global LAST_STDERR
    LAST_STDERR = out.stderr          # lo usa src/tablero.py para leer la traza JSON
    if out.returncode!=0:
        raise RuntimeError(out.stderr[:500])
    if _os.environ.get('TRACE') and out.stderr:
        sys.stderr.write(out.stderr)
    rows=[l.split() for l in out.stdout.strip().split('\n') if l.strip()]
    K=['wr','noplay14','screw','spells6','firstplay','gamelen','cast','removal',
       'kills','sweep','counters','handend','manascrew','cseen','untap_at_counter','res_avg','win_dmg','lose_dmg','timeout',
       'hA3','hA6','hA9','hB3','hB6','hB9','disc_try','disc_hit','disc_handsz']
    out=[]
    for r in rows:
        d={'wr':int(r[0])/1e6}
        for i,k in enumerate(K[1:],start=1):
            d[k]=float(r[i]) if i<len(r) else 0.0
        out.append(d)
    return out

def per_matchup(R,opps,deck,ngames=400,life=20,maxturn=14,seed=999):
    res={}
    for dn,w,ids in opps:
        r=run(R,[(dn,1000,ids)],[deck],ngames,life,maxturn,seed)
        res[dn]=r[0]
    return res
