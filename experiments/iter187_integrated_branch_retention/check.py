"""Independent ancestry, online choice, accounting and registered-mask admission.

The evaluator/proposal/physics checker remains the admitted Iter183 checker.
All registered branches and returned-path masks receive scalar replay. Background
labels of evaluated but unregistered alternatives remain producer evidence.
"""

import argparse
import json
from pathlib import Path
import time

from experiments.iter183_timing_eligibility.check import connection_check
from experiments.iter183_timing_eligibility.eligibility_check import EligibilityReplay
from experiments.iter183_timing_eligibility.comparison import compare
from experiments.iter186_native_branch.check import tree, fields
from experiments.iter179_frontier_continuation_audit.check import scalar_masks
from experiments.iter182_late_frontier_timing.retained import state_key
from experiments.iter164_monitor_time_continuation.path_check import verify_path
from experiments.iter162_source_grouping_qualification.check import completion_check
from .selection_check import choose
from .common import BASE, read, require, rss, write
from .records import committed
from .contract import check_contract


def wiring(events, sequences, result, trace, case, old, plan, deadline):
    nodes, connections, expected_sequences = {}, {}, {}
    native_events, pending, registrations = [], [], []
    request, last_evaluations, choice_due = None, [], False
    attempts, queries, last_elapsed = 0, 1, 0.0
    eligibility = EligibilityReplay(case["geometry"], old, plan["per_run_seconds"])
    final = None
    for row in events:
        require(time.monotonic() < deadline, "checker_deadline")
        kind = row["kind"]
        if kind in ("native_event", "branch_choice", "native_path"):
            require(last_elapsed <= row["elapsed"] <= result["elapsed_seconds"], "event_time")
            last_elapsed = row["elapsed"]
        require(final is None, "events_after_final")
        if kind == "native_event":
            event = row["event"]
            native_events.append(event)
            if event["kind"] == 3:
                require(
                    not pending and not registrations and not choice_due and request is None,
                    "unfinished_connection",
                )
                require(
                    event["node"] in nodes and event["state"] == nodes[event["node"]]["state"],
                    "request_identity",
                )
                request = event
            elif event["kind"] == 0:
                require(
                    not nodes and event["state"] == [*case["geometry"]["reset"], 0], "root_identity"
                )
                nodes[event["node"]] = event
            else:
                require(bool(registrations), "unexpected_registration")
                token, expected_kind = registrations.pop(0)
                require(
                    event["token"] == token and event["kind"] == expected_kind, "registration_token"
                )
                sequence = expected_sequences[token]
                require(
                    event["parent"] == sequence["parent"]
                    and event["steps"] == len(sequence["trace"]) - 1
                    and event["state"]
                    == [*sequence["trace"][-1]["state"], sequence["trace"][-1]["frame"]],
                    "registration_sequence",
                )
                sequence["node"] = event["node"]
                nodes[event["node"]] = event
            continue
        if kind == "native_path":
            final = row
            continue
        if kind == "branch_choice":
            require(choice_due and row["call"] == len(connections), "choice_order")
            connection = connections[row["call"]]
            primary = (
                connection
                if connection["result"] is not None and len(connection["trace"]) > 1
                else None
            )
            extra = choose(last_evaluations, primary, nodes, case["geometry"]["route"])
            require(row["parent"] == request["node"] and row["extra"] == extra, "online_selection")
            tokens = []
            for is_extra, record in ((False, primary), (True, extra)):
                if record is not None:
                    token = 2 * row["call"] - (0 if is_extra else 1)
                    tokens.append(token)
                    expected_sequences[token] = dict(
                        call=row["call"],
                        extra=is_extra,
                        parent=request["node"],
                        node=None,
                        trace=record["trace"],
                    )
            require(row["tokens"] == tokens and type(row["expired"]) is bool, "choice_tokens")
            require(not row["expired"] or row["elapsed"] >= plan["per_run_seconds"], "early_expiry")
            registrations = [] if row["expired"] else [(t, 2 if t % 2 == 0 else 1) for t in tokens]
            request, choice_due = None, False
            continue
        require(
            request is not None and row["call"] == len(connections) + 1 and not choice_due,
            "connection_order",
        )
        if kind != "connection":
            require(kind in ("request", "evaluation"), "event_kind")
            pending.append(row)
            continue
        require(
            row["before"] == request["state"] and row["target"] == request["target"],
            "callback_binding",
        )
        n, q = connection_check(
            row, pending, case, old, plan, plan["attempt_budget"] - attempts, eligibility
        )
        attempts += n
        queries += q
        last_evaluations = [r for r in pending if r["kind"] == "evaluation"]
        pending, choice_due = [], True
        connections[row["call"]] = row
    require(final is not None and not pending and not choice_due, "event_finalization")
    expired = final["stop_code"] == 2
    require(not registrations and request is None or expired, "unregistered_submission")
    native = dict(events=native_events, rows=final["rows"])
    checked_nodes = tree(native)
    require(nodes == checked_nodes, "node_inventory")
    expected_sequences = {str(k): v for k, v in expected_sequences.items() if v["node"] is not None}
    require(sequences == expected_sequences, "registered_sequence_inventory")
    reconstructed, tokens = [trace[0]], []
    for row in final["rows"][1:]:
        token = int(row[6])
        sequence = sequences[str(token)]
        require(
            sequence["parent"] == int(row[8]) and sequence["node"] == int(row[7]), "path_ancestry"
        )
        segment = sequence["trace"]
        require(
            reconstructed[-1]["state"] == segment[0]["state"]
            and reconstructed[-1]["frame"] == segment[0]["frame"],
            "path_join",
        )
        reconstructed.extend(segment[1:])
        tokens.append(token)
    require(fields(trace) == fields(reconstructed), "path_controls")
    require(result["selected_tokens"] == final["selected_tokens"] == tokens, "selected_tokens")
    require(
        result["native_status"] == final["status"]
        and result["native_stop_code"] == final["stop_code"],
        "native_result",
    )
    require(
        type(result["complete"]) is bool and result["complete"] == (final["status"] == 2),
        "complete_status",
    )
    require(
        (not expired or final["status"] == 0 and not final["rows"])
        and (not final["finalization_expired"] or expired),
        "expiry_precedence",
    )
    require(
        attempts == result["attempts"] <= plan["attempt_budget"]
        and result["unused_attempt_budget"] == plan["attempt_budget"] - attempts,
        "outer_budget",
    )
    require(
        queries == result["queries"] and len(connections) == result["directed_calls"],
        "outer_counts",
    )
    require(
        result["accepted_connections"]
        == sum(c["result"] is not None and len(c["trace"]) > 1 for c in connections.values()),
        "accepted_count",
    )
    require(
        result["registered_primary"] == sum(not s["extra"] for s in sequences.values())
        and result["registered_extra"] == sum(s["extra"] for s in sequences.values()),
        "registered_count",
    )
    require(
        eligibility.last_time <= result["elapsed_seconds"] + 1e-9
        and 0 < result["elapsed_seconds"] <= plan["per_run_seconds"] + 5
        and 0 < result["peak_rss_bytes"] <= plan["max_rss_bytes"],
        "resources",
    )
    if result["complete"]:
        require(
            result["stop"] == "model_complete"
            and result["elapsed_seconds"] < plan["per_run_seconds"],
            "late_completion",
        )
    elif expired:
        require(
            result["stop"] == "time_budget"
            and result["elapsed_seconds"] >= plan["per_run_seconds"],
            "early_time_stop",
        )
    else:
        require(
            result["stop"] == "attempt_budget"
            and (
                attempts == plan["attempt_budget"]
                or list(connections.values())[-1]["stop"] == "attempt_reservation"
            ),
            "early_budget_stop",
        )
    return dict(
        native_nodes=len(nodes),
        selected_extra=sum(t % 2 == 0 for t in tokens),
        eligibility=eligibility.summary(),
    )


