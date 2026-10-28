"""Render every retained node from admitted data; no probe or planner execution."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from .common import BASE, encode, read, sha


def main(root):
    plt.rcParams.update(
        {"font.family": "DejaVu Sans", "font.size": 10, "svg.hashsalt": "sentinel190"}
    )
    data = json.loads(read(root, BASE / "proof/descriptive.json"))
    rows = data["records"]
    fig, ax = plt.subplots(figsize=(12, 10.6))
    fig.patch.set_facecolor("#ffffff")
    ax.set(xlim=(0, 12), ylim=(len(rows) + 1, -2.5))
    ax.axis("off")
    fig.suptitle(
        "Late states: full continuation and original expansion",
        x=0.055,
        ha="left",
        y=0.97,
        fontsize=17,
        fontweight="bold",
        color="#17324d",
    )
    fig.text(
        0.055,
        0.925,
        "All 22 retained records · 21 exact roots · original remaining budgets preserved",
        fontsize=11,
        color="#4b5d6d",
    )
    positions = [0.05, 3.05, 5.95, 8.95, 10.8]
    for x, label in zip(
        positions,
        [
            "Node · frame",
            "Stop / wait / route",
            "Beam then route",
            "Original requests",
            "Attempts left",
        ],
    ):
        ax.text(x, -1.1, label, fontsize=10, fontweight="bold", color="#17324d")
    previous = None
    for i, row in enumerate(rows):
        name, node = row["id"].split(":")
        if name != previous:
            ax.axhline(i - 0.48, color="#8293a6", lw=0.8)
        previous = name
        duplicate = " *" if row["id"] != row["representative"] else ""
        ax.text(
            0.05,
            i,
            f"{name.replace('_', ' ')} {node}{duplicate} · {row['frame']}",
            va="center",
            fontsize=9,
        )
        for j, arm in enumerate(row["arms"]):
            if arm["censored"]:
                color, label = "#f2d4d0", "censored"
            elif arm["budgeted_completion"]:
                color, label = "#17324d", f"complete @ {arm['completed_frame']}"
            elif arm["budgeted_checkpoint"]:
                color, label = "#f1ddaa", "checkpoint only"
            else:
                color, label = "#e8edf2", "bounded miss"
            x = 3.0 + 2.9 * j
            ax.add_patch(Rectangle((x, i - 0.36), 2.65, 0.72, facecolor=color, edgecolor="white"))
            ax.text(
                x + 1.325,
                i,
                f"{label} · {arm['attempts']:,}",
                ha="center",
                va="center",
                fontsize=9,
                color="white" if color == "#17324d" else "#23354a",
            )
        ax.text(9.55, i, str(row["original_requests"]), ha="center", va="center")
        ax.text(11.35, i, f"{row['remaining_attempts']:,}", ha="center", va="center")
    fig.text(
        0.055,
        0.045,
        "Cells show outcome and all attempted transitions. * Left node 85 shares node 76's exact state and clock; probe work is deduplicated.\nFinite misses do not prove infeasibility. Conditional paths add no integrated credit: the planner remains at 3/4.",
        fontsize=9,
        color="#4b5d6d",
        linespacing=1.5,
    )
    fig.subplots_adjust(left=0.05, right=0.98, bottom=0.08, top=0.91)
    folder = root / BASE / "proof"
    fig.savefig(folder / "late-continuations.png", dpi=170)
    fig.savefig(folder / "late-continuations.svg", metadata={"Date": None})
    plt.close(fig)
    p = folder / "late-continuations.svg"
    p.write_text("\n".join(line.rstrip() for line in p.read_text().splitlines()) + "\n")
    (folder / "figure-data.json").write_bytes(
        encode(
            dict(
                descriptive_sha256=sha(read(root, BASE / "proof/descriptive.json")),
                admission_sha256=data["admission_sha256"],
                records=rows,
            )
        )
    )


if __name__ == "__main__":
    main(Path.cwd())
