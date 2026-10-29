"""Step 2: every statistic. Writes data/results.json (all numbers used anywhere), data/places.csv,
data/countries.csv, data/zones.csv and data/population_by_offset.csv.

Measure. For a place at longitude L (degrees east), mean solar time runs 4*L minutes ahead of UTC.
Clock minus sun (minutes) on a day = the clock's offset from UTC that day minus 4*L. Positive: the clock is
ahead of the sun, so sunrise, solar noon and sunset all come later by the clock. "Standard" uses the zone's
standard offset (no daylight saving); "year average" averages the offset in force on each day of 2026.
Sunrise, sunset and solar noon use the NOAA solar equations (common.sun_times), which include the equation of time.

Official time. The boundary file puts most of Xinjiang in Asia/Urumqi (UTC+6), the informal "Xinjiang time"
many local people use. The legal time in all of China is Beijing time (UTC+8), so the main measure uses UTC+8
there, and Xinjiang time is reported as an alternative.
"""
import json, os, sys, datetime as dt
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import *

Z = load_json(os.path.join(WORK, "zones.json"))
ids = Z["ids"]; OFF = np.array(Z["days"], dtype=float); STD = np.array(Z["std"], dtype=float)
IX = {t: i for i, t in enumerate(ids)}
OFFICIAL = {"Asia/Urumqi": "Asia/Shanghai"}
OFF_OFF = OFF.copy(); STD_OFF = STD.copy()
for a, b in OFFICIAL.items():
    OFF_OFF[IX[a]] = OFF[IX[b]]; STD_OFF[IX[a]] = STD[IX[b]]
ANN = OFF_OFF.mean(1)
def wrap(e):
    """Clock minus sun folded into -12 to +12 hours (Tonga at UTC+13 near 175 degrees west is 40 minutes ahead, not 24 hours)."""
    return (np.asarray(e) + 720) % 1440 - 720
HAS_DST = OFF_OFF.max(1) != OFF_OFF.min(1)
DOY = np.arange(1, 366)
DATES = [dt.date(YEAR, 1, 1) + dt.timedelta(int(d) - 1) for d in DOY]
D_JUN21, D_DEC21 = 172 - 1, 355 - 1   # zero-based index of 21 June and 21 December 2026
ds = lambda i: DATES[i].strftime("%-d %B")
R = {"meta": {"year": YEAR, "tz_version": Z["tz_version"], "tz_boundaries": "timezone-boundary-builder 2026a",
              "zones": len(ids), "zones_with_change_2026": int(HAS_DST.sum()), "doi": DOI}}
R["meta"].update(load_json(os.path.join(WORK, "prepare_meta.json")))

# ---------------- population (Kontur, 22 km hexagons) ----------------
P = pd.read_csv(os.path.join(WORK, "pop.csv.gz"))
P = P[P.zone >= 0].copy()
z = P.zone.values; lon = P.lon.values; w = P.population.values
P["e_std"] = wrap(STD_OFF[z] - 4 * lon)
P["e_ann"] = wrap(ANN[z] - 4 * lon)
P["e_jun"] = wrap(OFF_OFF[z, D_JUN21] - 4 * lon)
P["e_dec"] = wrap(OFF_OFF[z, D_DEC21] - 4 * lon)
W = w.sum()
def share(mask): return float(w[mask].sum() / W)
def wq(x, q):
    o = np.argsort(x); c = np.cumsum(w[o]) / W; return float(x[o][np.searchsorted(c, q)])
pop = {"people": int(W), "hexes": int(len(P))}
for k in ["e_std", "e_ann", "e_jun", "e_dec"]:
    x = P[k].values
    pop[k] = {"mean": float((x * w).sum() / W), "median": wq(x, .5), "ahead": share(x > 0),
              "ahead_30": share(x > 30), "ahead_60": share(x > 60), "ahead_90": share(x > 90), "ahead_120": share(x > 120),
              "behind_30": share(x < -30), "behind_60": share(x < -60), "within_30": share(np.abs(x) <= 30),
              "within_15": share(np.abs(x) <= 15)}
