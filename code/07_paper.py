"""Step 7: the paper PDF. Fills code/paper_template.tex from data/results.json, writes release/paper/Hotham_Clock_vs_Sun.tex
and compiles it with xelatex (figures from step 5 are in release/paper/). Copies the PDF to release/."""
import json, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import *
import importlib.util
spec = importlib.util.spec_from_file_location("bs", os.path.join(HERE, "04_build_site.py")); bs = importlib.util.module_from_spec(spec); spec.loader.exec_module(bs)
R = bs.R; get = bs.get
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Clock_vs_Sun"
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")
def fmt(v, f):
    if f == "pct": return f"{round(v * 100)}\\%"
    if f == "pct1": return f"{v * 100:.1f}\\%"
    if f in ("int", "f1", "dur", "len"): return bs.fmt(v, f)
    return tex(v)
assert R["stories"]["europe_coruna_rank_all"] == 21
S = R["stories"]; sg = lambda m: ("$+$" if m >= 0 else "$-$") + f"{abs(m):.0f}"
# countries table
import pandas as pd
C = pd.read_csv(os.path.join(DATA, "countries.csv")); CB = C[C.population >= 1_000_000].sort_values("e_ann", ascending=False)
nm = lambda n: tex(n.replace("United States of America", "United States"))
row = lambda r: f"{nm(r.country)} & {r.population / 1e6:,.1f} & {sg(r.e_ann)} & {sg(r.e_std)} & {sg(r.e_jun)} & {sg(r.e_dec)}\\\\\n"
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{Countries of a million people or more furthest ahead of and behind the sun: "
      "population-weighted gap between clock and mean solar time, minutes, " + str(YEAR) + ".}\\label{tab:countries}"
      "\\begin{tabular}{lrrrrr}\\toprule Country & People (m) & Year average & No DST & 21 June & 21 Dec\\\\\\midrule\n"
      + "".join(row(r) for r in CB.head(10).itertuples()) + "\\midrule\n" + "".join(row(r) for r in CB.tail(5).iloc[::-1].itertuples())
      + "\\bottomrule\\end{tabular}\\end{table}")
gp = S["galicia_places"]
grow = lambda n: f"{tex(n)} & {gp[n]['rise_late']} ({gp[n]['rise_late_date'].replace(' January', ' Jan').replace(' December', ' Dec')}) & {gp[n]['rise_dec21']} & {gp[n]['noon_jun21']} & {gp[n]['set_jun21']} & {gp[n]['days_rise_after_9']} & {sg(gp[n]['e_ann'])}\\\\\n"
TG = ("\\begin{table}[tbp]\\centering\\small\\caption{Galicia against London, Madrid, Barcelona, Porto and Lisbon, " + str(YEAR) + ": latest sunrise of the year (date), "
      "sunrise on 21 December, solar noon and sunset on 21 June, days with sunrise after 9:00, and the year-average gap between clock and sun in minutes.}\\label{tab:galicia}"
      "\\begin{tabular}{lrrrrrr}\\toprule Place & Latest sunrise & Rise 21 Dec & Noon 21 Jun & Set 21 Jun & After 9:00 & Gap\\\\\\midrule\n"
      + "".join(grow(n) for n in ["A Coruña", "Santiago de Compostela", "Vigo", "Ourense", "Lugo"]) + "\\midrule\n"
      + "".join(grow(n) for n in ["Madrid", "Barcelona", "London", "Porto", "Lisbon"]) + "\\bottomrule\\end{tabular}\\end{table}")
ex = R["extremes"]
erow = lambda a, b: f"{tex(a['name'])}, {a['cc']} & {sg(a['e_ann'])} & {a['rise_late']} & {tex(b['name'])}, {b['cc']} & {sg(b['e_ann'])} & {b['rise_late']}\\\\\n"
TE = ("\\begin{table}[tbp]\\centering\\small\\caption{Cities of 100,000 or more with the largest year-average gaps ahead of and behind the sun (minutes), with each city's latest sunrise of " + str(YEAR) + ".}\\label{tab:extremes}"
      "\\begin{tabular}{lrrlrr}\\toprule \\multicolumn{3}{l}{Furthest ahead} & \\multicolumn{3}{l}{Furthest behind}\\\\ City & Gap & Latest rise & City & Gap & Latest rise\\\\\\midrule\n"
      + "".join(erow(a, b) for a, b in zip(ex["ahead_100k"], ex["behind_100k"])) + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(HERE, "paper_template.tex")).read()
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(?:\|([a-z0-9]+))?\}\}", lambda m: fmt(get(m.group(1).strip()), m.group(2) or "raw"), t)
t = t.replace("{{TABLE_COUNTRIES}}", TC).replace("{{TABLE_GALICIA}}", TG).replace("{{TABLE_EXTREMES}}", TE)
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
if r.returncode: print(r.stdout[-3000:]); raise SystemExit("xelatex failed")
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.move(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
print("paper ok")
