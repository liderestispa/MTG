/* sim.c - motor de simulacion de Magic para optimizacion de mazos
 * Modela: mana con colores reales (screw incluido), curva, mulligan londres,
 * combate evaluado, remocion, ventaja de cartas, keywords de evasion.
 * Compilar: gcc -O3 -march=native -o sim sim.c -lm
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>   /* tanhf, para la politica aprendida (POLNET) */

#define MAXDEF   16384
#define DECKMAX  70
#define ZONEMAX  70
#define BFMAX    48

/* ---------- tipos ---------- */
enum { T_NONE=0, T_CREA=1, T_INST=2, T_SORC=3, T_ENCH=4, T_PW=5, T_LAND=6, T_ART=7, T_BATTLE=8 };
/* keywords */
enum { K_FLY=1u<<0, K_DT=1u<<1, K_LL=1u<<2, K_TRA=1u<<3, K_VIG=1u<<4, K_HAS=1u<<5,
       K_MEN=1u<<6, K_REA=1u<<7, K_FS=1u<<8, K_DS=1u<<9, K_DEF=1u<<10, K_FLASH=1u<<11,
       K_HEX=1u<<12, K_IND=1u<<13, K_WARD=1u<<14, K_PRO=1u<<15, K_PROW=1u<<16 };
/* efectos */
enum { E_NONE=0, E_ETB_DMG=1, E_ETB_DRAIN=2, E_ETB_DRAW=3, E_ETB_DISCARD=4, E_ETB_TOKEN=5,
       E_DESTROY=7, E_DMG_SPELL=8, E_SWEEPER=9, E_LORD=10, E_EQUIP=11, E_DRAW_ON_DMG=12,
       E_UPKEEP_DRAIN=13, E_RAMP=14, E_COUNTER=15, E_BURN_FACE=16, E_LIFEGAIN=17, E_PUMP=18,
       E_REANIMATE=19, E_ENGINE=20, E_EXILE=21, E_BOUNCE=22, E_FIGHT=23, E_ETB_COUNTERS=24,
       E_COND_BUFF=25, E_LOOT_TOKEN=26, E_AMASS=27, E_TREASURE=28, E_SAGA=29, E_PW_TICK=30,
       E_SPELL_DMG=31, E_PROWESS_ENG=32, E_TOKEN_SCALE=33, E_TOKEN_DOUBLE=34, E_EXILE_ENGINE=35,
       E_UPKEEP_DRAW=36, E_REPEAT_PUMP=37, E_TEAM_PUMP=38, E_FOG_BOUNCE=39,
       E_MOBILIZE=40, E_MASS_CHEAT=41, E_DEATH_DMG=42, E_ATTACK_DRAW=43,
       E_RECURSIVE=44, E_TEAM_MANA=45, E_ATTACK_DMG=46, E_PROTECT=47,
       E_DMG_ANY=48, E_EDICT=49, E_TAPDOWN=50, E_TAX=51,
       E_LAND_KILL=52, E_MASS_BOUNCE=53,
       /* al entrar produce mana que dura solo este turno (Burning-Tree Emissary).
          No es un Tesoro: si sobra, se pierde al acabar el turno. */
       E_ETB_MANA=54 };

typedef struct {
  int16_t cmc, power, tough;
  uint8_t typ, colors, produces, gen, hybrid, mana_out, dyn, no_untap;
  uint8_t alt, altn;   /* coste alternativo: 1=sacrificar altn tierras, 2=pagar altn vidas */
  uint8_t die_eff;     /* disparo AL IR AL CEMENTERIO: efecto y parametro */
  int16_t die_p1;
  uint8_t act_eff, act_cost;  /* habilidad ACTIVADA: efecto y coste (1=sacrificar un
                                 artefacto). La decision de activarla es del jugador. */
  int16_t act_p1;
  /* CONDICION que exige un efecto estatico antes de aplicarse. Sin esto, E_COND_BUFF
     —que se llama condicional— y E_TAX se sumaban SIEMPRE. src/auditoria_lectura.py
     encontro 12 cartas asi, entre ellas el comandante que el buscador elegia para
     Brawl. 1=Storied (3+ artefactos/legendarias/Sagas tuyos, y una vez logrado NO se
     pierde), 2=Feroz (controlas una criatura de fuerza 4+), 3=Metalcraft (3+ artefactos). */
  uint8_t cond;
  uint8_t es_leg;      /* legendaria (bit 0) o Saga (bit 1): las cuenta Storied */
  uint8_t tax_atk;     /* el impuesto grava ATACAR y no LANZAR (Dain, Ghostly Prison) */
  uint8_t atk_eff;     /* DISPARO AL ATACAR, con su condicion en cond. Existian
                          E_ATTACK_DMG y E_ATTACK_DRAW y nada mas, asi que "al atacar
                          gana 2 vidas", "al atacar pon un +1/+1" o "al atacar tapea una
                          criatura" no se leian, o peor: caian en una ranura de ENTRADA y
                          se disparaban al bajar la criatura. Misma solucion que la
                          ranura de cementerio: se reutiliza apply(). */
  int16_t atk_p1;
  uint8_t coste_extra; /* coste adicional obligatorio, cobrado en generico */
  uint8_t adv_eff, adv_gen, adv_pip[5];  /* AVENTURA: cara barata, su coste y su
                          efecto. Se lanza antes, la carta vuelve a la mano y la
                          criatura se lanza despues. Ablacion: AVENTURA_OFF=1. */
  int16_t adv_p1;
  uint32_t sub;        /* subtipos de criatura, mascara */
  uint32_t lord_sub;   /* si el lord solo sube a una tribu, cual */
  uint32_t cond_sub;   /* tribu que exige cond=4 */
  uint8_t entra_girada;/* "This land enters tapped". El motor las metia TODAS destapadas,
                          y en el banco de Standard eso es el 52% de las tierras: medio
                          turno de ventaja regalado a cada mazo, en todos los mazos. */
  uint8_t cred;        /* COSTE QUE BAJA SEGUN EL TABLERO. 1 = {1} menos por cada
                          instantaneo/conjuro en tu cementerio (Eddymurk Crab).
                          2 = {X} menos, X = el mayor coste convertido entre tus
                          criaturas (Sunderflock; ver la nota en pay_gen). */
  uint8_t pip[5];
  uint32_t kw;
  uint8_t eff, eff2, eff3;
  int16_t p1,p2,p3,q1,q2,r1,r2;
  int16_t score;
} Def;

static long long ST_games, ST_mull, ST_noplay[9], ST_play[9], ST_screw, ST_spells6, ST_firstplay, ST_turns;
static long long ST_cast, ST_counter_used, ST_counter_seen, ST_removal, ST_kills, ST_sweep,
                 ST_gamelen, ST_draw, ST_manaflood, ST_manascrew, ST_handend, ST_lifeend;

static long long ST_turns_dbg, ST_win_dmg, ST_lose_dmg, ST_timeout, ST_deck;
/* diagnostico de negacion: manos por turno y eficacia del descarte */
static long long ST_hA[16], ST_hB[16], ST_hn[16];
static long long ST_disc_try, ST_disc_hit, ST_disc_handsz;
static int PEN_NOTARGET=15, W_TARGET=50;
/* Bloqueo en grupo: implementado y correcto por reglas, pero DESACTIVADO por defecto.
   Con el activado el ajuste a los winrates reales empeora (residuo 4.0 -> 8.0):
   el reparto de dano y la IA de ataque no son lo bastante finos para aprovecharlo. */
static int GANG_BASE=10, GANG_ON=0;
/* el atacante cuenta cuantos bloqueadores quedan LIBRES, en vez de suponer que el
   defensor puede bloquear a todos a la vez. Ablacion: BLOQ_LIBRE=0. */
static int BLOQ_LIBRE=1;
/* APAGADO POR DEFECTO: NOTARGET_DURO=1 para activarlo.
   Por reglas (601.2c) un hechizo que exige objetivo no se puede lanzar sin objetivo
   legal, y el motor los lanzaba: PEN_NOTARGET=15 no alcanza la distancia al suelo
   CAST_FLOOR=-20, asi que una remocion que puntua 12-14 quedaba en -3 y pasaba. Medido
   por el agente: 2,85 cartas por partida tiradas al vacio en Four-Color vs Mardu.

   Impedirlo empeora muchisimo, y en los TRES formatos:
       apagado (motor de hoy)                    1,270
       bloqueando solo sin objetivo legal        2,808
       bloqueando tambien lo que no mata         2,813
   La distincion entre "no hay objetivo" y "hay pero no muere" resulto indiferente: el
   danio viene de impedir el lanzamiento, no de cual se impide. El residuo de Brawl pasa
   de 2,06 a 5,24.

   Sin explicacion comprobada todavia. La sospecha es que el motor no sabe descartar ni
   reordenar la mano, asi que la remocion retenida se queda ocupando sitio y desplaza
   decisiones que si valian; pero es hipotesis, no medicion. */
static int NOTARGET_DURO=0;
/* APAGADO POR DEFECTO: FICHAS_REALES=1 para activarlo.
   Las fichas como criaturas de verdad es lo CORRECTO segun las reglas, y aun asi hunde
   el ajuste. Medido, y no es interaccion con BLOQ_LIBRE, es por si mismo:

       FICHAS_REALES=0 BLOQ_LIBRE=0   1,332
       FICHAS_REALES=0 BLOQ_LIBRE=1   1,270   <- el motor de hoy
       FICHAS_REALES=1 BLOQ_LIBRE=0   2,274
       FICHAS_REALES=1 BLOQ_LIBRE=1   2,354

   La codificacion NO es el problema: se comprobo que las fichas salen con la
   fuerza/resistencia correcta (1/1 -> 17, 2/2 -> 34). El problema es que meter dos
   cuerpos mas por partida en los mazos de fichas mueve ncreat(), y de ahi cuelgan el
   umbral de los barredores, la eleccion de objetivos de la remocion y la logica de
   carrera. Todo eso se calibro con las fichas inertes.

   HIPOTESIS DEL RE-TUNEO: REFUTADA. Descenso completo con las fichas encendidas recupera
   2,354 -> 2,230, o sea el 11% de lo que cuesta. El danio no esta en los diez umbrales.

   LO QUE SI SE AVERIGUO, y cambia como hay que leer todo esto. Desglose por arquetipo al
   encender las fichas:

       Mono Red Rally     32,6% -> 46,9%   real 46,4%   QUEDA CLAVADO
       Four-Color Control 51,4% -> 58,0%   real 53,0%   se pasa
       Jund Wildfire      47,6% -> 38,1%   real 49,7%   se hunde

   Rally era el peor arquetipo del banco toda la sesion (-13,8) y este arreglo lo resuelve
   solo. Y Jund no se rompe: se DESTAPA. Sus unicas fichas son 4 Writhing Chrysalis, que
   con el bug clonaban la carta y le regalaban ocho cuerpos 2/3 con alcance inexistentes.
   Su 47,6% se sostenia sobre eso. Al modelarlas bien aparece un hueco de -11,6 que
   llevaba ahi desde el principio, tapado.

   Se anadio tambien que las fichas que se sacrifican por mana (Eldrazi Spawn/Scion) ramp
   de verdad, que antes eran 0/1 vainilla: 2,354 -> 2,266.

   Sigue apagado porque el objetivo empeora, que es la regla. Pero NO es un cambio malo:
   es un cambio que descubre otro hueco. El desbloqueo es averiguar que hace Jund Wildfire
   que el motor no ve, no seguir tocando las fichas. */
static int FICHAS_REALES=0;
/* disparos al ir al cementerio. Ablacion: MUERTE_ON=0. */
static int MUERTE_ON=1;
/* habilidades activadas, evaluadas con su coste. Ablacion: ACTIVADAS_ON=0. */
static int ACTIVADAS_ON=1;

/* ---- los tres hallazgos que quedaban de data/errores_juego.md ----
   Los tres son INFORMACION QUE LE FALTA AL MOTOR PARA DECIDIR, no restricciones
   nuevas sobre lo que puede hacer. Esa distincion es la teoria corregida despues de
   que ocho cambios "mas correctos segun las reglas" empeoraran el ajuste: lo que paga
   es darle al motor un dato que no tenia; lo que falla es quitarle o imponerle una
   decision.

   RESULTADO. Medidos de uno en uno contra dato real, base 1,072:

       ATAQUE_LETAL   0,609   -0,463   ADOPTADO. 23 veces el ruido de semilla.
       REMATE_LETAL   1,073   +0,001   neutro, se deja por ser mas correcto
       LORD_VE        1,072   +0,000   neutro, se deja por ser mas correcto
       KW_ATAQUE      1,204   +0,132   APAGADO: empeora

   ADVERTENCIA sobre como se llego a esa tabla, porque la primera version era FALSA.
   Los cuatro midieron cero clavado al principio, y el motivo era que bin_brawl estaba
   VIEJO: se genera de sim.c con src/gen_brawl.py, asi que un cambio aqui no le llega
   hasta que se regenera, y nada avisaba. El residuo de Brawl estaba congelado en 2,06 y
   como estos cambios actuan casi solo ahi, ninguno se veia. Con el binario al dia el
   residuo cae a 0,04. Guarda puesta en src/salud.py: obj_real ahora se NIEGA a medir con
   un binario mas viejo que sim.c.

   ATAQUE_LETAL merece una lectura honesta: toda su ganancia esta en Brawl, cuyo dato
   real son DOS winrates de ladder. Standard y Pauper no se mueven. Con n=2 no se puede
   separar "el motor mejoro" de "el motor ahora acierta dos numeros". Lo que si es
   independiente del ajuste: los dos mazos de Brawl marcaban 62% de motor contra 75%
   real —partidas demasiado lentas— y esto es justo lo que hace que un mazo cierre las
   que ya iba ganando. Verificado ademas en sintetico: 57,5% -> 99,3%.

   KW_ATAQUE es el noveno cambio "mas correcto segun las reglas" que ajusta peor, y esta
   vez estaba avisado: src/sensibilidad.py dice que subir a Ketramose cuesta +0,449, y
   Ketramose es indestructible Y tiene amenaza, o sea que la bandera lo habilita por
   partida doble. CONSULTA sensibilidad.py ANTES de implementar, no despues.

   Lo que NO queda probado es la teoria de leer-vs-jugar. Los tres hallazgos eran
   "informacion que falta para decidir" y uno gano fuerte, otro perdio y dos no hicieron
   nada. Ademas el banco casi no tiene materia para dos: src/chk_hallazgos.py cuenta 8
   criaturas con amenaza, 1 con dano primero, 1 indestructible y 4 copias de un solo lord
   en los 19 mazos.

   Ablacion: poner la variable a 0.

   REMATE_LETAL=1  E_DMG_ANY tenia +60 cuando el hechizo mata al rival; E_BURN_FACE y
                   E_ETB_DRAIN no tenian nada, asi que un remate que gana la partida
                   competia con una criatura por su puntuacion normal y solia perder.
                   Sintetico del detector: el mismo hechizo etiquetado BURN_FACE gana
                   en 2,94 turnos y etiquetado DMG_ANY en 2,07.
   ATAQUE_LETAL=1  la decision de atacar mira criatura a criatura (opp->life <= P_*2).
                   Cinco criaturas de poder 2 contra un rival a 9 vidas es letal y
                   ninguna de las cinco lo ve. En el lado del bloqueo la agregada si
                   existe (lethal_now).
   KW_ATAQUE=1     amenaza, dano primero e indestructible son invisibles al declarar
                   ataques. Medido por el detector: las tres no cambian NI UNA partida.
                   Con GANG_ON=0 una criatura con amenaza es literalmente imbloqueable
                   en este motor (el bloqueo simple exige minb==1) y aun asi se queda
                   en casa.
   LORD_VE=1       pw()/th() devuelven el cuerpo base; lordbonus() solo se llamaba
                   dentro de combat(). Todo lo que decide fuera del combate ve las
                   criaturas mas chicas de lo que son: 1 de dano "mata" a un 1/1 que
                   con su lord es un 3/3. Sintetico: 5,24 muertes por partida que
                   deberian ser cero. */
