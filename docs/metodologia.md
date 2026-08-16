# Metodología de simulación y búsqueda

## 1. Common Random Numbers (obligatorio)

Con winrates cerca del 40-50%, el intervalo de confianza al 95% con 100 partidas es de ±10
puntos. Cualquier "mejora" menor a eso es ruido.

La solución no es solo subir la muestra: es **fijar las semillas** de forma que todas las
variantes enfrenten exactamente las mismas manos barajadas y los mismos mazos rivales. Así la
diferencia entre dos listas deja de contaminarse con la varianza de las manos.

```c
seed(SEED + oponente*1000003ULL + partida*7919ULL);
```

La misma partida `g` contra el mismo rival `o` produce el mismo barajado para toda variante.

Consecuencia práctica: **las semillas de búsqueda y las de validación deben ser distintas.**
Optimizar y validar con la misma semilla mide qué tan bien te ajustaste a esa semilla.

## 2. El sesgo del motor: medirlo, no ignorarlo

Todo motor hecho a mano tiene error de modelo. El que aparece una y otra vez: **sobrevalorar
mazos de criaturas frente a mazos de hechizos**, porque el combate es fácil de modelar y la
ventaja de cartas acumulada no.

**Prueba de cordura obligatoria:** haz que cada mazo del meta juegue contra el meta completo
(ponderado). Como cada uno juega contra el campo del que forma parte:

- El **promedio ponderado debe dar ~50%**. Si no, hay un bug de simetría.
- El **reparto** te dice el sesgo. Si los mazos de criaturas dan 85% y los de control 25%,
  el motor no puede predecir winrates absolutos contra ese campo.

Qué hacer con eso: el sesgo es **común** a todas las variantes de un mismo arquetipo enfrentando
el mismo campo, así que **se cancela al comparar listas entre sí**. Sirve para optimizar. No
sirve para prometer un winrate.

Fuente típica del sesgo: cartas que el motor no entiende quedan como **cartas en blanco**.
Mide el porcentaje. Por encima del 10% en un arquetipo, ese arquetipo está mal representado.

## 3. Métricas confiables

Estas dependen solo del barajado, la base de maná y la curva — no del modelo de combate:

| Métrica | Qué mide | Bueno |
|---|---|---|
| Turnos sin jugada (T1-4) | Cuánto tiempo muerto tienes al principio | < 1,3 |
| Turno de primera jugada | Cuándo empiezas a hacer algo | ≤ 2,2 |
| % screw de color | Manos con cartas jugables que no puedes pagar | < 25% |
| Hechizos lanzados T1-6 | Velocidad de despliegue real | > 4 |

Un mazo con winrate de motor alto pero 2,5 turnos muertos y primera jugada en el turno 3,5
**es un mal mazo**, aunque el simulador diga lo contrario.

## 4. Objetivo compuesto

```
objetivo = winrate − 0.030 · turnos_sin_jugada(T1-4) − 0.020 · max(0, primera_jugada − 2)
```

Los pesos están calibrados para que la penalización máxima ronde los 12 puntos: suficiente
para forzar disciplina de curva, insuficiente para dominar la señal de winrate.

Si el usuario pide explícitamente "que el mazo esté balanceado" o "que no tenga turnos muertos",
sube el primer coeficiente.

## 5. Beam search, no hill climbing

El hill climbing de un swap por vez se estanca en el primer óptimo local. Beam search mantiene
las K mejores listas parciales y explora desde todas.

```
B = [semilla]
por cada ronda:
    candidatos = union de vecinos(c) para c en B        # swaps de 1 y 2 cartas
    criba: evaluar TODOS a ~100 partidas                # barato
    profundo: re-evaluar los mejores 40 a ~600 partidas # caro pero pocos
    B = mejores K, deduplicados por contenido
```

El **racing** (criba barata → evaluación profunda de supervivientes) multiplica por ~6 la
cantidad de candidatos que puedes permitirte con el mismo presupuesto de cómputo.

Parámetros que funcionan: K=10, 240 candidatos por miembro del beam, 12 rondas.

### Sobre "probar todas las combinaciones"

No es alcanzable y conviene decirlo. Elegir 36 cartas entre ~190 distintas con hasta 4 copias
da del orden de 10¹⁶ listas. Lo que sí se puede es búsqueda dirigida y profunda con el criterio
del jugador incorporado como métrica explícita.

## 6. Semilla con curva

Si la semilla del beam se arma por "mejor puntuación heurística", y la puntuación es
`valor − cmc`, se llenará de bombas caras: una criatura 10/7 por 7 maná puntúa muy por encima
de un 2/2 por 2. El resultado es un mazo que no juega nada hasta el turno 4.

Arma la semilla por **franjas de coste** con una curva objetivo:

```python
CURVE = {1:0.10, 2:0.28, 3:0.26, 4:0.18, 5:0.10, 6:0.05, 7:0.03}
```

Esto cambia el resultado del barrido de colores de forma material, no cosmética.

## 7. Validación

- Semillas **nuevas**, no usadas en la búsqueda.
- Muestra grande: 3.000+ partidas por emparejamiento.
- Reporta el intervalo de confianza: `1.96·√(p(1−p)/n)`.
- Compara contra la **semilla greedy**, no contra cero: la pregunta es "¿la búsqueda aportó algo
  sobre construir por sentido común?".
- Si la mejora no supera el intervalo de confianza, dilo. Es un resultado válido y honesto.
