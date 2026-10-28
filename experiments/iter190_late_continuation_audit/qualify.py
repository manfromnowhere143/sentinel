"""Pre-freeze replay of the three previously admitted successful paths."""

import json
import time
from pathlib import Path
from experiments.iter164_monitor_time_continuation.path_check import verify_path
from experiments.iter182_late_frontier_timing.bound import progress_bound
from experiments.iter182_late_frontier_timing.bound_check import check_bound
from experiments.iter188_early_timing_feasibility.bound import certificate
from experiments.iter188_early_timing_feasibility.bound_check import verify as check_completion
from .common import CASES, OLD, PREVIOUS, read, require


def retained_successes(root):
    old = json.loads(read(root, OLD))
    cases = {c["id"]: c for c in json.loads(read(root, CASES))}
    previous = json.loads(read(root, PREVIOUS / "proof/admission.json"))
    results = []
    checks = 0
    started = time.monotonic()
    for record in previous["records"]:
        if not record["complete"]:
            continue
        case = cases[record["case"]]
        folder = root / PREVIOUS / "proof/search_raw" / record["case"] / "selected"
        trace = json.loads(read(folder, "trace.json"))
        metrics = verify_path(
            trace,
            case["geometry"],
            old,
            case["points"],
            case["ground"],
            lambda i: read(folder, f"mask_{i:03d}.bin", 40000),
            True,
            started + 120,
        )
        for row in trace:
            if 24 <= row["frame"] < 32:
                p = progress_bound(row["state"], row["frame"], case["geometry"], old, 32)
                c = certificate(row["state"], row["frame"], case["geometry"], old)
                require(
                    not check_bound(p, row["state"], row["frame"], case["geometry"], old, 32),
                    "success_progress_excluded",
                )
                require(
                    not check_completion(c, row["state"], row["frame"], case["geometry"], old),
                    "success_completion_excluded",
                )
                checks += 1
        results.append(dict(case=record["case"], verified_states=metrics["verified_states"]))
    require(len(results) == 3, "successful_control_population")
    return dict(
        status="supported",
        paths=results,
        timing_control_states=checks,
        elapsed_seconds=time.monotonic() - started,
        new_retained_root_probes=0,
    )


if __name__ == "__main__":
    print(json.dumps(retained_successes(Path.cwd())))