pop["dst_share"] = share(HAS_DST[z])
pop["xinjiang_people"] = int(w[z == IX["Asia/Urumqi"]].sum())
R["population"] = pop
# histogram by 15-minute bins for the chart
bins = np.arange(-180, 301, 15)
hist = {}
for k in ["e_std", "e_ann", "e_jun", "e_dec"]:
    h, _ = np.histogram(np.clip(P[k].values, bins[0], bins[-1] - .01), bins=bins, weights=w)
    hist[k] = (h / W).round(5).tolist()
R["hist"] = {"bins": bins.tolist(), **hist}
pd.DataFrame({"from_min": bins[:-1], "to_min": bins[1:], **{f"share_{k}": hist[k] for k in hist}}).to_csv(os.path.join(DATA, "population_by_offset.csv"), index=False)

# ---------------- countries ----------------
rows = []
for (a3, name), g in P.groupby(["adm0", "country"]):
    gw = g.population.values; tot = gw.sum()
    if tot < 1: continue
    big = g[g.population >= 1000]
    rows.append({"adm0": a3, "country": name, "population": int(tot),
                 "e_std": float((g.e_std * gw).sum() / tot), "e_ann": float((g.e_ann * gw).sum() / tot),
                 "e_jun": float((g.e_jun * gw).sum() / tot), "e_dec": float((g.e_dec * gw).sum() / tot),
                 "e_ann_min": float(big.e_ann.min()) if len(big) else None, "e_ann_max": float(big.e_ann.max()) if len(big) else None,
                 "n_offsets": int(len(set(STD_OFF[g.zone.values]))), "dst": float(gw[HAS_DST[g.zone.values]].sum() / tot)})
C = pd.DataFrame(rows).sort_values("e_ann", ascending=False)
C = C.drop(columns=["e_ann_min", "e_ann_max", "n_offsets"])
iso_of = P.groupby("adm0").iso2.first()
C["iso2"] = C.adm0.map(iso_of)
C.round(2).to_csv(os.path.join(DATA, "countries.csv"), index=False)
CB = C[C.population >= 1_000_000]
R["countries"] = {"n": int(len(C)), "n_1m": int(len(CB)),
                  "ahead_most": CB.head(12)[["country", "population", "e_ann", "e_std", "e_jun", "e_dec"]].round(1).to_dict("records"),
                  "behind_most": CB.tail(8).iloc[::-1][["country", "population", "e_ann", "e_std"]].round(1).to_dict("records"),
                  "share_1m_ahead": float((CB.e_ann > 0).mean()), "n_1m_ahead": int((CB.e_ann > 0).sum()),
                  "n_1m_ahead_60": int((CB.e_ann > 60).sum())}
cidx = C.set_index("country")
def crow(n): r = cidx.loc[n]; return {k: (float(r[k]) if isinstance(r[k], (float, np.floating)) else int(r[k]) if isinstance(r[k], (int, np.integer)) else r[k]) for k in ["population", "e_std", "e_ann", "e_jun", "e_dec", "e_ann_min", "e_ann_max", "n_offsets", "dst"] if k in r.index and not (isinstance(r[k], float) and np.isnan(r[k]))}
R["country"] = {n: crow(n) for n in ["Spain", "France", "Portugal", "United Kingdom", "Ireland", "China", "India", "Argentina", "Russia",
                                       "United States of America", "Brazil", "Indonesia", "Japan", "Germany", "Mongolia", "Chile", "Iceland", "Kazakhstan",
                                       "Australia", "Canada", "Belgium", "Netherlands", "Poland", "Nepal", "Bangladesh", "Myanmar", "Pakistan", "Afghanistan",
                                       "Nigeria", "Ghana", "Morocco", "Algeria", "Mexico", "Venezuela", "Egypt"] if n in cidx.index}

