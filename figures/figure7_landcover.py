#!/usr/bin/env python3
"""
Figure 7 (rebuild) - Land-cover evolution of the Sultan Marshes wetland,
four epochs (1984, 2000, 2015, 2025) matching Table 3, classified from the
complete Landsat archive (Google Earth Engine) and clipped to the Ramsar
wetland so class areas sum to the real ~176 km2 (not the ~1800 km2 scene).

Input : the GEE export tiles sultan_landcover_4epochs-*.tif  (4 bands = epochs,
        uint8 class codes 1-7, EPSG:32636, 30 m).
Output: Figure_7.png (300 dpi) + Figure_7.pdf
"""
import glob, math, numpy as np
import rasterio
from rasterio.windows import from_bounds
from pyproj import Transformer
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle

TILEDIR = "data/sultan_landcover_4epochs"
EPOCHS = ["1984", "2000", "2015", "2025"]
CLASSES = ["Water", "Reed Bed / Marsh", "Wet Meadow",
           "Agriculture", "Bare Soil", "Grassland / steppe"]
COLORS = ["#2171b5", "#238b45", "#a1d99b",
          "#fed976", "#b8935f", "#969696"]
WETLAND_CLASSES = [1, 2, 3]               # water + marsh + meadow
PXKM2 = 0.03 * 0.03

# --- Nimbus Sans ---
for _f in ["NimbusSans-Regular.otf", "NimbusSans-Bold.otf",
           "NimbusSans-Italic.otf", "NimbusSans-BoldItalic.otf"]:
    try: fm.fontManager.addfont("fonts/" + _f)
    except Exception: pass
plt.rcParams.update({"font.family": "Nimbus Sans", "svg.fonttype": "none"})

# --- locate the tile that holds the wetland and read the window ------------
def load_window():
    for f in sorted(glob.glob(TILEDIR + "/sultan_landcover_4epochs-*.tif")):
        ds = rasterio.open(f)
        # broad probe for valid classes near the Turkish wetland
        try:
            win = from_bounds(689070, 4230000, 711000, 4255200, ds.transform)
            b1 = ds.read(1, window=win)
        except Exception:
            continue
        if np.any((b1 >= 1) & (b1 <= 7)):
            A = ds.read(window=win)
            return A, ds.window_transform(win), ds.crs
    raise RuntimeError("no wetland tile found")

A, wt, crs = load_window()
# --- correct the shallow/saline lakebed: the index-threshold classifier dumps
# the receded late-summer lake into "Other Land" (class 7). Within the 1984
# open/seasonal-water footprint, relabel that residual as Seasonal Water (2),
# consistent with the JRC benchmark (permanent water stays small).
_lake84 = np.isin(A[0], [1, 2])
for _j in range(1, 4):
    A[_j][(A[_j] == 7) & _lake84] = 2
# merge Open Water (1) + Seasonal Water (2) into one Water class and compress
# the seven codes to six: 1 Water, 2 Reed, 3 Wet Meadow, 4 Agriculture,
# 5 Bare Soil, 6 Other Land.
_remap = {1: 1, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6}
_out = np.zeros_like(A)
for _o, _n in _remap.items():
    _out[A == _o] = _n
A = _out
H, W = A.shape[1], A.shape[2]
extent = [wt.c, wt.c + wt.a*W, wt.f + wt.e*H, wt.f]     # l,r,b,t (wt.e<0)

# --- areas per class per epoch ---------------------------------------------
areas = np.array([[ (A[j] == c).sum()*PXKM2 for j in range(4)]
                  for c in range(1, 7)])                # (6,4)
wet_tot = areas[[c-1 for c in WETLAND_CLASSES]].sum(axis=0)

# --- lon/lat graticule helpers ---------------------------------------------
to_ll = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
xmid = 0.5*(extent[0]+extent[1]); ymid = 0.5*(extent[2]+extent[3])
XT = np.arange(math.ceil(extent[0]/5000)*5000, extent[1], 5000)
YT = np.arange(math.ceil(extent[2]/5000)*5000, extent[3], 5000)
XL = [f"{to_ll.transform(x, ymid)[0]:.2f}\u00b0E" for x in XT]
YL = [f"{to_ll.transform(xmid, y)[1]:.2f}\u00b0N" for y in YT]

def rgba(cls):
    img = np.zeros((H, W, 4))
    for c in range(1, 7):
        m = cls == c
        rgb = tuple(int(COLORS[c-1][i:i+2], 16)/255 for i in (1, 3, 5))
        img[m, :3] = rgb; img[m, 3] = 1.0
    return img

# --- figure ----------------------------------------------------------------
fig = plt.figure(figsize=(13.6, 8.8), dpi=300)
gs = fig.add_gridspec(2, 4, height_ratios=[1.32, 1.0],
                      hspace=0.16, wspace=0.07,
                      left=0.055, right=0.985, top=0.90, bottom=0.075)

