"""Revalidate disclosed historical evidence without relabelling it as new execution."""

import hashlib
from pathlib import Path

from experiments.iter147_full_horizon_execution.coordinator import raw_identity
from experiments.iter151_recovery_canary.replay import pair_reports
from experiments.iter151_recovery_canary.admission import validate_plan as prior_plan
from experiments.iter145_constrained_execution.independent import check, close
from .admission import BASE, validate_plan
from .records import read


def verify(repository):
    repository = Path(repository).resolve()
    document = validate_plan(read(repository / BASE / "STUDY_PLAN.json"))
    binding = document["historical_comparator"]
    receipt_path = repository / binding["admission_path"]
    if hashlib.sha256(receipt_path.read_bytes()).hexdigest() != binding["admission_sha256"]:
        raise ValueError("historical_admission_changed")
    receipt = read(receipt_path)
    for key in ("raw_commit", "raw_inventory_sha256", "plan_sha256", "pair"):
        if receipt[key] != binding[key]:
            raise ValueError("historical_binding:" + key)
    if receipt["status"] != "supported" or receipt["replica_check"] != "supported":
        raise ValueError("historical_not_admitted")
    directory = repository / binding["raw_path"]
    if (
        raw_identity(repository, binding["raw_commit"], directory)
        != binding["raw_inventory_sha256"]
    ):
        raise ValueError("historical_inventory_changed")
    original = prior_plan(read(directory / "plan.json"))
    reports = pair_reports(directory, original, 0)
    if sum(r["steps"] for r in reports) != receipt["steps"]:
        raise ValueError("historical_replay_changed")
    return reports


def compatible(historical, current):
    for h, c in zip(historical, current):
        close(h["route"], c["route"], 0)
        close(h["reset_state"], c["reset_state"], 1e-9)
        check(h["actor_types"] == c["actor_types"], "historical_actor_types")


def client_identity(repository, directory):
    binding = read(Path(repository) / BASE / "STUDY_PLAN.json")["historical_comparator"]
    original = Path(repository) / binding["raw_path"] / "e2e147.py"
    if original.read_bytes() != (Path(directory) / "e2e147.py").read_bytes():
        raise ValueError("historical_client_changed")