# ---------------- places: sunrise, sunset and noon through 2026 ----------------
PL = pd.read_csv(os.path.join(WORK, "places.csv.gz"), keep_default_na=False)
PL = PL[PL.zone >= 0].reset_index(drop=True)
zp = PL.zone.values
PL["e_std"] = wrap(STD_OFF[zp] - 4 * PL.lon.values)
PL["e_ann"] = wrap(ANN[zp] - 4 * PL.lon.values)
PL["e_jun"] = wrap(OFF_OFF[zp, D_JUN21] - 4 * PL.lon.values)
PL["e_dec"] = wrap(OFF_OFF[zp, D_DEC21] - 4 * PL.lon.values)
PL["std_offset"] = STD_OFF[zp]; PL["dst"] = HAS_DST[zp]
PL["tz_boundaries"] = [ids[i] for i in zp]
# agreement with GeoNames' own time zone (compare offsets on every day of 2026, raw IANA rules)
from zoneinfo import ZoneInfo
gcache = {}
def goff(t):
    if t not in gcache:
        try:
            zz = ZoneInfo(t); gcache[t] = np.array([dt.datetime(d.year, d.month, d.day, 12, tzinfo=zz).utcoffset().total_seconds() / 60 for d in DATES])
        except Exception:
            gcache[t] = None
    return gcache[t]
agree = np.array([(goff(t) is not None and np.array_equal(goff(t), OFF[i])) for t, i in zip(PL.timezone, zp)])
R["meta"]["geonames_tz_agree"] = float(agree.mean()); R["meta"]["geonames_tz_disagree_n"] = int((~agree).sum())

PKL = os.path.join(WORK, "places.pkl.gz")
if os.path.exists(PKL) and not os.environ.get("FORCE"):
    out = pd.read_pickle(PKL)
else:
    CH = 20000
    cols = {k: np.zeros(len(PL)) for k in ["rise_late", "rise_late_doy", "rise_early", "rise_early_doy", "set_late", "set_late_doy", "set_early", "set_early_doy",
                                            "noon_late", "noon_early", "rise_dec21", "set_dec21", "rise_jun21", "set_jun21", "noon_jun21", "noon_dec21", "days_rise_after_9", "days_rise_after_830", "days_set_after_22"]}
    for a in range(0, len(PL), CH):
        s = PL.iloc[a:a + CH]
        la, lo, zz = s.lat.values[:, None], s.lon.values[:, None], s.zone.values
        noon, rise, sett = sun_times(la, lo, YEAR, DOY[None, :])
        off = OFF_OFF[zz]
        noon, rise, sett = noon + off, rise + off, sett + off
        with np.errstate(invalid="ignore"):
            for nm, arr, fn in [("rise_late", rise, np.nanargmax), ("rise_early", rise, np.nanargmin), ("set_late", sett, np.nanargmax), ("set_early", sett, np.nanargmin)]:
                ok = ~np.all(np.isnan(arr), 1)
                idx = np.zeros(len(s), int); idx[ok] = fn(arr[ok], 1)
                v = arr[np.arange(len(s)), idx]; v[~ok] = np.nan
                cols[nm][a:a + len(s)] = v; cols[nm + "_doy"][a:a + len(s)] = idx + 1
            cols["noon_late"][a:a + len(s)] = noon.max(1); cols["noon_early"][a:a + len(s)] = noon.min(1)
            cols["rise_dec21"][a:a + len(s)] = rise[:, D_DEC21]; cols["set_dec21"][a:a + len(s)] = sett[:, D_DEC21]
            cols["rise_jun21"][a:a + len(s)] = rise[:, D_JUN21]; cols["set_jun21"][a:a + len(s)] = sett[:, D_JUN21]
            cols["noon_jun21"][a:a + len(s)] = noon[:, D_JUN21]; cols["noon_dec21"][a:a + len(s)] = noon[:, D_DEC21]
            cols["days_rise_after_9"][a:a + len(s)] = (rise > 540).sum(1); cols["days_rise_after_830"][a:a + len(s)] = (rise > 510).sum(1)
            cols["days_set_after_22"][a:a + len(s)] = (sett > 1320).sum(1)
    for k, v in cols.items(): PL[k] = v
    out = PL[["geonameid", "name", "country", "admin1", "lat", "lon", "population", "tz_boundaries", "timezone", "std_offset", "dst", "e_std", "e_ann", "e_jun", "e_dec",
              "rise_late", "rise_late_doy", "rise_early", "rise_early_doy", "set_late", "set_late_doy", "set_early", "set_early_doy", "noon_early", "noon_late",
              "rise_dec21", "set_dec21", "rise_jun21", "set_jun21", "noon_jun21", "noon_dec21", "days_rise_after_9", "days_rise_after_830", "days_set_after_22"]].copy()
    out = out.rename(columns={"timezone": "tz_geonames"})
    out.to_pickle(PKL)
