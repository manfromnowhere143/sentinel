"""Plot admitted work and paired outcomes without changing evidence."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

BASE = Path(__file__).resolve().parent
state = json.loads((BASE / "admission.json").read_text())
calls = [r["call"] for r in state["pairs"]]
fig, ax = plt.subplots(figsize=(10.8, 7.2), layout="constrained")
fig.patch.set_facecolor("#f8fafc")
ax.set_facecolor("#f8fafc")
colors = {"program": "#245b85", "beam": "#ad6226"}
for arm, offset in (("program", -0.15), ("beam", 0.15)):
    rows = [
        next(r for r in state["records"] if r["call"] == call and r["arm"] == arm) for call in calls
    ]
    positions = np.arange(len(rows)) + offset
    ax.hlines(
        positions, 0, [r["attempts"] for r in rows], color=colors[arm], alpha=0.25, linewidth=2
    )
    for i, row in enumerate(rows):
        ax.scatter(
            row["attempts"],
            positions[i],
            marker="o" if row["witness"] else "x",
            s=65 if row["witness"] else 30,
            color=colors[arm],
            zorder=3,
        )
ax.axvline(128, color="#64748b", linestyle="--", linewidth=1)
ax.set_xlim(-2, 137)
ax.set_xticks([0, 32, 64, 96, 128])
ax.set_yticks(
    range(len(calls)), [f"{call}" + (" *" if call in (63, 132) else "") for call in calls]
)
ax.invert_yaxis()
ax.set_xlabel("Attempted transitions per run · ceiling 128", fontsize=11)
ax.set_ylabel("Retained root call", fontsize=11)
ax.set_title(
    "The same three roots yield checkpoint witnesses",
    loc="left",
    fontsize=17,
    fontweight="bold",
    pad=37,
)
ax.text(
    0,
    1.035,
    "16 paired roots · 3 witnesses per method · 0 gains · 0 losses · 0 censored pairs",
    transform=ax.transAxes,
    fontsize=11,
    color="#334155",
)
legend = [
    Line2D([0], [0], color=colors["program"], lw=2, label="Retained program"),
    Line2D([0], [0], color=colors["beam"], lw=2, label="Width-two beam"),
    Line2D([0], [0], color="#334155", marker="o", linestyle="none", label="Checkpoint witness"),
    Line2D([0], [0], color="#334155", marker="x", linestyle="none", label="Bounded miss"),
]
ax.legend(
    handles=legend,
    loc="lower center",
    bbox_to_anchor=(0.5, -0.205),
    ncol=4,
    frameon=False,
    fontsize=9,
)
fig.supxlabel(
    "* Prior necessary-progress exclusion; both methods still searched.\nEqual ceilings, different consumed work. Integrated qualification remains 3/4; source comparison closed.",
    fontsize=10,
    color="#334155",
)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="x", alpha=0.15)
fig.savefig(BASE / "continuation_comparison.png", dpi=180)
