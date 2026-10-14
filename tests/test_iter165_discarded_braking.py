"""Known-bad population, historical clock, and independent scalar-cache checks."""

import copy
import json
from pathlib import Path

import numpy as np
import pytest

from experiments.iter155_background_witness.geometry import count_points, vertices
from experiments.iter165_discarded_braking.candidates import candidates, prefix_for
from experiments.iter165_discarded_braking.check import ScalarCache
from experiments.iter165_discarded_braking.common import BASE, source_check

ROOT = Path(__file__).resolve().parents[1]


def test_complete_population_and_schedule():
    schedule, nodes = candidates(ROOT)
    assert schedule == json.loads((ROOT / BASE / "CANDIDATES.json").read_text())
    assert len(schedule) == 49
    assert len({r["node_id"] for r in schedule}) == 49
    for row in schedule:
        prefix = prefix_for(ROOT, nodes, row["node_id"])
        assert [r["frame"] for r in prefix] == list(range(28))
        assert prefix[-1]["state"] == nodes[row["node_id"]]["state"]
        if row["cohort"] == "discarded":
            assert [r["action"][0] for r in prefix[-2:]] == [-2, -2]


@pytest.mark.parametrize("field,value", [("state", [0] * 5), ("frame", 24)])
def test_changed_history_is_rejected(field, value):
    schedule, nodes = candidates(ROOT)
    nodes = copy.deepcopy(nodes)
    nodes[0][field] = value
    with pytest.raises(ValueError, match="historical_join"):
        prefix_for(ROOT, nodes, schedule[0]["node_id"])


def test_missing_parent_is_rejected():
    schedule, nodes = candidates(ROOT)
    nodes[schedule[0]["node_id"]]["parent"] = 999999
    with pytest.raises(KeyError):
        prefix_for(ROOT, nodes, schedule[0]["node_id"])


def test_scalar_cache_exact_vertices_and_packed_masks():
    points = [[0, 0.5, 0], [3, 0.5, 0], [0.8, 0.5, 0]]
    cache = ScalarCache(points)
    for x in [0, 0, 0.01, 0.01, 3]:
        box = vertices([x, 0, 0], 0)
        expected = count_points(points, box)
        actual = cache(points, box)
        for name in ["count", "certain_inside", "possible_inside"]:
            assert actual[name] == expected[name]
        assert np.array_equal(actual["mask"], expected["mask"])
    assert cache.evaluated == 3 and cache.reused == 2
    assert all(isinstance(value[1], bytes) for value in cache.entries.values())


def test_other_population_cannot_reuse_cache():
    points = [[0, 0, 0]]
    cache = ScalarCache(points)
    with pytest.raises(ValueError, match="cache_population"):
        cache(copy.deepcopy(points), vertices([0, 0, 0], 0))


def test_source_rejects_old_commit():
    plan = json.loads((ROOT / BASE / "PLAN.json").read_text())
    with pytest.raises(Exception):
        source_check(ROOT, plan, "76cb41cfdf91ae0897153038ac0812b0ede4d120")
