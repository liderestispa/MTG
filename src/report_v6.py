# -*- coding: utf-8 -*-
"""out/motor_v6.html — mejoras de modelo medidas una por una."""
import json, os
CSS=open('src/report_v4.py',encoding='utf-8').read().split('CSS = """')[1].split('"""')[0]
H=f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>MTG — Motor v6: mejoras de modelo</title>
<style>{CSS}</style></head><body><div class="wrap">
<h1>Sí: el motor mejoró un 27%</h1>
<p class="sub">16 ago 2026 · y por primera vez le gana a no saber nada — en Pauper</p>

<div class="box good">
<h3>El resumen en una tabla</h3>
<table><thead><tr><th>Cambio</th><th class="r">Objetivo antes</th><th class="r">después</th><th>Veredicto</th></tr></thead><tbody>
<tr><td>Daño "a cualquier objetivo" como daño flexible</td><td class="r">3,204</td><td class="r ok">2,948</td><td>adoptado</td></tr>
<tr><td>Bloque de negación (edicto, inmovilizar, impuesto, rebote)</td><td class="r">3,211</td><td class="r ok">2,892</td><td>adoptado</td></tr>
<tr><td>Destrucción de tierras</td><td class="r">2,863</td><td class="r bad">3,141</td><td>medido y descartado</td></tr>
<tr><td>Reajuste de la política de juego</td><td class="r">2,892</td><td class="r ok">2,491</td><td>adoptado</td></tr>
<tr><td><b>Total de la sesión</b></td><td class="r"><b>3,421</b></td><td class="r ok"><b>2,491</b></td><td><b>−27%</b></td></tr>
</tbody></table>
<p style="margin-bottom:0">Cada línea es una medición contra winrates reales publicados, con el cambio
encendido y apagado. Nada se adoptó "porque tiene sentido".</p>
</div>

<h2>El error grande: los mazos rojos no tenían interacción</h2>
<div class="box bad">
<p>41 cartas del meta —el 3,6%— dicen <em>"deals N damage to any target"</em>. El extractor las
mandaba todas a <code>BURN_FACE</code>: quemar a la cara y nada más. Entre ellas, Lightning Bolt,
Fiery Temper, Lava Dart, Chain Lightning, Galvanic Blast, Burst Lightning.</p>
<p><b>Un Rayo que no puede matar una criatura no es un Rayo.</b> Mono Red Madness aparecía con
0,98 piezas de remoción por partida cuando su lista lleva doce. Todo el arquetipo rojo estaba
jugando sin interacción.</p>
<p style="margin-bottom:0">Ahora existe <code>E_DMG_ANY</code>: mata la criatura si vale la pena,
remata a la cara si con eso gana la partida, y va a la cara si no hay nada que matar.
La correlación de orden de Pauper subió de <b>+0,66 a +0,76</b> solo con eso.</p>
</div>

<h2>El bloque de negación — tu estilo</h2>
<div class="box good">
<p>Estaban al 0% de cobertura: edicto (el rival sacrifica, sin apuntar, así que atraviesa el
antimaleficio), inmovilizar (girar y que no se enderece), impuesto (sus hechizos cuestan más),
rebote masivo, y descarte disfrazado (<em>"target opponent exiles a card from their hand"</em>
es descarte con otro nombre, y no lo estaba leyendo).</p>
<p style="margin-bottom:0">Ganancia: <b>3,211 → 2,892</b>, casi toda en Brawl (residuo 5,17 → 4,01),
que es donde más aparecen estos efectos. <b>El impuesto no cambió nada en el banco</b> porque ningún
mazo del meta lo usa — pero es exactamente la pieza que necesita tu mazo de prisión, y ahora existe.</p>
</div>

<h2>Lo que medí y tiré</h2>
<div class="box bad">
<h3>Destrucción de tierras <span class="tag">descartado</span></h3>
<p>Parecía obvio: <em>"sacrifice a land"</em>, <em>"destroy target land"</em> → atacar el maná del rival.
Estaba mal en los dos sentidos. <b>"Sacrifica una tierra" casi siempre es un coste que paga quien
lanza</b> (Crop Rotation, Highway Robbery), y hasta <em>"destroy target land"</em> se usa sobre tierra
propia para buscar y robar — Cleansing Wildfire, que es literalmente la carta que le da nombre a
Jund Wildfire en Pauper.</p>
<p style="margin-bottom:0">El ablation lo cantó: <b>2,863 sin ella, 3,141 con ella</b>. Fuera.</p>
</div>
<div class="box bad">
<h3>Un bug de una letra <span class="tag">corregido</span></h3>
<p style="margin-bottom:0">Mi expresión para "inmovilizar" buscaba <code>tap target creature</code>.
La cadena <code>untap target creature</code> <b>contiene</b> esa subcadena. Quirion Ranger, que
<em>endereza</em> criaturas, estaba siendo leída como una carta que las gira. Faltaba un límite de
palabra. Este tipo de error no da error: da números.</p>
</div>

