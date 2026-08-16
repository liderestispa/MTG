# -*- coding: utf-8 -*-
"""out/motor_v5.html — campana 4: calibrar contra datos reales."""
import json, html
F=json.load(open('out/final_c4.json')); D=json.load(open('out/report_v4.json'))
MC=json.load(open('out/mis_decks_cal.json'))
esc=F['escala']; fm=F['fmts']; FU=F['fuentes']
NOM={'standard':'Standard','pauper':'Pauper','brawl':'Standard Brawl'}
def e(s): return html.escape(str(s))
CSS=open('src/report_v4.py',encoding='utf-8').read().split('CSS = """')[1].split('"""')[0]

def mtx(k):
    o=fm[k]; n=o['names']; M=o['matrix']; f=o['field']
    head="".join(f"<th class='r'>{e(x[:11])}</th>" for x in n)
    body=[]
    for i,nm in enumerate(n):
        cells=[]
        for j in range(len(n)):
            v=M[i][j]*100
            cl='' if 40<=v<=60 else ('bad' if v<40 else 'warn')
            cells.append("<td class='r' style='color:#3d4450'>—</td>" if i==j else f"<td class='r {cl}'>{v:.0f}</td>")
        fv=f[i]*100; fcl='ok' if 40<=fv<=60 else ('bad' if fv<40 else 'warn')
        body.append(f"<tr><td>{e(nm)}</td>{''.join(cells)}<td class='r {fcl}'><b>{fv:.1f}</b></td></tr>")
    return (f"<h3 style='margin-top:18px'>{NOM[k]}</h3><table class='mtx'><thead><tr><th></th>{head}"
            f"<th class='r'>Campo</th></tr></thead><tbody>{''.join(body)}</tbody></table>")

def campo(k):
    o=fm[k]
    if 'campo_rows' not in o: return ""
    rows="".join(f"<tr><td>{e(n)}</td><td class='r'>{float(fv)*100:5.1f}%</td><td class='r'>{float(rv)*100:.1f}%</td>"
                 f"<td class='r {'ok' if abs(float(fv)-float(rv))<0.06 else 'bad'}'>{(float(fv)-float(rv))*100:+.1f}</td></tr>"
                 for n,fv,rv in o['campo_rows'])
    ex=esc.get(k,{})
    extra=""
    if ex.get('r') is not None:
        extra=(f"<p style='margin-bottom:0'>Sobredispersión <b>×{float(o.get('disp',0)):.1f}</b> · "
               f"correlación de orden <b class=\"{'ok' if float(ex['r'])>0.5 else 'bad'}\">r={float(ex['r']):+.2f}</b> · "
               f"{e(ex['confianza'])}</p>")
    return (f"<h3 style='margin-top:20px'>{NOM[k]}</h3>"
            f"<table><thead><tr><th>Mazo</th><th class='r'>Motor</th><th class='r'>Real publicado</th>"
            f"<th class='r'>Error</th></tr></thead><tbody>{rows}</tbody></table>"
            f"<p class='tot' style='margin-top:6px'>Desplazamiento común {float(o['campo_off'])*100:+.1f} pts · "
            f"residuo <b>{float(o['campo_resid'])*100:.2f}</b> pts</p>{extra}")

h2h=fm['standard'].get('h2h_rows',[])
h2hrows="".join(f"<tr><td>{e(a)}</td><td>{e(b)}</td><td class='r'>{float(m)*100:.1f}%</td>"
                f"<td class='r'>{float(r)*100:.1f}%</td><td class='r bad'>{(float(m)-float(r))*100:+.1f}</td>"
                f"<td class='r' style='color:#6b7280'>{ns}</td></tr>" for a,b,m,r,ns in h2h)

escrows="".join(
  f"<tr><td>{NOM[k]}</td><td class='r'>{('×%.1f'%float(fm[k]['disp'])) if fm[k].get('disp') else '—'}</td>"
  f"<td class='r'>{('%+.2f'%float(v['r'])) if v.get('r') is not None else '—'}</td>"
  f"<td class='r'>{('%.2f'%float(v['k'])) if v.get('k') is not None else 'no aplicable'}</td>"
  f"<td>{e(v['confianza'])}</td></tr>" for k,v in esc.items())

mios="".join(
  f"<tr><td>{NOM[k]}</td><td class='r idx'>{v['bruto']*100:.1f}%</td>"
  f"<td class='r ok'>{(('%.1f%%'%(v['cal']*100)) if v['cal'] else 'sin calibrar')}</td></tr>"
  for k,v in MC.items())

