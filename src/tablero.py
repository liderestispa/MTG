# -*- coding: utf-8 -*-
"""Reproductor 2D de partidas simuladas: out/tablero.html

Corre N partidas con TRACE_JSON=N y arma una pagina que las reproduce sola, una tras
otra: las vidas bajando, las cartas entrando y saliendo, las tierras girandose, y el
registro de lo que pasa DENTRO de cada turno.

Sobre eso ultimo: el motor emite una foto al final de cada turno, y con solo las fotos
las partidas parecen vacias porque lo que entra y muere en el mismo turno no aparece
nunca. Por eso el motor emite ademas eventos (lanza / entra / sale) con su turno, y el
tablero los va cantando antes de pintar la foto resultante.

Es una herramienta de diagnostico. Sirve para ver POR QUE un mazo pierde. No saques
winrates de aqui: para eso estan los promedios sobre miles de partidas.

    python3 src/tablero.py pauper "Mono Red Madness" "Blue Terror" 8 12
    python3 src/tablero.py standard "Four-Color" "Izzet" 3 8
"""
import sys, os, json, io
sys.path.insert(0, 'src'); sys.path.insert(0, 'data')

TIPO = {0: 'otro', 1: 'criatura', 2: 'instantaneo', 3: 'conjuro', 4: 'encantamiento',
        5: 'planeswalker', 6: 'tierra', 7: 'artefacto', 8: 'batalla'}


def captura(fmt, yo, rival, seed, njuegos):
    import driver
    from driver import build, run
    R, opps = build(fmt)

    def busca(q):
        c = [o for o in opps if q.lower() in o[0].lower()]
        if not c: raise SystemExit(f"no encuentro '{q}' en {[o[0] for o in opps]}")
        return c[0]

    me, op = busca(yo), busca(rival)
    os.environ['TRACE_JSON'] = str(njuegos)
    run(R, [(op[0], 1000, op[2])], [me[2]], ngames=njuegos, life=20, seed=seed)
    os.environ.pop('TRACE_JSON', None)

    juegos, act, pend = [], None, []
    for linea in (driver.LAST_STDERR or '').splitlines():
        if not linea.startswith('@J '): continue
        d = json.loads(linea[3:])
        if 'juego' in d:
            act = {'n': d['juego'], 'salida': d['salida'], 'turnos': [], 'fin': None}
            juegos.append(act); pend = []
        elif act is None:
            continue
        elif 'ev' in d:
            pend.append([d['ev'], d['p'], d['id']])
        elif 'fin' in d:
            act['fin'] = d
        else:
            d['evs'] = pend; pend = []
            act['turnos'].append(d)
    juegos = [g for g in juegos if g['turnos']]

    usados = set()
    for g in juegos:
        for t in g['turnos']:
            for lado in ('A', 'B'):
                for x in t[lado]['lands']: usados.add(x[0])
                for x in t[lado]['bf']:    usados.add(x[0])
            for e in t['evs']: usados.add(e[2])
    cat = {i: {'n': R.meta.get(i, f'#{i}'),
               'tp': TIPO.get(R.defs[i]['typ'], 'otro'),
               'cmc': R.defs[i]['cmc']} for i in usados}
    return juegos, cat, me[0], op[0]


