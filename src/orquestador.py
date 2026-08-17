# -*- coding: utf-8 -*-
"""Encadena el trabajo en CICLOS cortos y deja el estado por escrito. Corre mientras trabajas.

    python src/orquestador.py                     # 4 horas
    python src/orquestador.py --horas 2 --nucleos 4
    python src/orquestador.py --solo lab          # una fase suelta

Por que ciclos y no fases largas. Con una fase de entrenamiento de horas no se puede
intervenir: si durante la corrida se escribe una regla nueva en data/reglas_extra.json,
nadie la mide hasta el dia siguiente. En ciclos, cada vuelta vuelve a mirar la cola, asi
que se pueden ir metiendo reglas EN CALIENTE y se miden solas. El entrenamiento reanuda
desde donde quedo (out/politica_cem.json), asi que trocearlo no cuesta nada.

Cada vuelta:
  1. reglas candidatas sin medir -> laboratorio
  2. un bloque de entrenamiento (reanudando)
  3. si la politica mejoro desde la ultima vez, se contrasta contra DATO REAL
  4. se reescribe out/estado.json

QUE MIRAR MIENTRAS CORRE
  out/estado.json       resumen legible de maquina, se actualiza cada vuelta
  out/orquestador.log   salida cruda segun sale
  python src/vigilar.py --seguir

NO ADOPTA NADA. Mide, registra y reporta. Encender una regla o desplegar una politica se
decide leyendo el informe, porque el objetivo mide ORDEN y un arreglo correcto puede
romper la tabla. Ya paso tres veces.
"""
import sys, os, io, json, time, subprocess, datetime

OBJETIVO_ESPERADO = 1.069     # banco de 77k partidas + los cuatro hallazgos del detector
TOLERANCIA = 0.02             # ruido de semilla del objetivo
BLOQUE_GENS = 40              # generaciones por vuelta
LOG = 'out/orquestador.log'
ESTADO = 'out/estado.json'


def ejecuta(args, minutos=None):
    """Corre una fase volcando la salida al log SEGUN SALE, no al terminar."""
    t = time.time()
    env = dict(os.environ, PYTHONUTF8='1')
    with io.open(LOG, 'a', encoding='utf-8', errors='replace') as f:
        f.write(f"\n===== {datetime.datetime.now():%H:%M:%S}  {' '.join(args)}\n"); f.flush()
        try:
            p = subprocess.run([sys.executable, '-u'] + args, stdout=f,
                               stderr=subprocess.STDOUT, env=env,
                               timeout=minutos * 60 if minutos else None)
            rc = p.returncode
        except subprocess.TimeoutExpired:
            f.write('\n[tiempo agotado]\n'); rc = -1
    return time.time() - t, rc


def lee(ruta, defecto=None):
    try:
        return json.load(io.open(ruta, encoding='utf-8'))
    except (OSError, ValueError):
        return defecto


def objetivo_actual():
    ejecuta(['src/obj_real.py', '2000'], minutos=10)
    try:
        txt = io.open(LOG, encoding='utf-8', errors='replace').read()
        for l in reversed(txt.splitlines()):
            if l.startswith('OBJETIVO'): return float(l.split()[1])
    except (OSError, IndexError, ValueError):
        pass
    return None


