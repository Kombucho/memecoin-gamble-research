import json,glob,numpy as np
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from karma_data import DATA, DL, CHARTS, OUTPUTS, karma_files
r1=[];r24=[];r24m=[]
for d in karma_files():
  for t in d.get('tokens',[]):
    if t.get('status')=='scored' and t.get('copy_return_24h') is not None and not t['mint'].startswith('0x'):
      r24.append(t['copy_return_24h'])
      if t.get('price_1h') is not None and t['market_price_at_entry']:
        r1.append(t['price_1h']/t['market_price_at_entry']-1); r24m.append(t['copy_return_24h'])
edges=[("≤ −90%",-np.inf,-0.9),("−90% to −50%",-0.9,-0.5),("−50% to 0",-0.5,0),("0 to +100%",0,1),("2x to 10x",1,9),("≥ 10x",9,np.inf)]
def stats(r):
  r=np.array(r); o=dict(n=len(r),median=float(np.median(r)),mean=float(r.mean()),red=float((r<0).mean()),
    down90=float((r<=-0.9).mean()),up10x=float((r>=9).mean()),usd100=float(100*(1+np.median(r))),
    mean_ex_top10=float(np.sort(r)[::-1][10:].mean()),max=float(r.max()))
  b=[]
  for name,lo,hi in edges:
    m=(r>lo)&(r<=hi) if np.isfinite(lo) else (r<=hi)
    if not np.isfinite(hi): m=r>lo
    p=float(m.mean()); mu=float(r[m].mean()) if m.any() else 0.0
    b.append(dict(bucket=name,p=p,mean_ret=mu,contrib=p*mu))
  o["buckets"]=b; o["bucket_sum"]=sum(x["contrib"] for x in b); return o
res={"1h":stats(r1),"24h":stats(r24),"24h_matched_to_1h":stats(r24m)}
json.dump(res,open(os.path.join(DATA,"stats_1h_24h.json"),"w"),indent=1)
for k,v in res.items():
  print(k,{a:(round(b,4) if isinstance(b,float) else b) for a,b in v.items() if a!='buckets'})
  for x in v['buckets']: print('   ',x['bucket'],round(x['p']*100,1),round(x['mean_ret']*100,1),round(x['contrib']*100,1))
