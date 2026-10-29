"""Step 8: blog post (release/blog/post.html, meta.json), Zenodo folder (release/zenodo/) and README.md."""
import json, os, re, shutil, sys, zipfile
sys.path.insert(0, os.path.dirname(__file__))
from common import *
import importlib.util
spec = importlib.util.spec_from_file_location("bs", os.path.join(HERE, "04_build_site.py")); bs = importlib.util.module_from_spec(spec); spec.loader.exec_module(bs)
R = bs.R
BL = os.path.join(ROOT, "release", "blog"); ZD = os.path.join(ROOT, "release", "zenodo"); os.makedirs(ZD, exist_ok=True)
post = bs.fill(open(os.path.join(HERE, "blog_template.html")).read())
for m in re.findall(r"\{\{IMG\|([^|]+)\|", post): assert os.path.exists(os.path.join(BL, m)), m
open(os.path.join(BL, "post.html"), "w").write(post)
txt = re.sub(r"<[^>]+>", " ", re.sub(r"<!--.*?-->", "", post, flags=re.S)); print("blog words", len(txt.split()))
pct = lambda x: f"{round(x * 100)}%"
meta = {"title": "How wrong is your clock?", "slug": SLUG,
        "excerpt": f"For {pct(R['population']['e_ann']['ahead'])} of the world's people the clock runs ahead of the sun. I measured the gap everywhere, and found out why winter mornings in Galicia stay dark until after nine.",
        "seo_description": "How far clocks run from the sun worldwide in 2026, with sunrise times for any place, and why Galicia's winter sun rises after nine.",
        "tags": ["time zones", "daylight saving", "sunrise", "Spain", "Galicia", "maps", "data visualisation", "China"],
        "header_alt": "World map coloured by how far the clock runs ahead of the sun, mostly orange, beside the title How wrong is your clock?"}
assert len(meta["seo_description"]) < 160
json.dump(meta, open(os.path.join(BL, "meta.json"), "w"), ensure_ascii=False, indent=1)

open(os.path.join(ROOT, "README.md"), "w").write(bs.fill(open(os.path.join(HERE, "readme_template.md")).read()))
# ---- Zenodo ----
PDF = "Hotham_Clock_vs_Sun.pdf"
shutil.copy(os.path.join(ROOT, "release", PDF), os.path.join(ZD, PDF))
for f in ["places.csv", "places_1000.csv.gz", "countries.csv", "zones.csv", "population_by_offset.csv", "results.json"]:
    shutil.copy(os.path.join(DATA, f), os.path.join(ZD, f))
tex = open(os.path.join(ROOT, "release", "paper", "Hotham_Clock_vs_Sun.tex")).read()
ab = tex.split("\\begin{center}\\textbf{Abstract}\\end{center}")[1].split("\\textbf{Keywords:}")[0].strip()
ab = ab.replace("\\%", "%").replace("\\texttt{", "").replace("}", "").replace("$-$", "-").replace("$+$", "+")
assert "\\" not in ab and "{" not in ab, ab[:200]
zm = {"title": "How Wrong Is Your Clock? Clock Time Against Solar Time for the World's People in 2026",
      "description_html": f"<p>{ab}</p><p>Interactive version: {PAGE}. Data and code: {REPO}. Blog post: to follow.</p>",
      "keywords": ["time zones", "solar time", "daylight saving time", "sunrise", "longitude", "Spain", "Galicia", "China", "India", "population geography"],
      "licence": "cc-by-4.0",
      "related": [{"identifier": REPO, "relation": "issupplementedby", "resource_type": "software"},
                  {"identifier": PAGE, "relation": "issupplementedby", "resource_type": "other"},
                  {"identifier": "https://github.com/evansiroky/timezone-boundary-builder", "relation": "isderivedfrom", "resource_type": "dataset"},
                  {"identifier": "https://www.iana.org/time-zones", "relation": "isderivedfrom", "resource_type": "dataset"},
                  {"identifier": "https://data.humdata.org/dataset/kontur-population-dataset-22km", "relation": "isderivedfrom", "resource_type": "dataset"},
                  {"identifier": "https://download.geonames.org/export/dump/", "relation": "isderivedfrom", "resource_type": "dataset"},
                  {"identifier": "https://www.naturalearthdata.com/", "relation": "isderivedfrom", "resource_type": "dataset"}]}
json.dump(zm, open(os.path.join(ZD, "meta.json"), "w"), ensure_ascii=False, indent=1)
zp = os.path.join(ZD, f"{SLUG}_code_and_data.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ["code", "data"]:
        for f in sorted(os.listdir(os.path.join(ROOT, d))):
            p = os.path.join(ROOT, d, f)
            if os.path.isfile(p) and not f.endswith(".pyc") and f != "places_1000.csv.gz": z.write(p, f"{d}/{f}")
    for f in ["README.md", "LICENSE"]: z.write(os.path.join(ROOT, f), f)
for f in sorted(os.listdir(ZD)): print(f, os.path.getsize(os.path.join(ZD, f)) // 1024, "KB")
