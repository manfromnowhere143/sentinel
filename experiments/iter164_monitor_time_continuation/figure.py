"""Descriptive plot of admitted history and continuation; no new estimator."""

import json
import math
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

from .continuation import concatenate
from .common import inputs

BASE = Path("experiments/iter164_monitor_time_continuation")


def read(path):
    return json.loads(path.read_text())


def main():
    admission = read(BASE / "proof/admission.json")
    assert admission["status"] in {"supported", "contradicted"}
    plan = read(BASE / "PLAN.json")
    geometry, _, arrays = inputs(Path.cwd(), plan)
    prefix = read(BASE / "proof/prefix_raw/replica_0/trace.json")
    suffix = read(BASE / "proof/search_raw/selected/trace.json")
    joined = concatenate(prefix, suffix)
    old = read(
        Path(
            "experiments/iter162_source_grouping_qualification/proof/raw/exact/selected/trace.json"
        )
    )
    points = arrays["selected_xyz"]
    states = np.array([r["state"] for r in joined])
    previous = np.array([r["state"] for r in old])
    route = np.array(geometry["route"])
    start = plan["start_frame"]
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "text.color": "#162d3b",
            "axes.labelcolor": "#263945",
            "axes.edgecolor": "#aebbc2",
            "svg.fonttype": "none",
        }
    )
    fig = plt.figure(figsize=(14, 9), facecolor="white")
    grid = fig.add_gridspec(
        2,
        2,
        height_ratios=[1.3, 1],
        left=0.075,
        right=0.975,
        top=0.83,
        bottom=0.15,
        hspace=0.52,
        wspace=0.24,
    )
    ax = fig.add_subplot(grid[0, :])
    ax.scatter(
        points[:, 2],
        points[:, 0],
        s=0.12,
        color="#6e8391",
        alpha=0.13,
        rasterized=True,
        label="Selected centers (projection)",
    )
    ax.plot(route[:, 1], route[:, 0], "--", lw=1, color="#a1aab0", label="Route samples")
    ax.plot(
        previous[:, 0], previous[:, 1], lw=1.4, color="#b3a0bc", label="Earlier path from reset"
    )
    ax.plot(
        states[: start + 1, 0],
        states[: start + 1, 1],
        lw=3,
        color="#a47738",
        label="Preserved history",
    )
    ax.plot(
        states[start:, 0], states[start:, 1], lw=2.6, color="#14678a", label="Admitted partial path"
    )
    ax.scatter(*states[start, :2], s=45, color="#a47738", zorder=6)
    ax.annotate(
        "First fire: 6.25 s",
        states[start, :2],
        xytext=(-45, 22),
        textcoords="offset points",
        fontsize=9,
        arrowprops=dict(arrowstyle="-", color="#a47738"),
    )
    for x, y, _, width, length, _, yaw in geometry["obstacles"]:
        corners = [
            (
                x + u * math.cos(yaw) - v * math.sin(yaw),
                -(y + u * math.sin(yaw) + v * math.cos(yaw)),
            )
            for u, v in [
                (length / 2, width / 2),
                (length / 2, -width / 2),
                (-length / 2, -width / 2),
                (-length / 2, width / 2),
            ]
        ]
        ax.add_patch(Polygon(corners, facecolor="#cc7055", edgecolor="#aa4c35", alpha=0.8))
    ax.annotate(
        "Source actor",
        (30, -1.05),
        xytext=(18, -24),
        textcoords="offset points",
        fontsize=8,
        color="#aa4c35",
    )
    ax.set(
        xlim=(-2, 95),
        ylim=(-19, 10),
        xlabel="Forward coordinate (m)",
        ylabel="Lateral coordinate (m)",
    )
    ax.set_aspect("equal", adjustable="box")
    ax.set_title("A  |  The first 25 controls remain fixed", loc="left", fontweight="bold", pad=15)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=5,
        frameon=False,
        fontsize=8,
        markerscale=5,
    )
    ax.grid(alpha=0.13)
    ax = fig.add_subplot(grid[1, 0])
    for rows, color, label in [
        (prefix, "#a47738", "Preserved history"),
        (suffix, "#14678a", "Admitted partial path"),
    ]:
        ax.plot(
            [r["frame"] / 4 for r in rows],
            [r["route"]["rc"] for r in rows],
            lw=2.4,
            color=color,
            label=label,
        )
    for label, comparison in geometry["comparators"].items():
        t, threshold = comparison["hazard_time"], comparison["rc"] - 0.05
        ax.axvline(t, color="#aebbc2", ls=":", lw=1)
        ax.scatter(t, threshold, marker="_", s=160, color="#ad5845", zorder=6)
        ax.annotate(f"{t:g} s", (t, 1.04), fontsize=8, ha="center")
    ax.axvline(start / 4, color="#a47738", ls="--", lw=1)
    ax.axhline(1, color="#aebbc2", ls="--", lw=0.9)
    ax.set(
        xlim=(0, max(10, admission["final_absolute_time"] + 0.5)),
        ylim=(0, 1.13),
        xlabel="Absolute modeled time (s)",
        ylabel="Source route fraction",
    )
    ax.set_title(
        "B  |  Original deadlines, without resetting the clock",
        loc="left",
        fontweight="bold",
        pad=13,
    )
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    ax.grid(alpha=0.13)
    ax = fig.add_subplot(grid[1, 1])
    ax.scatter(
        [r["frame"] / 4 for r in joined],
        [r["background"]["count"] for r in joined],
        s=16,
        color="#14678a",
    )
    ax.axhline(100, color="#ad5845", ls="--", lw=1)
    ax.text(
        0.5,
        104,
        "Collision threshold: strictly more than 100 centers",
        fontsize=8.6,
        color="#ad5845",
    )
    ax.text(
        0.5,
        50,
        f"{admission['verified_states']} joined states independently replayed\n{admission['point_state_classifications']:,} point-state checks\n52 historical states separately qualified",
        fontsize=12,
        linespacing=1.7,
    )
    ax.set(
        xlim=(0, max(10, admission["final_absolute_time"] + 0.5)),
        ylim=(-8, 116),
        xlabel="Absolute modeled time (s)",
        ylabel="Selected centers inside box",
    )
    ax.set_title("C  |  Full scalar mask agreement", loc="left", fontweight="bold", pad=13)
    ax.grid(alpha=0.13)
    title = (
        "A continuation exists after the retained first fire"
        if admission["status"] == "supported"
        else "The bounded search misses from the retained first fire"
    )
    fig.text(0.075, 0.945, title, fontsize=23, fontweight="bold")
    fig.text(
        0.075,
        0.9,
        f"Iter164 · exact grouping / width 24 · {admission['attempts']:,} attempts · {admission['suffix_actions']} selected suffix actions",
        fontsize=12,
        color="#526773",
    )
    fig.text(
        0.075,
        0.066,
        "One exposed source model. The earlier reset path is context, not a matched method comparison. Projected centers do not certify road boundaries.",
        fontsize=9.1,
        color="#526773",
    )
    fig.text(
        0.075,
        0.036,
        "Offline privileged search. Native continuation, online availability, continuous background clearance, information benefit and transfer remain unknown.",
        fontsize=9.1,
        color="#526773",
    )
    for ext in ["png", "svg", "pdf"]:
        fig.savefig(
            BASE / "proof" / ("monitor_time_continuation." + ext), dpi=180, facecolor="white"
        )
    svg = BASE / "proof/monitor_time_continuation.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    plt.close(fig)


if __name__ == "__main__":
    main()
