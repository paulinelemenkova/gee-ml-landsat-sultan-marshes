#!/usr/bin/env python3
"""Figure 8 - condition-classifier performance (Random Forest vs Gradient Boosting)."""
import numpy as np, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

for _f in ["NimbusSans-Regular.otf","NimbusSans-Bold.otf","NimbusSans-Italic.otf","NimbusSans-BoldItalic.otf"]:
    try: fm.fontManager.addfont("fonts/"+_f)
    except Exception: pass
plt.rcParams.update({"font.family":"Nimbus Sans","svg.fonttype":"none"})

cm=np.load("data/confusion.npy"); res=json.load(open("data/clf_meta.json"))
classes=["Very good","Good","Moderate","Poor","Very poor"]
cmn=cm/cm.sum(1,keepdims=True)

fig,(ax1,ax2)=plt.subplots(1,2,figsize=(12.4,5.4),dpi=300,
                           gridspec_kw=dict(width_ratios=[1.05,1.0],wspace=0.32))

# --- confusion matrix (Random Forest) ---
im=ax1.imshow(cmn,cmap="Blues",vmin=0,vmax=1)
ax1.set_xticks(range(5)); ax1.set_yticks(range(5))
ax1.set_xticklabels(classes,rotation=35,ha="right",fontsize=8.5)
ax1.set_yticklabels(classes,fontsize=8.5)
ax1.set_xlabel("Predicted class",fontsize=10); ax1.set_ylabel("True class",fontsize=10)
ax1.set_title("(a) Random Forest confusion matrix",fontsize=11,fontweight="bold",loc="left",pad=8)
for i in range(5):
    for j in range(5):
        ax1.text(j,i,f"{cm[i,j]:,}",ha="center",va="center",fontsize=7.8,
                 color="white" if cmn[i,j]>0.5 else "#222222")
cb=fig.colorbar(im,ax=ax1,fraction=0.046,pad=0.03); cb.set_label("Row-normalised (recall)",fontsize=8.5)
cb.ax.tick_params(labelsize=7.5)

# --- metrics comparison RF vs GB ---
mets=["OA","Precision","Recall","F1","Kappa","AUC"]
rf=res["Random Forest"]; gb=res["Gradient Boosting"]
x=np.arange(len(mets)); w=0.38
ax2.bar(x-w/2,rf,w,label="Random Forest",color="#1f78b4",edgecolor="white",lw=0.5)
ax2.bar(x+w/2,gb,w,label="Gradient Boosting",color="#b2df8a",edgecolor="white",lw=0.5)
for i,(a,b) in enumerate(zip(rf,gb)):
    ax2.text(i-w/2,a+0.012,f"{a:.2f}",ha="center",fontsize=7,color="#1f4e79")
    ax2.text(i+w/2,b+0.012,f"{b:.2f}",ha="center",fontsize=7,color="#33691e")
ax2.set_xticks(x); ax2.set_xticklabels(mets,fontsize=9)
ax2.set_ylim(0,1.22); ax2.set_ylabel("Score",fontsize=10)
ax2.set_title("(b) Accuracy metrics (independent test set)",fontsize=11,fontweight="bold",loc="left",pad=8)
ax2.legend(fontsize=8.5,frameon=False,loc="upper center",ncol=2,
           bbox_to_anchor=(0.5,1.0),columnspacing=1.6,handlelength=1.5)
ax2.grid(axis="y",color="0.88",lw=0.6); ax2.set_axisbelow(True)
for sp in ["top","right"]: ax2.spines[sp].set_visible(False)
ax2.tick_params(labelsize=8.5)

fig.suptitle("Ecological-condition classifier performance",fontsize=13.5,fontweight="bold",
             x=0.02,ha="left",y=0.99)
fig.text(0.02,0.945,"Five condition classes predicted from climate, terrain and spectral "
         "predictors; 70/30 train\u2013test split. Errors fall mainly between neighbouring classes.",
         fontsize=8.6,style="italic",color="#555555",ha="left")
fig.tight_layout(rect=[0,0,1,0.93])
fig.savefig("Figure_08.png",dpi=300,bbox_inches="tight",facecolor="white",pad_inches=0.12)
fig.savefig("Figure_08.pdf",bbox_inches="tight",facecolor="white",pad_inches=0.12)
print("wrote Figure_08")
