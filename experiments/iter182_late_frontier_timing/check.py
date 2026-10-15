"""Case-scoped scalar replay, independent timing bounds and complete accounting."""

import argparse
from collections import Counter
import json
from pathlib import Path
import time

from experiments.iter171_centered_shooting.runtime import identity
from experiments.iter179_frontier_continuation_audit.check import scalar_masks
from .common import BASE, document, read, require, rss, write
from .contract import check_plan
from .records import committed
from .retained import load, OLD, through_first_rejection, state_key
from .replay import row_check, path_binding, path_check, probe_check
from .bound_check import check_bound
from .premature_check import check_completion


def classify(witness, progress, premature, censored):
    require(
        all(type(v) is bool for v in (witness, progress, premature, censored)),
        "classification_type",
    )
    require(not (witness and (progress or premature)), "bound_false_exclusion")
    require(not (witness and censored), "censored_witness")
    if witness:
        return "verified_continuation"
    if progress and premature:
        return "both_constraints_excluded"
    if progress:
        return "progress_excluded"
    if premature:
        return "premature_completion_excluded"
    return "unobserved_continuation" if censored else "bounded_miss"


def case_check(raw, case, connections, selected, trials, old, plan, execution, deadline):
    masks = scalar_masks(raw, case, deadline)
    used, prior, representatives, verified = set(), {}, [], 0
    paths = document(raw, "paths.json")
    require([p["call"] for p in paths] == [c["call"] for c in selected], "path_population")
    for path in paths:
        path_binding(path, connections, case["geometry"]["reset"])
        verified += path_check(path["trace"], path["masks"], case, old, masks)
        used.update(path["masks"])
        last = path["trace"][-1]
        key = tuple([*last["state"], last["frame"]])
        expected = prior.setdefault(key, path["call"])
        require(path["representative"] == expected, "duplicate_representative")
        if expected == path["call"]:
            representatives.append(path)
    require(len(prior) == len(selected), "distinct_frontier")
    evaluations = document(raw, "retained_evaluations.json")
    require(
        [(r["call"], r["evaluation"]) for r in evaluations]
        == [(r["call"], r["id"]) for r in trials],
        "evaluation_population",
    )
    first_reasons, prefix_states = Counter(), 0
    table = {c["call"]: c for c in connections}
    for record, trial in zip(evaluations, trials):
        prefix = list(through_first_rejection(trial))
        require(
            [*prefix[0]["state"], prefix[0]["frame"]] == table[trial["call"]]["before"],
            "retained_trial_root",
        )
        expected_keys = []
        for i, row in enumerate(prefix):
            require(
                row["frame"] == row["id"] == prefix[0]["frame"] + i
                and row["parent"] == (None if i == 0 else row["frame"] - 1),
                "retained_clock",
            )
            row_check(row, prefix[i - 1] if i else row, case, old, masks)
            key = None if row["background"] is None else state_key(row["state"])
            require(key is None or key in masks, "retained_mask_missing")
            if key is not None:
                used.add(key)
            expected_keys.append(key)
        reason = prefix[-1]["reason"] if prefix[-1]["reason"] != "clear" else "all_reported_clear"
        require(
            record["masks"] == expected_keys and record["first_reason"] == reason, "retained_prefix"
        )
        first_reasons[reason] += 1
        prefix_states += len(prefix)
    probes = document(raw, "probes.json")
    require([r["call"] for r in probes] == [p["call"] for p in representatives], "probe_population")
    records, combined_states, attempted = [], 0, 0
    for probe, path in zip(probes, representatives):
        require(time.monotonic() < deadline, "checker_deadline")
        folder = raw / f"probe_{probe['call']:03}"
        attempts = document(folder, "attempts.json")
        combined = document(folder, "trace.json")
        for row in attempts:
            if row["background"] is not None:
                key = state_key(row["state"])
                require(
                    key in masks and row["background"] == masks[key]["background"],
                    "all_query_scalar_binding",
                )
                used.add(key)
        witness = probe_check(probe, attempts, combined, path["trace"], case, old, plan, masks)
        last = path["trace"][-1]
        excluded = check_bound(
            probe["bound"],
            last["state"],
            last["frame"],
            case["geometry"],
            old,
            plan["target_frame"],
        )
        premature = check_completion(
            probe["completion_bound"],
            last["state"],
            last["frame"],
            case["geometry"],
            old,
            plan["target_frame"],
        )
        censored = probe["result"]["stop"] == "time_budget"
        if censored:
            require(
                execution["probe_envelope_seconds"] >= plan["aggregate_search_seconds"],
                "probe_early_censor",
            )
        label = classify(witness, excluded, premature, censored)
        records.append(
            dict(
                case=case["id"],
                call=probe["call"],
                completion_bound_applicable=probe["completion_bound"]["applicable"],
                premature_completion_excluded=premature,
                outgoing_calls=[
                    c["call"] for c in connections if c["before"] == [*last["state"], last["frame"]]
                ],
                start_frame=last["frame"],
                classification=label,
                checkpoint_continuation=witness,
                progress_excluded=excluded,
                censored=censored,
                stop=probe["result"]["stop"],
                attempts=probe["result"]["attempts"],
                returned_frame=combined[-1]["frame"],
                source_model_complete=witness and combined[-1]["route"]["rc"] >= 1,
                returned_route_completion=combined[-1]["route"]["rc"],
            )
        )
        attempted += probe["result"]["attempts"]
        combined_states += len(combined)
        used.update(probe["masks"])
    require(used == set(masks), "unused_materialization")
    return dict(
        case=case["id"],
        records=records,
        retained_endpoint_records=len(paths),
        distinct_frontier_states=len(prior),
        retained_path_state_records=verified,
        probe_path_state_records=combined_states,
        distinct_scalar_states=len(masks),
        point_state_classifications=len(masks) * len(case["points"]),
        retained_evaluations=len(evaluations),
        retained_prefix_state_records=prefix_states,
        first_rejections=dict(first_reasons),
        diagnostic_attempts=attempted,
    )


