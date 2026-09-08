#!/usr/bin/env bash
# =============================================================================
# Figure 1 - Study area: the Sultan Marshes (Sultansazligi), Kayseri, Turkiye
# -----------------------------------------------------------------------------
# Backend : GMT 6 (classic mode). Needs internet on first run to (a) download
#           the SRTMGL3 3-arc-sec relief tile from the GMT data server and
#           (b) query OpenStreetMap (Overpass) for wetland / hydrography layers.
#
# Data
#   Relief    : @earth_relief_03s  (SRTMGL3 ~90 m, NASA/USGS)
#   Wetlands  : OpenStreetMap  natural=water | natural=wetland
#   Hydrography + National Park boundary (OSM relation 271965)
#
# Turkish place names (correct Turkish -> ASCII used on the map):
#   Yesilhisar(Yesilhisar) Yahyali(Yahyali) Ovaciftlik(Ovaciftlik)
#   Soysalli(Soysalli) Sindelhoyuk(Sindelhoyuk) Cayirozu(Cayirozu)
#   Kopcu(Kopcu) Kovali(Kovali) Develi Yenihayat ; Col Golu / Sobe Golu / Yay
#
# Design notes
#   * Per-label fonts are supplied ONLY on the command line via -F+f...+j...;
#     label files hold "lon lat text" only (prevents "12p,Helvetica,.." text).
#   * Locator inset (B) is placed INSIDE panel A. The Cartesian overlay used to
#     draw its white box shares the SHIFTED plot origin (after -X/-Y), so the
#     map plot box spans (0,0)-(17,AH) in that system; do NOT add OX/OY.
#     If you change PROJ/REG/OX/OY, recompute AH with:
#         gmt mapproject -R$REG -J$PROJ -W      (-> 17  16.4829  => AH=16.48)
#
# Output: fig01_sultan_marshes_90m.pdf (vector) + .png (300 dpi)
# =============================================================================
set -e
D=./gmt_layers
OUT=.
mkdir -p "$D"

# -----------------------------------------------------------------------------
# 1. Fetch + classify OSM polygons/lines -> GMT multisegment text files
# -----------------------------------------------------------------------------
python3 - "$D" << 'PYEOF'
import sys, urllib.request, urllib.parse, json, socket, time
D = sys.argv[1]
socket.setdefaulttimeout(180)
EPS = ["https://overpass-api.de/api/interpreter",
       "https://overpass.kumi.systems/api/interpreter"]
BBOX = "38.08,34.98,38.56,35.58"          # S,W,N,E
Q = f"""[out:json][timeout:180];
(way["natural"="water"]({BBOX});way["natural"="wetland"]({BBOX});
 relation["natural"="wetland"]({BBOX});relation["natural"="water"]({BBOX});
 way["waterway"="river"]({BBOX});relation(271965););
out geom;"""

def overpass():
    for ep in EPS:
        for _ in range(4):                       # Overpass can 504; retry
            try:
                data = urllib.parse.urlencode({"data": Q}).encode()
                req = urllib.request.Request(ep, data=data,
                        headers={"User-Agent": "sultan-marshes-fig/2.3"})
                return json.loads(urllib.request.urlopen(req).read().decode())
            except Exception as e:
                print("retry", ep, repr(e)[:60]); time.sleep(20)
    raise SystemExit("Overpass unavailable")

j = overpass()

def rings(el):
    out = []
    if el["type"] == "way" and el.get("geometry"):
        out.append([[p["lon"], p["lat"]] for p in el["geometry"]])
    elif el["type"] == "relation":
        for m in el.get("members", []):
            if m.get("role") == "outer" and "geometry" in m:
                out.append([[p["lon"], p["lat"]] for p in m["geometry"]])
    return out

layers = {k: [] for k in
          ["openwater", "saltmarsh", "marsh", "reedbed", "wetmeadow", "reservoir"]}
rivers, park = [], []
for el in j["elements"]:
    t = el.get("tags", {}); nm = t.get("name", "")
    nat, wet = t.get("natural", ""), t.get("wetland", "")
    if t.get("waterway") == "river" and el.get("geometry"):
        rivers.append([[p["lon"], p["lat"]] for p in el["geometry"]]); continue
    if el["type"] == "relation" and el.get("id") == 271965:
        park += rings(el); continue
    for c in rings(el):
        if len(c) < 4: continue
        if c[0] != c[-1]: c = c + [c[0]]
        if nat == "water":
            layers["reservoir" if "Baraj" in nm else "openwater"].append(c)
        elif nat == "wetland":
            key = {"saltmarsh": "saltmarsh", "reedbed": "reedbed",
                   "wet_meadow": "wetmeadow"}.get(wet, "marsh")
            layers[key].append(c)

