"""Paired admitted counts, with misses and tree/path differences visible."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    base = Path(__file__).resolve().parent
    a = json.loads((base / "proof/admission.json").read_text())
    rows = a["records"]
    pairs = a["comparison"]["pairs"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
    fig.patch.set_facecolor("#fafaf7")
    for ax in axes:
        ax.set_facecolor("#fafaf7")
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_yticks(range(4), [r["case"].replace("_", " ") for r in rows])
        ax.invert_yaxis()
    for i, (row, pair) in enumerate(zip(rows, pairs)):
        axes[0].barh(i-.16, pair["reference_attempts"], height=.28, color="#b9c8d0")
        axes[0].barh(i+.16, row["attempts"], height=.28, color="#326784")
        axes[0].text(row["attempts"]+250, i+.16, f'{row["attempts"]:,}', va="center", fontsize=9)
        axes[1].barh(i-.16, pair["reference_frame"]*.25, height=.28, color="#b9c8d0")
        axes[1].barh(i+.16, row["returned_frame"]*.25, height=.28,
                     color="#277461" if row["complete"] else "#ac5e38")
        axes[1].plot(row["max_tree_frame"]*.25, i+.16, marker="|", color="#162c36", markersize=15)
    axes[0].axvline(18000, color="#53616a", linestyle="--", linewidth=1)
    axes[0].set(xlim=(0, 21400), xlabel="Attempted transitions · 18,000 cap per case",
                title="Same ceilings; more work consumed")
    axes[0].set_xticks([0, 6000, 12000, 18000], ["0", "6,000", "12,000", "18,000"])
    for checkpoint in (4, 8):
        axes[1].axvline(checkpoint, color="#53616a", linestyle="--", linewidth=1)
    axes[1].set(xlim=(0, 9), xlabel="Returned model time · checkpoint lines at 4 and 8 s",
                title="Two completions; two bounded misses")
    fig.suptitle("Checkpoint preference: 2/4 complete, down from 3/4", fontsize=18, y=.97)
    fig.text(.06, .13, "Upper pale bar: retained Iter178. Lower bar: checkpoint candidate. "
             "Green = complete; rust = miss. Tick = furthest accepted tree endpoint.", fontsize=10)
    fig.text(.06, .055, "Iter181 · Zero gains, one lost success. Source comparison remains closed. "
             "No latency or generalization claim.", fontsize=10, color="#465057")
    fig.subplots_adjust(left=.12, right=.97, bottom=.28, top=.78, wspace=.42)
    fig.savefig(base / "proof/qualification.png", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    main()