out["name"] = out.name.str.replace("\u2013", "-").str.replace("\u2014", "-").str.replace("--", "-")
R["meta"]["places_used"] = int(len(out))
out.to_pickle(PKL)
pub = out.copy()
for c in ["rise_late", "rise_early", "set_late", "set_early", "noon_early", "noon_late", "rise_dec21", "set_dec21", "rise_jun21", "set_jun21", "noon_jun21", "noon_dec21"]:
    pub[c] = pub[c].round(0).astype("Int64")
pub = pub.round({"e_std": 1, "e_ann": 1, "e_jun": 1, "e_dec": 1})
pub[pub.population >= 10000].to_csv(os.path.join(DATA, "places.csv"), index=False)
pub.to_csv(os.path.join(DATA, "places_1000.csv.gz"), index=False, compression="gzip")
# within-country range from places of 1,000 or more (GeoNames country codes; hexagons straddle borders)
rng = out.groupby("country").agg(e_ann_min=("e_ann", "min"), e_ann_max=("e_ann", "max"), e_std_min=("e_std", "min"), e_std_max=("e_std", "max"),
                                  n_offsets=("std_offset", "nunique"), places=("name", "size"))
C = C.merge(rng, left_on="iso2", right_index=True, how="left")
C.round(2).to_csv(os.path.join(DATA, "countries.csv"), index=False)
cidx = C.set_index("country")
R["country"] = {n: crow(n) for n in R["country"]}

def prow(r, extra=()):
    d = {"name": r["name"], "cc": r["country"], "pop": int(r["population"]), "lat": float(r["lat"]), "lon": float(r["lon"]), "tz": r["tz_boundaries"],
         "std_offset": int(r["std_offset"]), "e_std": round(float(r["e_std"]), 1), "e_ann": round(float(r["e_ann"]), 1),
         "e_jun": round(float(r["e_jun"]), 1), "e_dec": round(float(r["e_dec"]), 1),
         "rise_late": hm(r["rise_late"]), "rise_late_date": ds(int(r["rise_late_doy"]) - 1), "rise_early": hm(r["rise_early"]), "rise_early_date": ds(int(r["rise_early_doy"]) - 1),
         "set_late": hm(r["set_late"]), "set_late_date": ds(int(r["set_late_doy"]) - 1), "set_early": hm(r["set_early"]),
         "rise_dec21": hm(r["rise_dec21"]), "set_dec21": hm(r["set_dec21"]), "rise_jun21": hm(r["rise_jun21"]), "set_jun21": hm(r["set_jun21"]),
         "noon_jun21": hm(r["noon_jun21"]), "noon_dec21": hm(r["noon_dec21"]), "noon_late": hm(r["noon_late"]), "noon_early": hm(r["noon_early"]),
         "days_rise_after_9": int(r["days_rise_after_9"]), "days_rise_after_830": int(r["days_rise_after_830"]), "days_set_after_22": int(r["days_set_after_22"]),
         "rise_late_min": round(float(r["rise_late"]), 1), "set_jun21_min": round(float(r["set_jun21"]), 1), "rise_dec21_min": round(float(r["rise_dec21"]), 1), "rise_jun21_min": round(float(r["rise_jun21"]), 1)}
    return d