def wr(fn, polys):
    with open(fn, "w") as f:
        for c in polys:
            f.write(">\n")
            for x, y in c: f.write(f"{x} {y}\n")

for k, v in layers.items(): wr(f"{D}/{k}.txt", v)
wr(f"{D}/rivers.txt", rivers)
wr(f"{D}/park.txt", park)

# --- 10 cities/towns (verified names, ASCII). side = label anchor:
#     R=label LEFT of dot(right-just), L=label RIGHT(left-just), T=above, B=below
places = [("Yesilhisar", 35.0887, 38.3523, "R"),
          ("Develi",     35.4901, 38.3879, "L"),
          ("Yahyali",    35.3541, 38.1003, "L"),
          ("Ovaciftlik", 35.1941, 38.2368, "R"),
          ("Soysalli",   35.3653, 38.3821, "L"),
          ("Sindelhoyuk",35.3776, 38.3424, "L"),
          ("Cayirozu",   35.2958, 38.4203, "T"),
          ("Yenihayat",  35.2912, 38.2603, "L"),
          ("Kopcu",      35.3742, 38.2332, "L"),
          ("Kovali",     35.1708, 38.1826, "B")]
with open(f"{D}/places.txt", "w") as f:
    for nm, x, y, s in places: f.write(f"{x} {y}\n")
grp = {"L": [], "R": [], "T": [], "B": []}
for nm, x, y, s in places: grp[s].append((x, y, nm))
for s, arr in grp.items():
    with open(f"{D}/lab_{s}.txt", "w") as f:
        for x, y, nm in arr: f.write(f"{x} {y} {nm}\n")

# --- feature labels: coordinates + text ONLY (font supplied via -F on CLI) ---
def wl(fn, items):
    with open(fn, "w") as f:
        for x, y, tx in items: f.write(f"{x} {y} {tx}\n")
wl(f"{D}/lab_water.txt",     [(35.283, 38.345, "Lake Yay"),
                              (35.205, 38.487, "Col Golu"),
                              (35.228, 38.417, "Sobe Golu")])
# SULTAN MARSHES centred at 38 deg 16 min N (38.2667 N), same lon 35.222
wl(f"{D}/lab_marshname.txt", [(35.222, 38.2667, "SULTAN"),
                              (35.222, 38.2537, "MARSHES")])
wl(f"{D}/lab_reed.txt",      [(35.315, 38.418, "Kepir reedbed")])
wl(f"{D}/lab_res.txt",       [(35.400, 38.168, "Agcasar Res.")])
wl(f"{D}/lab_basin.txt",     [(35.165, 38.455, "DEVELI BASIN")])   # off-white
wl(f"{D}/lab_basin2.txt",    [(35.165, 38.443, "(closed basin)")])
wl(f"{D}/erciyes.txt",       [(35.447, 38.545, "")])               # Mt Erciyes marker
print("OSM layers written to", D)
PYEOF

# -----------------------------------------------------------------------------
# 2. Relief basemap + hillshade  (3-arc-sec SRTMGL3, ~90 m)
# -----------------------------------------------------------------------------
REG=35.00/35.55/38.13/38.55        # study-area extent (W/E/S/N)
PROJ=M17c                          # Mercator, 17 cm wide
OX=5; OY=7                         # paper origin of panel A (cm)
PS=fig01.ps

gmt grdcut  @earth_relief_03s -R$REG -Gsm.nc
gmt grdgradient sm.nc -A315 -Ne0.6 -Gsm_int.nc
gmt makecpt -Cgeo -T1000/3400/50 -Z > relief.cpt

gmt set FONT_ANNOT_PRIMARY 9p,Helvetica,black FONT_LABEL 10p,Helvetica,black \
        MAP_FRAME_TYPE plain MAP_FRAME_PEN 1.1p,black MAP_TICK_LENGTH_PRIMARY 4p \
        MAP_TICK_LENGTH_SECONDARY 2p MAP_GRID_PEN_PRIMARY 0.25p,white@55,. \
        FORMAT_GEO_MAP ddd:mmF PS_MEDIA a2

# -----------------------------------------------------------------------------
# 3. MAIN PANEL (A)
# -----------------------------------------------------------------------------
gmt grdimage sm.nc -Ism_int.nc -Crelief.cpt -J$PROJ -R$REG -Y${OY}c -X${OX}c -K > $PS

# --- 200 m topographic contours, thin brown ---
gmt grdcontour sm.nc -C200 -Wthin,132/86/40@25 -J -R -O -K >> $PS