static int REMATE_LETAL=1;
static int ATAQUE_LETAL=1;
static int KW_ATAQUE=0;    /* APAGADO: ver la tabla de abajo, empeora +0,132 */
static int LORD_VE=1;
/* Umbrales de la politica de bloqueo, ajustados por descenso coordenada-a-coordenada
   contra la calibracion del meta (11.07 -> 10.35). No son "juego optimo": son los
   valores que reproducen mejor los resultados reales. */
static int TH_BLOCK=0, TH_TRADE=-4, TH_PERFECT=24, TH_WALL=0, TH_BADBLOCK=-14;
static int RESERVE_MAX=1, SWEEP_MIN=2, CAST_FLOOR=-20;
/* HALLAZGO C4-2: la remocion valia lo mismo matando un 1/1 que un 7/7, y el motor
   no miraba cuanto dano tenia enfrente. Un mazo de control a 9 vidas contra 7 de
   poder seguia lanzando cantrips. W_PRESSURE premia quitar dano cuando queda poco
   tiempo de vida; W_TARGET premia matar lo gordo. */
static int W_PRESSURE=70;   /* ajustado contra winrates reales publicados (6.58 -> 6.49) */
static int DISABLE_EFF=-1;
static int DMG_ANY_FACE=0;
static int NEG_ON=1;   /* bloque de negacion: edicto, inmovilizar, impuesto, tierras, rebote */
static int TRACE=0;      /* 1 = imprime la primera partida turno a turno */
static int TRACE_ON=0;
static int TJ=0, TJ_ON=0; /* TRACE_JSON=N: traza las N primeras partidas, para src/tablero.py */
static int TJ_TURN=0; static long long TJ_GAME=0;
/* eventos dentro del turno: sin esto el tablero solo muestra fotos de fin de turno y las
   partidas parecen vacias, porque lo que entra y muere en el mismo turno no se ve nunca. */
static void tj_ev(const char*ev, void*jug, int id);
static void*PLAYER_A=0;

static void tj_ev(const char*ev, void*jug, int id){
  if(!TJ_ON) return;
  fprintf(stderr,"@J {\"t\":%d,\"ev\":\"%s\",\"p\":\"%s\",\"id\":%d}\n",
          TJ_TURN, ev, jug==PLAYER_A?"A":"B", id);
}
static Def D[MAXDEF];
static int NDEF = 0;

/* ---------- RNG determinista (xoshiro) ---------- */
static uint64_t rs[4];
static inline uint64_t rotl(uint64_t x,int k){return (x<<k)|(x>>(64-k));}
static inline uint64_t rnd(void){
  uint64_t r=rotl(rs[1]*5,7)*9,t=rs[1]<<17;
  rs[2]^=rs[0];rs[3]^=rs[1];rs[1]^=rs[2];rs[0]^=rs[3];rs[2]^=t;rs[3]=rotl(rs[3],45);
  return r;
}
static void seed(uint64_t s){ for(int i=0;i<4;i++){ s+=0x9E3779B97F4A7C15ULL;
  uint64_t z=s; z=(z^(z>>30))*0xBF58476D1CE4E5B9ULL; z=(z^(z>>27))*0x94D049BB133111EBULL;
  rs[i]=z^(z>>31);} for(int i=0;i<16;i++) rnd(); }
static inline int ri(int n){ return (int)(rnd()%(uint64_t)n); }

/* ---------- jugador ---------- */
typedef struct {
  int life;
  int deck[DECKMAX], nd;
  int hand[ZONEMAX], nh;
  int bf[BFMAX];   int nbf;
  uint8_t tap[BFMAX], sick[BFMAX], frz[BFMAX];   /* frz = turnos que no se endereza */
  int taxed;                                     /* impuesto que le cobra el rival */
  int16_t ctr[BFMAX];     /* contadores +1/+1 */
  int16_t eqp[BFMAX];     /* bono de equipo acumulado (p<<8|t) */
  int lands[BFMAX], nl;   /* indices de def de tierras en juego */
  uint8_t ltap[BFMAX];
  int army;               /* indice bf del Army de amass, -1 */
  int treasures;
  int flot;               /* mana flotante de este turno (E_ETB_MANA); se pierde al acabar */
  int storied;            /* "enduring story": una vez conseguido, no se pierde */
  int tax_atk;            /* {N} que hay que pagar POR CRIATURA para atacarme */
  int gy_is;              /* instantaneos y conjuros que han ido al cementerio.
                             El motor NO tiene cementerio: un hechizo lanzado se resuelve
                             y desaparece. Esto es lo minimo que hace falta para los
                             costes que bajan con el cementerio, y de paso sirve para
                             umbral, delirio y cuentas de hechizos. */
  uint8_t hand_adv[ZONEMAX];   /* aventura ya usada en ESA copia de la mano */
  int played_land;
  int cards_drawn_turn;
  int lost;
} P;

/* ---------- POLNET: politica de lanzamiento aprendida por autojuego ----------
   Una MLP diminuta (NIN -> NH -> 1, tanh) que CORRIGE la puntuacion heuristica en vez
   de reemplazarla: v_final = v_heuristico + PN_ESCALA * red(rasgos). Con los pesos a
   cero el motor se comporta exactamente igual que sin ella, asi que el entrenamiento
   arranca desde el motor actual y solo puede mejorar desde ahi.

   Los pesos se cargan de un archivo de texto (POLNET=ruta). Sin archivo, PN_ON=0 y no
   se ejecuta ni una multiplicacion. El entrenador es src/entrenar_politica.py.

   Va en C y no en Python porque el entrenamiento es evolutivo: solo necesita la pasada
   hacia delante y el resultado de la partida, que es justo lo que esta maquina hace a
   70.000 partidas por segundo. */
#define PN_NIN 17
#define PN_NH  12
static int   PN_ON = 0;
/* PN_LADO=0 (por defecto): la red pilota SOLO al jugador A y el rival sigue con la
   heuristica. Es lo que hace falta para entrenar: si pilotara a los dos, el round-robin
   no se moveria y no habria senal que medir. PN_LADO=1 la pone en ambos lados, que es
   como se despliega una vez adoptada. */
static int   PN_LADO = 0;
static float PN_ESCALA = 6.0f;
static float PN_W1[PN_NH][PN_NIN], PN_B1[PN_NH], PN_W2[PN_NH], PN_B2;
static int   turno_actual = 0;

static void pn_cargar(const char*ruta){
  FILE*f = fopen(ruta, "r");
  if(!f) return;
  int nin=0, nh=0;
  if(fscanf(f, "POLNET %d %d", &nin, &nh) != 2 || nin != PN_NIN || nh != PN_NH){
    fprintf(stderr, "POLNET: cabecera incompatible (%d,%d), esperaba (%d,%d)\n",
            nin, nh, PN_NIN, PN_NH);
    fclose(f); return;
  }
  for(int j=0;j<PN_NH;j++) for(int i=0;i<PN_NIN;i++)
    if(fscanf(f,"%f",&PN_W1[j][i])!=1){ fclose(f); return; }
  for(int j=0;j<PN_NH;j++) if(fscanf(f,"%f",&PN_B1[j])!=1){ fclose(f); return; }
  for(int j=0;j<PN_NH;j++) if(fscanf(f,"%f",&PN_W2[j])!=1){ fclose(f); return; }
  if(fscanf(f,"%f",&PN_B2)!=1){ fclose(f); return; }
  fclose(f); PN_ON = 1;
}

static int ncreat(P*p);              /* definidas mas abajo */
static int untapped_count(P*p);
static inline int pw(P*p,int i);
/* poder total en mesa: no existia como helper, solo maxpower y board_pressure */
static int board_power(P*p){
  int s=0; for(int i=0;i<p->nbf;i++) if(D[p->bf[i]].typ==T_CREA) s+=pw(p,i);
  return s;
}

static float pn_correccion(Def*d, P*me, P*opp, int turno){
  float x[PN_NIN];
  int e = d->eff, e2 = d->eff2;
  int rem = (e==E_DESTROY||e==E_EXILE||e==E_DMG_SPELL||e==E_DMG_ANY||e==E_EDICT);
  int rob = (e==E_ETB_DRAW||e==E_ENGINE||e2==E_ETB_DRAW||e==E_UPKEEP_DRAW||e2==E_UPKEEP_DRAW);
  int que = (e==E_BURN_FACE||e==E_DMG_ANY||e==E_ETB_DRAIN||e2==E_ETB_DRAIN);
  x[0]  = d->cmc / 6.0f;
  x[1]  = d->typ==T_CREA;
  x[2]  = d->power / 6.0f;
  x[3]  = d->tough / 6.0f;
  x[4]  = (d->typ==T_INST || d->typ==T_SORC);
  x[5]  = rem; x[6] = rob; x[7] = que;
  x[8]  = me->life  / 20.0f;
  x[9]  = opp->life / 20.0f;
  x[10] = ncreat(me)  / 5.0f;
  x[11] = ncreat(opp) / 5.0f;
  x[12] = board_power(me)  / 10.0f;
  x[13] = board_power(opp) / 10.0f;
  x[14] = turno / 12.0f;
  x[15] = me->nh / 7.0f;
  x[16] = untapped_count(me) / 6.0f;
  float s = PN_B2;
  for(int j=0;j<PN_NH;j++){
    float h = PN_B1[j];
    for(int i=0;i<PN_NIN;i++) h += PN_W1[j][i]*x[i];
    h = tanhf(h);
    s += PN_W2[j]*h;
  }
  return PN_ESCALA * tanhf(s);
}

static int ncreat_fwd(P*p);
static inline int dynbase(P*p,int i){
  Def*d=&D[p->bf[i]];
  if(!d->dyn) return -1;
  if(d->dyn==1) return p->nl;                 /* = numero de tierras */
  if(d->dyn==2) return ncreat_fwd(p);         /* = numero de criaturas */
  return 4;
}
static inline int pw(P*p,int i){ int b=dynbase(p,i);
  return (b>=0?b:D[p->bf[i]].power) + p->ctr[i] + (p->eqp[i]>>8); }
static inline int th(P*p,int i){ int b=dynbase(p,i);
  return (b>=0?b:D[p->bf[i]].tough) + p->ctr[i] + (p->eqp[i]&0xFF); }

/* ---- condiciones de los efectos estaticos ----
   E_COND_BUFF se llamaba condicional y se sumaba siempre; E_TAX igual. Doce cartas del
   banco y de la coleccion regalaban su bono, entre ellas Dain, el comandante que el
   buscador elegia para Brawl. Ablacion: CONDICIONES_OFF=1. */
static int CONDICIONES_ON = 1;
/* Tierras que entran giradas. APAGADO POR DEFECTO: TIERRA_GIRADA=1 para activarlo.
   Es correcto sin discusion —el 52% de las tierras del banco de Standard entran
   giradas y el motor las metia todas destapadas, o sea medio turno regalado— y aun asi
   mide PEOR por los dos criterios, tambien por el residuo, que es el que se acaba de
   adoptar como arbitro:

       formato    residuo sin  ->  con      desplazamiento
       Standard      4,14         4,14        -1,3 -> -1,5
       Pauper        5,51         5,87        -1,2 -> -1,6

   O sea que no es un artefacto del ranking. La lectura probable es que el modelo de
   mana compensa por otro lado —no hay mulligan real, ni pantalla de colores, ni
   busqueda de tierras bien modelada— y quitarle el regalo lo deja demasiado lento.
   Es el caso 11 de "mas correcto y ajusta peor".

   OJO PARA CONSTRUIR MAZOS: 18 de las 26 tierras no basicas de la coleccion de Ricardo
   entran giradas. Con esto apagado, el buscador las trata como si fueran duales
   perfectas y las va a meter de mas. Si algun dia se arregla el modelo de mana, hay
   que volver a medir esto ANTES que nada. */
static int TIERRA_GIRADA = 0;

static int cumple_cond(P*p, Def*d){
  if(!CONDICIONES_ON || !d->cond) return 1;
  if(d->cond==1){                      /* Storied: 3+ artefactos/legendarias/Sagas */
    if(p->storied) return 1;           /* "enduring": logrado una vez, ya no se pierde */
    int n=0;
    for(int i=0;i<p->nbf;i++){ Def*x=&D[p->bf[i]];
      if(x->typ==T_ART || x->es_leg) n++; }
    for(int i=0;i<p->nl;i++) if(D[p->lands[i]].es_leg) n++;
    if(n>=3){ p->storied=1; return 1; }
    return 0;
  }
  if(d->cond==2){                      /* Feroz: controlas una criatura de fuerza 4+ */
    for(int i=0;i<p->nbf;i++)
      if(D[p->bf[i]].typ==T_CREA && D[p->bf[i]].power>=4) return 1;
    return 0;
  }
  if(d->cond==4){                      /* controlas OTRA criatura de esa tribu */
    for(int i=0;i<p->nbf;i++)
      if(D[p->bf[i]].typ==T_CREA && (D[p->bf[i]].sub & d->cond_sub)) return 1;
    return 0;
  }
  if(d->cond==3){                      /* Metalcraft: 3+ artefactos */
    int n=0; for(int i=0;i<p->nbf;i++) if(D[p->bf[i]].typ==T_ART) n++;
    return n>=3;
  }
  return 1;
}

/* lord estatico: suma bonos de todas las criaturas/artefactos con E_LORD */
/* Bonus para UNA criatura concreta: un lord tribal solo sube a los de su tribu, y hasta
   el 18-ago el motor no sabia distinguirlos porque no tenia subtipos. lord_sub=0 quiere
   decir "sube a todas", que es como se comportaba antes. */
static void lordbonus_de(P*p,int idx,int*bp,int*bt){
  *bp=0;*bt=0;
  uint32_t mia = (idx>=0 && idx<p->nbf) ? D[p->bf[idx]].sub : 0xFFFFFFFFu;
  for(int i=0;i<p->nbf;i++){ Def*d=&D[p->bf[i]];
    if(!cumple_cond(p,d)) continue;
    if(d->eff==E_LORD && (!d->lord_sub || (mia & d->lord_sub))){*bp+=d->p1;*bt+=d->p2;}
    if(d->eff2==E_LORD && (!d->lord_sub || (mia & d->lord_sub))){*bp+=d->q1;*bt+=d->q2;} }
}
/* Version global: solo los lords SIN restriccion. La usan los sitios que estiman el
   tablero entero de un vistazo y no pueden preguntar por una criatura concreta. */
static void lordbonus(P*p,int*bp,int*bt){
  *bp=0;*bt=0;
  for(int i=0;i<p->nbf;i++){ Def*d=&D[p->bf[i]];
    if(!cumple_cond(p,d) || d->lord_sub) continue;
    if(d->eff==E_LORD){*bp+=d->p1;*bt+=d->p2;}
    if(d->eff2==E_LORD){*bp+=d->q1;*bt+=d->q2;} }
}

/* poder/resistencia EFECTIVOS: el cuerpo mas el bono estatico de los lords.
   combat() ya llamaba a lordbonus(); best_killable, biggest_threat, board_pressure y
   E_SWEEPER no, asi que decidian sobre criaturas mas chicas de lo que estan en mesa.
   Con LORD_VE=0 se comportan como antes, para poder medir la diferencia. */
static inline int pw_eff(P*p,int i){
  if(!LORD_VE) return pw(p,i);
  int bp,bt; lordbonus_de(p,i,&bp,&bt); return pw(p,i)+bp;
}
static inline int th_eff(P*p,int i){
  if(!LORD_VE) return th(p,i);
  int bp,bt; lordbonus_de(p,i,&bp,&bt); return th(p,i)+bt;
}

/* ---------- mana: comprueba si se puede pagar coste con tierras destapadas ---------- */
/* asignacion por backtracking pequeno: pips de color primero (los mas restringidos) */
/* ---- costes que BAJAN con el tablero ----
   Distinto de un coste alternativo: aqui no se cambia la forma de pagar, se paga menos.
   Y no es un detalle de una carta: Izzet Spellementals lleva 4 Eddymurk Crab a 7 mana y
   4 Sunderflock a 9 en un mazo de cantrips de 1 y 2. Cobrandolos a precio de tapa, el
   motor NO LOS LANZA NUNCA, y por eso las dos reglas que les daban su efecto de entrada
   midieron +0,009 y +0,000: le estaban dando habilidades a cartas que no salen de la
   mano. Es el mismo error que cobrar Fireblast a 6.

   La reduccion solo toca la parte GENERICA del coste, que es como funciona de verdad:
   los pips de color hay que pagarlos igual.

   La ablacion es CRED_OFF=1 y va en el EXTRACTOR, no aqui: extract.py deja de etiquetar
   la carta y le devuelve la rebaja plana de cost_reduction(), que es el modelo anterior.
   Apagarlo solo en C dejaria las cartas a precio de tapa, que no es ninguno de los dos
   modelos y no serviria para comparar. */
