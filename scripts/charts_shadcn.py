"""All thread images in shadcn/ui card style. 1h primary, 24h secondary (same 4,186 calls). Run from anywhere: python scripts/charts_shadcn.py"""
import json,glob,datetime as dt,sys
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from karma_data import DATA, DL, CHARTS, OUTPUTS, karma_files
import numpy as np
from shadcn_style import *
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
D=DATA; O=CHARTS
R=json.load(open(f"{D}/results_1h.json")); S=json.load(open(f"{D}/stats_1h_24h.json"))
H=S["1h"]; M=S["24h_matched_to_1h"]
# returns
r1=[];r24=[]
for d in karma_files():
    for t in d.get("tokens",[]):
        if t.get("status")=="scored" and t.get("copy_return_24h") is not None and not t["mint"].startswith("0x") and t.get("price_1h") is not None and t["market_price_at_entry"]:
            r1.append(t["price_1h"]/t["market_price_at_entry"]-1); r24.append(t["copy_return_24h"])
r1=np.array(r1); r24=np.array(r24); assert len(r1)==R["n"]==4186
KS=("Source: Karma open dataset (github.com/Kombucho/karma), snapshot Sep 16–Oct 3, 2026 · GeckoTerminal 15-min candles · 4,186 scored Solana calls with a 1h price.\n"
    "Return = price 1h (or 24h) after the call ÷ market price at the call. Gross: no fees, slippage or tips.")
COST="Costs per side 3.69%: pumpdotfun curve fee ~1.5% (DefiLlama, Sep 2026) + Axiom 0.95% + 1% slippage (assumption) + 0.002 SOL tips on a $100 trade."
pct0=lambda v,_=None:f"{v:+.0f}%".replace("+0%","0%").replace("-","−")
def mfmt(v): return f"{v*100:+.1f}%".replace("-","−")

# ---------- 1: outcome distribution (1h bars, 24h ghost) ----------
c=Card(800,450,"Where copied calls are 1 hour later","Share of 4,186 copied Solana calls in each return bucket · 1h (bars) vs 24h (outline)",
       "Gain buckets carry all of the gross average. EV contribution per bucket shown under each label (1h).",KS)
ax=c.axes(left=48,bottom=c.content_bottom+44)
B1=R["buckets"]; B24=M["buckets"]; x=np.arange(6)
ax.set_xlim(-0.6,5.6); ax.set_ylim(0,42)
for i,(a,b) in enumerate(zip(B1,B24)):
    rounded_bar(ax,i-0.13,a["p"]*100,0.34,RED if i<3 else EMR,r_px=5)
    ax.bar(i+0.21,b["p"]*100,0.26,fc="none",ec=Z["600"],lw=1*PT,zorder=2)
    c.fig.canvas.draw()
    ax.text(i-0.13,a["p"]*100+1.2,f"{a['p']*100:.1f}%",ha="center",fontproperties=F["semi"],fontsize=10*PT,color=Z["50"])
ax.set_xticks(x); ax.set_xticklabels([b["bucket"] for b in B1]); ax.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f"{v:.0f}%"))
c.ticks(ax)
for i,a in enumerate(B1):
    xx=c.m+48+(i+0.6)/6.2*(c.W-c.m*2-48-28)
    c.text(xx,c.content_bottom+8,f"EV {a['contrib']*100:+.1f} pts".replace("-","−"),9,"mono",EMR if a["contrib"]>0 else RED,ha="center")
c.badge(c.W-c.m-c.pad,c.H-c.m-c.pad-8,"1h median −12.6% · 24h −50.3%",9.5,ha="right")
c.save(f"{O}/memecoin-1-outcome-distribution.png")

# ---------- table helper ----------
def table(c,top,cols,xs,aligns,rows,rowh,colors,bold=()):
    y=top
    for t,xx,a in zip(cols,xs,aligns):
        if isinstance(t,tuple): c.badge(xx,y,t[0],10,ha=a,fg=t[1],bg=t[2],ec=t[3])
        else: c.text(xx,y,t,10.5,"med",Z["500"],ha=a,va="center")
    y-=rowh*0.55
    c.fig.add_artist(plt.Line2D([c.fx(c.m+c.pad),c.fx(c.W-c.m-c.pad)],[c.fy(y),c.fy(y)],color=Z["800"],lw=1*PT))
    y-=rowh*0.5
    for i,row in enumerate(rows):
        for j,(v,xx,a) in enumerate(zip(row,xs,aligns)):
            w="semi" if (i in bold and j) else ("reg" if j==0 else "med")
            c.text(xx,y,v,12.5 if j else 12.5,w,colors[i][j],ha=a,va="center")
        if i<len(rows)-1:
            ly=y-rowh/2; c.fig.add_artist(plt.Line2D([c.fx(c.m+c.pad),c.fx(c.W-c.m-c.pad)],[c.fy(ly),c.fy(ly)],color=Z["800"],lw=0.8*PT))
        y-=rowh
    return y
