"""Descriptive figure from admitted case records; no new statistical analysis."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from .common import BASE, encode, read, sha


def render(root):
    sources = {
        183: "iter183_timing_eligibility",
        187: "iter187_integrated_branch_retention",
        189: "iter189_uniform_timing_eligibility",
    }
    data, bindings = {}, {}
    for number, directory in sources.items():
        path = Path("experiments") / directory / "proof/admission.json"
        raw = read(root, path)
        bindings[str(path)] = sha(raw)
        data[number] = json.loads(raw)["records"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "svg.fonttype": "none"})
    fig, axes = plt.subplots(1, 3, figsize=(12.4, 4.6), sharey=True)
    labels = ["Left bend", "Right bend", "Left chicane", "Right chicane"]
    for ax, (number, rows) in zip(axes, data.items()):
        for y, row in enumerate(rows):
            color = "#17324d" if row["complete"] else "#b75a3b"
            ax.barh(y, row["attempts"], height=0.46, color=color)
            ax.text(
                row["attempts"] + 200 if row["attempts"] < 4000 else 200,
                y,
                f"{row['attempts']:,}",
                va="center",
                ha="left",
                color="#17324d" if row["attempts"] < 4000 else "white",
                fontsize=9,
                fontweight="bold",
            )
            ax.text(
                18500,
                y,
                f"f{row['returned_frame']}",
                va="center",
                ha="left",
                color="#45576b",
                fontsize=9,
            )
        ax.set_title(
            f"Iter{number}  ·  3/4 complete", loc="left", fontsize=12, pad=15, weight="bold"
        )
        ax.axvline(18000, color="#8d9cab", linestyle=(0, (3, 3)), linewidth=1)
        ax.set_xlim(0, 21000)
        ax.set_xticks([0, 9000, 18000], ["0", "9,000", "18,000"])
        ax.set_xlabel("Attempted transitions", labelpad=10)
        ax.set_yticks(range(4), labels)
        ax.tick_params(axis="both", length=0, pad=7, colors="#45576b")
        for spine in ax.spines.values():
            spine.set_visible(False)
    axes[0].invert_yaxis()
    fig.suptitle(
        "Uniform timing checks preserve the same three successes",
        x=0.03,
        ha="left",
        y=0.98,
        fontsize=17,
        weight="bold",
        color="#17324d",
    )
    fig.text(
        0.03,
        0.88,
        "Four exposed cases · one fixed seed per case · unchanged 18,000-transition / 120-second ceilings",
        color="#45576b",
        fontsize=10,
    )
    fig.legend(
        handles=[
            Patch(color="#17324d", label="Complete"),
            Patch(color="#b75a3b", label="Bounded miss"),
        ],
        loc="lower left",
        bbox_to_anchor=(0.025, 0.005),
        ncol=2,
        frameon=False,
    )
    fig.text(
        0.98,
        0.045,
        "f = returned frame; required final checkpoint = 32. No superiority inference.",
        ha="right",
        fontsize=9,
        color="#45576b",
    )
    fig.subplots_adjust(left=0.12, right=0.98, top=0.72, bottom=0.23, wspace=0.27)
    for extension in ("png", "svg"):
        fig.savefig(root / BASE / "proof" / ("comparison." + extension), dpi=170, facecolor="white")
    svg = root / BASE / "proof/comparison.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    (root / BASE / "proof/figure-data.json").write_bytes(
        encode(dict(inputs=bindings, records={str(n): r for n, r in data.items()}))
    )
    plt.close(fig)


if __name__ == "__main__":
    render(Path.cwd())
