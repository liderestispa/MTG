# -*- coding: utf-8 -*-
"""Genera out/motor_v4.html a partir de out/report_v4.json + out/calib_v4.json"""
import json, html, os

D = json.load(open('out/report_v4.json'))
C = json.load(open('out/calib_v4.json')) if os.path.exists('out/calib_v4.json') else {}

# valores de la revision anterior (v3) para la columna "antes"
V3 = {'standard': 11.70, 'pauper': 8.70, 'brawl': 12.90, 'global': 11.06}
NOM = {'standard':'Standard', 'pauper':'Pauper', 'brawl':'Standard Brawl'}

CSS = """
:root{--bg:#0f1115;--card:#171a21;--ink:#e8eaed;--dim:#9aa3af;--line:#252a33;--ok:#4ade80;--warn:#fbbf24;--bad:#f87171;--acc:#7dd3fc}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:1060px;margin:0 auto;padding:32px 20px 80px}
h1{font-size:27px;margin:0 0 4px;letter-spacing:-.02em} .sub{color:var(--dim);margin:0 0 30px;font-size:14px}
h2{font-size:19px;margin:42px 0 14px;padding-bottom:8px;border-bottom:1px solid var(--line)} h3{font-size:17px;margin:0 0 12px}
.col{font-weight:400;color:var(--acc);font-size:13px;margin-left:6px}
section.deck,.box{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:20px;margin-bottom:18px}
.box.good{border-left:3px solid var(--ok)} .box.warn2{border-left:3px solid var(--warn)} .box.bad{border-left:3px solid var(--bad)}
.box.info{border-left:3px solid var(--acc)}
.grid{display:grid;grid-template-columns:1.3fr 1fr;gap:24px} @media(max-width:820px){.grid{grid-template-columns:1fr}}
table{width:100%;border-collapse:collapse;font-size:13.5px}
.list td{padding:3px 6px;border-bottom:1px solid #1d222a}
.list .q{width:26px;color:var(--acc);font-weight:600} .list .mc{width:92px;color:var(--dim);font-family:ui-monospace,monospace;font-size:12px}
.list .pt{width:74px;color:var(--dim);text-align:right;font-size:12px}
tr.band td{padding-top:10px;color:var(--dim);font-size:11px;text-transform:uppercase;letter-spacing:.08em;border:0}
.lands{font-size:13px;color:var(--dim);margin:12px 0 4px} .tot{font-size:13px;color:var(--dim);margin:0} .ok{color:var(--ok)} .bad{color:var(--bad)} .warn{color:var(--warn)}
.cmd{background:#1e2430;border-left:3px solid var(--acc);padding:8px 12px;border-radius:4px;margin-bottom:14px;font-weight:600}
.cmd span{display:block;font-size:11px;color:var(--dim);text-transform:uppercase;letter-spacing:.08em;font-weight:400}
.stat{background:#12161d;border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin-bottom:10px}
.stat span{display:block;font-size:12px;color:var(--dim)} .stat b{font-size:19px;color:var(--ok)}
.stat small{display:block;color:#6b7280;font-size:11px;margin-top:2px}
th{text-align:left;font-size:11px;color:var(--dim);text-transform:uppercase;letter-spacing:.06em;padding:6px;border-bottom:1px solid var(--line)}
td{padding:5px 6px;border-bottom:1px solid #1d222a} .r{text-align:right} .idx{color:var(--warn)}
ul{padding-left:20px} li{margin:7px 0} code{background:#12161d;padding:1px 5px;border-radius:4px;font-size:12.5px;color:var(--acc)}
ol{padding-left:22px} ol li{margin:5px 0}
.mono{font-family:ui-monospace,monospace;font-size:12px}
.mtx td,.mtx th{font-size:11.5px;padding:4px 5px}
.tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:20px;border:1px solid var(--line);color:var(--dim);margin-left:6px}
"""

def esc(s): return html.escape(str(s))

