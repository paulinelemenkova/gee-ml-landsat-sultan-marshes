#!/usr/bin/env python3
"""
Figure 1 - Conceptual framework of the AI-assisted wetland-monitoring approach
for the Sultan Marshes (Central Anatolia, Turkiye).

Corrected version (rebuilt in Matplotlib):
  * Data sources limited to those actually used in the paper
    (Landsat C2 SR, TerraClimate, SRTM DEM, Park/Ramsar boundaries).
    Removed: CHIRPS, ERA5, ESA WorldCover.
  * Seven spectral indices only (NDVI, NDWI, MNDWI, NDMI, NBR, BSI, TCW).
    Removed: LSWI.
  * Five ecological-condition classes (Very good -> Very poor).
    Replaced the previous four-class chips.
  * Study-area inset uses the provided relief map (fig02 panel A).

Output: Figure_1.png  (300 dpi)
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
import matplotlib.image as mpimg
import matplotlib.font_manager as fm

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
INSET_IMAGE = "fig02_geographic_setting.png"   # provided relief map (panel A)
OUT_PNG     = "Figure_1.png"
W, H        = 16.0, 9.2                         # canvas size (inches-equivalent)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "svg.fonttype": "none",
})

# palette (one colour per framework stage) --------------------------------
C_INPUT  = "#2f6f5e"   # teal-green   - inputs
C_PREP   = "#1f5f8b"   # blue         - preprocessing
C_IND    = "#2a9d8f"   # green-teal   - indicators
C_AI     = "#5c4b8a"   # purple       - AI / ML / XAI
C_OUT    = "#b5651d"   # brown-orange - outputs
C_APP    = "#c99700"   # gold         - applications
INK      = "#1a1a1a"
GREY     = "#8a8a8a"

# five ecological-condition classes (green -> red)
COND = [("Very good", "#1a7a3f"),
        ("Good",      "#7cb342"),
        ("Moderate",  "#f4c430"),
        ("Poor",      "#ef7d34"),
        ("Very poor", "#d62828")]

# ----------------------------------------------------------------------
# Canvas
# ----------------------------------------------------------------------
fig = plt.figure(figsize=(W, H), dpi=300)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")

def f2f(x, y, w, h):
    """data rectangle -> figure-fraction rectangle (for inset axes)."""
    return [x / W, y / H, w / W, h / H]

# ----------------------------------------------------------------------
# Drawing helpers
# ----------------------------------------------------------------------
def panel(x, y, w, h, edge, title, tnum=None, fill="#ffffff", lw=1.8,
          title_size=12, pad_round=0.02):
    """Rounded panel with a coloured title and an underline divider."""
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle=f"round,pad=0,rounding_size={pad_round}",
                         mutation_aspect=1,
                         linewidth=lw, edgecolor=edge, facecolor=fill,
                         zorder=2)
    ax.add_patch(box)
    ty = y + h - 0.34
    tx = x + 0.28
    if tnum is not None:
        r = 0.20
        cx, cy = x + 0.34, y + h - 0.34
        ax.add_patch(Circle((cx, cy), r, facecolor=edge, edgecolor="none",
                            zorder=4))
        ax.text(cx, cy, str(tnum), ha="center", va="center",
                color="white", fontsize=11, fontweight="bold", zorder=5)
        tx = cx + r + 0.16
    ax.text(tx, ty, title, ha="left", va="center", color=edge,
            fontsize=title_size, fontweight="bold", zorder=5)
    # underline
    ax.plot([x + 0.26, x + w - 0.26], [y + h - 0.62, y + h - 0.62],
            color=edge, lw=1.1, alpha=0.55, zorder=3)
    return box

def chip(x, y, w, h, text, edge, fill=None, tcolor=None, size=9.5, bold=False):
    fill = fill if fill else "#f4f6f8"
    tcolor = tcolor if tcolor else INK
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0,rounding_size=0.05",
                 linewidth=1.2, edgecolor=edge, facecolor=fill, zorder=4))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            color=tcolor, fontsize=size, fontweight="bold" if bold else "normal",
            zorder=5)

def bullet(x, y, text, size=9.6, color=INK, lead="\u2022 "):
    ax.text(x, y, lead + text, ha="left", va="center", color=color,
            fontsize=size, zorder=5)

def arrow(x0, y0, x1, y1, color=GREY, lw=2.4, ms=14):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1),
                 arrowstyle=f"-|>,head_width={ms/28:.2f},head_length={ms/18:.2f}",
                 mutation_scale=ms, linewidth=lw, color=color,
                 shrinkA=0, shrinkB=0, zorder=1))

# ======================================================================
# Header strip
# ======================================================================
ax.add_patch(FancyBboxPatch((0.25, 8.62), W - 0.5, 0.5,
             boxstyle="round,pad=0,rounding_size=0.06",
             linewidth=0, facecolor="#eef2f4", zorder=1))
ax.text(0.55, 8.87,
        "AI-assisted framework for monitoring ecological degradation and "
        "wetland drying in the Sultan Marshes",
        ha="left", va="center", fontsize=13.5, fontweight="bold", color=INK)
ax.text(W - 0.55, 8.87, "Landsat archive 1984\u20132025",
        ha="right", va="center", fontsize=11, style="italic", color="#4a4a4a")

# ======================================================================
# LEFT COLUMN  -  study area inset + input data
# ======================================================================
LX, LW = 0.30, 4.25

# --- study-area inset image ---
img_y0, img_y1 = 5.02, 8.34
ax.text(LX + LW/2, img_y1 + 0.14, "Study area: Sultan Marshes, Central Anatolia",
        ha="center", va="bottom", fontsize=10.5, fontweight="bold", color=INK)
try:
    im = mpimg.imread(INSET_IMAGE)
    ih, iw = im.shape[0], im.shape[1]
    aspect = iw / ih
    # fit image inside the box, centred
    box_w, box_h = LW - 0.30, img_y1 - img_y0
    if box_w / box_h > aspect:
        draw_h = box_h
        draw_w = box_h * aspect
    else:
        draw_w = box_w
        draw_h = box_w / aspect
    ix0 = LX + 0.15 + (box_w - draw_w) / 2
    iy0 = img_y0 + (box_h - draw_h) / 2
    iax = fig.add_axes(f2f(ix0, iy0, draw_w, draw_h), zorder=6)
    iax.imshow(im)
    iax.axis("off")
    for s in iax.spines.values():
        s.set_visible(True); s.set_edgecolor(C_INPUT); s.set_linewidth(1.4)
except FileNotFoundError:
    ax.text(LX + LW/2, (img_y0+img_y1)/2, "[ study-area map ]",
            ha="center", va="center", color=GREY, fontsize=11)

# --- input-data panel ---
panel(LX, 0.32, LW, 4.45, C_INPUT, "Input data (open-access)", tnum=1,
      title_size=11.5)
yb = 3.92
ax.text(LX + 0.30, yb, "Satellite \u2014 Landsat Collection 2 SR",
        fontsize=10, fontweight="bold", color=C_INPUT, va="center")
for i, t in enumerate(["Landsat 5 TM / 7 ETM+", "Landsat 8 OLI / 9 OLI-2",
                       "1984\u20132025, 30 m, Google Earth Engine"]):
    bullet(LX + 0.42, yb - 0.34 - i*0.30, t, size=9.3)
yb2 = 2.55
ax.text(LX + 0.30, yb2, "Climate \u2014 TerraClimate (~4 km)",
        fontsize=10, fontweight="bold", color=C_INPUT, va="center")
for i, t in enumerate(["Precipitation, temperature",
                       "Potential evapotranspiration, water balance"]):
    bullet(LX + 0.42, yb2 - 0.34 - i*0.30, t, size=9.3)
yb3 = 1.42
ax.text(LX + 0.30, yb3, "Ancillary",
        fontsize=10, fontweight="bold", color=C_INPUT, va="center")
for i, t in enumerate(["SRTM DEM (~30 m); hydrography",
                       "National Park / Ramsar boundaries; settlements"]):
    bullet(LX + 0.42, yb3 - 0.34 - i*0.30, t, size=9.3)

# ======================================================================
# MIDDLE PIPELINE  -  4 stacked stages
# ======================================================================
MX, MW = 4.92, 6.75
# stage vertical extents
s2 = (6.86, 1.48)   # (y0, height) preprocessing
s3 = (4.86, 1.72)   # indicators
s4 = (2.42, 2.16)   # AI/ML/XAI
s5 = (0.30, 1.88)   # outputs

# --- Stage 2: preprocessing ---
panel(MX, s2[0], MW, s2[1], C_PREP,
      "Preprocessing & time-series construction", tnum=2, title_size=11.5)
steps = ["Cloud &\nshadow mask\n(Fmask/QA)", "Growing-season\nmedian\ncomposites",
         "Annual series\n1984\u20132025", "Space\u2013time cube\n(pixel \u00d7 year)"]
cw = (MW - 0.7) / len(steps)
for i, s in enumerate(steps):
    cx = MX + 0.35 + i*cw
    chip(cx, s2[0] + 0.16, cw - 0.22, 0.62, s, C_PREP, fill="#eef4f9", size=8.6)
    if i < len(steps) - 1:
        arrow(cx + cw - 0.20, s2[0] + 0.47, cx + cw + 0.02, s2[0] + 0.47,
              color=C_PREP, lw=1.8, ms=11)

# --- Stage 3: indicators ---
panel(MX, s3[0], MW, s3[1], C_IND,
      "Spectral indicators (7) + temporal features", tnum=3, title_size=11.5)
inds = ["NDVI", "NDWI", "MNDWI", "NDMI", "NBR", "BSI", "TCW"]
cw3 = (MW - 0.7) / 7
for i, t in enumerate(inds):
    chip(MX + 0.35 + i*cw3, s3[0] + 0.80, cw3 - 0.14, 0.46, t, C_IND,
         fill="#e9f5f2", tcolor="#14584f", size=9.4, bold=True)
ax.text(MX + MW/2, s3[0] + 0.42,
        "per-pixel trajectories  \u2192  mean, min/max, CV, Sen slope, "
        "Mann\u2013Kendall, anomalies",
        ha="center", va="center", fontsize=9.2, color="#333333")

# --- Stage 4: AI / ML / XAI ---
panel(MX, s4[0], MW, s4[1], C_AI,
      "AI modelling & explainable AI", tnum=4, title_size=11.5)
sub_w = (MW - 0.9) / 3
subs = [("Machine learning",
         ["Random Forest (baseline)", "XGBoost \u00b7 LightGBM", "CatBoost"]),
        ("Deep learning",
         ["LSTM network", "Temporal CNN", "(temporal dependencies)"]),
        ("Explainable AI",
         ["SHAP", "Permutation importance", "PDP \u00b7 ALE"])]
for i, (h, items) in enumerate(subs):
    sx = MX + 0.35 + i*sub_w
    ax.add_patch(FancyBboxPatch((sx, s4[0] + 0.18), sub_w - 0.20, 1.34,
                 boxstyle="round,pad=0,rounding_size=0.05",
                 linewidth=1.3, edgecolor=C_AI, facecolor="#f1eef7", zorder=4))
    ax.text(sx + (sub_w-0.20)/2, s4[0] + 1.34, h, ha="center", va="center",
            fontsize=9.6, fontweight="bold", color=C_AI, zorder=5)
    for j, it in enumerate(items):
        ax.text(sx + 0.16, s4[0] + 1.06 - j*0.28, "\u2022 " + it,
                ha="left", va="center", fontsize=8.5, color=INK, zorder=5)
    if i < 2:
        arrow(sx + sub_w - 0.22, s4[0] + 0.85, sx + sub_w - 0.02,
              s4[0] + 0.85, color=C_AI, lw=1.6, ms=10)

# --- Stage 5: outputs ---
panel(MX, s5[0], MW, s5[1], C_OUT,
      "Outputs", tnum=5, title_size=11.5)
# 5-class ecological-condition legend
ax.text(MX + 0.35, s5[0] + 1.12, "Ecological condition (5 classes):",
        ha="left", va="center", fontsize=9.3, fontweight="bold", color=C_OUT)
cxx = MX + 0.35
for name, col in COND:
    ax.add_patch(FancyBboxPatch((cxx, s5[0] + 0.62), 0.28, 0.28,
                 boxstyle="round,pad=0,rounding_size=0.03",
                 linewidth=0.6, edgecolor="#555555", facecolor=col, zorder=4))
    ax.text(cxx + 0.34, s5[0] + 0.76, name, ha="left", va="center",
            fontsize=8.4, color=INK, zorder=5)
    cxx += 0.34 + 0.10 + 0.62 * (len(name) / 8.0) + 0.30
ax.text(MX + 0.35, s5[0] + 0.28,
        "+ trend maps  \u00b7  degradation hotspots  \u00b7  future drying-risk maps",
        ha="left", va="center", fontsize=9.0, color="#333333")

# vertical arrows down the pipeline
for (ya, yb) in [(s2[0], s3[0] + s3[1]), (s3[0], s4[0] + s4[1]),
                 (s4[0], s5[0] + s5[1])]:
    arrow(MX + MW/2, ya, MX + MW/2, yb + 0.02, color=GREY, lw=2.6, ms=15)

# elbow connector: Input-data panel -> pipeline (stage 2)
inx = LX + LW - 0.02          # right edge of the input panel
ax.plot([inx, inx], [4.77, 7.60], color=GREY, lw=2.6, zorder=1)
arrow(inx, 7.60, MX - 0.02, 7.60, color=GREY, lw=2.6, ms=15)

# ======================================================================
# RIGHT COLUMN  -  applications & impact
# ======================================================================
RX, RW = 11.92, 3.83
panel(RX, 0.32, RW, 8.02, C_APP, "Applications & impact", tnum=6,
      title_size=11.5)
apps = [("Early-warning system",
         "timely detection of ecological stress and drying"),
        ("Sustainable water management",
         "support water allocation and wetland conservation"),
        ("Biodiversity conservation",
         "protect habitats of migratory and resident birds"),
        ("Policy & decision support",
         "evidence-based planning and management"),
        ("Transferability",
         "applicable to other Ramsar wetlands and semi-arid basins")]
ay = 7.10
for title, desc in apps:
    ax.add_patch(Circle((RX + 0.45, ay), 0.14, facecolor=C_APP,
                        edgecolor="none", zorder=5))
    ax.text(RX + 0.78, ay, title, ha="left", va="center",
            fontsize=10, fontweight="bold", color=INK, zorder=5)
    # wrap description
    words = desc.split()
    lines, cur = [], ""
    for w in words:
        if len(cur + " " + w) > 34:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    for k, ln in enumerate(lines):
        ax.text(RX + 0.78, ay - 0.30 - k*0.24, ln, ha="left", va="center",
                fontsize=8.6, color="#444444", zorder=5)
    ay -= 0.30 + 0.24*len(lines) + 0.42

# arrow from outputs into applications
arrow(MX + MW, s5[0] + s5[1]/2, RX - 0.02, s5[0] + s5[1]/2,
      color=GREY, lw=2.6, ms=15)

# ----------------------------------------------------------------------
fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight", facecolor="white",
            pad_inches=0.12)
fig.savefig("Figure_1.pdf", bbox_inches="tight", facecolor="white",
            pad_inches=0.12)                       # vector copy for the journal
print("wrote", OUT_PNG, "and Figure_1.pdf")