def check(root, commit):
    started = time.monotonic()
    plan = document(root, BASE / "PLAN.json")
    check_plan(plan)
    raw = root / BASE / "proof/audit_raw"
    execution = committed(root, raw, commit, plan)
    deadline = started + plan["audit_checker_seconds"]
    runtime = json.loads(read(root, BASE / "RUNTIME.json"))
    require(identity() == runtime, "runtime_identity")
    inputs = load(root, plan)
    old = json.loads(read(root, OLD))
    cases = [
        case_check(
            raw / case["id"], case, connections, selected, trials, old, plan, execution, deadline
        )
        for case, connections, selected, trials in inputs
    ]
    totals = {
        k: sum(c[k] for c in cases)
        for k in (
            "retained_endpoint_records",
            "distinct_frontier_states",
            "retained_path_state_records",
            "probe_path_state_records",
            "distinct_scalar_states",
            "point_state_classifications",
            "retained_evaluations",
            "retained_prefix_state_records",
            "diagnostic_attempts",
        )
    }
    require(
        execution["new_motion_searches"] == totals["distinct_frontier_states"] == 7
        and execution["new_integrated_schedules"] == 0
        and execution["diagnostic_attempts"]
        == totals["diagnostic_attempts"]
        <= plan["depth_specific_maximum_attempts"]
        <= plan["maximum_total_attempts"]
        and execution["distinct_masks"] == totals["distinct_scalar_states"],
        "audit_scope",
    )
    require(
        identity() == runtime and rss() <= plan["max_rss_bytes"] and time.monotonic() < deadline,
        "checker_resources",
    )
    records = [r for c in cases for r in c["records"]]
    witnesses = sum(r["checkpoint_continuation"] for r in records)
    censored = sum(r["censored"] for r in records)
    return dict(
        iteration=182,
        phase="closed",
        analysis_status="exploratory",
        status="supported" if witnesses else ("inconclusive" if censored else "null"),
        claim="The fixed diagnostic finds at least one scalar-verified frame-32 continuation from the seven exposed late Iter181 endpoints.",
        source_commit=execution["source_commit"],
        raw_commit=commit,
        **totals,
        checkpoint_witnesses=witnesses,
        progress_exclusions=sum(r["progress_excluded"] for r in records),
        premature_completion_exclusions=sum(r["premature_completion_excluded"] for r in records),
        bounded_misses=sum(r["classification"] == "bounded_miss" for r in records),
        censored_probes=censored,
        records=records,
        cases=cases,
        retained_complete_cases=3,
        retained_total_cases=4,
        candidate_complete_cases=2,
        qualified_for_source_comparison=False,
        new_integrated_schedules=0,
        new_driving_episodes=0,
        provider_spend=0,
        source_recovery=None,
        superiority=None,
        transfer=None,
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
        boundary="Seven exposed endpoint records; full scalar queries and numeric-joined paths. Bounds apply only to the declared source numerical model. Bounded misses do not prove infeasibility. A diagnostic witness does not repair integrated qualification or establish actual-history intervention.",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--raw-commit", required=True)
    args = parser.parse_args()
    result = check(args.root.resolve(), args.raw_commit)
    write(args.root.resolve() / BASE / "proof/admission.json", result)
    print(
        json.dumps({k: v for k, v in result.items() if k not in {"records", "cases"}}), flush=True
    )
