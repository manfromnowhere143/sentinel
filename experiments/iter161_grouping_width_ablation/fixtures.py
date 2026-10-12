"""Complete lateral reflection of a frozen left-hand fixture; no scene tuning."""

import copy


def reflect(case):
    result = copy.deepcopy(case)
    prefix, side = case["id"].rsplit("_", 1)
    if side not in ("left", "right"):
        raise ValueError("reflection_id")
    result["id"] = prefix + ("_right" if side == "left" else "_left")
    g = result["geometry"]
    for k in (1, 2, 4):
        g["reset"][k] = -g["reset"][k]
    g["route"] = [[-p[0], p[1]] for p in g["route"]]
    g["obstacles"] = [
        [-v if i in (1, 6) else v for i, v in enumerate(obj)] for obj in g["obstacles"]
    ]
    result["points"] = [[-p[0], p[1], p[2]] for p in result["points"]]
    result["witness_actions"] = [[a, -r] for a, r in result["witness_actions"]]
    signs = (-1, 1, 1, 1)
    result["ground"] = [
        [[value * signs[i] * signs[j] for j, value in enumerate(row)] for i, row in enumerate(pose)]
        for pose in result["ground"]
    ]
    return result
