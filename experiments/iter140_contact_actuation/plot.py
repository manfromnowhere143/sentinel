"""Render retained contact geometry without synthesizing simulator states."""

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.patches import Polygon

from experiments.iter140_contact_actuation.independent import corners
from experiments.iter140_contact_actuation.inputs import ARMS, OLD, load_inputs, strict_json, traces


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--primary", type=Path, required=True)
    p.add_argument("--independent", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    verdict = json.loads(a.independent.read_bytes())
    assert verdict["status"] in ("supported", "inconclusive")
    assert verdict["primary_sha256"] == hashlib.sha256(a.primary.read_bytes()).hexdigest()
    manifest = strict_json(
        (a.root / "experiments/iter140_contact_actuation/INPUTS.json").read_bytes()
    )
    raw = traces(load_inputs(a.root, manifest))
    fig, axes = plt.subplots(2, 4, figsize=(14, 8), layout="constrained")
    for ax, arm in zip(axes.flat, ARMS):
        frames = raw[arm][1:-1]
        terminal = frames[-1]["after"]["timestamp"]
        chosen = [f for f in frames if f["after"]["timestamp"] >= terminal - 2]
        ego = [f["after"]["ego_box"] for f in chosen]
        actor = [f["after"]["obj_boxes"][0] for f in chosen]
        for boxes, color, label, style in [
            (ego, "#1269a8", "Ego", "-"),
            (actor, "#ba3c32", "Actor", "--"),
        ]:
            ax.plot(
                [b[0] for b in boxes],
                [b[1] for b in boxes],
                style,
                color=color,
                marker=".",
                markersize=3,
                label=label,
            )
            ax.add_patch(
                Polygon(
                    corners(boxes[-1]), closed=True, facecolor=color, edgecolor=color, alpha=0.28
                )
            )
            for corner in corners(boxes[-1]):
                ax.update_datalim([corner])
        ax.set_title(arm + f" | contact at {terminal:.1f} s", fontsize=11)
        ax.set_aspect("equal", adjustable="datalim")
        ax.autoscale_view()
        ax.margins(0.15)
        ax.grid(alpha=0.2)
        ax.set_xlabel("World planar x (m)")
        ax.set_ylabel("World planar y (m)")
    axes[0, 0].legend(loc="best", fontsize=9)
    fig.suptitle(
        "Iter140 | Observed paths over the final 2 simulated seconds\nFilled rectangles: terminal foreground collision geometry; dots: recorded steps",
        fontsize=14,
    )
    a.output.mkdir(exist_ok=True)
    for suffix in ("png", "svg"):
        dest = a.output / ("terminal_contacts." + suffix)
        assert not dest.exists()
        fig.savefig(dest, dpi=180)
    plt.close(fig)
    print(
        json.dumps(
            dict(
                status="rendered",
                source=OLD,
                scope="recorded discrete paths and terminal rectangles; no counterfactual trajectory",
            )
        )
    )


if __name__ == "__main__":
    main()
