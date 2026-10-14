"""Independent replay of the correction, with both frozen prior comparators."""

import argparse
import json
from pathlib import Path
import time
from experiments.iter168_control_connector.check import verify_trace
from experiments.iter169_full_horizon_control.check import accounting
from .binding import verify_comparison
from .common import BASE, OLD, read, require, rss, write
from .records import committed


def check(root, commit):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    verify_comparison(root, plan)
    raw = root / BASE / "proof/search_raw"
    execution = committed(root, raw, commit, plan)
    require(
        json.loads(read(raw, "runtime.json")) == json.loads(read(root, BASE / "RUNTIME.json")),
        "runtime_record",
    )
    cases = json.loads(read(root, "experiments/iter168_control_connector/CASES.json"))
    old = json.loads(read(root, OLD))
    require(
        [c["id"] for c in cases] == plan["cases"] and len(execution["records"]) == len(cases),
        "case_population",
    )
    prior = json.loads(read(root, "experiments/iter168_control_connector/proof/admission.json"))
    require(
        prior["source_commit"] == plan["comparator_source_commit"]
        and prior["raw_commit"] == plan["comparator_raw_commit"],
        "comparator_identity",
    )
    baseline = [r for r in prior["records"] if r["depth"] == 2]
    require([r["case"] for r in baseline] == plan["cases"], "comparator_population")
    previous = json.loads(
        read(root, "experiments/iter169_full_horizon_control/proof/admission.json")
    )
    require(
        previous["source_commit"] == plan["previous_source_commit"]
        and previous["raw_commit"] == plan["previous_raw_commit"],
        "previous_identity",
    )
    require([r["case"] for r in previous["records"]] == plan["cases"], "previous_population")
    records = []
    states = points = 0
    for i, case in enumerate(cases):
        require(time.monotonic() - started < plan["search_checker_seconds"], "checker_deadline")
        witness = raw / (case["id"] + "_witness")
        wt = json.loads(read(witness, "trace.json"))
        require([r["action"] for r in wt[1:]] == case["witness_actions"], "witness_actions")
        counts = verify_trace(wt, case, old, lambda f: read(witness, f"mask_{f:03d}.bin"), True)
        states += counts["verified_states"]
        points += counts["verified_states"] * len(case["points"])
        folder = raw / case["id"]
        result = json.loads(read(folder, "result.json"))
        require(result == execution["records"][i] and result["case"] == case["id"], "case_result")
        require(0 < result["elapsed_seconds"] <= plan["per_run_seconds"] + 2, "run_time")
        require(0 < result["peak_rss_bytes"] <= plan["max_rss_bytes"], "run_memory")
        ev = [json.loads(line) for line in read(folder, "evaluations.jsonl").splitlines()]
        req = [json.loads(line) for line in read(folder, "requests.jsonl").splitlines()]
        trace = json.loads(read(folder / "selected", "trace.json"))
        accounting(ev, req, trace, result, case, old, plan)
        metrics = verify_trace(
            trace,
            case,
            old,
            lambda f: read(folder / "selected", f"mask_{f:03d}.bin"),
            result["complete"],
        )
        states += metrics["verified_states"]
        points += metrics["verified_states"] * len(case["points"])
        comparator = (
            root
            / "experiments/iter168_control_connector/proof/search_raw"
            / (case["id"] + "_depth2")
            / "selected"
        )
        ct = json.loads(read(comparator, "trace.json"))
        cm = verify_trace(
            ct, case, old, lambda f: read(comparator, f"mask_{f:03d}.bin"), baseline[i]["complete"]
        )
        states += cm["verified_states"]
        points += cm["verified_states"] * len(case["points"])
        pf = (
            root
            / "experiments/iter169_full_horizon_control/proof/search_raw"
            / case["id"]
            / "selected"
        )
        pt = json.loads(read(pf, "trace.json"))
        pm = verify_trace(
            pt,
            case,
            old,
            lambda f: read(pf, f"mask_{f:03d}.bin"),
            previous["records"][i]["complete"],
        )
        states += pm["verified_states"]
        points += pm["verified_states"] * len(case["points"])
        records.append(
            dict(
                **result,
                **metrics,
                final_state=trace[-1]["state"],
                baseline_complete=baseline[i]["complete"],
                baseline_attempts=baseline[i]["attempts"],
                previous_complete=previous["records"][i]["complete"],
                previous_attempts=previous["records"][i]["attempts"],
            )
        )
    passes = sum(r["complete"] for r in records)
    require(
        time.monotonic() - started <= plan["search_checker_seconds"]
        and rss() <= plan["max_rss_bytes"],
        "checker_resources",
    )
    return dict(
        iteration=170,
        phase="closed",
        status="supported" if passes == len(cases) else "contradicted",
        claim="The full-horizon shooting controller completes all twelve unchanged constructed temporal tasks within the frozen envelope.",
        source_commit=execution["source_commit"],
        raw_commit=commit,
        total_cases=len(cases),
        complete_cases=passes,
        previous_complete_cases=previous["complete_cases"],
        previous_attempts=previous["total_attempts"],
        baseline_complete_cases=sum(r["complete"] for r in baseline),
        total_attempts=sum(r["attempts"] for r in records),
        baseline_attempts=sum(r["attempts"] for r in baseline),
        total_evaluations=sum(r["evaluations"] for r in records),
        cache_hits=sum(r["cache_hits"] for r in records),
        verified_states=states,
        point_state_classifications=points,
        qualified_for_local_tasks=passes == len(cases),
        qualified_for_source_comparison=False,
        records=records,
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
    result = check(a.root.resolve(), a.raw_commit)
    write(a.root.resolve() / BASE / "proof/admission.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "records"}), flush=True)
