#!/usr/bin/env python3
"""
Figure 9 (rebuild) - Wetland drying-risk index for the Sultan Marshes.

Risk (0..1) combines two real signals from the 1984-2025 ECI series:
  deficit = how far current (2025) condition sits below "Good" (ECI 0.50),
  decline = the per-decade downward ECI trend (per-pixel OLS).
  risk = clip(0.6*deficit + 0.4*decline, 0, 1).
High risk = already dry and still drying.

Input : sultan_ECI_4epochs.tif  (4 bands = epochs, ECI 0..1, EPSG:32636)
Output: Figure_9.png (300 dpi) + Figure_9.pdf
"""
import math, numpy as np
import rasterio
from pyproj import Transformer
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib import cm
from matplotlib.colors import Normalize

SRC = "data/sultan_ECI_4epochs.tif"
YEARS = np.array([1984, 2000, 2015, 2025], float)

for _f in ["NimbusSans-Regular.otf", "NimbusSans-Bold.otf",
           "NimbusSans-Italic.otf", "NimbusSans-BoldItalic.otf"]:
    try: fm.fontManager.addfont("fonts/" + _f)
    except Exception: pass
plt.rcParams.update({"font.family": "Nimbus Sans", "svg.fonttype": "none"})

ds = rasterio.open(SRC)
E = ds.read().astype("float32")
b = ds.bounds; extent = [b.left, b.right, b.bottom, b.top]
H, W = E.shape[1], E.shape[2]
fin = np.isfinite(E).all(axis=0)

dt = YEARS - YEARS.mean()
slope = np.tensordot(dt, E - E.mean(axis=0), axes=(0, 0)) / (dt**2).sum()
deficit = np.clip((0.50 - E[3]) / 0.30, 0, 1)
decline = np.clip((-slope*10) / 0.15, 0, 1)
risk = np.clip(0.6*deficit + 0.4*decline, 0, 1)
risk[~fin] = np.nan

# sectors (northing tertiles)
rows = np.where(fin)[0]; r1, r2 = np.percentile(rows, [33.3, 66.6])
yy = np.arange(H)[:, None] * np.ones((1, W))
zone = np.where(yy <= r1, 1, np.where(yy <= r2, 2, 3))
sect = {}
for z, nm in [(1, "North"), (2, "Central"), (3, "South")]:
    m = (zone == z) & fin
    sect[nm] = (float(np.nanmean(risk[m])), float(np.mean(risk[m] > 0.6)*100),
                float(m.sum()*0.0009))
print("sector mean-risk / %high / km2:", sect)

# graticule
to_ll = Transformer.from_crs(ds.crs, "EPSG:4326", always_xy=True)
xmid = 0.5*(extent[0]+extent[1]); ymid = 0.5*(extent[2]+extent[3])
XT = np.arange(math.ceil(extent[0]/5000)*5000, extent[1], 5000)
YT = np.arange(math.ceil(extent[2]/5000)*5000, extent[3], 5000)
XL = [f"{to_ll.transform(x, ymid)[0]:.2f}\u00b0E" for x in XT]
YL = [f"{to_ll.transform(xmid, y)[1]:.2f}\u00b0N" for y in YT]

fig = plt.figure(figsize=(11.2, 8.4), dpi=300)
gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 0.82], wspace=0.02,
                      left=0.075, right=0.965, top=0.9, bottom=0.09)

# --- risk map ---
ax = fig.add_subplot(gs[0, 0]); ax.set_facecolor("#eef1f4")
cmap = plt.get_cmap("YlOrRd")
im = ax.imshow(risk, extent=extent, origin="upper", cmap=cmap, vmin=0, vmax=1,
               interpolation="nearest")
ax.contour(fin.astype(float), levels=[0.5], colors="#333333", linewidths=0.6,
           extent=extent, origin="upper")
ax.set_xticks(XT); ax.set_yticks(YT)
ax.set_xticklabels(XL, fontsize=8); ax.set_yticklabels(YL, fontsize=8)
ax.tick_params(length=2); ax.set_aspect("equal")
ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3])
for sp in ax.spines.values(): sp.set_linewidth(0.8)
# scale bar (bottom-right) + north arrow (upper-left)
x1 = extent[0]+0.93*(extent[1]-extent[0]); y0 = extent[2]+0.06*(extent[3]-extent[2])
ax.plot([x1-5000, x1], [y0, y0], color="black", lw=3, solid_capstyle="butt")
ax.text(x1-2500, y0+700, "5 km", ha="center", va="bottom", fontsize=8)
nx = extent[0]+0.09*(extent[1]-extent[0]); ny = extent[2]+0.83*(extent[3]-extent[2])
ax.annotate("N", xy=(nx, ny+3500), xytext=(nx, ny), ha="center", va="center",
            fontsize=11, fontweight="bold",
            arrowprops=dict(arrowstyle="-|>", color="black", lw=1.6))
cb = fig.colorbar(im, ax=ax, orientation="horizontal", fraction=0.045, pad=0.09)
cb.set_label("Drying-risk index (0 = low, 1 = high)", fontsize=9)
cb.ax.tick_params(labelsize=8)

# --- sector summary + note ---
rax = fig.add_subplot(gs[0, 1]); rax.axis("off"); rax.set_xlim(0,1); rax.set_ylim(0,1)
rax.text(0.0, 0.99, "Mean drying risk by sector", fontsize=11, fontweight="bold", va="top")
order = ["Central", "North", "South"]
ytop = 0.86; bw = 0.11
for i, nm in enumerate(order):
    val, hi, km2 = sect[nm]
    yb = ytop - i*0.16
    rax.add_patch(plt.Rectangle((0.30, yb-bw), 0.60*val, bw,
                  facecolor=cmap(val), edgecolor="0.3", lw=0.5))
    rax.add_patch(plt.Rectangle((0.30, yb-bw), 0.60, bw, fill=False,
                  edgecolor="0.6", lw=0.5))
    rax.text(0.28, yb-bw/2, nm, ha="right", va="center", fontsize=9.5)
    rax.text(0.30+0.60*val+0.02, yb-bw/2, f"{val:.2f}", ha="left", va="center",
             fontsize=9, fontweight="bold")
    rax.text(0.30, yb-bw-0.03, f"{hi:.0f}% of area at high risk (>0.6); {km2:.0f} km\u00b2",
             ha="left", va="top", fontsize=7.6, color="#555555")
rax.text(0.0, 0.30,
         "Risk combines current dryness (2025 ECI below the \u201cGood\u201d\n"
         "level, 0.50) and the per-pixel ECI decline rate, 1984\u20132025.\n"
         "The central marshes and former lakebed are most exposed;\n"
         "the southern spring-fed margin is least exposed.",
         fontsize=8.4, va="top", color="#333333")
rax.text(0.0, 0.10,
         "Data: complete Landsat archive (Google Earth Engine); "
         "ECI trajectory, Ramsar wetland (176.7 km\u00b2).",
         fontsize=7.6, va="top", style="italic", color="#555555")

fig.suptitle("Future drying risk of the Sultan Marshes", fontsize=13.5,
             fontweight="bold", x=0.075, ha="left", y=0.965)
fig.savefig("Figure_9.png", dpi=300, bbox_inches="tight", facecolor="white", pad_inches=0.12)
fig.savefig("Figure_9.pdf", bbox_inches="tight", facecolor="white", pad_inches=0.12)
print("wrote Figure_9.png / .pdf")
