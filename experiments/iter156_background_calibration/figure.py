"""Plot admitted counts and exploratory query cost without changing evidence."""

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BASE = Path(__file__).resolve().parent
raw_bytes = (BASE / "proof/raw/predictions.json").read_bytes()
admission_bytes = (BASE / "proof/admission.json").read_bytes()
raw, admission = json.loads(raw_bytes), json.loads(admission_bytes)
assert admission["status"] == "supported"
counts = {tuple(r["state"]): r["count"] for r in raw["states"]}
traces = list(dict.fromkeys(r["trace"] for r in raw["rows"]))[::2]
labels = ["Nominal", "Monitor", "Brake from 0 s", "Brake from 2.5 s", "Selected maneuver"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "axes.spines.top": False, "axes.spines.right": False})
fig = plt.figure(figsize=(12, 8), layout="constrained")
grid = fig.add_gridspec(5, 2, width_ratios=[1.35, 1], wspace=0.12)
for index, (trace, label) in enumerate(zip(traces, labels)):
    ax = fig.add_subplot(grid[index, 0])
    rows = [r for r in raw["rows"] if r["trace"] == trace]
    times = [r["time"] for r in rows]
    values = [counts[tuple(r["state"])] for r in rows]
    ax.plot(times, values, "o-", color="#176985", markersize=2.5, linewidth=1.4)
    ax.axhline(100, color="#ad6a20", linestyle="--", linewidth=1)
    if index < 4:
        ax.plot(times[-1], values[-1], marker="D", markersize=6, markerfacecolor="white",
                markeredgecolor="#343c46")
    else:
        ax.annotate("273 centers / native collision", (times[-1], values[-1]),
                    xytext=(3.7, 245), fontsize=9, color="#963d32")
    ax.set(xlim=(0, 9.3), ylim=(-24, 305), yticks=[0, 100, 273], ylabel=label)
    ax.tick_params(axis="both", labelsize=8)
    ax.grid(axis="y", alpha=0.12)
    if index == 0:
        ax.set_title("Complete-population model counts", loc="left", fontsize=12)
    if index < 4:
        ax.tick_params(labelbottom=False)
    else:
        ax.set_xlabel("Recorded simulation time (s)")
ax = fig.add_subplot(grid[:3, 1])
x = np.arange(115)
ax.scatter(x, [r["scalar_seconds"] * 1000 for r in admission["states"]],
           s=11, color="#77679f", label="Separate scalar checker")
ax.scatter(x, [r["accelerated_seconds"] * 1000 for r in admission["states"]],
           s=11, color="#176985", label="Full-population vector query")
ax.set(yscale="log", ylim=(8, 4500), xlabel="Fixed unique-state index",
       ylabel="Local query time (ms)")
ax.set_title("Exploratory cost · same retained points", loc="left", fontsize=12)
ax.set_yticks([10, 100, 1000], ["10", "100", "1,000"])
ax.grid(axis="y", alpha=0.15)
ax.legend(loc="center right", frameon=False, fontsize=9)
ax = fig.add_subplot(grid[3:, 1]); ax.axis("off")
ax.text(0, 0.96, "115 / 115 full masks agree", fontsize=15, weight="bold", va="top")
ax.text(0, 0.75,
        "276,519 source centers per state\n"
        "26 direct background labels + 266 negative implications\n"
        "8 collision-positive labels remain unattributed\n\n"
        "◇  Background component unknown in the older trace\n"
        "– –  Native collision requires strictly more than 100\n\n"
        "Each left trace represents two identical replicas.\n"
        "One exposed scene; no new drive or useful recovery.\n"
        "Native full masks remain the two Iter155 poses.\n"
        "Timing is local and exploratory; no real-time claim.",
        fontsize=9.2, va="top", linespacing=1.55)
fig.suptitle("Sentinel · Iter156 background calibration", x=0.06, ha="left", fontsize=17)
for suffix in ["svg", "png"]:
    fig.savefig(BASE / "proof" / ("calibration." + suffix), dpi=180,
                metadata={"Creator": "Sentinel retained-evidence plot"})
svg = BASE / "proof/calibration.svg"
svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
identity = {"predictions_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "admission_sha256": hashlib.sha256(admission_bytes).hexdigest(),
            "matplotlib": matplotlib.__version__, "display_replica": 1,
            "scope": "Derived display; every admitted state remains in the linked records."}
(BASE / "proof/figure_identity.json").write_text(json.dumps(identity, indent=2) + "\n")