fuentes="".join(f"<li><a href='{u}' style='color:#7dd3fc'>{e(u.split('/')[2])}</a> — {e(k)}</li>" for k,u in FU.items())

H=f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>MTG — Motor v5: contra datos reales</title>
<style>{CSS}</style></head><body><div class="wrap">
<h1>Cuarta revisión: dejar de calibrar contra una suposición</h1>
<p class="sub">16 ago 2026 · pediste que el motor quedara prístino. Prístino no es que el número suba: es saber cuál número creer.</p>

<div class="box bad">
<h3>Lo primero: la métrica que veníamos usando estaba escondiendo el error</h3>
<p>Hasta ahora medía el motor así: pongo a los mazos del meta a jugar entre ellos, y si el motor
es bueno todos deberían quedar cerca del 50%. Standard daba <b>9,56</b> con esa vara y parecía bien.</p>
<p>El problema es que <b>un error que infla a un mazo y desinfla a otro se cancela en ese promedio</b>.
Fui a buscar los winrates que se publican de verdad — resultados de papel de los Regional Championships,
las ligas de MTGO semana a semana, y enfrentamientos directos rastreados. Contra eso, el error de
Standard no es 9,56: es <b class="bad">20,66</b>.</p>
<p style="margin-bottom:0">Mismo motor. Distinta vara. La vara vieja mentía.</p>
</div>

<h2>El motor contra los enfrentamientos reales (Standard)</h2>
<div class="box">
<table><thead><tr><th>Gana</th><th>Contra</th><th class="r">Motor</th><th class="r">Real</th><th class="r">Error</th><th class="r">n</th></tr></thead>
<tbody>{h2hrows}</tbody></table>
<p style="margin-bottom:0">La realidad vive entre <b>51 y 58%</b>. El motor va de <b>27 a 68%</b>.
No es que se equivoque de ganador: es que <b>separa siete veces más de lo que la realidad separa</b>.</p>
</div>

<h2>El motor contra los winrates publicados, formato por formato</h2>
<div class="box">
{campo('pauper')}
{campo('standard')}
{campo('brawl')}
</div>

<div class="box good">
<h3>El hallazgo que cambia cómo hay que usar esto</h3>
<p>La correlación de orden dice si el motor al menos <em>ordena</em> bien los mazos, aunque el nivel
esté corrido:</p>
<table><thead><tr><th>Formato</th><th class="r">Sobredispersión</th><th class="r">Correlación</th><th class="r">Factor k</th><th>Qué se puede creer</th></tr></thead>
<tbody>{escrows}</tbody></table>
<p><b>En Pauper el motor funciona</b> (r=+0,70 con 6 mazos): ordena bien y solo hay que comprimir
la escala a la mitad. <b>En Standard no está validado</b> (r=−0,03): con 4 mazos de dato real
y todos ellos entre 49,9% y 54,7%, el rango real es más chico que el ruido de la medición —
así que el dato no puede ni confirmar ni desmentir al motor, y eso también hay que decirlo.</p>
<p style="margin-bottom:0">Por qué justo Pauper: es un formato de comunes, de cuerpos y de combate,
que es exactamente lo que el motor sabe modelar. Standard es de raras con texto largo,
modos, planeswalkers y sideboard. <b>El motor mide músculo, no astucia</b> — y Pauper se
gana con músculo.</p>
</div>

<h2>La capa de traducción</h2>
<div class="box info">
<p>El índice bruto sirve para <b>buscar mazos</b> (a la búsqueda solo le importa el orden), pero no
para decir "voy a ganar el 90%". Ahora hay una capa que traduce el índice bruto a una estimación honesta,
usando la compresión medida contra el dato real:</p>
<table><thead><tr><th>Tus mazos</th><th class="r">Índice bruto</th><th class="r">Estimación honesta</th></tr></thead>
<tbody>{mios}</tbody></table>
<p style="margin-bottom:0">Y tiene un freno puesto a propósito: <b>en Brawl se niega a calibrar el nivel</b>.
Los dos únicos winrates reales que existen para ese formato son los de Elspeth (77%) y Ketramose (73%),
o sea los dos mejores mazos del formato. Ajustar una recta a esos dos y aplicarla a todo devolvería
"90% para cualquier cosa". Prefiero que diga <em>no sé</em>.</p>
</div>

