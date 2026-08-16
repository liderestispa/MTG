# -*- coding: utf-8 -*-
"""Grafico referencial de como avanzan los mazos en las partidas simuladas.

Lee out/report_v6.json y escribe out/avance.html: un solo archivo, SVG en linea, sin
dependencias ni internet. Es una vista de apoyo, no un entregable: sirve para mirar de
un vistazo contra quien gana cada mazo y a que ritmo juega.

Tres bloques por formato:

  1. Enfrentamientos. Una barra por rival del meta, con su cuota. La linea del 50% es la
     referencia; el ancho es el winrate del mazo contra ese rival.
  2. Cartas en mano en los turnos 3, 6 y 9, propias contra las del rival. Es lo unico
     parecido a una trayectoria que el motor emite hoy (ST_hA/ST_hB en sim.c). Bajar
     rapido es normal en un mazo agresivo; quedar por debajo del rival todo el rato es
     desventaja de cartas.
  3. Ritmo: turno de primera jugada, largo de partida, turnos sin jugada en T1-4 y screw.

OJO con el eje: el winrate del motor esta SOBREDISPERSO. Estos numeros ordenan bien
—para eso se usan— pero no son predicciones. La estimacion honesta esta en el informe.

    python3 src/grafico.py
"""
import json, io, sys

W, BARH, GAP = 560, 18, 7
COL = {'bien': '#4ade80', 'mal': '#f87171', 'medio': '#fbbf24',
       'yo': '#60a5fa', 'rival': '#a78bfa', 'linea': '#475569', 'txt': '#cbd5e1'}


def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def barras(mm):
    """Winrate contra cada rival del meta, con la cuota al lado."""
    alto = len(mm) * (BARH + GAP) + 34
    p = [f'<svg viewBox="0 0 {W} {alto}" width="100%" role="img">']
    x0, ancho = 168, W - 168 - 58
    for k in (0, 25, 50, 75, 100):
        x = x0 + ancho * k / 100
        p.append(f'<line x1="{x:.1f}" y1="16" x2="{x:.1f}" y2="{alto-18}" '
                 f'stroke="{COL["linea"]}" stroke-width="{2 if k==50 else 1}" '
                 f'{"" if k==50 else "stroke-dasharray=\'2 3\'"} opacity="0.7"/>')
        p.append(f'<text x="{x:.1f}" y="11" fill="{COL["txt"]}" font-size="9" '
                 f'text-anchor="middle" opacity="0.6">{k}%</text>')
    for i, (nom, cuota, wr) in enumerate(mm):
        y = 22 + i * (BARH + GAP)
        c = COL['bien'] if wr >= 55 else (COL['mal'] if wr < 45 else COL['medio'])
        p.append(f'<text x="0" y="{y+13}" fill="{COL["txt"]}" font-size="11">'
                 f'{esc(nom[:24])}</text>')
        p.append(f'<text x="164" y="{y+13}" fill="{COL["txt"]}" font-size="9" '
                 f'text-anchor="end" opacity="0.55">{cuota:.0f}%</text>')
        p.append(f'<rect x="{x0}" y="{y}" width="{ancho*wr/100:.1f}" height="{BARH}" '
                 f'fill="{c}" rx="2" opacity="0.85"/>')
        p.append(f'<text x="{x0+ancho*wr/100+5:.1f}" y="{y+13}" fill="{c}" '
                 f'font-size="11" font-weight="600">{wr:.0f}%</text>')
    p.append('</svg>')
    return ''.join(p)


def trayectoria(st):
    """Cartas en mano en T3/T6/T9: el mazo contra el campo."""
    turnos = [3, 6, 9]
    yo = [st.get(f'hA{t}') for t in turnos]
    riv = [st.get(f'hB{t}') for t in turnos]
    if any(v is None for v in yo + riv):
        return '<p class="nd">sin datos de trayectoria en el informe</p>'
    alto, x0, y0 = 150, 34, 116
    ancho, altoU = W - x0 - 90, 94
    tope = max(yo + riv + [1]) * 1.15
    p = [f'<svg viewBox="0 0 {W} {alto}" width="100%" role="img">']
    for v in range(0, int(tope) + 1, 2):
        y = y0 - altoU * v / tope
        p.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x0+ancho}" y2="{y:.1f}" '
                 f'stroke="{COL["linea"]}" stroke-width="1" stroke-dasharray="2 3" opacity="0.5"/>')
        p.append(f'<text x="{x0-6}" y="{y+3:.1f}" fill="{COL["txt"]}" font-size="9" '
                 f'text-anchor="end" opacity="0.6">{v}</text>')
    # 'tu mazo' suele ir por debajo del campo, asi que su etiqueta va abajo y la del
    # campo arriba: si no, en el turno 3 los dos numeros caen uno encima del otro.
    for serie, col, etiq, dy in ((yo, COL['yo'], 'tu mazo', 16),
                                 (riv, COL['rival'], 'el campo', -9)):
        pts = [(x0 + ancho * i / (len(turnos) - 1), y0 - altoU * v / tope)
               for i, v in enumerate(serie)]
        p.append('<polyline points="' + ' '.join(f'{a:.1f},{b:.1f}' for a, b in pts) +
                 f'" fill="none" stroke="{col}" stroke-width="2.5"/>')
        for i, ((a, b), v) in enumerate(zip(pts, serie)):
            p.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="3.5" fill="{col}"/>')
            # el primer punto cae encima del eje: se corre a la derecha para no pisarlo
            anc, dx = ('start', 7) if i == 0 else ('middle', 0)
            p.append(f'<text x="{a+dx:.1f}" y="{b+dy:.1f}" fill="{col}" font-size="10" '
                     f'text-anchor="{anc}">{v:.1f}</text>')
        ax, ay = pts[-1]
        p.append(f'<text x="{ax+9:.1f}" y="{ay+4:.1f}" fill="{col}" font-size="10">{etiq}</text>')
    for i, t in enumerate(turnos):
        p.append(f'<text x="{x0+ancho*i/(len(turnos)-1):.1f}" y="{y0+18}" '
                 f'fill="{COL["txt"]}" font-size="10" text-anchor="middle" '
                 f'opacity="0.7">turno {t}</text>')
    p.append(f'<text x="{x0}" y="14" fill="{COL["txt"]}" font-size="10" opacity="0.6">'
             f'cartas en mano</text>')
    p.append('</svg>')
    return ''.join(p)


