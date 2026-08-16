# -*- coding: utf-8 -*-
"""Encadena el trabajo del dia y escribe un informe. Pensado para correr MIENTRAS trabajas.

    python src/orquestador.py --horas 8
    python src/orquestador.py --horas 2 --nucleos 4      # maquina ocupada
    python src/orquestador.py --solo lab                 # una fase suelta

Fases:
  1. control     comprueba que el arbol reproduce el objetivo esperado. Si no, para:
                 medir sobre un motor roto es peor que no medir.
  2. cobertura   regenera la cola de cartas cuyo texto el motor no lee.  (segundos)
  3. laboratorio mide las reglas candidatas de data/reglas_extra.json.   (minutos)
  4. politica    entrena la politica de lanzamiento por autojuego.       (el resto)
  5. informe     escribe out/informe_dia.md

CONVIVENCIA CON TU MAQUINA. Esto no puede dejarte el PC inutilizable:
  - driver.py lanza el simulador con prioridad IDLE en Windows, asi que el escritorio
    manda siempre y el motor solo usa los ciclos que sobran.
  - por defecto se usa un TERCIO de los nucleos, no todos.
  - entre generaciones hay una pausa para que el sistema respire.
  - --nucleos N y --respiro S para ajustarlo a mano.

LO QUE NO HACE, A PROPOSITO: no adopta nada. Mide, registra y reporta. Encender una
regla o desplegar una politica es una decision que se toma leyendo el informe, porque
el objetivo mide ORDEN y un arreglo correcto puede romper la tabla. Ya paso tres veces.
"""
import sys, os, io, json, time, subprocess, datetime

OBJETIVO_ESPERADO = 1.547     # actualizalo cuando adoptes un cambio de motor
TOLERANCIA = 0.02             # ruido de semilla del objetivo


LOG = 'out/orquestador.log'


def ejecuta(args, minutos=None):
    """Corre una fase VOLCANDO la salida al log segun sale.

    Antes usaba capture_output, que retiene todo hasta que la fase acaba: con un
    entrenamiento de ocho horas eso son ocho horas a ciegas. Ahora se puede seguir con
    `Get-Content out/orquestador.log -Wait` o con `python src/vigilar.py --seguir`.
    """
    t = time.time()
    env = dict(os.environ, PYTHONUTF8='1')
    with io.open(LOG, 'a', encoding='utf-8', errors='replace') as f:
        f.write(f"\n===== {datetime.datetime.now():%H:%M:%S}  {' '.join(args)}\n")
        f.flush()
        try:
            p = subprocess.run([sys.executable, '-u'] + args, stdout=f,
                               stderr=subprocess.STDOUT, env=env,
                               timeout=minutos * 60 if minutos else None)
            rc = p.returncode
        except subprocess.TimeoutExpired:
            f.write('\n[tiempo agotado]\n'); rc = -1
    try:
        with io.open(LOG, encoding='utf-8', errors='replace') as f:
            texto = f.read()
        texto = texto[texto.rfind(f"===== ") if '=====' in texto else 0:]
    except OSError:
        texto = ''
    return texto, time.time() - t, rc


def objetivo_actual():
    out, _, _ = ejecuta(['src/obj_real.py', '2000'], minutos=10)
    for l in out.splitlines():
        if l.startswith('OBJETIVO'):
            try: return float(l.split()[1])
            except (IndexError, ValueError): pass
    return None


