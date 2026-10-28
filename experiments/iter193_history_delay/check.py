"""Independent absolute-history, scalar physics, masks and local native replay."""

import argparse
import copy
import json
from pathlib import Path
import time
from experiments.iter153_action_feasibility.check import motion, near
from experiments.iter164_monitor_time_continuation.path_check import verify_path
from experiments.iter162_source_grouping_qualification.check import completion_check
from experiments.iter191_stop_wait_release.wiring import wiring
from experiments.iter191_stop_wait_release.runtime import verify
from .common import BASE, PLANNER, read, require, rss, write, load_source
from .contract import check_contract
from .records import committed


def prefix_check(prefix, history, condition):
    origin, delay = condition["origin"], condition["delay"]
    require(
        len(prefix) == origin + delay + 1 and prefix[: origin + 1] == history[: origin + 1],
        "preserved_history",
    )
    for frame in range(origin + 1, origin + delay + 1):
        row = prefix[frame]
        require(
            row["frame"] == row["id"] == frame
            and row["parent"] == frame - 1
            and row["action"] == history[origin]["action"],
            "held_command",
        )
        near(row["state"], motion(prefix[frame - 1]["state"], history[origin]["action"]))


def local_inputs(case, old, planner, prefix):
    geometry = copy.deepcopy(case["geometry"])
    offset = prefix[-1]["frame"]
    geometry["reset"] = prefix[-1]["state"][:]
    for name, item in geometry["comparators"].items():
        original = case["geometry"]["comparators"][name]["hazard_time"]
        item["hazard_time"] = original - offset / 4
        require(
            item["hazard_time"] > 0 and item["hazard_time"] * 4 == int(item["hazard_time"] * 4),
            "deadline_translation",
        )
    return dict(case, geometry=geometry), dict(planner, max_actions=old["max_actions"] - offset)


def classify(records):
    actual = [r for r in records if r["condition"]["origin"] == 25]
    require(
        len(actual) == 3 and all(type(r["complete"]) is bool for r in records),
        "decision_population",
    )
    if any(r["complete"] for r in actual):
        return "supported"
    return "inconclusive" if any(r["stop"] == "time_budget" for r in actual) else "contradicted"


def case_check(folder, case, old, history, planner, condition, result, deadline):
    require(
        result == json.loads(read(folder, "result.json")) and result["condition"] == condition,
        "result_binding",
    )
    prefix = json.loads(read(folder, "prefix.json"))
    prefix_check(prefix, history, condition)
    joined = json.loads(read(folder / "selected", "trace.json"))
    rejected = any(r["reason"] != "clear" for r in prefix)
    require(rejected == (result["stop"] == "prefix_ineligible"), "prefix_eligibility")
    details = {}
    if rejected:
        require(
            joined == prefix
            and result["complete"] is False
            and result["attempts"] == result["queries"] == 0,
            "ineligible_search",
        )
        require(not (folder / "events.jsonl").exists(), "ineligible_events")
    else:
        local, config = local_inputs(case, old, planner, prefix)
        trace = json.loads(read(folder, "trace.json"))
        sequences = json.loads(read(folder, "sequences.json"))
        events = [json.loads(line) for line in read(folder, "events.jsonl").splitlines()]
        details = wiring(events, sequences, result, trace, local, old, config, deadline, True)
        offset = len(prefix) - 1
        require(
            trace[0]["state"] == prefix[-1]["state"]
            and trace[0]["background"] == prefix[-1]["background"],
            "splice_identity",
        )
        expected = prefix + [
            dict(r, frame=offset + i, id=offset + i, parent=offset + i - 1)
            for i, r in enumerate(trace[1:], 1)
        ]
        require(joined == expected, "absolute_join")
        require(
            result["remaining_actions"] == 401 - offset
            and result["first_new_control_frame"] == offset + 1,
            "absolute_horizon",
        )
        require(0 < result["elapsed_seconds"] <= result["worker_seconds"], "search_worker_clock")
    require(
        result["setup_queries"] == condition["delay"]
        and result["materialization_queries"] == len(joined),
        "auxiliary_queries",
    )
    metrics = verify_path(
        joined,
        case["geometry"],
        old,
        case["points"],
        case["ground"],
        lambda i: read(folder / "selected", f"mask_{i:03d}.bin", 40000),
        result["complete"],
        deadline,
        allow_rejections=rejected,
    )
    if not rejected:
        completion_check(metrics, result["complete"], len(case["geometry"]["comparators"]))
    require(
        {p.name for p in (folder / "selected").iterdir()}
        == {"trace.json", *(f"mask_{i:03d}.bin" for i in range(len(joined)))},
        "mask_inventory",
    )
    return dict(
        **result,
        **details,
        **metrics,
        returned_frame=joined[-1]["frame"],
        returned_progress=joined[-1]["route"]["rc"],
        scalar_classifications=len(joined) * len(case["points"]),
        search_within_tick=None if rejected else result["elapsed_seconds"] <= 0.25,
        worker_within_tick=result["worker_seconds"] <= 0.25,
    )


def check(root, commit):
    started = time.monotonic()
    verify(root)
    plan = json.loads(read(root, BASE / "PLAN.json"))
    check_contract(root, plan)
    raw = root / BASE / "proof/search_raw"
    execution = committed(root, raw, commit, plan)
    require(
        execution["children_reaped"] is True and len(execution["records"]) == 6,
        "execution_population",
    )
    case, old, history = load_source(root)
    planner = json.loads(read(root, PLANNER))
    records = []
    for condition, result in zip(plan["conditions"], execution["records"]):
        require(
            result["worker_seconds"] <= plan["worker_supervisor_seconds"]
            and result["worker_peak_rss_bytes"] <= plan["max_rss_bytes"],
            "worker_resources",
        )
        records.append(
            case_check(
                raw / condition["id"],
                case,
                old,
                history,
                planner,
                condition,
                result,
                started + plan["search_checker_seconds"],
            )
        )
        print(json.dumps(dict(checked=condition["id"], complete=result["complete"])), flush=True)
    require(
        time.monotonic() - started <= plan["search_checker_seconds"]
        and rss() <= plan["max_rss_bytes"],
        "checker_resources",
    )
    return dict(
        iteration=193,
        phase="closed",
        status=classify(records),
        source_commit=execution["source_commit"],
        raw_commit=commit,
        conditions=6,
        actual_first_fire_conditions=3,
        actual_first_fire_completions=sum(
            r["complete"] and r["condition"]["origin"] == 25 for r in records
        ),
        earlier_completions=sum(r["complete"] and r["condition"]["origin"] == 23 for r in records),
        censored_searches=sum(r["stop"] == "time_budget" for r in records),
        ineligible_prefixes=sum(r["stop"] == "prefix_ineligible" for r in records),
        total_attempts=sum(r["attempts"] for r in records),
        total_queries=sum(r["queries"] for r in records),
        scalar_classifications=sum(r["scalar_classifications"] for r in records),
        records=records,
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
        new_driving_episodes=0,
        provider_spend=0,
        native_execution=None,
        online_recovery=None,
        superiority=None,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--raw-commit", required=True)
    a = p.parse_args()
    result = check(Path.cwd(), a.raw_commit)
    write(Path.cwd() / BASE / "proof/admission.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "records"}))
