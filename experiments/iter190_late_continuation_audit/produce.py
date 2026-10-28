"""One frozen all-root acquisition, with original remaining-work accounting."""

import json
from pathlib import Path
import time

from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter182_late_frontier_timing.bound import progress_bound
from experiments.iter188_early_timing_feasibility.bound import certificate
from .common import BASE, OLD, read, require, write
from .contract import check_contract
from .runtime import verify
from .records import initialize, finish, failure
from .population_check import load, through_rejection
from .masks import Queries
from .probe import run


def acquire(root, source):
    started = time.monotonic()
    output = root / BASE / "proof/audit_raw"
    output.parent.mkdir(exist_ok=True)
    plan = initialize(root, output, source, "audit")
    try:
        check_contract(root, plan)
        verify(root)
        qualification = json.loads(read(root, BASE / "QUALIFICATION.json"))
        require(
            qualification["status"] == "supported"
            and qualification["new_retained_root_probes"] == 0,
            "qualification_gate",
        )
        population, sources = load(root)
        old = json.loads(read(root, OLD))
        cases = []
        for source_case in sources:
            case = source_case["case"]
            name = case["id"]
            folder = output / name
            folder.mkdir()
            query = Queries(folder / "masks", query_for(case))
            records = [r for r in population["records"] if r["case"] == name]
            for record in records:
                for row in record["trace"]:
                    query.retain(row)
                for evaluation in source_case["outgoing"].get(record["node"], []):
                    for row in through_rejection(evaluation):
                        query.retain(row)
            offline_queries = query.calls
            roots = []
            for record in records:
                if record["id"] != record["representative"]:
                    continue
                require(
                    time.monotonic() - started < plan["audit_producer_seconds"], "audit_deadline"
                )
                members = [r for r in records if r["representative"] == record["id"]]
                cap = min(plan["per_arm_attempts"], *(r["remaining_attempts"] for r in members))
                seconds = min(plan["per_arm_seconds"], *(r["remaining_seconds"] for r in members))
                target = folder / f"node_{record['node']:03d}"
                target.mkdir()
                bound_start = time.monotonic()
                bounds = dict(
                    progress=progress_bound(
                        record["state"], record["frame"], case["geometry"], old, 32
                    ),
                    completion=certificate(record["state"], record["frame"], case["geometry"], old),
                )
                write(target / "bounds.json", bounds)
                common_seconds = time.monotonic() - bound_start
                arms = []
                for method in plan["arms"]:
                    before = query.calls
                    arm_start = time.monotonic()
                    deadline = arm_start + max(0.0, seconds - common_seconds)
                    result = run(
                        method,
                        record["state"],
                        record["frame"],
                        case["geometry"],
                        old,
                        cap,
                        query,
                        deadline,
                        plan["max_rss_bytes"],
                    )
                    write(target / (method + ".json"), result)
                    charged = common_seconds + time.monotonic() - arm_start
                    timing = dict(
                        method=method,
                        attempt_cap=cap,
                        wall_cap=seconds,
                        common_seconds=common_seconds,
                        charged_seconds=charged,
                        queries=query.calls - before,
                        censored=charged >= seconds or result["stop"] == "time_budget",
                    )
                    write(target / (method + "-timing.json"), timing)
                    arms.append(timing)
                roots.append(
                    dict(
                        id=record["id"],
                        node=record["node"],
                        members=[r["id"] for r in members],
                        arms=arms,
                    )
                )
            query.finish()
            row = dict(
                case=name,
                offline_queries=offline_queries,
                total_queries=query.calls,
                distinct_states=len(query.rows),
                roots=roots,
            )
            write(folder / "summary.json", row)
            cases.append(row)
            print(
                json.dumps(dict(case=name, roots=len(roots), distinct_states=len(query.rows))),
                flush=True,
            )
        verify(root)
        finish(
            output,
            source,
            plan,
            "audit",
            started,
            cases=cases,
            children_reaped=True,
            new_integrated_runs=0,
        )
    except Exception as exc:
        failure(output, started, exc)
        raise


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True)
    a = p.parse_args()
    acquire(Path.cwd(), a.source)