def place(name, cc, admin1=None):
    q = out[(out.name == name) & (out.country == cc)]
    if admin1: q = q[q.admin1 == admin1]
    return q.sort_values("population").iloc[-1]

# most "wrong" inhabited places
def extremes(df, k, n=10, asc=False):
    return [prow(r) for _, r in df.sort_values(k, ascending=asc).head(n).iterrows()]
big = out[out.population >= 100000]
R["extremes"] = {"ahead_any": extremes(out, "e_ann"), "behind_any": extremes(out, "e_ann", asc=True),
                 "ahead_100k": extremes(big, "e_ann"), "behind_100k": extremes(big, "e_ann", asc=True),
                 "ahead_std_100k": extremes(big, "e_std"), "n_100k": int(len(big)),
                 "latest_rise_100k_55": extremes(big[big.lat.abs() <= 55], "rise_late", 10), "latest_set_100k_55": extremes(big[big.lat.abs() <= 55], "set_late", 10)}
# shares of big cities
R["cities_100k"] = {"ahead": float((big.e_ann > 0).mean()), "ahead_60": float((big.e_ann > 60).mean()), "behind_30": float((big.e_ann < -30).mean())}

# ---------------- stories ----------------
S = {}
gal_names = [("A Coruña", "ES"), ("Santiago de Compostela", "ES"), ("Vigo", "ES"), ("London", "GB"), ("Madrid", "ES"), ("Barcelona", "ES"), ("Porto", "PT"), ("Lisbon", "PT"), ("Ourense", "ES"), ("Lugo", "ES")]
S["galicia_places"] = {n: prow(place(n, c)) for n, c in gal_names}
gal = out[(out.country == "ES") & (out.admin1 == "58")]
gw = gal.population.values
S["galicia_region"] = {"places": int(len(gal)), "people_in_places": int(gw.sum()), "e_ann": float((gal.e_ann * gw).sum() / gw.sum()),
                       "e_std": float((gal.e_std * gw).sum() / gw.sum()), "westmost": prow(gal.sort_values("lon").iloc[0]),
                       "rise_late_mean": float((gal.rise_late * gw).sum() / gw.sum())}
# Spanish places of 100k+, ranked by latest sunrise
es = big[big.country == "ES"].sort_values("rise_late", ascending=False)
S["spain_latest_rise_100k"] = [prow(r) for _, r in es.head(6).iterrows()]
S["spain_n_100k"] = int(len(es))
eu = big[big.country.isin(["ES", "PT", "FR", "GB", "IE", "DE", "IT", "NL", "BE", "PL", "AT", "CH", "DK", "SE", "NO", "FI", "CZ", "SK", "HU", "SI", "HR", "RO", "BG", "GR", "LU", "EE", "LV", "LT"])]
S["europe_latest_rise_rank"] = {n: int((eu.rise_late > place(n, c).rise_late).sum()) + 1 for n, c in [("A Coruña", "ES"), ("Vigo", "ES"), ("Santiago de Compostela", "ES")] if place(n, c).population >= 100000}
S["europe_n_100k"] = int(len(eu))
S["europe_most_ahead_100k"] = [prow(r) for _, r in eu.sort_values("e_ann", ascending=False).head(5).iterrows()]
eu55 = eu[eu.lat < 55].sort_values("rise_late", ascending=False)
S["europe_s55_latest_rise"] = [prow(r) for _, r in eu55.head(6).iterrows()]
S["europe_s55_n"] = int(len(eu55))
S["europe_latest_noon_jun21"] = [prow(r) for _, r in eu.sort_values("noon_jun21", ascending=False).head(5).iterrows()]
S["europe_coruna_rank_all"] = int((eu.rise_late > place("A Coruña", "ES").rise_late).sum()) + 1
S["europe_above_coruna_countries"] = sorted(set(eu[eu.rise_late > place("A Coruña", "ES").rise_late].country))
S["europe_latest_rise_100k"] = [prow(r) for _, r in eu.sort_values("rise_late", ascending=False).head(8).iterrows()]
# daily series for the Galicia chart (clock minutes)
ser = {}
for n, c in gal_names[:8]:
    r = place(n, c); noon, rise, sett = sun_times(r.lat, r.lon, YEAR, DOY)
    off = OFF_OFF[IX[r.tz_boundaries]]
    ser[n] = {"rise": np.round(rise + off, 1).tolist(), "set": np.round(sett + off, 1).tolist(), "noon": np.round(noon + off, 1).tolist()}
