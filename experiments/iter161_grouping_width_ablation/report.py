"""Post-acquisition arithmetic and figure from admitted records; no search."""

import argparse
from collections import Counter
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent


def summarize():
    admission = json.loads((BASE / "proof/admission.json").read_bytes())
    cases = json.loads((BASE / "CASES.json").read_bytes())
    plan = json.loads((BASE / "PLAN.json").read_bytes())
    arms, values = [], {}
    for grouping, width in plan["arms"]:
        rows = [
            r for r in admission["records"] if (r["aggregation"], r["width"]) == (grouping, width)
        ]
        assert [r["case"] for r in rows] == [c["id"] for c in cases]
        complete = sum(r["complete"] for r in rows)
        values[grouping, width] = complete
        arms.append(
            dict(
                aggregation=grouping,
                width=width,
                complete=complete,
                attempts=sum(r["attempts"] for r in rows),
                search_queries=sum(r["queries"] for r in rows),
                search_seconds=sum(r["elapsed_seconds"] for r in rows),
                stops=dict(Counter(r["stop"] for r in rows)),
                retention={k: sum(r["retention"][k] for r in rows) for k in rows[0]["retention"]},
                first_loss=dict(Counter(r["witness_loss"]["cause"] for r in rows)),
            )
        )
    contrasts = dict(
        grouping_at_24=values["exact", 24] - values["quantized", 24],
        grouping_at_48=values["exact", 48] - values["quantized", 48],
        width_for_quantized=values["quantized", 48] - values["quantized", 24],
        width_for_exact=values["exact", 48] - values["exact", 24],
    )
    contrasts["interaction"] = contrasts["grouping_at_48"] - contrasts["grouping_at_24"]
    table = [
        "| Case | Grouping / width | Outcome | Attempts | Queries | Depth | Progress | Grouping removed | Width removed |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    records = []
    for row in admission["records"]:
        trace = json.loads((BASE / "proof/raw" / row["name"] / "selected/trace.json").read_bytes())
        progress = trace[-1]["route"]["rc"]
        record = dict(row, selected_progress=progress)
        records.append(record)
        table.append(
            f"| {row['case'].replace('_', ' ')} | {row['aggregation']} / {row['width']} | "
            f"{row['stop']} | {row['attempts']:,} | {row['queries']:,} | "
            f"{row['completed_depth']} | {progress:.6f} | "
            f"{row['retention']['grouping_removed']:,} | {row['retention']['width_removed']:,} |"
        )
    result = dict(
        iteration=161,
        scope="Arithmetic from admitted fixed-budget factorial records",
        arms=arms,
        contrasts=contrasts,
        contrast_units="Difference in completion counts among the same four disclosed controls",
        records=records,
        witness_count=len(admission["witnesses"]),
        point_state_classifications=sum(
            r["verified_states"] * len(next(c for c in cases if c["id"] == r["case"])["points"])
            for r in [*admission["witnesses"], *admission["records"]]
        ),
        observed_progress_checks=sum(
            r["progress_checks"] for r in [*admission["witnesses"], *admission["records"]]
        ),
    )
    (BASE / "proof/summary.json").write_text(json.dumps(result, indent=2) + "\n")
    (BASE / "proof/table.md").write_text("\n".join(table) + "\n")
    return result


def figure(result):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "none"})
    fig, ax = plt.subplots(figsize=(12, 6.6))
    fig.patch.set_facecolor("#0e1824")
    ax.set_facecolor("#0e1824")
    ax.set_xlim(-1.25, 4)
    ax.set_ylim(-0.7, 4.8)
    ax.axis("off")
    for j, arm in enumerate(result["arms"]):
        ax.text(
            j + 0.45,
            4.27,
            f"{arm['aggregation'].title()} · {arm['width']}",
            color="#ecf2f7",
            ha="center",
            size=12,
            weight="bold",
        )
        ax.text(
            j + 0.45, 3.98, f"{arm['complete']}/4 complete", color="#afbdcb", ha="center", size=11
        )
    cases = ["bend_left", "bend_right", "chicane_left", "chicane_right"]
    for i, case in enumerate(cases):
        y = 3 - i
        ax.text(
            -0.15,
            y + 0.45,
            case.replace("_", " ").title(),
            color="#dce5ee",
            ha="right",
            va="center",
            size=12,
        )
        for j, arm in enumerate(result["arms"]):
            row = next(
                r
                for r in result["records"]
                if (r["case"], r["aggregation"], r["width"])
                == (case, arm["aggregation"], arm["width"])
            )
            color = "#78d3b3" if row["complete"] else "#edb66b"
            ax.add_patch(
                FancyBboxPatch(
                    (j, y),
                    0.9,
                    0.88,
                    boxstyle="round,pad=0.012,rounding_size=.04",
                    facecolor="#172737",
                    edgecolor=color,
                    linewidth=1.2,
                )
            )
            label = "Complete" if row["complete"] else row["stop"].replace("_", " ").title()
            ax.text(j + 0.45, y + 0.66, label, color=color, ha="center", size=11, weight="bold")
            ax.text(
                j + 0.45,
                y + 0.4,
                f"{row['attempts']:,} attempts",
                color="#ecf2f7",
                ha="center",
                size=10,
            )
            ax.text(
                j + 0.45,
                y + 0.16,
                f"Depth {row['completed_depth']} · rc {row['selected_progress']:.3f}",
                color="#afbdcb",
                ha="center",
                size=9,
            )
    fig.text(
        0.06,
        0.95,
        "Grouping and width have different fixed-budget effects",
        color="#ecf2f7",
        size=17,
        weight="bold",
    )
    fig.text(
        0.06,
        0.9,
        "Four disclosed controls · same route guide and proposals · 18,000-transition cap per run",
        color="#afbdcb",
        size=11,
    )
    fig.text(
        0.06,
        0.055,
        "Depth = fully expanded layers; rc = selected-prefix progress. Threshold: rc ≥ 1. All selected paths replay independently.",
        color="#afbdcb",
        size=9,
    )
    fig.text(
        0.06,
        0.025,
        "Two paired scene families; no population or native-recovery claim. Source: Iter161 independent admission.",
        color="#afbdcb",
        size=9,
    )
    fig.subplots_adjust(top=0.86, bottom=0.10, left=0.04, right=0.98)
    for extension in ("png", "pdf", "svg"):
        fig.savefig(BASE / f"proof/factorial.{extension}", dpi=180, facecolor=fig.get_facecolor())
    svg = BASE / "proof/factorial.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()
    result = summarize()
    if args.plot:
        figure(result)
    print(json.dumps(dict(arms=result["arms"], contrasts=result["contrasts"]), indent=2))
