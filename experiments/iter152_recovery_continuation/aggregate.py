"""Keep fourteen new slots separate from the two historical nominal observations."""

from experiments.iter151_recovery_canary.aggregate import predicates
from .admission import history


def summarize(document, receipts):
    history(document, receipts, len(receipts))
    complete = [r for r in receipts if r["pair"] in (2, 6)]
    per_pulse = {}
    for arm in ("brake_t0", "brake_t2_5"):
        rows = [r["comparisons"][arm] for r in complete]
        per_pulse[arm] = {
            k: predicates([r[k] for r in rows], 2)
            for k in ("intersection_witness", "action_contrast", "harm_vs_successful_nominal")
        }
        for comparator in ("nominal", "monitor"):
            per_pulse[arm][comparator] = {
                k: predicates([r[comparator][k] for r in rows], 2)
                for k in ("opportunity", "progress_at_hazard_satisfied", "witness")
            }
    return dict(
        status="supported" if len(receipts) == 7 else "inconclusive",
        planned_new_slots=14,
        admitted_new_slots=2 * len(receipts),
        new_slots_without_supported_admission=14 - 2 * len(receipts),
        historical_comparator_slots=2,
        historical_comparator_actions=62,
        planned_scenarios=2,
        compared_scenarios=len(complete),
        independently_verified_new_actions=sum(r["steps"] for r in receipts),
        per_pulse=per_pulse,
        scope="Fixed exposed development continuation; original Iter151 remains closed and inconclusive.",
    )