static int mayor_cmc_criatura(P*p){
  int m=0; for(int i=0;i<p->nbf;i++)
    if(D[p->bf[i]].typ==T_CREA && D[p->bf[i]].cmc>m) m=D[p->bf[i]].cmc;
  return m;
}
static int reduccion(P*p,Def*d){
  if(!d->cred) return 0;
  if(d->cred==1) return p->gy_is;
  /* cred=2 es "el mayor coste convertido entre los Elementales que controlas". El motor
     no tiene subtipos, asi que se aproxima con TODAS tus criaturas. En Izzet
     Spellementals, el unico mazo del banco que lleva la carta, las criaturas son todas
     Elementales y la aproximacion es exacta. En un mazo mixto sobreestimaria. */
  if(d->cred==2) return mayor_cmc_criatura(p);
  return 0;
}
/* Cobrar el coste adicional obligatorio. APAGADO POR DEFECTO: COSTE_EXTRA_ON=1.
   Es correcto —Stir Up Trouble pide sacrificar un artefacto o criatura ADEMAS de su {B}
   y el motor tenia un Doom Blade de un mana— y rompe el ajuste justo donde mas duele:

       Pauper  residuo 5,51 -> 5,61   r=+0,68 -> +0,48
       LOOCV   Pauper pasa de GANARLE al modelo tonto (+0,14) a PERDER (-0,31)

   Es el caso 12 de mas-correcto-y-ajusta-peor, y el primero que tumba el unico
   resultado bueno que tiene el proyecto, asi que no se adopta. La lectura probable es
   la de siempre: encarecer la remocion frena a los mazos del banco y el motor ya iba
   lento. Volver a medirlo si algun dia se arregla el modelo de mana. */
static int COSTE_EXTRA_ON = 0;
static int pay_gen(P*p,Def*d){
  int g = d->gen + (p->taxed>0 && d->typ!=T_LAND ? p->taxed : 0);
  if(COSTE_EXTRA_ON) g += d->coste_extra;
  g -= reduccion(p,d);
  return g>0 ? g : 0;
}

/* ---- costes alternativos ("rather than pay this spell's mana cost") ----
   alt=1 sacrificar altn tierras (Fireblast), alt=2 pagar altn vidas (Snuff Out).
   Son hechizos que en la practica se juegan SIEMPRE por la via alternativa: cobrarlos
   a su coste nominal hacia que el motor no los lanzara nunca. La politica es
   conservadora: solo se recurre a la alternativa cuando el mana no alcanza, y nunca
   si la contrapartida deja al jugador sin tierras o al borde de morir. */
static P* ALT_OPP = 0;   /* rival del jugador que esta lanzando; lo fijan cast_phase y
                            defender_instants. Hace falta para saber si un remate mata. */
static int alt_ok(P*p,Def*d){
  if(!d->alt) return 0;
  if(d->alt==1){
    /* Sacrificar tierras es carisimo: dejarlo suelto hace que el motor se mutile la
       base de mana en el turno 3. Fireblast se juega para REMATAR, asi que solo se
       permite cuando el dano mata al rival. Medido: sin esta condicion 2.580 (peor
       que no tenerlo), con ella 2.4xx. */
    if(p->nl <= d->altn) return 0;              /* que sobreviva al menos una tierra */
    return ALT_OPP && ALT_OPP->life <= d->p1;
  }
  if(d->alt==2) return p->life > d->altn + 4;   /* no suicidarse por un hechizo */
  return 0;
}
static void alt_pay(P*p,Def*d){
  if(d->alt==1){
    for(int k=0;k<d->altn && p->nl>0;k++){      /* sacrifica las ya giradas primero */
      int q=-1;
      for(int i=p->nl-1;i>=0;i--) if(p->ltap[i]){ q=i; break; }
      if(q<0) q=p->nl-1;
      for(int i=q;i<p->nl-1;i++){ p->lands[i]=p->lands[i+1]; p->ltap[i]=p->ltap[i+1]; }
      p->nl--;
    }
  } else if(d->alt==2) p->life -= d->altn;
}

static int payable_mana(P*p,Def*d,int extra_any);
static int payable(P*p,Def*d,int extra_any){
  if(payable_mana(p,d,extra_any)) return 1;
  return alt_ok(p,d);
}
static int payable_mana(P*p,Def*d,int extra_any){
  uint8_t col[BFMAX]; uint8_t amt[BFMAX]; int na=0;
  for(int i=0;i<p->nl;i++) if(!p->ltap[i]){
    col[na]=D[p->lands[i]].produces;
    amt[na]=D[p->lands[i]].mana_out? D[p->lands[i]].mana_out : 1;
    na++;
  }
  for(int i=0;i<extra_any;i++){ col[na]=31; amt[na]=1; na++; }
  /* criaturas y artefactos que producen mana (Llanowar Elves, Priest of Titania...) */
  int team_mana=0;
  for(int i=0;i<p->nbf;i++) if(D[p->bf[i]].eff==E_TEAM_MANA) team_mana=1;
  for(int i=0;i<p->nbf;i++){ Def*dd=&D[p->bf[i]];
    int mo = dd->mana_out;
    if(team_mana && dd->typ==T_CREA && mo==0) mo=1;
    if(!mo || p->tap[i]) continue;
    if(dd->typ==T_CREA && p->sick[i]) continue;
    col[na]=dd->produces? dd->produces : 31;
    amt[na]=mo; na++; }
  int need[5]; int totmana=0;
  for(int i=0;i<na;i++) totmana+=amt[i];
  int gen_real = pay_gen(p,d);
  int tot=gen_real;
  for(int c=0;c<5;c++){ need[c]=d->pip[c]; tot+=need[c]; }
  if(tot>totmana) return 0;
  uint8_t used[BFMAX]; memset(used,0,na);
  int spent[BFMAX]; memset(spent,0,sizeof(int)*na);
  /* pips de color: la fuente mas restringida primero */
  for(int c=0;c<5;c++){
    for(int k=0;k<need[c];k++){
      int best=-1,bestn=99;
      for(int i=0;i<na;i++){ if(spent[i]>=amt[i]||!(col[i]&(1<<c))) continue;
        int n=__builtin_popcount(col[i]); if(n<bestn){bestn=n;best=i;} }
      if(best<0) return 0;
      spent[best]++;
    }
  }
  int libre=0; for(int i=0;i<na;i++) libre += amt[i]-spent[i];
  return libre>=gen_real;
}
static void paycost(P*p,Def*d,int*treas){
  /* si el mana no alcanza pero hay via alternativa, se paga por ahi */
  if(d->alt && !payable_mana(p,d,*treas) && alt_ok(p,d)){ alt_pay(p,d); return; }
  int idx[BFMAX]; int amt[BFMAX]; int spent[BFMAX]; int na=0;
  for(int i=0;i<p->nl;i++) if(!p->ltap[i]){
    idx[na]=i; amt[na]=D[p->lands[i]].mana_out? D[p->lands[i]].mana_out : 1; spent[na]=0; na++;
  }
  int need[5]; for(int c=0;c<5;c++) need[c]=d->pip[c];
  for(int c=0;c<5;c++) for(int k=0;k<need[c];k++){
    int best=-1,bestn=99;
    for(int i=0;i<na;i++){ if(spent[i]>=amt[i]) continue;
      uint8_t pr=D[p->lands[idx[i]]].produces;
      if(!(pr&(1<<c))) continue; int n=__builtin_popcount(pr); if(n<bestn){bestn=n;best=i;} }
    if(best>=0) spent[best]++;
    else if(*treas>0) (*treas)--;
  }
  int g=pay_gen(p,d);
  for(int i=0;i<na && g>0;i++) while(spent[i]<amt[i] && g>0){ spent[i]++; g--; }
  while(g>0 && *treas>0){ (*treas)--; g--; }
  for(int i=0;i<na;i++) if(spent[i]>0) p->ltap[idx[i]]=1;
}
static int untapped_count(P*p){ int n=0;
  for(int i=0;i<p->nl;i++) if(!p->ltap[i]) n += D[p->lands[i]].mana_out? D[p->lands[i]].mana_out : 1;
  for(int i=0;i<p->nbf;i++){ Def*dd=&D[p->bf[i]];
    if(dd->mana_out && !p->tap[i] && !(dd->typ==T_CREA && p->sick[i])) n += dd->mana_out; }
  return n+p->treasures; }

/* ---------- zonas ---------- */
/* Robo SELECTIVO: la mayoria del robo de control es "mira N, toma M".
   Modela que el jugador elige tierra si le faltan, y hechizo si va sobrado. */
static void draw_select(P*p,int n,int look){
  for(int k=0;k<n;k++){
    if(p->nd<=0){ p->lost=1; return; }
    int cand = look<p->nd ? look : p->nd;
    int need_land = (p->nl < 4);
    int best=-1;
    for(int i=0;i<cand;i++){
      int idx=p->nd-1-i; int isl = (D[p->deck[idx]].typ==T_LAND);
      if(best<0){ best=idx; continue; }
      int bl = (D[p->deck[best]].typ==T_LAND);
      if(need_land){ if(isl && !bl) best=idx; }
      else { if(!isl && bl) best=idx;
             else if(isl==bl && D[p->deck[idx]].score > D[p->deck[best]].score) best=idx; }
    }
    if(best<0) best=p->nd-1;
    p->hand_adv[p->nh]=0; p->hand[p->nh++]=p->deck[best];
    for(int i=best;i<p->nd-1;i++) p->deck[i]=p->deck[i+1];
    p->nd--;
    p->cards_drawn_turn++;
  }
}
static void draw(P*p,int n){
  for(int i=0;i<n;i++){
    if(p->nd<=0){ p->lost=1; return; }
    p->hand_adv[p->nh]=0; p->hand[p->nh++]=p->deck[--p->nd];
    p->cards_drawn_turn++;
  }
}
static void shuffle(P*p){ for(int i=p->nd-1;i>0;i--){ int j=ri(i+1); int t=p->deck[i];p->deck[i]=p->deck[j];p->deck[j]=t; } }

static void addbf(P*p,int def){
  tj_ev("entra", p, def);
  if(D[def].typ==T_LAND){ if(p->nl<BFMAX){ p->lands[p->nl]=def;
      p->ltap[p->nl]=(TIERRA_GIRADA && D[def].entra_girada)?1:0; p->nl++; } return; }
  if(p->nbf>=BFMAX) return;
  int i=p->nbf++;
  p->bf[i]=def; p->tap[i]=0; p->ctr[i]=0; p->eqp[i]=0;
  p->sick[i] = (D[def].typ==T_CREA && !(D[def].kw&K_HAS)) ? 1 : 0;
}
static P *OPP_OF_A=0, *OPP_OF_B=0;
static void apply(P*me,P*opp,int def,int which);
static void apply_die(P*me,P*opp,int def);
static void apply_atk(P*me,P*opp,int def);
static int CMD_OF(P*p);
static void rmbf(P*p,int i){
  tj_ev("sale", p, p->bf[i]);
  /* disparo al ir al cementerio (Ichor Wellspring, Nihil Spellbomb, Lembas). Antes no
     existia: el motor solo leia la mitad de entrada de esas cartas. */
  if(MUERTE_ON && D[p->bf[i]].die_eff){
    P*o = (p==OPP_OF_A)? OPP_OF_B : OPP_OF_A;
    apply_die(p, (o&&o!=p)?o:p, p->bf[i]);
  }
  { Def*dd=&D[p->bf[i]];
    if(dd->eff==E_DEATH_DMG || dd->eff2==E_DEATH_DMG){
      int amt = (dd->eff==E_DEATH_DMG)? dd->p1 : dd->q1;
      P*o = (p==OPP_OF_A)? OPP_OF_B : OPP_OF_A;
      if(o && o!=p) o->life -= amt;
    }
    /* la recursion cuesta recursos: solo vuelve una de cada tres veces */
    if(dd->eff==E_RECURSIVE && p->nh<ZONEMAX && (rnd()%3)==0) p->hand[p->nh++]=p->bf[i];
  }
  p->nbf--;
  for(int k=i;k<p->nbf;k++){ p->bf[k]=p->bf[k+1];p->tap[k]=p->tap[k+1];p->sick[k]=p->sick[k+1];
                             p->ctr[k]=p->ctr[k+1];p->eqp[k]=p->eqp[k+1]; }
  if(p->army==i) p->army=-1; else if(p->army>i) p->army--;
}
/* La mejor criatura que este dano SI puede matar. Un hechizo de 2 dano no debe
   apuntar al 5/5: apunta al mejor objetivo que realmente muere. */
/* HALLAZGO C4-1: antimaleficio y vigilia estaban parseados pero NUNCA se leian.
   Toda remocion dirigida mataba criaturas con antimaleficio. Los mazos de una sola
   amenaza grande (voltron/tempo) perdian por un bug, no por su plan. */
static int SPARE_MANA=0;
static int WARD_COST=3;
static int HEXWARD_ON=1;
static int targetable(P*p,int i){
  Def*d=&D[p->bf[i]];
  if(!HEXWARD_ON) return 1;
  if(d->kw&K_HEX) return 0;                                  /* no se puede apuntar */
  if((d->kw&K_WARD) && SPARE_MANA < WARD_COST) return 0;      /* no alcanza para pagar la vigilia */
  return 1;
}
static int best_killable(P*p,int dmg){
  int best=-1,bv=-1;
  for(int i=0;i<p->nbf;i++){ Def*d=&D[p->bf[i]];
    if(d->typ!=T_CREA) continue;
    if(d->kw&K_IND) continue;
    if(!targetable(p,i)) continue;
    int t=0; for(int q=0;q<p->nbf;q++) if(q==i) t=th(p,i);
    if(th_eff(p,i)>dmg) continue;
    int v=pw_eff(p,i)*2+th_eff(p,i);
    if(d->kw&K_FLY) v+=3; if(d->kw&K_DT) v+=3;
    if(d->eff==E_LORD||d->eff==E_ENGINE||d->eff==E_SPELL_DMG||d->eff==E_UPKEEP_DRAW) v+=8;
    if(v>bv){bv=v;best=i;} }
  return best;
}
/* El dueno responde a la remocion con un hechizo de proteccion si lo tiene y puede pagarlo. */
static int try_protect(P*owner){
  for(int i=0;i<owner->nh;i++){ Def*d=&D[owner->hand[i]];
    if(d->eff!=E_PROTECT) continue;
    if(!payable(owner,d,owner->treasures)) continue;
    for(int k=i;k<owner->nh-1;k++) owner->hand[k]=owner->hand[k+1];
    owner->nh--;
    paycost(owner,d,&owner->treasures);
    return 1;
  }
  return 0;
}
static int biggest_threat(P*p){
  int best=-1,bv=-1;
  for(int i=0;i<p->nbf;i++){ if(D[p->bf[i]].typ!=T_CREA) continue;
    if(!targetable(p,i)) continue;
    int v=pw_eff(p,i)*2+th_eff(p,i); if(D[p->bf[i]].kw&K_FLY) v+=3; if(D[p->bf[i]].kw&K_DT) v+=3;
    if(D[p->bf[i]].eff==E_LORD||D[p->bf[i]].eff==E_ENGINE) v+=6;
    if(v>bv){bv=v;best=i;} }
  return best;
}
/* dano por turno que me viene encima, descontando lo que pueden frenar mis bloqueadores */
static int board_pressure(P*me,P*opp){
  int dmg=0, blk=0;
  for(int i=0;i<opp->nbf;i++) if(D[opp->bf[i]].typ==T_CREA) dmg+=pw_eff(opp,i);
  for(int i=0;i<me->nbf;i++)  if(D[me->bf[i]].typ==T_CREA && !(D[me->bf[i]].kw&K_DEF)) blk+=th_eff(me,i);
  int neto = dmg - blk/2;
  return neto>0?neto:0;
}
static int turnos_de_vida(P*me,P*opp){
  int pres=board_pressure(me,opp);
  if(pres<=0) return 99;
  int t=(me->life + pres - 1)/pres;
  return t<1?1:t;
}
static int ncreat_fwd(P*p){ int n=0; for(int i=0;i<p->nbf;i++) if(D[p->bf[i]].typ==T_CREA) n++; return n; }
static int ncreat(P*p){ int n=0; for(int i=0;i<p->nbf;i++) if(D[p->bf[i]].typ==T_CREA) n++; return n; }
static int maxpower(P*p){ int m=0; for(int i=0;i<p->nbf;i++) if(D[p->bf[i]].typ==T_CREA&&pw(p,i)>m) m=pw(p,i); return m; }
static int nartleg(P*p){ int n=0; for(int i=0;i<p->nbf;i++){ uint8_t t=D[p->bf[i]].typ; if(t==T_ART||t==T_ENCH) n++; } return n; }

