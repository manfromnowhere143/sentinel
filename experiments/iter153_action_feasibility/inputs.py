"""Bound retained evidence and extract an explicitly privileged geometry record."""

import hashlib
from pathlib import Path

from experiments.iter145_constrained_execution.resources import file_identity
from experiments.iter146_route_outcome_contract.check import strict, read, verify

BASE = Path("experiments/iter153_action_feasibility")


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def digest(value):
    import json

    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def document(path):
    return strict(
        file_identity(Path(path).absolute(), max_bytes=32 * 1024**2, include_bytes=True)["data"]
    )


def load(root):
    root = Path(root).resolve()
    manifest = document(root / BASE / "INPUTS.json")
    for name, expected in manifest["files"].items():
        require(
            file_identity(root / name, max_bytes=32 * 1024**2) == expected, "input_identity:" + name
        )
    events = [n for n in manifest["files"] if n.endswith("/events.jsonl")]
    require(len(events) == 4, "input_population")
    common, comparators, actions = None, {}, 0
    for name in sorted(events):
        rows, summary = read((root / name).parent)
        report = verify(rows, summary)
        require(report["status"] == "supported", "historical_replay")
        steps = [r for r in rows if r["event"] == "step"]
        resets = [r for r in rows if r["event"] == "reset"]
        objects = steps[0]["info"]["obj_boxes"]
        require(
            objects and all(s["info"]["obj_boxes"] == objects for s in steps), "stationary_geometry"
        )
        require(all(len(box) == 7 and min(box[3:6]) > 0 for box in objects), "obstacle_geometry")
        dims = steps[0]["info"]["ego_box"][3:6]
        require(all(s["info"]["ego_box"][3:6] == dims for s in steps), "ego_geometry")
        geometry = dict(
            route=rows[0]["route"], reset=resets[0]["state"], ego_dimensions=dims, obstacles=objects
        )
        require(len(resets) == 1 and geometry["reset"] == [0, 0, 0, 1, 0], "reset_geometry")
        require(common is None or common == geometry, "replica_geometry")
        common = geometry
        failure = report["outcome"]["first_failure_time"]
        row = next((r for r in report["scientific"] if r["time"] == failure), None)
        require(row is not None and report["outcome"]["collision_observed"], "comparator_failure")
        comparator = dict(hazard_time=failure, rc=row["rc"])
        arm = report["arm"]
        require(arm in ("nominal", "monitor"), "comparator_arm")
        require(arm not in comparators or comparators[arm] == comparator, "comparator_replica")
        comparators[arm] = comparator
        actions += report["steps"]
    require(set(comparators) == {"nominal", "monitor"}, "comparator_inventory")
    return dict(
        schema="sentinel.iter153.geometry.v1",
        **common,
        comparators=comparators,
        historical_actions_replayed=actions,
        input_manifest_sha256=digest(manifest),
        scope="Privileged source route/boxes; obstacle held stationary beyond observations by model assumption.",
    )
