"""One exclusive fixed qualification schedule; all queries and failures retained."""

import json
from pathlib import Path
import subprocess
import sys
import time
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter190_late_continuation_audit.masks import Queries
from .common import BASE, OLD, PREVIOUS, read, require, write
from .contract import check_contract
from .population_check import load
from .records import initialize, finish, failure
from .runtime import LIBRARY, verify
from .worker import request


def acquire(root, source):
    started = time.monotonic()
    output = root / BASE / "proof/qualification_raw"
    output.parent.mkdir(exist_ok=True)
    plan = initialize(root, output, source, "qualification")
    try:
        check_contract(root, plan)
        verify(root)
        q = json.loads(read(root, BASE / "QUALIFICATION.json"))
        require(
            q["status"] == "supported" and q["new_retained_input_evaluations"] == 0,
            "qualification_gate",
        )
        native = output / "native"
        native.mkdir()
        for label in plan["native_fixtures"]:
            for arm in plan["arms"]:
                command = [
                    sys.executable,
                    "-m",
                    "experiments.iter191_stop_wait_release.worker",
                    "--output",
                    str(native / (label + "-" + arm)),
                    "--library",
                    str(LIBRARY),
                    "--fixture",
                    label,
                ]
                if arm == "candidate":
                    command.append("--candidate")
                with (native / (label + "-" + arm + ".log")).open("xb") as stream:
                    child = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT)
                    try:
                        code = child.wait(timeout=plan["native_supervisor_seconds"])
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.wait()
                        raise ValueError("native_supervisor_deadline")
                require(code == 0, "native_worker_failure:" + label + ":" + arm)
                print(json.dumps(dict(native=label, arm=arm, status="retained")), flush=True)
        population, cases = load(root)
        old = json.loads(read(root, OLD))
        planner = json.loads(read(root, PREVIOUS / "PLAN.json"))
        queries, offline = {}, {}
        for name, case in cases.items():
            folder = output / name
            folder.mkdir()
            queries[name] = Queries(folder / "masks", query_for(case))
            for record in population["records"]:
                if record["case"] == name:
                    for row in record["trace"]:
                        queries[name].retain(row)
            offline[name] = queries[name].calls
        schedule = []
        for index, record in enumerate(population["records"]):
            require(
                time.monotonic() - started < plan["qualification_producer_seconds"],
                "producer_deadline",
            )
            folder = output / record["case"] / f"request_{index:03d}"
            folder.mkdir()
            order = plan["arms"] if index % 2 == 0 else list(reversed(plan["arms"]))
            for arm in order:
                query = queries[record["case"]]
                before = query.calls
                value, arm_start = request(
                    record, cases[record["case"]], old, planner, query, arm == "candidate"
                )
                write(folder / (arm + ".json"), value)
                charged = time.monotonic() - arm_start
                total = record["charged_original_wall"] + charged
                timing = dict(
                    charged_seconds=charged,
                    original_plus_seconds=total,
                    censored=total >= planner["per_run_seconds"] or value["events"][-1]["expired"],
                )
                write(folder / (arm + "-timing.json"), timing)
                require(query.calls - before == value["queries"], "worker_query_accounting")
                schedule.append(dict(index=index, input_id=record["id"], arm=arm))
            print(
                json.dumps(dict(request=index, input_id=record["id"], status="retained")),
                flush=True,
            )
        summaries = []
        for name, query in queries.items():
            query.finish()
            row = dict(
                case=name,
                offline_queries=offline[name],
                total_queries=query.calls,
                distinct_states=len(query.rows),
            )
            write(output / name / "summary.json", row)
            summaries.append(row)
        verify(root)
        finish(
            output,
            source,
            plan,
            "qualification",
            started,
            schedule=schedule,
            cases=summaries,
            native_workers=6,
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
