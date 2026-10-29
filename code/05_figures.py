"""Step 5: static figures for the paper (release/paper/fig_*.png) and the blog (release/blog/b_*.png).
Run: FONT_DIR=/path/to/fonts python3 code/05_figures.py (Fraunces, IBM Plex Mono, Source Serif 4; falls back to defaults)."""
import json, os, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import ListedColormap, BoundaryNorm
sys.path.insert(0, os.path.dirname(__file__))
from common import *

FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
if os.path.isdir(FD):
    for f in os.listdir(FD):
        if f.endswith(".ttf"): fm.fontManager.addfont(os.path.join(FD, f))
    plt.rcParams["font.family"] = "IBM Plex Mono"
FG, MUT, RULE, BG, SEA = "#1E1B18", "#6A635A", "#E2D9C9", "#FFFFFF", "#EEF1F2"
BREAKS = [-60, -30, 0, 30, 60, 90, 120, 150]
COLS = ["#24527F", "#5D8EBD", "#B7D2E6", "#FBE6A9", "#F5C064", "#EC9038", "#D8602A", "#B0362A", "#6E1F3C"]
LABS = ["more than\n1 h behind", "30 to 60\nbehind", "0 to 30\nbehind", "0 to 30\nahead", "30 to 60\nahead", "1 h to\n1 h 30", "1 h 30\nto 2 h", "2 h to\n2 h 30", "more than\n2 h 30"]
RGB = np.array([[int(c[i:i + 2], 16) for i in (1, 3, 5)] for c in COLS], np.uint8)
PAP = os.path.join(ROOT, "release", "paper"); BLG = os.path.join(ROOT, "release", "blog")
os.makedirs(PAP, exist_ok=True); os.makedirs(BLG, exist_ok=True)
plt.rcParams.update({"axes.edgecolor": MUT, "axes.labelcolor": FG, "xtick.color": MUT, "ytick.color": MUT, "text.color": FG,
                     "axes.spines.top": False, "axes.spines.right": False, "savefig.facecolor": BG, "figure.facecolor": BG})

R = load_json(os.path.join(DATA, "results.json"))
Z = load_json(os.path.join(WORK, "zones.json"))
ids = Z["ids"]; IX = {t: i for i, t in enumerate(ids)}
OFF = np.array(Z["days"], float); STD = np.array(Z["std"], float)
OFF[IX["Asia/Urumqi"]] = OFF[IX["Asia/Shanghai"]]; STD[IX["Asia/Urumqi"]] = STD[IX["Asia/Shanghai"]]
ANN = OFF.mean(1)
G = np.load(os.path.join(WORK, "grid_idx.npz"))["g"].astype(np.int32)
NY, NX = G.shape; LON = -180 + (np.arange(NX) + .5) * .1
BORD = load_json(os.path.join(DATA, "borders.json"))

def gap_grid(val):
    v = np.where(G > 0, val[np.maximum(G - 1, 0)], np.nan)
    e = v - 4 * LON[None, :]
    return (e + 720) % 1440 - 720

def rgb_grid(e):
    k = np.digitize(np.nan_to_num(e, nan=0), BREAKS)
    img = RGB[k].astype(float) / 255
    a = np.where(np.isnan(e), 0, 1.0)
    return np.dstack([img, a])

def borders(ax, lw=.35, col="#5B564F", box=None):
    for f in BORD["features"]:
        g = f["geometry"]; polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for p in polys:
            for ring in p:
                a = np.array(ring)
                if box and (a[:, 0].max() < box[0] or a[:, 0].min() > box[1] or a[:, 1].max() < box[2] or a[:, 1].min() > box[3]): continue
                ax.plot(a[:, 0], a[:, 1], color=col, lw=lw, solid_joinstyle="round")

def legend_strip(fig, rect, fs=8):
    ax = fig.add_axes(rect)
    for i, c in enumerate(COLS):
        ax.add_patch(plt.Rectangle((i, 0), 1, 1, color=c, ec="white", lw=.8))
        ax.text(i + .5, -.25, LABS[i], ha="center", va="top", fontsize=fs, color=FG, linespacing=1.1)
    ax.set_xlim(0, len(COLS)); ax.set_ylim(-1.6, 1); ax.axis("off")
    ax.text(0, 1.25, "clock behind the sun: sun early", fontsize=fs, color=MUT, ha="left")
    ax.text(len(COLS), 1.25, "clock ahead of the sun: sun late", fontsize=fs, color=MUT, ha="right")

def save(fig, name, blog=True, paper=True):
    if blog: fig.savefig(os.path.join(BLG, "b_" + name + ".png"), dpi=200)
    if paper: fig.savefig(os.path.join(PAP, "fig_" + name + ".png"), dpi=200)
    plt.close(fig)

