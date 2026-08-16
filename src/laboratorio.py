# -*- coding: utf-8 -*-
"""Prueba hipotesis contra el dato real, con disciplina estadistica, sin gastar tokens.

Automatiza el bucle que dio todas las victorias: cambiar algo, medir, validar, adoptar
o aparcar. Lo que NO automatiza es inventar la hipotesis a partir del texto de una
carta; eso sigue siendo criterio. La cola la genera src/cobertura_texto.py.

EL PROBLEMA QUE ESTE ARCHIVO EXISTE PARA EVITAR

Hay diez winrates reales publicados. Un proceso que pruebe cien hipotesis al dia contra
diez numeros VA a encontrar mejoras falsas: no es un riesgo, es una certeza aritmetica.
Ya paso a mano con SWEEP_MIN=3, que el descenso propuso dos campanas seguidas y las dos
veces era ruido de la semilla canonica. Automatizado, ese error se multiplica.

Cuatro guardas, y ninguna es opcional:

  1. Numeros aleatorios comunes. Cada variante se mide con las MISMAS semillas que la
     referencia y se comparan las diferencias emparejadas. Elimina la varianza del
     escenario y multiplica la potencia del contraste.
  2. Correccion por comparaciones multiples. El umbral se endurece con el numero total
     de hipotesis probadas en la historia del registro, no solo en esta corrida
     (Bonferroni sobre alfa=0,05). Por eso el registro es permanente.
  3. Semillas de confirmacion. Tres semillas que NO participan en la decision. Si el
     signo del efecto no aguanta en ellas, no se adopta aunque el contraste pase.
  4. Registro completo, tambien de lo que falla. Sin el no se puede corregir por
     comparaciones multiples, y ademas evita volver a perseguir un fantasma ya muerto.

    python3 src/laboratorio.py --lista                    # que hay en la cola
    python3 src/laboratorio.py "ETBMANA_ON=1" "RECUR_ON=1"
    python3 src/laboratorio.py --reglas                   # las de reglas_extra.json
    python3 src/laboratorio.py --reglas --horas 6         # dejarlo trabajando
"""
import sys, os, io, json, math, time, statistics
sys.path.insert(0, 'src'); sys.path.insert(0, 'data')
from valida_semillas import con_variante

REGISTRO = 'out/laboratorio.json'
# Nueve semillas y no cinco: con la correccion por comparaciones multiples, cinco no dan
# potencia para nada por debajo de ~0,08, y la primera politica aprendida se quedo a las
# puertas con -0,070. El error tipico baja con la raiz del numero de semillas.
SEMILLAS_DECISION    = [1234567, 777001, 20260816, 424242, 99881177,
                        13579, 246810, 55501, 909091]
SEMILLAS_CONFIRMACION = [31337, 606060, 8112024]
NGAMES = 2000
ALFA = 0.05
MINIMO = 0.02        # efecto minimo que merece llamarse asi: el ruido de semilla


def inv_normal(p):
    """Cuantil de la normal estandar. Aproximacion de Acklam; no hay scipy en la maquina."""
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    pl, ph = 0.02425, 1 - 0.02425
    if p < pl:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > ph:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5; r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def carga_registro():
    try:
        with io.open(REGISTRO, encoding='utf-8') as f: return json.load(f)
    except (OSError, ValueError):
        return {'probadas': 0, 'entradas': []}


