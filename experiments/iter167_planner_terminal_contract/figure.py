"""Render admitted experiment summaries; no new trajectory or collision queries."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def render(root):
    first = json.loads(
        (root / "experiments/iter165_discarded_braking/proof/admission.json").read_text()
    )
    second = json.loads(
        (root / "experiments/iter167_planner_terminal_contract/proof/admission.json").read_text()
    )
    assert first["phase"] == second["phase"] == "closed"
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    fig, (left, right) = plt.subplots(
        1, 2, figsize=(14, 5.1), gridspec_kw={"width_ratios": [1.15, 1]}
    )
    fig.patch.set_facecolor("#f7f8f6")
    for ax in [left, right]:
        ax.set_facecolor("#f7f8f6")
        ax.spines["left"].set_color("#aeb9bc")
        ax.spines["bottom"].set_color("#aeb9bc")
    colors = {"discarded": "#b76643", "retained": "#477783"}
    for cohort, y in [("discarded", 1), ("retained", 0)]:
        rows = [r for r in first["records"] if r["cohort"] == cohort]
        assert len(rows) in [24, 25] and not any(r["complete"] for r in rows)
        points = [r["completed_depth"] / 4 for r in rows]
        offsets = [y + (i - (len(rows) - 1) / 2) * 0.017 for i in range(len(rows))]
        left.scatter(
            points, offsets, s=35, c=colors[cohort], alpha=0.8, edgecolors="white", linewidths=0.6
        )
    left.set_yticks([0, 1], ["Retained roots · 24", "Discarded braking roots · 25"])
    left.set_xlabel("Absolute time at first empty beam (seconds)")
    left.set_xlim(7.25, 10.6)
    left.set_ylim(-0.5, 1.6)
    left.axvline(7.75, color="#a5b1b3", ls="--", lw=0.8)
    left.axvline(9, color="#a5b1b3", ls="--", lw=0.8)
    left.text(7.75, 1.45, "checkpoint 1", rotation=0, ha="center", fontsize=8, color="#657375")
    left.text(9, 1.45, "checkpoint 2", rotation=0, ha="center", fontsize=8, color="#657375")
    left.set_title("49 continuations. No complete path.", loc="left", weight="bold", pad=20)
    left.grid(axis="x", alpha=0.12)
    names = [r["case"].replace("_", " ").title() for r in second["records"]]
    values = [r["final_progress"] for r in second["records"]]
    right.barh(range(4), values, color="#477783", height=0.45)
    right.set_yticks(range(4), names)
    right.invert_yaxis()
    right.axvline(1, color="#b76643", lw=1.2, ls="--")
    right.set_xlim(0, 1.15)
    right.set_xlabel("Progress of independently checked partial path")
    for i, value in enumerate(values):
        right.text(value + 0.018, i, f"{value:.3f}", va="center", fontsize=9)
    right.set_title("Independent RRT: 0 of 4 qualify.", loc="left", weight="bold", pad=20)
    right.grid(axis="x", alpha=0.12)
    fig.suptitle(
        "Recovery remains unproved under the original constraints",
        x=0.04,
        y=0.985,
        ha="left",
        fontsize=16,
        weight="bold",
        color="#1b343d",
    )
    fig.text(
        0.04,
        0.065,
        "Left: 60,000-attempt cap per root; every search ends with an empty beam. Points show search-log stopping, not physical inevitability.",
        fontsize=9,
        color="#43595f",
    )
    fig.text(
        0.04,
        0.025,
        "Right: 18,000 attempts per case; all four caps reached. Each selected path observes only one of two checkpoints. Iter166’s invalid early completions remain retained.",
        fontsize=9,
        color="#43595f",
    )
    fig.subplots_adjust(left=0.17, right=0.96, top=0.79, bottom=0.24, wspace=0.55)
    output = (
        root
        / "experiments/iter167_planner_terminal_contract/proof/continuation_and_qualification.png"
    )
    fig.savefig(output, dpi=170, facecolor=fig.get_facecolor())
    plt.close(fig)
    return output


if __name__ == "__main__":
    print(render(Path.cwd()))
