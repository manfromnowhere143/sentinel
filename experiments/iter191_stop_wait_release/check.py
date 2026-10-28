"""Independent complete-population, native, all-query and paired qualification."""

import json
from pathlib import Path
import time
from experiments.iter153_action_feasibility.check import near
from experiments.iter168_control_connector.check import physical
from experiments.iter172_integrated_rrt.check import outcome
from experiments.iter190_late_continuation_audit.masks import verify as scalar_masks
from .callback_check import check as callback_check, query_rows, timing_check
from .common import BASE, OLD, PREVIOUS, read, require, rss, write
from .contract import check_contract
from .fixtures import case as fixture_case
from .population_check import load
from .records import committed
from .runtime import verify
from .wiring import wiring


def path_check(trace, case, old, masks):
    require(
        0 < len(trace) <= 97
        and trace[0]["state"] == case["geometry"]["reset"]
        and trace[0]["action"] is None,
        "path_root",
    )
    final = max(
        (r["hazard_time"] / old["dt"] for r in case["geometry"]["comparators"].values()), default=0
    )
    for frame, row in enumerate(trace):
        require(
            type(row["frame"]) is int
            and type(row["id"]) is int
            and row["frame"] == row["id"] == frame
            and row["parent"] == (frame - 1 if frame else None),
            "path_clock",
        )
        previous = trace[frame - 1] if frame else row
        require(not frame or previous["route"]["rc"] < 1, "path_after_completion")
        require(
            physical(
                previous["state"],
                row["state"],
                row["action"],
                frame,
                dict(case, task=dict(wait_until=0, stop_from=None)),
                old,
            )
            is None,
            "path_physical",
        )
        actual = outcome(row["state"], case["geometry"])
        require(actual["nearest"] == row["route"]["nearest"], "path_route")
        near([actual["distance"], actual["rc"]], [row["route"]["distance"], row["route"]["rc"]])
        require(
            row["reason"] == "clear" and row["background"]["decision"] == "clear", "path_rejected"
        )
        require(actual["rc"] < 1 or frame >= final, "path_premature")
    return query_rows(trace, masks)


def baseline_match(current, original):
    fields = (
        "attempts",
        "queries",
        "evaluations",
        "requests",
        "cache_hits",
        "selected_evaluation",
        "selected_prefix",
        "target_complete",
        "world_complete",
        "unused_attempt_budget",
        "stop",
        "optimizer",
    )
    return all(
        current[k] == original[k]
        for k in ("call", "before", "target", "task", "budget", "trace", "stop")
    ) and all(current["result"][k] == original["result"][k] for k in fields)


def native_admit(folder, label, enabled, root, deadline):
    inputs = json.loads(read(folder, "inputs.json"))
    old = json.loads(read(root, OLD))
    plan = json.loads(read(root, PREVIOUS / "PLAN.json"))
    plan.update(attempt_budget=512, per_run_seconds=10)
    case = fixture_case(label)
    require(inputs == dict(case=case, old=old, plan=plan, enabled=enabled), "native_fixture_inputs")
    result = json.loads(read(folder, "result.json"))
    trace = json.loads(read(folder, "trace.json"))
    sequences = json.loads(read(folder, "sequences.json"))
    events = [json.loads(line) for line in read(folder, "events.jsonl").splitlines()]
    checked = wiring(events, sequences, result, trace, case, old, plan, deadline, enabled)
    masks = scalar_masks(folder, case, deadline)
    used = path_check(trace, case, old, masks)
    for event in events:
        if event["kind"] == "evaluation":
            used |= query_rows(event["trace"], masks)
        elif event["kind"] == "connection" and event["result"] is not None:
            used |= query_rows(event["trace"], masks)
    for sequence in sequences.values():
        used |= query_rows(sequence["trace"], masks)
    require(used == set(masks), "native_query_inventory")
    require(result["complete"] == (trace[-1]["route"]["rc"] >= 1), "native_complete_path")
    feedback = sum(e["kind"] == "request" and e["caller"] == "stop_wait_release" for e in events)
    semantic = {k: v for k, v in result.items() if k not in ("elapsed_seconds", "peak_rss_bytes")}
    return dict(
        fixture=label,
        arm="candidate" if enabled else "baseline",
        complete=result["complete"],
        censored=result["stop"] == "time_budget",
        feedback_requests=feedback,
        attempts=result["attempts"],
        queries=result["queries"],
        scalar_states=len(masks),
        scalar_classifications=len(masks) * len(case["points"]),
        native_nodes=checked["native_nodes"],
        semantic=dict(result=semantic, trace=trace, sequences=sequences),
    )


