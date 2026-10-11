"""Exclusive local bounded search; no cloud adapter, subprocess or package installation."""

import argparse
import platform
import sys
import time
from pathlib import Path

from experiments.iter151_recovery_canary.records import record
from .inputs import BASE, digest, document, load, require
from .planner import candidates, reference, command, transition, limits
from .geometry import obstacles, ego_box, separation, sweep_clear, route_outcome


def trial(geometry, spec, plan, replica, deadline):
    path, arc = reference(geometry["route"], spec, plan)
    state = list(geometry["reset"])
    boxes = obstacles(geometry)
    rows, states, actions = [], [state], []
    sweep = True
    stop = "censored"
    if any(separation(ego_box(state, geometry["ego_dimensions"]), b) <= 0 for b in boxes):
        stop = "initial_contact"
    else:
        for frame in range(plan["max_actions"]):
            if time.monotonic() >= deadline:
                stop = "budget_expired"
                break
            action = command(state, path, arc, spec, plan)
            after = transition(state, action, plan)
            valid = limits(after, action, plan)
            fg = any(separation(ego_box(after, geometry["ego_dimensions"]), b) <= 0 for b in boxes)
            sweep = sweep and sweep_clear(state, after, geometry["ego_dimensions"], boxes, plan)
            outcome = route_outcome(after, geometry["route"])
            rows.append(
                dict(
                    time=(frame + 1) * plan["dt"],
                    **outcome,
                    foreground_collision=fg,
                    controls_valid=valid,
                )
            )
            states.append(after)
            actions.append(action)
            state = after
            if not valid or fg or outcome["distance"] > 10 or outcome["rc"] >= 1:
                stop = (
                    "controls_invalid"
                    if not valid
                    else "foreground_contact"
                    if fg
                    else "off_route"
                    if outcome["distance"] > 10
                    else "model_complete"
                )
                break
    complete = stop == "model_complete"
    progress = {}
    for name, comparator in geometry["comparators"].items():
        row = next((r for r in rows if r["time"] == comparator["hazard_time"]), None)
        progress[name] = (
            True
            if complete and rows[-1]["time"] < comparator["hazard_time"]
            else None
            if row is None
            else row["rc"] >= comparator["rc"] - plan["progress_slack"]
        )
    return dict(
        schema="sentinel.iter153.trial.v1",
        candidate=spec,
        replica=replica,
        geometry_sha256=digest(geometry),
        plan_sha256=digest(plan),
        states=states,
        actions=actions,
        rows=rows,
        stop=stop,
        producer=dict(
            model_complete=complete,
            swept_clear=sweep,
            progress=progress,
            eligible=complete and sweep and all(v is True for v in progress.values()),
        ),
        background_collision=None,
        road_compliance=None,
        live_recovery=None,
        information_benefit=None,
    )


def execute(root, directory):
    root, directory = Path(root).resolve(), Path(directory).absolute()
    require(directory == root / BASE / "proof/search_000", "search_directory")
    plan = document(root / BASE / "PLAN.json")
    qualification = document(root / BASE / "QUALIFICATION.json")
    require(qualification["status"] == "supported", "qualification")
    binding = document(root / BASE / "SOURCE.json")
    from experiments.iter145_constrained_execution.resources import file_identity

    for name, expected in binding["files"].items():
        require(file_identity(root / name) == expected, "frozen_source")
    geometry = load(root)
    require(digest(geometry) == qualification["geometry_sha256"], "qualified_geometry")
    directory.mkdir()  # Exclusive initialization; never resume or overwrite this search.
    started = time.monotonic()
    record(
        directory / "initialized.json",
        dict(
            plan_sha256=digest(plan),
            source_sha256=digest(binding),
            python=sys.version,
            platform=platform.platform(),
            wall_limit=plan["maximum_wall_seconds"],
        ),
    )
    record(directory / "geometry.json", geometry)
    specs = candidates(plan)
    require(len(specs) == plan["expected_candidates"], "population")
    completed = 0
    try:
        for spec in specs:
            for replica in range(1, plan["replicas"] + 1):
                result = trial(
                    geometry, spec, plan, replica, started + plan["maximum_wall_seconds"]
                )
                record(directory / f"{spec['id']}_{replica}.json", result)
                completed += 1
                print(spec["id"], replica, result["stop"], flush=True)
                if result["stop"] == "budget_expired":
                    raise TimeoutError("search_budget")
        status, error = "completed", None
    except Exception as exc:
        status, error = "invalid", f"{type(exc).__name__}:{exc}"
    record(
        directory / "execution.json",
        dict(
            status=status,
            error=error,
            retained_trials=completed,
            uninitialized_trials=len(specs) * plan["replicas"] - completed,
            elapsed_seconds=time.monotonic() - started,
        ),
    )
    return 0 if status == "completed" else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    raise SystemExit(execute(args.root, args.output))
