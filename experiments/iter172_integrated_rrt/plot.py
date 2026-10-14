"""Render retained qualification counts; this script performs no search."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    base = Path(__file__).resolve().parent
    admission = json.loads((base / "proof/admission.json").read_text())
    diagnostic = json.loads((base / "proof/diagnostics.json").read_text())
    rows = admission["records"]
    labels = [r["case"].replace("_", " ") for r in rows]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4), gridspec_kw={"width_ratios": [1.1, 1]})
    fig.patch.set_facecolor("#fafaf7")
    for ax in axes:
        ax.set_facecolor("#fafaf7")
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_yticks(range(4), labels)
        ax.invert_yaxis()
    axes[0].barh(range(4), [r["attempts"] for r in rows], color="#326784", height=.5)
    axes[0].axvline(18000, color="#303b42", linestyle="--", linewidth=1)
    for i, row in enumerate(rows):
        axes[0].text(row["attempts"] - 350, i, f'{row["attempts"]:,}',
                     ha="right", va="center", color="white", weight="bold")
    axes[0].set(xlim=(0, 19000), xlabel="Attempted transitions · cap 18,000 per case",
                title="Every case exhausts its allocatable budget")
    axes[0].set_xticks([0, 6000, 12000, 18000], ["0", "6,000", "12,000", "18,000"])
    maximum = [r["maximum_accepted_frame"] * .25 for r in diagnostic["records"]]
    returned = [r["selected_actions"] * .25 for r in rows]
    axes[1].barh(range(4), maximum, color="#c6d2d7", height=.5,
                 label="Furthest accepted connection")
    axes[1].barh(range(4), returned, color="#ac5e38", height=.22,
                 label="Returned partial path")
    axes[1].axvline(4, color="#303b42", linestyle="--", linewidth=1)
    axes[1].set(xlim=(0, 4.4), xlabel="Absolute model time, seconds · first checkpoint at 4 s",
                title="No accepted connection reaches checkpoint one")
    axes[1].legend(loc="upper center", bbox_to_anchor=(.5, -.28), fontsize=9, frameon=False)
    fig.suptitle("Integrated RRT: 0 of 4 original cases complete", fontsize=18, x=.51, y=.98)
    fig.text(.04, .035, "Iter172 · One frozen seed per case. Partial paths are not completions. "
             "No source recovery or generalization claim.", fontsize=10, color="#465057")
    fig.subplots_adjust(left=.115, right=.97, bottom=.29, top=.79, wspace=.42)
    fig.savefig(base / "proof/qualification.png", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    main()
