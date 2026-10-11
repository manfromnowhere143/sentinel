"""Raw commitment precedes separate full-scene scientific admission."""

from pathlib import Path
from experiments.iter147_full_horizon_execution.coordinator import raw_identity
from experiments.iter148_recovery_study.admission import completed_pair
from .admission import validate_plan, history, identity
from .contract import packet
from .check import verify_case
from .baseline import verify as historical


def admit(repository, directory, document, pair, commit, receipts, raw_root):
    validate_plan(document)
    previous = history(document, receipts, pair)
    digest = raw_identity(repository, commit, directory)
    completed_pair(directory, document, pair)
    selected, geometry = packet(repository)
    if historical(repository) != geometry:
        raise ValueError("historical_geometry_changed")
    reports = [
        verify_case(Path(directory) / "runs" / slot["id"], slot, selected, geometry)
        for slot in document["slots"]
    ]
    # Dictionary comparisons retain booleans and outcomes; numerical state replay is separate.
    if (
        reports[0]["scientific"] != reports[1]["scientific"]
        or reports[0]["outcome"] != reports[1]["outcome"]
    ):
        raise ValueError("replica_disagreement")
    good = all(r["outcome"]["completion_qualified"] for r in reports)
    harm = any(
        r["outcome"]["collision_observed"] or r["outcome"]["off_route_observed"] for r in reports
    )
    return dict(
        status="supported",
        replica_check="supported",
        pair=0,
        plan_sha256=identity(document),
        raw_commit=commit,
        raw_inventory_sha256=digest,
        previous_receipt_sha256=previous,
        steps=sum(r["steps"] for r in reports),
        historical_slots_counted_as_new=0,
        scientific_status="supported" if good else "contradicted" if harm else "inconclusive",
        road_compliance=None,
        information_benefit=None,
        cases=[{k: v for k, v in r.items() if k not in ("scientific", "route")} for r in reports],
    )
