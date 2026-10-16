"""Plot admitted conditional paths and separate remaining-work accounting."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

BASE = Path(__file__).resolve().parent


def main():
    result = json.loads((BASE / "STATE.json").read_text())
    plan = json.loads((BASE / "PLAN.json").read_text())
    cases = json.loads((BASE.parent / "iter161_grouping_width_ablation/CASES.json").read_text())
    case = next(c for c in cases if c["id"] == "bend_right")
    colors = ["#237466", "#b37d56", "#416b85"]
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.3), gridspec_kw=dict(width_ratios=[1, 1.3]))
    fig.patch.set_facecolor("#fafaf8")
    for ax in axes:
        ax.set_facecolor("#fafaf8")
        ax.spines[["top", "right"]].set_visible(False)
    route = case["geometry"]["route"]
    axes[0].plot(
        [p[1] for p in route],
        [p[0] for p in route],
        color="#c4cacb",
        linewidth=6,
        label="Reference route",
    )
    for i, row in enumerate(result["records"]):
        trace = json.loads((BASE / f"proof/search_raw/probe_{i}/trace.json").read_text())
        raw = json.loads((BASE / f"proof/search_raw/probe_{i}/result.json").read_text())
        frame = raw["start_frame"]
        prefix, suffix = trace[: frame + 1], trace[frame:]
        axes[0].plot(
            [p["state"][0] for p in prefix],
            [p["state"][1] for p in prefix],
            color=colors[i],
            linestyle="--",
            alpha=0.5,
            linewidth=1.4,
        )
        label = f"Call {row['root_identity'][0]}: " + (
            "complete" if row["full_route_continuation"] else "bounded miss"
        )
        axes[0].plot(
            [p["state"][0] for p in suffix],
            [p["state"][1] for p in suffix],
            color=colors[i],
            linewidth=2.7,
            label=label,
        )
        axes[0].scatter(
            *prefix[-1]["state"][:2], s=70, facecolors="white", edgecolors=colors[i], zorder=5
        )
        axes[0].scatter(
            *trace[-1]["state"][:2],
            s=80,
            marker="*" if row["full_route_continuation"] else "x",
            color=colors[i],
            zorder=6,
        )
        before = 18000 - plan["remaining_attempts"][i]
        axes[1].barh(i, before, color="#c3c9cb", height=0.55)
        axes[1].barh(
            i,
            row["attempts"],
            left=before,
            color=colors[0] if row["full_route_continuation"] else colors[1],
            height=0.55,
        )
        axes[1].text(18250, i, f"{row['attempts']:,}", va="center", fontsize=12)
    axes[0].set_aspect("equal", adjustable="datalim")
    axes[0].set_xlabel("Source-model x")
    axes[0].set_ylabel("Source-model y")
    axes[0].set_title("Dashed: retained prefix · solid: new continuation", fontsize=12, pad=14)
    axes[0].legend(frameon=False, loc="lower left", fontsize=10)
    axes[1].set_yticks(
        range(3), ["Call 83 / root frame 24", "Call 98 / root frame 24", "Call 110 / root frame 14"]
    )
    axes[1].set_ylim(3.4, -0.5)
    axes[1].text(18250, -0.38, "New work", fontsize=10)
    axes[1].axvline(18000, color="#737b80", linestyle="--", linewidth=1.2)
    axes[1].set_xlim(0, 20600)
    axes[1].set_xticks([0, 6000, 12000, 18000], ["0", "6,000", "12,000", "18,000"])
    axes[1].set_xlabel("Accounted transitions per conditional root")
    axes[1].set_title("Original work through discovery + conditional search", fontsize=12, pad=14)
    axes[1].legend(
        handles=[
            Patch(color="#c3c9cb", label="Original work"),
            Patch(color="#237466", label="New work; completion"),
            Patch(color="#b37d56", label="New work; bounded miss"),
        ],
        frameon=False,
        loc="lower left",
        fontsize=10,
    )
    fig.suptitle("One discarded full-route opportunity; two unresolved misses", fontsize=20, y=0.97)
    fig.text(
        0.5,
        0.035,
        "Fresh conditional trees; no integrated qualification credit. Best retained result 3/4; source comparison closed.",
        ha="center",
        fontsize=11,
        color="#53616a",
    )
    fig.tight_layout(rect=(0, 0.09, 1, 0.91), w_pad=3)
    fig.savefig(BASE / "proof/continuations.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