# ---------- 1. world map, year average ----------
def world(mode="ann"):
    e = gap_grid(ANN if mode == "ann" else STD)
    fig = plt.figure(figsize=(7.6, 4.75))
    ax = fig.add_axes([0.01, 0.2, 0.98, 0.79])
    ax.add_patch(plt.Rectangle((-180, -60), 360, 145, color=SEA, zorder=0))
    ax.imshow(rgb_grid(e), extent=[-180, 180, -60, 85], interpolation="nearest", zorder=1)
    borders(ax, lw=.25)
    ax.set_xlim(-180, 180); ax.set_ylim(-58, 84); ax.set_aspect(1.15); ax.axis("off")
    for nm, lon, lat, dx, dy in [("Kashgar", 75.99, 39.47, -14, 9), ("A Coruña", -8.4, 43.37, -30, 7), ("Buenos Aires", -58.4, -34.6, 6, -9), ("Tinsukia", 95.36, 27.49, 6, -10), ("Vorkuta", 64.0, 67.5, -8, 8)]:
        ax.plot(lon, lat, "o", ms=3, mfc=FG, mec="white", mew=.6, zorder=5)
        ax.annotate(nm, (lon, lat), xytext=(lon + dx, lat + dy), fontsize=7.5, color=FG, zorder=6,
                    arrowprops=dict(arrowstyle="-", color=FG, lw=.5), bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=.8))
    legend_strip(fig, [0.05, 0.03, 0.9, 0.09], fs=6.6)
    return fig
save(world("ann"), "world")

# ---------- 2. population histogram ----------
h = R["hist"]; b = np.array(h["bins"])
fig, ax = plt.subplots(figsize=(7.6, 3.9))
mid = (b[:-1] + b[1:]) / 2
cols = [COLS[np.digitize(m, BREAKS)] for m in mid]
ax.bar(mid, np.array(h["e_ann"]) * 100, width=14, color=cols, edgecolor="#00000030", lw=.4, label="Year average")
ax.step(np.r_[b[:-1], b[-1]], np.r_[np.array(h["e_std"]) * 100, h["e_std"][-1] * 100], where="post", color=FG, lw=1.2, label="No daylight saving")
ax.axvline(0, color=FG, lw=1)
ax.set_xlim(-150, 240); ax.set_xticks(range(-120, 241, 60)); ax.set_xticklabels(["2 h behind", "1 h", "0", "1 h", "2 h", "3 h", "4 h ahead"], fontsize=9)
ax.set_ylabel("share of the world's people (%)", fontsize=9); ax.tick_params(labelsize=9)
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
ax.legend([Patch(fc=COLS[4], ec="#00000030"), Line2D([0], [0], color=FG, lw=1.2)], ["Year average (bars, coloured by band)", "No daylight saving (outline)"], frameon=False, fontsize=9, loc="upper right")
ax.grid(axis="y", color=RULE, lw=.6); ax.set_axisbelow(True)
fig.tight_layout(); save(fig, "hist")

# ---------- 3. countries ----------
cc = R["country_chart"]
fig, ax = plt.subplots(figsize=(7.6, 7.2))
y = np.arange(len(cc))[::-1]
for yy, r in zip(y, cc):
    ax.barh(yy, r["e_ann"], color=COLS[np.digitize(r["e_ann"], BREAKS)], height=.72, edgecolor="#00000030", lw=.4)
    ax.plot([r["e_std"]] * 2, [yy - .4, yy + .4], color=FG, lw=1.6)
    ax.text(max(0, r["e_ann"]) + 2, yy, f'{r["e_ann"]:+.0f} min', va="center", fontsize=8, color=MUT)
ax.set_yticks(y); ax.set_yticklabels([r["country"].replace("United States of America", "United States").replace("Central African Rep.", "Central African Rep") for r in cc], fontsize=8.5)
ax.axvline(0, color=FG, lw=1); ax.set_xlim(-45, 125)
ax.set_xlabel("clock minus sun, minutes (bar: year average; mark: no daylight saving)", fontsize=8.5)
ax.grid(axis="x", color=RULE, lw=.6); ax.set_axisbelow(True); ax.tick_params(axis="x", labelsize=8.5)
fig.tight_layout(); save(fig, "countries")

# ---------- 4. Galicia sunrise ----------
ser = load_json(os.path.join(WORK, "galicia_series.json"))
GALS = [("A Coruña", "#8E2A3B", 2.4, "-"), ("Santiago de Compostela", "#D9661F", 1.8, "-"), ("Vigo", "#E3A33B", 1.8, "-"),
        ("Madrid", "#5B564F", 1.1, "--"), ("Barcelona", "#8C8379", 1.1, ":"), ("London", "#2F5F8F", 1.4, "-"), ("Porto", "#2E8B7A", 1.1, "-.")]
