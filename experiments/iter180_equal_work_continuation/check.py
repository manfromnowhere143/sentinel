"""Independent paired admission with scalar masks for every queried state."""

import argparse
import json
import math
from pathlib import Path
import time
from experiments.iter171_centered_shooting.runtime import identity
from experiments.iter179_frontier_continuation_audit.check import scalar_masks
from experiments.iter179_frontier_continuation_audit.replay import (
    path_binding,
    path_check,
    probe_check,
)
from experiments.iter179_frontier_continuation_audit.retained import state_key
from .common import BASE, OLD, document, read, require, rss, write, encode
from .contract import check_plan, ARMS
from .records import committed
from .retained import load
from .target_check import check_target
from .program_check import program_check
from .comparison import compare


def check(root, commit):
    started = time.monotonic()
    plan = document(root, BASE / "PLAN.json")
    check_plan(plan)
    raw = root / BASE / "proof/study_raw"
    execution = committed(root, raw, commit, plan)
    deadline = started + plan["study_checker_seconds"]
    runtime = json.loads(read(root, BASE / "RUNTIME.json"))
    require(identity() == runtime, "runtime_identity")
    old = json.loads(read(root, OLD))
    case, connections, retained = load(root, plan)
    paths = document(raw, "paths.json")
    require(encode(paths) == encode(retained), "retained_path_identity")
    masks = scalar_masks(raw, case, deadline)
    used, prior, representatives, retained_states = set(), {}, [], 0
    for path in paths:
        path_binding(path, connections, case["geometry"]["reset"])
        retained_states += path_check(path["trace"], path["masks"], case, old, masks)
        used.update(path["masks"])
        endpoint = path["trace"][-1]
        key = (*endpoint["state"], endpoint["frame"])
        representative = prior.setdefault(key, path["call"])
        require(representative == path["representative"], "representative_binding")
        if representative == path["call"]:
            representatives.append(path)
    require(len(representatives) == 16, "distinct_frontier")
    expected = [
        (p, a)
        for i, p in enumerate(representatives)
        for a in (("program", "beam") if i % 2 == 0 else ("beam", "program"))
    ]
    runs = document(raw, "runs.json")
    require(len(runs) == len(expected) == 32, "run_population")
    records, returned_states, attempts, queries = [], 0, 0, 0
    for i, (record, (path, arm)) in enumerate(zip(runs, expected)):
        require(time.monotonic() < deadline, "checker_deadline")
        require(
            record["index"] == i and record["call"] == path["call"] and record["arm"] == arm,
            "run_schedule",
        )
        folder = raw / f"run_{i:02}"
        events, trace = document(folder, "events.json"), document(folder, "trace.json")
        last = path["trace"][-1]
        check_target(
            record["target"], last["state"], last["frame"], case["geometry"], plan["target_frame"]
        )
        require(
            type(record["search_seconds"]) in (int, float)
            and math.isfinite(record["search_seconds"])
            and record["search_seconds"] >= 0,
            "search_clock",
        )
        if arm == "program":
            witness = program_check(record, events, trace, path["trace"], case, old, plan, masks)
            rows = [r for e in events if e["kind"] == "evaluation" for r in e["trace"]]
        else:
            witness = probe_check(record, events, trace, path["trace"], case, old, plan, masks)
            require(
                record["result"]["attempts"] <= plan["maximum_beam_attempts"], "beam_work_bound"
            )
            rows = events
        for row in rows:
            if row["background"] is not None:
                key = state_key(row["state"])
                require(
                    key in masks and masks[key]["background"] == row["background"],
                    "complete_scalar_inventory",
                )
                used.add(key)
        used.update(record["masks"])
        result = record["result"]
        censored = result["stop"] == "time_budget"
        require(not censored or record["search_seconds"] >= plan["per_run_seconds"], "early_censor")
        attempts += result["attempts"]
        queries += result["queries"]
        returned_states += len(trace)
        records.append(
            dict(
                call=path["call"],
                arm=arm,
                witness=witness,
                censored=censored,
                attempts=result["attempts"],
                queries=result["queries"],
                stop=result["stop"],
                root_frame=last["frame"],
                returned_frame=trace[-1]["frame"],
                search_seconds=record["search_seconds"],
            )
        )
    paired = compare(records)
    require(used == set(masks), "unused_mask")
    require(
        execution["new_motion_searches"] == 32
        and execution["new_integrated_schedules"] == 0
        and execution["diagnostic_attempts"] == attempts <= plan["maximum_total_attempts"]
        and execution["distinct_masks"] == len(masks),
        "comparison_scope",
    )
    require(
        identity() == runtime and rss() <= plan["max_rss_bytes"] and time.monotonic() < deadline,
        "checker_resources",
    )
    return dict(
        iteration=180,
        phase="closed",
        analysis_status="exploratory",
        claim="The fixed stepwise search gains at least one checkpoint continuation with no loss against the retained program generator under equal per-run ceilings.",
        source_commit=execution["source_commit"],
        raw_commit=commit,
        **paired,
        distinct_frontier_states=16,
        total_runs=32,
        retained_endpoint_records=19,
        retained_path_state_records=retained_states,
        returned_path_state_records=returned_states,
        distinct_scalar_states=len(masks),
        point_state_classifications=len(masks) * len(case["points"]),
        program_witnesses=sum(r["witness"] for r in records if r["arm"] == "program"),
        beam_witnesses=sum(r["witness"] for r in records if r["arm"] == "beam"),
        censored_runs=sum(r["censored"] for r in records),
        diagnostic_attempts=attempts,
        diagnostic_queries=queries,
        arm_attempts={a: sum(r["attempts"] for r in records if r["arm"] == a) for a in ARMS},
        records=records,
        retained_complete_cases=3,
        retained_total_cases=4,
        qualified_for_source_comparison=False,
        new_integrated_schedules=0,
        new_driving_episodes=0,
        provider_spend=0,
        source_recovery=None,
        superiority=None,
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
        boundary="Exposed correlated roots from one retained case; checkpoint feasibility under a new common objective and target rule, not original sampled-target replay or integrated success. All queried background states scalar-checked. Bounded misses do not establish infeasibility, required work or the causal value of changed tree allocation.",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--raw-commit", required=True)
    args = parser.parse_args()
    result = check(args.root.resolve(), args.raw_commit)
    write(args.root.resolve() / BASE / "proof/admission.json", result)
    print(
        json.dumps({k: v for k, v in result.items() if k not in ("records", "pairs")}), flush=True
    )