def deck_html(k):
    d = D[k]
    bands = {}
    for c in d['sp']: bands.setdefault(c['cmc'], []).append(c)
    rows = []
    for cmc in sorted(bands):
        rows.append(f"<tr class='band'><td colspan='4'>{cmc} mana</td></tr>")
        for c in sorted(bands[cmc], key=lambda x: (-x['n'], x['name'])):
            rows.append(f"<tr><td class='q'>{c['n']}</td><td>{esc(c['name'])}</td>"
                        f"<td class='mc'>{esc(c['mc'])}</td><td class='pt'>{esc(c['pt'])}</td></tr>")
    lands = " · ".join(f"{n} {esc(nm)}" for nm, n in sorted(d['la'].items(), key=lambda x: -x[1]))
    cmd = f"<div class='cmd'><span>Comandante</span>{esc(d['cmd'])}</div>" if d.get('cmd') else ""
    mm = "".join(f"<tr><td>{esc(n)}</td><td class='r'>{w:.1f}%</td><td class='r idx'>{i:.0f}</td></tr>"
                 for n, w, i in d['mm'])
    tot = d['ns'] + d['nl']
    totlab = f"{d['ns']} hechizos + {d['nl']} tierras = <b class='ok'>{tot}</b>" + (" + comandante" if d.get('cmd') else "")
    return f"""<section class="deck">
<h3>{esc(d['t'])}<span class="col">{esc(d['col'])}</span></h3>
{cmd}
<div class="grid"><div>
<table class="list"><tbody>{''.join(rows)}</tbody></table>
<p class="lands"><b>Tierras ({d['nl']}):</b> {lands}</p>
<p class="tot">{totlab}</p>
</div><div>
<div class="stat"><span>Ventaja sobre la semilla codiciosa</span><b>{esc(d['gain'])}</b>
<small>lo que aportó la búsqueda por haz sobre "meter las mejores cartas"</small></div>
<table><thead><tr><th>Rival del meta</th><th class="r">Peso</th><th class="r">Índice</th></tr></thead><tbody>{mm}</tbody></table>
<p class="tot" style="margin-top:8px">El índice no es un winrate real: es la nota del motor, que infla tus cartas de sobre (ver más abajo).</p>
</div></div></section>"""

# ---- tabla de calibracion ----
def calib_rows():
    out = []
    for k in ['standard', 'pauper', 'brawl']:
        c = C.get(k)
        if not c:
            out.append(f"<tr><td>{NOM[k]}</td><td class='r'>{V3[k]:.2f}</td><td class='r dim'>—</td><td class='r'>—</td><td class='r'>—</td></tr>")
            continue
        r4 = c['rmse'] * 100
        delta = r4 - V3[k]
        cls = 'ok' if delta < 0 else 'warn'
        out.append(f"<tr><td>{NOM[k]}</td><td class='r'>{V3[k]:.2f}</td>"
                   f"<td class='r {cls}'><b>{r4:.2f}</b></td>"
                   f"<td class='r'>{c['spread']*100:.1f}</td>"
                   f"<td class='r'>{c['outside']}/{len(c['field'])}</td></tr>")
    if 'global' in C:
        g = C['global'] * 100
        cls = 'ok' if g < V3['global'] else 'warn'
        out.append(f"<tr><td><b>Global</b></td><td class='r'>{V3['global']:.2f}</td>"
                   f"<td class='r {cls}'><b>{g:.2f}</b></td><td class='r'></td><td class='r'></td></tr>")
    return "".join(out)

def matrix_html(k):
    c = C.get(k)
    if not c: return ""
    n = c['names']; M = c['matrix']; f = c['field']
    sh = [x[:11] for x in n]
    head = "".join(f"<th class='r'>{esc(x)}</th>" for x in sh)
    body = []
    for i, nm in enumerate(n):
        cells = []
        for j in range(len(n)):
            v = M[i][j] * 100
            cl = '' if 40 <= v <= 60 else ('bad' if v < 40 else 'warn')
            if i == j: cells.append("<td class='r' style='color:#3d4450'>—</td>")
            else: cells.append(f"<td class='r {cl}'>{v:.0f}</td>")
        fv = f[i] * 100
        fcl = 'ok' if 40 <= fv <= 60 else ('bad' if fv < 40 else 'warn')
        body.append(f"<tr><td>{esc(nm)}</td>{''.join(cells)}<td class='r {fcl}'><b>{fv:.1f}</b></td></tr>")
    return (f"<h3 style='margin-top:18px'>{NOM[k]}</h3><table class='mtx'><thead><tr><th></th>{head}"
            f"<th class='r'>Campo</th></tr></thead><tbody>{''.join(body)}</tbody></table>")

