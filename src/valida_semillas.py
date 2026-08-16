# -*- coding: utf-8 -*-
"""Comprueba si una mejora del objetivo sobrevive a semillas independientes.

El tuning y la busqueda miden siempre con la misma semilla (1234567). Una ganancia de
unas milesimas puede ser ruido de esa semilla y no una mejora del motor. Esto vuelve a
medir el objetivo con varias semillas independientes y reporta media y dispersion, de
modo que la comparacion entre variantes se hace contra el ruido y no contra una corrida.

Es la regla 6 del proyecto aplicada al objetivo: hasta ahora solo revalidar.py usaba
semillas nuevas, y eso cubre los mazos, no el ajuste.

Uso:
    python3 src/valida_semillas.py 2000 "" "SWEEP_MIN=3"
    python3 src/valida_semillas.py 2000 "" "TH_TRADE=10" "PEN_NOTARGET=30"

El primer argumento es el numero de partidas. Cada argumento siguiente es una variante:
una cadena vacia significa "los defaults compilados", y el resto son asignaciones
VAR=valor separadas por espacios. Un cambio solo es real si su ventaja supera la
dispersion entre semillas.
"""
import sys, os, statistics
sys.path.insert(0, 'src'); sys.path.insert(0, 'data')
from obj_real import medir, objetivo, linea

SEMILLAS = [1234567, 777001, 20260816, 424242, 99881177]

def con_variante(spec, ng, seed):
    previo = {}
    for par in spec.split():
        if '=' not in par: continue
        k, v = par.split('=', 1)
        previo[k] = os.environ.get(k)
        os.environ[k] = v
    try:
        d = medir(ng, seed=seed)
        return objetivo(d), d
    finally:
        for k, v in previo.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v

if __name__ == '__main__':
    ng = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    variantes = sys.argv[2:] or ['']
    print(f"{len(SEMILLAS)} semillas independientes, {ng} partidas por enfrentamiento\n")
    resultados = {}
    for spec in variantes:
        etiqueta = spec if spec else '(defaults compilados)'
        vals = []
        for s in SEMILLAS:
            g, d = con_variante(spec, ng, s)
            vals.append(g * 100)
            print(f"  {etiqueta:<28} semilla {s:>9}  {g*100:7.3f}   {linea(d)}", flush=True)
        media = statistics.mean(vals)
        sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
        resultados[etiqueta] = (media, sd, vals)
        print(f"  {etiqueta:<28} MEDIA {media:7.3f}  sd {sd:.3f}  "
              f"rango [{min(vals):.3f}, {max(vals):.3f}]\n", flush=True)

    if len(resultados) > 1:
        base = list(resultados.values())[0]
        print("=== veredicto (menor es mejor) ===")
        for et, (media, sd, _) in resultados.items():
            delta = media - base[0]
            ruido = max(sd, base[1])
            if et == list(resultados)[0]:
                print(f"  {et:<28} {media:7.3f}   referencia")
            elif abs(delta) <= ruido:
                print(f"  {et:<28} {media:7.3f}   {delta:+.3f}  DENTRO DEL RUIDO (sd {ruido:.3f}) "
                      f"-> no adoptar")
            else:
                veredicto = 'mejora real' if delta < 0 else 'empeora'
                print(f"  {et:<28} {media:7.3f}   {delta:+.3f}  {veredicto} (sd {ruido:.3f})")
