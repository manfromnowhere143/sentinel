"""Derived presentation of committed admission and selected-prefix evidence."""

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

base = Path(__file__).resolve().parent
root = base.parents[1]
paths = [
    base / "proof/admission.json",
    base / "proof/raw/trace.json",
    root / "experiments/iter153_action_feasibility/proof/search_000/geometry.json",
]
admission, trace, geometry = [json.loads(p.read_text()) for p in paths]
fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))
fig.subplots_adjust(left=0.055, right=0.98, bottom=0.25, top=0.73, wspace=0.35)
fig.suptitle(
    "A verified prefix; useful recovery remains unestablished",
    x=0.055,
    ha="left",
    fontsize=16,
    fontweight="bold",
)
fig.text(
    0.055,
    0.84,
    "Iter158  /  Inconclusive  /  One exposed source-model scene",
    fontsize=10,
    color="#4b5f6d",
)
route = [p for p in geometry["route"] if p[1] <= 34]
axes[0].plot(
    [p[1] for p in route], [p[0] for p in route], "--", color="#8c9aa5", label="Source route"
)
axes[0].plot(
    [r["state"][0] for r in trace],
    [r["state"][1] for r in trace],
    color="#236878",
    lw=2.4,
    label="Retained prefix",
)
axes[0].scatter([trace[-1]["state"][0]], [trace[-1]["state"][1]], color="#236878")
axes[0].scatter([30], [-1.05], marker="s", s=100, color="#b5734c", label="Foreground center")
axes[0].set(
    xlabel="Forward position (m)",
    ylabel="Lateral position (m)",
    title="The retained path is partial",
)
axes[0].legend(fontsize=8, loc="lower left", frameon=False)
times = [r["frame"] / 4 for r in trace]
axes[1].step(times, [100 * r["route"]["rc"] for r in trace], where="post", color="#236878", lw=2.3)
for i, (name, c) in enumerate(geometry["comparators"].items()):
    floor = 100 * (c["rc"] - 0.05)
    axes[1].scatter([c["hazard_time"]], [floor], marker="x", color="#b5734c", s=55)
    axes[1].annotate(
        f"{name} floor",
        (c["hazard_time"], floor),
        xytext=(-8, 14 if i == 0 else -22),
        textcoords="offset points",
        ha="right",
        fontsize=8,
    )
axes[1].set(
    xlim=(0, 9.5),
    ylim=(0, 38),
    xlabel="Model time (s)",
    ylabel="Source route progress (%)",
    title="No progress checkpoint reached",
)
axes[2].plot(times, [r["background"]["count"] for r in trace], "o-", ms=3, color="#236878")
axes[2].axhline(100, ls="--", color="#b5734c", lw=1)
axes[2].text(0.1, 103, "Collision requires >100", fontsize=8, color="#965a39")
axes[2].set(
    ylim=(-4, 120),
    xlabel="Model time (s)",
    ylabel="Selected centers inside box",
    title="19 complete scalar masks agree",
)
for ax in axes:
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=8)
    ax.grid(axis="y", alpha=0.13)
    title = ax.get_title()
    ax.set_title("", loc="center")
    ax.set_title(title, fontsize=10, loc="left", pad=12)
fig.text(
    0.055,
    0.09,
    "10,633 attempted transitions. No complete trajectory. Unselected pruning remains producer evidence.",
    fontsize=10,
)
fig.text(
    0.055,
    0.045,
    "No native drive, road-compliance claim, physical occupancy proof or global infeasibility conclusion.",
    fontsize=9,
    color="#4b5f6d",
)
for suffix in ("png", "svg"):
    fig.savefig(base / f"proof/search-prefix.{suffix}", dpi=170)
(base / "proof/figure-identity.json").write_text(
    json.dumps(
        {
            "scope": "Derived figure; no new scientific evaluation",
            "inputs": {
                str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths
            },
            "outputs": {
                suffix: hashlib.sha256(
                    (base / f"proof/search-prefix.{suffix}").read_bytes()
                ).hexdigest()
                for suffix in ("png", "svg")
            },
        },
        indent=2,
    )
    + "\n"
)