# --- wetland classes (broad -> narrow) ---
gmt psxy $D/wetmeadow.txt -J -R -G176/212/150@20 -L -O -K >> $PS
gmt psxy $D/marsh.txt     -J -R -G95/170/110      -L -O -K >> $PS
[ -s $D/reedbed.txt ] && gmt psxy $D/reedbed.txt -J -R -G45/120/75 -L -O -K >> $PS
gmt psxy $D/saltmarsh.txt -J -R -G70/160/175      -L -O -K >> $PS
gmt psxy $D/openwater.txt -J -R -G28/105/170      -L -O -K >> $PS
gmt psxy $D/reservoir.txt -J -R -G60/125/190 -Wthin,28/105/170 -L -O -K >> $PS
gmt psxy $D/rivers.txt    -J -R -W0.9p,60/120/190 -O -K >> $PS
gmt psxy $D/park.txt      -J -R -W1.8p,45/105/45   -O -K >> $PS
gmt psbasemap             -J -R -Bg0.1            -O -K >> $PS   # white graticule

# --- Mt Erciyes marker + label ---
gmt psxy $D/erciyes.txt -J -R -St0.42c -Ggray25 -Wthin,white -O -K >> $PS
echo "35.447 38.545 Mt. Erciyes (3916 m)" | \
  gmt pstext -J -R -F+f8p,Helvetica-Bold,gray15+jCB -Dj0/0.26c -Gwhite@25 -O -K >> $PS

# --- feature labels (font ONLY on the CLI) ---
gmt pstext $D/lab_water.txt     -J -R -F+f10.5p,Helvetica-BoldOblique,white+jCM  -O -K >> $PS
gmt pstext $D/lab_marshname.txt -J -R -F+f11p,Helvetica-BoldOblique,25/65/25+jCM -O -K >> $PS
gmt pstext $D/lab_reed.txt      -J -R -F+f8p,Helvetica-Oblique,20/55/20+jLM      -O -K >> $PS
gmt pstext $D/lab_res.txt       -J -R -F+f7p,Helvetica-Oblique,20/40/90+jCM      -O -K >> $PS
# Develi Basin: off-white, larger
gmt pstext $D/lab_basin.txt     -J -R -F+f10p,Helvetica-Oblique,250/249/240+jCM  -O -K >> $PS
gmt pstext $D/lab_basin2.txt    -J -R -F+f7.5p,Helvetica-Oblique,250/249/240+jCM -O -K >> $PS

# --- cities: enlarged YELLOW markers + labels (one pstext per anchor side) ---
gmt psxy  $D/places.txt -J -R -Sc0.22c -Gyellow -W0.6p,black -O -K >> $PS
gmt pstext $D/lab_L.txt -J -R -F+f9p,Helvetica-Bold,black+jLM -D0.20c/0  -Gwhite@30 -O -K >> $PS
gmt pstext $D/lab_R.txt -J -R -F+f9p,Helvetica-Bold,black+jRM -D-0.20c/0 -Gwhite@30 -O -K >> $PS
gmt pstext $D/lab_T.txt -J -R -F+f9p,Helvetica-Bold,black+jCB -D0/0.18c  -Gwhite@30 -O -K >> $PS
gmt pstext $D/lab_B.txt -J -R -F+f9p,Helvetica-Bold,black+jCT -D0/-0.18c -Gwhite@30 -O -K >> $PS

# --- scale bar (bottom-right, nudged WEST so "10 km" stays inside frame) ---
gmt psbasemap -J -R -Lg35.43/38.155+w10k+f+u+l"km" --FONT_LABEL=8p --FONT_ANNOT_PRIMARY=8p -O -K >> $PS
# --- north arrow ---
gmt psbasemap -J -R -Tdg35.505/38.51+w0.75c+f2+l,,,N --FONT_TITLE=11p -O -K >> $PS

# --- WESN frame; minor ticks: X = 9 per major (a0.15 f0.015),
#                              Y = 6 per major (a0.1  f0.0142857) ---
gmt psbasemap -J -R -Bxa0.15f0.015 -Bya0.1f0.0142857 -BWESN -O -K >> $PS

# --- elevation colorbar: 11 pt WHITE font, NO halo ---
gmt psscale -R$REG -J$PROJ -Crelief.cpt -DjBR+w4.0c/0.32c+o0.55c/1.25c+v+ml \
        -Bxa500f250 -By+l"m" \
        --FONT_ANNOT_PRIMARY=11p,Helvetica,white \
        --FONT_LABEL=11p,Helvetica,white \
        --MAP_FRAME_PEN=0.6p -O -K >> $PS

# --- panel tag A ---
echo "35.012 38.543 A" | gmt pstext -J -R -F+f16p,Helvetica-Bold,white+jLT -Gblack@25 -C28%/28% -O -K >> $PS

