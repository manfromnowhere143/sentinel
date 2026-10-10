"""Deterministic development schedule. Missing launch evidence is explicit."""

import hashlib
from .source import bound_inputs
from experiments.iter143_model_contract.qualification import strict_json

INVENTORY = "experiments/iter143_model_contract/proof/case_inventory.json"
ARMS = ("nominal", "monitor", "brake_t0", "brake_t2_5")
REQUIRED_BINDINGS = (
    "source_commit",
    "runtime_manifest_sha256",
    "asset_manifest_sha256",
    "full_simulator_smoke_receipt_sha256",
    "qualification_receipt_sha256",
    "resource_envelope_sha256",
    "live_preregistration_commit",
)


def schedule(root):
    raw = bound_inputs(root)[INVENTORY]
    inventory = strict_json(raw)
    selected = [r for r in inventory["rows"] if r["role"] == "proposed_pilot"]
    if len(selected) != 14 or sorted({r["scene"] for r in selected}) != ["0013", "0038", "0041"]:
        raise ValueError("pilot_inventory_changed")
    slots = []
    for scenario in selected:
        for arm in ARMS:
            for replica in (1, 2):
                slots.append(
                    dict(
                        slot=len(slots),
                        scenario=scenario["name"],
                        scenario_sha256=scenario["sha256"],
                        scene=scenario["scene"],
                        arm=arm,
                        replica=replica,
                        seed=144,
                        reset_count=1,
                        max_actions=401,
                        status="proposed",
                        outcome=None,
                    )
                )
    return dict(
        schema="sentinel.iter144.study_schedule.v1",
        status="proposed",
        inventory_sha256=hashlib.sha256(raw).hexdigest(),
        inventory=inventory["rows"],
        independent_base_scenes=3,
        untouched_holdout_scenes=0,
        slots=slots,
        regime="sentinel.timed_trajectory.v1",
        binding={k: None for k in REQUIRED_BINDINGS},
        live_admitted=False,
        cloud_budget=0,
        stopping="no initialized retry or replacement; invalid replay stops later slots",
        reverse_brake="-sign(v)*min(2,abs(v)/.25); preserve nominal steering after projection",
        numerical_replica_policy="same seed, fresh process, single explicit reset per episode",
    )


def readiness(document):
    """Completeness report only; external receipts still require independent validation."""
    missing = [k for k in REQUIRED_BINDINGS if document["binding"].get(k) is None]
    return dict(
        status="proposed",
        live_admitted=False,
        missing_bindings=missing,
        reason="This preparation tool cannot authorize a live run; bind and validate a new live protocol.",
    )