def case_check(folder, case, old, plan, record, deadline):
    result = json.loads(read(folder, "result.json"))
    require(result == record, "result_binding")
    events = [json.loads(line) for line in read(folder, "events.jsonl").splitlines()]
    trace = json.loads(read(folder / "selected", "trace.json"))
    sequences = json.loads(read(folder, "sequences.json"))
    details = wiring(events, sequences, result, trace, case, old, plan, deadline)
    masks = scalar_masks(folder, case, deadline)
    used = set()
    for segment in [trace, *(s["trace"] for s in sequences.values())]:
        for row in segment:
            key = state_key(row["state"])
            require(
                key in masks and masks[key]["background"] == row["background"],
                "registered_scalar_binding",
            )
            used.add(key)
    require(
        used == set(masks)
        and result["distinct_registered_states"] == len(masks)
        and result["materialization_queries"] == len(trace) + len(masks),
        "materialization_inventory",
    )
    metrics = verify_path(
        trace,
        case["geometry"],
        old,
        case["points"],
        case["ground"],
        lambda i: read(folder / "selected", f"mask_{i:03d}.bin", 40000),
        result["complete"],
        deadline,
    )
    completion_check(metrics, result["complete"], len(case["geometry"]["comparators"]))
    return dict(
        **result,
        **details,
        **metrics,
        final_progress=trace[-1]["route"]["rc"],
        returned_frame=trace[-1]["frame"],
        scalar_classifications=len(masks) * len(case["points"]),
    )