/* ---------- aplicar efecto ---------- */
static int token_mult(P*p){
  int m=1;
  for(int i=0;i<p->nbf;i++) if(D[p->bf[i]].eff==E_TOKEN_DOUBLE) m*=2;
  return m>8?8:m;
}
static int16_t defscore(Def*d);      /* definida mas abajo */

/* ---- fichas de verdad, no clones de la carta que las crea ----
   mk_tokens ignoraba pwr y tou y metia en la mesa el Def de la carta generadora. Si esa
   carta era un conjuro o un artefacto, la "ficha" entraba con typ de conjuro y 0/0: no
   contaba como criatura, no atacaba, no bloqueaba, no recibia bonos de lord y no moria
   nunca. Solo inflaba el contador de permanentes.

   Medido en sintetico: 20 conjuros "crea dos fichas 2/2" contra un rival vacio ganaban
   el 0,0% y no hacian danio jamas; el mismo mana en criaturas 2/2 de verdad, la mitad de
   cuerpos, ganaba el 76,2%.

   Y fallaba al reves tambien: si la fuente SI era criatura, la ficha salia copia
   completa de ella (Writhing Chrysalis 2/3 regalaba dos 2/3 en vez de fichas chicas).

   Se cachean por fuerza/resistencia al final de D[]. pwr<0 pide clonar la fuente a
   proposito, que es lo correcto en Hare Apparent. Ablacion: FICHAS_REALES=0. */
static int TOKDEF[16][16][2];
static int token_def(int pwr,int tou,int mana){
  if(pwr<0) pwr=0;  if(pwr>15) pwr=15;
  if(tou<1) tou=1;  if(tou>15) tou=15;
  mana = mana?1:0;
  if(TOKDEF[pwr][tou][mana]) return TOKDEF[pwr][tou][mana];
  if(NDEF>=MAXDEF) return -1;
  int i=NDEF++;
  memset(&D[i],0,sizeof(Def));
  D[i].typ=T_CREA; D[i].power=(int16_t)pwr; D[i].tough=(int16_t)tou;
  /* fichas que se sacrifican por mana (Eldrazi Spawn/Scion). Sin esto son 0/1 vainilla
     y se pierde su valor entero, que es rampa y no cuerpo. */
  if(mana){ D[i].mana_out=1; D[i].produces=31; }
  D[i].score=defscore(&D[i]);
  TOKDEF[pwr][tou][mana]=i;
  return i;
}
static void mk_tokens(P*me,int proto,int count,int pwr,int tou,int mana){
  int m=token_mult(me); count*=m;
  int td = proto;
  if(FICHAS_REALES && pwr>=0){
    if(pwr==0 && tou==0){ pwr=1; tou=1; }   /* sin p/t en el texto: ficha 1/1 */
    int t=token_def(pwr,tou,mana);
    if(t>=0) td=t;
  }
  for(int k=0;k<count && me->nbf<BFMAX;k++){
    int i=me->nbf++;
    me->bf[i]=td; me->tap[i]=0; me->sick[i]=1; me->ctr[i]=0; me->eqp[i]=0;
  }
}
/* Disparo AL ATACAR. Mismo truco que apply_die: se copia el Def a una entrada temporal
   con el efecto en la ranura primaria y se reutiliza el switch de apply, en vez de
   duplicar los cincuenta casos. Ablacion: ATAQUE_OFF=1. */
static int ATAQUE_ON = 1;
static int cumple_cond(P*p, Def*d);
static void apply_atk(P*me,P*opp,int def){
  if(!ATAQUE_ON || !D[def].atk_eff) return;
  if(!cumple_cond(me,&D[def])) return;
  if(NDEF+1>=MAXDEF) return;
  int t = NDEF+1;        /* temporal propio: NDEF ya lo usa apply_die */
  D[t] = D[def];
  D[t].eff = D[def].atk_eff; D[t].p1 = D[def].atk_p1;
  D[t].eff2=0; D[t].eff3=0; D[t].die_eff=0; D[t].atk_eff=0;
  apply(me,opp,t,0);
}

/* Ejecuta el disparo de cementerio reutilizando el switch de apply. Se copia el Def a
   una entrada temporal con el efecto de muerte en la ranura primaria: asi no hay que
   duplicar los cincuenta casos del switch ni tocar su firma. */
static void apply_die(P*me,P*opp,int def){
  if(NDEF>=MAXDEF) return;
  int t=NDEF;                      /* temporal: NO se incrementa NDEF, se reusa siempre */
  D[t]=D[def];
  D[t].eff=D[def].die_eff; D[t].p1=D[def].die_p1; D[t].p2=0;
  D[t].eff2=0; D[t].eff3=0; D[t].die_eff=0;
  apply(me,opp,t,0);
}
static void apply(P*me,P*opp,int def,int which){
  Def*d=&D[def];
  int e = (which==0)? d->eff : (which==1? d->eff2 : d->eff3);
  int a = (which==0)? d->p1  : (which==1? d->q1   : d->r1);
  int b = (which==0)? d->p2  : (which==1? d->q2   : d->r2);
  switch(e){
    case E_ETB_DMG: case E_DMG_SPELL: {
      ST_removal++;
      int t=best_killable(opp,a);
      if(t>=0 && !try_protect(opp)){ rmbf(opp,t); ST_kills++; }
      else if(ncreat(opp)==0) opp->life-=a;   /* sin objetivos: a la cara */
    } break;
    case E_BURN_FACE: opp->life-=a; break;
    /* dano flexible ("a cualquier objetivo"): mata si la criatura vale la pena,
       remata si con eso gana, y si no va a la cara. */
    case E_DMG_ANY: {
      if(DMG_ANY_FACE){ opp->life-=a; break; }   /* ablacion: como estaba antes, solo a la cara */
      ST_removal++;
      if(opp->life <= a){ opp->life -= a; break; }           /* remate */
      int t = best_killable(opp,a);
      int vale = 0;
      if(t>=0){
        int val = pw(opp,t)*2 + th(opp,t);
        if(D[opp->bf[t]].kw&K_FLY) val+=3;
        if(D[opp->bf[t]].kw&K_DT)  val+=3;
        if(D[opp->bf[t]].eff==E_LORD||D[opp->bf[t]].eff==E_ENGINE||
           D[opp->bf[t]].eff==E_SPELL_DMG||D[opp->bf[t]].eff==E_UPKEEP_DRAW) val+=10;
        vale = (val >= a*2) || (turnos_de_vida(me,opp) <= 4);
      }
      if(t>=0 && vale && !try_protect(opp)){ rmbf(opp,t); ST_kills++; }
      else opp->life -= a;
    } break;
    case E_ETB_DRAIN: opp->life-=a; me->life+=a; break;
    case E_ETB_DRAW: draw_select(me,a, 2*a+2); break;
    case E_ETB_DISCARD: {
      /* el descarte dirigido se lleva la MEJOR carta, no una al azar */
      ST_disc_try++; ST_disc_handsz += opp->nh;
      for(int rep=0; rep<(a>0?a:1) && opp->nh>0; rep++){
        ST_disc_hit++;
        int j=0; for(int i=1;i<opp->nh;i++) if(D[opp->hand[i]].score > D[opp->hand[j]].score) j=i;
        for(int k=j;k<opp->nh-1;k++) opp->hand[k]=opp->hand[k+1];
        opp->nh--;
      }
    } break;
    case E_ETB_TOKEN: mk_tokens(me,def,a,(b>>4)&15,b&15,(b>>8)&1); break;
    case E_TOKEN_SCALE: {
      /* Hare Apparent: fichas = numero de copias propias ya en mesa */
      int same=0; for(int i=0;i<me->nbf;i++) if(me->bf[i]==def) same++;
      /* aqui la ficha SI es copia de la carta, asi que se clona a proposito */
      if(same>1) mk_tokens(me,def,same-1,-1,-1,0);
    } break;
    case E_TOKEN_DOUBLE: break;   /* estatico, se lee en token_mult */
    case E_EXILE_ENGINE: break;   /* estatico, se dispara al exiliar */
    case E_DEATH_DMG: break;      /* estatico, se dispara al morir */
    case E_ATTACK_DRAW: break;    /* estatico, se dispara al atacar */
    case E_RECURSIVE: break;      /* estatico, vuelve del cementerio */
    case E_TEAM_MANA: break;      /* estatico, lo lee payable */
    case E_ATTACK_DMG: break;     /* estatico, se dispara al atacar */
    case E_PROTECT: break;        /* reactivo, se usa en try_protect */
    case E_UPKEEP_DRAW: break;    /* estatico, se lee en upkeep */
    case E_REPEAT_PUMP: break;    /* estatico, se lee en combate */
    case E_TEAM_PUMP: {           /* remate: todo el equipo crece */
      int nc=ncreat(me);
      for(int i=0;i<me->nbf;i++) if(D[me->bf[i]].typ==T_CREA) me->ctr[i] += (nc>a?a:nc);
    } break;
    case E_FOG_BOUNCE: {          /* devuelve los atacantes: se modela limpiando su tablero temporalmente */
      for(int i=opp->nbf-1;i>=0;i--) if(D[opp->bf[i]].typ==T_CREA && opp->tap[i]){
        opp->hand[opp->nh++]=opp->bf[i]; rmbf(opp,i); }
    } break;
    /* ---- BLOQUE DE NEGACION ---- */
    case E_EDICT: { if(!NEG_ON) break;            /* el rival sacrifica: elige la PEOR, y no apunta */
      for(int rep=0; rep<(a>0?a:1); rep++){
        int worst=-1, wv=1<<30;
        for(int i=0;i<opp->nbf;i++){ if(D[opp->bf[i]].typ!=T_CREA) continue;
          int v=pw(opp,i)*2+th(opp,i);
          if(v<wv){wv=v;worst=i;} }
        if(worst<0) break;
        rmbf(opp,worst); ST_kills++;
      }
    } break;
    case E_TAPDOWN: { if(!NEG_ON) break;   /* inmoviliza la amenaza: no ataca ni bloquea */
      int t=biggest_threat(opp);
      if(t>=0 && !try_protect(opp)){
        opp->tap[t]=1;
        if(a>=2) opp->frz[t]=(uint8_t)(a-1);      /* y tampoco se endereza */
      }
    } break;
    case E_TAX: break;         /* estatico: lo lee cast_phase via ->taxed */
    case E_LAND_KILL: { if(!NEG_ON) break;  /* le quita una tierra: se lleva su turno */
      for(int rep=0; rep<(a>0?a:1); rep++){
        if(opp->nl<=0) break;
        int worst=0;                              /* la que menos colores da */
        for(int i=1;i<opp->nl;i++)
          if(__builtin_popcount(D[opp->lands[i]].produces) >
             __builtin_popcount(D[opp->lands[worst]].produces)) worst=i;
        for(int k=worst;k<opp->nl-1;k++){ opp->lands[k]=opp->lands[k+1]; opp->ltap[k]=opp->ltap[k+1]; }
        opp->nl--;
      }
    } break;
    case E_MASS_BOUNCE: { if(!NEG_ON) break; /* devuelve a la mano todo lo que este atacando */
      for(int i=opp->nbf-1;i>=0;i--) if(D[opp->bf[i]].typ==T_CREA && opp->tap[i]){
        opp->hand[opp->nh++]=opp->bf[i]; rmbf(opp,i); }
    } break;
    case E_MOBILIZE: mk_tokens(me,def,a,1,1,0); break;
    case E_MASS_CHEAT: {          /* baja criaturas de la mano gratis */
      int put=0;
      for(int i=me->nh-1;i>=0 && put<a;i--) if(D[me->hand[i]].typ==T_CREA){
        int cd=me->hand[i];
        for(int k=i;k<me->nh-1;k++) me->hand[k]=me->hand[k+1];
        me->nh--; addbf(me,cd); put++; }
    } break;
    case E_DESTROY: case E_EXILE: { int t=biggest_threat(opp);
        ST_removal++;
        if(t>=0 && !(D[opp->bf[t]].kw&K_IND) && !try_protect(opp)){ rmbf(opp,t); ST_kills++;
          if(e==E_EXILE){    /* cada exilio alimenta a Ketramose y similares */
            for(int q=0;q<me->nbf;q++)
              if(D[me->bf[q]].eff==E_EXILE_ENGINE){ draw_select(me,D[me->bf[q]].p1,3); me->life--; }
          }
        } } break;
    case E_BOUNCE: { int t=biggest_threat(opp); if(t>=0){ opp->hand[opp->nh++]=opp->bf[t]; rmbf(opp,t);} } break;
    case E_FIGHT: { int t=biggest_threat(opp); int m=-1,mv=-1;
        for(int i=0;i<me->nbf;i++) if(D[me->bf[i]].typ==T_CREA&&pw(me,i)>mv){mv=pw(me,i);m=i;}
        if(t>=0&&m>=0){ if(mv>=th(opp,t)) rmbf(opp,t); } } break;
    case E_SWEEPER: { ST_sweep++;
      { int n=0; for(int i=0;i<opp->nbf;i++) if(D[opp->bf[i]].typ==T_CREA&&th_eff(opp,i)<=a) n++;
        if(n>0) for(int q=0;q<me->nbf;q++)
          if(D[me->bf[q]].eff==E_EXILE_ENGINE){ draw_select(me,D[me->bf[q]].p1,3); me->life--; } }
      /* Ojo con el orden: el barrido mata lords, y en cuanto muere uno el resto encoge.
         Se congela el bono de los dos lados ANTES de empezar a quitar criaturas, que es
         como funciona de verdad (el dano se marca a la vez y luego mueren juntas). */
      { int sbp,sbt,mbp,mbt; lordbonus(opp,&sbp,&sbt); lordbonus(me,&mbp,&mbt);
        if(!LORD_VE){ sbt=0; mbt=0; }
        for(int i=opp->nbf-1;i>=0;i--)
          if(D[opp->bf[i]].typ==T_CREA && th(opp,i)+sbt<=a && !(D[opp->bf[i]].kw&K_IND)) rmbf(opp,i);
        for(int i=me->nbf-1;i>=0;i--)
          if(D[me->bf[i]].typ==T_CREA && th(me,i)+mbt<=a && !(D[me->bf[i]].kw&K_IND)) rmbf(me,i); }
    } break;
    case E_LIFEGAIN: me->life+=a; break;
    case E_ETB_COUNTERS: { int m=-1,mv=-1; for(int i=0;i<me->nbf;i++) if(D[me->bf[i]].typ==T_CREA&&pw(me,i)>mv){mv=pw(me,i);m=i;}
        if(m>=0) me->ctr[m]+=a; } break;
    case E_TREASURE: me->treasures+=(a?a:1); break;
    /* Burning-Tree Emissary se paga sola: entra, devuelve su mana y permite encadenar
       otra criatura el mismo turno. Modelarla como un 2/2 vainilla dejaba al arquetipo
       10 puntos por debajo de su winrate real. El mana va al pozo flotante, que se
       vacia al final del turno: no es un Tesoro. */
    case E_ETB_MANA: { int q=(a?a:1); me->treasures+=q; me->flot+=q; } break;
    case E_AMASS: { if(me->army<0){ if(me->nbf<BFMAX){ int i=me->nbf++; me->bf[i]=def; me->tap[i]=0;
            me->sick[i]=1; me->ctr[i]=0; me->eqp[i]=0; me->army=i; } }
        if(me->army>=0) me->ctr[me->army]+=a; } break;
    case E_LOOT_TOKEN: draw(me,1); if(me->nh>0){ int j=ri(me->nh); for(int k=j;k<me->nh-1;k++) me->hand[k]=me->hand[k+1]; me->nh--; } break;
    case E_EQUIP: { int m=-1,mv=-1; for(int i=0;i<me->nbf;i++) if(D[me->bf[i]].typ==T_CREA&&pw(me,i)>mv){mv=pw(me,i);m=i;}
        if(m>=0) me->eqp[m]+= (a<<8)|b; } break;
    case E_PUMP: { int m=-1,mv=-1; for(int i=0;i<me->nbf;i++) if(D[me->bf[i]].typ==T_CREA&&pw(me,i)>mv){mv=pw(me,i);m=i;}
        if(m>=0) me->ctr[m] += (a>b?a:b); } break;
    case E_RAMP: me->treasures++; break;
    case E_COUNTER: break;   /* se resuelve en try_counter */

    default: break;
  }
}