save_json(ser, os.path.join(WORK, "galicia_series.json"))
# Tui (ES) and Valença (PT) face each other across the Minho
for n, c in [("Tui", "ES"), ("Valença", "PT")]:
    try: S.setdefault("minho", {})[n] = prow(place(n, c))
    except IndexError: pass

# UK east to west
gb = out[(out.country == "GB") & (out.population >= 5000)]
gb = gb[gb.tz_boundaries == "Europe/London"]
S["uk"] = {"east": prow(gb.sort_values("lon").iloc[-1]), "west_ni": prow(gb[gb.admin1 == "NIR"].sort_values("lon").iloc[0]),
           "london": prow(place("London", "GB")), "belfast": prow(place("Belfast", "GB")), "cardiff": prow(place("Cardiff", "GB")),
           "edinburgh": prow(place("Edinburgh", "GB")), "glasgow": prow(place("Glasgow", "GB")), "lowestoft": prow(place("Lowestoft", "GB")),
           "penzance": prow(place("Penzance", "GB")), "stornoway": prow(place("Stornoway", "GB")), "lerwick": prow(place("Lerwick", "GB"))}
S["uk"]["east_west_min"] = round(S["uk"]["west_ni"]["e_std"] - S["uk"]["east"]["e_std"], 1)
# China
cn = out[out.country == "CN"]
S["china"] = {"kashgar": prow(place("Kashgar", "CN")), "urumqi": prow(place("Ürümqi", "CN")), "beijing": prow(place("Beijing", "CN")),
              "shanghai": prow(place("Shanghai", "CN")), "lhasa": prow(place("Lhasa", "CN")), "harbin": prow(place("Harbin", "CN")),
              "east_west_deg": float(cn.lon.max() - cn.lon.min()), "west_place": prow(cn.sort_values("lon").iloc[0]), "east_place": prow(cn.sort_values("lon").iloc[-1])}
k = S["china"]["kashgar"]; S["china"]["kashgar_xinjiang_time_e_std"] = round(float(STD[IX["Asia/Urumqi"]] - 4 * k["lon"]), 1)
S["china"]["urumqi_xinjiang_time_e_std"] = round(float(STD[IX["Asia/Urumqi"]] - 4 * S["china"]["urumqi"]["lon"]), 1)
# India single zone
ind = big[big.country == "IN"]
S["india"] = {"east": prow(ind.sort_values("lon").iloc[-1]), "west": prow(ind.sort_values("lon").iloc[0]),
              "kolkata": prow(place("Kolkata", "IN")), "mumbai": prow(place("Mumbai", "IN")), "delhi": prow(place("New Delhi", "IN"))}
