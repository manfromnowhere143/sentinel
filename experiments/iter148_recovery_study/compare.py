"""Complete pre-onset equality before the unchanged three-valued witness rules."""

from experiments.iter146_route_outcome_contract.compare import compare as prior_compare, replicas
from experiments.iter145_constrained_execution.independent import check, close


def compare(nominal, monitor, intervention):
    n, p = replicas(nominal), replicas(intervention)
    onset = 0 if p["arm"] == "brake_t0" else 2.5
    prefix = min(int(onset * 4), len(n["scientific"]), len(p["scientific"]))
    for x, y in zip(n["scientific"][:prefix], p["scientific"][:prefix]):
        for field in ("time", "state", "action", "nominal_action", "rc"):
            close(x[field], y[field], 1e-9)
        for field in ("nominal", "delivered", "rgb", "actors", "collision", "off_route"):
            check(x[field] == y[field], "complete_intervention_prefix:" + field)
    result = prior_compare(nominal, monitor, intervention)
    result["prefix_steps_verified"] = prefix
    return result
