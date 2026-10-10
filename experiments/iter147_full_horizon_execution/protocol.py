"""Finite populations, stable order, and explicit separation of diagnostics from study data."""

import hashlib
import json
from experiments.iter144_timed_trajectory.study import schedule


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def identity(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def slots(root, purpose):
    proposed = schedule(root)["slots"]
    if purpose == "study":
        selected = [(s, "none") for s in proposed]
    elif purpose == "qualification":
        # Selection fixed by lexical scenario/controller inventory, not outcomes.
        selected = []
        for case, arm, probe in (
            ("scene-0013-easy-00.yaml", "monitor", "monitor_hold"),
            ("scene-0013-extreme-00.yaml", "nominal", "none"),
            ("scene-0013-hard-00.yaml", "nominal", "none"),
            ("scene-0013-medium-00.yaml", "nominal", "none"),
        ):
            selected.extend(
                (s, probe) for s in proposed if s["scenario"] == case and s["arm"] == arm
            )
    else:
        raise ValueError("purpose")
    return [
        dict(
            index=i,
            id=f"{purpose}_{i:03d}__{s['scenario'].removesuffix('.yaml')}__{s['arm']}__{s['replica']}",
            scenario=s["scenario"],
            scenario_sha256=s["scenario_sha256"],
            arm=s["arm"],
            replica=s["replica"],
            seed=144,
            reset_count=1,
            max_actions=401,
            probe=probe,
        )
        for i, (s, probe) in enumerate(selected)
    ]


def plan(root, purpose):
    population = slots(root, purpose)
    return dict(
        schema="sentinel.iter147.plan.v1",
        purpose=purpose,
        slots=population,
        child_seconds=1200,
        host_seconds=len(population) * 1200 + 1200,
        compute_hourly_upper_usd=3.0,
        compute_cap_usd=(len(population) * 1200 + 1200) / 3600 * 3,
        raw_before_analysis=True,
        initialized_retry=False,
        live_admitted=False,
    )


def validate(root, document):
    if document != plan(root, document.get("purpose")):
        raise ValueError("frozen_plan_changed")
    return document
