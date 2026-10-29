"""Step 3: files the interactive page loads.

data/zgrid.png     0.1 degree grid (3600 x 1450, 85N to 60S) of time zone index + 1 in red (low byte) and green (high byte)
data/page.json     zones (id, official offset on each change date of 2026), places for search and names, chart series
data/tzlines.json  simplified lines where the clock changes between neighbouring zones (any day of 2026)
data/borders.json  Natural Earth 1:50m country outlines (rounded) for the borders layer
data/hills.png     shaded relief in Web Mercator (copied from the games-on-the-map study; AWS Terrain Tiles)
"""
import json, os, shutil, sys, zipfile
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape, mapping
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from common import *

Z = load_json(os.path.join(WORK, "zones.json"))
ids = Z["ids"]; OFF = np.array(Z["days"]); IX = {t: i for i, t in enumerate(ids)}
OFFICIAL = {"Asia/Urumqi": "Asia/Shanghai"}
OFFO = OFF.copy()
for a, b in OFFICIAL.items(): OFFO[IX[a]] = OFF[IX[b]]
STD = np.array(Z["std"]); STDO = STD.copy()
for a, b in OFFICIAL.items(): STDO[IX[a]] = STD[IX[b]]

# ---- grid image ----
G = np.load(os.path.join(WORK, "grid_idx.npz"))["g"]
rgb = np.zeros(G.shape + (3,), np.uint8); rgb[..., 0] = G & 255; rgb[..., 1] = G >> 8
Image.fromarray(rgb, "RGB").save(os.path.join(DATA, "zgrid.png"), optimize=True)

# ---- zones: transitions ----
def trans(row):
    t = [[1, int(row[0])]]
    for d in range(1, len(row)):
        if row[d] != row[d - 1]: t.append([d + 1, int(row[d])])
    return t
zones = [{"id": t, "std": int(STDO[i]), "tr": trans(OFFO[i])} for i, t in enumerate(ids)]
zones[IX["Asia/Urumqi"]]["alt"] = {"name": "Xinjiang time", "std": int(STD[IX["Asia/Urumqi"]])}

# ---- places for search and names ----
PL = pd.read_pickle(os.path.join(WORK, "places.pkl.gz"))
keep = (PL.population >= 15000) | ((PL.country.isin(["ES", "PT", "GB", "IE"])) & (PL.population >= 5000))
pl = PL[keep].sort_values("population", ascending=False)
places = [[r.name, r.country, round(float(r.lat), 3), round(float(r.lon), 3), int(r.population)] for r in pl.itertuples()]
countries_iso = pd.read_csv(os.path.join(DATA, "countries.csv"))

# ---- Galicia chart series ----
ser = load_json(os.path.join(WORK, "galicia_series.json"))
gal = {k: {"rise": v["rise"], "set": v["set"]} for k, v in ser.items()}

R = load_json(os.path.join(DATA, "results.json"))
page = {"zones": zones, "places": places, "gal": gal, "year": YEAR,
        "grid": {"n": 85, "s": -60, "res": 0.1, "w": int(G.shape[1]), "h": int(G.shape[0])}}
save_json(page, os.path.join(DATA, "page.json"), separators=(",", ":"))

# ---- tz change lines ----
print("zone lines")
with zipfile.ZipFile(os.path.join(SRC, "timezones.geojson.zip")) as z:
    gj = json.loads(z.read("combined.json"))
geoms = {f["properties"]["tzid"]: shape(f["geometry"]) for f in gj["features"]}
del gj
sig = {}
for t in ids: sig.setdefault(tuple(OFFO[IX[t]]), []).append(t)
def polys(g):
    """Polygonal parts only (make_valid can return collections with stray lines, whose boundary is empty)."""
    parts = [q for q in shapely.get_parts(g) if q.geom_type in ("Polygon", "MultiPolygon")]
    return shapely.union_all(parts)
groups = []
for k, ts in sig.items():
    gs = [polys(shapely.make_valid(shapely.simplify(geoms[t], 0.005))) for t in ts]
    groups.append(polys(shapely.union_all(gs)))
# shared edges only: the part of each group's outline that lies against another group
groups = [g.intersection(shapely.box(-180, -60, 180, 90)) for g in groups]
groups = [polys(g) for g in groups if not g.is_empty]
tree = shapely.STRtree(groups)
lines = []
for i, g in enumerate(groups):
    bd = g.boundary
    for j in tree.query(g):
        if j <= i: continue
        seg = bd.intersection(groups[j].buffer(0.02))
        if not seg.is_empty: lines.append(shapely.simplify(seg, 0.01))
flat = []
def walk(g):
    for q in shapely.get_parts(g):
        if q.geom_type == "LineString": flat.append(q)
        elif q.geom_type in ("MultiLineString", "GeometryCollection"): walk(q)
for l in lines: walk(l)
L = shapely.line_merge(shapely.MultiLineString(flat))
def rnd(geom):
    m = mapping(geom)
    def r(c):
        return [round(c[0], 3), round(c[1], 3)] if isinstance(c[0], float) else [r(x) for x in c]
    m["coordinates"] = r(m["coordinates"]); return m
save_json({"type": "Feature", "properties": {}, "geometry": rnd(L)}, os.path.join(DATA, "tzlines.json"), separators=(",", ":"))

# ---- borders (Natural Earth 1:50m) ----
ne = load_json(os.path.join(NE, "ne_50m_admin_0_countries.geojson"))
feats = []
for f in ne["features"]:
    g = shapely.simplify(shape(f["geometry"]), 0.02)
    feats.append({"type": "Feature", "properties": {"n": f["properties"].get("NAME")}, "geometry": rnd(g)})
save_json({"type": "FeatureCollection", "features": feats}, os.path.join(DATA, "borders.json"), separators=(",", ":"))

src = "/home/claude/hist/games-on-the-map/data/hills.png"
if not os.path.exists(os.path.join(DATA, "hills.png")): shutil.copy(src, os.path.join(DATA, "hills.png"))
for fn in ["zgrid.png", "page.json", "tzlines.json", "borders.json", "hills.png"]:
    print(fn, os.path.getsize(os.path.join(DATA, fn)) // 1024, "KB")
print("places", len(places))
