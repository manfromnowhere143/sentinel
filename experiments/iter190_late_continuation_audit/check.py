"""Independent all-query, native-population and conditional-budget admission."""

import argparse
import json
import math
from pathlib import Path
import time

from experiments.iter182_late_frontier_timing.replay import row_check
from experiments.iter182_late_frontier_timing.bound_check import check_bound
from experiments.iter188_early_timing_feasibility.bound_check import verify as completion_check
from experiments.iter182_late_frontier_timing.retained import state_key
from .common import BASE, OLD, PREVIOUS, read, require, rss, write
from .contract import check_contract
from .records import committed
from .runtime import verify
from .population_check import load, through_rejection, expansion
from .masks import verify as scalar_masks
from .probe_check import check as arm_check


def path_check(trace, case, old, masks):
    require(
        0 < len(trace) <= 97
        and trace[0]["state"] == case["geometry"]["reset"]
        and trace[0]["action"] is None,
        "path_root",
    )
    used = set()
    for frame, row in enumerate(trace):
        require(type(row["frame"]) is int and row["frame"] == frame, "path_clock")
        if frame:
            require(trace[frame - 1]["route"]["rc"] < 1, "path_after_completion")
        require(
            row_check(row, trace[frame - 1] if frame else row, case, old, masks) == "clear",
            "path_rejected",
        )
        key = state_key(row["state"])
        require(key in masks, "path_mask_missing")
        used.add(key)
    return used


def timing_check(timing, value, cap, seconds, common):
    require(
        set(timing)
        == {
            "method",
            "attempt_cap",
            "wall_cap",
            "common_seconds",
            "charged_seconds",
            "queries",
            "censored",
        },
        "timing_schema",
    )
    require(
        timing["method"] == value["method"]
        and timing["attempt_cap"] == cap
        and timing["wall_cap"] == seconds,
        "timing_budget_identity",
    )
    require(
        type(timing["charged_seconds"]) in (int, float)
        and math.isfinite(timing["charged_seconds"])
        and timing["charged_seconds"] >= common >= 0
        and timing["common_seconds"] == common,
        "charged_wall",
    )
    require(
        timing["queries"] == value["queries"] and type(timing["censored"]) is bool, "timing_queries"
    )
    censored = timing["charged_seconds"] >= seconds or value["stop"] == "time_budget"
    require(timing["censored"] is censored, "timing_censor")
    if value["stop"] == "time_budget":
        require(timing["charged_seconds"] >= seconds, "early_time_stop")
    return not censored


