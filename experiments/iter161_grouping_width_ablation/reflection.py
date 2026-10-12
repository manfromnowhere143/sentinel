"""Independent field-by-field reflection admission; no fixture-generator import."""

from .common import encode, require


def check_pair(left, right):
    require(
        set(left) == set(right) == {"id", "geometry", "points", "ground", "witness_actions"},
        "reflection_fields",
    )
    require(
        left["id"].endswith("_left") and right["id"] == left["id"][:-5] + "_right", "reflection_id"
    )
    a, b = left["geometry"], right["geometry"]
    require(
        set(a) == set(b) == {"reset", "route", "ego_dimensions", "obstacles", "comparators"},
        "geometry_fields",
    )
    expected = [v if k in (0, 3) else -v for k, v in enumerate(a["reset"])]
    require(encode(b["reset"]) == encode(expected), "reflection_reset")
    require(encode(b["route"]) == encode([[-p[0], p[1]] for p in a["route"]]), "reflection_route")
    require(
        encode(b["obstacles"])
        == encode([[(-v if k in (1, 6) else v) for k, v in enumerate(o)] for o in a["obstacles"]]),
        "reflection_foreground",
    )
    require(
        encode(b["ego_dimensions"]) == encode(a["ego_dimensions"])
        and encode(b["comparators"]) == encode(a["comparators"]),
        "reflection_fixed_fields",
    )
    require(
        encode(right["points"]) == encode([[-p[0], p[1], p[2]] for p in left["points"]]),
        "reflection_points",
    )
    require(
        encode(right["witness_actions"]) == encode([[a, -r] for a, r in left["witness_actions"]]),
        "reflection_commands",
    )
    expected_ground = [
        [
            [(-v if (i == 0) != (j == 0) else v) for j, v in enumerate(row)]
            for i, row in enumerate(pose)
        ]
        for pose in left["ground"]
    ]
    require(encode(right["ground"]) == encode(expected_ground), "reflection_ground")


def check_cases(cases, previous):
    require(
        [c["id"] for c in cases] == ["bend_left", "bend_right", "chicane_left", "chicane_right"],
        "case_population",
    )
    for i in (0, 2):
        require(encode(cases[i]) == encode(previous[i]), "left_case_changed")
        check_pair(cases[i], cases[i + 1])
