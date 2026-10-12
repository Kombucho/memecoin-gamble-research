"""1h-primary analysis on the 4,186 Solana calls with a 1h price. Run from anywhere: python scripts/analysis_1h.py"""
import json,glob,numpy as np
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from karma_data import DATA, DL, CHARTS, OUTPUTS, karma_files
OUT=DATA
r1=[];r24=[];peak=[]
for d in karma_files():
    for t in d.get("tokens",[]):
        if t.get("status")=="scored" and t.get("copy_return_24h") is not None and not t["mint"].startswith("0x") \
           and t.get("price_1h") is not None and t["market_price_at_entry"]:
            r1.append(t["price_1h"]/t["market_price_at_entry"]-1); r24.append(t["copy_return_24h"]); peak.append(t.get("copy_peak_multiple"))
r=np.array(r1); r24=np.array(r24); n=len(r); rs=np.sort(r)[::-1]
np.save(f"{OUTPUTS}/r1h.npy",r)
res={"n":n,"median":float(np.median(r)),"mean":float(r.mean()),"red":float((r<0).mean()),"down90":float((r<=-0.9).mean()),
     "up2x":float((r>=1).mean()),"up10x":float((r>=9).mean()),"mean_log":float(np.mean(np.log(np.maximum(1+r,1e-6)))),
     "max":float(r.max()),"top10":[float(x) for x in rs[:10]]}
k1=n//100
res["tail"]={"drop_top10":float(rs[10:].mean()),"drop_top1pct":float(rs[k1:].mean()),"top1pct_k":k1,
             "drop_all_10x":float(r[r<9].mean()),"n_10x":int((r>=9).sum()),
             "top1pct_share_of_gains":float(rs[:k1].sum()/r[r>0].sum()),"top10_share_of_gains":float(rs[:10].sum()/r[r>0].sum())}
res["drop_curve"]={int(k):float(rs[k:].mean()) for k in range(0,121)}
# where does mean cross zero / cost line
res["k_cross_zero"]=int(next(k for k in range(n) if rs[k:].mean()<0))
SOLPX=120.07
def side(protocol=0.015,terminal=0.0095,slip=0.01,prio=0.002,stake=100): return protocol+terminal+slip+prio*SOLPX/stake
SC={"cheap":(side(terminal=0,slip=0.005),0.0),"base":(side(),0.0),"base_late10":(side(),0.10)}
net=lambda x,c,p:(1+x)*(1-c)**2/(1+p)-1
res["scenarios"]={k:dict(side_cost=c,premium=p,mean=float(net(r,c,p).mean()),median=float(np.median(net(r,c,p))),
     mean_drop_top10=float(net(rs[10:],c,p).mean()),mean_drop_top1pct=float(net(rs[k1:],c,p).mean()),
     mean_drop_10x=float(net(r[r<9],c,p).mean())) for k,(c,p) in SC.items()}
res["k_cross_cost_base"]=int(next(k for k in range(n) if net(rs[k:],SC["base"][0],0).mean()<0))
mb=(1-SC["base"][0])**2
res["breakeven_premium"]={k:float((1+r.mean())*(1-c)**2-1) for k,(c,p) in SC.items() if p==0}
res["breakeven_premium_ex_top1pct"]=float((1+rs[k1:].mean())*mb-1)
res["kelly_growth"]={}
for f in [0.01,0.02,0.05,0.10]:
    res["kelly_growth"][f]=float(np.mean(np.log(np.maximum(1+f*net(r,SC["base"][0],0),1e-12))))
# EV buckets
edges=[("≤ −90%",None,-0.9),("−90% to −50%",-0.9,-0.5),("−50% to 0",-0.5,0),("0 to +100%",0,1),("2x to 10x",1,9),("≥ 10x",9,None)]
B=[]
for name,lo,hi in edges:
    m=np.ones(n,bool)
    if lo is not None: m&=r>lo
    if hi is not None: m&=r<=hi
    if hi is None: m=r>lo
    B.append(dict(bucket=name,p=float(m.mean()),mean_ret=float(r[m].mean()),contrib=float(m.mean()*r[m].mean())))
res["buckets"]=B
# TP at 2x: peak field is not 1h-bounded -> not computable
res["tp2x_1h"]="not computable: Karma stores one peak (copy_peak_multiple) with no 1h-bounded peak and no intra-hour path"
# Monte Carlo
rng=np.random.default_rng(20261012)
def mc(c,p,f=0.10,N=100,sims=100_000,B0=1000):
    R=net(r[rng.integers(0,n,size=(sims,N))],c,p); return B0*np.cumprod(1+f*R,axis=1)
res["mc"]={}
for k,(c,p) in SC.items():
    P=mc(c,p); E=P[:,-1]; s=np.sort(E)
    res["mc"][k]=dict(median_end=float(np.median(E)),mean_end=float(E.mean()),p_profit=float((E>1000).mean()),
       p_lose_half=float((E<500).mean()),p_ruin90=float((P.min(axis=1)<100).mean()),
       p5=float(np.percentile(E,5)),p25=float(np.percentile(E,25)),p75=float(np.percentile(E,75)),p95=float(np.percentile(E,95)),
       top1pct_share=float(s[-len(s)//100:].sum()/s.sum()))
    if k=="base": np.save(f"{OUTPUTS}/mc1h_base_paths_sample.npy",P[:2000])
res["sweep"]=[]
for f in [0.02,0.05,0.10,0.20,0.30,0.50]:
    P=mc(*SC["base"],f=f,sims=40_000); E=P[:,-1]
    res["sweep"].append(dict(f=f,median_end=float(np.median(E)),mean_end=float(E.mean()),p_profit=float((E>1000).mean()),p_ruin90=float((P.min(axis=1)<100).mean())))
# 24h on same calls (secondary)
r24s=np.sort(r24)[::-1]
res["cmp24h_same_calls"]=dict(median=float(np.median(r24)),mean=float(r24.mean()),red=float((r24<0).mean()),
   mean_base_costs=float(net(r24,SC["base"][0],0).mean()),drop_top10=float(r24s[10:].mean()))
P=None
json.dump(res,open(f"{OUT}/results_1h.json","w"),indent=1)
print(json.dumps({k:v for k,v in res.items() if k not in("drop_curve",)},indent=1))
