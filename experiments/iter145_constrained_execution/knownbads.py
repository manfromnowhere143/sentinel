"""Reproducible corruption checks of complete measured artifacts; keep base hashes."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import argparse
from .independent import validate
from .integration_check import verify


def mutate_at(value, path, replacement):
    for part in path[:-1]:
        value = value[part]
    value[path[-1]] = replacement


def run(root):
    proof = root / "experiments/iter145_constrained_execution/proof"
    optimizer_bytes = (proof / "optimizer_raw_v3.json").read_bytes()
    integration_bytes = (proof / "integration_raw.json").read_bytes()
    optimizer = json.loads(optimizer_bytes)
    integration = json.loads(integration_bytes)
    old = json.loads(
        (root / "experiments/iter144_timed_trajectory/proof/raw_qualification.json").read_text()
    )
    controls = [
        i for i, e in enumerate(integration["cases"][0]["events"]) if e["event"] == "control"
    ]
    step = next(i for i, e in enumerate(integration["cases"][0]["events"]) if e["event"] == "step")
    actor = next(
        i
        for i, e in enumerate(integration["cases"][0]["events"])
        if e["event"] == "actor" and e["value"]["event"] == "consume"
    )
    base = ["candidate", 0, "result"]
    case = ["cases", 0]
    control = case + ["events", controls[0]]
    recipes = [
        ("optimizer_missing_case", "optimizer", ["candidate"], optimizer["candidate"][:-1]),
        ("optimizer_wrong_order", "optimizer", ["candidate", 0, "index"], 9),
        ("optimizer_control", "optimizer", base + ["inputs", 0, 0], 0.0),
        ("optimizer_state", "optimizer", base + ["states", 1, 0], 99.0),
        ("optimizer_gradient", "optimizer", base + ["certificate", "gradient", 0], 99.0),
        ("optimizer_dual", "optimizer", base + ["certificate", "multipliers", 0], -1.0),
        ("optimizer_slack", "optimizer", base + ["certificate", "slack", 0], 99.0),
        ("optimizer_false_admission", "optimizer", base + ["admitted"], False),
        ("optimizer_missing_action", "optimizer", base + ["applied"], None),
        ("optimizer_iteration_cap", "optimizer", base + ["iterations"], 101),
        ("optimizer_timing", "optimizer", base + ["solver_ns"], 0),
        (
            "optimizer_handoff",
            "optimizer",
            ["candidate", 2, "result", "slsqp_returned_inputs", 0, 0],
            0.0,
        ),
        (
            "optimizer_refinement_previous",
            "optimizer",
            ["candidate", 2, "result", "refinement", 0, "previous_inputs", 0, 0],
            0.0,
        ),
        (
            "optimizer_refinement_alpha",
            "optimizer",
            ["candidate", 2, "result", "refinement", 0, "alpha"],
            0.0,
        ),
        (
            "optimizer_baseline_relabel",
            "optimizer",
            ["baseline", 0, "execution", "stop_reason"],
            "converged",
        ),
        ("integration_missing_case", "integration", ["cases"], integration["cases"][:-1]),
        ("integration_missing_boundary", "integration", case + ["boundary"], []),
        ("integration_incomplete", "integration", case + ["summary", "steps"], 11),
        ("integration_wrong_frame", "integration", control + ["frame"], 1),
        ("integration_wrong_time", "integration", control + ["result", "application_time"], 0.0),
        ("integration_stale_plan", "integration", control + ["delivery", "knot_times", 0], 0.0),
        (
            "integration_changed_plan_bytes",
            "integration",
            control + ["delivery", "delivered", "sha256"],
            "b" * 64,
        ),
        ("integration_bad_horizon", "integration", control + ["result", "reference"], []),
        ("integration_uncertified", "integration", control + ["result", "admitted"], False),
        ("integration_wrong_action", "integration", case + ["events", step, "applied", "acc"], 0.0),
        ("integration_wrong_transition", "integration", case + ["events", step, "after", 0], 99.0),
        (
            "integration_separate_render_collision",
            "integration",
            case + ["boundary", 0, "shared_transform_object"],
            False,
        ),
        (
            "integration_old_actor_pose",
            "integration",
            case + ["events", actor, "value", "transforms", "agent_0", 0, 3],
            999.0,
        ),
        ("integration_claimed_gpu", "integration", ["gpu_observed"], True),
        ("integration_claimed_live", "integration", ["live_study_admitted"], True),
    ]
    result = []
    for name, kind, path, replacement in recipes:
        value = deepcopy(optimizer if kind == "optimizer" else integration)
        mutate_at(value, path, replacement)
        digest = hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        ).hexdigest()
        try:
            validate(value, old) if kind == "optimizer" else verify(value)
        except (ValueError, KeyError, TypeError, IndexError) as exc:
            result.append(
                dict(
                    name=name,
                    kind=kind,
                    path=path,
                    rejected=True,
                    error=str(exc),
                    mutant_sha256=digest,
                )
            )
        else:
            result.append(
                dict(name=name, kind=kind, path=path, rejected=False, mutant_sha256=digest)
            )
    return dict(
        status="supported" if all(r["rejected"] for r in result) else "failed",
        optimizer_sha256=hashlib.sha256(optimizer_bytes).hexdigest(),
        integration_sha256=hashlib.sha256(integration_bytes).hexdigest(),
        total=len(result),
        rejected=sum(r["rejected"] for r in result),
        rows=result,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = run(a.root)
    with a.output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}))
    return 0 if result["status"] == "supported" else 1


if __name__ == "__main__":
    raise SystemExit(main())
