"""New continuation admission around unchanged scientific and full-prefix validators."""

from pathlib import Path

from experiments.iter147_full_horizon_execution.coordinator import raw_identity
from experiments.iter151_recovery_canary.replay import pair_reports
from experiments.iter148_recovery_study.compare import compare
from .admission import validate_plan, history, identity
from .baseline import verify, compatible, client_identity


def admit(repository, directory, document, pair, commit, receipts, raw_root):
    validate_plan(document)
    previous = history(document, receipts, pair)
    digest = raw_identity(repository, commit, directory)
    reports = pair_reports(directory, document, pair)
    client_identity(repository, directory)
    historical = verify(repository)
    if pair < 3:
        compatible(historical, reports)
    result = dict(
        status="supported",
        replica_check="supported",
        pair=pair,
        plan_sha256=identity(document),
        raw_commit=commit,
        raw_inventory_sha256=digest,
        previous_receipt_sha256=previous,
        steps=sum(r["steps"] for r in reports),
        historical_comparator_sha256=identity(document["historical_comparator"]),
        historical_slots_counted_as_new=0,
        cases=[{k: v for k, v in r.items() if k not in ("scientific", "route")} for r in reports],
    )
    if pair in (2, 6):
        arms = {"nominal": historical} if pair == 2 else {}
        indices = range(0, 3) if pair == 2 else range(3, 7)
        for index in indices:
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
        result.update(
            scenario_comparison_status="supported",
            comparisons=comparisons,
            comparator_origin="iter151_historical" if pair == 2 else "iter152_new",
        )
    return result
