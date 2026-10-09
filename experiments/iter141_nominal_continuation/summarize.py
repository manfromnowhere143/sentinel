"""Frozen four-arm decision; no favorable imputation for missing results."""


def summarize(reports):
    arms = ("reference_a", "reference_b", "nominal_a", "nominal_b")
    if any(a not in reports or reports[a].get("status") != "validated" for a in arms):
        return dict(status="inconclusive", verdict="SCHEDULE_INCOMPLETE")
    if reports["reference_b"].get("verdict") != "REPLAY_MATCHED":
        return dict(status="failed", verdict="REFERENCE_NOT_ADMITTED")
    if reports["nominal_b"].get("nominal_replica", {}).get("prefix") != "matched":
        return dict(status="invalid", verdict="NOMINAL_REPLAY_DIVERGED")
    nominal = [reports[a] for a in arms[2:]]
    if any(
        r.get("prefix") != "matched" or not r["outcomes"]["action_contrast_observed"]
        for r in nominal
    ):
        return dict(status="inconclusive", verdict="NO_ACTION_CONTRAST")
    outcomes = [r["outcomes"] for r in nominal]
    useful = sum(r["useful_recovery"] for r in outcomes)
    if useful == 2:
        status, suffix = "supported", "SUPPORTED"
    elif useful:
        return dict(status="invalid", verdict="NOMINAL_REPLAY_DIVERGED")
    elif any(r["censored"] for r in outcomes):
        status, suffix = "inconclusive", "INCONCLUSIVE"
    else:
        status, suffix = "null", "NULL"
    return dict(
        status=status,
        verdict="NOMINAL_CONTINUATION_" + suffix,
        useful_recoveries=useful,
        nominal_episodes=2,
        outcomes=outcomes,
    )
