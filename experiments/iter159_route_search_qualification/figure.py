"""Presentation derived only from admitted synthetic traces and case inputs."""

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

base = Path(__file__).resolve().parent
admission = json.loads((base / "proof/admission.json").read_text())
cases = json.loads((base / "CASES.json").read_text())
fig = plt.figure(figsize=(15, 9), layout="constrained")
grid = fig.add_gridspec(2, 3, width_ratios=[1, 1, 1.22])
fig.suptitle("A feasible action exists. Search can still lose it.", fontsize=19, x=0.04, ha="left")
colors = {"endpoint": "#a26844", "route": "#246b83"}
identities = []
for index, case in enumerate(cases):
    ax = fig.add_subplot(grid[index // 2, index % 2])
    points = np.asarray(case["points"])
    ax.scatter(points[::25, 2], points[::25, 0], s=1.5, color="#bac3c9", alpha=0.7)
    for obstacle in case["geometry"]["obstacles"]:
        ax.scatter([obstacle[0]], [-obstacle[1]], marker="s", s=14, color="#6e5575")
    witness = base / "proof/raw" / (case["id"] + "_witness/trace.json")
    trace = json.loads(witness.read_text())
    ax.plot(
        [r["state"][0] for r in trace],
        [r["state"][1] for r in trace],
        "--",
        lw=1.8,
        color="#414950",
        label="Verified witness",
    )
    for ranking in ("endpoint", "route"):
        record = next(
            r
            for r in admission["records"]
            if r["case"] == case["id"]
            and r["ranking"] == ranking
            and r["pruning"] == "speed_groups"
        )
        path = base / "proof/raw" / record["name"] / "selected/trace.json"
        rows = json.loads(path.read_text())
        ax.plot(
            [r["state"][0] for r in rows],
            [r["state"][1] for r in rows],
            color=colors[ranking],
            lw=2,
            label=ranking.title() + " + speed groups",
        )
        ax.scatter(
            [rows[-1]["state"][0]],
            [rows[-1]["state"][1]],
            marker="o" if record["complete"] else "x",
            s=45,
            color=colors[ranking],
        )
        identities.append(
            dict(
                path=str(path.relative_to(base)),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )
    ax.set_title(case["id"].replace("_", " ").title(), loc="left", fontsize=12)
    ax.set_xlabel("Forward position (m)")
    ax.set_ylabel("Lateral position (m)")
    ax.set_aspect("equal", adjustable="datalim")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=8)
    if index == 0:
        ax.legend(fontsize=7, frameon=False, loc="upper left")

ax = fig.add_subplot(grid[0, 2])
ax.axis("off")
labels = ["Endpoint / rank", "Endpoint / speed", "Route / rank", "Route / speed"]
arms = [
    ("endpoint", "rank"),
    ("endpoint", "speed_groups"),
    ("route", "rank"),
    ("route", "speed_groups"),
]
rows, fills = [], []
for case in cases:
    record = [
        next(
            r
            for r in admission["records"]
            if r["case"] == case["id"] and (r["ranking"], r["pruning"]) == arm
        )
        for arm in arms
    ]
    rows.append(
        [
            "Complete"
            if r["complete"]
            else ("Budget" if r["stop"] == "attempt_budget" else "Beam empty")
            for r in record
        ]
    )
    fills.append(["#e2eee9" if r["complete"] else "#f2e7df" for r in record])
table = ax.table(
    cellText=rows,
    cellColours=fills,
    rowLabels=[c["id"].replace("_", "\n") for c in cases],
    colLabels=[label.replace(" / ", "\n") for label in labels],
    cellLoc="center",
    loc="center",
    bbox=[0.08, 0.24, 0.92, 0.62],
)
table.auto_set_font_size(False)
table.set_fontsize(7.5)
for cell in table.get_celld().values():
    cell.set_edgecolor("white")
ax.set_title("All 16 registered outcomes", loc="left", fontsize=13, fontweight="bold")
ax.text(
    0.08,
    0.1,
    "Candidate: 3/4 complete. Four-case bar contradicted.\nFixed 18,000-transition cap for every run.",
    transform=ax.transAxes,
    fontsize=9,
    va="top",
)

ax = fig.add_subplot(grid[1, 2])
ax.axis("off")
causes = {}
for r in admission["records"]:
    cause = r["witness_loss"]["cause"]
    causes[cause] = causes.get(cause, 0) + 1
lines = [
    "What is independently checked",
    "",
    f"{admission['verified_states']} retained states; full point masks",
    "4 complete witnesses; 16 selected paths",
    "Dynamics, controls, foreground and progress",
    "",
    "First lost reference prefix:",
]
lines += [f"{v} runs: {k.replace('_', ' ')}" for k, v in causes.items()]
lines += [
    "",
    "Losing one witness does not prove that all",
    "feasible continuations were lost.",
    "",
    "Constructed development geometry only.",
    "Background between samples and native",
    "recovery remain unestablished.",
]
ax.text(
    0,
    0.96,
    "\n".join(lines),
    transform=ax.transAxes,
    va="top",
    fontsize=10,
    linespacing=1.45,
    color="#2f424d",
)
for extension in ("png", "svg"):
    fig.savefig(base / "proof" / f"qualification.{extension}", dpi=160)
plt.close(fig)
identities.extend(
    dict(path=n, sha256=hashlib.sha256((base / n).read_bytes()).hexdigest())
    for n in ("proof/admission.json", "CASES.json")
)
(base / "proof/figure-identity.json").write_text(json.dumps(identities, indent=2) + "\n")
