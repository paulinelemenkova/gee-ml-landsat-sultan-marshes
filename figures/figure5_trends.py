#!/usr/bin/env python3
"""
Figure 5 - Spatial distribution of long-term (1984-2025) trends in five spectral
indicators over the Sultan Marshes, from the Theil-Sen slope and the
Mann-Kendall test (per-pixel), computed in Google Earth Engine.

Input : sultan_trends_fig5_60m.tif  (15 bands, EPSG:32636, 60 m)
        band order = [NDWI, MNDWI, NDVI, NDMI, BSI] x [slope, tau, p]
Output: Figure_5.png (300 dpi) + Figure_5.pdf

Notes
-----
* The exported Mann-Kendall p-value bands are NaN (a known limitation of
  ee.Reducer.kendallsCorrelation), so significance is derived from Kendall's
  tau via the large-sample MK normal approximation: for n = 42 annual values,
  |tau| >= 0.211 corresponds to p < 0.05 (two-sided). Non-significant pixels
  are muted.
* Red always denotes change toward a drier / more degraded surface: a decrease
  in NDWI, MNDWI, NDVI and NDMI, or an increase in BSI (its scale is reversed).
"""
import numpy as np
import rasterio
from pyproj import Transformer
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrow, Rectangle
from matplotlib.lines import Line2D
import math
from matplotlib import font_manager as fm

SRC = "data/sultan_trends_fig5_60m.tif"
N_YEARS = 42
TAU_CRIT = 0.211            # |tau| for p<0.05, MK normal approx., n=42

# --- Nimbus Sans font ---
for _f in ["NimbusSans-Regular.otf", "NimbusSans-Bold.otf",
           "NimbusSans-Italic.otf", "NimbusSans-BoldItalic.otf"]:
    try:
        fm.fontManager.addfont("fonts/" + _f)
    except Exception:
        pass
plt.rcParams.update({"font.family": "Nimbus Sans", "svg.fonttype": "none"})

# ---- read -----------------------------------------------------------------
with rasterio.open(SRC) as ds:
    A = ds.read().astype("float32")
    b = ds.bounds
    crs = ds.crs
extent = [b.left, b.right, b.bottom, b.top]           # UTM metres
names = ["NDWI", "MNDWI", "NDVI", "NDMI", "BSI"]
slope = {names[i]: A[i*3] for i in range(5)}
tau   = {names[i]: A[i*3+1] for i in range(5)}

# ---- lon/lat tick helpers (approx graticule on a UTM axes) ----------------
to_ll = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
xmid = 0.5*(b.left+b.right); ymid = 0.5*(b.bottom+b.top)
def xticks_lonlat():
    xs = np.arange(math.ceil(b.left/10000)*10000, b.right, 10000)
    labs = [f"{to_ll.transform(x, ymid)[0]:.2f}\u00b0E" for x in xs]
    return xs, labs
def yticks_lonlat():
    ys = np.arange(math.ceil(b.bottom/10000)*10000, b.top, 10000)
    labs = [f"{to_ll.transform(xmid, y)[1]:.2f}\u00b0N" for y in ys]
    return ys, labs
XT, XL = xticks_lonlat()
YT, YL = yticks_lonlat()

# ---- figure ---------------------------------------------------------------
fig, axes = plt.subplots(2, 3, figsize=(10.4, 10.8), dpi=300)
axes = axes.ravel()
panel_tags = ["(a)", "(b)", "(c)", "(d)", "(e)"]

for k, nm in enumerate(names):
    ax = axes[k]
    s = slope[nm].copy()
    t = tau[nm]
    reverse = (nm == "BSI")                 # BSI: increase = degradation -> red
    cmap = "RdBu_r" if reverse else "RdBu"
    # robust symmetric limits
    v = np.nanpercentile(np.abs(s[np.isfinite(s)]), 98)
    v = math.ceil(v*1000)/1000.0
    im = ax.imshow(s, extent=extent, origin="upper", cmap=cmap,
                   vmin=-v, vmax=v, interpolation="nearest")
    # mute non-significant pixels (|tau| < critical)
    nonsig = (np.abs(t) < TAU_CRIT).astype(float)
    overlay = np.zeros((*s.shape, 4), dtype=float)
    overlay[..., :3] = 1.0                 # white
    overlay[..., 3] = np.where(np.isfinite(t), nonsig*0.55, 0.0)
    ax.imshow(overlay, extent=extent, origin="upper", interpolation="nearest")

    ax.set_title(f"{panel_tags[k]} {nm}", fontsize=11, fontweight="bold",
                 loc="left", pad=3)
    # graticule ticks only on outer axes
    ax.set_xticks(XT); ax.set_yticks(YT)
    if k in (3, 4):
        ax.set_xticklabels(XL, fontsize=7)
    else:
        ax.set_xticklabels([])
    if k in (0, 3):
        ax.set_yticklabels(YL, fontsize=7)
    else:
        ax.set_yticklabels([])
    ax.tick_params(length=2)
    for sp in ax.spines.values():
        sp.set_linewidth(0.8)
    ax.set_aspect("equal")

    # per-panel colourbar
    cb = fig.colorbar(im, ax=ax, orientation="horizontal", fraction=0.046,
                      pad=0.02, ticks=[-v, 0, v])
    cb.ax.tick_params(labelsize=7)
    cb.set_label("Sen slope (yr$^{-1}$)", fontsize=7.5)
    cb.ax.set_xticklabels([f"{-v:+.3f}", "0", f"{v:+.3f}"])

    # scale bar + north arrow on panel (a)
    if k == 0:
        x0 = b.left + 0.06*(b.right-b.left)
        y0 = b.bottom + 0.07*(b.top-b.bottom)
        ax.plot([x0, x0+10000], [y0, y0], color="black", lw=3,
                solid_capstyle="butt")
        ax.text(x0+5000, y0+1500, "10 km", ha="center", va="bottom",
                fontsize=7.5)
        nx = b.left + 0.90*(b.right-b.left)
        ny = b.bottom + 0.86*(b.top-b.bottom)
        ax.annotate("N", xy=(nx, ny+6500), xytext=(nx, ny),
                    ha="center", va="center", fontsize=10, fontweight="bold",
                    arrowprops=dict(arrowstyle="-|>", color="black", lw=1.6))

