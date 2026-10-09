"""Frozen grid-level decision; absent cells remain unobserved."""

from experiments.iter139_finite_pulse_recoverability.trace import ARMS


def summarize(reports):
    cells = {}
    for arm in list(ARMS)[2:]:
        r = reports.get(arm)
        if r is None:
            cells[arm] = dict(status="unobserved", outcomes=None)
        elif r.get("status") != "validated" or r.get("prefix") != "matched":
            cells[arm] = dict(status="invalid", outcomes=r.get("outcomes"))
        else:
            cells[arm] = dict(status="observed", outcomes=r["outcomes"])
    if reports.get("reference_b", {}).get("verdict") != "REPLAY_MATCHED":
        return dict(status="inconclusive", verdict="REFERENCE_GATE_NOT_PASSED", cells=cells)
    complete = all(c["status"] == "observed" for c in cells.values())
    useful = [k for k, c in cells.items() if c["outcomes"] and c["outcomes"]["useful_recovery"]]
    if not complete:
        status, verdict = "inconclusive", "FINITE_PULSE_GRID_INCOMPLETE"
    elif useful:
        status, verdict = "supported", "FINITE_PULSE_RECOVERY_SUPPORTED"
    elif any(c["outcomes"]["censored"] for c in cells.values()):
        status, verdict = "inconclusive", "FINITE_PULSE_RECOVERY_INCONCLUSIVE"
    else:
        status, verdict = "null", "FINITE_PULSE_RECOVERY_NULL"
    return dict(
        status=status,
        verdict=verdict,
        useful_cells=useful,
        observed_cells=sum(c["status"] == "observed" for c in cells.values()),
        cells=cells,
        scope="finite intervention availability in one disclosed development scenario",
    )
