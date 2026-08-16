import sys, os; sys.path.insert(0,'src')
from driver import build, run
fmt=sys.argv[1]; yo=sys.argv[2]; rival=sys.argv[3]
R,opps=build(fmt)
me=[o for o in opps if yo.lower() in o[0].lower()][0]
op=[o for o in opps if rival.lower() in o[0].lower()][0]
os.environ['TRACE']='1'
r=run(R,[(op[0],1000,op[2])],[me[2]],ngames=1,life=20,seed=int(sys.argv[4]) if len(sys.argv)>4 else 5)
print(f"\n{me[0]} vs {op[0]}: wr {r[0]['wr']*100:.0f}%")
