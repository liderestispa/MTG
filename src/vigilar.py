# -*- coding: utf-8 -*-
"""Mira como va el orquestador sin esperar a que termine, y sin estorbarle.

Solo LEE archivos que las otras piezas escriben en vivo. No lanza simulaciones, no
consume CPU y no interfiere: se puede correr en otra terminal mientras trabaja.

    python src/vigilar.py            # una foto
    python src/vigilar.py --seguir   # se refresca cada 30 s

Lo importante no es el numero, son los AVISOS: estan puestos para cazar un bug a los
diez minutos en vez de a las ocho horas. Los tres que mas valen:

  - No llegan generaciones nuevas -> se colgo, o el motor esta petando en cada llamada.
  - Sigma en el suelo -> la distribucion colapso y ya no explora: seguir es tirar horas.
  - La media no se despega de la base -> no esta aprendiendo nada.
"""
import sys, os, io, json, time, datetime

SEGUIR_CADA = 30


def edad(ruta):
    try: return time.time() - os.path.getmtime(ruta)
    except OSError: return None


def hhmm(seg):
    if seg is None: return '—'
    seg = int(seg)
    return f"{seg//3600}h {seg%3600//60}m" if seg >= 3600 else f"{seg//60}m {seg%60}s"


def foto():
    L = []
    ahora = datetime.datetime.now()
    L.append(f"=== {ahora:%H:%M:%S} ===")
    avisos = []

    # ---- estado del orquestador ----
    try:
        e = json.load(io.open('out/estado.json', encoding='utf-8'))
        L.append(f"orquestador  ciclo {e.get('ciclo', 0)}  fase: {e.get('fase')}  "
                 f"quedan {e.get('minutos_restantes', '?')} min")
        for a in e.get('avisos', []): avisos.append(a)
        ed = edad('out/estado.json')
        if ed is not None and ed > 3600:
            avisos.append(f"el estado no se actualiza desde hace {hhmm(ed)}")
    except (OSError, ValueError):
        L.append("orquestador  (sin estado; puede que no este corriendo)")

    # ---- laboratorio ----
    try:
        reg = json.load(io.open('out/laboratorio.json', encoding='utf-8'))
        e = reg['entradas']
        cuenta = {}
        for x in e: cuenta[x['veredicto']] = cuenta.get(x['veredicto'], 0) + 1
        L.append(f"laboratorio  {reg['probadas']} hipotesis  " +
                 '  '.join(f"{k}:{v}" for k, v in sorted(cuenta.items())))
        mej = [x for x in e if x['veredicto'] == 'MEJORA']
        for x in mej[-3:]:
            L.append(f"             *** {x['spec']}  {x['media']:+.3f}")
    except (OSError, ValueError):
        L.append("laboratorio  (sin registro todavia)")

    # ---- politica ----
    try:
        h = json.load(io.open('out/politica_hist.json', encoding='utf-8'))
        hist, base = h['hist'], h['base'] * 100
        ult = hist[-1]
        mejor = h['mejor'] * 100
        # La generacion buena esta en el estado CEM, no aqui: politica_hist.json solo
        # tiene las de ESTE bloque, asi que al trocear el entrenamiento en ciclos decia
        # 26 cuando la real era 236. Un monitor que engana es peor que no tenerlo.
        cem = json.load(io.open('out/politica_cem.json', encoding='utf-8')) \
              if os.path.exists('out/politica_cem.json') else {}
        g = cem.get('gen_total', len(hist))
        rein = cem.get('reinicios', 0)
        ed = edad('out/politica_hist.json')
        L.append(f"politica     gen {g} ({len(hist)} en este bloque, {rein} reinicios)   "
                 f"base {base:.3f}%   mejor {mejor:.3f}%   ({mejor-base:+.3f})   "
                 f"hace {hhmm(ed)}")
        L.append(f"             ultima gen: elite {ult['mejor_pob']*100:.3f}%  "
                 f"mu {ult['media_dist']*100:.3f}%  sigma {ult['sigma']:.3f}")

        # tendencia de las ultimas 10 generaciones
        v = [x['media_dist'] * 100 for x in hist[-10:]]
        if len(v) >= 4:
            mitad = len(v) // 2
            tend = sum(v[mitad:]) / len(v[mitad:]) - sum(v[:mitad]) / len(v[:mitad])
            L.append(f"             tendencia ultimas {len(v)} gens: {tend:+.3f} puntos")

        # ---- avisos ----
        if ed is not None and ed > 900:
            avisos.append(f"NO llegan generaciones desde hace {hhmm(ed)}. Puede estar "
                          f"colgado o el motor petando en cada llamada.")
        if ult['sigma'] <= 0.035:
            avisos.append("SIGMA EN EL SUELO: la distribucion colapso y ya no explora. "
                          "Seguir horas asi no aporta; sube SIGMA0 o reinicia.")
        if g >= 15 and mejor - base < 0.05:
            avisos.append(f"En {g} generaciones la mejor politica solo saca {mejor-base:+.3f} "
                          f"puntos a la heuristica. O el margen no esta aqui, o hay un bug.")
        if g >= 8:
            ritmo = None
            try:
                t0 = os.path.getmtime('out/politica.txt')
                ritmo = None  # solo tenemos la marca de la ultima escritura
            except OSError: pass
        if any(x['media_dist'] < x['mejor_pob'] - 0.03 for x in hist[-5:]):
            avisos.append("La media de la distribucion va MUY por debajo de su elite: "
                          "senal de que la elite se esta ajustando a la semilla del turno.")
    except (OSError, ValueError, KeyError, IndexError):
        L.append("politica     (sin historial todavia; puede seguir en laboratorio)")

    # ---- informe final ----
    if os.path.exists('out/informe_dia.md'):
        ed = edad('out/informe_dia.md')
        if ed is not None and ed < 300:
            L.append("")
            L.append(">>> out/informe_dia.md recien escrito: el orquestador TERMINO.")

    # ---- procesos ----
    if os.name == 'nt':
        try:
            import subprocess
            r = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq bin_sim.exe'],
                               capture_output=True, text=True)
            n = r.stdout.count('bin_sim.exe')
            L.append(f"motor        {n} procesos bin_sim vivos")
            if n == 0:
                avisos.append("NINGUN proceso del motor vivo. O termino, o se cayo.")
        except OSError:
            pass

    if avisos:
        L.append("")
        for a in avisos: L.append(f"  /!\\  {a}")
    return '\n'.join(L)


if __name__ == '__main__':
    if '--seguir' in sys.argv:
        try:
            while True:
                print(foto(), flush=True); print(flush=True)
                time.sleep(SEGUIR_CADA)
        except KeyboardInterrupt:
            print("fin")
    else:
        print(foto())