S["india"]["east_west_min"] = round(S["india"]["west"]["e_std"] - S["india"]["east"]["e_std"], 1)
S["india"]["sunrise_gap_min"] = round(S["india"]["west"]["rise_jun21_min"] - float(ind.sort_values("lon").iloc[-1].rise_jun21), 1)
# Argentina
ar = big[big.country == "AR"]
S["argentina"] = {"buenos_aires": prow(place("Buenos Aires", "AR")), "mendoza": prow(place("Mendoza", "AR")), "cordoba": prow(place("Córdoba", "AR")),
                  "ushuaia": prow(place("Ushuaia", "AR")), "west_100k": prow(ar.sort_values("lon").iloc[0]),
                  "santiago_cl": prow(place("Santiago", "CL"))}
# Russia
ru = out[out.country == "RU"]
S["russia"] = {"zones_std_offsets": sorted({int(x) for x in ru.std_offset}), "moscow": prow(place("Moscow", "RU")),
               "ahead_100k": [prow(r) for _, r in big[big.country == "RU"].sort_values("e_ann", ascending=False).head(3).iterrows()]}
# Others for the text
for key, (n, c) in {"paris": ("Paris", "FR"), "brest": ("Brest", "FR"), "reykjavik": ("Reykjavík", "IS"), "dublin": ("Dublin", "IE"),
                    "galway": ("Galway", "IE"), "warsaw": ("Warsaw", "PL"), "berlin": ("Berlin", "DE"), "amsterdam": ("Amsterdam", "NL"),
                    "seville": ("Sevilla", "ES"), "valencia": ("Valencia", "ES"), "bilbao": ("Bilbao", "ES"), "las_palmas": ("Las Palmas de Gran Canaria", "ES"),
                    "ulaanbaatar": ("Ulan Bator", "MN"), "kabul": ("Kabul", "AF"), "kathmandu": ("Kathmandu", "NP"), "dhaka": ("Dhaka", "BD"),
                    "new_york": ("New York City", "US"), "detroit": ("Detroit", "US"), "el_paso": ("El Paso", "US"), "lagos": ("Lagos", "NG")}.items():
    try: S[key] = prow(place(n, c))
    except IndexError: print("missing", n)
R["stories"] = S

# ---------------- biggest clock jumps across a land border ----------------
G = np.load(os.path.join(WORK, "grid_idx.npz"))["g"].astype(np.int32)
stdg = np.where(G > 0, STD_OFF[np.maximum(G - 1, 0)], np.nan)
jumps = {}
for a, b in [(stdg[:, :-1], stdg[:, 1:]), (stdg[:-1, :], stdg[1:, :])]:
    d = np.abs(a - b); d = np.minimum(d, 1440 - d)
    ga = G[:, :-1] if a.shape[1] != G.shape[1] else G[:-1, :]
    gb_ = G[:, 1:] if a.shape[1] != G.shape[1] else G[1:, :]
    m = d >= 120
    for x, y, dd in zip(ga[m], gb_[m], d[m]):
        key = tuple(sorted((ids[x - 1], ids[y - 1])))
        jumps[key] = max(jumps.get(key, 0), float(dd))
J = sorted(jumps.items(), key=lambda kv: -kv[1])
R["jumps"] = [{"a": a, "b": b, "minutes": m} for (a, b), m in J[:12]]

# ---------------- zone table ----------------
zt = pd.DataFrame({"tzid": ids, "std_offset_min": STD.astype(int), "official_std_offset_min": STD_OFF.astype(int),
                   "offset_jun21": OFF[:, D_JUN21].astype(int), "offset_dec21": OFF[:, D_DEC21].astype(int), "changes_in_2026": OFF.max(1) != OFF.min(1)})
zt.to_csv(os.path.join(DATA, "zones.csv"), index=False)

save_json(R, os.path.join(DATA, "results.json"), indent=1)
print(json.dumps(R["population"], indent=1)[:2500])
print(json.dumps(R["countries"], indent=1)[:3000])
