"""Admitted late-frontier timing, with constraints and continuations separated."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    base = Path(__file__).resolve().parent
    evidence = json.loads((base / "proof/admission.json").read_text())
    rows = evidence["records"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor("#fafaf7")
    ax.set_facecolor("#fafaf7")
    ax.spines[["top", "right", "left"]].set_visible(False)
    for i, row in enumerate(rows):
        start, end = row["start_frame"] / 4, row["returned_frame"] / 4
        witness = row["checkpoint_continuation"]
        color = "#277461" if witness else "#ae5836"
        ax.plot([5.7, start], [i, i], color="#c4cbd0", linewidth=4)
        ax.plot(start, i, "o", color="#405564", markersize=7)
        if end > start:
            ax.plot([start, end], [i, i], color=color, linewidth=4)
        ax.plot(end, i, "o" if witness else "x", color=color, markersize=9, markeredgewidth=2)
        if witness:
            text = "Verified checkpoint continuation"
            if row["source_model_complete"]:
                text += " + completion"
        elif row["premature_completion_excluded"]:
            text = "Every next position completes too early"
        elif row["progress_excluded"]:
            text = "Insufficient reachable checkpoint progress"
        else:
            text = "Censored" if row["censored"] else "Unresolved finite miss"
        ax.text(8.15, i, text, va="center", fontsize=10, color=color)
    ax.axvline(8, color="#6b747b", linestyle="--", linewidth=1)
    ax.set_yticks(
        range(len(rows)), [r["case"].replace("bend_", "") + f" · call {r['call']}" for r in rows]
    )
    ax.set_xticks([6, 6.5, 7, 7.5, 8])
    ax.set(xlim=(5.7, 11.45), ylim=(len(rows) - 0.5, -0.6), xlabel="Model time (seconds)")
    ax.tick_params(axis="y", length=0)
    count = evidence["checkpoint_witnesses"]
    excluded = sum(r["progress_excluded"] or r["premature_completion_excluded"] for r in rows)
    fig.suptitle(
        f"Late frontier: {count} verified continuations, {excluded} timing exclusions",
        fontsize=18,
        y=0.96,
    )
    fig.text(
        0.12,
        0.845,
        "Dark circle: retained root. Green: verified diagnostic suffix. "
        "Rust cross: constrained root. Dashed line: checkpoint.",
        fontsize=10,
    )
    fig.text(
        0.12,
        0.10,
        "Iter182 · All seven endpoints audited; every queried mask independently replayed. "
        "Bounds did not prune the probes.",
        fontsize=10,
    )
    fig.text(
        0.12,
        0.055,
        "Declared source numerical model only. Integrated qualification remains 3/4; "
        "source comparison closed.",
        fontsize=10,
        color="#465057",
    )
    fig.subplots_adjust(left=0.12, right=0.98, bottom=0.23, top=0.80)
    fig.savefig(base / "proof/timing.png", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    main()
