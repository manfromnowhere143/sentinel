"""Plot admitted outcomes and attempted work; no scientific acquisition."""

import json
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .common import BASE, read


def main(root):
    current = json.loads(read(root, BASE / "proof/admission.json"))
    older = [
        json.loads(read(root, "experiments/" + name + "/proof/admission.json"))
        for name in ("iter183_timing_eligibility", "iter189_uniform_timing_eligibility")
    ]
    groups = [*older, current]
    labels = ["Left bend", "Right bend", "Left chicane", "Right chicane"]
    plt.rcParams.update(
        {"font.family": "DejaVu Sans", "font.size": 10, "svg.hashsalt": "sentinel192"}
    )
    fig, (left, right) = plt.subplots(
        1, 2, figsize=(12, 4.7), gridspec_kw={"width_ratios": [0.9, 1.4]}
    )
    fig.suptitle(
        "Exact feedback integration: four complete cases",
        x=0.06,
        y=0.97,
        ha="left",
        fontsize=17,
        fontweight="bold",
        color="#17324d",
    )
    for col, group in enumerate(groups):
        for row, record in enumerate(group["records"]):
            left.scatter(
                col, row, s=380, marker="s", color="#17324d" if record["complete"] else "#e4e9ef"
            )
            left.text(
                col,
                row,
                "✓" if record["complete"] else "×",
                color="white" if record["complete"] else "#8a4c42",
                ha="center",
                va="center",
                fontsize=14,
            )
    left.set_xticks(range(3), ["Iter183\n3/4", "Iter189\n3/4", "Iter192\n4/4"])
    left.set_yticks(range(4), labels)
    left.invert_yaxis()
    left.set_xlim(-0.5, 2.5)
    left.set_title("Completion · retained controls", loc="left", pad=19, fontsize=11)
    for index, group in enumerate(groups):
        positions = [i + (index - 1) * 0.25 for i in range(4)]
        right.bar(
            positions,
            [r["attempts"] for r in group["records"]],
            width=0.23,
            color=["#c9d2dc", "#8298ab", "#17324d"][index],
            label=f"Iter{group['iteration']}",
        )
    right.axhline(18000, color="#a76651", linestyle="--", linewidth=1)
    right.text(3.6, 18350, "18,000 cap", ha="right", fontsize=9, color="#81503f")
    right.set_ylim(0, 21000)
    right.set_xticks(range(4), ["Left\nbend", "Right\nbend", "Left\nchicane", "Right\nchicane"])
    right.set_ylabel("Attempted transitions")
    right.set_title("Used work · unchanged ceilings", loc="left", pad=19, fontsize=11)
    right.grid(axis="y", color="#e8edf2")
    right.set_axisbelow(True)
    right.legend(frameon=False, ncol=3, loc="upper right", bbox_to_anchor=(1.03, -0.17))
    for ax in (left, right):
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(length=0)
    fig.text(
        0.06,
        0.035,
        "Four exposed development cases · one fixed seed each · no actual-history or real-time recovery claim",
        color="#4b5d6d",
        fontsize=10,
    )
    fig.subplots_adjust(left=0.105, right=0.98, bottom=0.25, top=0.78, wspace=0.4)
    for extension in ("png", "svg"):
        fig.savefig(
            root / BASE / ("proof/integrated-comparison." + extension),
            dpi=170,
            metadata={"Date": None} if extension == "svg" else None,
        )
    plt.close(fig)
    path = root / BASE / "proof/integrated-comparison.svg"
    path.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()) + "\n")


if __name__ == "__main__":
    main(Path.cwd())