B1H=("1h",Z["50"],"#172554",ACC); B24H=("24h",Z["400"],Z["900"],Z["800"])

# ---------- 1b results table ----------
c=Card(800,500,"What copying a call gets you","Typical outcome of 4,186 copied Solana calls, 1 hour vs 24 hours after the call (same calls)",
       "1h is the primary view: memecoin trades are in and out fast. 24h shown for comparison.",KS)
L=c.m+c.pad; xs=[L,560,c.W-c.m-c.pad]
rows=[["Median return",mfmt(H["median"]),mfmt(M["median"])],["Calls in the red",f"{H['red']*100:.1f}%",f"{M['red']*100:.1f}%"],
      ["Down 90% or more",f"{H['down90']*100:.1f}%",f"{M['down90']*100:.1f}%"],["Up 10x or more",f"{H['up10x']*100:.1f}%",f"{M['up10x']*100:.1f}%"],
      ["$100 on the median call becomes",f"${H['usd100']:.0f}",f"${M['usd100']:.0f}"],["Gross average (mean)",mfmt(H["mean"]),mfmt(M["mean"])]]
cl=[[Z["300"],RED,RED],[Z["300"],RED,RED],[Z["300"],RED,RED],[Z["300"],EMR,EMR],[Z["300"],RED,RED],[Z["300"],EMR,EMR]]
table(c,c.content_top-14,["Metric",B1H,B24H],xs,["left","right","right"],rows,46,cl,bold=(4,))
c.save(f"{O}/memecoin-1b-results-table-1h-vs-24h.png")

# ---------- 1c EV table ----------
c=Card(800,540,"Expected value, bucket by bucket","E[R] = sum of p × r: each bucket's share of calls × its average return = its contribution (pts)",
       "Gross, before costs. 1h primary; 24h on the same 4,186 calls for comparison.",KS)
xs=[L,300,395,490,615,710,c.W-c.m-c.pad]
top=c.content_top-10
c.badge(395,top,"1h",10,ha="center",fg=Z["50"],bg="#172554",ec=ACC); c.badge(710,top,"24h",10,ha="center",fg=Z["400"])
rows=[];cl=[]
for a,b in zip(R["buckets"],M["buckets"]):
    rows.append([a["bucket"],f"{a['p']*100:.1f}%",f"{a['mean_ret']*100:+,.0f}%".replace("-","−"),f"{a['contrib']*100:+.1f}".replace("-","−"),
                 f"{b['p']*100:.1f}%",f"{b['mean_ret']*100:+,.0f}%".replace("-","−"),f"{b['contrib']*100:+.1f}".replace("-","−")])
    cl.append([Z["300"],Z["50"],Z["500"],EMR if a["contrib"]>0 else RED,Z["50"],Z["500"],EMR if b["contrib"]>0 else RED])
h10=H["bucket_sum"]-R["buckets"][-1]["contrib"]; d10=M["bucket_sum"]-M["buckets"][-1]["contrib"]
rows.append(["Without the ≥ 10x bucket","","",f"{h10*100:+.1f}".replace("-","−"),"","",f"{d10*100:+.1f}".replace("-","−")]); cl.append([Z["400"]]+[Z["50"]]*2+[RED if h10<0 else EMR]+[Z["50"]]*2+[RED])
rows.append(["Gross EV per call","","",mfmt(H["bucket_sum"]),"","",mfmt(M["bucket_sum"])]); cl.append([Z["50"]]+[Z["50"]]*2+[EMR]+[Z["50"]]*2+[EMR])
table(c,top-30,["Return bucket","share","avg","EV pts","share","avg","EV pts"],xs,["left"]+["right"]*6,rows,37,cl,bold=(7,))
c.save(f"{O}/memecoin-1c-ev-table-1h-vs-24h.png")

# ---------- 2 tail dependence ----------
c=Card(800,450,"The edge lives in two dozen lottery tickets","Average return after removing the k best calls (of 4,186) · 1h vs 24h",
       f"1h: +16.5% with every call, below the ~7.2% cost line after removing 6 calls, below zero after 24 (0.57%).",KS+"\n"+COST)