# ---- legend cell (width standardised to the NDVI map) --------------------
import textwrap
lax = axes[5]; lax.axis("off"); lax.set_xlim(0, 1); lax.set_ylim(0, 1)

fig.suptitle("Long-term trends in spectral indicators, Sultan Marshes (1984\u20132025)",
             fontsize=12.5, fontweight="bold", y=0.986)
fig.tight_layout(rect=[0, 0, 1, 0.99], h_pad=1.6, w_pad=1.0)
fig.subplots_adjust(top=0.95)          # balanced gap under the title
fig.canvas.draw()

# measure the NDVI (panel c) drawn-image width, map it into the legend axes
imbb = axes[2].images[0].get_window_extent()
lbb  = lax.get_window_extent()
xL = (imbb.x0 - lbb.x0) / lbb.width
xR = (imbb.x1 - lbb.x0) / lbb.width
w_pts = lbb.width  * 72.0 / fig.dpi
h_pts = lbb.height * 72.0 / fig.dpi
def lh(fs):  return 1.34 * fs / h_pts                     # line height (axes frac)
def nchars(fs, x0):  return max(8, int(((xR - x0) * w_pts) / (0.50 * fs)))

cursor = 0.985
def para(text, fs, italic=False, bold=False, color="black", x=None, gap=0.0):
    global cursor
    x = xL if x is None else x
    cursor -= gap
    for line in textwrap.fill(text, nchars(fs, x)).split("\n"):
        lax.text(x, cursor, line, fontsize=fs, va="top", ha="left",
                 style="italic" if italic else "normal",
                 fontweight="bold" if bold else "normal", color=color)
        cursor -= lh(fs)

para("Legend", 11, bold=True)
para("Colour = Theil\u2013Sen slope (index change per year), 1984\u20132025. "
     "One panel per indicator; all share the extent and projection (UTM Zone 36N).",
     8.2, gap=0.010)
cursor -= 0.010
# diverging gradient bar, same width as the map
grad = np.linspace(0, 1, 256).reshape(1, -1)
hbar = 0.050
ytop = cursor
lax.imshow(grad, extent=(xL, xR, ytop - hbar, ytop), aspect="auto",
           cmap="RdBu", zorder=3)
from matplotlib.patches import Rectangle
lax.add_patch(Rectangle((xL, ytop - hbar), xR - xL, hbar, fill=False, lw=0.6))
cursor = ytop - hbar - 0.006
lax.text(xL, cursor, "drier / degraded", fontsize=7.5, va="top", color="#b2182b")
lax.text(xR, cursor, "wetter / greener", fontsize=7.5, va="top", ha="right",
         color="#2166ac")
cursor -= lh(7.5)
para("Red marks change toward a drier, more degraded surface \u2014 a decrease in "
     "NDWI, MNDWI, NDVI, NDMI, or an increase in BSI (its scale is reversed).",
     8.0, gap=0.012)
# significance swatches
cursor -= 0.012
sw = 0.05; sh = lh(8.0) * 0.85
lax.add_patch(Rectangle((xL, cursor - sh), sw, sh, facecolor="#c23b3b",
                        ec="0.4", lw=0.4))
lax.text(xL + sw + 0.02, cursor - sh*0.15, "significant (p < 0.05)",
         fontsize=7.8, va="top")
cursor -= lh(7.8) + 0.004
lax.add_patch(Rectangle((xL, cursor - sh), sw, sh, facecolor="#e6b3b3",
                        ec="0.4", lw=0.4))
lax.text(xL + sw + 0.02, cursor - sh*0.15, "not significant (p \u2265 0.05)",
         fontsize=7.8, va="top")
cursor -= lh(7.8)
para("Significance from Kendall\u2019s \u03c4 (|\u03c4| \u2265 0.21 \u2248 p < 0.05, "
     "n = 42).", 7.6, italic=True, color="#333333", gap=0.006)
para("Data: complete Landsat Collection 2 archive, Google Earth Engine. "
     "Trend: Theil\u2013Sen slope; significance: Mann\u2013Kendall.",
     7.4, italic=True, color="#444444", gap=0.012)

fig.savefig("Figure_5.png", dpi=300, bbox_inches="tight", facecolor="white",
            pad_inches=0.12)
fig.savefig("Figure_5.pdf", bbox_inches="tight", facecolor="white", pad_inches=0.12)
print("wrote Figure_5.png and Figure_5.pdf  (NDVI-map width frac: %.3f-%.3f)" % (xL, xR))
for nm in names:
    t = tau[nm]; frac = np.mean(np.abs(t[np.isfinite(t)]) >= TAU_CRIT)*100
    print(f"{nm:6s} significant {frac:5.1f}%  median slope {np.nanmedian(slope[nm]):+.4f}/yr")
