"""Admitted outcome and work comparison against both retained references."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch


def main():
    base = Path(__file__).resolve().parent
    a = json.loads((base / "proof/admission.json").read_text())
    best, parent, rows = a["comparison"]["pairs"], a["parent_comparison"]["pairs"], a["records"]
    matrix = [
        [
            int(best[i]["reference_complete"]),
            int(parent[i]["reference_complete"]),
            int(r["complete"]),
        ]
        for i, r in enumerate(rows)
    ]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.8), gridspec_kw={"width_ratios": [1, 1.4]})
    fig.patch.set_facecolor("#fafaf7")
    names = [r["case"].replace("_", " ") for r in rows]
    axes[0].imshow(
        matrix, cmap=ListedColormap(["#e3d1c6", "#277461"]), vmin=0, vmax=1, aspect="auto"
    )
    axes[0].set_yticks(range(4), names)
    axes[0].set_xticks(range(3), ["Iter178\n3/4", "Iter181\n2/4", "Iter183\n3/4"])
    axes[0].set_title("One regression repaired; no new best outcome", fontsize=11, pad=15)
    axes[0].tick_params(length=0)
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            axes[0].text(
                j,
                i,
                "Complete" if value else "Miss",
                ha="center",
                va="center",
                color="white" if value else "#613b2c",
                fontsize=10,
            )
    for spine in axes[0].spines.values():
        spine.set_visible(False)
    colors = ["#b9c6ce", "#b8886e", "#326784"]
    axes[1].set_facecolor("#fafaf7")
    axes[1].spines[["top", "right", "left"]].set_visible(False)
    for i, row in enumerate(rows):
        values = [best[i]["reference_attempts"], parent[i]["reference_attempts"], row["attempts"]]
        for offset, value, color in zip((-0.24, 0, 0.24), values, colors):
            axes[1].barh(i + offset, value, height=0.2, color=color)
        axes[1].text(
            row["attempts"] + 250, i + 0.24, f"{row['attempts']:,}", va="center", fontsize=9
        )
    axes[1].set_yticks(range(4), names)
    axes[1].invert_yaxis()
    axes[1].tick_params(axis="y", length=0)
    axes[1].axvline(18000, color="#687078", linestyle="--", linewidth=1)
    axes[1].set(
        xlim=(0, 20700),
        xlabel="Attempted transitions; 18,000 cap per case",
        title="Same ceilings; different work consumed",
    )
    axes[1].set_xticks([0, 6000, 12000, 18000], ["0", "6,000", "12,000", "18,000"])
    fig.suptitle("Timing eligibility restores 3/4; right bend still misses", fontsize=18, y=0.96)
    fig.legend(
        handles=[
            Patch(color=color, label=label)
            for color, label in zip(
                colors, ["Retained Iter178", "Parent Iter181", "Candidate Iter183"]
            )
        ],
        loc="lower center",
        bbox_to_anchor=(0.53, 0.11),
        ncol=3,
        frameon=False,
    )
    fig.text(
        0.07,
        0.055,
        "Source comparison remains closed. One exposed seed per case; no actual-history intervention or latency claim.",
        fontsize=10,
        color="#465057",
    )
    fig.subplots_adjust(left=0.11, right=0.98, bottom=0.29, top=0.79, wspace=0.43)
    fig.savefig(base / "proof/qualification.png", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    main()
