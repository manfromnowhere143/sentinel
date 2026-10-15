"""One acquisition; all seven late endpoints, two isolated scene inventories."""

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
from .premature import completion_bound
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
        inputs = load(root, plan)
        old = json.loads(read(root, OLD))
        prepared = []
        for case, connections, selected, trials in inputs:
            folder = raw / case["id"]
            folder.mkdir()
            vector = query_for(case)
            masks = Masks(folder / "masks", vector)
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
            require(len(paths) == len(selected), "path_population")
            write(folder / "paths.json", paths)
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
            write(folder / "retained_evaluations.json", rejected)
            prepared.append((case, folder, vector, masks, representatives))
        probe_started = time.monotonic()
        deadline = probe_started + plan["aggregate_search_seconds"]
        total_attempts, total_masks, total_probes = 0, 0, 0
        for case, folder, vector, masks, representatives in prepared:

            def query(state):
                return summary(vector(state))

            probes = []
            for path in representatives:
                last = path["trace"][-1]
                bound = progress_bound(
                    last["state"], last["frame"], case["geometry"], old, plan["target_frame"]
                )
                completion = completion_bound(
                    last["state"], last["frame"], case["geometry"], old, plan["target_frame"]
                )
                result = probe(
                    last["state"], last["frame"], case["geometry"], old, plan, query, deadline
                )
                suffix = result.pop("trace")
                attempts = result.pop("attempt_records")
                # Materialize EVERY queried state, including rejected/unselected alternatives.
                for row in attempts:
                    if row["background"] is not None:
                        masks.add(row["state"], row["background"])
                combined = copy.deepcopy(path["trace"] + suffix[1:])
                for i, row in enumerate(combined):
                    row.update(id=i, parent=i - 1 if i else None)
                keys = masks.path(combined)
                destination = folder / f"probe_{path['call']:03}"
                destination.mkdir()
                write(destination / "attempts.json", attempts)
                write(destination / "trace.json", combined)
                probes.append(
                    dict(
                        call=path["call"],
                        bound=bound,
                        completion_bound=completion,
                        result=result,
                        masks=keys,
                        selected_attempt_ids=[r["id"] for r in suffix],
                    )
                )
            write(folder / "probes.json", probes)
            masks.finish()
            total_attempts += sum(p["result"]["attempts"] for p in probes)
            total_masks += len(masks.rows)
            total_probes += len(probes)
        elapsed = time.monotonic() - probe_started
        require(identity() == runtime, "runtime_identity")
        require(
            total_attempts
            <= plan["depth_specific_maximum_attempts"]
            <= plan["maximum_total_attempts"],
            "total_probe_budget",
        )
        finish(
            raw,
            source,
            plan,
            "audit",
            started,
            new_motion_searches=total_probes,
            new_integrated_schedules=0,
            diagnostic_attempts=total_attempts,
            probe_envelope_seconds=elapsed,
            distinct_masks=total_masks,
        )
        print(
            json.dumps(
                dict(
                    status="completed",
                    diagnostic_attempts=total_attempts,
                    distinct_masks=total_masks,
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