/* ---------- puntuacion heuristica para el orden de juego de la IA ---------- */
static int16_t defscore(Def*d){
  int s=0;
  if(d->typ==T_CREA){ s = d->power*3 + d->tough*2;
    if(d->kw&K_FLY) s+=4; if(d->kw&K_DT) s+=4; if(d->kw&K_TRA) s+=2; if(d->kw&K_LL) s+=2;
    if(d->kw&K_MEN) s+=2; if(d->kw&K_FS) s+=2; if(d->kw&K_HAS) s+=1; }
  switch(d->eff){
    case E_DESTROY: case E_EXILE: s+=14; break;
    case E_DMG_SPELL: s+=8+d->p1*2; break;
    case E_DMG_ANY:   s+=10+d->p1*2; break;   /* flexible: mata o remata */
    case E_EDICT:     s+=10; break;           /* mata sin apuntar */
    case E_TAPDOWN:   s+=5+d->p1*3; break;
    case E_TAX:       s+=9*d->p1; break;      /* prision: encarece todo lo suyo */
    case E_LAND_KILL: s+=7; break;
    case E_MASS_BOUNCE: s+=11; break;
    case E_SWEEPER: s+=18; break;
    case E_ETB_DRAW: s+=5*d->p1; break;
    case E_ENGINE: case E_DRAW_ON_DMG: s+=14; break;
    case E_EXILE_ENGINE: s+=18; break;
    case E_LORD: s+=10; break;
    case E_EQUIP: s+=4+d->p1*2; break;
    case E_ETB_DRAIN: s+=3*d->p1; break;
    case E_BURN_FACE: s+=2*d->p1; break;
    case E_UPKEEP_DRAIN: s+=12; break;
    case E_SPELL_DMG: s+=16; break;
    case E_UPKEEP_DRAW: s+=14; break;
    case E_REPEAT_PUMP: s+=9; break;
    case E_TEAM_PUMP: s+=20; break;
    case E_MOBILIZE: s+=8; break;
    case E_MASS_CHEAT: s+=16; break;
    case E_DEATH_DMG: s+=6; break;
    case E_ATTACK_DRAW: s+=10; break;
    case E_ATTACK_DMG: s+=9; break;
    case E_PROTECT: s+=7; break;
    case E_TEAM_MANA: s+=14; break;
    case E_FOG_BOUNCE: s+=10; break;
    default: break;
  }
  if(d->mana_out && d->typ!=T_LAND) s += 6*d->mana_out;   /* aceleracion de mana */
  if(d->no_untap) s -= 8;                                  /* no se endereza: gran inconveniente */
  if(d->dyn) s -= 4;                                       /* P/T variable: arranca pequena */
  return (int16_t)(s - d->cmc);   /* eficiencia */
}

/* ---------- mulligan ---------- */
static int keepable(P*p,int nkeep){
  int lands=0, cheap=0;
  for(int i=0;i<p->nh;i++){ Def*d=&D[p->hand[i]];
    if(d->typ==T_LAND) lands++; else if(d->cmc<=3) cheap++; }
  if(nkeep<=5) return 1;
  return (lands>=2 && lands<=5 && cheap>=2);
}

/* ---------- turno ---------- */
/* cuanto mana reserva el jugador para instantaneos en el turno rival */
/* Solo el CONTRAHECHIZO obliga a dejar mana abierto: la remocion se puede lanzar
   perfectamente en el propio turno. Reservar para todo paralizaba a los mazos de control. */
static int reserve_for_instants(P*p){
  int cheapest=99;
  for(int i=0;i<p->nh;i++){ Def*d=&D[p->hand[i]];
    if(d->eff!=E_COUNTER) continue;
    if(d->cmc<cheapest) cheapest=d->cmc; }
  if(cheapest==99) return 0;
  if(cheapest>RESERVE_MAX) cheapest=RESERVE_MAX;
  /* Solo se reserva si SOBRA mana: hay que poder desarrollar Y dejar abierto.
     Reservar desde el turno 3 paralizaba a los mazos de tempo azul. */
  return (p->nl>=3) ? cheapest : 0;
}
/* el defensor intenta contrarrestar un hechizo entrante; 1 = contrarrestado */
static int try_counter(P*def,Def*spell){
  int best=-1;
  for(int i=0;i<def->nh;i++){ Def*d=&D[def->hand[i]];
    if(d->eff!=E_COUNTER) continue;
    ST_counter_seen++;
    { int u=0; for(int q=0;q<def->nl;q++) if(!def->ltap[q]) u++; ST_draw += u; ST_manaflood++; }
    if(!payable(def,d,def->treasures)) continue;
    /* umbral: cuanto peor vamos, mas barato contrarrestamos */
    int umbral = (def->life<=10) ? 0 : (def->life<=15 ? 3 : 6);
    if(spell->score < umbral) continue;
    best=i; break; }
  if(best<0) return 0;
  int def_i=def->hand[best];
  for(int k=best;k<def->nh-1;k++) def->hand[k]=def->hand[k+1]; def->nh--;
  paycost(def,&D[def_i],&def->treasures);
  ST_counter_used++;
  return 1;
}
/* el defensor usa remocion instantanea en el turno rival */
static int has_counter_in_hand(P*p){
  for(int i=0;i<p->nh;i++) if(D[p->hand[i]].eff==E_COUNTER) return D[p->hand[i]].cmc;
  return 0;
}
static void defender_instants(P*def,P*act){
  ALT_OPP = act;
  int keep = has_counter_in_hand(def);
  for(int guard=0;guard<3;guard++){
    int best=-1,bv=0;
    for(int i=0;i<def->nh;i++){ Def*d=&D[def->hand[i]];
      if(d->typ!=T_INST && !(d->kw&K_FLASH)) continue;
      if(!(d->eff==E_DESTROY||d->eff==E_DMG_SPELL||d->eff==E_DMG_ANY||d->eff==E_EXILE||
           d->eff==E_BOUNCE||d->eff==E_EDICT||d->eff==E_TAPDOWN||d->eff==E_MASS_BOUNCE||d->typ==T_CREA)) continue;
      if(!payable(def,d,def->treasures)) continue;
      /* deja mana para el contrahechizo si lo tiene y no esta contra las cuerdas */
      if(keep>0 && def->life>8 && untapped_count(def) - d->cmc < keep) continue;
      int t=biggest_threat(act); if(t<0 && d->typ!=T_CREA && d->eff!=E_DMG_ANY) continue;
      int v=d->score; if(v>bv){bv=v;best=i;} }
    if(best<0) return;
    int di=def->hand[best];
    for(int k=best;k<def->nh-1;k++) def->hand[k]=def->hand[k+1]; def->nh--;
    paycost(def,&D[di],&def->treasures);
    if(D[di].typ==T_INST||D[di].typ==T_SORC) def->gy_is++;
    if(D[di].typ==T_CREA) addbf(def,di);
    SPARE_MANA = untapped_count(def);
    apply(def,act,di,0);
    if(D[di].eff2) apply(def,act,di,1);
  }
}

/* ---- habilidades ACTIVADAS ----
   La diferencia con un efecto de entrada es TODA la carta: el jugador elige cuando, y
   paga un coste cada vez. Modelar Krark-Clan Shaman como barredor de entrada lo hacia
   suicidarse al entrar (es un 1/1 y su barrido mata resistencia <=1 en los dos lados):
   medido, 2,266 -> 3,102. Con eleccion y coste, la misma carta es el plan del mazo.

   Se evalua una vez por turno, en la primera fase principal, y se repite mientras siga
   siendo favorable y quede con que pagar. Ablacion: ACTIVADAS_ON=0. */
static int cuenta_artefactos(P*p){
  int n=0; for(int i=0;i<p->nbf;i++) if(D[p->bf[i]].typ==T_ART) n++;
  return n;
}
static void activar_habilidades(P*me,P*opp){
  if(!ACTIVADAS_ON) return;
  for(int vuelta=0; vuelta<4; vuelta++){
    int hecho=0;
    for(int i=0;i<me->nbf;i++){
      Def*d=&D[me->bf[i]];
      if(!d->act_eff) continue;
      if(d->act_cost==1 && cuenta_artefactos(me)<1) continue;   /* nada que sacrificar */
      /* ¿conviene? Para un barrido, solo si mata mas suyas que mias. */
      if(d->act_eff==E_SWEEPER){
        int suyas=0,mias=0;
        for(int j=0;j<opp->nbf;j++)
          if(D[opp->bf[j]].typ==T_CREA && th(opp,j)<=d->act_p1 && !(D[opp->bf[j]].kw&K_IND)) suyas++;
        for(int j=0;j<me->nbf;j++)
          if(D[me->bf[j]].typ==T_CREA && th(me,j)<=d->act_p1 && !(D[me->bf[j]].kw&K_IND)) mias++;
        if(suyas<=mias) continue;          /* regalar el tablero propio no es un plan */
      }
      /* pagar el coste */
      if(d->act_cost==1){
        for(int j=me->nbf-1;j>=0;j--) if(D[me->bf[j]].typ==T_ART){ rmbf(me,j); break; }
      }
      /* la carta puede haberse movido al sacrificar: se re-localiza por indice de Def */
      int def=-1;
      for(int j=0;j<me->nbf;j++) if(D[me->bf[j]].act_eff==d->act_eff &&
                                    D[me->bf[j]].act_p1==d->act_p1){ def=me->bf[j]; break; }
      if(def<0) break;
      int t=NDEF; if(t>=MAXDEF) return;
      D[t]=D[def]; D[t].eff=D[def].act_eff; D[t].p1=D[def].act_p1; D[t].p2=0;
      D[t].eff2=0; D[t].eff3=0; D[t].die_eff=0; D[t].act_eff=0;
      apply(me,opp,t,0);
      hecho=1; break;                      /* el tablero cambio: reevaluar desde cero */
    }
    if(!hecho) break;
  }
}


/* ---- AVENTURA ----
   Se evalua una vez por turno, antes de la fase principal. Solo se lanza si el efecto
   sirve AHORA: remocion con objetivo, robo o rampa. Sin ese filtro el motor quemaba la
   mitad barata de Smaug en el turno 2 contra una mesa vacia. */
static int AVENTURA_ON = 1;
static int aventura_util(P*me,P*opp,Def*d){
  int e=d->adv_eff;
  if(e==E_DESTROY||e==E_EXILE||e==E_DMG_SPELL||e==E_EDICT||e==E_TAPDOWN||e==E_BOUNCE)
    return ncreat(opp)>0;
  if(e==E_DMG_ANY||e==E_BURN_FACE||e==E_ETB_DRAIN) return 1;
  if(e==E_ETB_DRAW||e==E_RAMP||e==E_ETB_TOKEN||e==E_LIFEGAIN||e==E_ETB_COUNTERS) return 1;
  if(e==E_SWEEPER) return ncreat(opp)>ncreat(me);
  return 0;
}
static void lanzar_aventuras(P*me,P*opp){
  if(!AVENTURA_ON) return;
  for(int i=0;i<me->nh;i++){
    Def*d=&D[me->hand[i]];
    if(!d->adv_eff || me->hand_adv[i]) continue;
    if(!aventura_util(me,opp,d)) continue;
    /* coste de la cara barata: se arma un Def temporal para reusar payable/paycost */
    if(NDEF+2>=MAXDEF) return;
    int t=NDEF+2;
    D[t]=*d;
    D[t].gen=d->adv_gen; D[t].typ=T_SORC; D[t].alt=0; D[t].coste_extra=0; D[t].cred=0;
    for(int k=0;k<5;k++) D[t].pip[k]=d->adv_pip[k];
    if(!payable(me,&D[t],me->treasures)) continue;
    paycost(me,&D[t],&me->treasures);
    D[t].eff=d->adv_eff; D[t].p1=d->adv_p1; D[t].p2=0;
    D[t].eff2=0; D[t].eff3=0; D[t].die_eff=0; D[t].atk_eff=0;
    apply(me,opp,t,0);
    me->hand_adv[i]=1;      /* esta copia ya gasto su aventura */
    return;                 /* una por turno */
  }
}

