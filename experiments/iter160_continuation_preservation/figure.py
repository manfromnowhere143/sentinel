"""Presentation of admitted continuations; no extra rollout or inferred outcome."""

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

base = Path(__file__).resolve().parent
admission = json.loads((base / "proof/admission.json").read_text())
cases = json.loads((base.parent / "iter159_route_search_qualification/CASES.json").read_text())
case = next(c for c in cases if c["id"] == "chicane_left")
traces = {}
identities = []
for record in admission["records"]:
    path = base / "proof/raw" / record["name"] / "trace.json"
    traces[record["name"]] = json.loads(path.read_text())["rows"]
    identities.append(
        dict(path=str(path.relative_to(base)), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    )
colors = {"discarded": "#236d7e", "representative": "#ad663d"}
fig = plt.figure(figsize=(14, 6.5))
grid = fig.add_gridspec(
    1, 3, width_ratios=[1.3, 1, 1.35], left=0.055, right=0.97, top=0.77, bottom=0.23, wspace=0.42
)
fig.text(
    0.055,
    0.94,
    "Same remaining commands. One different terminal outcome.",
    fontsize=20,
    weight="bold",
)
fig.text(
    0.055,
    0.885,
    "Five registered pairs · ten admitted trajectories · no new search or native driving",
    fontsize=11,
    color="#53606a",
)
for index, zoom in enumerate((False, True)):
    ax = fig.add_subplot(grid[index])
    route = case["geometry"]["route"]
    ax.plot(
        [p[1] for p in route],
        [p[0] for p in route],
        color="#c6cdd1",
        lw=5,
        alpha=0.65,
        label="Frozen route",
    )
    for arm in colors:
        rows = traces["pair_2_" + arm]
        ax.plot(
            [r["state"][0] for r in rows],
            [r["state"][1] for r in rows],
            color=colors[arm],
            lw=2,
            ls="--" if arm == "discarded" else "-",
            label=arm.title() + " state",
        )
        ax.scatter(
            [rows[-1]["state"][0]], [rows[-1]["state"][1]], color=colors[arm], s=45, zorder=5
        )
    ax.set_xlabel("Forward position (m)", fontsize=9)
    ax.set_ylabel("Lateral position (m)", fontsize=9)
    ax.set_aspect("equal", adjustable="datalim")
    if zoom:
        ax.set_xlim(24.8, 26.2)
        ax.set_ylim(9.1, 10.3)
        for j in (230, 231, 232):
            p = route[j]
            ax.scatter(p[1], p[0], s=25, color="#5c6870", zorder=4)
            ax.annotate(
                str(j),
                (p[1], p[0]),
                xytext=(0, -17),
                textcoords="offset points",
                ha="center",
                fontsize=8,
            )
        ax.set_title(
            "Terminal positions\nRoute index 231 first qualifies", loc="left", fontsize=11, pad=14
        )
    else:
        ax.set_title("Chicane left · endpoint representative", loc="left", fontsize=11, pad=14)
        ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=8)
ax = fig.add_subplot(grid[2])
labels = [
    "Bend left",
    "Bend right",
    "Chicane left\nendpoint",
    "Chicane left\nroute",
    "Chicane right",
]
for i in range(5):
    rows = [r for r in admission["records"] if r["name"].startswith(f"pair_{i}_")]
    values = [r["final_progress"] for r in rows]
    ax.plot(values, [i - 0.05, i + 0.05], color="#b7bfc5", lw=2)
    for r in rows:
        ax.scatter(
            r["final_progress"],
            i + (-0.05 if r["arm"] == "discarded" else 0.05),
            color=colors[r["arm"]],
            marker="o" if r["arm"] == "discarded" else "s",
            s=42,
            zorder=4,
        )
ax.axvline(1, color="#65727b", ls=":", lw=1)
ax.set_yticks(range(5), labels, fontsize=9)
ax.invert_yaxis()
ax.set_xlim(0.996, 1.010)
ax.set_ylim(4.65, -0.65)
ax.set_xlabel("Terminal source progress (1.0 = complete)", fontsize=9)
ax.set_title("All five paired outcomes", loc="left", fontsize=11, pad=14)
ax.spines[["top", "right"]].set_visible(False)
ax.tick_params(axis="x", labelsize=8)
fig.text(
    0.055,
    0.115,
    "One fixed suffix ends at 0.998703; its witness reaches 1.007350. All ten pass every observed hard constraint.",
    fontsize=11,
)
fig.text(
    0.055,
    0.067,
    "This is a finite-horizon completion difference. Alternative continuations and whole-search causation remain untested.",
    fontsize=10,
    color="#53606a",
)
for extension in ("png", "svg"):
    fig.savefig(base / "proof" / f"continuations.{extension}", dpi=170)
plt.close(fig)
identities.append(
    dict(
        path="proof/admission.json",
        sha256=hashlib.sha256((base / "proof/admission.json").read_bytes()).hexdigest(),
    )
)
identities.append(
    dict(
        path="../iter159_route_search_qualification/CASES.json",
        sha256=hashlib.sha256(
            (base.parent / "iter159_route_search_qualification/CASES.json").read_bytes()
        ).hexdigest(),
    )
)
(base / "proof/figure-identity.json").write_text(json.dumps(identities, indent=2) + "\n")
