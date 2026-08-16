# -*- coding: utf-8 -*-
"""Cuanto margen le queda al motor: el suelo de ruido del dato real.

El motor se juzga contra REAL_FIELD, y esos valores no son la verdad: son medias de
unas pocas semanas de MTGO, cada una con su propio ruido de muestreo. Si esas medias
traen +-3 puntos de error, ningun modelo puede bajar de ahi por bueno que sea. Esto
estima ese piso y lo compara con el error del motor.

Metodo, en tres pasos:

  1. Dispersion semana a semana. Para cada arquetipo con varias mediciones se calcula
     su desviacion tipica, y se agrupan todas en una sola estimacion (varianza pooled).
     Ese numero es ruido de muestreo MAS deriva real del metajuego, asi que es una cota
     superior del ruido puro.
  2. Error de la media. El motor no se compara contra una semana suelta sino contra la
     media de k semanas, cuyo error tipico es sd/raiz(k). Los arquetipos con una sola
     medicion no promedian nada y arrastran la sd entera: pesan muchisimo.
  3. Suelo = raiz de la media cuadratica de esos errores, que es la misma vara con la
     que loocv.py reporta el error del motor. Asi se comparan de igual a igual.

Contraste independiente: con muestras de 180-640 listas, el error binomial teorico por
semana es 50/raiz(N) puntos. Si la dispersion observada cae en ese rango, lo que vemos
es muestreo y no metajuego moviendose.

    python3 src/suelo_ruido.py [error_motor] [error_modelo_tonto]
"""
import sys, math, statistics
sys.path.insert(0, 'src'); sys.path.insert(0, 'data')
from real_wr import REAL_SEMANAL, REAL_FIELD


def pooled(series):
    """Desviacion tipica agrupada de varias series. Devuelve (sd, grados_libertad)."""
    num = gl = 0.0
    for v in series:
        if len(v) < 2: continue
        s = statistics.stdev(v)
        num += (len(v) - 1) * s * s
        gl += len(v) - 1
    return (math.sqrt(num / gl) if gl else float('nan')), int(gl)


