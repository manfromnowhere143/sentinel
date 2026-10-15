"""Post-outcome accounting of retained requests; no search or policy changes."""

import json
from pathlib import Path

from experiments.iter172_integrated_rrt.diagnostics import summarize
from experiments.iter174_forward_integrated_rrt.diagnostics import selection_summary
from .comparison import coverage


def horizon_coverage(rows):
    pending, groups, continuations = [], {}, []
    for row in rows:
        if row["kind"] in ("request", "evaluation"):
            pending.append(row)
        if row["kind"] != "connection":
            continue
        if row["result"] is not None:
            horizon = row["task"]["terminal_frame"]
            counts = coverage(pending)
            assert sum(counts["transitions"].values()) == row["result"]["attempts"]
            group = groups.setdefault(horizon, dict(calls=0, transitions=0, halton_transitions=0))
            group["calls"] += 1
            group["transitions"] += sum(counts["transitions"].values())
            group["halton_transitions"] += counts["transitions"]["halton"]
            for trial in pending:
                if (trial["kind"] == "evaluation" and trial["interrupted"] is None
                        and trial["valid_prefix"] > trial["selected_prefix"]):
                    end = trial["trace"][trial["valid_prefix"]]
                    if end["frame"] >= 32:
                        continuations.append(dict(call=row["call"], evaluation=trial["id"],
                                                  frame=end["frame"], progress=end["route"]["rc"],
                                                  selected_prefix=trial["selected_prefix"],
                                                  valid_prefix=trial["valid_prefix"]))
        else:
            assert not pending
        pending = []
    assert not pending
    return dict(by_horizon=groups, truncated_prefixes_at_or_after_final_checkpoint=continuations)


def analyze(base):
    result = summarize(base)
    for row in result["records"]:
        path = base / "proof/search_raw" / row["case"] / "events.jsonl"
        with path.open() as stream:
            row["selection"] = selection_summary(json.loads(line) for line in stream)
        with path.open() as stream:
            row["coverage"] = horizon_coverage(json.loads(line) for line in stream)
    result["selection_boundary"] = (
        "Retrospective selected/valid-prefix counts are not an online oracle or a demonstrated "
        "repair. Unselected background labels remain producer evidence. Later tree outcomes "
        "under another ranking are unknown."
    )
    return result


if __name__ == "__main__":
    base = Path(__file__).resolve().parent
    (base / "proof/diagnostics.json").write_text(json.dumps(analyze(base), indent=2) + "\n")
