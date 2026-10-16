"""Independent all-query scalar replay of conditional continuations."""

import argparse
import copy
from pathlib import Path
import time

from experiments.iter150_cloud_observation.native import parse
from experiments.iter171_centered_shooting.runtime import identity as runtime_identity
from experiments.iter179_frontier_continuation_audit.check import scalar_masks
from experiments.iter183_timing_eligibility.check import connection_check
from experiments.iter183_timing_eligibility.eligibility_check import EligibilityReplay
from experiments.iter182_late_frontier_timing.retained import state_key
from .common import BASE, document, read, write, require, rss
from .retained import load, OLD, PREVIOUS, identity, conditional_plan
from .records import committed
from .contract import check_plan
from .audit_check import admitted
from .replay import native_binding, path_check, certificates_check, classify


def budget_check(result, settings, connections, attempts, elapsed):
    require(
        attempts == result["attempts"] <= settings["attempt_budget"]
        and result["unused_attempt_budget"] == settings["attempt_budget"] - attempts,
        "outer_attempt_budget",
    )
    require(
        type(elapsed) in (int, float) and 0 < elapsed <= settings["per_run_seconds"] + 5,
        "outer_wall_budget",
    )
    require(
        type(result["complete"]) is bool and result["complete"] == (result["native_status"] == 2),
        "exact_completion_status",
    )
    if result["complete"]:
        require(result["stop"] == "model_complete", "complete_stop")
    elif result["stop"] == "attempt_budget":
        require(
            attempts == settings["attempt_budget"]
            or list(connections.values())[-1]["stop"] == "attempt_reservation",
            "attempt_stop",
        )
    else:
        require(
            result["stop"] == "time_budget" and elapsed >= settings["per_run_seconds"], "time_stop"
        )


def probe_check(folder, path, record, case, old, settings, deadline):
    result = document(folder, "result.json")
    require(result == record, "result_binding")
    masks = scalar_masks(folder, case, deadline)
    conditional_case = copy.deepcopy(case)
    last = path["trace"][-1]
    conditional_case["geometry"]["reset"] = last["state"]
    eligibility = EligibilityReplay(conditional_case["geometry"], old, settings["per_run_seconds"])
    events = [parse(line) for line in read(folder, "events.jsonl").splitlines()]
    nodes = {tuple([*last["state"], last["frame"]])}
    pending, connections, native, attempts, queries, used = [], {}, [], 0, 1, set()
    for row in events:
        require(time.monotonic() < deadline, "checker_deadline")
        if row["kind"] == "native_path":
            native.append(row)
            continue
        require(row["call"] == len(connections) + 1, "connection_order")
        if row["kind"] != "connection":
            pending.append(row)
            continue
        require(tuple(row["before"]) in nodes, "conditional_tree_parent")
        n, q = connection_check(
            row,
            pending,
            conditional_case,
            old,
            settings,
            settings["attempt_budget"] - attempts,
            eligibility,
        )
        for trial in pending:
            if trial["kind"] == "evaluation":
                for state in trial["trace"]:
                    if state["background"] is not None:
                        key = state_key(state["state"])
                        require(
                            key in masks and masks[key]["background"] == state["background"],
                            "all_query_scalar_binding",
                        )
                        used.add(key)
        for state in row.get("trace", []):
            if state["background"] is not None:
                key = state_key(state["state"])
                require(
                    key in masks and masks[key]["background"] == state["background"],
                    "connection_scalar_binding",
                )
                used.add(key)
        attempts += n
        queries += q
        connections[row["call"]] = row
        pending = []
        if row["result"] is not None and len(row["trace"]) > 1:
            endpoint = row["trace"][-1]
            nodes.add(tuple([*endpoint["state"], endpoint["frame"]]))
    require(not pending and len(native) == 1 and events[-1] is native[0], "event_finalization")
    suffix = document(folder, "suffix.json")
    combined = document(folder, "trace.json")
    native_binding(native[0], connections, suffix, last["state"], last["frame"], old)
    require(
        native[0]["status"] == result["native_status"]
        and native[0]["selected_connections"] == result["selected_connections"],
        "native_status",
    )
    require(combined == path["trace"] + suffix[1:], "preserved_full_prefix")
    keys = [state_key(r["state"]) for r in combined]
    checks = path_check(combined, keys, case, old, masks)
    used.update(keys)
    require(used == set(masks), "unused_query_materialization")
    require(result["complete"] == (combined[-1]["route"]["rc"] >= 1), "false_route_completion")
    require(
        queries == result["queries"] and len(connections) == result["directed_calls"],
        "conditional_search_counts",
    )
    accepted = sum(c["result"] is not None and len(c["trace"]) > 1 for c in connections.values())
    require(result["accepted_connections"] == accepted, "conditional_edge_count")
    require(
        result["query_calls"] == queries + len(suffix)
        and result["path_queries"] == len(suffix)
        and result["distinct_scalar_candidates"] == len(masks),
        "query_accounting",
    )
    require(
        eligibility.last_time <= result["elapsed_seconds"] + 1e-9
        and 0 < result["peak_rss_bytes"] <= 1073741824,
        "conditional_resources",
    )
    budget_check(result, settings, connections, attempts, result["elapsed_seconds"])
    progress, premature = certificates_check(path["certificates"], last, case, old)
    censored = result["stop"] == "time_budget"
    label = classify(result["complete"], progress, premature, censored)
    return dict(
        root_identity=list(identity(path)),
        classification=label,
        full_route_continuation=result["complete"],
        censored=censored,
        progress_excluded=progress,
        premature_excluded=premature,
        attempts=attempts,
        directed_calls=len(connections),
        accepted_connections=accepted,
        returned_frame=combined[-1]["frame"],
        returned_progress=combined[-1]["route"]["rc"],
        checkpoint_checks=checks,
        verified_states=len(combined),
        distinct_scalar_states=len(masks),
        scalar_classifications=len(masks) * len(case["points"]),
        charged_wall_seconds=result["charged_wall_seconds"],
        wall_overrun_seconds=max(0, result["charged_wall_seconds"] - 120),
        stop=result["stop"],
        eligibility=eligibility.summary(),
    )


