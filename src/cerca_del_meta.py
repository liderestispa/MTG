# -*- coding: utf-8 -*-
"""¿Que tan cerca esta la coleccion de un mazo del metajuego, y que costaria completarlo?

La pregunta que esto contesta es distinta de la que contesta run_brawl. Aquel busca el
mejor mazo CON LO QUE HAY; este mira los mazos que la gente juega de verdad y calcula la
distancia. Son decisiones distintas: una no cuesta dinero y la otra si.

El resultado del 18-ago fue tajante y conviene tenerlo escrito: la coleccion de Ricardo
—371 cartas de El Senor de los Anillos y Avatar— comparte CERO cartas con cinco de los
seis mazos del banco de Brawl, y dos con el sexto. No es que el buscador sea raro al
proponer un homebrew: es que no hay ningun arquetipo establecido que armar con ese pool.
Avatar es reciente y de LOTR tiene pocas.

Y el hallazgo que nadie esperaba: el mejor mazo del campo es tambien el mas barato, y son
literalmente DOS nombres de carta.

    python3 src/cerca_del_meta.py
"""
import sys, io, json
sys.path.insert(0, 'src'); sys.path.insert(0, 'data')
from driver import lookup, norm
from brawl import build_brawl, my_pool
from compras_brawl import precio
import meta_decks as MD


def main():
    R, opps = build_brawl()
    tengo = {norm(p['name']) for p in my_pool(R)}

    filas = []
    for tup in MD.BRAWL:
        nombre = tup[0]
        cartas = MD.parse(tup[-1])
        total = sum(n for n, _ in cartas)
        falta_n = 0; coste = 0.0; sin_precio = 0; caras = []
        for n, nm in cartas:
            if norm(nm) in tengo:
                continue
            c = lookup(nm)
            p = precio(c) if c else None
            falta_n += n
            if p is None: sin_precio += n
            else:
                coste += p * n
                if p > 1: caras.append((p * n, n, nm))
        caras.sort(reverse=True)
        filas.append(dict(mazo=nombre, tienes=total - falta_n, total=total,
                          faltan=falta_n, usd=round(coste, 2), sin_precio=sin_precio,
                          caras=[(round(t, 2), n, nm) for t, n, nm in caras[:6]]))

    filas.sort(key=lambda r: r['usd'])
    print("DISTANCIA A CADA MAZO DEL METAJUEGO\n")
    print(f"{'mazo':<32}{'tienes':>8}{'faltan':>8}{'USD':>9}")
    for r in filas:
        extra = f"  (+{r['sin_precio']} sin precio)" if r['sin_precio'] else ""
        print(f"{r['mazo'][:30]:<32}{r['tienes']:>4}/{r['total']:<3}{r['faltan']:>8}"
              f"{r['usd']:>9.0f}{extra}")

    print("\nDONDE ESTA EL DINERO, mazo por mazo:")
    for r in filas:
        if not r['caras']: continue
        print(f"\n  {r['mazo']}")
        for t, n, nm in r['caras']:
            print(f"     {t:7.2f}   {n}x {nm}")

    json.dump(filas, io.open('out/cerca_del_meta.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print("\nescrito out/cerca_del_meta.json")


if __name__ == '__main__':
    main()