def classify(records, native):
    actual = [r for r in records if r["kind"] == "original"]
    baseline_reproduced = all(r["baseline_reproduced"] for r in actual)
    losses = sum(r["arms"][0]["complete"] and not r["arms"][1]["complete"] for r in actual)
    left_gains = sum(
        r["case"] == "bend_left" and not r["arms"][0]["complete"] and r["arms"][1]["complete"]
        for r in actual
    )
    controls = all(r["qualified"] for r in native)
    censored = any(a["censored"] for r in actual for a in r["arms"]) or any(
        r["censored"] for r in native
    )
    supported = baseline_reproduced and losses == 0 and left_gains > 0 and controls
    status = "inconclusive" if censored else ("supported" if supported else "contradicted")
    return dict(
        status=status,
        baseline_reproduced=baseline_reproduced,
        original_completion_losses=losses,
        original_left_completion_gains=left_gains,
        constructed_controls_qualified=controls,
    )


def arm_entry(result, timing, payload, record, case, old, planner, arm):
    fits = timing_check(timing, payload, record, planner)
    trace = (
        result["connection"]["trace"] if "trace" in result["connection"] else record["trace"][-1:]
    )
    checkpoints = {
        int(c["hazard_time"] / old["dt"]) for c in case["geometry"]["comparators"].values()
    }
    extra = result["extra"]
    entry = dict(
        arm=arm,
        complete=result["complete"] and fits,
        observed_complete=result["complete"],
        attempts=result["attempts"],
        queries=result["queries"],
        feedback_requests=result["feedback_requests"],
        returned_frame=trace[-1]["frame"],
        returned_progress=trace[-1]["route"]["rc"],
        returned_steps=len(trace) - 1,
        primary_checkpoint_crossings=sum(r["frame"] in checkpoints for r in trace[1:]),
        extra_checkpoint_crossings=sum(r["frame"] in checkpoints for r in extra["trace"][1:])
        if extra
        else 0,
        original_plus_attempts=record["consumed_attempts"] + result["attempts"],
        **timing,
    )
    require(
        entry["original_plus_attempts"] <= planner["attempt_budget"],
        "remaining_attempts",
    )
    return entry


