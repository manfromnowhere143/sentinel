"""Plot independently admitted counts and retained full-horizon paths."""

import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

BASE = Path(__file__).parent


def main():
    admission = json.loads((BASE / "proof/admission.json").read_text())
    prior = BASE.parent / "iter170_derivative_step"
    cases = {
        r["id"]: r
        for r in json.loads((BASE.parent / "iter168_control_connector/CASES.json").read_text())
    }
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "text.color": "#172f43",
        }
    )
    fig, axes = plt.subplots(2, 2, figsize=(12, 7.6))
    fig.subplots_adjust(left=0.14, right=0.97, top=0.82, bottom=0.13, wspace=0.3, hspace=0.6)
    fig.suptitle(
        "Full-horizon control qualifies on twelve constructed tasks",
        x=0.09,
        y=0.96,
        ha="left",
        fontsize=17,
        fontweight="bold",
    )
    fig.text(
        0.09,
        0.905,
        "Sentinel · Iter169–171 · Same tasks, tolerances and caps · Independent scalar replay · 14 October 2026",
        fontsize=9,
        color="#526779",
    )
    first = json.loads(
        (BASE.parent / "iter169_full_horizon_control/proof/admission.json").read_text()
    )
    totals = [
        admission["baseline_attempts"],
        first["total_attempts"],
        admission["previous_attempts"],
        admission["total_attempts"],
    ]
    bars = axes[0, 0].barh(
        ["168 · two steps", "169 · shooting", "170 · diff. step", "171 · centered"],
        totals,
        color=["#889bab"] * 3 + ["#008d82"],
    )
    axes[0, 0].bar_label(
        bars,
        labels=[f"{v:,} · {n}/12" for v, n in zip(totals, [10, 10, 10, 12])],
        padding=5,
        fontsize=9,
    )
    axes[0, 0].invert_yaxis()
    axes[0, 0].set(xlim=(0, 8900), xlabel="Total attempted transitions across 12 tasks")
    axes[0, 0].set_title("Completion and work; equal caps, different cost", loc="left", fontsize=11)
    for i, r in enumerate(admission["records"][-2:]):
        task = cases[r["case"]]["task"]
        errors = np.abs(np.array(r["final_state"]) - task["target"]) / task["tolerance"]
        axes[0, 1].bar(
            np.arange(5) + (i - 0.5) * 0.31,
            errors,
            width=0.29,
            color=["#008d82", "#85c8bf"][i],
            label=["Left", "Right"][i],
        )
    axes[0, 1].axhline(1, color="#b76d3c", linestyle="--", linewidth=1, label="Tolerance")
    axes[0, 1].set(
        xticks=np.arange(5),
        xticklabels=["Forward", "Lateral", "Heading", "Speed", "Steering"],
        ylim=(0, 1.22),
        ylabel="Absolute error / allowed error",
    )
    axes[0, 1].set_title(
        "Both longer turns satisfy every terminal tolerance", loc="left", fontsize=11
    )
    axes[0, 1].legend(frameon=False, fontsize=8, ncols=3, loc="upper center")
    locations = [
        (prior / "proof/search_raw/turn_8_left/selected", "170 · unsuccessful", "#889bab"),
        (BASE / "proof/search_raw/turn_8_left/selected", "171 · qualified", "#008d82"),
        (BASE / "proof/search_raw/turn_8_left_witness", "Constructive witness", "#c58936"),
    ]
    for folder, label, color in locations:
        rows = json.loads((folder / "trace.json").read_text())
        states = np.array([r["state"] for r in rows])
        t = np.array([r["frame"] for r in rows]) * 0.25
        for j, column in enumerate([3, 4]):
            axes[1, j].plot(t, states[:, column], ".-", color=color, label=label)
    axes[1, 0].set(xlabel="Time (s)", ylabel="Speed (m/s)")
    axes[1, 1].set(xlabel="Time (s)", ylabel="Steering angle (rad)")
    axes[1, 0].set_title("Longer left turn: speed across the full horizon", loc="left", fontsize=11)
    axes[1, 1].set_title(
        "Longer left turn: steering across the full horizon", loc="left", fontsize=11
    )
    axes[1, 0].legend(frameon=False, fontsize=8)
    for ax in axes.flat:
        ax.grid(axis="y", alpha=0.15)
        ax.set_axisbelow(True)
    fig.text(
        0.09,
        0.045,
        "284 states/full masks independently replay. These exposed model tasks do not qualify RRT integration or source recovery.",
        fontsize=9,
        color="#526779",
    )
    fig.savefig(BASE / "proof/full_horizon_qualification.png", dpi=180, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
