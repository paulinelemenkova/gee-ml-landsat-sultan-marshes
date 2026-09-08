#!/usr/bin/env python3
"""
Figure 6 (rebuild) - Ecological-condition maps of the Sultan Marshes wetland,
four epochs (1984, 2000, 2015, 2025) matching Table 3, five-class scheme
(Very good -> Very poor) from a per-pixel Ecological Condition Index (ECI),
clipped to the Ramsar wetland (176.7 km2).

Input : sultan_ECI_4epochs.tif  (4 bands = epochs, float ECI 0..1, EPSG:32636)
Output: Figure_6.png (300 dpi) + Figure_6.pdf ; prints the regenerated Table 3.

Class breaks (equal-interval, applied to every epoch):
  Very good >= 0.60 | Good 0.50-0.60 | Moderate 0.40-0.50 |
  Poor 0.30-0.40 | Very poor < 0.30
"""
import math, numpy as np
import rasterio
from pyproj import Transformer
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle

SRC = "data/sultan_ECI_4epochs.tif"
EPOCHS = ["1984", "2000", "2015", "2025"]
NAMES = ["Very good", "Good", "Moderate", "Poor", "Very poor"]
COLORS = ["#1a7a3f", "#7cb342", "#f4c430", "#ef7d34", "#d62828"]
BREAKS = [0.60, 0.50, 0.40, 0.30]          # VG,G,M,P thresholds; VP below
PX = 0.03 * 0.03

for _f in ["NimbusSans-Regular.otf", "NimbusSans-Bold.otf",
           "NimbusSans-Italic.otf", "NimbusSans-BoldItalic.otf"]:
    try: fm.fontManager.addfont("fonts/" + _f)
    except Exception: pass
plt.rcParams.update({"font.family": "Nimbus Sans", "svg.fonttype": "none"})

ds = rasterio.open(SRC)
E = ds.read().astype("float32")
b = ds.bounds; extent = [b.left, b.right, b.bottom, b.top]
H, W = E.shape[1], E.shape[2]

def classify(e):
    c = np.zeros(e.shape, np.uint8); fin = np.isfinite(e)
    c[fin & (e < BREAKS[3])] = 5
    c[fin & (e >= BREAKS[3])] = 4
    c[fin & (e >= BREAKS[2])] = 3
    c[fin & (e >= BREAKS[1])] = 2
    c[fin & (e >= BREAKS[0])] = 1
    return c
CLS = [classify(E[i]) for i in range(4)]

# areas + regenerated Table 3
areas = np.array([[ (CLS[j] == k).sum()*PX for j in range(4)] for k in range(1, 6)])
tot = np.array([np.isfinite(E[j]).sum()*PX for j in range(4)])
good = areas[0] + areas[1]                                   # Very good + Good
print("Regenerated Table 3 (km2, %):")
for k in range(5):
    print(NAMES[k].ljust(11) + "".join(
        f"{areas[k,j]:6.1f} ({100*areas[k,j]/tot[j]:4.1f})".rjust(15) for j in range(4)))

# lon/lat graticule
to_ll = Transformer.from_crs(ds.crs, "EPSG:4326", always_xy=True)
xmid = 0.5*(extent[0]+extent[1]); ymid = 0.5*(extent[2]+extent[3])
XT = np.arange(math.ceil(extent[0]/5000)*5000, extent[1], 5000)
YT = np.arange(math.ceil(extent[2]/5000)*5000, extent[3], 5000)
XL = [f"{to_ll.transform(x, ymid)[0]:.2f}\u00b0E" for x in XT]
YL = [f"{to_ll.transform(xmid, y)[1]:.2f}\u00b0N" for y in YT]

def rgba(cls):
    img = np.zeros((H, W, 4))
    for k in range(1, 6):
        m = cls == k
        rgb = tuple(int(COLORS[k-1][i:i+2], 16)/255 for i in (1, 3, 5))
        img[m, :3] = rgb; img[m, 3] = 1.0
    return img

fig = plt.figure(figsize=(13.6, 8.8), dpi=300)
gs = fig.add_gridspec(2, 4, height_ratios=[1.32, 1.0], hspace=0.16, wspace=0.07,
                      left=0.055, right=0.985, top=0.90, bottom=0.075)

