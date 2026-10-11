"""Finite-study accounting; observed unknowns and unexecuted comparisons stay distinct."""

from .admission import history


def predicates(values, planned):
    if any(v is not True and v is not False and v is not None for v in values):
        raise ValueError("comparison_predicate_type")
    if len(values) > planned:
        raise ValueError("comparison_count")
    return dict(
        true=sum(v is True for v in values),
        false=sum(v is False for v in values),
        unknown=sum(v is None for v in values),
        missing=planned - len(values),
    )


def summarize(document, receipts):
    history(document, receipts, len(receipts))
    complete = [r for r in receipts if r["pair"] % 4 == 3]
    per_pulse = {}
    for arm in ("brake_t0", "brake_t2_5"):
        rows = [r["comparisons"][arm] for r in complete]
        per_pulse[arm] = {
            k: predicates([r[k] for r in rows], 14)
            for k in ("intersection_witness", "action_contrast", "harm_vs_successful_nominal")
        }
        for comparator in ("nominal", "monitor"):
            per_pulse[arm][comparator] = {
                k: predicates([r[comparator][k] for r in rows], 14)
                for k in ("opportunity", "progress_at_hazard_satisfied", "witness")
            }
    return dict(
        status="supported" if len(receipts) == 56 else "inconclusive",
        planned_scenarios=14,
        compared_scenarios=len(complete),
        admitted_pairs=len(receipts),
        admitted_slots=2 * len(receipts),
        slots_without_supported_admission=112 - 2 * len(receipts),
        independently_verified_steps=sum(r["steps"] for r in receipts),
        per_pulse=per_pulse,
        scope="Exposed development library; no whole-study prevalence from partial execution.",
    )
