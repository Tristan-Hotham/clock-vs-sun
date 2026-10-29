"""Reddit collage: How wrong is your clock? 2400 x 3000 px. Run from the project root: python3 reddit/collage.py"""
import os, sys
import numpy as np
ROOTP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOTP, "code"))
src = open(os.path.join(ROOTP, "code", "05_figures.py")).read().split("# ---------- 1. world map")[0]
exec(src)
from matplotlib import font_manager as fm
DISP = fm.FontProperties(fname=os.path.join(FD, "FrauncesVar.ttf"), weight=900)
SER = "Source Serif 4"; MONO = "IBM Plex Mono"
PAPER = "#FBF3E6"; ACC = "#C2410C"
S = R["stories"]; gp = S["galicia_places"]; P = R["population"]

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=PAPER)
fig.text(0.04, 0.972, "How wrong is your clock?", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(0.04, 0.918, "Clock time minus solar time for the world's people under the time zone rules of 2026.\nOrange: the clock runs ahead of the sun, so sunrise, noon and sunset all come late by the clock.",
         family=SER, fontsize=15, color=FG, va="top", linespacing=1.35)

# hero map
ax = fig.add_axes([0.02, 0.585, 0.96, 0.27]); ax.set_facecolor(PAPER)
ax.imshow(rgb_grid(gap_grid(ANN)), extent=[-180, 180, -60, 85], interpolation="nearest", zorder=1)
borders(ax, lw=.22)
ax.set_xlim(-170, 180); ax.set_ylim(-56, 82); ax.set_aspect(1.1); ax.axis("off")
def dur(m):
    m = int(round(abs(m))); h, mm = divmod(m, 60)
    return f"{h} h {mm} min" if h and mm else (f"{h} h" if h else f"{mm} min")
k_, t_, m_ = S["china"]["kashgar"], S["india"]["east"], S["argentina"]["mendoza"]
for nm, lon, lat, tx, ty, lab in [("Kashgar", k_["lon"], k_["lat"], 52, 60, f'Kashgar\n{dur(k_["e_std"])} ahead'),
                                   ("A Coruña", gp["A Coruña"]["lon"], gp["A Coruña"]["lat"], -45, 25, f'A Coruña\n{dur(gp["A Coruña"]["e_ann"])} ahead'),
                                   ("Tinsukia", t_["lon"], t_["lat"], 120, 6, f'Tinsukia, Assam\n{dur(t_["e_std"])} behind'),
                                   ("Mendoza", m_["lon"], m_["lat"], -122, -40, f'Mendoza\n{dur(m_["e_std"])} ahead')]:
    ax.plot(lon, lat, "o", ms=5, mfc=FG, mec="white", mew=1, zorder=5)
    ax.annotate(lab, (lon, lat), xytext=(tx, ty), fontsize=10.5, family=MONO, color=FG, zorder=6, ha="center", va="center",
                arrowprops=dict(arrowstyle="-", color=FG, lw=.8), bbox=dict(boxstyle="round,pad=0.3", fc=PAPER, ec="none", alpha=.9))
# legend strip
lx = fig.add_axes([0.2, 0.555, 0.6, 0.018])
for i, c in enumerate(COLS): lx.add_patch(plt.Rectangle((i, 0), 1, 1, color=c, ec=PAPER, lw=1.5))
lx.set_xlim(0, 9); lx.set_ylim(0, 1); lx.axis("off")
for i, t in enumerate(["1 h", "30", "0", "30", "1 h", "1 h 30", "2 h", "2 h 30"]):
    lx.text(i + 1, -.35, t, ha="center", va="top", fontsize=9.5, family=MONO, color=MUT)
lx.text(0, 1.35, "clock behind the sun", fontsize=10, family=MONO, color=MUT); lx.text(9, 1.35, "clock ahead of the sun", fontsize=10, family=MONO, color=MUT, ha="right")

# headline numbers
nums = [(f'{round(P["e_ann"]["ahead"] * 100)}%', "of the world's people live where the\nclock runs ahead of the sun (2026 average)."),
        (f'{R["v"]["ahead_60_people_m"]:,}m', "people whose clock is more than\nan hour ahead of the sun."),
        (dur(R["country"]["Spain"]["e_ann"]), f"Spain: the furthest ahead of {R['countries']['n_1m']}\ncountries of a million people or more."),
        (gp["A Coruña"]["rise_late"], f"latest sunrise of the year in A Coruña,\nagainst {gp['London']['rise_late']} in London, {R['v']['gal_lat_minus_london']:.0f} degrees further north.")]
for k, (big, small) in enumerate(nums):
    x = 0.04 + (k % 2) * 0.48; y = 0.532 - (k // 2) * 0.09
    fig.text(x, y, big, fontproperties=DISP, fontsize=34, color=ACC, va="top")
    fig.text(x, y - 0.042, small, family=SER, fontsize=13, color=FG, va="top", linespacing=1.3)

# Galicia sunrise chart
fig.text(0.04, 0.33, "SUNRISE BY THE CLOCK, 2026 (LATER IS LOWER)", family=MONO, fontsize=11, color=MUT)
ser = load_json(os.path.join(WORK, "galicia_series.json"))
ag = fig.add_axes([0.08, 0.105, 0.5, 0.21]); ag.set_facecolor(PAPER)
d = np.arange(1, 366)
for n, c, w in [("London", "#2F5F8F", 1.6), ("Porto", "#2E8B7A", 1.3), ("Madrid", "#5B564F", 1.3), ("A Coruña", "#8E2A3B", 3)]:
    v = np.array(ser[n]["rise"]) / 60; ag.plot(d, v, color=c, lw=w)
    ag.text(368, v[-1] + {"London": .13, "Porto": -.13}.get(n, 0), n, fontsize=10.5, family=MONO, color=c, va="center", fontweight="medium")
ag.axhline(9, color="#8E2A3B", lw=.8, ls=(0, (4, 3))); ag.text(8, 8.93, "9:00", fontsize=9.5, family=MONO, color="#8E2A3B", va="bottom")
ag.set_ylim(9.5, 4.25); ag.set_xlim(1, 365)
ag.set_yticks([5, 6, 7, 8, 9]); ag.set_yticklabels(["5:00", "6:00", "7:00", "8:00", "9:00"], fontsize=9.5)
ag.set_xticks([15, 105, 196, 288]); ag.set_xticklabels(["Jan", "Apr", "Jul", "Oct"], fontsize=9.5)
for sp in ["top", "right"]: ag.spines[sp].set_visible(False)
ag.spines["left"].set_color(MUT); ag.spines["bottom"].set_color(MUT); ag.set_facecolor(PAPER)
ag.grid(axis="y", color="#E8DCC8", lw=.7)

# clock dials: latest sunrise of the year
fig.text(0.68, 0.33, "LATEST SUNRISE OF THE YEAR", family=MONO, fontsize=11, color=MUT)
dials = [("Kashgar", S["china"]["kashgar"]["rise_late"], "#6E1F3C"), ("A Coruña", gp["A Coruña"]["rise_late"], "#8E2A3B"),
         ("Madrid", gp["Madrid"]["rise_late"], "#5B564F"), ("London", gp["London"]["rise_late"], "#2F5F8F")]
for k, (n, t, c) in enumerate(dials):
    cx, cy = 0.73 + (k % 2) * 0.13, 0.27 - (k // 2) * 0.13
    a = fig.add_axes([cx - 0.055, cy - 0.044, 0.11, 0.088]); a.set_xlim(-1.25, 1.25); a.set_ylim(-1.25, 1.25); a.set_aspect(1); a.axis("off")
    a.add_patch(plt.Circle((0, 0), 1, fc="white", ec=FG, lw=1.6))
    for h in range(12):
        ang = np.pi / 2 - h * np.pi / 6; r0 = .82 if h % 3 else .74
        a.plot([r0 * np.cos(ang), .93 * np.cos(ang)], [r0 * np.sin(ang), .93 * np.sin(ang)], color=FG, lw=1.4 if h % 3 == 0 else .8)
    hh, mm = map(int, t.split(":"))
    am = np.pi / 2 - mm / 60 * 2 * np.pi; ah = np.pi / 2 - ((hh % 12) + mm / 60) / 12 * 2 * np.pi
    a.plot([0, .5 * np.cos(ah)], [0, .5 * np.sin(ah)], color=c, lw=3.2, solid_capstyle="round")
    a.plot([0, .78 * np.cos(am)], [0, .78 * np.sin(am)], color=c, lw=2, solid_capstyle="round")
    a.add_patch(plt.Circle((0, 0), .06, color=c))
    fig.text(cx, cy - 0.05, f"{n}  {t}", family=MONO, fontsize=11.5, color=FG, ha="center", va="top", fontweight="medium")

fig.text(0.04, 0.016, "Data: timezone-boundary-builder 2026a (ODbL, from OpenStreetMap); IANA tz database 2026e; Kontur Population 2023 (CC BY 4.0);\n"
         "GeoNames (CC BY 4.0); Natural Earth. Legal time (Xinjiang on Beijing time). Sun times: NOAA solar equations.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib. maps.tristanhotham.com/clock-vs-sun",
         family=MONO, fontsize=9, color=MUT, linespacing=1.45)
fig.savefig(os.path.join(ROOTP, "reddit", "clock_vs_sun.png"), dpi=200, facecolor=PAPER)
print("collage done")
