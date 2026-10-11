"""Admit a fixed pair only after retained raw, replay and full scenario comparisons."""

from pathlib import Path
from experiments.iter147_full_horizon_execution.coordinator import raw_identity
from experiments.iter147_full_horizon_execution.gpu_check import verify_case
from experiments.iter147_full_horizon_execution.protocol import identity
from experiments.iter146_route_outcome_contract.compare import replicas
from .admission import validate_plan, history, completed_pair
from .compare import compare


def pair_reports(directory, document, pair):
    completed_pair(directory, document, pair)
    reports = [
        verify_case(Path(directory) / "runs" / slot["id"], slot, "study")
        for slot in document["slots"][pair * 2 : pair * 2 + 2]
    ]
    replicas(reports)
    return reports


def admit(repository, directory, document, pair, commit, receipts, raw_root):
    validate_plan(repository, document)
    previous = history(document, receipts, pair)
    digest = raw_identity(repository, commit, directory)
    reports = pair_reports(directory, document, pair)
    result = dict(
        status="supported",
        pair=pair,
        plan_sha256=identity(document),
        raw_commit=commit,
        raw_inventory_sha256=digest,
        previous_receipt_sha256=previous,
        steps=sum(r["steps"] for r in reports),
        cases=[{k: v for k, v in r.items() if k not in ("scientific", "route")} for r in reports],
    )
    if pair % 4 == 3:
        arms = {}
        for index in range(pair - 3, pair + 1):
            source = Path(raw_root) / f"pair_{index:03d}"
            if index != pair:
                prior = receipts[index]
                if (
                    raw_identity(repository, prior["raw_commit"], source)
                    != prior["raw_inventory_sha256"]
                ):
                    raise ValueError("prior_raw_identity")
            pair_result = reports if index == pair else pair_reports(source, document, index)
            arms[pair_result[0]["arm"]] = pair_result
        comparisons = {
            arm: compare(arms["nominal"], arms["monitor"], arms[arm])
            for arm in ("brake_t0", "brake_t2_5")
        }
        result.update(scenario_comparison_status="supported", comparisons=comparisons)
    return result
