"""Step 6: header.png, the 1200 x 630 social card (matplotlib, same map as figure 1)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
# reuse helpers without re-rendering every figure
src = open(os.path.join(os.path.dirname(__file__), "05_figures.py")).read().split("# ---------- 1. world map")[0]
exec(src)
from matplotlib import font_manager as fm
DISP = fm.FontProperties(fname=os.path.join(FD, "FrauncesVar.ttf"), weight=900) if os.path.isdir(FD) else None
CREAM = "#FAF6EE"
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=CREAM)
ax = fig.add_axes([0.345, 0.03, 0.645, 0.94]); ax.set_facecolor(CREAM)
ax.imshow(rgb_grid(gap_grid(ANN)), extent=[-180, 180, -60, 85], interpolation="nearest", zorder=1)
borders(ax, lw=.2)
ax.set_xlim(-170, 180); ax.set_ylim(-56, 82); ax.set_aspect(1.1); ax.axis("off")
fig.text(0.035, 0.90, "How wrong\nis your\nclock?", fontproperties=DISP, fontsize=50, color=FG, va="top", linespacing=.9)
fig.text(0.035, 0.49, f'{round(R["population"]["e_ann"]["ahead"] * 100)}% of the world\'s people live\nwhere the clock runs ahead\nof the sun.', fontsize=15, color=FG, va="top", family="Source Serif 4", linespacing=1.25)
for i, c in enumerate(COLS):
    fig.patches.append(plt.Rectangle((0.035 + i * 0.03, 0.255), 0.03, 0.024, color=c, transform=fig.transFigure, figure=fig))
fig.text(0.035, 0.24, "clock behind", fontsize=9, color=MUT, va="top"); fig.text(0.035 + 9 * 0.03, 0.24, "ahead of the sun", fontsize=9, color=MUT, va="top", ha="right")
fig.text(0.035, 0.06, "Dr Tristan Hotham · 2026\nmaps.tristanhotham.com/clock-vs-sun", fontsize=10.5, color=MUT, va="bottom", linespacing=1.4)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=CREAM)
print("header.png")
