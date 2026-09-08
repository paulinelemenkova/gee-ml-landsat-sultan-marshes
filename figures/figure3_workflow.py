#!/usr/bin/env python3
"""
Figure 3 - Workflow of the proposed AI-assisted framework for the Sultan Marshes.
Recoloured with the ColorBrewer "Paired" qualitative palette: light header
bands with dark, same-hue titles, borders and badges (lighter than the previous
dark solid bands).

Main spine: (1) data acquisition -> (2) preprocessing -> (3) index extraction
-> (4) AI modelling -> (5) outputs, with three offshoots feeding the outputs
(trend analysis; explainable AI; evaluation with an iterate loop).

Output: Figure_3.png (300 dpi) + Figure_3.pdf
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

OUT_PNG = "Figure_3.png"
W, H = 15.6, 9.4
plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none"})

# ColorBrewer "Paired" palette, as (light, dark) hue pairs
PAIR = {
    "blue":   ("#a6cee3", "#1f78b4"),
    "green":  ("#b2df8a", "#33a02c"),
    "red":    ("#fb9a99", "#e31a1c"),
    "orange": ("#fdbf6f", "#ff7f00"),
    "purple": ("#cab2d6", "#6a3d9a"),
    "brown":  ("#ffff99", "#b15928"),
}
S1, S2, S3, S4, S5 = PAIR["blue"], PAIR["green"], PAIR["orange"], PAIR["purple"], PAIR["red"]
TREND, XAI, EVAL = PAIR["blue"], PAIR["purple"], PAIR["brown"]
INK, GREY = "#1a1a1a", "#8a8a8a"

fig = plt.figure(figsize=(W, H), dpi=300)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")

def card(x, y, w, h, pair, num, title, bullets, hh=0.52, tsize=10.4, bsize=8.4):
    light, dark = pair
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0,rounding_size=0.03", linewidth=1.8,
        edgecolor=dark, facecolor="#ffffff", zorder=2))
    ax.add_patch(FancyBboxPatch((x, y + h - hh), w, hh,
        boxstyle="round,pad=0,rounding_size=0.03", linewidth=0,
        facecolor=light, zorder=3))
    cy = y + h - hh / 2
    if num is not None:
        ax.add_patch(Circle((x + 0.30, cy), 0.185, facecolor=dark,
                     edgecolor="none", zorder=5))
        ax.text(x + 0.30, cy, str(num), ha="center", va="center",
                color="white", fontsize=10, fontweight="bold", zorder=6)
        tx = x + 0.56
    else:
        tx = x + 0.20
    ax.text(tx, cy, title, ha="left", va="center", color=dark,
            fontsize=tsize, fontweight="bold", zorder=6)
    by = y + h - hh - 0.30
    for b in bullets:
        ax.text(x + 0.20, by, "\u2022 " + b, ha="left", va="center",
                color=INK, fontsize=bsize, zorder=5)
        by -= 0.315

def arrow(x0, y0, x1, y1, color=GREY, lw=2.6, ms=15, ls="-"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1),
        arrowstyle="-|>,head_width=0.5,head_length=0.9", mutation_scale=ms,
        linewidth=lw, color=color, linestyle=ls, shrinkA=0, shrinkB=0, zorder=1))

def elbow(pts, color=GREY, lw=2.6, ms=15):
    for i in range(len(pts) - 2):
        ax.plot([pts[i][0], pts[i+1][0]], [pts[i][1], pts[i+1][1]],
                color=color, lw=lw, zorder=1, solid_capstyle="round")
    arrow(pts[-2][0], pts[-2][1], pts[-1][0], pts[-1][1], color, lw, ms)

def lbl(x, y, t, color="#444444", size=8.0):
    ax.text(x, y, t, ha="center", va="center", fontsize=size, style="italic",
            color=color, zorder=6,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9))

# header
ax.add_patch(FancyBboxPatch((0.25, 8.96), W - 0.5, 0.44,
    boxstyle="round,pad=0,rounding_size=0.05", linewidth=0,
    facecolor="#eef2f4", zorder=1))
ax.text(0.5, 9.18, "Processing workflow: from the complete Landsat archive to "
        "explainable ecological assessment", ha="left", va="center",
        fontsize=12.5, fontweight="bold", color=INK)

# main spine
CY0, CH = 5.15, 2.20
xs = [0.35, 3.25, 6.15, 9.05, 11.95]
CW = 2.55
mid = CY0 + CH / 2
card(xs[0], CY0, CW, CH, S1, 1, "Data acquisition",
     ["Landsat C2 SR (TM\u2013OLI-2)", "TerraClimate; SRTM DEM",
      "Park / Ramsar boundaries", "Google Earth Engine, 1984\u20132025"])
card(xs[1], CY0, CW, CH, S2, 2, "Preprocessing",
     ["QA/Fmask cloud & shadow mask", "Growing-season (May\u2013Oct) median",
      "Reproject UTM 36N, 30 m", "Annual cloud-free composites"])
card(xs[2], CY0, CW, CH, S3, 3, "Index extraction",
     ["NDVI, NDWI, MNDWI, NDMI", "NBR, BSI, TCW",
      "Per-pixel annual stacks", "Continuous 1984\u20132025 series"])
card(xs[3], CY0, CW, CH, S4, 4, "AI modelling",
     ["Random Forest (baseline)", "XGBoost / LightGBM / CatBoost",
      "LSTM / Temporal CNN", "Five condition classes"])
card(xs[4], CY0, CW, CH, S5, 5, "Outputs",
     ["Ecological-condition maps", "Trend & hotspot maps",
      "Driver ranking", "Future drying-risk maps"])
for i in range(4):
    arrow(xs[i] + CW, mid, xs[i+1] - 0.02, mid, color=GREY)

# offshoots
tx, tw, ty, th = xs[2], CW, 2.72, 2.00
card(tx, ty, tw, th, TREND, None, "Feature engineering & trends",
     ["Temporal features (mean, SD, CV)", "Theil\u2013Sen slope",
      "Mann\u2013Kendall significance", "Anomalies, moving averages"],
     hh=0.46, tsize=9.2, bsize=8.1)
arrow(xs[2] + CW/2, CY0, xs[2] + CW/2, ty + th + 0.02, color=TREND[1])
lbl(xs[2] + CW/2, (CY0 + ty + th)/2, "temporal stack", TREND[1])

ex, ew, ey, eh = xs[3], CW, 2.72, 2.00
card(ex, ey, ew, eh, EVAL, None, "Model evaluation",
     ["OA, precision, recall, F1", "Cohen\u2019s \u03ba, AUC-ROC",
      "Confusion matrices", "Train/val loss, early stopping"],
     hh=0.46, tsize=9.2, bsize=8.1)
arrow(xs[3] + CW*0.72, CY0, xs[3] + CW*0.72, ey + eh + 0.02, color=EVAL[1])
arrow(xs[3] + CW*0.28, ey + eh + 0.02, xs[3] + CW*0.28, CY0 - 0.005,
      color=EVAL[1], ls=(0, (4, 3)), lw=2.0, ms=12)
lbl(xs[3] + CW*0.28, (CY0 + ey + eh)/2, "iterate", EVAL[1])
lbl(xs[3] + CW*0.72, (CY0 + ey + eh)/2, "evaluate", EVAL[1])

ax0, aw, ay0, ah = xs[3], CW, 7.60, 1.25
card(ax0, ay0, aw, ah, XAI, None, "Explainable AI",
     ["SHAP (global + local)", "Permutation importance; PDP / ALE"],
     hh=0.42, tsize=9.2, bsize=8.0)
arrow(xs[3] + CW/2, CY0 + CH, xs[3] + CW/2, ay0 - 0.02, color=XAI[1])
lbl(xs[3] + CW/2 + 0.62, (CY0 + CH + ay0)/2, "attribution", XAI[1])

# feed-ins to outputs
ox = xs[4] + CW/2
elbow([(xs[2] + CW/2, ty), (xs[2] + CW/2, 2.28), (13.05, 2.28),
       (13.05, CY0 - 0.02)], color=TREND[1])
lbl(10.0, 2.28, "trend maps", TREND[1])
elbow([(ax0 + aw, ay0 + ah/2), (ox + 0.30, ay0 + ah/2),
       (ox + 0.30, CY0 + CH + 0.02)], color=XAI[1])
lbl(ox + 0.30, ay0 + ah/2 + 0.24, "driver ranking", XAI[1])

ax.text(W/2, 0.72,
        "Open-access data  \u00b7  Google Earth Engine + Python (scikit-learn, "
        "TensorFlow, SHAP)  \u00b7  reproducible and transferable",
        ha="center", va="center", fontsize=8.6, style="italic", color="#555555")

fig.savefig(OUT_PNG, dpi=300, bbox_inches="tight", facecolor="white", pad_inches=0.12)
fig.savefig("Figure_3.pdf", bbox_inches="tight", facecolor="white", pad_inches=0.12)
print("wrote", OUT_PNG, "and Figure_3.pdf")
