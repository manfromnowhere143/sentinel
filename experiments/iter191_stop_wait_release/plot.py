"""Render admitted paired completion counts; no scientific execution."""

import json
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .common import BASE, read


def main(root):
    data = json.loads(read(root, BASE / "proof/descriptive.json"))
    plt.rcParams.update(
        {"font.family": "DejaVu Sans", "font.size": 10, "svg.hashsalt": "sentinel191"}
    )
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
    fig.patch.set_facecolor("white")
    fig.suptitle(
        "Connector qualification: gains without lost completions",
        x=0.06,
        y=0.98,
        ha="left",
        fontsize=17,
        fontweight="bold",
        color="#17324d",
    )
    for ax, kind, title in zip(
        axes,
        ("original", "goal"),
        ("23 original requests · primary test", "21 synthetic goal requests · separate diagnostic"),
    ):
        groups = [r for r in data["groups"] if r["kind"] == kind]
        for i, color, label in (
            (0, "#a7b4c2", "Original connector"),
            (1, "#17324d", "With stop / wait / release"),
        ):
            positions = [j + (i - 0.5) * 0.36 for j in range(4)]
            bars = ax.bar(
                positions,
                [r["arms"][i]["complete"] for r in groups],
                width=0.34,
                color=color,
                label=label,
            )
            ax.bar_label(
                bars,
                labels=[f"{r['arms'][i]['complete']}/{r['requests']}" for r in groups],
                padding=5,
                fontsize=10,
            )
        ax.set_title(title, loc="left", fontsize=11, pad=17, color="#17324d")
        ax.set_xticks(range(4), ["Left bend", "Right bend", "Left chicane", "Right chicane"])
        ax.set_ylim(0, max(a["complete"] for r in data["groups"] for a in r["arms"]) + 2)
        ax.set_axisbelow(True)
        ax.grid(axis="y", color="#e8edf2")
        for edge in ("top", "right", "left"):
            ax.spines[edge].set_visible(False)
        ax.tick_params(axis="both", length=0)
    axes[0].set_ylabel("Full completions within original remaining budget")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles, labels, loc="lower left", bbox_to_anchor=(0.05, 0.07), ncol=2, frameon=False
    )
    fig.text(
        0.06,
        0.035,
        "All requests retained · fixed target horizons and budgets · exposed inputs · integrated result remains 3/4",
        color="#4b5d6d",
        fontsize=10,
    )
    fig.subplots_adjust(left=0.065, right=0.98, bottom=0.23, top=0.78, wspace=0.16)
    folder = root / BASE / "proof"
    fig.savefig(folder / "paired-completions.png", dpi=170)
    fig.savefig(folder / "paired-completions.svg", metadata={"Date": None})
    plt.close(fig)
    path = folder / "paired-completions.svg"
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


if __name__ == "__main__":
    main(Path.cwd())
