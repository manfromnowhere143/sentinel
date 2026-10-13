"""Descriptive figure from independently admitted native records; no new estimator."""

import json
from pathlib import Path
import math
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from experiments.iter163_native_path_replay.background_check import population

ROOT = Path.cwd()
BASE = ROOT / "experiments/iter163_native_path_replay"


def read(path):
    return json.loads(path.read_text())


def events(path):
    return [json.loads(s) for s in path.read_text().splitlines()]


def main():
    admission = read(BASE / "proof/admissions/pair_000.json")
    assert admission["status"] == "supported" and admission["scientific_status"] == "supported"
    cases = admission["cases"]
    traces = [
        events(BASE / "proof/study_raw/pair_000/runs" / c["episode"] / "trace/events.jsonl")
        for c in cases
    ]
    steps = [[r for r in rows if r["event"] == "step"] for rows in traces]
    assert [r["after"] for r in steps[0]] == [r["after"] for r in steps[1]]
    head = next(r for r in traces[0] if r["event"] == "header")
    reset = next(r for r in traces[0] if r["event"] == "reset")
    states = np.array([reset["state"]] + [r["after"] for r in steps[0]])
    route = np.array(head["route"])
    _, points, _ = population(ROOT)
    points = np.array(points)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.labelcolor": "#263945",
            "text.color": "#162d3b",
            "axes.edgecolor": "#aebbc2",
            "xtick.color": "#526773",
            "ytick.color": "#526773",
            "svg.fonttype": "none",
        }
    )
    fig = plt.figure(figsize=(14, 9), facecolor="white")
    gs = fig.add_gridspec(
        2,
        2,
        height_ratios=[1.3, 1],
        left=0.075,
        right=0.975,
        top=0.84,
        bottom=0.14,
        hspace=0.55,
        wspace=0.24,
    )
    ax = fig.add_subplot(gs[0, :])
    ax.scatter(
        points[:, 2],
        points[:, 0],
        s=0.12,
        color="#6e8391",
        alpha=0.13,
        rasterized=True,
        label="Selected background centers (projection)",
    )
    ax.plot(
        route[:, 1], route[:, 0], ls="--", lw=1.2, color="#8a9aa4", label="Source route samples"
    )
    ax.plot(
        states[:, 0],
        states[:, 1],
        lw=2.6,
        color="#14678a",
        label="Native path: both replicas agree",
    )
    ax.scatter(
        states[::8, 0],
        states[::8, 1],
        s=21,
        color="#2ba79b",
        edgecolors="white",
        linewidths=0.6,
        zorder=5,
    )
    for box in reset["info"]["obj_boxes"]:
        x, y, _, width, length, _, yaw = box
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
        ax.add_patch(
            Polygon(
                corners,
                facecolor="#cc7055",
                alpha=0.85,
                edgecolor="#aa4c35",
                label="Native foreground actor",
            )
        )
    ax.set_xlim(-2, 95)
    ax.set_ylim(-19, 10)
    ax.set_aspect("equal", adjustable="box")
    ax.scatter(states[-1, 0], states[-1, 1], s=30, color="#14678a", zorder=5)
    ax.annotate(
        "Native stop",
        states[-1, :2],
        xytext=(-8, 10),
        textcoords="offset points",
        ha="right",
        fontsize=8.5,
    )
    ax.set_xlabel("Forward coordinate (m)")
    ax.set_ylabel("Lateral coordinate (m)")
    ax.set_title(
        "A  |  Executed motion in the retained scene", loc="left", fontweight="bold", pad=13
    )
    ax.grid(alpha=0.14)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, 1.02),
        ncol=4,
        frameon=False,
        fontsize=8.2,
        markerscale=6,
    )
    ax = fig.add_subplot(gs[1, 0])
    t = [r["time"] for r in steps[0]]
    rc = [r["rc"] for r in steps[0]]
    ax.plot(t, rc, color="#14678a", lw=2.3, label="Native fixed path (two replicas)")
    historic = [
        (
            "Nominal history",
            "#b78e4d",
            "experiments/iter151_recovery_canary/proof/study_raw/pair_000/runs/canary151_000__scene-0013-medium-00__nominal__1/trace/events.jsonl",
        ),
        (
            "Monitor history",
            "#a66d80",
            "experiments/iter152_recovery_continuation/proof/study_raw/pair_000/runs/continuation152_000__scene-0013-medium-00__monitor__1/trace/events.jsonl",
        ),
    ]
    for label, color, path in historic:
        rows = [r for r in events(ROOT / path) if r["event"] == "outcome_observation"]
        ax.plot(
            [r["time"] for r in rows], [r["rc"] for r in rows], color=color, lw=1.6, label=label
        )
        ax.scatter(rows[-1]["time"], rows[-1]["rc"], color=color, s=23, zorder=4)
    ax.axhline(1, ls="--", lw=0.9, color="#526773")
    for stamp in [7.75, 9]:
        ax.axvline(stamp, ls=":", color="#aebbc2", lw=0.9)
    ax.set(
        xlim=(0, 17), ylim=(0, 1.12), xlabel="Simulation time (s)", ylabel="Source route fraction"
    )
    ax.set_title("B  |  Completion and original checkpoints", loc="left", fontweight="bold", pad=13)
    ax.legend(loc="upper left", frameon=False, fontsize=8.6)
    ax.grid(alpha=0.14)
    ax = fig.add_subplot(gs[1, 1])
    frames = cases[0]["background"]["frames"]
    ax.scatter(
        [r["time"] for r in frames],
        [r["native_count"] for r in frames],
        s=16,
        color="#14678a",
        label="Native count; scalar masks agree",
    )
    ax.axhline(100, ls="--", lw=1.1, color="#ba6953")
    ax.text(
        0.4,
        104,
        "Collision threshold: strictly more than 100 centers",
        fontsize=8.5,
        color="#a15443",
    )
    total = sum(c["background"]["point_state_classifications"] for c in cases)
    masks = sum(c["background"]["executed_queries"] for c in cases)
    ax.text(
        0.5,
        55,
        f"{masks} full masks independently replayed\n{total:,} point-state classifications\nZero mask disagreements",
        fontsize=12,
        linespacing=1.7,
    )
    ax.set(
        xlim=(0, 17),
        ylim=(-8, 116),
        xlabel="Simulation time (s)",
        ylabel="Centers inside native box",
    )
    ax.set_title("C  |  Background checks at executed steps", loc="left", fontweight="bold", pad=13)
    ax.grid(alpha=0.14)
    fig.text(
        0.075, 0.945, "An admitted path completes the native scene", fontsize=24, fontweight="bold"
    )
    fig.text(
        0.075,
        0.9,
        "Two fresh replicas · 66 actions each · fixed controls from reset · inference bypassed",
        fontsize=12,
        color="#526773",
    )
    fig.text(
        0.075,
        0.064,
        "One exposed scene. Historical policies are context, not a matched causal comparison. Projected centers do not certify road boundaries.",
        fontsize=9.3,
        color="#526773",
    )
    fig.text(
        0.075,
        0.036,
        "Native stopping uses the sampled-route rule. Monitor-time recovery, continuous background clearance and information benefit remain unproved.",
        fontsize=9.3,
        color="#526773",
    )
    for extension in ["png", "svg", "pdf"]:
        fig.savefig(BASE / "proof" / ("native_replay." + extension), dpi=180, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