static void cast_phase(P*me,P*opp,int main2){
  ALT_OPP = opp;
  if(!main2){ activar_habilidades(me,opp); lanzar_aventuras(me,opp); }
  /* impuesto que me cobra el rival (Ghostly Prison y familia): encarece todo lo mio */
  me->taxed=0; me->tax_atk=0;
  for(int i=0;i<opp->nbf;i++){
    if(!NEG_ON) break;
    /* tax_atk grava ATACAR, no lanzar: son efectos distintos y confundirlos inflaba
       a Dain 17 puntos. El de ataque lo cobra combat(), no pay_gen(). */
    { Def*dx=&D[opp->bf[i]];
      if(dx->eff==E_TAX || dx->eff2==E_TAX){
        if(!cumple_cond(opp,dx)) continue;
        int q = (dx->eff==E_TAX)? dx->p1 : dx->q1;
        if(dx->tax_atk) me->tax_atk += q; else me->taxed += q;
      } }
  }
  /* jugar tierra */
  if(!me->played_land){
    int best=-1;
    for(int i=0;i<me->nh;i++) if(D[me->hand[i]].typ==T_LAND){
      if(best<0) best=i;
      else { /* prefiere la que da colores que faltan */
        int hb=__builtin_popcount(D[me->hand[best]].produces), hi=__builtin_popcount(D[me->hand[i]].produces);
        if(hi>hb) best=i; } }
    if(best>=0){ addbf(me,me->hand[best]); me->played_land=1;
      for(int k=best;k<me->nh-1;k++){ me->hand[k]=me->hand[k+1];
      me->hand_adv[k]=me->hand_adv[k+1]; } me->nh--; }
  }
  /* lanzar hechizos por valor mientras alcance el mana.
     Dos pasadas: la primera respeta la reserva de mana para contrahechizos;
     si con la reserva no se puede jugar NADA y no hay tablero, se repite
     ignorandola. Reservar hasta paralizarse no es jugar control, es no jugar. */
  for(int guard=0; guard<24; guard++){
    int best=-1, bv=-1000;
    int ignora_reserva=0;
    static int dbg_v[ZONEMAX];
    for(int i=0;i<ZONEMAX;i++) dbg_v[i]=-999;
   REINTENTO:
    for(int i=0;i<me->nh;i++){ Def*d=&D[me->hand[i]];
      if(d->typ==T_LAND) continue;
      if(!payable(me,d,me->treasures)) continue;
      SPARE_MANA = untapped_count(me) - d->cmc; if(SPARE_MANA<0) SPARE_MANA=0;
      int v=d->score;
      int imposible=0;   /* exige objetivo y no lo tiene: no se puede lanzar */
      if(d->typ==T_INST && !main2) v-=2;                  /* prefiere guardar instantaneos */
      /* RESERVA DURA de mana para interaccion instantanea.
         Se SALTA el candidato (no se rompe el bucle) para que el mazo pueda
         lanzar otra cosa mas barata y aun asi dejar mana abierto. */
      /* contrahechizos y proteccion NUNCA se lanzan proactivamente: solo responden */
      if(d->eff==E_COUNTER || d->eff==E_PROTECT) continue;
      /* la reserva la respeta TODO lo que no sea interaccion, incluidos los
         instantaneos de valor: un cantrip no debe comerse el mana del contra */
      {
        int es_interaccion = (d->eff==E_DESTROY||d->eff==E_DMG_SPELL||
                              d->eff==E_EXILE||d->eff==E_BOUNCE);
        if(!es_interaccion){
          int res=reserve_for_instants(me);
          int desperate = (me->life <= 6) || ignora_reserva;
          if(res>0 && !desperate && untapped_count(me) - d->cmc < res) continue;
        }
      }
      /* La remocion vale lo que mata. Sin objetivo no se lanza; con objetivo
         pequeno vale poco; contra la amenaza gorda vale mucho. */
      {
        if(d->eff==E_DMG_ANY && d->typ!=T_CREA){
          int t=best_killable(opp,d->p1);
          if(t>=0){
            v += (pw(opp,t)*2 + th(opp,t) - 8)*W_TARGET/100;
            if(W_PRESSURE>0){ int tv=turnos_de_vida(me,opp);
              if(tv<=6) v += W_PRESSURE * pw(opp,t) / tv / 10; }
          }
          if(opp->life <= d->p1) v += 60;                  /* remata: lanzalo ya */
        }
        /* Mismo bonus para las otras dos formas de mandar dano a la cara. Sin esto un
           hechizo que gana la partida ahi mismo puntuaba 2*p1 (BURN_FACE) o 3*p1
           (ETB_DRAIN) y perdia contra una criatura decente. "Si esto gana ahora, se
           lanza ahora" no admite discusion. Ablacion: REMATE_LETAL=0. */
        if(REMATE_LETAL){
          int cara = 0;
          if(d->eff ==E_BURN_FACE || d->eff ==E_ETB_DRAIN) cara += d->p1;
          if(d->eff2==E_BURN_FACE || d->eff2==E_ETB_DRAIN) cara += d->q1;
          if(d->eff3==E_BURN_FACE || d->eff3==E_ETB_DRAIN) cara += d->r1;
          if(cara>0 && opp->life <= cara) v += 60;
        }
        int es_rem = (d->eff==E_DESTROY||d->eff==E_EXILE||d->eff==E_DMG_SPELL||d->eff==E_ETB_DMG);
        if(es_rem && d->typ!=T_CREA){
          int t = (d->eff==E_DESTROY||d->eff==E_EXILE) ? biggest_threat(opp)
                                                       : best_killable(opp,d->p1);
          /* Por reglas (601.2c) un hechizo que exige objetivo NO se puede lanzar sin
             objetivo legal. Aqui se lanzaba igual: PEN_NOTARGET=15 es menor que la
             distancia al suelo CAST_FLOOR=-20, asi que una remocion que puntua 12-14
             quedaba en -3 y pasaba el corte. La carta se iba de la mano y apply() no
             hacia nada porque biggest_threat devolvia -1.

             Medido por el agente: 2,85 cartas por partida tiradas al vacio en
             Four-Color vs Mardu, 2,27 en Izzet vs Dimir. En sintetico, 20 remociones
             contra un rival sin criaturas se lanzaban 13,12 veces por partida y
             vaciaban la mano matando cero.

             Con NOTARGET_DURO se marca imposible en vez de penalizar, que es la regla
             de verdad. Ablacion: NOTARGET_DURO=0 vuelve a la penalizacion blanda. */
          if(t<0){
            /* OJO a la diferencia, que la primera version se comio: t<0 significa "no
               hay nada que MATAR", y eso pasa en dos casos muy distintos. Si el rival
               no tiene criaturas, no hay objetivo legal y por 601.2c el hechizo no se
               puede lanzar. Pero si tiene criaturas y solo pasa que no las mata, el
               objetivo SI es legal y lanzarlo es una mala decision, no una ilegal.
               Bloquear los dos casos disparo el objetivo de 1,270 a 2,813. */
            if(NOTARGET_DURO && ncreat(opp)==0) imposible = 1;
            else v -= PEN_NOTARGET;                         /* nada que matar */
          }
          else {
            int val = pw(opp,t)*2 + th(opp,t);
            if(D[opp->bf[t]].kw&K_FLY) val+=3;
            if(D[opp->bf[t]].kw&K_DT)  val+=3;
            v += (val - 8)*W_TARGET/100;                     /* premia matar algo gordo */
            if(me->life<=10) v += 8;                         /* con la vida baja, urge */
            /* y sobre todo: cuanto dano por turno me quita, con que urgencia */
            if(W_PRESSURE>0){
              int tv=turnos_de_vida(me,opp);
              if(tv<=6) v += W_PRESSURE * pw(opp,t) / tv / 10;
            }
          }
        }
        if(es_rem && d->typ==T_CREA && ncreat(opp)==0) v -= 4;
      }
      if((d->eff==E_EDICT||d->eff==E_TAPDOWN||d->eff==E_MASS_BOUNCE) && ncreat(opp)==0) v-=40;
      if(d->eff==E_LAND_KILL && opp->nl<=2) v-=15;      /* ya esta sin tierras */
      if(d->eff==E_FIGHT && (ncreat(me)==0||ncreat(opp)==0)) v-=45;
      if(d->eff==E_BOUNCE && ncreat(opp)==0) v-=35;
      if((d->eff==E_PUMP||d->eff==E_EQUIP||d->eff==E_ETB_COUNTERS) && ncreat(me)==0) v-=25;
      if(d->eff==E_SWEEPER){
        int oc=ncreat(opp), mc=ncreat(me);
        if(oc<SWEEP_MIN) v-=30;                      /* espera a que valga la pena */
        else v += (oc-mc)*6;                 /* mejor cuanto mas desbalanceado */
        /* barrer cuando te estan matando vale mucho mas que barrer por valor */
        if(W_PRESSURE>0 && oc>=SWEEP_MIN){
          int tv=turnos_de_vida(me,opp);
          if(tv<=6) v += W_PRESSURE * board_pressure(me,opp) / tv / 10;
        }
      }
      if(d->typ==T_CREA) v+=3;
      if(imposible) continue;      /* regla 601.2c */
      /* correccion aprendida (POLNET). Con pesos en cero no cambia nada, asi que el
         punto de partida del entrenamiento es exactamente esta heuristica. */
      if(PN_ON && (PN_LADO || me==(P*)PLAYER_A))
        v += pn_correccion(d, me, opp, turno_actual);
      dbg_v[i]=v;
      if(v>bv){bv=v;best=i;} }
    if(TRACE_ON && me==(P*)PLAYER_A){
      fprintf(stderr,"    [lanzar] mana libre %d | ", untapped_count(me));
      for(int i=0;i<me->nh;i++){ Def*x=&D[me->hand[i]];
        if(x->typ==T_LAND) continue;
        fprintf(stderr,"#%d(cmc%d %s v=%d) ", me->hand[i], x->cmc,
                payable(me,x,me->treasures)?"pag":"NOpag", (int)dbg_v[i]); }
      fprintf(stderr,"=> %s\n", best<0?"NADA":"lanza");
    }
    if(best<0||bv<CAST_FLOOR) break;
    int def=me->hand[best];
    for(int k=best;k<me->nh-1;k++){ me->hand[k]=me->hand[k+1];
      me->hand_adv[k]=me->hand_adv[k+1]; } me->nh--;
    paycost(me,&D[def],&me->treasures);
    tj_ev("lanza", me, def);
    SPARE_MANA = untapped_count(me);
    Def*d=&D[def];
    /* al cementerio va igual, se resuelva o lo contrarresten */
    if(d->typ==T_INST||d->typ==T_SORC) me->gy_is++;
    if(try_counter(opp,d)) continue;                 /* contrarrestado: se va al cementerio */
    if(d->typ!=T_CREA){
      for(int q=0;q<me->nbf;q++){
        if(D[me->bf[q]].eff==E_SPELL_DMG) opp->life -= D[me->bf[q]].p1;
        if(D[me->bf[q]].eff2==E_SPELL_DMG) opp->life -= D[me->bf[q]].q1;
        if(D[me->bf[q]].kw & K_PROW) me->ctr[q] += 0;   /* prowess: efimero, no acumula */
      }
    }
    if(d->typ==T_CREA||d->typ==T_ART||d->typ==T_ENCH||d->typ==T_PW||d->typ==T_LAND) addbf(me,def);
    apply(me,opp,def,0);
    if(d->eff2) apply(me,opp,def,1);
    if(d->eff3) apply(me,opp,def,2);
  }
}

/* Fuerza y resistencia EFECTIVAS de una criatura en combate: cuerpo + contadores +
   equipo + los lords que de verdad la suben. Un lord tribal solo cuenta para los suyos,
   asi que esto NO se puede resolver con un bono global calculado una vez. */
#define PWC(p,i) ({ int _b,_t; lordbonus_de((p),(i),&_b,&_t); pw((p),(i))+_b; })
#define THC(p,i) ({ int _b,_t; lordbonus_de((p),(i),&_b,&_t); th((p),(i))+_t; })

