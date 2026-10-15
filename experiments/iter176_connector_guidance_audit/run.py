"""One bounded audit acquisition; original scientific schedules stay closed."""

import argparse
import json
from pathlib import Path
import time

from experiments.iter159_route_search_qualification.run import query_for, retain_trace
from experiments.iter171_centered_shooting.runtime import identity
from .common import BASE, read, require, rss, write
from .produce import extract_path, nominal, reflected
from .records import initialize, finish, failure
from .retained import case_records, request_identity, verify_inputs


def run(root, source):
    started = time.monotonic()
    output = root / BASE / "proof/audit_raw"
    output.parent.mkdir(exist_ok=True)
    plan = initialize(root, output, source, "audit")
    try:
        expected_runtime = json.loads(read(root, BASE / "RUNTIME.json"))
        require(identity() == expected_runtime, "runtime_identity")
        cases = verify_inputs(root, plan)
        requests, excluded, paths = [], [], []
        deadline = started + plan["audit_producer_seconds"]
        for case in cases:
            connections, trials = case_records(root, case["id"], plan)
            for row in connections:
                require(rss() <= plan["max_rss_bytes"], "memory_budget")
                if row["result"] is None:
                    excluded.append(dict(case=case["id"], call=row["call"], reason=row["stop"]))
                    continue
                reset, task = reflected(row["before"][:5], row["task"])
                requests.append(dict(
                    **request_identity(case["id"], row),
                    original=nominal(row["before"][:5], row["task"], row["budget"],
                                     plan["max_proposals"], deadline),
                    mirrored=nominal(reset, task, row["budget"], plan["max_proposals"], deadline),
                ))
            if case["id"] == plan["selected_case"]:
                require(sorted(trials) == plan["selected_evaluations"], "selected_population")
                query = query_for(case)
                for number in plan["selected_evaluations"]:
                    require(time.monotonic() < deadline, "producer_deadline")
                    trace, provenance = extract_path(connections, trials[number],
                                                     plan["selected_call"], case["geometry"]["reset"])
                    folder = f"path_{number:03}"
                    retain_trace(output / folder, trace, query)
                    paths.append(dict(case=case["id"], call=plan["selected_call"],
                                      evaluation=number, folder=folder, **provenance))
        require(len(requests) == plan["executed_count"] and len(excluded) == plan["excluded_count"]
                and len(requests)+len(excluded) == plan["connection_count"], "audit_population")
        write(output / "proposals.json", dict(requests=requests, excluded=excluded))
        write(output / "paths.json", paths)
        require(identity() == expected_runtime, "runtime_identity")
        finish(output, source, plan, "audit", started, request_count=len(requests),
               path_count=len(paths), new_motion_searches=0, new_integrated_schedules=0)
        print(json.dumps(dict(requests=len(requests), paths=len(paths), status="completed")), flush=True)
    except Exception as exc:
        failure(output, started, exc)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    run(args.root.resolve(), args.source)
