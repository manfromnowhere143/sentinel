"""One prospective advancing prefix; consume only this connection's recorded work."""

from experiments.iter158_constraint_aware_search.common import require


def endpoint(row):
    return (*row["state"], row["frame"])


def nearest(state, route):
    require(len(state) == 5 and bool(route), "route_dimensions")
    return min(
        range(len(route)),
        key=lambda i: (state[0] - route[i][1]) ** 2 + (state[1] - route[i][0]) ** 2,
    )


def choose(evaluations, primary, current_max, endpoints, route):
    """Return evaluation/prefix plus trace, never issue a new state query.

    current_max includes all prior registered endpoints. The primary endpoint is
    added before ranking; every state on the primary edge is excluded. Unknown
    eligibility remains eligible through the parent's eligible_prefix contract.
    """
    if primary is None:
        return None
    selected = primary["trace"]
    selected_index = nearest(selected[-1]["state"], route)
    if (selected_index + 1) / (0.9 * len(route)) >= 1:
        return None
    maximum = max(current_max, selected_index)
    represented = set(endpoints) | {endpoint(r) for r in selected}
    candidates, seen = [], set()
    for row in evaluations:
        require(row["id"] not in seen, "evaluation_identity")
        seen.add(row["id"])
        require(endpoint(row["trace"][0]) == endpoint(selected[0]), "selection_parent")
        eligible = row["eligibility"]["eligible_prefix"]
        require(0 <= eligible <= row["valid_prefix"] < len(row["trace"]), "eligible_prefix")
        if row["interrupted"] is not None or not row["eligibility"]["complete"]:
            continue
        for k in range(1, eligible + 1):
            state = row["trace"][k]
            index = nearest(state["state"], route)
            if index > maximum and endpoint(state) not in represented:
                candidates.append(((-index, state["frame"], row["id"], k), row))
    if not candidates:
        return None
    rank, row = min(candidates, key=lambda c: c[0])
    k = rank[-1]
    return dict(
        evaluation=row["id"],
        prefix=k,
        nearest_index=-rank[0],
        maximum_after_primary=maximum,
        trace=row["trace"][: k + 1],
    )