<h2>Lo que se arregló en el motor</h2>
<div class="box good">
<h3>Antimaleficio y vigilia estaban leídos y nunca usados <span class="tag">bug</span></h3>
<p>El extractor marcaba correctamente <code>hexproof</code>, <code>ward</code> e <code>indestructible</code>,
pero la remoción dirigida solo miraba indestructible. <b>Toda la remoción del motor mataba criaturas
con antimaleficio.</b> Los mazos de una sola amenaza grande perdían por un bug, no por su plan.</p>
<p style="margin-bottom:0">Ahora el antimaleficio impide apuntar y la vigilia exige tener maná de sobra
para pagarla. En este meta casi no cambió el número (ninguna criatura del meta tiene antimaleficio
estático), pero <b>en tu colección sí las hay</b>, y hasta hoy el motor las estaba tirando gratis.</p>
</div>
<div class="box good">
<h3>La remoción no miraba cuánto daño tenía enfrente <span class="tag">adoptado</span></h3>
<p>La traza de Cuatro Colores Control lo mostró crudo: turno 4, <b>9 vidas, cero permanentes en mesa</b>,
el rival con tres criaturas, y el motor lanzando un cantrip de 1 maná porque puntuaba 17 contra 16.
Matar un 1/1 valía lo mismo que matar un 7/7.</p>
<p style="margin-bottom:0">Ahora la remoción y los barredores valen más cuanto menos te queda de vida
y más daño quitan (<code>W_PRESSURE=70</code>, ajustado contra el dato real).</p>
</div>
<div class="box warn2">
<h3>Los parámetros están saturados <span class="tag">límite</span></h3>
<p style="margin-bottom:0">Barrí diez parámetros de la política de juego contra el objetivo real, dos rondas
completas. Ganancia total: <b>6,58 → 6,49</b>, un 1,4%. Ya no queda nada que sacar apretando tornillos:
lo que falta es modelo, no ajuste. Y lo que falta en el modelo tiene nombre — el motor no sabe
valorar negarle el juego al rival.</p>
</div>

<h2>Los tres mazos siguen en pie</h2>
<div class="box good">
<p>Regla propia: después de tocar el motor hay que comprobar que cada lista siga ganándole a su
semilla simple. Con el motor nuevo:</p>
<table><thead><tr><th>Formato</th><th class="r">Mazo</th><th class="r">Semilla</th><th class="r">Ventaja</th></tr></thead><tbody>
<tr><td>Standard (WBG)</td><td class="r">85,92</td><td class="r">75,07</td><td class="r ok"><b>+10,86</b></td></tr>
<tr><td>Pauper (BR)</td><td class="r">73,21</td><td class="r">61,56</td><td class="r ok"><b>+11,65</b></td></tr>
<tr><td>Brawl (Thorin)</td><td class="r">54,98</td><td class="r">—</td><td class="r ok">estable</td></tr>
</tbody></table>
<p style="margin-bottom:0">Las listas no cambian. Lo que cambia es lo que puedo decirte del número.</p>
</div>

<h2>Matrices completas</h2>
<div class="box">{mtx('standard')}{mtx('pauper')}{mtx('brawl')}</div>

<h2>Qué significa esto para ti, en concreto</h2>
<div class="box warn2">
<ul>
<li><b>Tu mazo de Pauper es el que tiene respaldo.</b> Es el formato donde el motor demostró que ordena
bien. Estimación honesta: ~64%, no 77%.</li>
<li><b>Tu mazo de Standard está bien construido pero sin validar.</b> La lista es legal, armable, con
buena curva y buen conteo de tierras — eso es fiable. Que sea <em>el mejor</em> de tu colección, no lo puedo
demostrar con el dato que existe.</li>
<li><b>Standard Brawl — tu prioridad — es el caso más flojo.</b> Usa cartas de Standard (complejas) y
casi no hay winrates publicados. Ahí el motor te sirve para descartar listas malas, no para elegir
entre dos buenas.</li>
</ul>
<p style="margin-bottom:0">No es lo que querías oír, pero es lo que pediste: que el motor quede prístino.
Un motor prístino no es el que da el número más alto, es el que sabe cuándo callarse.</p>
</div>

<h2>Fuentes del dato real</h2>
<div class="box"><ul style="font-size:13px">{fuentes}</ul>
<p class="tot" style="margin-bottom:0">Calidad: magic.gg es papel, no-espejo, miles de partidas, pero de mayo.
MTGGoldfish es MTGO semanal, muestras de 180-640 listas (una sola semana se mueve 17 puntos, por eso se promedian varias).
MTG Nexus son 55-95 partidas por enfrentamiento: ±10 puntos, sirve para ver errores de 20-30, no para afinar 2.</p>
</div>

</div></body></html>"""
open('out/motor_v5.html','w',encoding='utf-8').write(H)
print('escrito out/motor_v5.html', len(H))
