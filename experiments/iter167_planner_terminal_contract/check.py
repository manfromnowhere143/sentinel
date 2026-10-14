"""Independent scalar selected-path admission and budget/edge accounting."""

import argparse
import json
from pathlib import Path
import time

from experiments.iter164_monitor_time_continuation.path_check import verify_path
from experiments.iter162_source_grouping_qualification.check import completion_check
from .common import BASE, read, require, rss, write
from .records import committed


def check(root, commit):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    raw = root / BASE / "proof/search_raw"
    execution = committed(root, raw, commit, plan)
    old = json.loads(read(root, "experiments/iter153_action_feasibility/PLAN.json"))
    cases = json.loads(read(root, "experiments/iter161_grouping_width_ablation/CASES.json"))
    records = []
    require(len(execution["records"]) == len(plan["cases"]) == 4, "case_count")
    for name, seed, recorded in zip(plan["cases"], plan["seeds"], execution["records"]):
        case = next(c for c in cases if c["id"] == name)
        folder = raw / name
        result = json.loads(read(folder, "result.json"))
        require(
            result == recorded and result["case"] == name and result["seed"] == seed, "case_binding"
        )
        require(0 < result["peak_rss_bytes"] <= plan["max_rss_bytes"], "worker_memory")
        attempts = [json.loads(x) for x in read(folder, "attempts.jsonl").splitlines()]
        expansions = [json.loads(x) for x in read(folder, "expansions.jsonl").splitlines()]
        require(len(attempts) == result["attempts"] <= plan["attempt_budget"], "attempt_budget")
        require([r["id"] for r in attempts] == list(range(1, len(attempts) + 1)), "attempt_order")
        require(
            result["queries"] == 1 + sum(r["background"] is not None for r in attempts),
            "query_count",
        )
        require(
            len(expansions) == result["directed_calls"]
            and [r["call"] for r in expansions] == list(range(1, len(expansions) + 1)),
            "expansion_count",
        )
        chosen = {r["selected"] for r in expansions if r["selected"] is not None}
        require(
            all(1 <= i <= len(attempts) and attempts[i - 1]["reason"] == "clear" for i in chosen),
            "chosen_valid",
        )
        trace = json.loads(read(folder / "selected", "trace.json"))
        require(len(trace) <= plan["max_actions"] + 1, "horizon")
        require(
            result["path_queries"] == result["materialization_queries"] == len(trace),
            "path_queries",
        )
        for previous, row in zip(trace, trace[1:]):
            require(
                any(
                    attempts[i - 1]["before"] == [*previous["state"], previous["frame"]]
                    and attempts[i - 1]["action"] == row["action"]
                    and attempts[i - 1]["state"] == row["state"]
                    and attempts[i - 1]["frame"] == row["frame"]
                    for i in chosen
                ),
                "native_selected_edge",
            )
        require(
            type(result["complete"]) is bool
            and result["complete"] == (result["native_status"] == 2),
            "exact_status",
        )
        if not result["complete"]:
            require(result["stop"] in ["attempt_budget", "time_budget"], "miss_stop")
            require(
                (result["attempts"] == plan["attempt_budget"])
                if result["stop"] == "attempt_budget"
                else result["elapsed_seconds"] >= plan["per_run_seconds"],
                "budget_stopping",
            )
        require(0 < result["elapsed_seconds"] <= plan["per_run_seconds"] + 5, "run_time")
        metrics = verify_path(
            trace,
            case["geometry"],
            old,
            case["points"],
            case["ground"],
            lambda i: read(folder / "selected", f"mask_{i:03d}.bin", 40000),
            result["complete"],
            started + plan["search_checker_seconds"],
        )
        completion_check(metrics, result["complete"], len(case["geometry"]["comparators"]))
        records.append(dict(**result, **metrics, final_progress=trace[-1]["route"]["rc"]))
    require(time.monotonic() - started <= plan["search_checker_seconds"], "checker_deadline")
    require(rss() <= plan["max_rss_bytes"], "checker_memory")
    passes = sum(r["complete"] for r in records)
    return dict(
        iteration=167,
        phase="closed",
        status="supported" if passes == 4 else "contradicted",
        claim="This fixed released control-RRT adapter completes all four disclosed qualification cases within the same 18,000-transition, 120-second, 96-action envelope as Iter161.",
        source_commit=execution["source_commit"],
        raw_commit=commit,
        qualified_for_source_comparison=passes == 4,
        complete_cases=passes,
        total_cases=4,
        records=records,
        point_state_classifications=sum(
            r["verified_states"] * len(next(c for c in cases if c["id"] == r["case"])["points"])
            for r in records
        ),
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
        source_recovery=None,
        superiority=None,
        transfer=None,
        new_driving_episodes=0,
        provider_spend=0,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--raw-commit", required=True)
    a = p.parse_args()
    root = a.root.resolve()
    result = check(root, a.raw_commit)
    write(root / BASE / "proof/admission.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "records"}), flush=True)
