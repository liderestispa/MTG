# Transcript de continuación — proyecto MTG

Pega esto como primer mensaje en Claude Code, o deja que lea `CLAUDE.md`, que trae lo mismo
en formato de contexto permanente. **Lee `CLAUDE.md` antes de tocar nada.**

---

Estoy retomando un proyecto de optimización de mazos de Magic por simulación. Motor en C +
buscador en Python, calibrado contra winrates realmente publicados. Juego en papel, en tienda
local, y lo que corre mi tienda es **Standard Brawl**. Juego control de prisión: negarle el
juego al rival.

## Dónde quedó (18-ago-2026)

El 18 de agosto se hizo la auditoría que faltaba y cambió medio proyecto. Resumen:

**1. Ahora hay dos auditorías de cartas, no una.** `cobertura_texto.py` encuentra las que el
motor NO lee; `auditoria_lectura.py` las que lee MAL. Faltaba la segunda y era la peligrosa:
una carta muda te hace perder valor, una mal leída te hace **construir el mazo equivocado con
confianza**. `ficha_coleccion.py` une las dos y da el estado de las 204 cartas distintas de la
colección: **77 bien leídas, 61 a medias, 51 mudas, 15 mal leídas**.

**2. El caso que lo destapó.** Dáin, Lord of the Iron Hills, el comandante que el buscador
elegía para Brawl, dice que las criaturas no pueden **atacarte** salvo que paguen {1}, y solo
con *Storied*. El motor gravaba **lanzar hechizos**, sin condición. Quitando ese impuesto el
mazo caía de 51,0% a 34,2%: dos tercios de su nota eran un efecto que la carta no tiene.

**3. Cinco clases de mala lectura arregladas**, cada una con su ablación:
`ACTIVADAS_GRATIS=1` (41 cartas ejecutaban gratis habilidades con coste — Giant's Boulder era
un Vindicate de 1 maná), `MUERTE_OFF=1` (14 disparos de muerte puestos al entrar),
`MODAL_TODO=1` (13 modales disparaban todos los modos), `CONDICIONES_OFF=1` (Storied, Feroz,
Metalcraft), `ATAQUE_OFF=1` (ranura nueva de disparo al atacar).

**4. Y lo más importante: el objetivo dejó de ser buen árbitro.** Esos arreglos suben
`obj_real` de 0,608 a 0,955 y a la vez el residuo de Pauper baja de 8,11 a 5,51 puntos, el
desplazamiento se parte a la mitad y **Pauper pasa de perder contra el modelo tonto a ganarle**
(LOOCV 1,41% → 1,11% contra 1,25%). El objetivo mide **orden**, y en Pauper el orden real cabe
en 1,04 puntos con ±1,5 de error: no es recuperable ni en principio. Para juzgar lecturas de
cartas se usa `calib_real.py` (residuo y desplazamiento) y `loocv.py`. `obj_real.py` queda como
control de reproducibilidad y para cambios de política.

**5. Un `.exe` viejo escondió durante medio día la mejora más grande del proyecto.** `bin_brawl`
se genera de `sim.c` y no se estaba regenerando. Cuatro cambios midieron "cero" y eran falsos:
con el binario al día, `ATAQUE_LETAL` baja el objetivo de 1,072 a 0,609. Guarda puesta en
`src/salud.py`: `obj_real` **se niega a medir** con binarios viejos. **Compila siempre con
`bash scripts/build.sh`**, nunca gcc a mano.

**6. El entrenador se estaba mintiendo.** Reportaba +2,135 puntos de autojuego y eran
+1,251 ± 0,056: comparaba el **máximo** de ~1.000 evaluaciones contra **una** de referencia.
Arreglado — valida cada 20 generaciones en semillas limpias y emparejadas. Y el aprendizaje no
transfiere: el objetivo contra dato real da ruido en cada ciclo. `src/audita_politica.py` lo
re-mide cuando haga falta.

## Reglas de trabajo que ya costaron caro

1. **Compila con `bash scripts/build.sh`.** Los dos binarios o ninguno.
2. **Cuenta la materia antes de medir** (`chk_hallazgos.py`). Un cambio correcto sobre material
   que el banco no tiene mide cero, y ese cero se lee como "no sirve".
3. **Consulta `sensibilidad.py` ANTES de implementar**, no después. Dos veces se implementó un
   arreglo cuyo fracaso el análisis ya predecía.
4. **Dos preguntas distintas.** `sintetico.py` responde *¿funciona?*; `laboratorio.py` responde
   *¿conviene adoptarlo?*. Ninguno sustituye al otro.
5. **Un máximo sobre una serie ruidosa no es una medida.**
6. **Nunca reportes un winrate del motor como predicción.** En Brawl la escala se niega a
   calibrar: n=2 y los dos entre 73% y 77%.
7. **Revalida los mazos después de tocar el motor** (`impacto_mazos.py`, `revalidar.py`).
8. **Corre todo con `PYTHONUTF8=1`** — hay 45 `open()` sin encoding y los nombres con acento
   revientan.

## Lo que sigue pendiente

- **51 cartas mudas y 61 a medias** en la colección (`out/ficha_coleccion.md`). Las mudas están
  INFRAvaloradas, así que el buscador las descarta y pueden ser mejores de lo que cree.
- **Familias identificadas y sin escribir**: daño a criatura atacante/bloqueadora (Razor Rings,
  4 copias), daño repartido (Gandalf Spark Starter), Auras que traban una criatura (Enchanted
  River's Grasp, 4), disparo al atacar que tapea (Vengeful Villagers), y las caras de Aventura
  y MDFC, que el motor ignora por completo (14 copias, entre ellas Smaug).
- **Tierras que entran giradas**: implementado y APAGADO (`TIERRA_GIRADA=1`). El 52% de las
  tierras del banco de Standard entran giradas y el motor las mete destapadas. Correcto y
  mide peor también por residuo. Caso 11 de "más correcto y ajusta peor".
- **El banco de Standard es pre-ban** y n=4: no vale para juzgar nada.
- **Sneaky Snacker en `data/meta_decks.py`**: 4 Hadas {U}{B} en un mazo de 19 Montañas. Hace
  falta una fuente verificada de la lista real.
