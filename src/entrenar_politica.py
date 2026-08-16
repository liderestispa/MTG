# -*- coding: utf-8 -*-
"""Entrena la politica de lanzamiento por autojuego, con metodo de entropia cruzada.

La red vive en sim.c (bloque POLNET) y CORRIGE la puntuacion heuristica en vez de
reemplazarla: con los pesos a cero el motor es exactamente el de siempre, asi que el
entrenamiento arranca desde ahi y solo puede mejorar.

Como se mide un candidato. La red pilota SOLO al jugador A (POLNET_LADO=0) y el rival
sigue con la heuristica, asi que la victoria de A es directamente "esta politica juega
mejor que la de siempre". Si pilotara a los dos lados el round-robin no se moveria y no
habria nada que medir.

Por que evolucion y no gradiente: la senal es el resultado de la partida, que no es
derivable respecto de los pesos sin montar RL entero. CEM solo necesita EVALUAR
candidatos, y evaluar es justo lo que esta maquina hace rapido.

LO QUE ESTO NO DECIDE. Ganar mas partidas no basta para adoptar la politica. El motor se
calibra contra winrates de humanos, asi que una politica superhumana pero rara puede
empeorar el ajuste. La adopcion se decide con:

    POLNET=out/politica.txt POLNET_LADO=1 python3 src/valida_semillas.py 2000 "" ""

y solo si baja el objetivo contra dato real. El autojuego propone, el dato real dispone.

    python3 src/entrenar_politica.py                 # 30 generaciones
    python3 src/entrenar_politica.py 200 --horas 8   # toda la tarde
"""
import sys, os, json, math, random, time, io, subprocess, tempfile
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, 'src'); sys.path.insert(0, 'data')

NIN, NH = 17, 12
NPAR = NH * NIN + NH + NH + 1          # 229 pesos

POB      = 40        # candidatos por generacion
ELITE    = 8         # cuantos sobreviven
NGAMES   = 300       # partidas por enfrentamiento
SIGMA0    = 0.35
SIGMA_MIN = 0.03     # suelo; al tocarlo se reinicia en vez de quedarse ahi
SUAVE     = 0.30     # cuanto se mueve la media hacia la elite
FMT      = 'pauper'  # formato de entrenamiento: es el unico validado

# Cuanta maquina se usa. Por defecto un TERCIO de los nucleos, no todos: esto esta
# pensado para correr mientras trabajas. Ademas driver.py lanza el simulador con
# prioridad IDLE, asi que el escritorio manda siempre. --nucleos N para forzarlo.
def cuantos_nucleos(argv):
    if '--nucleos' in argv:
        return max(1, int(argv[argv.index('--nucleos') + 1]))
    n = os.cpu_count() or 4
    return max(1, min(n - 2, int(n * 0.34)))


def escribe_pesos(v, ruta):
    with io.open(ruta, 'w', encoding='utf-8') as f:
        f.write(f"POLNET {NIN} {NH}\n")
        f.write(' '.join(f"{x:.6f}" for x in v))
        f.write('\n')


def evalua(args):
    """Winrate medio del jugador A a traves de todos los enfrentamientos del banco."""
    v, semilla = args
    import driver
    from driver import build, run
    R, opps = build(FMT)
    fd, ruta = tempfile.mkstemp(suffix='.txt', prefix='pol_')
    os.close(fd)
    try:
        escribe_pesos(v, ruta)
        os.environ['POLNET'] = ruta
        os.environ['POLNET_LADO'] = '0'
        tot, n = 0.0, 0
        for i, (dn, w, ids) in enumerate(opps):
            for j, (dn2, w2, ids2) in enumerate(opps):
                if i == j: continue
                r = run(R, [(dn2, 1000, ids2)], [ids],
                        ngames=NGAMES, life=20, seed=semilla + i * 97 + j)[0]
                tot += r['wr']; n += 1
        return tot / n if n else 0.0
    finally:
        os.environ.pop('POLNET', None)
        try: os.remove(ruta)
        except OSError: pass


ESTADO_CEM = 'out/politica_cem.json'


def guarda_cem(mu, sigma, mejor_v, mejor_f, base, reinicios, gen_total, hist):
    json.dump(dict(mu=mu, sigma=sigma, mejor_v=mejor_v, mejor_f=mejor_f, base=base,
                   reinicios=reinicios, gen_total=gen_total, hist=hist[-300:]),
              io.open(ESTADO_CEM, 'w', encoding='utf-8'))


def carga_cem():
    try:
        d = json.load(io.open(ESTADO_CEM, encoding='utf-8'))
        if len(d['mu']) == NPAR: return d
    except (OSError, ValueError, KeyError):
        pass
    return None


