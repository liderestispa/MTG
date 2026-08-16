"""Genera sim_brawl.c desde el sim.c actual + soporte de zona de mando."""
s = open('src/sim.c').read()

# comandante entra a la mano tras el mulligan
s = s.replace("""    /* devolver al fondo: las mas caras primero (lo que haria un jugador) */""",
"""    /* devolver al fondo: las mas caras primero (lo que haria un jugador) */
    (void)0;""")
s = s.replace("""  P*cur=onplay?&A:&B, *oth=onplay?&B:&A;
  ST_games++;""",
"""  if(CMD_A>=0 && A.nh<ZONEMAX) A.hand[A.nh++]=CMD_A;   /* zona de mando */
  if(CMD_B>=0 && B.nh<ZONEMAX) B.hand[B.nh++]=CMD_B;
  int taxA=0, taxB=0;
  P*cur=onplay?&A:&B, *oth=onplay?&B:&A;
  ST_games++;""")
# el comandante vuelve a la mano al morir, con impuesto
s = s.replace("""static void rmbf(P*p,int i){""",
"""static int CMD_OF(P*p);
static void rmbf(P*p,int i){""")
s = s.replace("""  for(int j=opp->nbf-1;j>=0;j--) if(deadB[j]) rmbf(opp,j);
  for(int i=me->nbf-1;i>=0;i--)  if(deadA[i]) rmbf(me,i);""",
"""  for(int j=opp->nbf-1;j>=0;j--) if(deadB[j]) rmbf(opp,j);
  for(int i=me->nbf-1;i>=0;i--)  if(deadA[i]) rmbf(me,i);""")
# el comandante vuelve a la zona de mando desde CUALQUIER salida del campo
s = s.replace("""static void rmbf(P*p,int i){
  p->nbf--;""",
"""static void rmbf(P*p,int i){
  { int dd=p->bf[i]; int c=CMD_OF(p);
    if(dd==c && c>=0 && p->nh<ZONEMAX) p->hand[p->nh++]=dd; }
  p->nbf--;""")
s = s.replace("""/* ---------- diagnostico ---------- */""",
"""static P *PA=0,*PB=0;
static int CMD_A, CMD_B;
static int CMD_OF(P*p){ return (p==PA)?CMD_A:((p==PB)?CMD_B:-1); }

/* ---------- diagnostico ---------- */""")
s = s.replace("""  A.life=B.life=life; A.army=B.army=-1;""",
"""  A.life=B.life=life; A.army=B.army=-1; PA=&A; PB=&B;""")
# protocolo con comandante
s = s.replace("static int OPP[16][DECKMAX]; static int OPPN[16]; static int OPPW[16]; static int NOPP;",
              "static int OPP[16][DECKMAX]; static int OPPN[16]; static int OPPW[16]; static int OPPCMD[16]; static int NOPP;")
s = s.replace("""    scanf("%d %d",&OPPW[o],&OPPN[o]);""","""    scanf("%d %d %d",&OPPW[o],&OPPCMD[o],&OPPN[o]);""")
s = s.replace("""    int n; scanf("%d",&n);
    for(int i=0;i<n;i++) scanf("%d",&V[i]);""",
"""    int n, vc; scanf("%d %d",&vc,&n);
    for(int i=0;i<n;i++) scanf("%d",&V[i]);
    CMD_A=vc;""")
s = s.replace("""        seed(SEED + (unsigned long long)o*1000003ULL + (unsigned long long)g*7919ULL);
        wins += play_game(V,n,OPP[o],OPPN[o],LIFE,MT, g&1);""",
"""        seed(SEED + (unsigned long long)o*1000003ULL + (unsigned long long)g*7919ULL);
        CMD_B=OPPCMD[o];
        wins += play_game(V,n,OPP[o],OPPN[o],LIFE,MT, g&1);""")
open('src/sim_brawl.c','w').write(s)
print("sim_brawl.c regenerado desde sim.c actual")
