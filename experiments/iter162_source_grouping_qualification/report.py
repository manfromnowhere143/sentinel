"""Render only retained, independently admitted Iter162 selected paths."""

import json
from pathlib import Path
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "experiments/iter162_source_grouping_qualification"
a = json.loads((BASE / "proof/admission.json").read_text())
g = json.loads(
    (ROOT / "experiments/iter153_action_feasibility/proof/search_000/geometry.json").read_text()
)
assert a["phase"] == "closed" and a["runs"] == 2
colors = {"quantized": "#147b96", "exact": "#b24a30"}
plt.rcParams.update(
    {
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "svg.fonttype": "none",
        "savefig.facecolor": "#faf9f6",
        "figure.facecolor": "#faf9f6",
        "axes.facecolor": "#faf9f6",
        "font.family": "DejaVu Sans",
    }
)
fig, axs = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)
route = np.array(g["route"])
axs[0, 0].plot(route[:, 1], route[:, 0], c="#b2b6b7", lw=2, label="Retained route")
for r in a["records"]:
    arm = r["aggregation"]
    c = colors[arm]
    trace = json.loads((BASE / f"proof/raw/{arm}/selected/trace.json").read_text())
    states = np.array([row["state"] for row in trace])
    t = np.array([row["frame"] / 4 for row in trace])
    progress = [row["route"]["rc"] for row in trace]
    counts = [row["background"]["count"] for row in trace]
    label = f"{arm.title()} / 24"
    axs[0, 0].plot(states[:, 0], states[:, 1], c=c, lw=2, label=label)
    axs[0, 0].scatter(states[-1, 0], states[-1, 1], c=c, s=45, marker="s", zorder=4)
    axs[0, 1].plot(t, progress, c=c, lw=2, label=label)
    axs[0, 1].scatter(t[-1], progress[-1], c=c, s=30)
    axs[1, 0].plot(t, counts, c=c, lw=1.8, label=label)
    stop = r["stop"].replace("_", " ")
    axs[0, 1].annotate(
        f"{arm.title()}: {stop}\n{r['attempts']:,} attempts; {r['completed_depth']} layers",
        xy=(0.98, 0.26 if arm == "exact" else 0.10),
        xycoords="axes fraction",
        ha="right",
        color=c,
        fontsize=9,
    )
axs[0, 0].set(
    xlabel="Model x (m)",
    ylabel="Model y (m)",
    title="A · Admitted selected paths, not the whole search tree",
)
axs[0, 0].set_aspect("equal", adjustable="datalim")
axs[0, 0].legend(loc="best", frameon=False, fontsize=9)
axs[0, 1].axhline(1, color="#444444", lw=1, ls="--", label="Completion threshold")
for item in g["comparators"].values():
    axs[0, 1].scatter(
        item["hazard_time"], item["rc"] - 0.05, marker="^", s=45, c="#262626", zorder=5
    )
axs[0, 1].set(
    xlabel="Absolute model time (s)",
    ylabel="Original route progress",
    title="B · Progress and required checkpoint minima",
    ylim=(-0.03, 1.08),
)
axs[0, 1].legend(
    loc="upper left", frameon=True, facecolor="#faf9f6", edgecolor="none", framealpha=1, fontsize=9
)
axs[1, 0].axhline(100, color="#444444", lw=1, ls="--", label="Strict rejection above 100")
axs[1, 0].set(
    xlabel="Absolute model time (s)",
    ylabel="Centers in sampled vehicle box",
    title="C · Full-population scalar replay at selected states",
)
axs[1, 0].legend(
    loc="upper right", frameon=True, facecolor="#faf9f6", edgecolor="none", framealpha=1, fontsize=9
)
axs[1, 0].text(
    0.5,
    0.45,
    "Both paths: zero enclosed centers\nat every selected state",
    transform=axs[1, 0].transAxes,
    ha="center",
    color="#444444",
    fontsize=10,
)
keys = ["grouping_removed", "width_removed", "retained"]
labels = ["Removed by grouping", "Removed by width", "Retained events"]
palette = ["#d8ba9b", "#8295a6", "#53665b"]
left = np.zeros(2)
for key, label, color in zip(keys, labels, palette):
    values = np.array([r["retention"][key] for r in a["records"]])
    axs[1, 1].barh([0, 1], values, left=left, color=color, label=label, height=0.4)
    left += values
axs[1, 1].set(
    yticks=[0, 1],
    yticklabels=["Quantized / 24", "Exact / 24"],
    xlabel="Clear candidate events at completed depths",
    title="D · Grouping and width remain separate stages",
)
axs[1, 1].legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), frameon=False, fontsize=9, ncol=1)
for ax in axs.flat:
    ax.grid(axis="y", alpha=0.15)
fig.suptitle(
    f"Iter162 · Matched source-model qualification\n{a['complete_runs']}/2 complete paths · {a['verified_states']} scalar-verified states · one exposed source scene",
    fontsize=16,
)
for ext in ["png", "pdf", "svg"]:
    fig.savefig(BASE / f"proof/source_comparison.{ext}", dpi=180)
plt.close(fig)