def check(root, commit):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    check_contract(root, plan)
    raw = root / BASE / "proof/search_raw"
    execution = committed(root, raw, commit, plan)
    from .qualify import admitted

    admitted(root, execution["source_commit"], execution["qualification_commit"])
    require(
        execution["children_reaped"] is True and len(execution["records"]) == 4,
        "execution_population",
    )
    old = json.loads(read(root, "experiments/iter153_action_feasibility/PLAN.json"))
    cases = {
        c["id"]: c
        for c in json.loads(read(root, "experiments/iter161_grouping_width_ablation/CASES.json"))
    }
    records = []
    for name, seed, record in zip(plan["cases"], plan["seeds"], execution["records"]):
        require(record["case"] == name and record["seed"] == seed, "case_identity")
        records.append(
            case_check(
                raw / name, cases[name], old, plan, record, started + plan["search_checker_seconds"]
            )
        )
    passes = sum(r["complete"] for r in records)
    require(
        rss() <= plan["max_rss_bytes"]
        and time.monotonic() - started <= plan["search_checker_seconds"],
        "checker_resources",
    )
    comparisons = {}
    for number, name in (
        (178, "iter178_root_domain_consistency"),
        (183, "iter183_timing_eligibility"),
    ):
        baseline = json.loads(read(root, f"experiments/{name}/proof/admission.json"))
        comparisons[str(number)] = compare(records, baseline, number)
        comparisons[str(number)]["boundary"] = (
            "Four exposed development cases, one fixed seed each. Modified branch retention changes later trees and used work. No population, real-time or superiority claim."
        )
    return dict(
        iteration=187,
        phase="closed",
        status="supported" if passes == 4 else "contradicted",
        source_commit=execution["source_commit"],
        raw_commit=commit,
        complete_cases=passes,
        total_cases=4,
        qualified_for_source_comparison=passes == 4,
        comparisons=comparisons,
        total_attempts=sum(r["attempts"] for r in records),
        registered_extra=sum(r["registered_extra"] for r in records),
        scalar_classifications=sum(r["scalar_classifications"] for r in records),
        records=records,
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
        actual_history_intervention=None,
        response_delay=None,
        superiority=None,
        new_driving_episodes=0,
        provider_spend=0,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--raw-commit", required=True)
    a = p.parse_args()
    result = check(a.root.resolve(), a.raw_commit)
    write(a.root.resolve() / BASE / "proof/admission.json", result)
    print(json.dumps({k: v for k, v in result.items() if k not in ("records", "comparisons")}))