def ritmo(st):
    campos = [('primera jugada', 'firstplay', 'turno {:.2f}'),
              ('largo de partida', 'gamelen', '{:.1f} turnos'),
              ('turnos sin jugada T1-4', 'noplay14', '{:.2f}'),
              ('screw de color', 'screw', '{:.0%}'),
              ('hechizos lanzados', 'cast', '{:.1f}'),
              ('remocion usada', 'removal', '{:.1f}')]
    out = []
    for etiq, k, fmt in campos:
        v = st.get(k)
        if v is None: continue
        out.append(f'<div class="kpi"><span class="v">{fmt.format(v)}</span>'
                   f'<span class="e">{etiq}</span></div>')
    return '<div class="kpis">' + ''.join(out) + '</div>'


def main(entrada='out/report_v6.json', salida='out/avance.html'):
    d = json.load(io.open(entrada, encoding='utf-8'))
    sec = []
    for f in ('standard', 'pauper', 'brawl'):
        o = d.get(f)
        if not o: continue
        cal = (f' · estimacion honesta <b>{o["cal"]:.1f}%</b>'
               if o.get('cal') else ' · estimacion honesta: <i>no calculable</i>')
        cmd = f' · {esc(o["cmd"])}' if o.get('cmd') else ''
        sec.append(f'''<section>
<h2>{esc(o['t'])} <span class="col">{esc(o['col'])}</span>{cmd}</h2>
<p class="sub">indice bruto <b>{o['wr']:.1f}%</b>{cal} · {'legal y armable' if o.get('legal') else 'REVISAR LEGALIDAD'}</p>
<h3>Contra el meta</h3>{barras(o['mm'])}
<h3>Trayectoria</h3>{trayectoria(o.get('st', {}))}
{ritmo(o.get('st', {}))}
</section>''')
    html = f'''<!doctype html><meta charset="utf-8">
<title>Avance de los mazos — simulacion</title>
<style>
 body{{background:#0f172a;color:#e2e8f0;font:14px/1.5 system-ui,sans-serif;
       max-width:760px;margin:0 auto;padding:28px 18px}}
 h1{{font-size:20px;margin:0 0 4px}} h2{{font-size:16px;margin:0 0 2px}}
 h3{{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#94a3b8;
     margin:20px 0 6px;font-weight:600}}
 .col{{color:#94a3b8;font-weight:400}} .sub{{color:#94a3b8;margin:0;font-size:12px}}
 section{{border:1px solid #1e293b;border-radius:10px;padding:16px 18px;margin:18px 0;
          background:#0b1220}}
 .kpis{{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}}
 .kpi{{background:#111c31;border:1px solid #1e293b;border-radius:7px;padding:7px 11px;
       min-width:92px}}
 .kpi .v{{display:block;font-size:14px;font-weight:600;color:#e2e8f0}}
 .kpi .e{{display:block;font-size:10px;color:#94a3b8}}
 .aviso{{border-left:3px solid #fbbf24;padding:8px 12px;background:#1c1917;
         color:#d6d3d1;font-size:12px;border-radius:0 6px 6px 0}}
 .nd{{color:#94a3b8;font-style:italic;font-size:12px}}
 footer{{color:#64748b;font-size:11px;margin-top:22px}}
</style>
<h1>Avance de los mazos en simulacion</h1>
<p class="sub">Vista referencial generada con <code>src/grafico.py</code> desde <code>out/report_v6.json</code>.</p>
<p class="aviso"><b>El indice bruto no es una prediccion.</b> El motor sobredispersa: separa
a los mazos mucho mas de lo que los separa la realidad. Estos numeros sirven para ordenar
listas entre si, que es lo unico que la busqueda necesita. Para el nivel, mira la estimacion
honesta, y donde dice <i>no calculable</i> es porque la muestra real no da para calibrarlo.</p>
{''.join(sec)}
<footer>Cartas en mano medidas en ST_hA/ST_hB de src/sim.c. Cuotas de meta y winrates por
enfrentamiento, del informe v6.</footer>'''
    io.open(salida, 'w', encoding='utf-8').write(html)
    print(f'escrito {salida}  ({len(html)/1024:.0f} KB)')


if __name__ == '__main__':
    main(*(sys.argv[1:3] or []))