for key, nm in [("rise", "galicia"), ("set", "galicia_set")]:
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    d = np.arange(1, 366)
    for n, c, w, ls in GALS[::-1]:
        v = np.array(ser[n][key]) / 60
        ax.plot(d, v, color=c, lw=w, ls=ls, label=n.replace("Santiago de Compostela", "Santiago"))
    if key == "rise": ax.axhline(9, color="#8E2A3B", lw=.8, ls=(0, (4, 3))); ax.invert_yaxis()
    ax.set_xlim(1, 365)
    mt = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30]) + 15
    ax.set_xticks(mt); ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], fontsize=8.5)
    yt = ax.get_yticks(); ax.set_yticks(yt); ax.set_yticklabels([f"{int(t)}:{int(round((t % 1) * 60)):02d}" for t in yt], fontsize=8.5)
    ax.set_ylim(*((10.25, 3.75) if key == "rise" else (15.5, 22.75)))
    ax.set_ylabel("sunrise by the clock" if key == "rise" else "sunset by the clock", fontsize=9)
    ax.grid(color=RULE, lw=.6); ax.set_axisbelow(True)
    h_, l_ = ax.get_legend_handles_labels(); ax.legend(h_[::-1], l_[::-1], frameon=False, fontsize=8, ncol=4, loc="upper center", bbox_to_anchor=(.5, -.1))
    fig.tight_layout(); save(fig, nm, paper=(key == "rise"), blog=True)

# ---------- 5. Iberia and France zoom ----------
e = gap_grid(ANN)
fig = plt.figure(figsize=(7.6, 6.6))
ax = fig.add_axes([0.01, 0.17, 0.98, 0.82])
ax.add_patch(plt.Rectangle((-180, -60), 360, 145, color=SEA, zorder=0))
ax.imshow(rgb_grid(e), extent=[-180, 180, -60, 85], interpolation="nearest", zorder=1)
box = (-12.5, 9, 35.5, 52.6)
borders(ax, lw=.6, box=box)
ax.set_xlim(box[0], box[1]); ax.set_ylim(box[2], box[3]); ax.set_aspect(1 / np.cos(np.radians(43))); ax.axis("off")
gp = R["stories"]["galicia_places"]
pts = [("A Coruña", -1.2, .55), ("Vigo", -1.3, .05), ("Santiago de Compostela", 1.0, 0), ("Porto", -1.3, -.6), ("Lisbon", -1.3, 0), ("Madrid", .4, .4), ("Barcelona", -1.2, .6), ("London", .4, -.6)]
for n, dx, dy in pts:
    r = gp[n]; lab = f'{n.replace("Santiago de Compostela", "Santiago")}\n{"+" if r["e_ann"] >= 0 else ""}{int(round(r["e_ann"]))} min'
    ax.plot(r["lon"], r["lat"], "o", ms=4, mfc=FG, mec="white", mew=.8, zorder=5)
    ax.text(r["lon"] + dx, r["lat"] + dy, lab, fontsize=8, color=FG, ha="right" if dx < 0 else "left", va="center", zorder=6,
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=.85), linespacing=1.1)
legend_strip(fig, [0.05, 0.02, 0.9, 0.09], fs=6.6)
save(fig, "iberia")

# ---------- 6. clock minus sun against longitude ----------
PL = pd.read_pickle(os.path.join(WORK, "places.pkl.gz"))
big = PL[PL.population >= 100000]
fig, ax = plt.subplots(figsize=(7.6, 4.6))
ax.scatter(big.lon, big.e_std, s=3, color="#CFC4B2", lw=0, label="other cities")
for cc_, nm, c in [("CN", "China", "#B0362A"), ("IN", "India", "#EC9038"), ("RU", "Russia", "#5D8EBD"), ("ES", "Spain", "#6E1F3C"), ("AR", "Argentina", "#2E8B7A"), ("US", "United States", "#24527F")]:
    q = big[big.country == cc_]
    ax.scatter(q.lon, q.e_std, s=7, color=c, lw=0, label=nm)
ax.axhline(0, color=FG, lw=.9)
ax.set_xlim(-130, 150); ax.set_ylim(-90, 200)
ax.set_xlabel("longitude (degrees east)", fontsize=9); ax.set_ylabel("clock minus sun, no daylight saving (min)", fontsize=9)
ax.tick_params(labelsize=8.5); ax.grid(color=RULE, lw=.6); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=8, ncol=4, loc="upper left", markerscale=2)
fig.tight_layout(); save(fig, "longitude")
print("figures done")
