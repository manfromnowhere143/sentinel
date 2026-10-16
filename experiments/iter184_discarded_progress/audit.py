"""One prefix/certificate acquisition followed by separate committed-raw admission."""

import argparse
from pathlib import Path
import time

from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter182_late_frontier_timing.produce import Masks
from experiments.iter182_late_frontier_timing.bound import progress_bound
from experiments.iter182_late_frontier_timing.premature import completion_bound
from .common import BASE, document, write, require
from .records import initialize, finish, failure
from .retained import load, OLD, identity
from .produce import extract
from .contract import check_plan
from .runtime import verify


def run(root, source, library):
    started = time.monotonic()
    verify(root, library)
    raw = root / BASE / "proof/audit_raw"
    raw.parent.mkdir(exist_ok=True)
    plan = initialize(root, raw, source, "audit")
    try:
        check_plan(root, plan)
        case, connections, trials, records, maxima = load(root, plan)
        old = document(root, OLD)
        table = {(t["call"], t["id"]): t for t in trials}
        masks = Masks(raw / "masks", query_for(case))
        paths = []
        for record in records:
            require(time.monotonic() - started < plan["audit_producer_seconds"], "audit_deadline")
            path = extract(
                connections, table[(record["call"], record["evaluation"])], record["prefix"]
            )
            path["masks"] = masks.path(path["trace"])
            last = path["trace"][-1]
            if 24 <= last["frame"] < 32:
                cert = dict(
                    status="checked",
                    progress=progress_bound(
                        last["state"], last["frame"], case["geometry"], old, 32
                    ),
                    completion=completion_bound(
                        last["state"], last["frame"], case["geometry"], old, 32
                    ),
                )
            else:
                cert = dict(status="outside_window", progress=None, completion=None)
            path.update(
                certificates=cert,
                selected_for_probe=identity(record) in [identity(m) for m in maxima],
            )
            paths.append(path)
        write(raw / "paths.json", paths)
        masks.finish()
        finish(
            raw,
            source,
            plan,
            "audit",
            started,
            path_records=len(paths),
            distinct_masks=len(masks.rows),
            new_motion_searches=0,
        )
        print("Prefix acquisition complete; raw admission required", flush=True)
    except Exception as error:
        failure(raw, started, error)
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--library", type=Path, required=True)
    a = p.parse_args()
    run(a.root.resolve(), a.source, a.library.resolve())