static void combat(P*me,P*opp){
  /* Estos dos son el bono de los lords SIN restriccion de tribu, y ya solo sirven de
     resumen: cada criatura pregunta por el suyo con PWC/THC, porque un lord de Elfos no
     sube a un Goblin. Antes se calculaba una vez y se sumaba a todo el mundo. */
  int bp,bt; lordbonus(me,&bp,&bt);
  int obp,obt; lordbonus(opp,&obp,&obt);
  (void)bp; (void)bt; (void)obp; (void)obt;
  /* habilidades activadas de pump: se usan una vez por turno sobre la mejor criatura */
  { int pump=0;
    for(int i=0;i<me->nbf;i++) if(D[me->bf[i]].eff==E_REPEAT_PUMP && !me->tap[i]) pump+=D[me->bf[i]].p1;
    if(pump>0){ int m=-1,mv=-1;
      for(int i=0;i<me->nbf;i++) if(D[me->bf[i]].typ==T_CREA && !me->sick[i] && pw(me,i)>mv){mv=pw(me,i);m=i;}
      if(m>=0) me->ctr[m]+=pump; } }

  /* --- eleccion de atacantes --- */
  int atk[BFMAX], na=0;
  int def_untapped=0;
  for(int j=0;j<opp->nbf;j++) if(D[opp->bf[j]].typ==T_CREA && !opp->tap[j]) def_untapped++;

  /* --- ataque letal AGREGADO ---
     La decision de atacar se toma criatura a criatura contra opp->life <= P_*2, asi que
     cinco criaturas de poder 2 frente a un rival a 9 vidas no ven que juntas lo matan y
     cada una decide quedarse en casa. En el lado del bloqueo la variable agregada si
     existe (lethal_now); en el del ataque no existia.
     Se calcula el dano que pasa SI ATACAN TODAS y el defensor bloquea lo mejor posible,
     o sea parando a los mas grandes. Es deliberadamente conservador: solo cuenta lo que
     al defensor no le alcanzan cuerpos para frenar. Ablacion: ATAQUE_LETAL=0. */
  int letal_agregado = 0;
  if(ATAQUE_LETAL){
    int pot[BFMAX], np=0;
    for(int i=0;i<me->nbf;i++){ Def*d2=&D[me->bf[i]];
      if(d2->typ!=T_CREA||me->sick[i]||me->tap[i]||(d2->kw&K_DEF)) continue;
      int p2=PWC(me,i);
      if(d2->eff ==E_COND_BUFF && cumple_cond(me,d2)) p2+=d2->p1;
      if(d2->eff2==E_COND_BUFF && cumple_cond(me,d2)) p2+=d2->q1;
      if(p2>0) pot[np++]=p2;
    }
    for(int a2=0;a2<np;a2++) for(int b2=a2+1;b2<np;b2++)
      if(pot[b2]>pot[a2]){ int t=pot[a2];pot[a2]=pot[b2];pot[b2]=t; }
    int pasa=0;
    for(int q=def_untapped;q<np;q++) pasa+=pot[q];
    letal_agregado = (pasa>0 && pasa >= opp->life);
  }

  /* ---- impuesto por atacar (Dain, Ghostly Prison) ----
     Es distinto de encarecer los hechizos: solo castiga al que quiere atacar, y por eso
     un mazo de control no lo nota. Se modela como lo que es: un tope al numero de
     atacantes segun el mana que quede sin gastar. El combate va despues de la primera
     fase principal, asi que reservar mana para atacar tiene un coste real. */
  int cupo_atacantes = BFMAX;
  if(opp->tax_atk > 0){
    cupo_atacantes = untapped_count(me) / opp->tax_atk;
    if(cupo_atacantes < 0) cupo_atacantes = 0;
  }
  for(int i=0;i<me->nbf;i++){
    Def*d=&D[me->bf[i]];
    if(na >= cupo_atacantes) break;             /* no alcanza para pagar mas ataques */
    if(d->typ!=T_CREA||me->sick[i]||me->tap[i]||(d->kw&K_DEF)) continue;
    int P_=PWC(me,i), T_=THC(me,i);
    if(d->eff==E_COND_BUFF && cumple_cond(me,d)){ P_+=d->p1; T_+=d->p2; }
    if(d->eff2==E_COND_BUFF && cumple_cond(me,d)){ P_+=d->q1; T_+=d->q2; }
    if(P_<=0) continue;
    /* cuenta bloqueadores que me matan sin morir, y los que intercambian */
    int lethalblk=0, tradeblk=0, poder_disponible=0, n_disponibles=0;
    for(int j=0;j<opp->nbf;j++){ Def*o=&D[opp->bf[j]];
      if(o->typ!=T_CREA||opp->tap[j]) continue;
      if((d->kw&K_FLY) && !((o->kw&K_FLY)||(o->kw&K_REA))) continue;
      int op=PWC(opp,j), ot=THC(opp,j);
      poder_disponible += op; n_disponibles++;
      int kills_me=(op>=T_)||(o->kw&K_DT);
      int i_kill=(P_>=ot)||(d->kw&K_DT);
      /* Dano primero e indestructible ya se tienen en cuenta al BLOQUEAR y no al
         ATACAR. La asimetria hace que el motor crea que va a morir en un combate que
         el mismo resolveria a su favor tres lineas mas abajo. Ablacion: KW_ATAQUE=0. */
      if(KW_ATAQUE){
        if((d->kw&K_FS) && !(o->kw&K_FS) && i_kill)   kills_me=0;  /* lo mato antes */
        if((o->kw&K_FS) && !(d->kw&K_FS) && kills_me) i_kill=0;    /* y al reves */
        if(d->kw&K_IND) kills_me=0;
        if(o->kw&K_IND) i_kill=0;
      }
      if(kills_me && !i_kill) lethalblk++;
      else if(kills_me && i_kill) tradeblk++;
    }
    /* el atacante DEBE prever el bloqueo en grupo: si entre varios lo matan
       y solo pierden una criatura, atacar es regalar la carta */
    int muere_por_grupo = GANG_ON && n_disponibles>=2 && poder_disponible>=T_;
    int minb_atk = (d->kw&K_MEN)?2:1;
    if(muere_por_grupo && n_disponibles>=minb_atk){
      /* cuantas de las suyas matan mis P_ puntos de dano repartidos */
      int resto=P_, mueren=0, usados=0;
      for(int j=0;j<opp->nbf && usados<3;j++){ Def*o=&D[opp->bf[j]];
        if(o->typ!=T_CREA||opp->tap[j]) continue;
        if((d->kw&K_FLY) && !((o->kw&K_FLY)||(o->kw&K_REA))) continue;
        int ot=THC(opp,j); usados++;
        if(resto>=ot || (d->kw&K_DT)){ mueren++; resto-=ot; }
      }
      if(mueren<=1) lethalblk++;      /* cambio malo: yo muero, el pierde <=1 */
    }
    int racing  = (opp->life <= P_*2) || (ncreat(opp)==0) || letal_agregado;
    int behind  = (me->life < opp->life - 6);
    /* AMENAZA: el defensor necesita minb_atk cuerpos para bloquear. Si no los tiene, el
       ataque no puede salir mal. Y con GANG_ON=0 el bloqueo en grupo ni siquiera existe
       —la rama de bloqueo simple exige minb==1—, asi que en este motor una criatura con
       amenaza es literalmente imbloqueable... y aun asi se quedaba en casa. */
    int imbloqueable = KW_ATAQUE &&
                       (n_disponibles < minb_atk || (!GANG_ON && minb_atk > 1));
    /* CADA criatura bloquea a UN atacante. Si ya declare tantos atacantes como
       bloqueadores pueden pararme, este pasa si o si y da igual que lo maten: no queda
       nadie libre para bloquearlo.

       Sin esto, cada criatura decidia por su cuenta mirando si EXISTE un bloqueador que
       la mate, o sea razonando como si el defensor pudiera bloquearlas a todas, y un
       ejercito entero se quedaba en casa ante un solo bloqueador grande. Medido en
       sintetico: 24 criaturas 1/1 con prisa contra 16 muros 3/3 con defensor daban 0%
       de winrate y CERO danio en 20 turnos; contra muros 0/3, que no las matan, el
       mismo mazo ganaba el 100% en 7,4 turnos.

       n_disponibles ya respeta volar, asi que sirve mejor que def_untapped, que cuenta
       a todos. Ablacion: BLOQ_LIBRE=0. */
    int hay_bloqueador_libre = (na < n_disponibles);
    if((BLOQ_LIBRE && !hay_bloqueador_libre) || imbloqueable) { /* nadie puede pararlo */ }
    else {
      if(lethalblk>0 && !racing) continue;              /* no regalar criaturas */
      if(tradeblk>0 && !racing && !behind && d->cmc >= 4) continue; /* no cambiar mi bomba por su 2-drop */
    }
    atk[na++]=i;
    if(!(d->kw&K_VIG)) me->tap[i]=1;
  }
  if(!na) return;

  int total=0; for(int k=0;k<na;k++) total+=PWC(me,atk[k]);

  /* --- bloqueos: el defensor intercambia Y puede bloquear en grupo --- */
  int blk[BFMAX][3]; int nblk[BFMAX];
  for(int k=0;k<na;k++){ nblk[k]=0; blk[k][0]=blk[k][1]=blk[k][2]=-1; }
  uint8_t usedb[BFMAX]; memset(usedb,0,opp->nbf);
  int incoming = total;
  int order[BFMAX]; for(int k=0;k<na;k++) order[k]=k;
  for(int a=0;a<na;a++) for(int b=a+1;b<na;b++)
    if(pw(me,atk[order[b]]) > pw(me,atk[order[a]])){ int t=order[a];order[a]=order[b];order[b]=t; }

  for(int oi=0;oi<na;oi++){
    int k=order[oi];
    int i=atk[k]; Def*d=&D[me->bf[i]];
    int P_=PWC(me,i), T_=THC(me,i);
    if(d->eff==E_COND_BUFF && cumple_cond(me,d)){ P_+=d->p1; T_+=d->p2; }
    if(d->eff2==E_COND_BUFF && cumple_cond(me,d)){ P_+=d->q1; T_+=d->q2; }
    int lethal_now = (incoming >= opp->life);
    int pressure = 0;
    if(opp->life<=5) pressure=14; else if(opp->life<=10) pressure=8; else if(opp->life<=15) pressure=4;

    /* candidatos legales */
    int cand[BFMAX], nc=0;
    for(int j=0;j<opp->nbf;j++){ Def*o=&D[opp->bf[j]];
      if(o->typ!=T_CREA||opp->tap[j]||usedb[j]) continue;
      if((d->kw&K_FLY) && !((o->kw&K_FLY)||(o->kw&K_REA))) continue;
      cand[nc++]=j;
    }
    int minb = (d->kw&K_MEN) ? 2 : 1;
    if(nc < minb) continue;

    /* 1) el bloqueo individual mas rentable */
    int best=-1,bs=-1000;
    for(int q=0;q<nc;q++){ int j=cand[q]; Def*o=&D[opp->bf[j]];
      int op=PWC(opp,j), ot=THC(opp,j);
      int kills=(op>=T_)||(o->kw&K_DT);
      int dies =(P_>=ot)||(d->kw&K_DT);
      if((d->kw&K_FS) && !(o->kw&K_FS) && (P_>=ot)) kills=0;
      int v;
      if(kills && !dies)      v = TH_PERFECT + o->cmc;
      else if(kills && dies)  v = TH_TRADE + (d->cmc - o->cmc)*3;
      else if(!kills && !dies)v = TH_WALL;
      else                    v = TH_BADBLOCK + (d->cmc - o->cmc)*2;
      v += pressure + P_;
      if(lethal_now) v += 60;
      if(o->eff==E_LORD||o->eff==E_ENGINE||o->eff==E_EXILE_ENGINE) v -= 10;
      if(v>bs){bs=v;best=q;}
    }

    /* 2) bloqueo en GRUPO: si ninguno lo mata solo, junta hasta 3 que si lo maten.
          Es como los mazos de criaturas pequenas responden a una amenaza gorda. */
    int gang[3], ng=0, gangval=-1000;
    {
      /* ordena candidatos por poder descendente para matar con los menos posibles */
      int ord[BFMAX]; for(int q=0;q<nc;q++) ord[q]=cand[q];
      for(int a2=0;a2<nc;a2++) for(int b2=a2+1;b2<nc;b2++)
        if(pw(opp,ord[b2]) > pw(opp,ord[a2])){ int t=ord[a2];ord[a2]=ord[b2];ord[b2]=t; }
      int acc=0, take[3], nt=0;
      for(int q=0;q<nc && nt<3;q++){
        int j=ord[q]; acc += PWC(opp,j); take[nt++]=j;
        if(acc>=T_ || (D[opp->bf[j]].kw&K_DT)) break;
      }
      int mata = (acc>=T_);
      for(int q=0;q<nt;q++) if(D[opp->bf[take[q]]].kw&K_DT) mata=1;
      if(GANG_ON && nt>=minb && mata && nt>1){
        /* cuanto pierdo: el atacante reparte su dano entre los bloqueadores */
        int perdidos=0, resto=P_, coste=0;
        for(int q=0;q<nt;q++){ int j=take[q];
          int ot=THC(opp,j);
          if(resto>=ot || (d->kw&K_DT)){ perdidos++; coste += D[opp->bf[j]].cmc; resto-=ot; }
        }
        gangval = GANG_BASE - perdidos*7 - coste + pressure + P_/2;
        if(lethal_now) gangval += 60;
        if(gangval > bs){ ng=nt; for(int q=0;q<nt;q++) gang[q]=take[q]; }
      }
    }

    if(ng>0){
      for(int q=0;q<ng;q++){ blk[k][q]=gang[q]; usedb[gang[q]]=1; }
      nblk[k]=ng; incoming -= P_;
    } else if(best>=0 && bs>0 && minb==1){
      blk[k][0]=cand[best]; usedb[cand[best]]=1; nblk[k]=1; incoming -= P_;
    }
  }

  /* --- resolucion: marcar muertes, aplicar despues --- */
  uint8_t deadA[BFMAX], deadB[BFMAX];
  memset(deadA,0,me->nbf); memset(deadB,0,opp->nbf);
  for(int k=0;k<na;k++){
    int i=atk[k]; Def*d=&D[me->bf[i]];
    int P_=PWC(me,i), T_=THC(me,i);
    if(d->eff==E_COND_BUFF && cumple_cond(me,d)){ P_+=d->p1; T_+=d->p2; }
    if(d->eff2==E_COND_BUFF && cumple_cond(me,d)){ P_+=d->q1; T_+=d->q2; }
    if(nblk[k]==0){
      if(d->eff==E_ATTACK_DMG) opp->life -= d->p1;
      if(d->eff2==E_ATTACK_DMG) opp->life -= d->q1;
      if(d->eff==E_ATTACK_DRAW||d->eff2==E_ATTACK_DRAW){ draw(me,1); me->life--; }
      apply_atk(me,opp,me->bf[atk[k]]);
      int dmg=P_; if(d->kw&K_DS) dmg*=2;
      opp->life-=dmg;
      if(d->kw&K_LL) me->life+=dmg;
      if(d->eff==E_DRAW_ON_DMG||d->eff2==E_DRAW_ON_DMG) draw(me,1);
    } else {
      if(d->eff==E_ATTACK_DMG) opp->life -= d->p1;
      if(d->eff2==E_ATTACK_DMG) opp->life -= d->q1;
      if(d->eff==E_ATTACK_DRAW||d->eff2==E_ATTACK_DRAW){ draw(me,1); me->life--; }
      apply_atk(me,opp,me->bf[atk[k]]);
      int resto=P_, total_bloq=0, ll=0;
      for(int q=0;q<nblk[k];q++){
        int j=blk[k][q]; Def*o=&D[opp->bf[j]];
        int op=PWC(opp,j), ot=THC(opp,j);
        total_bloq += op;
        /* el atacante reparte su dano en orden */
        int asigna = (resto>=ot)? ot : resto;
        if(d->kw&K_DT) asigna = (resto>0)? 1 : 0;
        int muere_bloq = (asigna>=ot) || ((d->kw&K_DT)&&asigna>0);
        if((o->kw&K_FS)&&!(d->kw&K_FS)&&((op>=T_))) muere_bloq=0;   /* pega antes */
        if(muere_bloq && !(o->kw&K_IND)) deadB[j]=1;
        resto -= asigna; if(resto<0) resto=0;
        ll += asigna;
      }
      if((d->kw&K_TRA) && resto>0) opp->life -= resto;
      if(d->kw&K_LL) me->life += P_;
      int muere_atk = (total_bloq>=T_);
      for(int q=0;q<nblk[k];q++) if(D[opp->bf[blk[k][q]]].kw&K_DT) muere_atk=1;
      if((d->kw&K_FS)){ int algun_fs=0; for(int q=0;q<nblk[k];q++) if(D[opp->bf[blk[k][q]]].kw&K_FS) algun_fs=1;
        if(!algun_fs){ int todos=1; for(int q=0;q<nblk[k];q++) if(!deadB[blk[k][q]]) todos=0;
          if(todos) muere_atk=0; } }
      if(muere_atk && !(d->kw&K_IND)) deadA[i]=1;
    }
  }
  for(int j=opp->nbf-1;j>=0;j--) if(deadB[j]) rmbf(opp,j);
  for(int i=me->nbf-1;i>=0;i--)  if(deadA[i]) rmbf(me,i);
}

/* ---- traza de tablero en JSON (TRACE_JSON=1) ----
   Emite el estado completo al final de cada turno para que src/tablero.py lo reproduzca.
   Solo van indices de def: los nombres los pone Python desde R.meta. Va a stderr con
   prefijo @J para no mezclarse con la salida normal del motor. */
static void tj_lado(P*p, const char*n){
  fprintf(stderr,"\"%s\":{\"life\":%d,\"hand\":%d,\"deck\":%d,\"lands\":[",
          n, p->life, p->nh, p->nd);
  for(int i=0;i<p->nl;i++)
    fprintf(stderr,"%s[%d,%d]", i?",":"", p->lands[i], p->ltap[i]?1:0);
  fprintf(stderr,"],\"bf\":[");
  for(int i=0;i<p->nbf;i++)
    fprintf(stderr,"%s[%d,%d,%d,%d,%d]", i?",":"", p->bf[i], p->tap[i]?1:0,
            pw(p,i), th(p,i), p->sick[i]?1:0);
  fprintf(stderr,"]}");
}
static void tj_turno(int turn, const char*act, P*a, P*b){
  fprintf(stderr,"@J {\"t\":%d,\"act\":\"%s\",", turn, act);
  tj_lado(a,"A"); fprintf(stderr,","); tj_lado(b,"B"); fprintf(stderr,"}\n");
}

static void upkeep(P*me,P*opp){
  for(int i=0;i<me->nbf;i++){ Def*d=&D[me->bf[i]];
    if(d->eff==E_UPKEEP_DRAIN){ opp->life-=d->p1; me->life+=d->p1; }
    if(d->eff==E_ENGINE) draw(me,1);
    if(d->eff==E_UPKEEP_DRAW){ draw(me,d->p1); me->life -= 1; }
    /* OJO: el robo recurrente tambien puede caer en la ranura secundaria (The Arkenstone,
       Haliya: LORD en eff + motor de robo en eff2). Leer solo eff dejaba el motor muerto.
       Sin perdida de vida: esa es la pega de Dark Confidant, no de estas cartas. Medido:
       con perdida 2.566 (peor), sin perdida 2.542 (mejor). Ver out/obj_eff2.txt. */
    if(d->eff2==E_UPKEEP_DRAW){ draw(me,d->q1); } }
}

static P *PA=0,*PB=0;
static int CMD_A=-1, CMD_B=-1;
static int CMD_OF(P*p){ return (p==PA)?CMD_A:((p==PB)?CMD_B:-1); }

/* ---------- diagnostico ---------- */
static void stats_reset(void){ ST_games=ST_mull=ST_screw=ST_spells6=ST_firstplay=ST_turns=0;
  ST_cast=ST_counter_used=ST_counter_seen=ST_removal=ST_kills=ST_sweep=0;
  ST_gamelen=ST_draw=ST_manaflood=ST_manascrew=ST_handend=ST_lifeend=0; ST_turns_dbg=0;
  ST_win_dmg=ST_lose_dmg=ST_timeout=ST_deck=0;
  ST_disc_try=ST_disc_hit=ST_disc_handsz=0;
  for(int i=0;i<16;i++){ST_hA[i]=0;ST_hB[i]=0;ST_hn[i]=0;}
  for(int i=0;i<9;i++){ST_noplay[i]=0;ST_play[i]=0;} }

