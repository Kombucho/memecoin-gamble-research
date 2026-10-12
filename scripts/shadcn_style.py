"""shadcn/ui-style card helpers for matplotlib (zinc dark theme)."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.ticker import FuncFormatter
import os
FONTS=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"fonts")
FD=FONTS+"/"
F={k:fm.FontProperties(fname=FD+v) for k,v in {"reg":"Geist-400.ttf","med":"Geist-500.ttf","semi":"Geist-600.ttf","mono":"GeistMono-400.ttf"}.items()}
F["sym"]=fm.FontProperties(fname=os.path.join(FONTS,"InterS-Regular.ttf"))  # fallback for Σ
Z={"950":"#09090b","900":"#18181b","800":"#27272a","700":"#3f3f46","600":"#52525b","500":"#71717a","400":"#a1a1aa","300":"#d4d4d8","50":"#fafafa"}
CHART={1:"#2662d9",2:"#2eb88a",3:"#e88c30",4:"#af57db",5:"#e23670"}   # shadcn dark chart-1..5
ACC=CHART[1]; RED="#ef4444"; EMR="#10b981"; OUTER="#000000"
DPI=200; PT=0.72  # 1 logical px = 0.72 pt at figsize W/100 inch
plt.rcParams.update({"text.parse_math":False,"savefig.facecolor":OUTER,"figure.facecolor":OUTER})
class Card:
    def __init__(s,W=800,H=450,title="",subtitle="",desc="",source="",m=10,pad=28):
        s.W,s.H,s.m,s.pad=W,H,m,pad
        s.fig=plt.figure(figsize=(W/100,H/100),dpi=DPI)
        s.fig.add_artist(FancyBboxPatch((s.fx(m),s.fy(m)),s.fx(W-2*m),s.fy(H-2*m),
            boxstyle=f"round,pad=0,rounding_size={s.fx(14)}",mutation_aspect=W/H,
            transform=s.fig.transFigure,fc=Z["950"],ec=Z["800"],lw=1*PT,zorder=-10))
        y=H-m-pad
        s.text(m+pad,y,title,16,"semi",Z["50"],va="top"); y-=24
        if subtitle: s.text(m+pad,y,subtitle,12,"reg",Z["400"],va="top"); y-=18
        if desc: s.text(m+pad,y,desc,11,"reg",Z["500"],va="top"); y-=17
        s.content_top=y-14
        fy=m+16
        s.text(m+pad,fy,source,8.5,"reg",Z["500"],va="bottom",linespacing=1.55)
        s.text(W-m-pad,fy,"@KombuchoBuild",8.5,"med",Z["600"],va="bottom",ha="right")
        nlines=source.count("\n")+1
        s.footer_top=fy+nlines*13+12
        s.fig.add_artist(plt.Line2D([s.fx(m+1),s.fx(W-m-1)],[s.fy(s.footer_top),s.fy(s.footer_top)],color=Z["800"],lw=1*PT))
        s.content_bottom=s.footer_top+16
    fx=lambda s,px: px/s.W
    fy=lambda s,px: px/s.H
    def text(s,x,y,t,size,w="reg",color=None,**kw):
        return s.fig.text(s.fx(x),s.fy(y),t,fontproperties=F[w],fontsize=size*PT,color=color or Z["50"],**kw)
    def axes(s,left=64,right=28,top=None,bottom=None):
        top=s.content_top if top is None else top; bottom=s.content_bottom+40 if bottom is None else bottom
        ax=s.fig.add_axes([s.fx(s.m+left),s.fy(bottom),s.fx(s.W-s.m-left-right),s.fy(top-bottom)])
        ax.set_facecolor("none")
        for k in ["top","right","left"]: ax.spines[k].set_visible(False)
        ax.spines["bottom"].set_color(Z["800"]); ax.spines["bottom"].set_linewidth(1*PT)
        ax.grid(axis="y",color=Z["800"],lw=0.8*PT,ls=(0,(3,3))); ax.set_axisbelow(True)
        ax.tick_params(length=0,labelsize=10*PT,colors=Z["500"],pad=6)
        return ax
    def ticks(s,ax):
        for l in ax.get_xticklabels()+ax.get_yticklabels(): l.set_fontproperties(F["reg"]); l.set_fontsize(10*PT); l.set_color(Z["500"])
    def badge(s,x,y,t,size=10,ha="left",fg=None,bg=None,ec=None):
        txt=s.text(x,y,t,size,"med",fg or Z["300"],ha=ha,va="center")
        txt.set_bbox(dict(boxstyle="round,pad=0.35,rounding_size=0.6",fc=bg or Z["900"],ec=ec or Z["800"],lw=1*PT)); return txt
    def save(s,path): s.fig.savefig(path,dpi=DPI); plt.close(s.fig)
def rounded_bar(ax,x,h,w,color,r_px=6,alpha=1.0):
    """Bar with rounded top corners only (data coords; ylim/xlim must be set first)."""
    fig=ax.figure; bb=ax.get_window_extent()
    xr=ax.get_xlim(); yr=ax.get_ylim()
    ppx=bb.width/(xr[1]-xr[0]); ppy=bb.height/(yr[1]-yr[0])   # display px per data unit
    rpx=r_px*DPI/100; rx=rpx/ppx; ry=rpx/ppy
    if h<=0: return
    ry_eff=min(ry,h); rx_eff=rx*ry_eff/ry
    ax.add_patch(FancyBboxPatch((x-w/2,0),w,h,boxstyle=f"round,pad=0,rounding_size={rx_eff}",mutation_aspect=ry_eff/rx_eff,fc=color,ec="none",alpha=alpha,zorder=3))
    ax.add_patch(Rectangle((x-w/2,0),w,max(h-ry_eff,0),fc=color,ec="none",alpha=alpha,zorder=3))
