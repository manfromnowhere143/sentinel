"""One frozen retained-frontier audit acquisition; no source comparison."""

import argparse
import copy
import json
from pathlib import Path
import time

from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter171_centered_shooting.runtime import identity
from .common import BASE, read, require, write
from .contract import check_plan
from .records import initialize, finish, failure
from .retained import load, OLD, through_first_rejection
from .produce import extract, Masks
from .bound import progress_bound
from .probe import probe


def run(root, source):
    started = time.monotonic()
    raw = root / BASE / "proof/audit_raw"
    raw.parent.mkdir(exist_ok=True)
    plan = initialize(root, raw, source, "audit")
    try:
        check_plan(plan)
        runtime = json.loads(read(root, BASE / "RUNTIME.json"))
        require(identity() == runtime, "runtime_identity")
        case, connections, selected, trials = load(root, plan)
        old = json.loads(read(root, OLD))
        vector = query_for(case)

        def query(state):
            return summary(vector(state))

        masks = Masks(raw / "masks", vector)
        paths, representatives, prior = [], [], {}
        for edge in selected:
            path = extract(connections, edge["call"])
            path["masks"] = masks.path(path["trace"])
            endpoint = path["trace"][-1]
            numeric = tuple([*endpoint["state"], endpoint["frame"]])
            path["representative"] = prior.setdefault(numeric, edge["call"])
            paths.append(path)
            if path["representative"] == edge["call"]:
                representatives.append(path)
        require(len(paths) == 19 and len(representatives) == 16, "path_population")
        write(raw / "paths.json", paths)
        rejected = []
        for trial in trials:
            require(
                time.monotonic() - started < plan["audit_producer_seconds"], "producer_deadline"
            )
            prefix = list(through_first_rejection(trial))
            keys = [
                None if r["background"] is None else masks.add(r["state"], r["background"])
                for r in prefix
            ]
            rejected.append(
                dict(
                    call=trial["call"],
                    evaluation=trial["id"],
                    masks=keys,
                    first_reason=prefix[-1]["reason"]
                    if prefix[-1]["reason"] != "clear"
                    else "all_reported_clear",
                )
            )
        write(raw / "retained_evaluations.json", rejected)
        probes = []
        probe_started = time.monotonic()
        deadline = probe_started + plan["aggregate_search_seconds"]
        for path in representatives:
            last = path["trace"][-1]
            bound = progress_bound(
                last["state"], last["frame"], case["geometry"], old, plan["target_frame"]
            )
            result = probe(
                last["state"], last["frame"], case["geometry"], old, plan, query, deadline
            )
            suffix = result.pop("trace")
            attempt_records = result.pop("attempt_records")
            combined = copy.deepcopy(path["trace"] + suffix[1:])
            for i, row in enumerate(combined):
                row.update(id=i, parent=i - 1 if i else None)
            keys = masks.path(combined)
            folder = raw / f"probe_{path['call']:03}"
            folder.mkdir()
            write(folder / "attempts.json", attempt_records)
            write(folder / "trace.json", combined)
            probes.append(
                dict(
                    call=path["call"],
                    bound=bound,
                    result=result,
                    masks=keys,
                    selected_attempt_ids=[r["id"] for r in suffix],
                )
            )
        elapsed = time.monotonic() - probe_started
        write(raw / "probes.json", probes)
        masks.finish()
        require(identity() == runtime, "runtime_identity")
        attempts = sum(p["result"]["attempts"] for p in probes)
        require(attempts <= plan["maximum_total_attempts"], "total_probe_budget")
        finish(
            raw,
            source,
            plan,
            "audit",
            started,
            new_motion_searches=16,
            new_integrated_schedules=0,
            diagnostic_attempts=attempts,
            probe_envelope_seconds=elapsed,
            distinct_masks=len(masks.rows),
        )
        print(
            json.dumps(
                dict(
                    status="completed", diagnostic_attempts=attempts, distinct_masks=len(masks.rows)
                )
            ),
            flush=True,
        )
    except Exception as exc:
        failure(raw, started, exc)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    run(args.root.resolve(), args.source)