PAGINA = r"""<!doctype html><meta charset="utf-8">
<title>Tablero — %(yo)s vs %(rival)s</title>
<style>
 :root{--bg:#0b1220;--pan:#111c31;--bor:#1e293b;--txt:#e2e8f0;--ten:#94a3b8}
 body{background:var(--bg);color:var(--txt);font:13px/1.45 system-ui,sans-serif;
      margin:0 auto;padding:16px;max-width:1020px}
 h1{font-size:17px;margin:0 0 2px} .sub{color:var(--ten);font-size:12px;margin:0 0 13px}
 .ctrl{display:flex;gap:10px;align-items:center;background:var(--pan);
       border:1px solid var(--bor);border-radius:9px;padding:10px 13px;margin-bottom:11px;
       position:sticky;top:0;z-index:5;flex-wrap:wrap}
 button{background:#1e40af;color:#fff;border:0;border-radius:6px;padding:7px 15px;
        font-size:13px;cursor:pointer;font-weight:600}
 button:hover{background:#2563eb}
 .marc{background:#0b1220;border:1px solid var(--bor);border-radius:6px;padding:4px 10px;
       font-size:12px;color:var(--ten)} .marc b{color:var(--txt)}
 .lado{border:1px solid var(--bor);border-radius:10px;padding:11px 13px;margin-bottom:8px;
       background:var(--pan);transition:border-color .18s,box-shadow .18s}
 .lado.activo{border-color:#3b82f6;box-shadow:0 0 0 1px #3b82f6 inset}
 .cab{display:flex;align-items:center;gap:12px;margin-bottom:8px;flex-wrap:wrap}
 .nom{font-weight:600;font-size:14px} .yo .nom{color:#60a5fa} .riv .nom{color:#f472b6}
 .vida{font-size:26px;font-weight:700;min-width:50px;transition:color .3s,transform .2s}
 .vida.baja{color:#f87171;transform:scale(1.14)} .vida.sube{color:#4ade80}
 .z{color:var(--ten);font-size:11px}
 .fila{display:flex;gap:5px;flex-wrap:wrap;min-height:24px;align-items:flex-start}
 .et{font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:var(--ten);
     margin:7px 0 3px}
 .c{border-radius:5px;padding:4px 7px;font-size:11px;border:1px solid;line-height:1.25;
    animation:ent .25s ease-out;max-width:152px}
 @keyframes ent{from{opacity:0;transform:translateY(-6px) scale(.9)}to{opacity:1}}
 .c.criatura{background:#14532d33;border-color:#4ade8066;color:#bbf7d0}
 .c.tierra{background:#44403c44;border-color:#a8a29e55;color:#e7e5e4;padding:3px 6px}
 .c.artefacto{background:#37415144;border-color:#9ca3af66;color:#e5e7eb}
 .c.encantamiento{background:#4c1d9544;border-color:#a78bfa66;color:#ddd6fe}
 .c.planeswalker{background:#78350f44;border-color:#fbbf2466;color:#fde68a}
 .c.otro,.c.batalla,.c.instantaneo,.c.conjuro{background:#1e293b;border-color:#475569;color:#cbd5e1}
 .c.gir{opacity:.4;transform:rotate(7deg)} .pt{font-weight:700;margin-left:4px}
 .sick{border-style:dashed}
 .log{background:#0b1220;border:1px solid var(--bor);border-radius:8px;padding:8px 11px;
      min-height:52px;font-size:12px;margin-bottom:8px}
 .ev{display:inline-block;margin:2px 5px 2px 0;padding:2px 8px;border-radius:11px;
     font-size:11px;animation:ent .2s}
 .ev.lanza{background:#1e3a8a55;color:#bfdbfe;border:1px solid #3b82f655}
 .ev.entra{background:#14532d55;color:#bbf7d0;border:1px solid #4ade8055}
 .ev.sale{background:#7f1d1d55;color:#fecaca;border:1px solid #f8717155}
 .fin{background:#052e16;border:1px solid #4ade80;border-radius:8px;padding:9px 13px;
      margin-top:8px;display:none} .fin.ver{display:block} .fin b{color:#4ade80}
 .aviso{border-left:3px solid #fbbf24;padding:7px 11px;background:#1c1917;color:#d6d3d1;
        font-size:11px;border-radius:0 6px 6px 0;margin-top:13px}
</style>
<h1>%(yo)s <span style="color:#64748b">vs</span> %(rival)s</h1>
<p class="sub">%(nj)s partidas seguidas, semilla %(seed)s, formato %(fmt)s. Generado por <code>src/tablero.py</code>.</p>
<div class="ctrl">
  <button id="pp">⏸ Pausa</button>
  <button id="re">↻ Desde el principio</button>
  <span class="marc">partida <b id="gn">1</b>/%(nj)s</span>
  <span class="marc">turno <b id="tn">1</b></span>
  <span class="marc">marcador <b id="mk">0–0</b></span>
  <span class="z">velocidad</span>
  <input type="range" id="vel" min="70" max="1500" value="1000" style="width:130px">
</div>
<div class="log" id="log"><span class="z">…</span></div>
<div id="riv" class="lado riv"></div>
<div id="yo" class="lado yo"></div>
<div id="fin" class="fin"></div>
<p class="aviso"><b>Son partidas sueltas, no una medición.</b> Esto muestra el mecanismo:
si un mazo se atasca de tierras, si nunca llega a lanzar su remate, si el rival lo desborda.
Los winrates salen de promediar miles de partidas, no de mirar estas.</p>
<script>
const G=%(juegos)s, CAT=%(cat)s, NOM={A:%(yo_j)s,B:%(rival_j)s};
const $=s=>document.querySelector(s);
let g=0,i=0,tocando=true,timer=null,prev={A:20,B:20},win={A:0,B:0};

function nom(id){ return (CAT[id]||{n:'#'+id}).n; }
function carta(x,esTierra){
  const [id,tap,p,t,sick]=esTierra?[x[0],x[1],null,null,0]:x;
  const c=CAT[id]||{n:'#'+id,tp:'otro'};
  const cl=['c',c.tp,tap?'gir':'',sick?'sick':''].filter(Boolean).join(' ');
  const pt=(c.tp==='criatura'&&p!==null)?`<span class="pt">${p}/${t}</span>`:'';
  return `<div class="${cl}" title="${c.n}${c.cmc!==undefined?' · cmc '+c.cmc:''}">${c.n}${pt}</div>`;
}
function lado(el,d,quien,activo){
  const dv=d.life-prev[quien];
  const cls=dv<0?'vida baja':(dv>0?'vida sube':'vida');
  el.className='lado '+(quien==='A'?'yo':'riv')+(activo?' activo':'');
  el.innerHTML=`<div class="cab"><span class="nom">${NOM[quien]}</span>
     <span class="${cls}">${d.life}</span>
     <span class="z">mano ${d.hand} · biblioteca ${d.deck} · permanentes ${d.bf.length}</span></div>
   <div class="et">campo de batalla</div>
   <div class="fila">${d.bf.length?d.bf.map(x=>carta(x,false)).join(''):'<span class="z">vacío</span>'}</div>
   <div class="et">tierras (${d.lands.length})</div>
   <div class="fila">${d.lands.length?d.lands.map(x=>carta(x,true)).join(''):'<span class="z">ninguna</span>'}</div>`;
}
const VERBO={lanza:'lanza',entra:'entra',sale:'se va'};
function pinta(){
  const J=G[g], s=J.turnos[i]; if(!s) return;
  lado($('#riv'),s.B,'B',s.act==='B');
  lado($('#yo'), s.A,'A',s.act==='A');
  prev={A:s.A.life,B:s.B.life};
  $('#gn').textContent=J.n; $('#tn').textContent=s.t;
  $('#mk').textContent=`${win.A}–${win.B}`;
  $('#log').innerHTML = s.evs.length
    ? s.evs.map(e=>`<span class="ev ${e[0]}">${NOM[e[1]].slice(0,14)}: ${VERBO[e[0]]} ${nom(e[2])}</span>`).join('')
    : '<span class="z">sin jugadas este turno</span>';
  const f=$('#fin');
  if(i===J.turnos.length-1&&J.fin){ f.className='fin ver';
    f.innerHTML=`<b>Gana ${NOM[J.fin.fin]}</b> en el turno ${J.fin.turno}.`; }
  else f.className='fin';
}
function paso(){
  const J=G[g];
  if(i<J.turnos.length-1){ i++; pinta(); return; }
  if(J.fin) win[J.fin.fin]++;
  if(g<G.length-1){ g++; i=0; prev={A:20,B:20}; pinta(); }
  else parar();
}
function ritmo(){ return +$('#vel').max - +$('#vel').value + 70; }
function arranca(){ clearInterval(timer); timer=setInterval(paso,ritmo());
  tocando=true; $('#pp').textContent='⏸ Pausa'; }
function parar(){ tocando=false; clearInterval(timer); $('#pp').textContent='▶ Reproducir'; }
$('#pp').onclick=()=>tocando?parar():arranca();
$('#re').onclick=()=>{ g=0;i=0;win={A:0,B:0};prev={A:20,B:20};pinta();arranca(); };
$('#vel').oninput=()=>{ if(tocando) arranca(); };
pinta(); arranca();
</script>"""


