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

/* lord estatico: suma bonos de todas las criaturas/artefactos con E_LORD */
static void lordbonus(P*p,int*bp,int*bt){
  *bp=0;*bt=0;
  for(int i=0;i<p->nbf;i++){ Def*d=&D[p->bf[i]];
    if(d->eff==E_LORD){*bp+=d->p1;*bt+=d->p2;}
    if(d->eff2==E_LORD){*bp+=d->q1;*bt+=d->q2;} }
}

/* ---------- mana: comprueba si se puede pagar coste con tierras destapadas ---------- */
/* asignacion por backtracking pequeno: pips de color primero (los mas restringidos) */
static int pay_gen(P*p,Def*d){ return d->gen + (p->taxed>0 && d->typ!=T_LAND ? p->taxed : 0); }

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
    p->hand[p->nh++]=p->deck[best];
    for(int i=best;i<p->nd-1;i++) p->deck[i]=p->deck[i+1];
    p->nd--;
    p->cards_drawn_turn++;
  }
}
static void draw(P*p,int n){
  for(int i=0;i<n;i++){
    if(p->nd<=0){ p->lost=1; return; }
    p->hand[p->nh++]=p->deck[--p->nd];
    p->cards_drawn_turn++;
  }
}
static void shuffle(P*p){ for(int i=p->nd-1;i>0;i--){ int j=ri(i+1); int t=p->deck[i];p->deck[i]=p->deck[j];p->deck[j]=t; } }

static void addbf(P*p,int def){
  tj_ev("entra", p, def);
  if(D[def].typ==T_LAND){ if(p->nl<BFMAX){ p->lands[p->nl]=def; p->ltap[p->nl]=0; p->nl++; } return; }
  if(p->nbf>=BFMAX) return;
  int i=p->nbf++;
  p->bf[i]=def; p->tap[i]=0; p->ctr[i]=0; p->eqp[i]=0;
  p->sick[i] = (D[def].typ==T_CREA && !(D[def].kw&K_HAS)) ? 1 : 0;
}
static P *OPP_OF_A=0, *OPP_OF_B=0;
static void rmbf(P*p,int i){
  tj_ev("sale", p, p->bf[i]);
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
    if(th(p,i)>dmg) continue;
    int v=pw(p,i)*2+th(p,i);
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
    int v=pw(p,i)*2+th(p,i); if(D[p->bf[i]].kw&K_FLY) v+=3; if(D[p->bf[i]].kw&K_DT) v+=3;
    if(D[p->bf[i]].eff==E_LORD||D[p->bf[i]].eff==E_ENGINE) v+=6;
    if(v>bv){bv=v;best=i;} }
  return best;
}
/* dano por turno que me viene encima, descontando lo que pueden frenar mis bloqueadores */
static int board_pressure(P*me,P*opp){
  int dmg=0, blk=0;
  for(int i=0;i<opp->nbf;i++) if(D[opp->bf[i]].typ==T_CREA) dmg+=pw(opp,i);
  for(int i=0;i<me->nbf;i++)  if(D[me->bf[i]].typ==T_CREA && !(D[me->bf[i]].kw&K_DEF)) blk+=th(me,i);
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
static void mk_tokens(P*me,int proto,int count,int pwr,int tou){
  int m=token_mult(me); count*=m;
  for(int k=0;k<count && me->nbf<BFMAX;k++){
    int i=me->nbf++;
    me->bf[i]=proto; me->tap[i]=0; me->sick[i]=1; me->ctr[i]=0; me->eqp[i]=0;
  }
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
    case E_ETB_TOKEN: mk_tokens(me,def,a,(b>>4)&15,b&15); break;
    case E_TOKEN_SCALE: {
      /* Hare Apparent: fichas = numero de copias propias ya en mesa */
      int same=0; for(int i=0;i<me->nbf;i++) if(me->bf[i]==def) same++;
      if(same>1) mk_tokens(me,def,same-1,1,1);
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
    case E_MOBILIZE: mk_tokens(me,def,a,1,1); break;
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
      { int n=0; for(int i=0;i<opp->nbf;i++) if(D[opp->bf[i]].typ==T_CREA&&th(opp,i)<=a) n++;
        if(n>0) for(int q=0;q<me->nbf;q++)
          if(D[me->bf[q]].eff==E_EXILE_ENGINE){ draw_select(me,D[me->bf[q]].p1,3); me->life--; } }
      for(int i=opp->nbf-1;i>=0;i--)
        if(D[opp->bf[i]].typ==T_CREA && th(opp,i)<=a && !(D[opp->bf[i]].kw&K_IND)) rmbf(opp,i);
      for(int i=me->nbf-1;i>=0;i--)
        if(D[me->bf[i]].typ==T_CREA && th(me,i)<=a && !(D[me->bf[i]].kw&K_IND)) rmbf(me,i); } break;
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
    if(D[di].typ==T_CREA) addbf(def,di);
    SPARE_MANA = untapped_count(def);
    apply(def,act,di,0);
    if(D[di].eff2) apply(def,act,di,1);
  }
}

