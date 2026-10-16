"""Unchanged all-query conditional replay with corrected bound metadata loading."""

import argparse
from pathlib import Path
import time

from experiments.iter184_discarded_progress.check import probe_check
from experiments.iter184_discarded_progress.retained import identity, conditional_plan
from .common import BASE, document, write, require, rss
from .records import committed
from .context import preflight, check_plan, PRODUCER, RAW
from .audit import admitted


def check(root, commit):
    started = time.monotonic()
    plan = document(root, BASE / "PLAN.json")
    check_plan(plan)
    raw = root / BASE / "proof/search_raw"
    execution = committed(root, raw, commit, plan)
    audit, audit_hash = admitted(root, execution["audit_admission_commit"], plan)
    require(
        audit_hash == execution["audit_admission_sha256"]
        and audit["source_commit"] == execution["source_commit"],
        "admitted_prefix_identity",
    )
    context = preflight(root, execution["source_commit"])
    case, maxima, old, parent = [context[k] for k in ("case", "maxima", "old", "parent")]
    paths = document(context["raw"], "paths.json")
    require(
        len(execution["records"]) == 3
        and execution["children_reaped"] is True
        and execution["new_integrated_schedules"] == 0
        and execution["conditional_searches"] == 3,
        "search_population",
    )
    rows = []
    all_mask_keys = set()
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
        all_mask_keys.update(r["key"] for r in document(raw / f"probe_{i}/masks", "states.json"))
    require(
        time.monotonic() - started <= plan["search_checker_seconds"]
        and rss() <= plan["max_rss_bytes"],
        "checker_resources",
    )
    result = dict(
        iteration=185,
        phase="closed",
        status=(
            "supported"
            if any(r["full_route_continuation"] for r in rows)
            else "inconclusive"
            if any(r["censored"] for r in rows)
            else "null"
        ),
        admission_status="supported",
        prefix_producer_source_commit=PRODUCER,
        prefix_raw_commit=RAW,
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
        distinct_scalar_states=len(all_mask_keys),
        scalar_states_checked=sum(r["distinct_scalar_states"] for r in rows),
        unique_scalar_classifications=len(all_mask_keys) * len(case["points"]),
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