def guarda_registro(reg):
    json.dump(reg, io.open(REGISTRO, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def mide(spec, semillas):
    return [con_variante(spec, NGAMES, s)[0] * 100 for s in semillas]


def prueba(spec, reg):
    """Compara 'spec' contra la referencia con numeros aleatorios comunes."""
    base_d = mide('', SEMILLAS_DECISION)
    var_d  = mide(spec, SEMILLAS_DECISION)
    difs = [v - b for v, b in zip(var_d, base_d)]
    media = statistics.mean(difs)
    sd    = statistics.stdev(difs) if len(difs) > 1 else 0.0
    se    = sd / math.sqrt(len(difs)) if sd else 1e-9

    n_probadas = reg['probadas'] + 1
    z = inv_normal(1 - ALFA / (2 * n_probadas))          # Bonferroni sobre toda la historia
    # Significancia ESTADISTICA y significancia PRACTICA son cosas distintas. Con
    # numeros aleatorios comunes la varianza emparejada es diminuta, asi que una
    # diferencia de milesimas sale "significativa" y no significa nada: el ruido de
    # semilla del objetivo es +-0,02. Todo lo que no llegue a MINIMO se llama ruido
    # aunque el contraste pase.
    significativa = abs(media) > z * se and abs(media) >= MINIMO

    confirma = None
    if significativa and media < 0:                      # solo si parece mejora
        base_c = mide('', SEMILLAS_CONFIRMACION)
        var_c  = mide(spec, SEMILLAS_CONFIRMACION)
        dc = [v - b for v, b in zip(var_c, base_c)]
        confirma = statistics.mean(dc)

    if not significativa:
        if abs(media) < MINIMO and abs(media) > z * se:
            veredicto, motivo = 'irrelevante', f"{media:+.3f} real pero por debajo de {MINIMO}"
        else:
            veredicto, motivo = 'ruido', f"|{media:+.3f}| no supera {z:.2f}·{se:.3f}={z*se:.3f}"
    elif media > 0:
        veredicto, motivo = 'empeora', f"{media:+.3f} significativo"
    elif confirma is not None and confirma >= 0:
        veredicto, motivo = 'no confirma', f"decision {media:+.3f} pero confirmacion {confirma:+.3f}"
    else:
        veredicto, motivo = 'MEJORA', f"{media:+.3f} (confirmacion {confirma:+.3f})"

    ent = dict(spec=spec, media=round(media, 4), sd=round(sd, 4), se=round(se, 4),
               z_exigido=round(z, 3), n_probadas=n_probadas, confirmacion=confirma,
               veredicto=veredicto, motivo=motivo,
               base=[round(x, 3) for x in base_d], variante=[round(x, 3) for x in var_d])
    reg['probadas'] = n_probadas
    reg['entradas'].append(ent)
    guarda_registro(reg)
    return ent


def cola_de_reglas():
    try:
        with io.open('data/reglas_extra.json', encoding='utf-8') as f:
            reglas = json.load(f).get('reglas', [])
    except (OSError, ValueError):
        return []
    # medir=false marca las que el analisis ya descarto: o su arquetipo no tiene winrate
    # real, o la sensibilidad del objetivo a ese formato es menor que el ruido. Medirlas
    # gasta maquina y, peor, sube el umbral de Bonferroni para TODAS las demas.
    # El ORDEN del archivo es el orden de medicion, y esta puesto a proposito: primero
    # las que tocan arquetipos cuya subida baja el objetivo.
    return [f"REGLA_SOLO={r['nombre']}" for r in reglas
            if not r.get('activo') and r.get('medir', True)]


def main():
    reg = carga_registro()
    if '--lista' in sys.argv:
        print(f"registro: {reg['probadas']} hipotesis probadas en total")
        for e in reg['entradas'][-20:]:
            print(f"  {e['veredicto']:<12} {e['spec']:<34} {e['media']:+.3f}  {e['motivo']}")
        pend = cola_de_reglas()
        print(f"\nreglas inactivas en data/reglas_extra.json: {len(pend)}")
        for p in pend[:20]: print(f"  {p}")
        return

    horas = float(sys.argv[sys.argv.index('--horas') + 1]) if '--horas' in sys.argv else None
    limite = time.time() + horas * 3600 if horas else None
    specs = cola_de_reglas() if '--reglas' in sys.argv else \
            [a for a in sys.argv[1:] if not a.startswith('--') and not a.replace('.', '').isdigit()]
    if not specs:
        if '--reglas' in sys.argv:
            print("No hay reglas candidatas apagadas en data/reglas_extra.json.\n"
                  "La cola de trabajo la genera:  python src/cobertura_texto.py\n"
                  "Despues hay que leer esas cartas y escribir la regla en el JSON con\n"
                  "activo:false. Eso es lo unico del bucle que necesita criterio.")
        else:
            print("nada que probar. Usa --lista, --reglas, o pasa specs tipo \"FLAG=1\".")
        return

    print(f"{len(specs)} hipotesis. Umbral con Bonferroni sobre {reg['probadas']} ya probadas.\n")
    for spec in specs:
        if limite and time.time() > limite:
            print("tiempo agotado"); break
        e = prueba(spec, reg)
        marca = '***' if e['veredicto'] == 'MEJORA' else '   '
        print(f"{marca} {e['veredicto']:<12} {spec:<34} {e['media']:+.3f}  {e['motivo']}", flush=True)

    buenas = [e for e in reg['entradas'] if e['veredicto'] == 'MEJORA']
    print(f"\n{len(buenas)} mejoras confirmadas en toda la historia del registro "
          f"({reg['probadas']} hipotesis).")
    print("Ninguna se adopta sola: revisa el desglose por arquetipo antes de encender nada,")
    print("porque el objetivo mide ORDEN y un arreglo puede subir a un mazo y romper la tabla.")


if __name__ == '__main__':
    main()
