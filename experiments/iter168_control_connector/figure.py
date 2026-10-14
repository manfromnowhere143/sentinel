"""Render admitted counts and retained traces; no experiment or new inference."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

BASE = Path(__file__).parent


def main():
    admission = json.loads((BASE / "proof/admission.json").read_text())
    raw = BASE / "proof/search_raw"
    colors = ["#7799c3", "#00a99c", "#db9b43"]
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.labelcolor": "#294257",
            "text.color": "#172f43",
        }
    )
    fig, axes = plt.subplots(2, 2, figsize=(12, 7.4), gridspec_kw={"height_ratios": [1, 1.2]})
    fig.subplots_adjust(left=0.09, right=0.97, top=0.83, bottom=0.12, wspace=0.31, hspace=0.55)
    fig.suptitle(
        "Stopping and waiting pass. Longer turning remains unqualified.",
        x=0.09,
        y=0.96,
        ha="left",
        fontsize=18,
        fontweight="bold",
    )
    fig.text(
        0.09,
        0.905,
        "Sentinel · Iter168 · 12 disclosed tasks · Independent scalar admission · 14 October 2026",
        fontsize=10,
        color="#526779",
    )
    groups = [
        ("Stop + hold", "stop_", 4),
        ("Wait", "wait_", 2),
        ("Wait + restart", "wait_restart_", 2),
        ("Short turn", "turn_2_", 2),
        ("Longer turn", "turn_8_", 2),
    ]
    x = np.arange(5)
    for depth, offset in ((1, -0.17), (2, 0.17)):
        counts = []
        for label, prefix, n in groups:
            selected = [
                r
                for r in admission["records"]
                if r["depth"] == depth
                and r["case"].startswith(prefix)
                and (prefix != "wait_" or not r["case"].startswith("wait_restart_"))
            ]
            counts.append(sum(r["complete"] for r in selected))
        bars = axes[0, 0].bar(
            x + offset, counts, width=0.31, color=colors[depth - 1], label=f"{depth}-step"
        )
        axes[0, 0].bar_label(
            bars, labels=[f"{v}/{n}" for v, (_, _, n) in zip(counts, groups)], padding=3, fontsize=9
        )
    axes[0, 0].set(
        xticks=x,
        xticklabels=[g[0] for g in groups],
        ylim=(0, 5),
        yticks=[0, 2, 4],
        ylabel="Tasks completed",
    )
    axes[0, 0].tick_params(axis="x", labelsize=8)
    axes[0, 0].set_title("8/12 → 10/12, still below the 12/12 gate", loc="left", fontsize=11)
    axes[0, 0].legend(frameon=False, fontsize=9)
    totals = [sum(r["attempts"] for r in admission["records"] if r["depth"] == d) for d in (1, 2)]
    bars = axes[0, 1].barh(["1-step", "2-step"], totals, color=colors[:2], height=0.5)
    axes[0, 1].bar_label(bars, labels=[f"{v:,}" for v in totals], padding=5)
    axes[0, 1].set(xlim=(0, 8500), xlabel="Total attempted transitions across 12 tasks")
    axes[0, 1].set_title(
        "Equal caps; substantially different realized work", loc="left", fontsize=11
    )
    for depth in (0, 1, 2):
        folder = raw / (
            "turn_8_left_witness" if depth == 0 else f"turn_8_left_depth{depth}/selected"
        )
        trace = json.loads((folder / "trace.json").read_text())
        states = np.asarray([r["state"] for r in trace])
        color, label = (
            (colors[2], "Constructive witness")
            if depth == 0
            else (colors[depth - 1], f"{depth}-step selected")
        )
        axes[1, 0].plot(states[:, 0], states[:, 1], ".-", color=color, label=label)
        axes[1, 1].plot(np.arange(len(states)) / 4, states[:, 3], ".-", color=color, label=label)
    axes[1, 0].set(xlabel="Forward position (m)", ylabel="Lateral position (m)")
    axes[1, 0].set_title("Eight-frame left turn: retained paths", loc="left", fontsize=11)
    axes[1, 0].legend(frameon=False, fontsize=8, loc="upper left")
    axes[1, 1].set(xlabel="Time (s)", ylabel="Speed (m/s)", ylim=(0.6, 3.8))
    axes[1, 1].set_title("Both connectors end 1 m/s below the target", loc="left", fontsize=11)
    for ax in axes.flat:
        ax.grid(axis="y", alpha=0.15)
        ax.set_axisbelow(True)
    fig.text(
        0.09,
        0.035,
        "All 12 witnesses pass. All 24 runs reach the terminal frame without a budget cap. No source or native comparison.",
        fontsize=9,
        color="#526779",
    )
    fig.savefig(BASE / "proof/connector_qualification.png", dpi=180, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