/* ---------- partida ---------- */
static int play_game_inner(const int*d1,int n1,const int*d2,int n2,int life,int maxturn,int onplay){
  P A,B; memset(&A,0,sizeof A); memset(&B,0,sizeof B);
  A.life=B.life=life; A.army=B.army=-1; PA=&A; PB=&B; OPP_OF_A=&A; OPP_OF_B=&B; PLAYER_A=(void*)&A;
  memcpy(A.deck,d1,n1*sizeof(int)); A.nd=n1;
  memcpy(B.deck,d2,n2*sizeof(int)); B.nd=n2;
  /* mulligan de Londres: robas 7 siempre, pero devuelves N cartas al fondo */
  for(int side=0; side<2; side++){
    P*p = side? &B : &A;
    int mulls=0;
    for(; mulls<3; mulls++){
      shuffle(p); p->nh=0;
      for(int i=0;i<7;i++) p->hand[p->nh++]=p->deck[--p->nd];
      if(keepable(p, 7-mulls)) break;
      for(int i=0;i<p->nh;i++) p->deck[p->nd++]=p->hand[i];
      p->nh=0;
    }
    if(p->nh==0){ shuffle(p); for(int i=0;i<7;i++) p->hand[p->nh++]=p->deck[--p->nd]; }
    /* devolver al fondo: las mas caras primero (lo que haria un jugador) */
    (void)0;
    for(int k=0;k<mulls && p->nh>1;k++){
      int worst=0;
      for(int i=1;i<p->nh;i++) if(D[p->hand[i]].cmc > D[p->hand[worst]].cmc) worst=i;
      int card=p->hand[worst];
      for(int i=worst;i<p->nh-1;i++) p->hand[i]=p->hand[i+1];
      p->nh--;
      /* al fondo de la biblioteca */
      for(int i=p->nd;i>0;i--) p->deck[i]=p->deck[i-1];
      p->deck[0]=card; p->nd++;
    }
  }
  if(CMD_A>=0 && A.nh<ZONEMAX) A.hand[A.nh++]=CMD_A;   /* zona de mando */
  if(CMD_B>=0 && B.nh<ZONEMAX) B.hand[B.nh++]=CMD_B;
  int taxA=0, taxB=0;
  P*cur=onplay?&A:&B, *oth=onplay?&B:&A;
  ST_games++;
  if(TRACE && ST_games==1) TRACE_ON=1; else TRACE_ON=0;
  /* TRACE_JSON=N traza las N primeras partidas, no solo la primera */
  if(TJ && ST_games<=TJ) TJ_ON=1; else TJ_ON=0;
  TJ_GAME = ST_games;
  if(TJ_ON) fprintf(stderr,"@J {\"juego\":%lld,\"salida\":\"%s\"}\n",
                    TJ_GAME, onplay?"A":"B");
  if(TRACE_ON) fprintf(stderr,"\n=== TRAZA (A juega %s) ===\n", onplay?"primero":"segundo");
  int myturn=0, firstplay=0, spells6=0, screwed=0;
  #define ACC() do{ ST_screw+=screwed; ST_spells6+=spells6; \
      ST_firstplay += (firstplay?firstplay:9); ST_turns+=myturn; \
      ST_gamelen+=myturn; ST_handend+=A.nh; ST_lifeend+=(A.life>0?A.life:0); \
      if(A.nl>=8) ST_manaflood++; if(A.nl<=2) ST_manascrew++; }while(0)
  for(int turn=1;turn<=maxturn*2;turn++){
    TJ_TURN = turn; turno_actual = turn;
    /* untap */
    for(int i=0;i<cur->nl;i++) cur->ltap[i]=0;
    for(int i=0;i<cur->nbf;i++){
      if(cur->frz[i]>0){ cur->frz[i]--; }                 /* sigue girado */
      else if(!D[cur->bf[i]].no_untap) cur->tap[i]=0;
      cur->sick[i]=0; }
    cur->played_land=0; cur->cards_drawn_turn=0;
    upkeep(cur,oth);
    if(oth->life<=0){ ACC(); if(oth==&B) ST_win_dmg++; else ST_lose_dmg++; return (oth==&B); }
    if(!(turn==1&&onplay)) draw(cur,1);
    if(cur->lost){ ACC(); ST_deck++; return (cur==&B); }
    int before = (cur==&A) ? A.nbf : 0;
    int hand_before = cur->nh;
    int untapped_before = untapped_count(cur);
    cast_phase(cur,oth,0);
    if(cur==&A){
      myturn++;
      int cast_now = hand_before - cur->nh - (cur->played_land?1:0);
      if(myturn<=8){
        if(cast_now<=0){
          ST_noplay[myturn]++;
          /* distingue: no tenia mana o no tenia carta jugable del color */
          int haveplayable=0;
          for(int i=0;i<cur->nh;i++){ Def*d=&D[cur->hand[i]];
            if(d->typ!=T_LAND && d->cmc<=untapped_before) haveplayable=1; }
          if(haveplayable) screwed=1;
        } else { ST_play[myturn]++; if(!firstplay) firstplay=myturn; }
      }
      if(myturn<=6) spells6 += (cast_now>0?cast_now:0);
      ST_cast += (cast_now>0?cast_now:0);
    }
    defender_instants(oth,cur);
    combat(cur,oth);
    cast_phase(cur,oth,1);
    if(cur==&A && myturn>=1 && myturn<16){ ST_hA[myturn]+=A.nh; ST_hB[myturn]+=B.nh; ST_hn[myturn]++; }
    if(TRACE_ON){
      int ca=0,cb=0,pa2=0,pb2=0;
      for(int i=0;i<A.nbf;i++) if(D[A.bf[i]].typ==T_CREA){ca++;pa2+=pw(&A,i);}
      for(int i=0;i<B.nbf;i++) if(D[B.bf[i]].typ==T_CREA){cb++;pb2+=pw(&B,i);}
      fprintf(stderr,"t%-3d %s | A vida %3d mano %2d tierras %2d cri %d(%d pod) perm %2d | "
                     "B vida %3d mano %2d tierras %2d cri %d(%d pod) perm %2d\n",
        turn, cur==&A?"A":"B", A.life,A.nh,A.nl,ca,pa2,A.nbf, B.life,B.nh,B.nl,cb,pb2,B.nbf);
    }
    if(TJ_ON) tj_turno(turn, cur==&A?"A":"B", &A, &B);
    (void)before;
    if(oth->life<=0){ ACC(); if(oth==&B) ST_win_dmg++; else ST_lose_dmg++;
      if(TJ_ON) fprintf(stderr,"@J {\"fin\":\"%s\",\"turno\":%d}\n", oth==&B?"A":"B", turn);
      return (oth==&B); }
    /* el mana flotante no sobrevive al turno; los Tesoros si */
    if(cur->flot){ cur->treasures -= cur->flot; if(cur->treasures<0) cur->treasures=0; cur->flot=0; }
    P*t=cur;cur=oth;oth=t;
  }
  ACC(); ST_timeout++;
  /* tiempo agotado: decide la posicion real, no solo las vidas.
     Un mazo de control estabilizado en 6 vidas con la mesa limpia y cartas en mano
     esta ganando, aunque el rival tenga 20. */
  int pa=0,pb=0;
  for(int i=0;i<A.nbf;i++) if(D[A.bf[i]].typ==T_CREA) pa+=pw(&A,i);
  for(int i=0;i<B.nbf;i++) if(D[B.bf[i]].typ==T_CREA) pb+=pw(&B,i);
  double sa = A.life*0.6 + pa*2.0 + A.nh*1.5 + A.nd*0.05;
  double sb = B.life*0.6 + pb*2.0 + B.nh*1.5 + B.nd*0.05;
  if(sa!=sb) return sa>sb;
  return A.life>=B.life;
}

static int play_game(const int*d1,int n1,const int*d2,int n2,int life,int maxturn,int onplay){
  return play_game_inner(d1,n1,d2,n2,life,maxturn,onplay);
}

/* ================= IO / driver =================
 * Protocolo por stdin:
 *   NDEF
 *   NDEF x: cmc typ colors produces gen hybrid p0 p1 p2 p3 p4 kw eff eff2 p1 p2 p3 q1 q2 power tough
 *   NOPP
 *   NOPP x: weight_milesimas ncards c1..cn
 *   NGAMES LIFE MAXTURN SEED
 *   NVAR
 *   NVAR x: ncards c1..cn
 * Salida: NVAR lineas "winrate_ppm"
 */
static int OPP[16][DECKMAX]; static int OPPN[16]; static int OPPW[16]; static int OPPCMD[16]; static int NOPP;

int main(void){
  if(scanf("%d",&NDEF)!=1) return 1;
  for(int i=0;i<NDEF;i++){
    Def*d=&D[i]; int kw,cmc,typ,col,prod,gen,hyb,pw_,th_;
    int p0,p1_,p2_,p3_,p4_,eff,eff2,a,b,c,q1,q2;
    scanf("%d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d",
      &cmc,&typ,&col,&prod,&gen,&hyb,&p0,&p1_,&p2_,&p3_,&p4_,&kw,&eff,&eff2,&a,&b,&c,&q1,&q2,&pw_);
    scanf("%d",&th_);
    int mo_=0,dy_=0,nu_=0,e3_=0,r1_=0,r2_=0,al_=0,an_=0,de_=0,dp_=0,ae_=0,ap_=0,ac_=0,cr_=0;
    int co_=0,lg_=0,ta_=0,eg_=0,ke_=0,kp_=0,cx_=0;
    int av_=0,ag_=0,avp_=0,ap0_=0,ap1_=0,ap2_=0,ap3_=0,ap4_=0;
    scanf("%d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d",&mo_,&dy_,&nu_,
          &e3_,&r1_,&r2_,&al_,&an_,&de_,&dp_,&ae_,&ap_,&ac_,&cr_,&co_,&lg_,&ta_,&eg_,&ke_,
          &kp_,&cx_);
    scanf("%d %d %d %d %d %d %d %d",&av_,&ag_,&avp_,&ap0_,&ap1_,&ap2_,&ap3_,&ap4_);
    unsigned int sb_=0,ls_=0,cs_=0;
    scanf("%u %u %u",&sb_,&ls_,&cs_);
    d->sub=sb_; d->lord_sub=ls_; d->cond_sub=cs_;
    d->atk_eff=(uint8_t)ke_; d->atk_p1=(int16_t)kp_; d->coste_extra=(uint8_t)cx_;
    d->adv_eff=(uint8_t)av_; d->adv_gen=(uint8_t)ag_; d->adv_p1=(int16_t)avp_;
    d->adv_pip[0]=(uint8_t)ap0_; d->adv_pip[1]=(uint8_t)ap1_; d->adv_pip[2]=(uint8_t)ap2_;
    d->adv_pip[3]=(uint8_t)ap3_; d->adv_pip[4]=(uint8_t)ap4_;
    d->cred=(uint8_t)cr_; d->cond=(uint8_t)co_; d->es_leg=(uint8_t)lg_;
    d->tax_atk=(uint8_t)ta_; d->entra_girada=(uint8_t)eg_;
    d->mana_out=(uint8_t)mo_; d->dyn=(uint8_t)dy_; d->no_untap=(uint8_t)nu_;
    d->eff3=(uint8_t)e3_; d->r1=(int16_t)r1_; d->r2=(int16_t)r2_;
    d->alt=(uint8_t)al_; d->altn=(uint8_t)an_;
    d->die_eff=(uint8_t)de_; d->die_p1=(int16_t)dp_;
    d->act_eff=(uint8_t)ae_; d->act_p1=(int16_t)ap_; d->act_cost=(uint8_t)ac_;
    d->cmc=cmc; d->typ=typ; d->colors=col; d->produces=prod; d->gen=gen; d->hybrid=hyb;
    d->pip[0]=p0;d->pip[1]=p1_;d->pip[2]=p2_;d->pip[3]=p3_;d->pip[4]=p4_;
    d->kw=kw; d->eff=eff; d->eff2=eff2; d->p1=a; d->p2=b; d->p3=c; d->q1=q1; d->q2=q2;
    d->power=pw_; d->tough=th_;
    d->score=defscore(d);
  }
  scanf("%d",&NOPP);
  for(int o=0;o<NOPP;o++){
    scanf("%d %d %d",&OPPW[o],&OPPCMD[o],&OPPN[o]);
    for(int i=0;i<OPPN[o];i++) scanf("%d",&OPP[o][i]);
  }
  int NG,LIFE,MT; unsigned long long SEED;
  scanf("%d %d %d %llu",&NG,&LIFE,&MT,&SEED); if(MT<20) MT=20;
  { const char*e1=getenv("PEN_NOTARGET"); if(e1) PEN_NOTARGET=atoi(e1);
    const char*e2=getenv("W_TARGET"); if(e2) W_TARGET=atoi(e2);
    const char*e3=getenv("DISABLE_EFF"); if(e3) DISABLE_EFF=atoi(e3);
    const char*bl=getenv("BLOQ_LIBRE"); if(bl) BLOQ_LIBRE=atoi(bl);
    const char*nd=getenv("NOTARGET_DURO"); if(nd) NOTARGET_DURO=atoi(nd);
    const char*mo=getenv("MUERTE_ON"); if(mo) MUERTE_ON=atoi(mo);
    const char*ao=getenv("ACTIVADAS_ON"); if(ao) ACTIVADAS_ON=atoi(ao);
    const char*fr=getenv("FICHAS_REALES"); if(fr) FICHAS_REALES=atoi(fr);
    const char*rl=getenv("REMATE_LETAL"); if(rl) REMATE_LETAL=atoi(rl);
    const char*al=getenv("ATAQUE_LETAL"); if(al) ATAQUE_LETAL=atoi(al);
    const char*ka=getenv("KW_ATAQUE");    if(ka) KW_ATAQUE=atoi(ka);
    const char*lv=getenv("LORD_VE");      if(lv) LORD_VE=atoi(lv);
    const char*co=getenv("CONDICIONES_OFF"); if(co&&atoi(co)) CONDICIONES_ON=0;
    const char*tg=getenv("TIERRA_GIRADA"); if(tg) TIERRA_GIRADA=atoi(tg);
    const char*aq=getenv("ATAQUE_OFF"); if(aq&&atoi(aq)) ATAQUE_ON=0;
    const char*ce=getenv("COSTE_EXTRA_ON"); if(ce) COSTE_EXTRA_ON=atoi(ce);
    const char*av=getenv("AVENTURA_OFF"); if(av&&atoi(av)) AVENTURA_ON=0;

    const char*e4=getenv("GANG_BASE"); if(e4) GANG_BASE=atoi(e4);
    const char*e5=getenv("GANG_ON"); if(e5) GANG_ON=atoi(e5);
    const char*e6=getenv("HEXWARD_ON"); if(e6) HEXWARD_ON=atoi(e6);
    const char*et=getenv("TRACE"); if(et) TRACE=atoi(et);
    const char*ej=getenv("TRACE_JSON"); if(ej) TJ=atoi(ej);
    const char*pn=getenv("POLNET"); if(pn && *pn) pn_cargar(pn);
    const char*pe=getenv("POLNET_ESCALA"); if(pe) PN_ESCALA=(float)atof(pe);
    const char*pl=getenv("POLNET_LADO"); if(pl) PN_LADO=atoi(pl);
    const char*ef=getenv("DMG_ANY_FACE"); if(ef) DMG_ANY_FACE=atoi(ef);
    const char*en=getenv("NEG_ON"); if(en) NEG_ON=atoi(en);
    const char*ep=getenv("W_PRESSURE"); if(ep) W_PRESSURE=atoi(ep);
    const char*ew=getenv("W_TARGET");   if(ew) W_TARGET=atoi(ew);
    const char*e7=getenv("WARD_COST");  if(e7) WARD_COST=atoi(e7);
    const char*p1=getenv("TH_TRADE"); if(p1) TH_TRADE=atoi(p1);
    const char*p2=getenv("TH_PERFECT"); if(p2) TH_PERFECT=atoi(p2);
    const char*p3=getenv("TH_WALL"); if(p3) TH_WALL=atoi(p3);
    const char*p4=getenv("TH_BADBLOCK"); if(p4) TH_BADBLOCK=atoi(p4);
    const char*p5=getenv("RESERVE_MAX"); if(p5) RESERVE_MAX=atoi(p5);
    const char*p6=getenv("SWEEP_MIN"); if(p6) SWEEP_MIN=atoi(p6);
    const char*p7=getenv("PEN_NOTARGET2"); if(p7) PEN_NOTARGET=atoi(p7); }
  if(DISABLE_EFF>0) for(int i=0;i<NDEF;i++){
    if(D[i].eff==DISABLE_EFF){ D[i].eff=D[i].eff2; D[i].p1=D[i].q1; D[i].p2=D[i].q2; D[i].eff2=D[i].eff3; }
    if(D[i].eff2==DISABLE_EFF) D[i].eff2=0;
    if(D[i].eff3==DISABLE_EFF) D[i].eff3=0;
    D[i].score=defscore(&D[i]);
  }
  int NV; scanf("%d",&NV);
  static int V[DECKMAX]; 
  for(int v=0;v<NV;v++){
    int n, vc; scanf("%d %d",&vc,&n);
    for(int i=0;i<n;i++) scanf("%d",&V[i]);
    CMD_A=vc;
    long long wsum=0, wtot=0; stats_reset();
    for(int o=0;o<NOPP;o++){
      int wins=0;
      for(int g=0;g<NG;g++){
        seed(SEED + (unsigned long long)o*1000003ULL + (unsigned long long)g*7919ULL);
        CMD_B=OPPCMD[o];
        wins += play_game(V,n,OPP[o],OPPN[o],LIFE,MT, g&1);
      }
      wsum += (long long)wins * OPPW[o];
      wtot += (long long)NG * OPPW[o];
    }
    double g = ST_games? (double)ST_games : 1.0;
    long long np=0; for(int k=1;k<=4;k++) np+=ST_noplay[k];
    printf("%lld %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f %.4f\n",
       wtot? (wsum*1000000LL)/wtot : 0LL,
       np/g, ST_screw/g, ST_spells6/g, ST_firstplay/g,
       ST_gamelen/g, ST_cast/g, ST_removal/g, ST_kills/g, ST_sweep/g,
       ST_counter_used/g, ST_handend/g, ST_manascrew/g, ST_counter_seen/g,
       ST_manaflood? (double)ST_draw/ST_manaflood : -1.0,
       ST_turns_dbg? (double)ST_lifeend/ST_turns_dbg : -1.0,
       ST_win_dmg/g, ST_lose_dmg/g, ST_timeout/g,
       ST_hn[3]?(double)ST_hA[3]/ST_hn[3]:-1.0, ST_hn[6]?(double)ST_hA[6]/ST_hn[6]:-1.0,
       ST_hn[9]?(double)ST_hA[9]/ST_hn[9]:-1.0,
       ST_hn[3]?(double)ST_hB[3]/ST_hn[3]:-1.0, ST_hn[6]?(double)ST_hB[6]/ST_hn[6]:-1.0,
       ST_hn[9]?(double)ST_hB[9]/ST_hn[9]:-1.0,
       ST_disc_try/g, ST_disc_hit/g,
       ST_disc_try?(double)ST_disc_handsz/ST_disc_try:-1.0);
  }
  return 0;
}