ax=c.axes(left=52)
rs1=np.sort(r1)[::-1]; rs24=np.sort(r24)[::-1]; ks=np.arange(0,81)
ax.plot(ks,[rs1[k:].mean()*100 for k in ks],color=ACC,lw=2.2*PT*1.4,label="1h",zorder=4)
ax.plot(ks,[rs24[k:].mean()*100 for k in ks],color=Z["500"],lw=1.4*PT*1.4,ls=(0,(4,3)),label="24h",zorder=3)
cost=(1-(1-0.0369014)**2)*100
ax.axhline(cost,color=RED,lw=1*PT,ls=(0,(4,3))); ax.axhline(0,color=Z["700"],lw=1*PT)
ax.text(80,cost+0.8,f"~{cost:.1f}% round-trip costs",ha="right",fontproperties=F["med"],fontsize=9.5*PT,color=RED)
ax.set_xlim(0,80); ax.yaxis.set_major_formatter(FuncFormatter(pct0)); ax.set_xlabel("best calls removed (k)",fontproperties=F["reg"],fontsize=10*PT,color=Z["500"])
for k,lab in [(6,"k=6: below cost"),(24,"k=24: below 0")]:
    yv=rs1[k:].mean()*100; ax.scatter([k],[yv],color=Z["50"],s=10,zorder=5); ax.annotate(lab,(k,yv),(k+2,yv+3),fontproperties=F["reg"],fontsize=9*PT,color=Z["300"])
c.ticks(ax)
lg=ax.legend(frameon=False,loc="upper center",prop=F["reg"],labelcolor=Z["400"],ncol=2); 
for t in lg.get_texts(): t.set_fontsize(9.5*PT)
c.save(f"{O}/memecoin-2-tail-dependence.png")

# ---------- 3 MC paths ----------
P=np.load(f"{OUTPUTS}/mc1h_base_paths_sample.npy"); m=R["mc"]["base"]
c=Card(800,450,"100 copied calls, 100,000 simulated traders","$1,000 start · 10% of bankroll per call · in at the call, out after 1h · real outcomes resampled · costs included",
       "", "Monte Carlo: bootstrap of the 4,186 real 1h returns (Karma dataset), base costs 3.69% per side, entry at the market price at the call (no extra delay).\n300 random paths shown · script memecoin-gamble-data/analysis_1h.py, seed 20261012.")
ax=c.axes(left=60,right=215)
t=np.arange(101); full=np.c_[np.full(len(P),1000),P]
for p in full[:300]: ax.plot(t,p,color=ACC,alpha=0.11,lw=0.6)
ax.plot(t,np.median(full,axis=0),color=Z["50"],lw=2*PT*1.4)
ax.axhline(1000,color=Z["500"],lw=0.8*PT,ls=(0,(2,2))); ax.axhline(100,color=RED,lw=0.8*PT,ls=(0,(4,3)))
ax.text(1,85,"ruin line (−90%)",fontproperties=F["reg"],fontsize=8.5*PT,color=RED,va="top")
ax.set_yscale("log"); ax.set_ylim(20,5e4); ax.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f"${v:,.0f}")); ax.set_xlim(0,100)
ax.set_xlabel("calls copied",fontproperties=F["reg"],fontsize=10*PT,color=Z["500"]); c.ticks(ax)
ax.minorticks_off()
X=c.W-c.m-c.pad-150; y=c.content_top+2
c.badge(X,y,"after 100 calls",9.5,fg=Z["50"],bg="#172554",ec=ACC); y-=30
for lab,val,col in [("median bankroll",f"${m['median_end']:,.0f}",RED),("mean bankroll",f"${m['mean_end']:,.0f}",EMR),
                    ("ended in profit",f"{m['p_profit']*100:.1f}%",Z["50"]),("lost half or more",f"{m['p_lose_half']*100:.1f}%",RED),
                    ("hit −90% at some point",f"{m['p_ruin90']*100:.1f}%",RED),("top 1% hold",f"{m['top1pct_share']*100:.0f}% of money",Z["50"])]:
    c.text(X,y,lab,10,"reg",Z["400"],va="top"); c.text(X,y-14,val,14,"semi",col,va="top"); y-=37
c.save(f"{O}/memecoin-3-monte-carlo-bankrolls.png")

# ---------- 4 sweep ----------
Sw=R["sweep"]; f=[s["f"]*100 for s in Sw]
c=Card(800,450,"Bet size sets how fast the median trader loses","Same 1h simulation, 100 calls, varying the share of bankroll put into each call",
       "The median trader ends below $1,000 at every bet size. Labels: median ending bankroll.",
       "Monte Carlo as in the bankroll chart (40,000 traders per point, base costs). 'Ruined' = bankroll fell below $100 (−90%) at any point.")
