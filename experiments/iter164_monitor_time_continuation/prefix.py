"""One fixed historical-prefix acquisition; no continuation search."""

import argparse
import json
from pathlib import Path
import time

from experiments.iter153_action_feasibility.geometry import obstacles, route_outcome
from experiments.iter156_background_calibration.background import (
    BackgroundPopulation,
    box_for_state,
)
from experiments.iter158_constraint_aware_search.search import prior_reason, summary
from experiments.iter159_route_search_qualification.run import retain_trace
from .common import inputs
from .history import extract
from .records import initialize, finish, failure


def run(root, output, source):
    started = time.monotonic()
    plan = initialize(root, output, source, "prefix")
    try:
        geometry, old, arrays = inputs(root, plan)
        population = BackgroundPopulation(arrays["selected_xyz"], plan["population_sha256"])
        ground = arrays["ground_poses"]
        del arrays
        cases = extract(root, plan)
        boxes, records = obstacles(geometry), []

        def query(state):
            return population.query(box_for_state(state, ground)[0])

        for index, case in enumerate(cases):
            rows = []
            for frame, (state, action) in enumerate(zip(case["states"], case["actions"])):
                before = case["states"][max(frame - 1, 0)]
                background = summary(query(state))
                reason, _ = prior_reason(
                    before, state, action or [0, 0], frame, geometry, old, boxes
                )
                rows.append(
                    dict(
                        id=frame,
                        parent=frame - 1 if frame else None,
                        frame=frame,
                        action=action,
                        state=state,
                        route=route_outcome(state, geometry["route"]),
                        background=background,
                        reason=reason or background["decision"],
                    )
                )
            retain_trace(output / f"replica_{index}", rows, query)
            record = dict(
                episode=case["episode"],
                states=len(rows),
                queries=2 * len(rows),
                eligible=all(r["reason"] == "clear" for r in rows),
            )
            records.append(record)
            print(json.dumps(record), flush=True)
        finish(
            output,
            source,
            plan,
            "prefix",
            started,
            records=records,
            selected_points=plan["selected_points"],
            population_sha256=population.sha256,
        )
    except Exception as exc:
        failure(output, started, exc)
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--source", required=True)
    args = p.parse_args()
    run(args.root.resolve(), args.output.resolve(), args.source)