real_brawl = ""
if C.get('brawl', {}).get('real'):
    rb = C['brawl']['real']
    rows = "".join(f"<tr><td>{esc(n)}</td><td class='r'>{fv*100:.1f}%</td><td class='r'>{rv*100:.0f}%</td>"
                   f"<td class='r'>{(fv-rv)*100:+.1f}</td></tr>" for n, fv, rv in rb['rows'])
    real_brawl = f"""<div class="box info">
<h3>Brawl: por qué el 50% es la vara equivocada</h3>
<p>El meta de Standard Brawl no es plano. Elspeth y Ketramose ganan mucho más del 50% en la vida real,
así que exigirle al motor que los deje en 50% sería exigirle que se equivoque. La comparación honesta es
contra los winrates publicados:</p>
<table><thead><tr><th>Mazo</th><th class="r">Motor</th><th class="r">Real</th><th class="r">Error</th></tr></thead><tbody>{rows}</tbody></table>
<p style="margin-bottom:0">Desplazamiento constante <b>{rb['offset']*100:+.1f} pts</b> ·
residuo máximo <b class="ok">{rb['resid_max']*100:.1f} pts</b>. Un desplazamiento parejo no molesta: significa
que el motor mide bajo pero <em>ordena bien</em>. El residuo es lo que importa, y es lo que se optimizó.</p>
</div>"""

HTML = f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>MTG — Motor v4 (tercera revisión)</title>
<style>{CSS}</style></head><body><div class="wrap">
<h1>Tercera revisión del motor</h1>
<p class="sub">16 ago 2026 · dos ideas buenas que resultaron falsas, una que funcionó, y los tres mazos revalidados</p>

<h2>Calibración: dónde quedó el motor</h2>
<div class="box good">
<table><thead><tr><th>Formato</th><th class="r">RMSE v3</th><th class="r">RMSE v4</th><th class="r">Dispersión</th><th class="r">Fuera de 40-60%</th></tr></thead>
<tbody>{calib_rows()}</tbody></table>
<p style="margin-bottom:0"><b>RMSE</b> = cuánto se desvía del 50% el mazo promedio del meta cuando juegan todos contra todos.
Si el motor entendiera Magic perfectamente y el meta fuera parejo, daría 0. A menor número, más fiable el motor.
{C.get('standard',{}).get('ngames','1800')} juegos por enfrentamiento.</p>
</div>

{real_brawl}

<h2>Lo que se probó en esta revisión</h2>

<div class="box bad">
<h3>Bloqueo en grupo — implementado, correcto, y apagado <span class="tag">descartado</span></h3>
<p>El motor solo dejaba bloquear un atacante con una criatura. Implementé el bloqueo múltiple completo:
varios bloqueadores por atacante, orden de asignación de daño, y desborde por arrollar. También hice que
el atacante <em>anticipe</em> el bloqueo en grupo antes de decidir atacar.</p>
<p>Es más correcto según las reglas. Y empeoró la calibración: el residuo contra winrates reales
subió de <b>4,0 a 8,0 pts</b>, de forma monótona conforme subía el peso de la regla.</p>
<p style="margin-bottom:0">Lo dejé en el código con <code>GANG_ON=0</code> y un comentario explicando por qué.
La lección: <b>una regla más fiel no siempre da un motor más fiel</b>, porque los otros errores del motor
estaban compensándose entre sí. Añadir realismo por un lado desbalancea lo que ya estaba cuadrado.</p>
</div>

<div class="box bad">
<h3>Segundo intento de lanzamiento cuando la reserva paraliza <span class="tag">descartado</span></h3>
<p>Rastreé a Eluge y encontré que llega al turno 7 con el campo vacío: guarda maná para instantáneos
que nunca llega a usar. Probé una regla de segunda pasada — si no tienes nada en mesa, ignora la reserva y juega algo.</p>
<p style="margin-bottom:0">Global pasó de 11,06 a <b>11,42</b>. Peor. Revertido.</p>
</div>