def main():
    a = sys.argv
    horas   = float(a[a.index('--horas') + 1]) if '--horas' in a else 4.0
    nucleos = a[a.index('--nucleos') + 1] if '--nucleos' in a else None
    respiro = a[a.index('--respiro') + 1] if '--respiro' in a else '1.0'
    solo    = a[a.index('--solo') + 1] if '--solo' in a else None
    fin = time.time() + horas * 3600
    inicio = datetime.datetime.now()
    inf = [f"# Informe del {inicio:%Y-%m-%d %H:%M}", ""]

    def queda(): return max(0.0, (fin - time.time()) / 60.0)

    # ---- 1. control ----
    if not solo:
        obj = objetivo_actual()
        if obj is None:
            print("no pude medir el objetivo: motor roto o sin compilar. Paro."); return
        desvio = abs(obj - OBJETIVO_ESPERADO)
        inf += [f"## Control", "",
                f"- objetivo medido **{obj:.3f}**, esperado {OBJETIVO_ESPERADO:.3f} "
                f"(desvio {desvio:.3f})", ""]
        print(f"control: objetivo {obj:.3f} (esperado {OBJETIVO_ESPERADO:.3f})")
        if desvio > TOLERANCIA:
            inf += ["> **PARADO.** El arbol no reproduce el objetivo esperado. Medir sobre",
                    "> un motor que no sabemos que es no vale nada. Revisa antes de seguir.", ""]
            io.open('out/informe_dia.md', 'w', encoding='utf-8').write('\n'.join(inf))
            print("PARADO: el arbol no reproduce el objetivo. Ver out/informe_dia.md"); return

    # ---- 2. cobertura ----
    if solo in (None, 'cobertura'):
        out, seg, _ = ejecuta(['src/cobertura_texto.py'], minutos=10)
        cola = []
        try:
            cola = json.load(io.open('out/cobertura_banco.json', encoding='utf-8'))
        except (OSError, ValueError): pass
        blancas = [r for r in cola if r['categoria'] == 'BLANCA']
        inf += ["## Cola de trabajo", "",
                f"{len(blancas)} cartas en blanco para el motor "
                f"({sum(r['copias'] for r in blancas)} copias). Las diez que mas pesan:", ""]
        for r in blancas[:10]:
            inf.append(f"- **{r['copias']}x {r['carta']}** — {r['texto'][:110]}")
        inf += ["", "*Esto es lo unico que necesita tokens: leer estas cartas y escribir la "
                    "regla en `data/reglas_extra.json`.*", ""]
        print(f"cobertura: {len(blancas)} cartas en blanco ({seg:.0f}s)")

    # ---- 3. laboratorio ----
    if solo in (None, 'lab'):
        antes = len(json.load(io.open('out/laboratorio.json', encoding='utf-8'))['entradas']) \
                if os.path.exists('out/laboratorio.json') else 0
        out, seg, _ = ejecuta(['src/laboratorio.py', '--reglas'], minutos=min(90, queda()))
        reg = json.load(io.open('out/laboratorio.json', encoding='utf-8')) \
              if os.path.exists('out/laboratorio.json') else {'entradas': []}
        nuevas = reg['entradas'][antes:]
        inf += ["## Laboratorio", ""]
        if not nuevas:
            inf += ["Nada nuevo que medir: no hay reglas candidatas apagadas en "
                    "`data/reglas_extra.json`.", ""]
        else:
            inf += ["| hipotesis | delta | veredicto |", "|---|---|---|"]
            for e in nuevas:
                inf.append(f"| `{e['spec']}` | {e['media']:+.3f} | **{e['veredicto']}** |")
            buenas = [e for e in nuevas if e['veredicto'] == 'MEJORA']
            inf += ["", f"{len(buenas)} candidatas superaron el contraste. "
                        f"**No estan adoptadas**: revisa el desglose por arquetipo antes de "
                        f"encender nada, porque el objetivo mide orden.", ""]
        print(f"laboratorio: {len(nuevas)} hipotesis medidas ({seg:.0f}s)")

    # ---- 4. politica ----
    if solo in (None, 'politica') and queda() > 10:
        args = ['src/entrenar_politica.py', '9999', '--horas', f"{queda()/60:.2f}",
                '--respiro', respiro]
        if nucleos: args += ['--nucleos', nucleos]
        out, seg, _ = ejecuta(args, minutos=queda() + 5)
        gens = [l for l in out.splitlines() if l.strip().startswith('gen ')]
        inf += ["## Politica de juego (autojuego)", ""]
        if gens:
            inf += [f"{len(gens)} generaciones en {seg/60:.0f} min.", "", "```",
                    gens[0].strip(), *([ '...' ] if len(gens) > 2 else []),
                    gens[-1].strip(), "```", ""]
            try:
                h = json.load(io.open('out/politica_hist.json', encoding='utf-8'))
                d = (h['mejor'] - h['base']) * 100
                inf += [f"Mejor politica: **{h['mejor']*100:.3f}%** contra "
                        f"{h['base']*100:.3f}% de la heuristica ({d:+.3f} puntos).", ""]
                if d > 0.3:
                    inf += ["> Gana mas partidas. **Eso no basta para adoptarla.** "
                            "Compruebalo contra dato real:", "",
                            "> ```", "> POLNET=out/politica.txt POLNET_LADO=1 "
                            "python src/valida_semillas.py 2000 \"\" \"\"", "> ```", ""]
                else:
                    inf += ["Todavia no se despega de la heuristica. Necesita mas "
                            "generaciones.", ""]
            except (OSError, ValueError, KeyError): pass
        else:
            inf += ["No llego a completar ninguna generacion.", ""]
        print(f"politica: {len(gens)} generaciones ({seg/60:.0f} min)")

    inf += ["---", f"*Generado por `src/orquestador.py` en "
            f"{(datetime.datetime.now()-inicio).seconds//60} minutos.*"]
    io.open('out/informe_dia.md', 'w', encoding='utf-8').write('\n'.join(inf))
    print("\nescrito out/informe_dia.md")


if __name__ == '__main__':
    main()
