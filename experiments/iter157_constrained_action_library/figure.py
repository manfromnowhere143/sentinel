"""Presentation derived only from admitted counts; no new scientific evaluation."""

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

base = Path(__file__).resolve().parent
source = base / "proof/admission.json"
data = json.loads(source.read_text())
witnesses = [r for r in data["scalar_checks"] if r["decision"] == "collision"]
fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.0), gridspec_kw={"width_ratios": [1, 2.3]})
fig.subplots_adjust(top=0.78, bottom=0.26, left=0.16, right=0.98, wspace=0.35)
fig.suptitle(
    "No candidate meets every declared source-model condition",
    x=0.08,
    ha="left",
    fontsize=16,
    fontweight="bold",
)
axes[0].barh(
    ["Prior conditions\nfail", "Background\nrejects", "Qualifies"],
    [61, 14, 0],
    color=["#59748a", "#b87340", "#3e8578"],
)
axes[0].invert_yaxis()
axes[0].set_xlim(0, 75)
axes[0].set_xlabel("Candidates / fixed library of 75")
for i, n in enumerate([61, 14, 0]):
    axes[0].text(n + 1, i, str(n), va="center")
axes[1].bar(
    range(14),
    [r["count"] for r in witnesses],
    color=["#b87340" if r["candidate"] == "maneuver_059" else "#59748a" for r in witnesses],
)
axes[1].axhline(100, color="#713b36", ls="--", lw=1)
axes[1].text(
    13.4,
    105,
    "strict threshold >100",
    ha="right",
    fontsize=9,
    color="#713b36",
    bbox=dict(facecolor="white", edgecolor="none", alpha=0.88),
)
axes[1].set_xticks(range(14), [r["candidate"].split("_")[1] for r in witnesses], rotation=50)
axes[1].set_ylabel("Enclosed source centers")
axes[1].set_xlabel("Candidate ID / one scalar-verified rejection witness each")
for ax in axes:
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=9)
fig.text(
    0.08,
    0.065,
    "One exposed scene · 27 full scalar masks checked · no new drive\nPrior failures retain unevaluated background; a finite-library null is not physical unavoidability.",
    fontsize=10,
    color="#37434c",
)
outputs = {}
for extension in ["png", "svg"]:
    p = base / f"proof/library-null.{extension}"
    fig.savefig(p, dpi=180, facecolor="white")
    if extension == "svg":
        p.write_text("\n".join(line.rstrip() for line in p.read_text().splitlines()) + "\n")
    outputs[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
(base / "proof/figure_identity.json").write_text(
    json.dumps(
        dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), artifacts=outputs),
        indent=2,
    )
    + "\n"
)