def check(root, commit):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    check_contract(root, plan)
    verify(root)
    raw = root / BASE / "proof/qualification_raw"
    execution = committed(root, raw, commit, plan)
    deadline = started + plan["qualification_checker_seconds"]
    require(
        execution["native_workers"] == 6
        and execution["children_reaped"] is True
        and execution["new_integrated_runs"] == 0,
        "qualification_scope",
    )
    native, native_totals = [], dict(attempts=0, queries=0, states=0, classifications=0)
    for label in plan["native_fixtures"]:
        pair = [
            native_admit(
                raw / "native" / (label + "-" + arm), label, arm == "candidate", root, deadline
            )
            for arm in plan["arms"]
        ]
        parity = pair[0]["semantic"] == pair[1]["semantic"]
        qualified = (
            parity and pair[1]["feedback_requests"] == 0
            if label == "untimed"
            else pair[1]["complete"] and pair[1]["feedback_requests"] > 0
        )
        for result in pair:
            for field, key in (
                ("attempts", "attempts"),
                ("queries", "queries"),
                ("states", "scalar_states"),
                ("classifications", "scalar_classifications"),
            ):
                native_totals[field] += result[key]
            result.pop("semantic")
        native.append(
            dict(
                fixture=label,
                qualified=qualified,
                unchanged_behavior=parity,
                censored=any(r["censored"] for r in pair),
                arms=pair,
            )
        )
    population, cases = load(root)
    old = json.loads(read(root, OLD))
    planner = json.loads(read(root, PREVIOUS / "PLAN.json"))
    expected_schedule = [
        dict(index=i, input_id=r["id"], arm=a)
        for i, r in enumerate(population["records"])
        for a in (plan["arms"] if i % 2 == 0 else reversed(plan["arms"]))
    ]
    require(execution["schedule"] == expected_schedule, "fixed_schedule")
    records, states, classifications, total_attempts, total_queries = [], 0, 0, 0, 0
    for case_index, (name, case) in enumerate(cases.items()):
        folder = raw / name
        summary = json.loads(read(folder, "summary.json"))
        require(
            execution["cases"][case_index] == summary and summary["case"] == name, "case_summary"
        )
        masks = scalar_masks(folder, case, deadline)
        used, offline, queries = set(), 0, 0
        for index, record in enumerate(population["records"]):
            if record["case"] != name:
                continue
            used |= path_check(record["trace"], case, old, masks)
            offline += len(record["trace"])
            target = folder / f"request_{index:03d}"
            arms, reproduced = [], None
            for arm in plan["arms"]:
                require(time.monotonic() < deadline, "checker_deadline")
                payload = json.loads(read(target, arm + ".json"))
                timing = json.loads(read(target, arm + "-timing.json"))
                result = callback_check(
                    payload, record, case, old, planner, masks, arm == "candidate"
                )
                used |= result["used"]
                if record["kind"] == "original" and arm == "baseline":
                    reproduced = baseline_match(result["connection"], record["original_connection"])
                for sequence in payload["sequences"].values():
                    used |= path_check(record["trace"] + sequence["trace"][1:], case, old, masks)
                entry = arm_entry(result, timing, payload, record, case, old, planner, arm)
                arms.append(entry)
                total_attempts += result["attempts"]
                queries += result["queries"]
            records.append(
                dict(
                    index=index,
                    id=record["id"],
                    kind=record["kind"],
                    case=name,
                    parent=record["parent"],
                    members=record["members"],
                    baseline_reproduced=reproduced,
                    arms=arms,
                )
            )
        require(
            used == set(masks) and summary["distinct_states"] == len(masks), "case_query_inventory"
        )
        require(
            summary["offline_queries"] == offline and summary["total_queries"] == offline + queries,
            "case_query_counts",
        )
        states += len(masks)
        classifications += len(masks) * len(case["points"])
        total_queries += queries
    records.sort(key=lambda r: r["index"])
    require(
        len(records) == 44 and [r["index"] for r in records] == list(range(44)),
        "admitted_population",
    )
    verdict = classify(records, native)
    require(time.monotonic() < deadline and rss() <= plan["max_rss_bytes"], "checker_resources")
    return dict(
        iteration=191,
        phase="closed",
        **verdict,
        source_commit=execution["source_commit"],
        raw_commit=commit,
        original_requests=23,
        goal_requests=21,
        paired_requests=44,
        original_baseline_completions=sum(
            r["arms"][0]["complete"] for r in records if r["kind"] == "original"
        ),
        original_candidate_completions=sum(
            r["arms"][1]["complete"] for r in records if r["kind"] == "original"
        ),
        goal_baseline_completions=sum(
            r["arms"][0]["complete"] for r in records if r["kind"] == "goal"
        ),
        goal_candidate_completions=sum(
            r["arms"][1]["complete"] for r in records if r["kind"] == "goal"
        ),
        retained_attempts=total_attempts,
        retained_queries=total_queries,
        native_attempts=native_totals["attempts"],
        native_queries=native_totals["queries"],
        distinct_scalar_states=states + native_totals["states"],
        scalar_classifications=classifications + native_totals["classifications"],
        censored_arms=sum(a["censored"] for r in records for a in r["arms"]),
        native=native,
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
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--raw-commit", required=True)
    a = p.parse_args()
    value = check(Path.cwd(), a.raw_commit)
    write(Path.cwd() / BASE / "proof/admission.json", value)
    print(json.dumps({k: v for k, v in value.items() if k not in ("records", "native")}))
