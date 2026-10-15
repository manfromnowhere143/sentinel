"""Independent retained-mask replay, path/accounting admission and necessary bounds."""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import time

import numpy as np

from experiments.iter155_background_witness.geometry import ground_height, vertices, count_points
from experiments.iter171_centered_shooting.runtime import identity
from .common import BASE, document, read, require, rss, sha, write
from .contract import check_plan
from .records import committed
from .retained import load, OLD, through_first_rejection, state_key
from .replay import row_check, path_binding, path_check, probe_check
from .bound_check import check_bound


def scalar_masks(raw, case, deadline):
    rows = document(raw / "masks", "states.json")
    require(isinstance(rows, list) and 0 < len(rows) <= 10000, "mask_population")
    masks = {}
    for row in rows:
        require(time.monotonic() < deadline, "checker_deadline")
        require(set(row) == {"key", "state", "background"}, "mask_record_schema")
        state, key = row["state"], row["key"]
        require(
            len(state) == 5 and all(type(v) in (int, float) and math.isfinite(v) for v in state),
            "mask_state",
        )
        require(key == state_key(state) and key not in masks, "mask_identity")
        height, _ = ground_height(case["ground"], state[1], state[0])
        actual = count_points(case["points"], vertices([state[1], height, state[0]], state[2]))
        packed = np.packbits(np.asarray(actual["mask"], dtype=bool), bitorder="little").tobytes()
        require(read(raw / "masks", key + ".bin", 40000) == packed, "scalar_mask")
        expected = {k: actual[k] for k in ("count", "certain_inside", "possible_inside")}
        expected.update(
            mask_sha256=sha(packed),
            decision="clear"
            if actual["possible_inside"] <= 100
            else ("collision" if actual["certain_inside"] > 100 else "numerically_ambiguous"),
        )
        require(row["background"] == expected, "scalar_counts")
        masks[key] = row
        require(rss() <= 1073741824, "checker_memory")
    require(
        {p.name for p in (raw / "masks").iterdir()}
        == {"states.json", *(k + ".bin" for k in masks)},
        "mask_inventory",
    )
    return masks


def classify(witness, excluded, censored):
    require(all(type(v) is bool for v in (witness, excluded, censored)), "classification_type")
    require(not (witness and excluded), "bound_false_exclusion")
    return (
        "verified_continuation"
        if witness
        else (
            "progress_excluded"
            if excluded
            else ("unobserved_continuation" if censored else "bounded_miss")
        )
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
    case, connections, selected, trials = load(root, plan)
    old = json.loads(read(root, OLD))
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
    require(len(prior) == 16, "distinct_frontier")
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
        censored = probe["result"]["stop"] == "time_budget"
        if censored:
            require(
                execution["probe_envelope_seconds"] >= plan["aggregate_search_seconds"],
                "probe_early_censor",
            )
        label = classify(witness, excluded, censored)
        records.append(
            dict(
                call=probe["call"],
                start_frame=last["frame"],
                classification=label,
                checkpoint_continuation=witness,
                progress_excluded=excluded,
                censored=censored,
                stop=probe["result"]["stop"],
                attempts=probe["result"]["attempts"],
                returned_frame=combined[-1]["frame"],
            )
        )
        attempted += probe["result"]["attempts"]
        combined_states += len(combined)
        used.update(probe["masks"])
    require(used == set(masks), "unused_materialization")
    require(
        execution["new_motion_searches"] == 16
        and execution["new_integrated_schedules"] == 0
        and execution["diagnostic_attempts"] == attempted <= plan["maximum_total_attempts"]
        and execution["distinct_masks"] == len(masks),
        "audit_scope",
    )
    require(
        identity() == runtime and rss() <= plan["max_rss_bytes"] and time.monotonic() < deadline,
        "checker_resources",
    )
    witnesses = sum(r["checkpoint_continuation"] for r in records)
    censored = sum(r["censored"] for r in records)
    return dict(
        iteration=179,
        phase="closed",
        analysis_status="exploratory",
        status="supported" if witnesses else ("inconclusive" if censored else "null"),
        claim="At least one retained late bend-right state admits a scalar-verified continuation through checkpoint frame 16 under the frozen diagnostic probe.",
        source_commit=execution["source_commit"],
        raw_commit=commit,
        retained_endpoint_records=19,
        distinct_frontier_states=16,
        retained_path_state_records=verified,
        probe_path_state_records=combined_states,
        distinct_scalar_states=len(masks),
        point_state_classifications=len(masks) * len(case["points"]),
        retained_evaluations=len(evaluations),
        retained_prefix_state_records=prefix_states,
        first_rejections=dict(first_reasons),
        checkpoint_witnesses=witnesses,
        progress_exclusions=sum(r["progress_excluded"] for r in records),
        bounded_misses=sum(r["classification"] == "bounded_miss" for r in records),
        censored_probes=censored,
        diagnostic_attempts=attempted,
        records=records,
        retained_complete_cases=3,
        retained_total_cases=4,
        qualified_for_source_comparison=False,
        new_integrated_schedules=0,
        new_driving_episodes=0,
        provider_spend=0,
        source_recovery=None,
        superiority=None,
        transfer=None,
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
        boundary="Exposed retained frontier and finite diagnostic probes. Progress exclusions are sufficient within the declared numerical model; bounded misses do not prove collision inevitability. Verified checkpoint continuations are not integrated completions. Native ancestry and unselected new-probe background labels remain producer evidence.",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--raw-commit", required=True)
    args = parser.parse_args()
    result = check(args.root.resolve(), args.raw_commit)
    write(args.root.resolve() / BASE / "proof/admission.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "records"}), flush=True)
