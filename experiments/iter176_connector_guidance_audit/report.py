"""Descriptive grouping and figure from admitted audit records; no search."""

import hashlib
import json
from pathlib import Path


def summarize(base):
    admission_path = base / "proof/admission.json"
    proposals_path = base / "proof/audit_raw/proposals.json"
    admission = json.loads(admission_path.read_text())
    proposals = json.loads(proposals_path.read_text())
    groups = {}
    for field in ("case", "horizon"):
        groups[field] = {}
        for row in admission["records"]:
            group = groups[field].setdefault(str(row[field]), dict(total=0, closed=0, open=0))
            group["total"] += 1
            group["closed" if row["reflection_closed"] else "open"] += 1
    long_open = []
    for row, request in zip(admission["records"], proposals["requests"]):
        if row["horizon"] == 8 and not row["reflection_closed"]:
            long_open.append(dict(case=row["case"], call=row["call"], budget=row["budget"],
                                  missing_reflected=row["missing_reflected"],
                                  extra_mirrored=row["extra_mirrored"],
                                  initial_program_reused={arm: any(r["cached"] and r["evaluation"] == 1
                                                                   for r in request[arm]["requests"])
                                                          for arm in ("original", "mirrored")}))
    return dict(status="exploratory", groups=groups, open_eight_step_requests=long_open,
                source_hashes={str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in (admission_path, proposals_path)},
                boundary="Nominal program availability; cache hits correctly save work. No causal directional-bias, cache-defect or repaired-planner claim.")


def plot(base, result):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    a = json.loads((base / "proof/admission.json").read_text())
    names = ["bend_left", "bend_right", "chicane_left", "chicane_right"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4))
    fig.patch.set_facecolor("#fafaf7")
    for ax in axes:
        ax.set_facecolor("#fafaf7")
        ax.spines[["top", "right"]].set_visible(False)
        ax.invert_yaxis()
    groups = result["groups"]["case"]
    for i, name in enumerate(names):
        group = groups[name]
        axes[0].barh(i, group["closed"], color="#638295", height=.5)
        axes[0].barh(i, group["open"], left=group["closed"], color="#ba7650", height=.5)
        axes[0].text(group["total"]+2, i, f'{group["closed"]}/{group["total"]} closed',
                     va="center", fontsize=10)
    axes[0].set_yticks(range(4), [n.replace("_", " ") for n in names])
    axes[0].set(xlim=(0, 182), xlabel="Retained requests · blue = closed; rust = open",
                title="327/386 nominal sets preserve reflected coverage")
    axes[0].set_xticks([0, 50, 100, 150])
    for i, path in enumerate(a["paths"]):
        axes[1].barh(i, path["final_progress"], color="#638295", height=.5)
        axes[1].text(path["final_progress"]+.025, i, f'{path["final_progress"]:.3f}', va="center")
    axes[1].axvline(1, color="#303b42", linestyle="--", linewidth=1)
    axes[1].set_yticks(range(4), [f'Evaluation {p["evaluation"]}' for p in a["paths"]])
    axes[1].set(xlim=(0, 1.07), xlabel="Route fraction at 8 s · completion requires ≥1",
                title="Four admitted partial paths; none completes")
    fig.suptitle("Guidance audit: coverage differences are not a diagnosed repair", fontsize=17, y=.98)
    fig.text(.06, .13, "317/324 eight-step requests preserve coverage. All four paths share one case and ancestry; "
             "132 states/full masks replay.", fontsize=10)
    fig.text(.06, .055, "Iter176 · Exploratory nominal enumeration and retained-path replay. "
             "Integrated qualification remains 2/4; source comparison stays closed.", fontsize=10, color="#465057")
    fig.subplots_adjust(left=.12, right=.97, bottom=.28, top=.78, wspace=.48)
    fig.savefig(base / "proof/audit.png", dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)


if __name__ == "__main__":
    base = Path(__file__).resolve().parent
    result = summarize(base)
    (base / "proof/summary.json").write_text(json.dumps(result, indent=2)+"\n")
    plot(base, result)
