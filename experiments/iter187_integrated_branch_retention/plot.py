"""Admitted path/progress comparison on exposed constructed cases."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .common import BASE, read, write


def plot(root):
    admission = json.loads(read(root, BASE / "proof/admission.json"))
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), constrained_layout=True)
    data = []
    for ax, record in zip(axes.flat, admission["records"]):
        name = record["case"]
        current = json.loads(read(root, BASE / f"proof/search_raw/{name}/selected/trace.json"))
        prior = json.loads(
            read(
                root,
                f"experiments/iter183_timing_eligibility/proof/search_raw/{name}/selected/trace.json",
            )
        )
        color = "#126e63" if record["complete"] else "#ad433b"
        for trace, label, col, style in (
            (prior, "Iter183", "#7b8493", "--"),
            (current, "Iter187", color, "-"),
        ):
            ax.plot(
                [r["frame"] / 4 for r in trace],
                [r["route"]["rc"] for r in trace],
                color=col,
                linestyle=style,
                linewidth=2,
                label=label,
            )
        for second in (4, 8):
            ax.axvline(second, color="#ccd2db", linestyle=":", linewidth=1)
        ax.axhline(1, color="#a5aab3", linewidth=0.8)
        ax.set(
            title=name.replace("_", " ")
            + (" — complete" if record["complete"] else " — bounded miss"),
            xlabel="Simulated time (s)",
            ylabel="Source-defined route completion",
            xlim=(0, 10),
            ylim=(0, 1.08),
        )
        ax.grid(alpha=0.14)
        ax.legend(loc="upper left", frameon=False)
        data.append(
            dict(
                case=name,
                current=[(r["frame"], r["route"]["rc"]) for r in current],
                reference=[(r["frame"], r["route"]["rc"]) for r in prior],
            )
        )
    fig.suptitle("One gained case, one lost case: 3/4 remains 3/4", fontsize=16)
    fig.savefig(root / BASE / "proof/progress-comparison.png", dpi=170)
    svg = root / BASE / "proof/progress-comparison.svg"
    fig.savefig(svg)
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    plt.close(fig)
    write(
        root / BASE / "proof/figure-data.json",
        dict(raw_commit=admission["raw_commit"], records=data),
    )


if __name__ == "__main__":
    plot(Path.cwd())
