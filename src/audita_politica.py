# -*- coding: utf-8 -*-
"""Comprueba si la ganancia que reporta el entrenador es real o seleccion sobre ruido.

POR QUE HACE FALTA. entrenar_politica.py reporta (mejor_f - base), donde:

  base    = una UNICA evaluacion de la heuristica, en la semilla 1234567.
  mejor_f = el MAXIMO de ~1.000 evaluaciones de mu, una por generacion.

El maximo de mil tiradas ruidosas queda muy por encima de la media aunque no se haya
aprendido nada. Con una desviacion de medio punto entre semillas, el maximo de mil
draws esta 1,5-2 puntos arriba solo por serlo. O sea: el numero que dice "+2,135" puede
ser un artefacto de como se mide, no una politica mejor.

La sospecha llego mirando el log: la elite y la media de la poblacion alternan casi un
punto entre generaciones pares e impares, y mu alterna en ANTI-FASE. Eso no lo puede
hacer el aprendizaje. Lo hace la semilla: es 900000+g*7919, cuya paridad alterna con g,
y mu se evalua en semilla+1, o sea siempre en la paridad contraria.

Este script mide las dos cosas en semillas NUEVAS y emparejadas:

  1. La politica guardada contra la heuristica, en las mismas semillas.
  2. mu (el centro de lo aprendido) contra la heuristica, igual.
  3. Si hay efecto de paridad de semilla.

    python3 src/audita_politica.py            # 8 semillas
    python3 src/audita_politica.py 12 --nucleos 4
"""
import sys, io, os, json, statistics
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, 'src'); sys.path.insert(0, 'data')
from entrenar_politica import evalua, NPAR, ESTADO_CEM

N = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8
NUC = int(sys.argv[sys.argv.index('--nucleos') + 1]) if '--nucleos' in sys.argv else 4

# Semillas que NO participaron en el entrenamiento: las suyas son 900000+g*7919.
# Se eligen mitad pares y mitad impares a proposito, para poder separar el efecto.
SEMILLAS = [1234567, 1234568, 777001, 777002, 424243, 424244, 99881177, 99881178,
            31337, 31338, 606060, 606061][:max(2, N)]


def main():
    est = json.load(io.open(ESTADO_CEM, encoding='utf-8'))
    cero  = [0.0] * NPAR
    mu    = est['mu']
    mejor = est['mejor_v']
    print(f"estado: generacion {est.get('gen_total')}, mejor_f {est['mejor_f']*100:.3f}%, "
          f"base guardada {est['base']*100:.3f}%")
    print(f"o sea el entrenador reporta {(est['mejor_f']-est['base'])*100:+.3f} puntos.\n")
    print(f"Re-midiendo en {len(SEMILLAS)} semillas nuevas, emparejadas:\n")

    tareas = ([(cero, s) for s in SEMILLAS] + [(mu, s) for s in SEMILLAS] +
              [(mejor, s) for s in SEMILLAS])
    with ProcessPoolExecutor(max_workers=NUC) as ex:
        res = list(ex.map(evalua, tareas))
    n = len(SEMILLAS)
    heu, cen, top = res[:n], res[n:2*n], res[2*n:]

    print(f"{'semilla':>10} {'par?':>5} {'heuristica':>11} {'mu':>9} {'guardada':>10} "
          f"{'mu-heu':>8} {'guar-heu':>9}")
    for i, s in enumerate(SEMILLAS):
        print(f"{s:>10} {'par' if s % 2 == 0 else 'impar':>5} {heu[i]*100:>10.3f}% "
              f"{cen[i]*100:>8.3f}% {top[i]*100:>9.3f}% "
              f"{(cen[i]-heu[i])*100:>+8.3f} {(top[i]-heu[i])*100:>+9.3f}")

    dmu = [(c - h) * 100 for c, h in zip(cen, heu)]
    dto = [(t - h) * 100 for t, h in zip(top, heu)]
    for etiqueta, d in [('mu (centro de lo aprendido)', dmu), ('politica guardada', dto)]:
        m = statistics.mean(d)
        sd = statistics.stdev(d) if len(d) > 1 else 0.0
        se = sd / len(d) ** 0.5 if sd else 0.0
        print(f"\n{etiqueta}: {m:+.3f} puntos  (sd {sd:.3f}, error tipico {se:.3f})")

    pares   = [heu[i] * 100 for i, s in enumerate(SEMILLAS) if s % 2 == 0]
    impares = [heu[i] * 100 for i, s in enumerate(SEMILLAS) if s % 2 == 1]
    if pares and impares:
        print(f"\nefecto de paridad de la semilla sobre la MISMA heuristica: "
              f"pares {statistics.mean(pares):.3f}% vs impares "
              f"{statistics.mean(impares):.3f}%  "
              f"(diferencia {statistics.mean(pares)-statistics.mean(impares):+.3f})")


if __name__ == '__main__':
    main()
