"""Proposed paired witness rules over independently verified execution reports."""

from experiments.iter145_constrained_execution.independent import check, close


def conjunction(*values):
    """False is decisive; otherwise preserve any unknown operand."""
    check(all(v is True or v is False or v is None for v in values), "predicate type")
    if any(v is False for v in values):
        return False
    return None if any(v is None for v in values) else True


def qualified_success(outcome):
    if outcome["completion_qualified"]:
        return True
    if outcome["collision_observed"] or outcome["off_route_observed"]:
        return False
    return None if outcome["censored"] else False


def replicas(pair):
    check(len(pair) == 2 and all(p["status"] == "supported" for p in pair), "unverified replica")
    a, b = pair
    check(a["arm"] == b["arm"] and a["outcome"] == b["outcome"], "replica outcome disagreement")
    close(a["route"], b["route"], 0)
    close(a["reset_state"], b["reset_state"], 1e-9)
    check(len(a["scientific"]) == len(b["scientific"]), "replica length disagreement")
    for x, y in zip(a["scientific"], b["scientific"]):
        for field in ("time", "state", "action", "nominal_action", "rc"):
            close(x[field], y[field], 1e-9)
        check(set(x["actors"]) == set(y["actors"]), "replica actor identity")
        for key in x["actors"]:
            close(x["actors"][key], y["actors"][key], 1e-9)
        for field in ("nominal", "delivered", "collision", "off_route", "rgb"):
            check(x[field] == y[field], "replica trace disagreement:" + field)
    return a


def compare(nominal, monitor, intervention):
    n, m, p = (replicas(pair) for pair in (nominal, monitor, intervention))
    check(
        n["arm"] == "nominal" and m["arm"] == "monitor" and p["arm"] in ("brake_t0", "brake_t2_5"),
        "comparison arms",
    )
    for comparator in (n, m):
        close(comparator["route"], p["route"], 0)
        close(comparator["reset_state"], p["reset_state"], 1e-9)
    onset = 0 if p["arm"] == "brake_t0" else 2.5
    prefix_count = min(int(onset * 4), len(n["scientific"]), len(p["scientific"]))
    for x, y in zip(n["scientific"][:prefix_count], p["scientific"][:prefix_count]):
        close(x["state"], y["state"], 1e-9)
        close(x["action"], y["action"], 1e-9)
        check(x["nominal"] == y["nominal"] and x["actors"] == y["actors"], "intervention prefix")
        check(
            x["delivered"] == y["delivered"]
            and x["collision"] == y["collision"]
            and x["off_route"] == y["off_route"],
            "intervention prefix outcome",
        )
    # No-effect interventions cannot establish an action witness.
    contrast = any(
        abs(r["action"][0] - r["nominal_action"][0]) > 1e-9
        for r in p["scientific"]
        if onset <= r["time"] - 0.25 < onset + 1
    )
    if (
        not contrast
        and p["outcome"]["censored"]
        and (not p["scientific"] or p["scientific"][-1]["time"] < onset + 1)
    ):
        contrast = None
    answers = {}
    for label, comparator in (("nominal", n), ("monitor", m)):
        hazard = comparator["outcome"]["first_failure_time"]
        opportunity = None if comparator["outcome"]["censored"] else hazard is not None
        observed = next((r for r in p["scientific"] if r["time"] == hazard), None)
        hazard_row = next((r for r in comparator["scientific"] if r["time"] == hazard), None)
        earlier = bool(
            hazard is not None
            and p["outcome"]["completion_qualified"]
            and p["scientific"][-1]["time"] < hazard
        )
        progress = (
            True
            if earlier
            else (
                observed["rc"] >= hazard_row["rc"] - 0.05
                if observed is not None and hazard_row is not None
                else None
            )
        )
        answers[label] = dict(
            opportunity=opportunity,
            hazard_time=hazard,
            progress_at_hazard_satisfied=progress,
            witness=conjunction(opportunity, qualified_success(p["outcome"]), contrast, progress),
        )
    # Observed failure is decisive; incomplete nonfailure stays unknown in either arm.
    intervention_success = qualified_success(p["outcome"])
    harm = conjunction(
        qualified_success(n["outcome"]),
        None if intervention_success is None else not intervention_success,
    )
    return dict(
        status="supported",
        nominal=answers["nominal"],
        monitor=answers["monitor"],
        intersection_witness=conjunction(*(a["witness"] for a in answers.values())),
        action_contrast=contrast,
        harm_vs_successful_nominal=harm,
        scope="simulator-defined route completion, exposed development cases only",
    )