def main():
    fmt   = sys.argv[1] if len(sys.argv) > 1 else 'pauper'
    yo    = sys.argv[2] if len(sys.argv) > 2 else 'Mono Red Madness'
    rival = sys.argv[3] if len(sys.argv) > 3 else 'Blue Terror'
    seed  = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    nj    = int(sys.argv[5]) if len(sys.argv) > 5 else 12
    juegos, cat, nyo, nriv = captura(fmt, yo, rival, seed, nj)
    if not juegos:
        raise SystemExit("el motor no emitio traza: ¿recompilaste sim.c con el bloque TRACE_JSON?")
    html = PAGINA % dict(
        yo=nyo, rival=nriv, seed=seed, fmt=fmt, nj=len(juegos),
        yo_j=json.dumps(nyo, ensure_ascii=False), rival_j=json.dumps(nriv, ensure_ascii=False),
        juegos=json.dumps(juegos, separators=(',', ':')),
        cat=json.dumps(cat, ensure_ascii=False, separators=(',', ':')))
    io.open('out/tablero.html', 'w', encoding='utf-8').write(html)
    gana = sum(1 for j in juegos if j['fin'] and j['fin']['fin'] == 'A')
    evs = sum(len(t['evs']) for j in juegos for t in j['turnos'])
    print(f"escrito out/tablero.html — {len(juegos)} partidas, "
          f"{sum(len(j['turnos']) for j in juegos)} turnos, {evs} jugadas, "
          f"{len(cat)} cartas distintas. {nyo} gana {gana}/{len(juegos)}.")


if __name__ == '__main__':
    main()
