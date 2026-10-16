"""Post-admission chronological inventory only; no query, search or new tree."""

import json
from pathlib import Path

from experiments.iter172_integrated_rrt.check import outcome
from experiments.iter185_retained_prefix_admission.common import read, git, require, sha, write

RAW = "172cf0f5449e4171c3f9a25bc45d6e6cb7f03bd5"
ADMISSION = "d25eea6749395d173808e980cc134c9b51d9f94a"
BASE = Path("experiments/iter185_retained_prefix_admission")
PREVIOUS = Path("experiments/iter183_timing_eligibility")


def bound(root, name, commit):
    data = read(root, name)
    require(data == git(root, "show", commit + ":" + str(name)), "source_binding")
    return data


def main():
    root = Path.cwd()
    admitted = bound(root, BASE / "proof/admission.json", ADMISSION)
    require(json.loads(admitted)["full_route_continuations"] == 1, "admitted_scope")
    cases_data = bound(root, "experiments/iter161_grouping_width_ablation/CASES.json", RAW)
    cases = json.loads(cases_data)
    records = []
    for case in cases:
        data = bound(root, PREVIOUS / "proof/search_raw" / case["id"] / "events.jsonl", RAW)
        events = [json.loads(line) for line in data.splitlines()]
        best = outcome(case["geometry"]["reset"], case["geometry"])["nearest"]
        pending, candidates = [], []
        record_count = 0
        for event in events:
            if event["kind"] == "evaluation":
                pending.append(event)
            elif event["kind"] == "connection":
                result = event["result"]
                prior = best
                if result is not None and len(event["trace"]) > 1:
                    best = max(best, event["trace"][-1]["route"]["nearest"])
                available = []
                if result is not None and not result["world_complete"]:
                    for trial in pending:
                        for k in range(1, trial["eligibility"]["eligible_prefix"] + 1):
                            row = trial["trace"][k]
                            on_selected = (
                                trial["id"] == result["selected_evaluation"]
                                and k <= result["selected_prefix"]
                            )
                            if not on_selected and row["route"]["nearest"] > best:
                                available.append(
                                    dict(
                                        call=event["call"],
                                        evaluation=trial["id"],
                                        prefix=k,
                                        frame=row["frame"],
                                        state=row["state"],
                                        nearest=row["route"]["nearest"],
                                        route_fraction=row["route"]["rc"],
                                    )
                                )
                    record_count += len(available)
                    if available:
                        selected = min(
                            available,
                            key=lambda r: (-r["nearest"], r["frame"], r["evaluation"], r["prefix"]),
                        )
                        candidates.append(
                            dict(
                                **selected,
                                best_before=prior,
                                best_after_selected=best,
                                available_records=len(available),
                            )
                        )
                pending = []
        require(not pending, "pending_evaluation")
        records.append(
            dict(
                case=case["id"],
                input_sha256=sha(data),
                final_retained_nearest=best,
                advancing_prefix_records=record_count,
                candidate_connections=len(candidates),
                first_candidate=candidates[0] if candidates else None,
                candidates=candidates,
            )
        )
    write(
        root / BASE / "proof/online_candidate_inventory.json",
        dict(
            status="exploratory",
            raw_commit=RAW,
            admission_commit=ADMISSION,
            admission_sha256=sha(admitted),
            cases_sha256=sha(cases_data),
            records=records,
            scope="Chronological recorded-valid/eligible unselected prefixes above the accepted endpoint maximum available after each original connection. One maximum-index/earliest-frame candidate per connection; selected-edge interiors excluded. No new masks, search, insertion or counterfactual tree.",
            boundary="Only the fifteen separately audited right-bend prefixes have their additional masks admitted. Inventory counts do not establish other prefixes' scalar validity or usefulness. Original chronology cannot predict a modified tree.",
        ),
    )
    print(
        [
            {k: row[k] for k in ["case", "advancing_prefix_records", "candidate_connections"]}
            for row in records
        ]
    )


if __name__ == "__main__":
    main()