def check(root, commit):
    started = time.monotonic()
    plan = document(root, BASE / "PLAN.json")
    check_plan(root, plan)
    require(
        runtime_identity() == document(root, BASE / "RUNTIME.json")["python_runtime"],
        "checker_runtime",
    )
    raw = root / BASE / "proof/search_raw"
    execution = committed(root, raw, commit, plan)
    audit, audit_hash = admitted(root, execution["audit_admission_commit"], plan)
    require(
        audit_hash == execution["audit_admission_sha256"]
        and audit["source_commit"] == execution["source_commit"],
        "admitted_prefix_identity",
    )
    case, _, _, _, maxima = load(root, plan)
    paths = document(root, BASE / "proof/audit_retry_raw/paths.json")
    old = document(root, OLD)
    parent = document(root, PREVIOUS + "PLAN.json")
    require(
        len(execution["records"]) == 3
        and execution["children_reaped"] is True
        and execution["new_integrated_schedules"] == 0
        and execution["conditional_searches"] == 3,
        "search_population",
    )
    rows = []
    for i, (maximum, result) in enumerate(zip(maxima, execution["records"])):
        path = next(p for p in paths if identity(p) == identity(maximum))
        settings = conditional_plan(
            parent, plan["remaining_attempts"][i], plan["original_wall_seconds"]
        )
        require(
            result["root_identity"] == list(identity(maximum))
            and result["seed"] == plan["seeds"][i]
            and result["start_frame"] == maximum["frame"]
            and result["attempt_ceiling"] == settings["attempt_budget"]
            and result["wall_ceiling"] == settings["per_run_seconds"]
            and result["original_wall_seconds"] == plan["original_wall_seconds"]
            and result["charged_wall_seconds"]
            == result["elapsed_seconds"] + plan["original_wall_seconds"]
            and result["source_prefix_states"] == len(path["trace"]),
            "conditional_identity",
        )
        rows.append(
            probe_check(
                raw / f"probe_{i}",
                path,
                result,
                case,
                old,
                settings,
                started + plan["search_checker_seconds"],
            )
        )
    require(
        time.monotonic() - started <= plan["search_checker_seconds"]
        and rss() <= plan["max_rss_bytes"],
        "checker_resources",
    )
    result = dict(
        iteration=184,
        phase="closed",
        status="supported",
        source_commit=execution["source_commit"],
        raw_commit=commit,
        audit_admission_commit=execution["audit_admission_commit"],
        prefix_records=15,
        probed_roots=3,
        unprobed_records=12,
        full_route_continuations=sum(r["full_route_continuation"] for r in rows),
        demonstrated_constraints=sum(
            r["classification"] == "demonstrated_timing_constraint" for r in rows
        ),
        unresolved_misses=sum(r["classification"] == "unresolved_bounded_miss" for r in rows),
        censored_probes=sum(r["censored"] for r in rows),
        diagnostic_attempts=sum(r["attempts"] for r in rows),
        distinct_scalar_states=sum(r["distinct_scalar_states"] for r in rows),
        scalar_classifications=sum(r["scalar_classifications"] for r in rows),
        records=rows,
        qualified_for_source_comparison=False,
        integrated_complete_cases=3,
        actual_history_intervention=None,
        response_delay=None,
        superiority=None,
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
    )
    write(root / BASE / "proof/admission.json", result)
    print(
        {
            k: result[k]
            for k in [
                "status",
                "full_route_continuations",
                "demonstrated_constraints",
                "unresolved_misses",
                "censored_probes",
                "diagnostic_attempts",
            ]
        },
        flush=True,
    )
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--raw-commit", required=True)
    a = p.parse_args()
    check(a.root.resolve(), a.raw_commit)