# -----------------------------------------------------------------------------
# 4. LOCATOR INSET (B) - inside the top-right of panel A
# -----------------------------------------------------------------------------
# Overlay Cartesian system shares the SHIFTED origin (after -X5 -Y7), so the
# map plot box spans (0,0)-(17,16.48). Panel: w=5.39 h=2.613, margin 0.12:
#   X1=17-0.12=16.88 ; X0=16.88-5.39=11.49 ; Y1=16.48-0.12=16.36 ; Y0=13.747
X0=11.49; Y0=13.747; X1=16.88; Y1=16.36    # white panel corners (overlay cm)
ICX=11.61; ICY=13.867; IMW=5.15            # inset-map offset + width (cm)
IREG=25.5/45/35.5/42.5                     # Turkiye extent

gmt psxy -R0/17/0/16.4829 -Jx1c -Gwhite -W0.8p,gray40 -O -K << PANEL >> $PS
$X0 $Y0
$X1 $Y0
$X1 $Y1
$X0 $Y1
$X0 $Y0
PANEL

gmt pscoast -R$IREG -JM${IMW}c -Xa${ICX}c -Ya${ICY}c -Ggray82 -Slightblue@40 \
        -N1/0.4p,gray45 -Wthinnest,gray55 -A150 -O -K >> $PS
gmt psxy -R$IREG -JM${IMW}c -Xa${ICX}c -Ya${ICY}c -W1.6p,red -O -K << 'BOX' >> $PS
34.7 37.95
35.85 37.95
35.85 38.75
34.7 38.75
34.7 37.95
BOX
# Turkiye label centred, just above Kayseri
gmt pstext -R$IREG -JM${IMW}c -Xa${ICX}c -Ya${ICY}c -F+f8p,Helvetica-Bold,gray20+jCM -O -K << 'TT' >> $PS
36.3 40.2 T U R K I Y E
TT
gmt pstext -R$IREG -JM${IMW}c -Xa${ICX}c -Ya${ICY}c -F+f7p,Helvetica-Oblique,red3+jLM -O -K << 'KK' >> $PS
37.2 38.9 Kayseri
KK
# B label same size as A (16 pt)
gmt pstext -R$IREG -JM${IMW}c -Xa${ICX}c -Ya${ICY}c -F+f16p,Helvetica-Bold,black+jLM -Gwhite@25 -O -K << 'BB' >> $PS
26.3 41.6 B
BB

# -----------------------------------------------------------------------------
# 5. LEGEND (narrowed to 4.17c so "Ovaciftlik" clears it)
# -----------------------------------------------------------------------------
cat > legend.txt << 'LEG'
G 0.05c
H 10p,Helvetica-Bold Legend
G 0.06c
D 0 0.5p
G 0.08c
S 0.25c s 0.28c 28/105/170  0.3p,black 0.72c Permanent water
G 0.03c
S 0.25c s 0.28c 70/160/175  0.3p,black 0.72c Saline / salt marsh
G 0.03c
S 0.25c s 0.28c 95/170/110  0.3p,black 0.72c Freshwater marsh
G 0.03c
S 0.25c s 0.28c 176/212/150 0.3p,black 0.72c Wet meadow / fringe
G 0.03c
S 0.25c s 0.28c 60/125/190  0.3p,black 0.72c Reservoir
G 0.05c
S 0.25c - 0.48c - 1.8p,45/105/45 0.72c National Park boundary
G 0.03c
S 0.25c - 0.48c - 0.9p,60/120/190 0.72c River / stream
G 0.03c
S 0.25c c 0.20c yellow 0.5p,black 0.72c City / town
G 0.03c
S 0.25c t 0.28c gray25 0.3p,white 0.72c Mountain peak
LEG
gmt pslegend legend.txt -R$REG -J$PROJ -DjBL+w4.17c+o0.15c/0.15c \
        -F+gwhite@8+p0.8p,gray40+r4p --FONT_ANNOT_PRIMARY=8p -O -K >> $PS

# --- credit line (no title) ---
echo "35.00 38.108 Basemap: SRTMGL3 3-arc-sec (~90 m) relief (NASA/USGS). Wetlands, hydrography and park boundary: OpenStreetMap. Mercator projection (WGS84). Made with GMT." | \
  gmt pstext -J -R -N -F+f6.5p,Helvetica,gray35+jLT -Dj0/0.35c -O -K >> $PS

gmt psxy -R -J -T -O >> $PS

# -----------------------------------------------------------------------------
# 6. Export
# -----------------------------------------------------------------------------
gmt psconvert $PS -A0.4c -Tf -P              # vector PDF
gmt psconvert $PS -A0.4c -TG -E300 -P        # 300-dpi transparent PNG
mv fig01.pdf "$OUT/fig01_sultan_marshes_90m.pdf"
mv fig01.png "$OUT/fig01_sultan_marshes_90m.png"
echo "Done -> fig01_sultan_marshes_90m.pdf / .png"