static void cast_phase(P*me,P*opp,int main2){
  ALT_OPP = opp;
  /* impuesto que me cobra el rival (Ghostly Prison y familia): encarece todo lo mio */
  me->taxed=0;
  for(int i=0;i<opp->nbf;i++){
    if(!NEG_ON) break;
    if(D[opp->bf[i]].eff ==E_TAX) me->taxed += D[opp->bf[i]].p1;
    if(D[opp->bf[i]].eff2==E_TAX) me->taxed += D[opp->bf[i]].q1;
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
      for(int k=best;k<me->nh-1;k++) me->hand[k]=me->hand[k+1]; me->nh--; }
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
        int es_rem = (d->eff==E_DESTROY||d->eff==E_EXILE||d->eff==E_DMG_SPELL||d->eff==E_ETB_DMG);
        if(es_rem && d->typ!=T_CREA){
          int t = (d->eff==E_DESTROY||d->eff==E_EXILE) ? biggest_threat(opp)
                                                       : best_killable(opp,d->p1);
          if(t<0) v -= PEN_NOTARGET;                        /* nada que matar */
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
    for(int k=best;k<me->nh-1;k++) me->hand[k]=me->hand[k+1]; me->nh--;
    paycost(me,&D[def],&me->treasures);
    tj_ev("lanza", me, def);
    SPARE_MANA = untapped_count(me);
    Def*d=&D[def];
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

static void combat(P*me,P*opp){
  int bp,bt; lordbonus(me,&bp,&bt);
  int obp,obt; lordbonus(opp,&obp,&obt);
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
  for(int i=0;i<me->nbf;i++){
    Def*d=&D[me->bf[i]];
    if(d->typ!=T_CREA||me->sick[i]||me->tap[i]||(d->kw&K_DEF)) continue;
    int P_=pw(me,i)+bp, T_=th(me,i)+bt;
    if(d->eff==E_COND_BUFF){ P_+=d->p1; T_+=d->p2; }
    if(d->eff2==E_COND_BUFF){ P_+=d->q1; T_+=d->q2; }
    if(P_<=0) continue;
    /* cuenta bloqueadores que me matan sin morir, y los que intercambian */
    int lethalblk=0, tradeblk=0, poder_disponible=0, n_disponibles=0;
    for(int j=0;j<opp->nbf;j++){ Def*o=&D[opp->bf[j]];
      if(o->typ!=T_CREA||opp->tap[j]) continue;
      if((d->kw&K_FLY) && !((o->kw&K_FLY)||(o->kw&K_REA))) continue;
      int op=pw(opp,j)+obp, ot=th(opp,j)+obt;
      poder_disponible += op; n_disponibles++;
      int kills_me=(op>=T_)||(o->kw&K_DT);
      int i_kill=(P_>=ot)||(d->kw&K_DT);
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
        int ot=th(opp,j)+obt; usados++;
        if(resto>=ot || (d->kw&K_DT)){ mueren++; resto-=ot; }
      }
      if(mueren<=1) lethalblk++;      /* cambio malo: yo muero, el pierde <=1 */
    }
    int racing  = (opp->life <= P_*2) || (ncreat(opp)==0);
    int behind  = (me->life < opp->life - 6);
    if(lethalblk>0 && !racing) continue;              /* no regalar criaturas */
    if(tradeblk>0 && !racing && !behind && d->cmc >= 4) continue; /* no cambiar mi bomba por su 2-drop */
    atk[na++]=i;
    if(!(d->kw&K_VIG)) me->tap[i]=1;
  }
  if(!na) return;

  int total=0; for(int k=0;k<na;k++) total+=pw(me,atk[k])+bp;

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
    int P_=pw(me,i)+bp, T_=th(me,i)+bt;
    if(d->eff==E_COND_BUFF){ P_+=d->p1; T_+=d->p2; }
    if(d->eff2==E_COND_BUFF){ P_+=d->q1; T_+=d->q2; }
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
      int op=pw(opp,j)+obp, ot=th(opp,j)+obt;
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
        int j=ord[q]; acc += pw(opp,j)+obp; take[nt++]=j;
        if(acc>=T_ || (D[opp->bf[j]].kw&K_DT)) break;
      }
      int mata = (acc>=T_);
      for(int q=0;q<nt;q++) if(D[opp->bf[take[q]]].kw&K_DT) mata=1;
      if(GANG_ON && nt>=minb && mata && nt>1){
        /* cuanto pierdo: el atacante reparte su dano entre los bloqueadores */
        int perdidos=0, resto=P_, coste=0;
        for(int q=0;q<nt;q++){ int j=take[q];
          int ot=th(opp,j)+obt;
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
    int P_=pw(me,i)+bp, T_=th(me,i)+bt;
    if(d->eff==E_COND_BUFF){ P_+=d->p1; T_+=d->p2; }
    if(d->eff2==E_COND_BUFF){ P_+=d->q1; T_+=d->q2; }
    if(nblk[k]==0){
      if(d->eff==E_ATTACK_DMG) opp->life -= d->p1;
      if(d->eff2==E_ATTACK_DMG) opp->life -= d->q1;
      if(d->eff==E_ATTACK_DRAW||d->eff2==E_ATTACK_DRAW){ draw(me,1); me->life--; }
      int dmg=P_; if(d->kw&K_DS) dmg*=2;
      opp->life-=dmg;
      if(d->kw&K_LL) me->life+=dmg;
      if(d->eff==E_DRAW_ON_DMG||d->eff2==E_DRAW_ON_DMG) draw(me,1);
    } else {
      if(d->eff==E_ATTACK_DMG) opp->life -= d->p1;
      if(d->eff2==E_ATTACK_DMG) opp->life -= d->q1;
      if(d->eff==E_ATTACK_DRAW||d->eff2==E_ATTACK_DRAW){ draw(me,1); me->life--; }
      int resto=P_, total_bloq=0, ll=0;
      for(int q=0;q<nblk[k];q++){
        int j=blk[k][q]; Def*o=&D[opp->bf[j]];
        int op=pw(opp,j)+obp, ot=th(opp,j)+obt;
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
  A.life=B.life=life; A.army=B.army=-1; OPP_OF_A=&A; OPP_OF_B=&B; PLAYER_A=(void*)&A;
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
static int OPP[16][DECKMAX]; static int OPPN[16]; static int OPPW[16]; static int NOPP;

int main(void){
  if(scanf("%d",&NDEF)!=1) return 1;
  for(int i=0;i<NDEF;i++){
    Def*d=&D[i]; int kw,cmc,typ,col,prod,gen,hyb,pw_,th_;
    int p0,p1_,p2_,p3_,p4_,eff,eff2,a,b,c,q1,q2;
    scanf("%d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d",
      &cmc,&typ,&col,&prod,&gen,&hyb,&p0,&p1_,&p2_,&p3_,&p4_,&kw,&eff,&eff2,&a,&b,&c,&q1,&q2,&pw_);
    scanf("%d",&th_);
    int mo_=0,dy_=0,nu_=0,e3_=0,r1_=0,r2_=0,al_=0,an_=0;
    scanf("%d %d %d %d %d %d %d %d",&mo_,&dy_,&nu_,&e3_,&r1_,&r2_,&al_,&an_);
    d->mana_out=(uint8_t)mo_; d->dyn=(uint8_t)dy_; d->no_untap=(uint8_t)nu_;
    d->eff3=(uint8_t)e3_; d->r1=(int16_t)r1_; d->r2=(int16_t)r2_;
    d->alt=(uint8_t)al_; d->altn=(uint8_t)an_;
    d->cmc=cmc; d->typ=typ; d->colors=col; d->produces=prod; d->gen=gen; d->hybrid=hyb;
    d->pip[0]=p0;d->pip[1]=p1_;d->pip[2]=p2_;d->pip[3]=p3_;d->pip[4]=p4_;
    d->kw=kw; d->eff=eff; d->eff2=eff2; d->p1=a; d->p2=b; d->p3=c; d->q1=q1; d->q2=q2;
    d->power=pw_; d->tough=th_;
    d->score=defscore(d);
  }
  scanf("%d",&NOPP);
  for(int o=0;o<NOPP;o++){
    scanf("%d %d",&OPPW[o],&OPPN[o]);
    for(int i=0;i<OPPN[o];i++) scanf("%d",&OPP[o][i]);
  }
  int NG,LIFE,MT; unsigned long long SEED;
  scanf("%d %d %d %llu",&NG,&LIFE,&MT,&SEED); if(MT<20) MT=20;
  { const char*e1=getenv("PEN_NOTARGET"); if(e1) PEN_NOTARGET=atoi(e1);
    const char*e2=getenv("W_TARGET"); if(e2) W_TARGET=atoi(e2);
    const char*e3=getenv("DISABLE_EFF"); if(e3) DISABLE_EFF=atoi(e3);
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
    int n; scanf("%d",&n);
    for(int i=0;i<n;i++) scanf("%d",&V[i]);
    long long wsum=0, wtot=0; stats_reset();
    for(int o=0;o<NOPP;o++){
      int wins=0;
      for(int g=0;g<NG;g++){
        seed(SEED + (unsigned long long)o*1000003ULL + (unsigned long long)g*7919ULL);
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