def main():
    gens  = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 30
    horas = float(sys.argv[sys.argv.index('--horas') + 1]) if '--horas' in sys.argv else None
    limite = time.time() + horas * 3600 if horas else None

    rnd = random.Random(20260816)
    mu    = [0.0] * NPAR                       # arranca en la heuristica pura
    sigma = [SIGMA0] * NPAR
    hist  = []
    gen_previas = 0
    # --reanudar continua desde donde quedo la corrida anterior. Sin esto, cada bloque
    # del orquestador empezaria otra vez desde la heuristica y no acumularia nada.
    reanudado = None
    if '--reanudar' in sys.argv:
        reanudado = carga_cem()
        if reanudado:
            mu, sigma = reanudado['mu'], reanudado['sigma']
            hist = reanudado.get('hist', [])
            gen_previas = reanudado.get('gen_total', len(hist))
        else:
            print("--reanudar pedido pero no hay estado en out/politica_cem.json: "
                  "se empieza de cero.", flush=True)
    else:
        # SEGURO ANTICLOBBER. Empezar de cero teniendo una politica mejor guardada
        # sobreescribe out/politica.txt con una peor y se pierde el entrenamiento.
        # Paso de verdad: una corrida nueva piso 208 generaciones con 2.
        viejo = carga_cem()
        if viejo and viejo.get('mejor_f'):
            print(f"HAY una politica guardada de la generacion {viejo.get('gen_total')} "
                  f"con {viejo['mejor_f']*100:.3f}%.\n"
                  f"Empezar de cero la sobreescribiria. Usa --reanudar, o borra "
                  f"out/politica_cem.json si de verdad quieres reiniciar.", flush=True)
            return
    nucleos = cuantos_nucleos(sys.argv)
    respiro = float(sys.argv[sys.argv.index('--respiro') + 1]) if '--respiro' in sys.argv else 1.0

    if reanudado:
        base = reanudado['base']
        mejor_v, mejor_f = reanudado['mejor_v'], reanudado['mejor_f']
        reinicios = reanudado.get('reinicios', 0)
        print(f"reanudando en la generacion {gen_previas}: mejor {mejor_f*100:.3f}% contra "
              f"{base*100:.3f}% de base, {reinicios} reinicios, sigma "
              f"{sum(sigma)/NPAR:.3f}", flush=True)
    else:
        base = evalua(([0.0] * NPAR, 1234567))   # la heuristica de siempre, de referencia
        mejor_v, mejor_f, reinicios = [0.0] * NPAR, base, 0
        print(f"heuristica actual (pesos a cero): {base*100:.3f}%", flush=True)
    print(f"poblacion {POB}, elite {ELITE}, {NGAMES} partidas, {nucleos} nucleos", flush=True)

    for g in range(gen_previas + 1, gen_previas + gens + 1):
        if limite and time.time() > limite:
            print("tiempo agotado"); break
        semilla = 900000 + g * 7919            # semilla NUEVA cada generacion: si no,
                                               # la elite se ajusta a una sola tirada
        pobl = [[rnd.gauss(mu[k], sigma[k]) for k in range(NPAR)] for _ in range(POB)]
        with ProcessPoolExecutor(max_workers=nucleos) as ex:
            fits = list(ex.map(evalua, [(v, semilla) for v in pobl]))

        orden = sorted(range(POB), key=lambda i: -fits[i])
        elite = [pobl[i] for i in orden[:ELITE]]
        for k in range(NPAR):
            col = [e[k] for e in elite]
            m = sum(col) / ELITE
            var = sum((x - m) ** 2 for x in col) / ELITE
            mu[k]    = (1 - SUAVE) * mu[k] + SUAVE * m
            sigma[k] = max(SIGMA_MIN, (1 - SUAVE) * sigma[k] + SUAVE * math.sqrt(var))

        # ---- reinicio cuando la distribucion colapsa ----
        # CEM converge y deja de explorar: en la primera corrida sigma toco el suelo
        # hacia la generacion 193 y las siete horas siguientes no habrian aportado nada.
        # Al detectarlo se vuelve a inflar sigma alrededor de la mu actual, que es un
        # reinicio en caliente: se conserva lo aprendido y se recupera la exploracion.
        if sum(sigma) / NPAR <= SIGMA_MIN * 1.15:
            reinicios += 1
            infla = SIGMA0 * (0.7 ** min(reinicios, 4))   # cada vez algo mas fino
            sigma = [infla] * NPAR
            print(f"  --- reinicio {reinicios}: sigma colapsada, reinflada a {infla:.3f} "
                  f"alrededor de la mu actual ---", flush=True)

        fmu = evalua((mu, semilla + 1))        # la media, en semilla distinta a la elite
        if fmu > mejor_f: mejor_f, mejor_v = fmu, list(mu)
        hist.append(dict(gen=g, mejor_pob=max(fits), media_pob=sum(fits) / POB,
                         media_dist=fmu, sigma=sum(sigma) / NPAR))
        print(f"  gen {g:>3}  elite {max(fits)*100:6.3f}%  media {sum(fits)/POB*100:6.3f}%  "
              f"mu {fmu*100:6.3f}%  (base {base*100:.3f}%)  sigma {sum(sigma)/NPAR:.3f}",
              flush=True)
        escribe_pesos(mejor_v, 'out/politica.txt')
        json.dump(dict(base=base, mejor=mejor_f, gens=len(hist), hist=hist[-300:]),
                  io.open('out/politica_hist.json', 'w', encoding='utf-8'), indent=1)
        guarda_cem(mu, sigma, mejor_v, mejor_f, base, reinicios, g, hist)
        if respiro: time.sleep(respiro)   # deja respirar al sistema entre generaciones

    print(f"\nmejor politica {mejor_f*100:.3f}% contra {base*100:.3f}% de la heuristica "
          f"({(mejor_f-base)*100:+.3f} puntos), escrita en out/politica.txt")
    print("\nGANAR PARTIDAS NO BASTA PARA ADOPTARLA. Comprueba contra dato real:")
    print("  POLNET=out/politica.txt POLNET_LADO=1 python3 src/obj_real.py 2000")
    print("  y validala con src/valida_semillas.py antes de tocar nada.")


if __name__ == '__main__':
    main()
