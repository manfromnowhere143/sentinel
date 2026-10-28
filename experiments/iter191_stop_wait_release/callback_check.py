"""Independent local callback transport, scalar-query and deadline admission."""

import math
from experiments.iter182_late_frontier_timing.retained import state_key
from experiments.iter187_integrated_branch_retention.selection_check import choose
from experiments.iter189_uniform_timing_eligibility.eligibility_check import EligibilityReplay
from .common import require
from .replay import connection_check


def query_rows(rows, masks):
    used = set()
    for row in rows:
        if row["background"] is not None:
            key = state_key(row["state"])
            require(
                key in masks and masks[key]["background"] == row["background"],
                "all_query_scalar_binding",
            )
            used.add(key)
    return used


def check(payload, record, case, old, plan, masks, enabled):
    require(
        payload["input_id"] == record["id"]
        and payload["arm"] == ("candidate" if enabled else "baseline"),
        "callback_identity",
    )
    events = payload["events"]
    require(
        len(events) >= 2
        and events[-1]["kind"] == "branch_choice"
        and events[-2]["kind"] == "connection",
        "callback_event_end",
    )
    require(all(e["call"] == record["call"] for e in events), "callback_call")
    connection, choice = events[-2:]
    require(
        connection["before"] == record["before"] and connection["target"] == record["target"],
        "callback_inputs",
    )
    eligibility = EligibilityReplay(case["geometry"], old, plan["per_run_seconds"])
    attempts, queries = connection_check(
        connection,
        events[:-2],
        case,
        old,
        plan,
        plan["attempt_budget"] - record["consumed_attempts"],
        eligibility,
        enabled,
    )
    require(payload["attempts"] == attempts and payload["queries"] == queries, "callback_counts")
    evaluations = [e for e in events[:-2] if e["kind"] == "evaluation"]
    primary = (
        connection if connection["result"] is not None and len(connection["trace"]) > 1 else None
    )
    extra = choose(evaluations, primary, record["nodes"], case["geometry"]["route"])
    require(
        choice["parent"] == record["parent"] and choice["extra"] == extra,
        "callback_extra_selection",
    )
    require(
        type(choice["expired"]) is bool
        and type(choice["elapsed"]) in (int, float)
        and math.isfinite(choice["elapsed"]),
        "callback_clock",
    )
    require(
        choice["elapsed"] >= record["charged_original_wall"]
        and (not choice["expired"] or choice["elapsed"] >= plan["per_run_seconds"]),
        "callback_expiry",
    )
    expected, sequences = [], {}
    for is_extra, row in ((False, primary), (True, extra)):
        if row is None:
            continue
        trace = row["trace"]
        token = 2 * record["call"] - (0 if is_extra else 1)
        expected.append(
            dict(
                parent=record["parent"],
                token=token,
                steps=len(trace) - 1,
                flags=3,
                before=[*trace[0]["state"], trace[0]["frame"]],
                after=[*trace[-1]["state"], trace[-1]["frame"]],
            )
        )
        sequences[str(token)] = dict(
            call=record["call"], extra=is_extra, parent=record["parent"], node=None, trace=trace
        )
    require(
        choice["tokens"] == [r["token"] for r in expected] and payload["sequences"] == sequences,
        "callback_sequences",
    )
    require(payload["branches"] == ([] if choice["expired"] else expected), "callback_transport")
    used = query_rows([r for e in evaluations for r in e["trace"]], masks)
    if connection["result"] is not None:
        used |= query_rows(connection["trace"], masks)
    elapsed = payload["before_payload_seconds"]
    require(
        type(elapsed) in (int, float)
        and math.isfinite(elapsed)
        and elapsed >= 0
        and choice["elapsed"] <= record["charged_original_wall"] + elapsed,
        "callback_elapsed",
    )
    complete = primary is not None and primary["result"]["world_complete"] and not choice["expired"]
    return dict(
        connection=connection,
        primary=primary,
        extra=extra,
        complete=bool(complete),
        attempts=attempts,
        queries=queries,
        used=used,
        feedback_requests=sum(
            e["kind"] == "request" and e["caller"] == "stop_wait_release" for e in events
        ),
        expired=choice["expired"],
    )


def timing_check(timing, payload, record, plan):
    require(
        set(timing) == {"charged_seconds", "original_plus_seconds", "censored"}, "timing_schema"
    )
    seconds = timing["charged_seconds"]
    require(
        type(seconds) in (int, float)
        and math.isfinite(seconds)
        and seconds >= payload["before_payload_seconds"] >= 0,
        "charged_seconds",
    )
    require(
        timing["original_plus_seconds"] == record["charged_original_wall"] + seconds,
        "original_wall_debit",
    )
    censored = (
        timing["original_plus_seconds"] >= plan["per_run_seconds"]
        or payload["events"][-1]["expired"]
    )
    require(type(timing["censored"]) is bool and timing["censored"] is censored, "timing_censor")
    return not censored