def analiza(fmt, err_motor=None, err_tonto=None):
    semanal = REAL_SEMANAL.get(fmt) or {}
    campo = REAL_FIELD.get(fmt) or {}
    print(f"\n{'='*72}\nSUELO DE RUIDO — {fmt.upper()}\n{'='*72}")
    if not semanal:
        print("  No hay mediciones repetidas del mismo arquetipo en este formato.")
        print("  Sin series temporales no se puede separar ruido de señal: no calculable.")
        return None

    print(f"\n{'arquetipo':<20}{'n':>3}{'media':>9}{'sd':>8}{'err. media':>12}   semanas")
    con_varias = []
    for nom, v in sorted(semanal.items(), key=lambda x: -len(x[1])):
        m = statistics.mean(v)
        s = statistics.stdev(v) if len(v) > 1 else float('nan')
        if len(v) > 1: con_varias.append(v)
        sd_txt = f"{s:.2f}" if len(v) > 1 else "  --"
        print(f"{nom:<20}{len(v):>3}{m:>8.1f}%{sd_txt:>8}{'':>12}   "
              f"{' '.join(f'{x:.1f}' for x in v)}")

    sd, gl = pooled(con_varias)
    print(f"\n  Dispersion semana a semana (pooled, {gl} g.l.): {sd:.2f} puntos")

    # sin la serie mas dispersa, para ver cuanto depende de un solo outlier
    if len(con_varias) > 1:
        peor = max(con_varias, key=statistics.stdev)
        resto = [v for v in con_varias if v is not peor]
        sd2, gl2 = pooled(resto)
        print(f"  Sin la serie mas volatil ({statistics.stdev(peor):.2f}): "
              f"{sd2:.2f} puntos ({gl2} g.l.)")
    else:
        sd2 = sd

    # contraste binomial: 50/raiz(N) puntos para N partidas no-espejo
    print(f"\n  Contraste binomial (50/raiz(N) puntos por semana):")
    for n in (100, 200, 400, 800):
        print(f"     N={n:<5} -> {50/math.sqrt(n):.2f} puntos")
    print(f"  La dispersion observada equivale a N ~ {int((50/sd)**2)} partidas no-espejo")
    print(f"  por semana, que es del orden de lo que dan muestras de 180-640 listas.")
    print(f"  Es decir: lo que se ve es muestreo, no el metajuego moviendose.")

    # error de la media de cada valor de REAL_FIELD
    print(f"\n{'arquetipo del banco':<20}{'semanas':>9}{'error de su media':>20}")
    errs = []
    for nom in campo:
        k = len(semanal.get(nom, []))
        if k == 0:
            print(f"{nom:<20}{'sin serie':>9}{'no estimable':>20}")
            continue
        e = sd / math.sqrt(k)
        errs.append((nom, k, e))
        aviso = '  <-- sin promediar' if k == 1 else ''
        print(f"{nom:<20}{k:>9}{e:>19.2f}%{aviso}")

    if not errs:
        print("\n  Ningun arquetipo del banco tiene serie: no calculable.")
        return None

    suelo = math.sqrt(sum(e * e for _, _, e in errs) / len(errs))
    suelo2 = suelo * (sd2 / sd)
    print(f"\n  SUELO estimado: {suelo:.2f} puntos   (rango razonable {suelo2:.2f}–{suelo:.2f})")

    total = sum(e * e for _, _, e in errs)
    solos = sum(e * e for _, k, e in errs if k == 1)
    if solos:
        print(f"  Los arquetipos con UNA sola medicion aportan el {solos/total:.0%} de ese ruido.")

    if err_motor is not None:
        print(f"\n  {'-'*68}")
        print(f"  modelo tonto (no simular)  {err_tonto:.2f}%" if err_tonto else "")
        print(f"  motor                      {err_motor:.2f}%")
        print(f"  suelo de ruido             {suelo:.2f}%")
        if err_tonto:
            recorrido = err_tonto - suelo
            ganado = err_tonto - err_motor
            print(f"\n  Recorrido disponible desde el modelo tonto hasta el suelo: "
                  f"{recorrido:.2f} puntos.")
            print(f"  El motor se comio {ganado:.2f} de esos {recorrido:.2f}, "
                  f"o sea el {ganado/recorrido:.0%}.")
            print(f"  Le quedan {err_motor - suelo:.2f} puntos de margen teorico"
                  f"{' — y eso si el suelo esta bien estimado.' if err_motor > suelo else ''}")
        if err_motor <= suelo:
            print("\n  OJO: el motor esta POR DEBAJO del suelo estimado. Eso no demuestra que")
            print("  este sobreajustado: lo mas probable es que el suelo este sobreestimado.")
            print("  Este numero es una COTA SUPERIOR, por tres motivos:")
            print("    - la dispersion semanal mezcla ruido de muestreo con deriva real del meta;")
            print("    - se calcula con muy pocos grados de libertad y una sola serie volatil")
            print("      puede dominarla;")
            print("    - a los arquetipos con una sola medicion se les asigna la sd entera, que")
            print("      es su error ESPERADO, no el que realmente tienen.")
            print("  Tomalo como orden de magnitud, no como un muro. Y recuerda que loocv deja")
            print("  un mazo fuera, pero NO protege de haber elegido los cambios mirando el banco")
            print("  entero: contra eso solo sirve dato nuevo.")
    return suelo


if __name__ == '__main__':
    em = float(sys.argv[1]) if len(sys.argv) > 1 else 3.93
    et = float(sys.argv[2]) if len(sys.argv) > 2 else 4.40
    analiza('pauper', em, et)
    for f in ('standard', 'brawl'):
        analiza(f)
