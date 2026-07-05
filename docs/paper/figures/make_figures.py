#!/usr/bin/env python3
"""Manuscript figures, generated from committed evidence. Print-quality (PDF + 300 dpi PNG),
colorblind-validated palette (reference-theme slots; pairs pass the six-check validator),
grayscale-safe (texture on the baseline series; lightness-distinct action pair), direct labels
on every bar (the relief rule for the sub-3:1 aqua).

Data sources:
  F1  experiments/full14_power/proof/analysis_output.txt   (n=20/pair per-class cells)
  F2  experiments/verification/analyze_safety_case.py       (six lead-time events)
  F3  experiments/iter17_threat_routing/proof/analysis_output.txt (routing audit per class)
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BLUE = '#2a78d6'      # monitored (theme slot 1)
ORANGE = '#eb6834'    # unmonitored baseline (theme slot 8; hatched for grayscale)
VIOLET = '#4a3aa7'    # stop frames (slot 5)
AQUA = '#1baf7a'      # crawl frames (slot 2; relief: direct labels)
INK = '#0b0b0b'
INK2 = '#52514e'
GRID = '#e8e8e6'

plt.rcParams.update({
    'font.size': 8.5, 'axes.edgecolor': INK2, 'axes.labelcolor': INK,
    'text.color': INK, 'xtick.color': INK2, 'ytick.color': INK2,
    'axes.linewidth': 0.7, 'hatch.linewidth': 0.5,
})


def style(ax):
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def label_bars(ax, bars, fmt, dy):
    for b in bars:
        ax.annotate(fmt.format(b.get_height()), (b.get_x() + b.get_width() / 2, b.get_height()),
                    ha='center', va='bottom', fontsize=7.5, color=INK, xytext=(0, dy),
                    textcoords='offset points')


CLASSES = ['stationary', 'frontal', 'side']
X = range(3)
W = 0.36
GAP = 0.02  # the 2px-equivalent surface gap between adjacent fills

# ---- F1: per-class benchmark result at n=20/pair --------------------------------------------
score_off, score_mon = [3.65, 1.24, 1.48], [4.13, 1.78, 2.81]
coll_off, coll_mon = [29, 78, 74], [18, 90, 44]

fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.6, 2.5), constrained_layout=True)
for ax, off, mon, ylab, fmt, top in [
        (a1, score_off, score_mon, 'NeuroNCAP score (0–5)', '{:.2f}', 5),
        (a2, coll_off, coll_mon, 'collision rate (%)', '{:.0f}', 100)]:
    b1 = ax.bar([x - W / 2 - GAP / 2 for x in X], off, W, color=ORANGE, hatch='///',
                edgecolor='white', linewidth=0.4, label='unmonitored UniAD')
    b2 = ax.bar([x + W / 2 + GAP / 2 for x in X], mon, W, color=BLUE,
                edgecolor='white', linewidth=0.4, label='+ released union')
    style(ax)
    ax.set_xticks(list(X), CLASSES)
    ax.set_ylabel(ylab)
    ax.set_ylim(0, top * 1.14)
    label_bars(ax, b1, fmt, 1)
    label_bars(ax, b2, fmt, 1)
a1.legend(frameon=False, fontsize=7.5, loc='upper right')
fig.savefig('fig1_benchmark.pdf')
fig.savefig('fig1_benchmark.png', dpi=300)

# ---- F2: detection lead time — six events, shown as events (n too small for a histogram) ----
leads = [(3.5, 'frontal'), (1.9, 'frontal'), (1.0, 'frontal'), (1.7, 'frontal'),
         (2.5, 'side'), (3.5, 'side')]
fig, ax = plt.subplots(figsize=(4.6, 1.7), constrained_layout=True)
rows = {'frontal': 1, 'side': 0}
seen_offsets = {}
for t, k in leads:
    key = (t, k)
    seen_offsets[key] = seen_offsets.get(key, 0) + 1
    y = rows[k] + (seen_offsets[key] - 1) * 0.18
    ax.plot(t, y, 'o', ms=7, color=BLUE, mec='white', mew=0.8)
ax.axvline(2.5, color=INK2, linewidth=0.9, linestyle=(0, (4, 3)))
ax.annotate('median 2.5 s', (2.5, 1.52), ha='left', fontsize=7.5, color=INK2, xytext=(4, 0),
            textcoords='offset points')
style(ax)
ax.yaxis.grid(False)
ax.xaxis.grid(True, color=GRID, linewidth=0.6)
ax.set_yticks([0, 1], ['side', 'frontal'])
ax.set_xlim(0, 4)
ax.set_ylim(-0.4, 1.75)
ax.set_xlabel('first brake before counterfactual contact (s)')
fig.savefig('fig2_leadtime.pdf')
fig.savefig('fig2_leadtime.png', dpi=300)

# ---- F3: iteration-17 routing audit — latched frames by action, per class -------------------
stop_f, crawl_f = [82, 53, 35], [73, 86, 81]
fig, ax = plt.subplots(figsize=(3.4, 2.3), constrained_layout=True)
b1 = ax.bar([x - W / 2 - GAP / 2 for x in X], stop_f, W, color=VIOLET,
            edgecolor='white', linewidth=0.4, label='stop frames')
b2 = ax.bar([x + W / 2 + GAP / 2 for x in X], crawl_f, W, color=AQUA,
            edgecolor='white', linewidth=0.4, label='crawl frames')
style(ax)
ax.set_xticks(list(X), CLASSES)
ax.set_ylabel('latched frames (120 episodes)')
ax.set_ylim(0, 105)
label_bars(ax, b1, '{:.0f}', 1)
label_bars(ax, b2, '{:.0f}', 1)
ax.legend(frameon=False, fontsize=7.5, loc='upper left')
fig.savefig('fig3_routing.pdf')
fig.savefig('fig3_routing.png', dpi=300)
print('figures written')
