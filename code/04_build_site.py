"""Step 4: derived numbers for the text (saved into data/results.json under "v"), checks of facts stated in words,
and index.html from code/page_template.html ({{path|format}} tokens filled from results.json)."""
import json, os, re, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import *

R = load_json(os.path.join(DATA, "results.json"))
S = R["stories"]; C = pd.read_csv(os.path.join(DATA, "countries.csv"))
CB = C[C.population >= 1_000_000].sort_values("e_ann", ascending=False)
named = ["United Kingdom", "United States of America", "China", "India", "Russia", "Japan", "Brazil", "Indonesia"]
chart = pd.concat([CB.head(15), CB[CB.country.isin(named)], CB.tail(5)]).drop_duplicates("country").sort_values("e_ann", ascending=False)
R["country_chart"] = [{"country": r.country, "e_ann": round(r.e_ann, 1), "e_std": round(r.e_std, 1), "e_jun": round(r.e_jun, 1), "e_dec": round(r.e_dec, 1), "pop": int(r.population)} for r in chart.itertuples()]
rank = {c: i + 1 for i, c in enumerate(CB.country)}
g = S["galicia_places"]; uk = S["uk"]
V = {
    "spain_rank": rank["Spain"], "uk_rank": rank["United Kingdom"], "china_rank": rank["China"], "india_rank": rank["India"],
    "coruna_vs_london_rise": round(g["A Coruña"]["rise_late_min"] - g["London"]["rise_late_min"]),
    "coruna_vs_madrid_rise": round(g["A Coruña"]["rise_late_min"] - g["Madrid"]["rise_late_min"]),
    "coruna_vs_barcelona_rise": round(g["A Coruña"]["rise_late_min"] - g["Barcelona"]["rise_late_min"]),
    "vigo_vs_porto_e": round(g["Vigo"]["e_std"] - g["Porto"]["e_std"]),
    "gal_lat_minus_london": round(g["London"]["lat"] - g["A Coruña"]["lat"], 1),
    "stornoway_vs_london_dec": round(float(uk["stornoway"]["rise_dec21_min"]) - float(uk["london"]["rise_dec21_min"])),
    "world_people_bn": round(R["population"]["people"] / 1e9, 2),
    "ahead_60_people_m": round(R["population"]["e_ann"]["ahead_60"] * R["population"]["people"] / 1e6),
    "ahead_30_people_bn": round(R["population"]["e_ann"]["ahead_30"] * R["population"]["people"] / 1e9, 1),
    "xinjiang_people_m": round(R["population"]["xinjiang_people"] / 1e6),
    "kashgar_jun_set": S["china"]["kashgar"]["set_jun21"],
    "afg_chn_jump": next(j["minutes"] for j in R["jumps"] if {j["a"], j["b"]} == {"Asia/Kabul", "Asia/Urumqi"}),
}
R["v"] = V
save_json(R, os.path.join(DATA, "results.json"), indent=1)

# ---- checks of facts stated in words ----
assert CB.iloc[0].country == "Spain", CB.head(3)
assert S["europe_s55_latest_rise"][0]["name"] == "Brest" and S["europe_s55_latest_rise"][1]["name"] == "A Coruña"
assert S["europe_latest_noon_jun21"][0]["name"] == "Vigo"
assert set(S["europe_above_coruna_countries"]) == {"EE", "FI", "FR", "NO", "SE"}
assert R["extremes"]["ahead_100k"][0]["name"] == "Kashgar" and R["extremes"]["behind_100k"][0]["name"] == "Tinsukia"
assert R["extremes"]["behind_any"][0]["cc"] == "RU" and R["extremes"]["behind_any"][2]["name"] == "Vorkuta"
assert R["jumps"][0]["a"] == "Asia/Kabul" and R["jumps"][0]["b"] == "Asia/Urumqi"
assert uk["east"]["name"] == "Lowestoft" and uk["west_ni"]["name"] == "Enniskillen"
assert g["A Coruña"]["days_rise_after_9"] > 0 and g["London"]["days_rise_after_9"] == 0 and g["Madrid"]["days_rise_after_9"] == 0
assert S["russia"]["ahead_100k"][2]["name"] == "Novosibirsk"
assert S["europe_most_ahead_100k"][0]["name"] == "Vigo" and S["europe_most_ahead_100k"][1]["name"] == "A Coruña"
assert abs(R["extremes"]["behind_any"][2]["lon"] - 64) < 0.5
assert all(r["cc"] in ("IN", "CN") for r in R["extremes"]["behind_100k"]) and all(r["cc"] == "CN" and r["tz"] == "Asia/Urumqi" for r in R["extremes"]["ahead_100k"])
assert S["india"]["east"]["name"] == "Tinsukia" and S["india"]["west"]["name"] == "Porbandar"
print("checks ok")

# ---- fill template ----
def get(path):
    v = R; parts = path.split("."); i = 0
    while i < len(parts):
        for j in range(len(parts), i, -1):
            k = ".".join(parts[i:j])
            if isinstance(v, list) and k.isdigit(): v = v[int(k)]; i = j; break
            if isinstance(v, dict) and k in v: v = v[k]; i = j; break
        else: raise KeyError(path)
    return v

def dur(m, words=False):
    m = int(round(abs(float(m))))
    h, mm = divmod(m, 60)
    if h == 0: return f"{mm} min"
    if mm == 0: return f"{h} h"
    return f"{h} h {mm} min"

def fmt(v, f):
    if f in (None, "raw"): return str(v)
    if f == "int": return f"{round(v):,}"
    if f == "pct": return f"{round(v * 100)}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "f1": return f"{v:.1f}"
    if f == "dur": return dur(v)
    if f == "len": return str(len(v))
    if f == "m": return f"{round(v / 1e6):,} million"
    if f == "bn": return f"{v / 1e9:.1f} billion"
    raise ValueError(f)

def fill(t):
    return re.sub(r"\{\{([^}|]+)(?:\|([a-z0-9]+))?\}\}", lambda m: fmt(get(m.group(1).strip()), m.group(2)), t)

if __name__ == "__main__":
    tpl = open(os.path.join(HERE, "page_template.html")).read()
    html = fill(tpl)
    small = {k: R[k] for k in ["hist", "country_chart", "extremes", "population", "meta"]}
    html = html.replace("/*RESULTS*/", json.dumps(small, ensure_ascii=False, separators=(",", ":")))
    open(os.path.join(ROOT, "index.html"), "w").write(html)
    print("index.html", len(html) // 1024, "KB")
