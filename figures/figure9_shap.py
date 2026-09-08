#!/usr/bin/env python3
"""Figure 9 - SHAP driver attribution for the ecological-condition (ECI) model."""
import numpy as np, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

for _f in ["NimbusSans-Regular.otf","NimbusSans-Bold.otf","NimbusSans-Italic.otf","NimbusSans-BoldItalic.otf"]:
    try: fm.fontManager.addfont("fonts/"+_f)
    except Exception: pass
plt.rcParams.update({"font.family":"Nimbus Sans","svg.fonttype":"none"})

sv=np.load("data/shap_values.npy"); Xv=np.load("data/shap_X.npy"); meta=json.load(open("data/shap_meta.json"))
feat=meta["feat"]; order=meta["order"]
CAT={'NDVI':'Spectral','NDWI':'Spectral','MNDWI':'Spectral','NDMI':'Spectral','BSI':'Spectral',
     'Precipitation':'Climate','PET':'Climate','Water deficit':'Climate','Soil moisture':'Climate',
     'Max temperature':'Climate','Elevation':'Terrain'}
CCOL={'Spectral':'#2a9d8f','Climate':'#e76f51','Terrain':'#8a8a8a'}
mabs=np.abs(sv).mean(0); rel=100*mabs/mabs.sum()
order=list(order)                         # importance desc
topfeat=[feat[i] for i in order]

fig,(ax1,ax2)=plt.subplots(1,2,figsize=(12.8,5.8),dpi=300,
                           gridspec_kw=dict(width_ratios=[0.85,1.15],wspace=0.36))

# --- (a) mean|SHAP| bar, coloured by category ---
y=np.arange(len(order))[::-1]
cols=[CCOL[CAT[feat[i]]] for i in order]
ax1.barh(y,[rel[i] for i in order],color=cols,edgecolor="white",lw=0.5)
ax1.set_yticks(y); ax1.set_yticklabels(topfeat,fontsize=9)
for yi,i in zip(y,order):
    ax1.text(rel[i]+0.4,yi,f"{rel[i]:.1f}%",va="center",fontsize=7.6,color="#333")
ax1.set_xlabel("Relative importance  (mean |SHAP|, %)",fontsize=9.5)
ax1.set_xlim(0,max(rel)*1.16)
ax1.set_title("(a) Global feature importance",fontsize=11,fontweight="bold",loc="left",pad=8)
for sp in ["top","right"]: ax1.spines[sp].set_visible(False)
ax1.tick_params(labelsize=8.5)
handles=[plt.Rectangle((0,0),1,1,color=CCOL[c]) for c in ['Spectral','Climate','Terrain']]
ax1.legend(handles,['Spectral index','Climate','Terrain'],fontsize=8,frameon=False,loc="lower right")

# --- (b) beeswarm ---
rng=np.random.default_rng(0)
for row,i in enumerate(order):
    yy=len(order)-1-row
    x=sv[:,i]; v=Xv[:,i]
    vn=(v-v.min())/(np.ptp(v)+1e-9)
    jit=rng.uniform(-0.32,0.32,size=len(x))
    ax2.scatter(x,yy+jit,c=vn,cmap="coolwarm",s=6,alpha=0.55,linewidths=0,vmin=0,vmax=1)
ax2.axvline(0,color="0.6",lw=0.8)
ax2.set_yticks(np.arange(len(order))[::-1]); ax2.set_yticklabels(topfeat,fontsize=9)
ax2.set_xlabel("SHAP value  (impact on predicted condition)",fontsize=9.5)
ax2.set_title("(b) Per-pixel SHAP values",fontsize=11,fontweight="bold",loc="left",pad=8)
for sp in ["top","right"]: ax2.spines[sp].set_visible(False)
ax2.tick_params(labelsize=8.5)
sm=ScalarMappable(norm=Normalize(0,1),cmap="coolwarm")
cb=fig.colorbar(sm,ax=ax2,fraction=0.03,pad=0.02); cb.set_label("Predictor value (low \u2192 high)",fontsize=8)
cb.set_ticks([0,1]); cb.set_ticklabels(["low","high"]); cb.ax.tick_params(labelsize=7.5)

fig.suptitle("Drivers of ecological condition (SHAP attribution)",fontsize=13.5,
             fontweight="bold",x=0.02,ha="left",y=0.99)
fig.text(0.02,0.945,"Random-Forest model of the 2025 Ecological Condition Index (R\u00b2 = "
         f"{meta['R2']}). Vegetation (NDVI) and bare soil (BSI) dominate the spatial pattern; "
         "the ~4 km climate fields are near-uniform across the wetland and contribute little spatially.",
         fontsize=8.5,style="italic",color="#555555",ha="left")
fig.tight_layout(rect=[0,0,1,0.92])
fig.savefig("Figure_09.png",dpi=300,bbox_inches="tight",facecolor="white",pad_inches=0.12)
fig.savefig("Figure_09.pdf",bbox_inches="tight",facecolor="white",pad_inches=0.12)
print("wrote Figure_09")