def escribe_estado(e):
    e['actualizado'] = datetime.datetime.now().isoformat(timespec='seconds')
    json.dump(e, io.open(ESTADO, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def resumen_lab():
    reg = lee('out/laboratorio.json', {'probadas': 0, 'entradas': []})
    c = {}
    for x in reg['entradas']: c[x['veredicto']] = c.get(x['veredicto'], 0) + 1
    # Las mejoras se muestran UNA VEZ por spec, quedandose con la mas reciente. El
    # registro tenia siete entradas con el mismo spec —la politica, con nombre de archivo
    # fijo, medida en checkpoints distintos— y el informe las listaba como siete
    # victorias. Ademas se marca la huella del banco: las que no coinciden con el banco
    # de hoy se midieron contra otro dato y no son comparables.
    try:
        from laboratorio import huella_banco
        hoy = huella_banco()
    except Exception:
        hoy = '?'
    ultima = {}
    for x in reg['entradas']:
        if x['veredicto'] == 'MEJORA': ultima[x['spec']] = x
    return dict(probadas=reg['probadas'], veredictos=c, banco=hoy,
                mejoras=[dict(spec=x['spec'], media=x['media'],
                              banco=x.get('banco', 'sin marcar'),
                              vigente=(x.get('banco') == hoy))
                         for x in ultima.values()])


def pendientes():
    d = lee('data/reglas_extra.json', {'reglas': []})
    reg = lee('out/laboratorio.json', {'entradas': []})
    ya = {x['spec'] for x in reg['entradas']}
    return [r['nombre'] for r in d.get('reglas', [])
            if not r.get('activo') and r.get('medir', True)
            and f"REGLA_SOLO={r['nombre']}" not in ya]


def main():
    a = sys.argv
    horas   = float(a[a.index('--horas') + 1]) if '--horas' in a else 4.0
    nucleos = a[a.index('--nucleos') + 1] if '--nucleos' in a else None
    respiro = a[a.index('--respiro') + 1] if '--respiro' in a else '1.0'
    solo    = a[a.index('--solo') + 1] if '--solo' in a else None
    fin = time.time() + horas * 3600
    t0 = datetime.datetime.now()
    est = dict(inicio=t0.isoformat(timespec='seconds'), horas=horas, fase='arrancando',
               ciclo=0, avisos=[])
    escribe_estado(est)

    def queda(): return max(0.0, (fin - time.time()) / 60.0)

    # ---- control ----
    est['fase'] = 'control'; escribe_estado(est)
    obj = objetivo_actual()
    est['objetivo_control'] = obj
    if obj is None or abs(obj - OBJETIVO_ESPERADO) > TOLERANCIA:
        est['fase'] = 'PARADO'
        est['avisos'].append(f"el arbol da {obj} y se esperaba {OBJETIVO_ESPERADO}: "
                             f"medir sobre un motor desconocido no vale nada")
        escribe_estado(est)
        print(f"PARADO: objetivo {obj}, esperado {OBJETIVO_ESPERADO}"); return
    print(f"control: objetivo {obj:.3f} OK")

    # ---- cobertura ----
    est['fase'] = 'cobertura'; escribe_estado(est)
    ejecuta(['src/cobertura_texto.py'], minutos=10)
    cola = lee('out/cobertura_banco.json', [])
    blancas = [r for r in cola if r['categoria'] == 'BLANCA']
    est['cobertura'] = dict(blancas=len(blancas),
                            copias=sum(r['copias'] for r in blancas),
                            top=[f"{r['copias']}x {r['carta']}" for r in blancas[:8]])
    escribe_estado(est)
    print(f"cobertura: {len(blancas)} cartas en blanco")

    # ---- ciclos ----
    # El resumen del laboratorio se calcula ANTES del bucle: con --solo el bucle no
    # corre y el informe salia diciendo "0 hipotesis" con 43 en el registro.
    est['laboratorio'] = resumen_lab()
    ultimo_mejor = None
    ciclo = 0
    while queda() > 3 and solo is None:
        ciclo += 1
        est['ciclo'] = ciclo; est['minutos_restantes'] = round(queda())

        pend = pendientes()
        if pend:
            est['fase'] = f'laboratorio ({len(pend)} candidatas)'; escribe_estado(est)
            seg, _ = ejecuta(['src/laboratorio.py', '--reglas'], minutos=min(60, queda()))
            print(f"ciclo {ciclo}: laboratorio, {len(pend)} candidatas ({seg/60:.0f} min)")
        est['laboratorio'] = resumen_lab()

        if queda() < 4: break
        est['fase'] = f'entrenando (ciclo {ciclo})'; escribe_estado(est)
        args = ['src/entrenar_politica.py', str(BLOQUE_GENS), '--reanudar',
                '--horas', f"{min(queda() - 2, 45) / 60:.3f}", '--respiro', respiro]
        if nucleos: args += ['--nucleos', nucleos]
        seg, _ = ejecuta(args, minutos=min(queda(), 50))

        h = lee('out/politica_cem.json', {})
        if h:
            est['politica'] = dict(gen=h.get('gen_total'), base=h.get('base'),
                                   mejor=h.get('mejor_f'), reinicios=h.get('reinicios'),
                                   sigma=round(sum(h.get('sigma', [0])) / max(1, len(h.get('sigma', [1]))), 4))
            # DOS numeros, y solo uno es una medida.
            #   inflado = mejor_f - base, o sea el MAXIMO de una evaluacion por generacion
            #             contra UNA sola de referencia. Sube solo con dejarlo corriendo.
            #             En una corrida real dijo +2,135 cuando lo cierto era +1,25.
            #   honesto = mu contra la heuristica en semillas que no seleccionan nada, y
            #             emparejadas. Lo escribe entrenar_politica.py cada 20 generaciones.
            inflado = (h.get('mejor_f', 0) - h.get('base', 0)) * 100
            honesto = (lee('out/politica_hist.json', {}) or {}).get('validacion')
            est['politica']['ganancia_autojuego'] = round(honesto, 3) if honesto is not None \
                                                    else None
            est['politica']['ganancia_inflada'] = round(inflado, 3)
            txt = f"{honesto:+.3f} real" if honesto is not None else "sin validar aun"
            print(f"ciclo {ciclo}: gen {h.get('gen_total')}, autojuego {txt} "
                  f"(el maximo dice {inflado:+.3f}), "
                  f"sigma {est['politica']['sigma']:.3f} ({seg/60:.0f} min)")

            # Contrastar contra DATO REAL cuando cambie CUALQUIERA de los dos. Antes el
            # disparador era solo mejor_f, que es un maximo: en una corrida se congelo en
            # el ciclo 18 y los 22 ciclos siguientes no contrastaron nada, aunque mu si
            # se estaba moviendo.
            marca = (h.get('mejor_f'), honesto)
            if h.get('mejor_f') and marca != ultimo_mejor and queda() > 8:
                ultimo_mejor = marca
                est['fase'] = 'contrastando politica con dato real'; escribe_estado(est)
                import shutil
                # Nombre UNICO por generacion. Con un nombre fijo el registro acumulaba
                # siete entradas con el mismo spec, indistinguibles entre si: no se podia
                # saber a que punto del entrenamiento correspondia cada una, y --reglas no
                # las podia filtrar. Son hipotesis distintas y tienen que llamarse distinto.
                probando = f"out/politica_g{h.get('gen_total')}.txt"
                shutil.copy('out/politica.txt', probando)
                ejecuta(['src/laboratorio.py',
                         f'POLNET={probando} POLNET_LADO=1'],
                        minutos=min(20, queda()))
                reg = lee('out/laboratorio.json', {'entradas': []})
                pol = [x for x in reg['entradas'] if 'POLNET' in x['spec']]
                if pol:
                    u = pol[-1]
                    est['politica']['contra_dato_real'] = dict(
                        media=u['media'], veredicto=u['veredicto'], motivo=u['motivo'])
                    print(f"          contra dato real: {u['media']:+.3f} -> {u['veredicto']}")
        escribe_estado(est)

    # ---- informe ----
    est['fase'] = 'terminado'; escribe_estado(est)
    inf = [f"# Informe del {t0:%Y-%m-%d %H:%M} — {ciclo} ciclos en "
           f"{(datetime.datetime.now()-t0).seconds//60} min", "",
           f"Objetivo de control: **{obj:.3f}**", ""]
    c = est.get('cobertura', {})
    inf += ["## Cola de trabajo", "",
            f"{c.get('blancas', 0)} cartas en blanco ({c.get('copias', 0)} copias). "
            f"Las que mas pesan:", ""]
    inf += [f"- {x}" for x in c.get('top', [])]
    inf += ["", "*Lo unico que necesita tokens: leer estas cartas y escribir la regla en "
            "`data/reglas_extra.json` con `activo:false`.*", ""]
    lab = est.get('laboratorio', {})
    inf += ["## Laboratorio", "",
            f"{lab.get('probadas', 0)} hipotesis en total: " +
            ', '.join(f"{k} {v}" for k, v in sorted(lab.get('veredictos', {}).items())), ""]
    for m in lab.get('mejoras', []):
        # Ojo con leer esto como "el cambio es malo": lo que no vale es el NUMERO. Las
        # dos reglas del extractor se midieron contra el banco viejo y despues se
        # revalidaron contra el nuevo, y siguen en pie.
        aviso = '' if m.get('vigente') else \
                f"  ← el numero es de otro banco (`{m.get('banco')}`): hay que revalidarlo"
        inf.append(f"- **MEJORA** `{m['spec']}` {m['media']:+.3f}{aviso}")
    p = est.get('politica')
    if p:
        g = p.get('ganancia_autojuego')
        inf += ["", "## Politica de juego", "",
                f"- generacion **{p.get('gen')}**, {p.get('reinicios')} reinicios, "
                f"sigma {p.get('sigma')}",
                f"- autojuego, medido en semillas limpias y emparejadas: "
                f"**{g:+.3f}** puntos sobre la heuristica" if g is not None else
                "- autojuego: sin validar todavia en esta corrida",
                f"- (el maximo historico dice {p.get('ganancia_inflada'):+.3f}, y esta "
                f"inflado por ser un maximo: no lo uses para decidir nada)"]
        cdr = p.get('contra_dato_real')
        if cdr:
            inf += [f"- contra dato real: **{cdr['media']:+.3f}** → **{cdr['veredicto']}** "
                    f"({cdr['motivo']})"]
            if cdr['veredicto'] == 'MEJORA':
                inf += ["", "> Supero el contraste. Revisa el desglose por arquetipo antes "
                        "de desplegarla: el objetivo mide orden."]
    inf += ["", "---", "*`src/orquestador.py`. Estado en vivo: `out/estado.json`.*"]
    io.open('out/informe_dia.md', 'w', encoding='utf-8').write('\n'.join(inf))
    print("\nescrito out/informe_dia.md")


if __name__ == '__main__':
    main()
