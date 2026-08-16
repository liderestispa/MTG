# -*- coding: utf-8 -*-
"""Artefacto de mazos v4: las tres listas para llevar a la tienda."""
import json, html
D=json.load(open('out/report_v6.json'))
MC=json.load(open('out/mis_decks_cal.json')); FC=json.load(open('out/final_c4.json'))
CONF={'brawl':'sin validar — es el formato donde menos dato real existe',
      'standard':'construcción fiable, orden sin validar (r=+0,12)',
      'pauper':'el único con respaldo medido y cruzado (r=+0,72)'}
def esc(s): return html.escape(str(s))
CSS="""
:root{--bg:#0f1115;--card:#171a21;--ink:#e8eaed;--dim:#9aa3af;--line:#252a33;--ok:#4ade80;--warn:#fbbf24;--bad:#f87171;--acc:#7dd3fc}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:1000px;margin:0 auto;padding:30px 20px 70px}
h1{font-size:26px;margin:0 0 4px;letter-spacing:-.02em}.sub{color:var(--dim);margin:0 0 26px;font-size:14px}
h2{font-size:19px;margin:38px 0 14px;padding-bottom:8px;border-bottom:1px solid var(--line)}h3{font-size:17px;margin:0 0 12px}
.col{font-weight:400;color:var(--acc);font-size:13px;margin-left:6px}
section.deck,.box{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:20px;margin-bottom:18px}
.box.good{border-left:3px solid var(--ok)}.box.warn2{border-left:3px solid var(--warn)}.box.info{border-left:3px solid var(--acc)}
.grid{display:grid;grid-template-columns:1.3fr 1fr;gap:24px}@media(max-width:820px){.grid{grid-template-columns:1fr}}
table{width:100%;border-collapse:collapse;font-size:13.5px}
.list td{padding:3px 6px;border-bottom:1px solid #1d222a}
.list .q{width:26px;color:var(--acc);font-weight:600}.list .mc{width:92px;color:var(--dim);font-family:ui-monospace,monospace;font-size:12px}
.list .pt{width:74px;color:var(--dim);text-align:right;font-size:12px}
tr.band td{padding-top:10px;color:var(--dim);font-size:11px;text-transform:uppercase;letter-spacing:.08em;border:0}
.lands{font-size:13px;color:var(--dim);margin:12px 0 4px}.tot{font-size:13px;color:var(--dim);margin:0}.ok{color:var(--ok)}
.cmd{background:#1e2430;border-left:3px solid var(--acc);padding:8px 12px;border-radius:4px;margin-bottom:14px;font-weight:600}
.cmd span{display:block;font-size:11px;color:var(--dim);text-transform:uppercase;letter-spacing:.08em;font-weight:400}
.stat{background:#12161d;border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin-bottom:10px}
.stat span{display:block;font-size:12px;color:var(--dim)}.stat b{font-size:19px;color:var(--ok)}
.stat small{display:block;color:#6b7280;font-size:11px;margin-top:2px}
th{text-align:left;font-size:11px;color:var(--dim);text-transform:uppercase;letter-spacing:.06em;padding:6px;border-bottom:1px solid var(--line)}
td{padding:5px 6px;border-bottom:1px solid #1d222a}.r{text-align:right}.idx{color:var(--warn)}
ul{padding-left:20px}li{margin:7px 0}code{background:#12161d;padding:1px 5px;border-radius:4px;font-size:12.5px;color:var(--acc)}
.pill{display:inline-block;font-size:11px;padding:2px 9px;border-radius:20px;background:#1e2430;color:var(--acc);margin-left:8px;vertical-align:middle}
"""
def deck(k, badge=""):
    d=D[k]; bands={}
    m=MC.get(k,{})
    if m.get('cal'):
        estim=(f"<div class='stat'><span>Estimación honesta de victorias</span>"
               f"<b>{m['cal']*100:.0f}%</b><small>índice bruto {m['bruto']*100:.0f}%, comprimido con el "
               f"factor medido contra winrates reales · {CONF.get(k,'')}</small></div>")
    else:
        estim=(f"<div class='stat'><span>Estimación honesta de victorias</span>"
               f"<b style='color:#fbbf24'>no calculable</b><small>índice bruto {m.get('bruto',0)*100:.0f}%. "
               f"Solo hay 2 winrates reales publicados en este formato y son los dos mejores mazos: "
               f"calibrar con eso daría 90% para cualquier cosa · {CONF.get(k,'')}</small></div>")
    for c in d['sp']: bands.setdefault(c['cmc'],[]).append(c)
    rows=[]
    for cmc in sorted(bands):
        rows.append(f"<tr class='band'><td colspan='4'>{cmc} maná</td></tr>")
        for c in sorted(bands[cmc],key=lambda x:(-x['n'],x['name'])):
            rows.append(f"<tr><td class='q'>{c['n']}</td><td>{esc(c['name'])}</td>"
                        f"<td class='mc'>{esc(c['mc'])}</td><td class='pt'>{esc(c['pt'])}</td></tr>")
    lands=" · ".join(f"{n} {esc(nm)}" for nm,n in sorted(d['la'].items(),key=lambda x:-x[1]))
    cmd=f"<div class='cmd'><span>Comandante</span>{esc(d['cmd'])}</div>" if d.get('cmd') else ""
    mm="".join(f"<tr><td>{esc(n)}</td><td class='r'>{w:.1f}%</td><td class='r idx'>{i:.0f}</td></tr>" for n,w,i in d['mm'])
    tot=d['ns']+d['nl']
    lab=f"{d['ns']} hechizos + {d['nl']} tierras = <b class='ok'>{tot}</b>"+(" + comandante" if d.get('cmd') else "")
    return f"""<section class="deck"><h3>{esc(d['t'])}<span class="col">{esc(d['col'])}</span>{badge}</h3>{cmd}
<div class="grid"><div><table class="list"><tbody>{''.join(rows)}</tbody></table>
<p class="lands"><b>Tierras ({d['nl']}):</b> {lands}</p><p class="tot">{lab}</p></div>
<div>{estim}<div class="stat"><span>Ventaja sobre la semilla codiciosa</span><b>{esc(d['gain'])}</b>
<small>lo que aportó la búsqueda sobre "meter las mejores cartas"</small></div>
<table><thead><tr><th>Rival del meta</th><th class="r">Peso</th><th class="r">Índice</th></tr></thead><tbody>{mm}</tbody></table>
</div></div></section>"""
H=f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Mis mazos MTG — v6</title>
<style>{CSS}</style></head><body><div class="wrap">
<h1>Tus tres mazos — versión 6</h1>
<p class="sub">16 ago 2026 · las tres mejores listas armables con las 371 cartas que tenés · recalculadas con el motor mejorado (−27% de error)</p>
<div class="box good"><p style="margin:0">Las tres listas están <b>verificadas</b>: legales en su formato y armables con
tus cartas físicas, sin exceder copias. Las podés escribir tal cual y llevarlas a la tienda.</p></div>
<h2>Standard Brawl <span class="pill">tu prioridad — es lo que se juega en tu tienda</span></h2>
<div class="box warn2"><p style="margin:0"><b>Cambió el comandante.</b> Con el motor viejo salía Thorin
Oakenshield (rojo-blanco); con el motor corregido gana <b>Dáin, Lord of the Iron Hills</b> en mono-blanco.
Aviso honesto: aquí la búsqueda por haz solo aportó <b>+0,35</b> sobre meter las mejores cartas sin más,
o sea prácticamente nada.</p></div>
{deck('brawl')}
<h2>Standard</h2>
{deck('standard')}
<h2>Pauper</h2>
{deck('pauper')}
<h2>Cómo leer el índice</h2>
<div class="box warn2">
<p><b>El índice no es un winrate real.</b> Es la nota que le pone el simulador, y el simulador infla tus cartas:
las de sobre promedian 2,04 de cuerpo por maná contra 1,32-1,90 de los mazos del meta. Las cartas de Limitado
se pagan en cuerpo, las de Construido se pagan en habilidad — y el motor mide cuerpos bien y habilidades a medias.</p>
<p>Ahora hay una segunda cifra, la <b>estimación honesta</b>: el índice bruto comprimido con el factor
que se midió contra winrates realmente publicados. En Pauper la compresión es a la mitad y el motor
demostró que ordena bien; en Standard es a un cuarto y el orden no está validado; en Brawl no se calibra
porque el dato real disponible no da.</p>
<p style="margin-bottom:0">El bruto sirve para <b>comparar tus propias listas entre sí</b> — a la búsqueda
solo le importa el orden. La estimación honesta es la que podés decir en voz alta.</p>
</div>
<h2>Lo que viene</h2>
<div class="box info">
<p>Estos mazos son tu piso: lo mejor posible con lo que ya tenés, mientras aprendés. Ninguno es tu estilo —
vos jugás prisión, negarle el juego al rival, y eso no se puede armar todavía con estas cartas.</p>
<p><b>Novedad:</b> el motor ya sabe leer efectos de prisión —edicto, inmovilizar, impuesto sobre los
hechizos del rival—. En el banco del meta no cambió casi nada porque ningún mazo del meta los usa,
pero es justo la pieza que hacía falta para poder evaluar un mazo de tu estilo.</p>
<p style="margin-bottom:0">El plan de compra hacia Ketramose sigue en pie: <b>Etapa 1 por US$68</b> rinde igual
en el motor que la lista de US$220, porque el 88% del valor está en 10 cartas. Pero antes hay que arreglar
que el motor sepa valorar la asfixia — hoy le da 29% a un mazo de descarte que en la vida real gana 55%.</p>
</div>
</div></body></html>"""
open('out/mazos_v6.html','w',encoding='utf-8').write(H)
print('escrito out/mazos_v6.html', len(H))
