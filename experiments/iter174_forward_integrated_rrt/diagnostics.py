"""Post-outcome descriptive work/selection audit; no search or policy change."""

import json
from pathlib import Path

from experiments.iter172_integrated_rrt.diagnostics import summarize


def selection_summary(rows):
    evaluations = []
    calls = []
    maximum = truncated = 0
    for row in rows:
        if row["kind"] == "evaluation":
            evaluations.append(row)
            if row["interrupted"] is None and row["valid_prefix"] > 0:
                maximum = max(maximum, row["trace"][row["valid_prefix"]]["frame"])
                truncated += row["valid_prefix"] > row["selected_prefix"]
        if row["kind"] != "connection":
            continue
        result = row["result"]
        if result is not None:
            spent = 0
            selected_at = None
            for trial in evaluations:
                spent += len(trial["trace"])-1
                if trial["id"] == result["selected_evaluation"]:
                    selected_at = spent
            assert spent == result["attempts"], "diagnostic_attempt_accounting"
            assert (selected_at is None) == (result["selected_evaluation"] is None), "diagnostic_selection"
            calls.append(dict(call=row["call"], attempts=spent, final_selection_at=selected_at))
        else:
            assert not evaluations, "diagnostic_unexecuted"
        evaluations = []
    assert not evaluations, "diagnostic_pending"
    selected = [c for c in calls if c["final_selection_at"] is not None]
    return dict(calls=calls, maximum_reported_valid_frame=maximum,
                truncated_trial_prefixes=truncated, accepted_requests=len(selected),
                final_selection_by_128=sum(c["final_selection_at"] <= 128 for c in selected),
                attempts_after_final_selection=sum(c["attempts"]-c["final_selection_at"] for c in selected),
                attempts_without_edge=sum(c["attempts"] for c in calls if c["final_selection_at"] is None))


def analyze(base):
    result = summarize(base)
    for row in result["records"]:
        path = base / "proof/search_raw" / row["case"] / "events.jsonl"
        with path.open() as stream:
            row["selection"] = selection_summary(json.loads(line) for line in stream)
    fields = ["accepted_requests", "final_selection_by_128", "attempts_after_final_selection",
              "attempts_without_edge", "truncated_trial_prefixes"]
    result["selection_totals"] = {k: sum(r["selection"][k] for r in result["records"]) for k in fields}
    result["selection_boundary"] = (
        "Post-outcome accounting, not an online stopping oracle. Later controls can change the "
        "eventual selected return after 128 transitions. "
        "Unselected valid-prefix background labels remain producer evidence. A different budget "
        "changes the tree; no shorter-budget success or timing gain is established."
    )
    return result


if __name__ == "__main__":
    base = Path(__file__).resolve().parent
    (base / "proof/diagnostics.json").write_text(json.dumps(analyze(base), indent=2) + "\n")
