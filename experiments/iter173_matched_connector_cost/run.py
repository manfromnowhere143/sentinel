"""One frozen paired schedule; isolated processes, raw committed before replay."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

from experiments.iter153_action_feasibility.geometry import route_outcome
from experiments.iter153_action_feasibility.planner import transition
from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import query_for, retain_trace
from .common import BASE, OLD, read, require, write
from .records import initialize, finish, failure
from .runtime import verify


def schedule(requests, cases):
    population = [("request", r["id"]) for r in requests]
    population += [("constructive", c["id"]) for c in cases]
    return [(kind, identity, arm) for index, (kind, identity) in enumerate(population)
            for arm in (["shooting", "forward"] if index % 2 == 0 else ["forward", "shooting"])]


def remaining_resources(output, plan, started):
    remaining = plan["search_producer_seconds"] - (time.monotonic()-started)
    require(remaining > 0, "producer_deadline")
    used = sum(p.stat().st_size for p in output.rglob("*") if p.is_file())
    require(used < plan["max_output_bytes"] - 17000000, "output_reservation")
    return remaining


def retain_controls(output, case, actions, old):
    query = query_for(case)
    state, rows = case["geometry"]["reset"], []
    for frame, action in enumerate([None, *actions]):
        if action is not None:
            state = transition(state, action, old)
        background = summary(query(state))
        rows.append(dict(id=frame, frame=frame, parent=frame-1 if frame else None,
                         action=action, state=state,
                         route=route_outcome(state, case["geometry"]["route"]),
                         background=background, reason=background["decision"]))
    retain_trace(output, rows, query)


def run(root, source):
    started = time.monotonic()
    verify(root)
    output = root / BASE / "proof/search_raw"
    plan = initialize(root, output, source, "search")
    records = []
    try:
        write(output / "runtime.json", verify(root))
        cases = json.loads(read(root, BASE / "CASES.json"))
        requests = json.loads(read(root, BASE / "REQUESTS.json"))["requests"]
        old = json.loads(read(root, OLD))
        for case in cases:
            retain_controls(output / (case["id"] + "_witness"), case, case["witness_actions"], old)
            if case["id"].startswith("detour_"):
                retain_controls(output / (case["id"] + "_straight"), case, [[0, 0]] * 16, old)
        for kind, identity, arm in schedule(requests, cases):
            remaining = remaining_resources(output, plan, started)
            folder = output / (identity + "_" + arm)
            folder.mkdir()
            with (folder / "stdout.txt").open("xb") as out, (folder / "stderr.txt").open("xb") as err:
                process = subprocess.Popen([
                    sys.executable, "-m", "experiments.iter173_matched_connector_cost.worker",
                    "--root", str(root), "--output", str(folder), "--kind", kind,
                    "--identity", identity, "--arm", arm,
                ], cwd=root, stdout=out, stderr=err)
                try:
                    code = process.wait(timeout=min(remaining, plan["per_run_seconds"] + 15))
                except BaseException:
                    process.kill()
                    process.wait()
                    raise
            require(code == 0, "worker_failed:" + identity + ":" + arm)
            result = json.loads(read(folder, "result.json"))
            records.append(result)
            print(json.dumps(dict(id=identity, arm=arm, attempts=result["attempts"],
                                  complete=result.get("complete", result.get("target_complete")))), flush=True)
        verify(root)
        finish(output, source, plan, "search", started, records=records, children_reaped=True)
    except BaseException as exc:
        failure(output, started, exc)
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--source", required=True)
    a = p.parse_args()
    run(a.root.resolve(), a.source)
