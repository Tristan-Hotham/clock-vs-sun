"""Step 1: read the time zone boundaries, the IANA rules for 2026, Kontur population and GeoNames places.

Writes to work/ (intermediates, needed to rebuild):
  zones.json      zone ids, standard offset and the clock offset (minutes from UTC) on every day of 2026
  grid_idx.npz    0.1 degree grid (85N to 60S, 180W to 180E) of zone index + 1 (0 = outside every zone)
  pop.csv.gz      Kontur population hexagons (H3 resolution 4, about 22 km) with centre, zone and country
  places.csv.gz   GeoNames places of 1,000 or more with zone from the boundaries and from GeoNames
"""
import gzip, io, json, os, sqlite3, sys, zipfile, datetime as dt
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape
from zoneinfo import ZoneInfo
import h3
sys.path.insert(0, os.path.dirname(__file__))
from common import *

# ---------- time zone polygons ----------
print("reading time zone boundaries")
with zipfile.ZipFile(os.path.join(SRC, "timezones.geojson.zip")) as z:
    gj = json.loads(z.read("combined.json"))
ids = [f["properties"]["tzid"] for f in gj["features"]]
geoms = [shape(f["geometry"]) for f in gj["features"]]
del gj
geoms = [g if g.is_valid else shapely.make_valid(g) for g in geoms]
for g in geoms: shapely.prepare(g)
print(len(ids), "zones")

# ---------- IANA offsets for every day of 2026 ----------
days = [dt.date(YEAR, 1, 1) + dt.timedelta(d) for d in range(365)]
def offsets(tzid):
    z = ZoneInfo(tzid)
    return [int(dt.datetime(d.year, d.month, d.day, 12, tzinfo=z).utcoffset().total_seconds() // 60) for d in days]
OFF = np.array([offsets(t) for t in ids], dtype=np.int16)
# "standard" offset: the smaller of the offsets in force on 15 December 2026 and 15 June 2027, i.e. the clock
# without daylight saving under the rules as they stand at the end of 2026 (Morocco moved to plain UTC on
# 20 September 2026). Using offsets rather than the dst flag avoids Ireland's "negative DST" convention.
def off_at(tzid, d):
    return int(dt.datetime(d.year, d.month, d.day, 12, tzinfo=ZoneInfo(tzid)).utcoffset().total_seconds() // 60)
std = [min(off_at(t, dt.date(YEAR, 12, 15)), off_at(t, dt.date(YEAR + 1, 6, 15))) for t in ids]
zones = {"ids": ids, "std": std, "tz_version": TZ_VERSION, "year": YEAR, "days": OFF.tolist()}
save_json(zones, os.path.join(WORK, "zones.json"))
print("tz version", TZ_VERSION, "zones with a change in 2026:", int((OFF.max(1) != OFF.min(1)).sum()))

# ---------- 0.1 degree grid of zone index ----------
RES = 0.1; N0, S0 = 85.0, -60.0
ny, nx = int(round((N0 - S0) / RES)), int(round(360 / RES))
grid = np.zeros((ny, nx), dtype=np.uint16)
lon_c = -180 + (np.arange(nx) + .5) * RES
lat_c = N0 - (np.arange(ny) + .5) * RES
for k, g in enumerate(geoms):
    x0, y0, x1, y1 = g.bounds
    i0, i1 = max(0, int((N0 - y1) / RES)), min(ny, int((N0 - y0) / RES) + 1)
    j0, j1 = max(0, int((x0 + 180) / RES)), min(nx, int((x1 + 180) / RES) + 1)
    if i0 >= i1 or j0 >= j1: continue
    LO, LA = np.meshgrid(lon_c[j0:j1], lat_c[i0:i1])
    m = shapely.contains_xy(g, LO, LA)
    sub = grid[i0:i1, j0:j1]; sub[m] = k + 1
np.savez_compressed(os.path.join(WORK, "grid_idx.npz"), g=grid)
print("grid", grid.shape, "cells in a zone", int((grid > 0).sum()))

tree = shapely.STRtree(geoms)
def zone_of(lat, lon):
    pts = shapely.points(lon, lat)
    out = np.full(len(pts), -1, dtype=np.int32)
    pi, gi = tree.query(pts, predicate="within")
    out[pi] = gi
    miss = np.where(out < 0)[0]
    if len(miss):
        pi2, gi2 = tree.query_nearest(pts[miss], max_distance=0.3, all_matches=False)
        out[miss[pi2]] = gi2
    return out

# ---------- countries (Natural Earth 1:10m) ----------
ne = json.load(open(os.path.join(NE, "ne_10m_admin_0_countries.geojson")))
cn = [(f["properties"].get("ADM0_A3"), f["properties"].get("NAME"), f["properties"].get("ISO_A2_EH") or f["properties"].get("ISO_A2")) for f in ne["features"]]
cg = [shape(f["geometry"]) for f in ne["features"]]; cg = [g if g.is_valid else shapely.make_valid(g) for g in cg]
ctree = shapely.STRtree(cg)
def country_of(lat, lon):
    pts = shapely.points(lon, lat)
    out = np.full(len(pts), -1, dtype=np.int32)
    pi, gi = ctree.query(pts, predicate="within"); out[pi] = gi
    miss = np.where(out < 0)[0]
    if len(miss):
        pi2, gi2 = ctree.query_nearest(pts[miss], max_distance=0.3, all_matches=False); out[miss[pi2]] = gi2
    return out

# ---------- Kontur population ----------
print("population")
gp = os.path.join(WORK, "kontur_r4.gpkg")
with gzip.open(os.path.join(SRC, "kontur_population_20231101_r4.gpkg.gz")) as fi, open(gp, "wb") as fo:
    fo.write(fi.read())
con = sqlite3.connect(gp)
pop = pd.read_sql("select h3, population from population", con); con.close(); os.remove(gp)
ll = np.array([h3.cell_to_latlng(h) for h in pop.h3])
pop["lat"], pop["lon"] = ll[:, 0].round(4), ll[:, 1].round(4)
pop["zone"] = zone_of(pop.lat.values, pop.lon.values)
ci = country_of(pop.lat.values, pop.lon.values)
pop["adm0"] = [cn[i][0] if i >= 0 else "" for i in ci]
pop["country"] = [cn[i][1] if i >= 0 else "" for i in ci]
pop["iso2"] = [cn[i][2] if i >= 0 else "" for i in ci]
pop.drop(columns="h3").to_csv(os.path.join(WORK, "pop.csv.gz"), index=False)
print("hexes", len(pop), "people", int(pop.population.sum()), "unzoned people", int(pop.population[pop.zone < 0].sum()))

# ---------- GeoNames places ----------
print("places")
G = json.load(gzip.open(os.path.join(SRC, "cvs_geonames_cities1000.json.gz")))
pl = pd.DataFrame(G["rows"], columns=G["fields"])
pl = pl[pl.population >= 1000].reset_index(drop=True)
pl["zone"] = zone_of(pl.lat.values, pl.lon.values)
pl.to_csv(os.path.join(WORK, "places.csv.gz"), index=False)
meta = {"geonames_retrieved": G["retrieved"][:10], "geonames_rows": len(G["rows"]), "places": len(pl)}
save_json(meta, os.path.join(WORK, "prepare_meta.json"))
print(meta)
