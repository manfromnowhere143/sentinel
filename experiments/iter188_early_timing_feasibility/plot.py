"""Post-admission descriptive figure; no new search, bound or scientific decision."""

import hashlib
import json
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


def plot(root):
    base = root / "experiments/iter188_early_timing_feasibility"
    raw = (base / "proof/admission.json").read_bytes()
    admission = json.loads(raw)
    colors = {"excluded": "#b64a36", "retained_completion": "#14796c", "unknown": "#8392a5"}
    markers = {"excluded": "X", "retained_completion": "o", "unknown": "."}
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 7.7), sharex=True, constrained_layout=True)
    data = []
    for ax, summary in zip(axes.flat, admission["records"]):
        rows = sorted(
            (e for e in admission["endpoints"] if e["case"] == summary["case"]),
            key=lambda e: (e["frame"], e["node"]),
        )
        offsets = Counter()
        for row in rows:
            offset = offsets[row["frame"]]
            offsets[row["frame"]] += 1
            category = row["classification"]
            ax.scatter(
                row["frame"], offset + 1, color=colors[category], marker=markers[category],
                s=85 if category == "excluded" else (30 if category == "retained_completion" else 22),
                zorder=4 if category == "excluded" else 3,
            )
            data.append(dict(case=row["case"], node=row["node"], token=row["token"], frame=row["frame"],
                             stack=offset + 1, classification=category))
        for frame, color in [(24, "#8b98a7"), (32, "#40566f")]:
            ax.axvline(frame, color=color, linestyle="--", linewidth=1, zorder=1)
        ax.set_title(summary["case"].replace("_", " ").title(), loc="left", fontsize=13, weight="bold", pad=24)
        ax.text(0, 1.025,
                f'{summary["excluded"]} excluded · {summary["retained_completion"]} known suffix · {summary["unknown"]} unknown',
                transform=ax.transAxes, fontsize=10, color="#40566f")
        ax.set(xlim=(-1, 40), ylim=(0.4, max(offsets.values()) + 1.8),
               xlabel="Absolute endpoint frame (4 frames = 1 simulated second)",
               ylabel="Endpoint records at this frame", xticks=range(0, 41, 4))
        ax.grid(axis="y", alpha=0.13)
        ax.spines[["top", "right"]].set_visible(False)
        if summary["case"] == "bend_left":
            ax.annotate("Early exclusions\nframes 19 and 21", xy=(20, 1), xytext=(5, 8),
                        color=colors["excluded"], fontsize=10,
                        arrowprops=dict(arrowstyle="->", color=colors["excluded"]))
    handles = [Line2D([], [], marker=markers[c], linestyle="", color=colors[c], markersize=8, label=label)
               for c, label in [("excluded", "Timing exclusion"), ("retained_completion", "Known completion suffix"),
                                ("unknown", "Unknown")]]
    handles.extend([Line2D([], [], color="#8b98a7", linestyle="--", label="Old window starts: 24"),
                    Line2D([], [], color="#40566f", linestyle="--", label="Final checkpoint: 32")])
    fig.legend(handles=handles, loc="outside lower center", ncol=3, frameon=False, fontsize=10)
    fig.suptitle("Two early timing traps; 219 endpoints remain unresolved\n"
                 "All 255 native nodes retained · 300 successful transitions remain unexcluded", fontsize=15)
    fig.savefig(base / "proof/timing-feasibility.png", dpi=175)
    svg = base / "proof/timing-feasibility.svg"
    fig.savefig(svg)
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    plt.close(fig)
    (base / "proof/figure-data.json").write_text(json.dumps(
        dict(admission_sha256=hashlib.sha256(raw).hexdigest(), records=data,
             note="Stack positions separate records; duplicate states are not independent observations."),
        indent=2) + "\n")


if __name__ == "__main__":
    plot(Path.cwd())