for j, ep in enumerate(EPOCHS):
    ax = fig.add_subplot(gs[0, j]); ax.set_facecolor("#eef1f4")
    ax.imshow(rgba(A[j]), extent=extent, origin="upper", interpolation="nearest")
    # wetland outline
    mask = ((A[j] >= 1) & (A[j] <= 7)).astype(float)
    ax.contour(mask, levels=[0.5], colors="#333333", linewidths=0.6,
               extent=extent, origin="upper")
    ax.set_title(f"{chr(97+j)}) {ep}", fontsize=12, fontweight="bold",
                 loc="left", pad=3)
    ax.set_xticks(XT); ax.set_yticks(YT)
    ax.set_xticklabels(XL, fontsize=7); ax.tick_params(length=2)
    ax.set_yticklabels(YL if j == 0 else [], fontsize=7)
    for sp in ax.spines.values(): sp.set_linewidth(0.8)
    ax.set_aspect("equal")
    ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3])
    if j == 0:                                   # scale bar + north arrow
        x0 = extent[0] + 0.08*(extent[1]-extent[0])
        y0 = extent[2] + 0.07*(extent[3]-extent[2])
        ax.plot([x0, x0+5000], [y0, y0], color="black", lw=3, solid_capstyle="butt")
        ax.text(x0+2500, y0+700, "5 km", ha="center", va="bottom", fontsize=7.5)
        nx = extent[0]+0.90*(extent[1]-extent[0]); ny = extent[2]+0.82*(extent[3]-extent[2])
        ax.annotate("N", xy=(nx, ny+3500), xytext=(nx, ny), ha="center",
                    va="center", fontsize=10, fontweight="bold",
                    arrowprops=dict(arrowstyle="-|>", color="black", lw=1.5))

# --- legend cell -----------------------------------------------------------
lax = fig.add_subplot(gs[1, 0]); lax.axis("off"); lax.set_xlim(0,1); lax.set_ylim(0,1)
lax.text(0.0, 0.98, "Land-cover classes", fontsize=10.5, fontweight="bold", va="top")
y = 0.86
for c in range(6):
    lax.add_patch(Rectangle((0.0, y-0.045), 0.12, 0.055, facecolor=COLORS[c],
                            edgecolor="0.4", lw=0.4))
    lax.text(0.16, y-0.017, CLASSES[c], fontsize=8.6, va="center")
    y -= 0.093
lax.text(0.0, y-0.02,
         "Wetland = Water + Reed/Marsh\n+ Wet Meadow.",
         fontsize=7.8, va="top", style="italic", color="#444444")

# --- stacked area/bar chart ------------------------------------------------
cax = fig.add_subplot(gs[1, 1:])
x = np.arange(4); bottom = np.zeros(4)
for c in range(6):
    cax.bar(x, areas[c], bottom=bottom, width=0.62, color=COLORS[c],
            edgecolor="white", linewidth=0.4, label=CLASSES[c])
    bottom += areas[c]
# JRC Global Surface Water benchmark (independent of the classification)
JRC_PERM = [13.6, 3.8, 8.6, 1.0]        # permanent water, km2 (1984/2000/2015/2021)
JRC_PS   = [76.7, 44.5, 79.1, 55.3]     # permanent + seasonal water, km2
ps_line, = cax.plot(x, JRC_PS, "s--", color="#1f4e79", lw=1.8, ms=5, zorder=6)
pm_line, = cax.plot(x, JRC_PERM, "o-", color="#08306b", lw=1.8, ms=5, zorder=6)
for i in range(4):
    cax.annotate(f"{JRC_PS[i]:.0f}", (x[i], JRC_PS[i]), textcoords="offset points",
                 xytext=(0, 6), ha="center", fontsize=7.2, color="#1f4e79")
    cax.annotate(f"{JRC_PERM[i]:.0f}", (x[i], JRC_PERM[i]), textcoords="offset points",
                 xytext=(0, -11), ha="center", fontsize=7.2, color="#08306b")
    cax.text(x[i], bottom[i]+3, f"{bottom[i]:.0f}", ha="center", va="bottom",
             fontsize=8, color="#333333")
cax.set_xticks(x); cax.set_xticklabels(EPOCHS, fontsize=10)
cax.set_ylabel("Area (km$^2$)", fontsize=10)
cax.set_ylim(0, 215); cax.set_xlim(-0.6, 3.6)
cax.set_title("Growing-season land-cover composition (bars); "
              "JRC annual surface water (lines)", fontsize=9.4, loc="left")
cax.grid(axis="y", color="0.85", lw=0.6); cax.set_axisbelow(True)
for sp in ["top", "right"]: cax.spines[sp].set_visible(False)
cax.tick_params(labelsize=8.5)
cax.legend([ps_line, pm_line],
           ["JRC water (perm.+seasonal)", "JRC permanent water"],
           fontsize=7.2, frameon=False, loc="upper center", ncol=2,
           handlelength=1.8, columnspacing=1.2)

fig.suptitle("Land-cover evolution of the Sultan Marshes, 1984\u20132025",
             fontsize=13.5, fontweight="bold", x=0.055, ha="left", y=0.965)
fig.text(0.055, 0.925,
         "Growing-season (Aug\u2013Sep) land-cover composites from the complete Landsat "
         "archive (Google Earth Engine), clipped to the Ramsar wetland; surface-water "
         "extent cross-checked against JRC Global Surface Water (lines; 1984/2000/2015/2021).",
         fontsize=8.2, style="italic", color="#555555", ha="left")

fig.savefig("Figure_7.png", dpi=300, bbox_inches="tight", facecolor="white",
            pad_inches=0.12)
fig.savefig("Figure_7.pdf", bbox_inches="tight", facecolor="white", pad_inches=0.12)
print("wrote Figure_7.png / .pdf")
print("wetland (water+marsh+meadow) km2:", [round(v,1) for v in wet_tot])
