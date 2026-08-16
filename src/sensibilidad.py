# -*- coding: utf-8 -*-
"""Cuanto cambia el objetivo si un arquetipo sube. El mapa antes de tocar nada.

El objetivo mide CORRELACION DE ORDEN, no error absoluto, asi que el residuo crudo de un
arquetipo no dice si conviene subirlo. Un mazo puede estar 13 puntos por debajo de su
winrate real y aun asi estar en su sitio relativo: subirlo entonces ROMPE el orden y
empeora el ajuste. Ya paso tres veces (Burning-Tree Emissary dos, bonus_por_artefacto una).

Esto lo mide en vez de opinarlo: perturba el campo medido sumando +N puntos a un
arquetipo y restando lo mismo repartido entre los demas (suma cero, para no mover la
media, que la escala ya perdona), y recalcula el objetivo.

  signo negativo -> subir ese arquetipo BAJA el objetivo: es la direccion que paga
  signo positivo -> subirlo lo empeora, por muy infravalorado que este

Usalo ANTES de escribir una regla, para saber si la carta que vas a arreglar esta en un
mazo que conviene subir. Y recalculalo despues de cada cambio de motor: las
sensibilidades se mueven.

    python3 src/sensibilidad.py            # +2 puntos, ng=2000
    python3 src/sensibilidad.py 3 1200     # +3 puntos, ng=1200
"""
import sys, math, statistics
sys.path.insert(0, 'src'); sys.path.insert(0, 'data')
from obj_real import medir, objetivo
from real_wr import REAL_FIELD


def objetivo_con(d, fmt, campo):
    """Recalcula el objetivo sustituyendo el campo de un formato."""
    o = dict(d[fmt]); o['field'] = campo
    real = REAL_FIELD.get(fmt, {})
    idx = {n: i for i, n in enumerate(o['names'])}
    pares = [(campo[idx[n]], real[n]) for n in real if n in idx]
    if len(pares) > 2:
        em = [a for a, _ in pares]; rm = [b for _, b in pares]
        sx = statistics.pstdev(em); sy = statistics.pstdev(rm)
        mx = statistics.mean(em); my = statistics.mean(rm)
        cov = sum((a - mx) * (b - my) for a, b in pares) / len(pares)
        o['r'] = cov / (sx * sy) if sx * sy > 0 else 0.0
        o['sd_real'] = sy; o['sd_motor'] = sx
        o['resid_cal'] = sy * math.sqrt(max(0.0, 2 * (1 - o['r'])))
    errs = [a - b for a, b in pares]
    off = statistics.mean(errs) if errs else 0.0
    o['resid'] = math.sqrt(sum((e - off) ** 2 for e in errs) / len(errs)) if errs else 0.0
    d2 = dict(d); d2[fmt] = o
    return objetivo(d2)


if __name__ == '__main__':
    delta = float(sys.argv[1]) / 100 if len(sys.argv) > 1 else 0.02
    ng = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
    d = medir(ng)
    base = objetivo(d) * 100
    print(f"objetivo base {base:.3f}   (perturbacion suma-cero de {delta*100:+.0f} puntos, ng={ng})\n")
    print(f"{'formato/arquetipo':<34}{'motor':>8}{'real':>8}{'dOBJ':>9}   direccion")
    filas = []
    for fmt in ('standard', 'pauper', 'brawl'):
        o = d.get(fmt)
        if not o or 'names' not in o: continue
        real = REAL_FIELD.get(fmt, {})
        n = len(o['names'])
        if n < 2: continue
        for i, nom in enumerate(o['names']):
            campo = list(o['field'])
            campo[i] += delta
            for j in range(n):
                if j != i: campo[j] -= delta / (n - 1)
            try: nuevo = objetivo_con(d, fmt, campo) * 100
            except (ValueError, ZeroDivisionError): continue
            filas.append((nuevo - base, fmt, nom, o['field'][i] * 100,
                          real.get(nom, float('nan')) * 100))
    for dobj, fmt, nom, m, r in sorted(filas):
        rs = f"{r:.1f}%" if r == r else "  --"
        flecha = 'SUBIRLO PAGA' if dobj < -0.02 else ('subirlo empeora' if dobj > 0.02 else 'indiferente')
        print(f"  {fmt[:3]}/{nom[:28]:<30}{m:>7.1f}%{rs:>8}{dobj:>+9.3f}   {flecha}")
    print(f"\nRuido del objetivo: +-0,02. Lo que caiga dentro es indiferente y no vale la pena atacar.")
