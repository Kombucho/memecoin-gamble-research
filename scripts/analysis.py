"""Memecoin-gamble thread: data extraction, EV math, Monte Carlo. Run from anywhere: python scripts/analysis.py"""
import json, glob, math, statistics as st, csv, datetime as dt
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from karma_data import DATA, DL, CHARTS, OUTPUTS, karma_files
import numpy as np
OUT=DATA
rows=[]
for d in karma_files():
    for t in d.get("tokens",[]):
        if t.get("status")=="scored" and t.get("copy_return_24h") is not None:
            rows.append(dict(wallet=d["wallet"],handle=d.get("handle"),mint=t["mint"],
              chain="evm" if t["mint"].startswith("0x") else "solana",
              r24=t["copy_return_24h"],peak=t.get("copy_peak_multiple"),label=t.get("label")))
# (karma_scored_calls.csv is the input snapshot in data/; not rewritten here)
allr=np.array([x["r24"] for x in rows]); sol=[x for x in rows if x["chain"]=="solana"]
r=np.array([x["r24"] for x in sol]); n=len(r)
res={"all_n":len(allr),"all_median":float(np.median(allr)),"all_mean":float(allr.mean()),
     "sol_n":n,"sol_unique_mints":len({x["mint"] for x in sol}),"sol_callers":len({x["wallet"] for x in sol}),
     "sol_median":float(np.median(r)),"sol_mean":float(r.mean()),"sol_neg":float((r<0).mean()),
     "sol_le_-90":float((r<=-0.9).mean()),"sol_le_-50":float((r<=-0.5).mean()),
     "sol_ge_2x":float((r>=1).mean()),"sol_ge_10x":float((r>=9).mean()),
     "sol_peak_ge_2x":float(np.mean([ (x["peak"] or 0)>=2 for x in sol])),
     "sol_mean_log":float(np.mean(np.log(np.maximum(1+r,1e-6)))),
     "sol_geo_per_call":float(math.exp(np.mean(np.log(np.maximum(1+r,1e-6))))) }
rs=np.sort(r)[::-1]
res["drop_topk_mean"]={k:float(rs[k:].mean()) for k in [0,1,3,5,10,20,43]}
res["top1pct_share_of_gains"]=float(rs[:n//100].sum()/r[r>0].sum())
res["top10_returns"]=[float(x) for x in rs[:10]]
# EV buckets
edges=[(-1.01,-0.9,"≤ −90%"),(-0.9,-0.5,"−90% to −50%"),(-0.5,0,"−50% to 0"),(0,1,"0 to +100%"),(1,9,"2x to 10x"),(9,1e9,"≥ 10x")]
buckets=[]
for lo,hi,name in edges:
    m=(r>lo)&(r<=hi) if lo>-1.01 else (r<=hi)
    if hi==1e9: m=r>lo
    p=float(m.mean()); mu=float(r[m].mean()) if m.any() else 0
    buckets.append(dict(bucket=name,p=p,mean_ret=mu,contrib=p*mu))
res["buckets"]=buckets; res["bucket_sum"]=sum(b["contrib"] for b in buckets)
# TP-at-2x discipline (optimistic: assumes fill exactly at 2x whenever peak>=2x)
tp=np.array([1.0 if (x["peak"] or 0)>=2 else x["r24"] for x in sol]); res["tp2x_mean"]=float(tp.mean()); res["tp2x_median"]=float(np.median(tp))
# costs
SOLPX=120.07  # Lookonchain, Oct 7 2026
def side_cost(protocol=0.015,terminal=0.0095,slip=0.01,prio_sol=0.002,stake=100):
    return protocol+terminal+slip+prio_sol*SOLPX/stake
SC={"cheap (pump app, 0.5% slip)":side_cost(terminal=0,slip=0.005),
    "base (Axiom Wood, 1% slip)":side_cost(),
    "base + 10% late-entry premium":side_cost()}
PREM={"cheap (pump app, 0.5% slip)":0,"base (Axiom Wood, 1% slip)":0,"base + 10% late-entry premium":0.10}
def net(r,c,prem): return (1+r)*(1-c)**2/(1+prem)-1
res["scenarios"]={}
for k,c in SC.items():
    nr=net(r,c,PREM[k]); res["scenarios"][k]=dict(side_cost=c,mean=float(nr.mean()),median=float(np.median(nr)),
        mean_ex_top10=float(net(rs[10:],c,PREM[k]).mean()))
mult_base=(1-SC["base (Axiom Wood, 1% slip)"])**2
res["breakeven_entry_premium_base"]=float((1+r.mean())*mult_base-1)
# Monte Carlo
rng=np.random.default_rng(20261012)
def mc(c,prem,f=0.10,N=100,sims=100_000,B0=1000):
    idx=rng.integers(0,n,size=(sims,N)); R=net(r[idx],c,prem)
    paths=B0*np.cumprod(1+f*R,axis=1); return paths
res["mc"]={}
for k,c in SC.items():
    P=mc(c,PREM[k]); E=P[:,-1]
    res["mc"][k]=dict(median_end=float(np.median(E)),mean_end=float(E.mean()),p_profit=float((E>1000).mean()),
        p_lose_half=float((E<500).mean()),p_ruin90=float((P.min(axis=1)<100).mean()),p5=float(np.percentile(E,5)),
        p95=float(np.percentile(E,95)),p99=float(np.percentile(E,99)),top1pct_share_of_wealth=float(np.sort(E)[-len(E)//100:].sum()/E.sum()))
    if k.startswith("base (Axiom"): np.save(f"{OUTPUTS}/mc_base_paths_sample.npy",P[:2000]); np.save(f"{OUTPUTS}/mc_base_end.npy",E)
# sizing sweep (base)
sweep=[]
for f in [0.02,0.05,0.10,0.20,0.30,0.50]:
    P=mc(SC["base (Axiom Wood, 1% slip)"],0,f=f,sims=40_000); E=P[:,-1]
    sweep.append(dict(f=f,median_end=float(np.median(E)),p_profit=float((E>1000).mean()),p_ruin90=float((P.min(axis=1)<100).mean())))
res["sweep"]=sweep
# Pump fees
def series(fn):
    d=json.load(open(f"{DL}/{fn}")); return [(dt.datetime.fromtimestamp(t,dt.UTC).date().isoformat(),v) for t,v in d["totalDataChart"]]
for key,fn in [("lp_fees","fees_pump.fun_dailyFees.json"),("lp_rev","fees_pump.fun_dailyRevenue.json"),("lp_hold","fees_pump.fun_dailyHoldersRevenue.json"),
               ("ps_fees","fees_pumpswap_dailyFees.json"),("ps_rev","fees_pumpswap_dailyRevenue.json"),("app_fees","fees_pump.fun-mobile-app_dailyFees.json")]:
    s=series(fn); res[key]=dict(total=sum(v for _,v in s),first=s[0][0],last=s[-1][0])
res["fees_total_lp_ps"]=res["lp_fees"]["total"]+res["ps_fees"]["total"]; res["rev_total_lp_ps"]=res["lp_rev"]["total"]+res["ps_rev"]["total"]
# first date cumulative launchpad revenue crossed $1B
cum=0
for d_,v in series("fees_pump.fun_dailyRevenue.json"):
    cum+=v
    if cum>=1e9: res["lp_rev_cross_1B"]=d_; break
json.dump(res,open(f"{OUT}/results.json","w"),indent=1,default=float)
print(json.dumps(res,indent=1,default=float))
