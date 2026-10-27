"""Independent online choice from admitted connection work, without producer imports."""

from .common import require


def choose(evaluations, primary, nodes, route):
    if primary is None:
        return None

    def index(row):
        x, y = row["state"][:2]
        return min(((x - p[1]) ** 2 + (y - p[0]) ** 2, i) for i, p in enumerate(route))[1]

    selected = primary["trace"]
    if index(selected[-1]) + 1 >= 0.9 * len(route):
        return None
    maximum = max([index(selected[-1])] + [index(n) for n in nodes.values()])
    occupied = [tuple(n["state"]) for n in nodes.values()]
    occupied += [(*r["state"], r["frame"]) for r in selected]
    candidates = []
    for trial in evaluations:
        if trial["interrupted"] is not None or not trial["eligibility"]["complete"]:
            continue
        require(
            0 <= trial["eligibility"]["eligible_prefix"] <= trial["valid_prefix"], "eligibility"
        )
        for length in range(1, trial["eligibility"]["eligible_prefix"] + 1):
            row = trial["trace"][length]
            nearest = index(row)
            if nearest > maximum and (*row["state"], row["frame"]) not in occupied:
                candidates.append((-nearest, row["frame"], trial["id"], length, trial))
    if not candidates:
        return None
    nearest, _, evaluation, length, trial = min(candidates, key=lambda c: c[:4])
    return dict(
        evaluation=evaluation,
        prefix=length,
        nearest_index=-nearest,
        maximum_after_primary=maximum,
        trace=trial["trace"][: length + 1],
    )