for j, ep in enumerate(EPOCHS):
    ax = fig.add_subplot(gs[0, j]); ax.set_facecolor("#eef1f4")
    ax.imshow(rgba(CLS[j]), extent=extent, origin="upper", interpolation="nearest")
    ax.contour((CLS[j] >= 1).astype(float), levels=[0.5], colors="#333333",
               linewidths=0.6, extent=extent, origin="upper")
    ax.set_title(f"{chr(97+j)}) {ep}", fontsize=12, fontweight="bold", loc="left", pad=3)
    ax.set_xticks(XT); ax.set_yticks(YT)
    ax.set_xticklabels(XL, fontsize=7); ax.tick_params(length=2)
    ax.set_yticklabels(YL if j == 0 else [], fontsize=7)
    for sp in ax.spines.values(): sp.set_linewidth(0.8)
    ax.set_aspect("equal"); ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3])
    if j == 0:
        x0 = extent[0]+0.08*(extent[1]-extent[0]); y0 = extent[2]+0.07*(extent[3]-extent[2])
        ax.plot([x0, x0+5000], [y0, y0], color="black", lw=3, solid_capstyle="butt")
        ax.text(x0+2500, y0+700, "5 km", ha="center", va="bottom", fontsize=7.5)
        nx = extent[0]+0.90*(extent[1]-extent[0]); ny = extent[2]+0.82*(extent[3]-extent[2])
        ax.annotate("N", xy=(nx, ny+3500), xytext=(nx, ny), ha="center", va="center",
                    fontsize=10, fontweight="bold",
                    arrowprops=dict(arrowstyle="-|>", color="black", lw=1.5))

# legend
lax = fig.add_subplot(gs[1, 0]); lax.axis("off"); lax.set_xlim(0,1); lax.set_ylim(0,1)
lax.text(0.0, 0.98, "Ecological condition", fontsize=10.5, fontweight="bold", va="top")
y = 0.85
for k in range(5):
    lax.add_patch(Rectangle((0.0, y-0.05), 0.13, 0.06, facecolor=COLORS[k],
                            edgecolor="0.4", lw=0.4))
    lax.text(0.17, y-0.02, NAMES[k], fontsize=9, va="center")
    y -= 0.11
lax.text(0.0, y-0.01,
         "Per-pixel Ecological Condition Index\n(water + wet vegetation, minus bare\nsoil), five equal-interval classes.",
         fontsize=7.8, va="top", style="italic", color="#444444")

# stacked area chart + good subtotal
cax = fig.add_subplot(gs[1, 1:])
x = np.arange(4); bottom = np.zeros(4)
for k in range(5):
    cax.bar(x, areas[k], bottom=bottom, width=0.62, color=COLORS[k],
            edgecolor="white", linewidth=0.4)
    bottom += areas[k]
cax.plot(x, good, "o-", color="#08306b", lw=1.6, ms=5, zorder=5)
for i in range(4):
    cax.annotate(f"good\n{good[i]:.0f} km\u00b2", (x[i], good[i]),
                 textcoords="offset points", xytext=(0, 8), ha="center",
                 fontsize=7.6, color="#08306b", fontweight="bold")
    cax.text(x[i], bottom[i]+3, f"{bottom[i]:.0f}", ha="center", va="bottom",
             fontsize=8, color="#333333")
cax.set_xticks(x); cax.set_xticklabels(EPOCHS, fontsize=10)
cax.set_ylabel("Area (km$^2$)", fontsize=10); cax.set_ylim(0, 200); cax.set_xlim(-0.6, 3.6)
cax.set_title("Ecological-condition composition (176.7 km$^2$ wetland); "
              "line = Very good + Good", fontsize=9.8, loc="left")
cax.grid(axis="y", color="0.85", lw=0.6); cax.set_axisbelow(True)
for sp in ["top", "right"]: cax.spines[sp].set_visible(False)
cax.tick_params(labelsize=8.5)

fig.suptitle("Ecological condition of the Sultan Marshes, 1984\u20132025",
             fontsize=13.5, fontweight="bold", x=0.055, ha="left", y=0.965)
fig.text(0.055, 0.925,
         "Per-pixel Ecological Condition Index from the complete Landsat archive "
         "(Google Earth Engine), clipped to the Ramsar wetland.",
         fontsize=8.6, style="italic", color="#555555", ha="left")

fig.savefig("Figure_6.png", dpi=300, bbox_inches="tight", facecolor="white", pad_inches=0.12)
fig.savefig("Figure_6.pdf", bbox_inches="tight", facecolor="white", pad_inches=0.12)
print("\nwrote Figure_6.png / .pdf")