ax=c.axes(left=52)
ax.plot(f,[s["p_ruin90"]*100 for s in Sw],color=RED,lw=2*PT*1.4,marker="o",ms=4,label="ruined (−90% at some point)")
ax.plot(f,[s["p_profit"]*100 for s in Sw],color=EMR,lw=2*PT*1.4,marker="o",ms=4,label="ended in profit")
ax.axhline(50,color=Z["600"],lw=0.8*PT,ls=(0,(2,2))); ax.text(0.5,51.5,"50%",fontproperties=F["reg"],fontsize=8.5*PT,color=Z["500"],ha="left")
for s in Sw:
    lab=f"${s['median_end']:,.0f}" if s["median_end"]>=1 else "~$0"
    ax.annotate(lab,(s["f"]*100,s["p_profit"]*100),(0,-14),textcoords="offset points",ha="center",fontproperties=F["mono"],fontsize=8.5*PT,color=Z["400"])
ax.set_ylim(-12,105); ax.set_xlim(0,52); ax.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f"{v:.0f}%"))
ax.set_xlabel("% of bankroll per call",fontproperties=F["reg"],fontsize=10*PT,color=Z["500"]); c.ticks(ax)
lg=ax.legend(frameon=False,loc="upper left",prop=F["reg"],labelcolor=Z["400"])
for t_ in lg.get_texts(): t_.set_fontsize(9.5*PT)
c.save(f"{O}/memecoin-4-bet-size-vs-ruin.png")

# ---------- 5 fees ----------
def ser(fn):
    d=json.load(open(f"{DL}/{fn}")); return {dt.datetime.fromtimestamp(t,dt.UTC).date():v for t,v in d["totalDataChart"]}
lf,lr,pf,pr=[ser(x) for x in ["fees_pump.fun_dailyFees.json","fees_pump.fun_dailyRevenue.json","fees_pumpswap_dailyFees.json","fees_pumpswap_dailyRevenue.json"]]
days=sorted(set(lf)|set(pf))
cf=np.cumsum([lf.get(d,0)+pf.get(d,0) for d in days])/1e9; cr=np.cumsum([lr.get(d,0)+pr.get(d,0) for d in days])/1e9; clr=np.cumsum([lr.get(d,0) for d in days])/1e9
c=Card(800,450,"The house: $2.23B in fees, $1.32B kept","Cumulative trading fees on pumpdotfun's bonding curve + PumpSwap, and pumpdotfun's revenue · Mar 2024 – Oct 11, 2026",
       "",
       "Source: DefiLlama fees API (api.llama.fi/summary/fees/pump.fun and /pumpswap, dailyFees / dailyRevenue), pulled Oct 12, 2026.\nFees = all trading fees paid by users (incl. creator, cashback and LP slices). Revenue = pumpdotfun's own slice.")
ax=c.axes(left=52,right=80)
ax.fill_between(days,cf,0,color=ACC,alpha=0.18,lw=0); ax.plot(days,cf,color=ACC,lw=2*PT*1.4,label="fees paid by traders")
ax.plot(days,cr,color=Z["300"],lw=1.6*PT*1.4,label="pumpdotfun revenue (launchpad + PumpSwap)")
ax.plot(days,clr,color=Z["500"],lw=1.2*PT*1.4,ls=(0,(3,2)),label="pumpdotfun revenue (launchpad only)")
ax.axhline(1,color=Z["600"],lw=0.8*PT,ls=(0,(2,2)))
for yv,lab,col in [(cf[-1],f"${cf[-1]:.2f}B",ACC),(cr[-1]+0.05,f"${cr[-1]:.2f}B",Z["300"]),(clr[-1]-0.1,f"${clr[-1]:.2f}B",Z["500"])]:
    ax.text(days[-1]+dt.timedelta(days=12),yv,lab,fontproperties=F["semi"],fontsize=10*PT,color=col,va="center",clip_on=False)
ax.set_xlim(days[0],days[-1]); ax.set_ylim(0,2.45)
ax.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f"${v:.1f}B")); c.ticks(ax)
lg=ax.legend(frameon=False,loc="upper left",prop=F["reg"],labelcolor=Z["400"])
for t_ in lg.get_texts(): t_.set_fontsize(9.5*PT)
c.save(f"{O}/memecoin-5-pumpfun-cumulative-fees.png")
print("done")