def check(root, commit):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    check_contract(root, plan)
    verify(root)
    raw = root / BASE / "proof/audit_raw"
    execution = committed(root, raw, commit, plan)
    deadline = started + plan["audit_checker_seconds"]
    require(
        execution["children_reaped"] is True and execution["new_integrated_runs"] == 0,
        "audit_scope",
    )
    population, sources = load(root)
    old = json.loads(read(root, OLD))
    admitted = json.loads(read(root, PREVIOUS / "proof/admission.json"))
    missed = {r["case"] for r in admitted["records"] if not r["complete"]}
    records = []
    totals = dict(
        attempts=0, queries=0, scalar_states=0, scalar_classifications=0, retained_evaluations=0
    )
    for case_index, source in enumerate(sources):
        case = source["case"]
        name = case["id"]
        folder = raw / name
        summary = json.loads(read(folder, "summary.json"))
        require(
            execution["cases"][case_index] == summary and summary["case"] == name, "case_summary"
        )
        masks = scalar_masks(folder, case, deadline)
        used = set()
        offline = 0
        members = [r for r in population["records"] if r["case"] == name]
        for record in members:
            used |= path_check(record["trace"], case, old, masks)
            offline += len(record["trace"])
            for evaluation in source["outgoing"].get(record["node"], []):
                rows = through_rejection(evaluation)
                require(
                    rows[0]["state"] == record["state"] and rows[0]["frame"] == record["frame"],
                    "outgoing_root",
                )
                for index, row in enumerate(rows):
                    require(row["frame"] == record["frame"] + index, "outgoing_clock")
                    row_check(row, rows[index - 1] if index else row, case, old, masks)
                    if row["background"] is not None:
                        key = state_key(row["state"])
                        require(key in masks, "outgoing_mask_missing")
                        used.add(key)
                        offline += 1
                totals["retained_evaluations"] += 1
        roots = [r for r in members if r["id"] == r["representative"]]
        require([r["id"] for r in summary["roots"]] == [r["id"] for r in roots], "root_population")
        probe_queries = 0
        for root_record, root_summary in zip(roots, summary["roots"]):
            require(time.monotonic() < deadline, "checker_deadline")
            group = [r for r in members if r["representative"] == root_record["id"]]
            require(
                root_summary["members"] == [r["id"] for r in group]
                and root_summary["node"] == root_record["node"],
                "duplicate_mapping",
            )
            cap = min(plan["per_arm_attempts"], *(r["remaining_attempts"] for r in group))
            seconds = min(plan["per_arm_seconds"], *(r["remaining_seconds"] for r in group))
            target = folder / f"node_{root_record['node']:03d}"
            bounds = json.loads(read(target, "bounds.json"))
            excluded = check_bound(
                bounds["progress"],
                root_record["state"],
                root_record["frame"],
                case["geometry"],
                old,
                32,
            )
            premature = completion_check(
                bounds["completion"],
                root_record["state"],
                root_record["frame"],
                case["geometry"],
                old,
            )
            arms = []
            common = None
            require(len(root_summary["arms"]) == len(plan["arms"]), "arm_population")
            for method, timing in zip(plan["arms"], root_summary["arms"]):
                value = json.loads(read(target, method + ".json"))
                require(value["method"] == method, "arm_order")
                require(
                    timing == json.loads(read(target, method + "-timing.json")), "timing_binding"
                )
                checked = arm_check(value, root_record["trace"], case, old, cap, masks)
                used |= checked["used"]
                common = timing["common_seconds"] if common is None else common
                fits = timing_check(timing, value, cap, seconds, common)
                require(
                    not (checked["checkpoint"] and (excluded or premature)), "bound_false_exclusion"
                )
                if checked["complete"]:
                    suffix = [value["rows"][i] for i in value["complete_ids"]]
                    require(suffix[-1]["frame"] >= 32, "completion_before_checkpoint")
                    for member in group:
                        used |= path_check(member["trace"] + suffix[1:], case, old, masks)
                else:
                    suffix = None
                if checked["checkpoint"]:
                    witness = [value["rows"][i] for i in value["checkpoint_ids"]]
                    used |= path_check(root_record["trace"] + witness[1:], case, old, masks)
                arms.append(
                    dict(
                        method=method,
                        attempts=value["attempts"],
                        queries=value["queries"],
                        charged_seconds=timing["charged_seconds"],
                        censored=not fits,
                        checkpoint_witness=checked["checkpoint"],
                        full_route_witness=checked["complete"],
                        budgeted_checkpoint=checked["checkpoint"] and fits,
                        budgeted_completion=checked["complete"] and fits,
                        stop=value["stop"],
                        completed_frame=suffix[-1]["frame"] if suffix else None,
                        suffix=suffix,
                    )
                )
                totals["attempts"] += value["attempts"]
                probe_queries += value["queries"]
            for member in group:
                row = dict(
                    id=member["id"],
                    case=name,
                    node=member["node"],
                    representative=member["representative"],
                    frame=member["frame"],
                    remaining_attempts=member["remaining_attempts"],
                    remaining_seconds=member["remaining_seconds"],
                    progress_excluded=excluded,
                    premature_completion_excluded=premature,
                    arms=[],
                )
                for arm in arms:
                    suffix = arm["suffix"]
                    public = {k: v for k, v in arm.items() if k != "suffix"}
                    public.update(
                        original_plus_attempts=member["consumed_attempts"] + arm["attempts"],
                        original_plus_seconds=member["charged_original_wall"]
                        + arm["charged_seconds"],
                        expansion=expansion(member, suffix, source) if suffix else None,
                    )
                    if public["budgeted_completion"]:
                        require(
                            public["original_plus_attempts"] <= 18000
                            and public["original_plus_seconds"] < 120,
                            "original_budget_fit",
                        )
                    row["arms"].append(public)
                records.append(row)
        require(
            used == set(masks) and summary["distinct_states"] == len(masks), "all_query_inventory"
        )
        require(
            summary["offline_queries"] == offline
            and summary["total_queries"] == offline + probe_queries,
            "all_query_counts",
        )
        totals["queries"] += probe_queries
        totals["scalar_states"] += len(masks)
        totals["scalar_classifications"] += len(masks) * len(case["points"])
    require(len(records) == 22 and totals["retained_evaluations"] == 691, "audit_population")
    roots = [r for r in records if r["id"] == r["representative"]]
    successes = [r for r in roots if any(a["budgeted_completion"] for a in r["arms"])]
    missed_successes = [r for r in successes if r["case"] in missed]
    relevant_censor = any(a["censored"] for r in roots if r["case"] in missed for a in r["arms"])
    status = "supported" if missed_successes else ("inconclusive" if relevant_censor else "null")
    require(time.monotonic() < deadline and rss() <= plan["max_rss_bytes"], "checker_resources")
    return dict(
        iteration=190,
        phase="closed",
        status=status,
        source_commit=execution["source_commit"],
        raw_commit=commit,
        node_records=22,
        distinct_roots=21,
        full_route_roots=len(successes),
        full_route_missed_case_roots=len(missed_successes),
        checkpoint_roots=sum(any(a["budgeted_checkpoint"] for a in r["arms"]) for r in roots),
        censored_arms=sum(a["censored"] for r in roots for a in r["arms"]),
        unexpanded_complete_records=sum(
            any(
                a["budgeted_completion"] and a["expansion"] and not a["expansion"]["requested"]
                for a in r["arms"]
            )
            for r in records
        ),
        diagnostic_attempts=totals["attempts"],
        diagnostic_queries=totals["queries"],
        distinct_scalar_states=totals["scalar_states"],
        scalar_classifications=totals["scalar_classifications"],
        retained_evaluations=691,
        records=records,
        integrated_complete_cases=3,
        qualified_for_source_comparison=False,
        new_integrated_runs=0,
        new_driving_episodes=0,
        provider_spend=0,
        actual_history_intervention=None,
        response_delay=None,
        superiority=None,
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--raw-commit", required=True)
    a = p.parse_args()
    value = check(Path.cwd(), a.raw_commit)
    write(Path.cwd() / BASE / "proof/admission.json", value)
    print(json.dumps({k: v for k, v in value.items() if k != "records"}))