<div class="box good">
<h3>Ajuste de umbrales por descenso coordenada a coordenada <span class="tag">adoptado</span></h3>
<p>Los números que gobiernan cuándo la IA bloquea, intercambia o guarda maná estaban puestos a ojo.
Los expuse como parámetros (<code>TH_TRADE</code>, <code>TH_PERFECT</code>, <code>TH_WALL</code>,
<code>TH_BADBLOCK</code>, <code>RESERVE_MAX</code>, <code>SWEEP_MIN</code>) y los barrí uno por uno
contra el banco de calibración.</p>
<p style="margin-bottom:0">Resultado: <b class="ok">11,07 → 10,35</b>, con dos cambios que importan:
<code>TH_TRADE 10 → 4</code> (intercambiar es mejor de lo que yo creía) y
<code>TH_BADBLOCK −14 → −22</code> (bloquear mal es peor de lo que yo creía).</p>
</div>

<div class="box info">
<h3>Lo que descarté antes de gastar tiempo</h3>
<p style="margin-bottom:0">Mide qué porcentaje del meta usa tipos de carta que el motor no modela:
planeswalkers <b>1,7%</b>, sagas <b>0,7%</b>, equipo <b>0,3%</b>, auras <b>0,6%</b>. Suman menos del 4%.
No es ahí donde está el error, así que no toqué eso.</p>
</div>

<h2>Los tres mazos, revalidados</h2>
<p class="sub" style="margin-bottom:18px">Después de cambiar el motor hay que volver a comprobar que el mazo
sigue ganándole a su propia semilla. En la revisión anterior el de Brawl había caído a −1,58 — es decir,
la búsqueda había estado optimizando contra un motor equivocado. Ahora los tres vuelven a ganar.</p>
{deck_html('brawl')}
{deck_html('standard')}
{deck_html('pauper')}

<h2>Matrices completas del meta</h2>
<div class="box">
<p>Cada fila es cuánto gana ese mazo contra cada columna. Verde/blanco = dentro de 40-60%.
Estas son las casillas que el motor todavía lee mal.</p>
{matrix_html('standard')}
{matrix_html('pauper')}
{matrix_html('brawl')}
</div>

<h2>El límite que no se arregla ajustando</h2>
<div class="box warn2">
<p>Tus cartas de sobre promedian <b>2,04 puntos de fuerza/resistencia por maná</b>. Los mazos del meta
promedian entre <b>1,32 y 1,90</b>. No es que tus cartas sean mejores: es que las cartas de Limitado se
pagan en cuerpo y las de Construido se pagan en habilidad.</p>
<p>El motor mide cuerpos muy bien y habilidades a medias. Por eso te da índices del 85-95% en Standard
contra mazos que en la tienda te ganarían. <b>Los índices sirven para comparar tus propias listas entre sí,
no para predecir la mesa.</b></p>
<p style="margin-bottom:0">Lo que sí es fiable: el orden relativo, las curvas de maná, el conteo de tierras,
y que cada lista es legal y armable con las cartas que tienes físicamente.</p>
</div>

<h2>Lo que sigue roto — y es justo tu estilo</h2>
<div class="box bad">
<p>Los arquetipos de prisión y descarte siguen subestimados. El motor le da a Tinybones un <b>~29%</b>
cuando en la vida real ronda el <b>55%</b>. Cuatro Colores Control se queda en <b>34,6%</b>,
Orzhov Lifegain en <b>39,6%</b>, Tifa en <b>31,2%</b> y Eluge en <b>30,6%</b>.</p>
<p style="margin-bottom:0">El patrón es claro: el motor no sabe valorar <em>negarle el juego al rival</em>.
Sabe contar daño y cuerpos. Un mazo que gana por asfixia le parece un mazo que no hace nada.
Y eso es precisamente lo que tú quieres jugar — así que ese es el siguiente frente de trabajo,
no un detalle.</p>
</div>

</div></body></html>"""

open('out/motor_v4.html', 'w', encoding='utf-8').write(HTML)
print(f"escrito out/motor_v4.html  ({len(HTML)} bytes)")