<h2>La corrección de método</h2>
<div class="box info">
<p>El objetivo que usaba penalizaba la <b>sobredispersión</b> — que el motor separe más de lo que
separa la realidad. Pero eso ya lo corrige la capa de escala, así que penalizarlo dos veces castiga
cambios que mejoran el motor.</p>
<p>Con igualación de varianza el error calibrado sale en cerrado:</p>
<p style="text-align:center;font-family:ui-monospace,monospace;color:#7dd3fc">
error_calibrado = sd_real · √(2·(1 − r))</p>
<p style="margin-bottom:0">O sea: <b>minimizar el error calibrado es exactamente maximizar la
correlación de orden</b>. Que es lo único que se le puede pedir a un simulador: que ordene bien.
El nivel lo pone la escala.</p>
</div>

<h2>La prueba honesta: ¿le gana a no saber nada?</h2>
<div class="box warn2">
<p>Ajustar la escala con los mismos mazos con los que después te evalúas es hacer trampa con
muestras de 4-6. Así que hice validación cruzada dejando uno fuera: para cada mazo, ajusto con los
otros y predigo ese. Y lo comparo contra el <b>modelo tonto</b>: predecir siempre la media, sin
simular nada.</p>
<table><thead><tr><th>Formato</th><th class="r">Motor antes</th><th class="r">Motor ahora</th><th class="r">Modelo tonto</th><th>¿Aporta?</th></tr></thead><tbody>
<tr><td>Pauper</td><td class="r">4,86%</td><td class="r ok"><b>3,93%</b></td><td class="r">4,40%</td><td class="ok">sí, por primera vez</td></tr>
<tr><td>Standard</td><td class="r">7,69%</td><td class="r">5,94%</td><td class="r">2,44%</td><td class="bad">no</td></tr>
<tr><td><b>Global</b></td><td class="r"><b>6,43%</b></td><td class="r ok"><b>5,04%</b></td><td class="r">3,56%</td><td></td></tr>
</tbody></table>
<p><b>En Pauper el motor cruzó la línea.</b> Antes de hoy predecía peor que decir "todos ganan el 52%".
Ahora predice mejor. Es una ventaja chica —medio punto— pero es la primera vez que existe.</p>
<p style="margin-bottom:0"><b>En Standard sigue sin ganarle a una constante</b>, y hay una razón que no
es culpa del motor: los cuatro mazos de Standard con dato real están entre 49,9% y 54,7%. La
desviación típica real es de <b>1,85 puntos</b>. Cuando lo que hay que predecir varía menos de dos
puntos, cualquier modelo pierde contra decir la media. No es que el motor sea malo en Standard:
es que ahí casi no hay nada que predecir, y el motor mete ruido.</p>
</div>

<h2>Dónde quedó, formato por formato</h2>
<div class="box">
<table><thead><tr><th>Formato</th><th class="r">Correlación antes</th><th class="r">ahora</th><th class="r">Residuo Brawl</th><th>Qué se puede creer</th></tr></thead><tbody>
<tr><td>Pauper</td><td class="r">+0,65</td><td class="r ok"><b>+0,72</b></td><td class="r">—</td><td>el orden es utilizable, y ahora con respaldo cruzado</td></tr>
<tr><td>Standard</td><td class="r">−0,02</td><td class="r">+0,12</td><td class="r">—</td><td>ya no es negativa, pero sigue sin validar</td></tr>
<tr><td>Standard Brawl</td><td class="r">—</td><td class="r">—</td><td class="r ok">5,06 → <b>2,12</b></td><td>el nivel encaja mucho mejor; el orden sigue sin datos</td></tr>
</tbody></table>
</div>

<h2>Lo que sigue sin estar</h2>
<div class="box">
<ul>
<li><b>Cuatro Colores Control</b> sigue en 33,9% contra 53% real. Es el peor error que queda y es
estructural: el motor no sabe que acumular cartas es un plan de victoria.</li>
<li><b>Costes alternativos.</b> Fireblast se juega sacrificando dos montañas; el motor lo ve como un
hechizo de 6 maná y no lo lanza nunca. Son pocas cartas, pero en mono-rojo de Pauper es el remate.</li>
<li><b>Locura y pagos por descarte</b> (Sneaky Snacker, Marauding Mako): siguen invisibles.</li>
<li><b>Sideboard.</b> Los winrates reales son de partidas al mejor de tres con cambios entre juegos;
el motor juega un solo juego sin banquillo. Eso explica buena parte de la sobredispersión que queda,
y no se arregla sin listas de banquillo.</li>
</ul>
<p style="margin-bottom:0">El 4,8% de las cartas del meta sigue siendo invisible para el motor,
y ahí no está el problema: el problema es que las que sí ve, a veces las ve mal.</p>
</div>

</div></body></html>"""
open('out/motor_v6.html','w',encoding='utf-8').write(H)
print('escrito out/motor_v6.html', len(H))
