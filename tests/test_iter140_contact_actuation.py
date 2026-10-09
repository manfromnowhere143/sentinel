import copy
import hashlib
import math
from pathlib import Path
import random

import pytest

from experiments.iter140_contact_actuation import analyze, independent
from experiments.iter140_contact_actuation.geometry import SourceGeometry, validate_box
from experiments.iter140_contact_actuation.inputs import read_bound, strict_json

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def geometry():
    p = (
        ROOT
        / "experiments/iter136_hugsim_recoverability_canary/proof/source/HUGSIM/sim/hugsim_env/envs/hug_sim.py.txt"
    )
    q = ROOT / "experiments/iter139_finite_pulse_recoverability/proof/score_calculator.py.txt"
    return SourceGeometry(q.read_bytes(), p.read_bytes())


def box(x=0.0, y=0.0, width=2.0, length=4.0, yaw=0.0):
    return [x, y, 0.0, width, length, 1.5, yaw]


@pytest.mark.parametrize(
    "other,hit",
    [
        (box(5), False),
        (box(4), True),
        (box(4, 2), True),
        (box(4.000001), False),
        (box(3.999999), True),
        (box(width=1, length=1), True),
        (box(3, yaw=math.pi / 2), True),
        (box(3.01, yaw=math.pi / 2), False),
        (box(0, 2.5), False),
    ],
)
def test_source_and_independent_geometry(geometry, other, hit):
    measured = geometry.measure(box(), [other])["actors"][0]
    assert measured["intersects"] == hit
    assert (independent.gap(box(), other) <= 1e-12) == hit
    area, distance = independent.area_and_distance(box(), other)
    assert measured["overlap_area_m2"] == pytest.approx(area, abs=1e-10)
    assert measured["distance_m"] == pytest.approx(distance, abs=1e-10)


def test_width_length_swap_changes_contact(geometry):
    assert not geometry.measure(box(), [box(0, 2.5)])["foreground"]
    assert geometry.measure(box(width=4, length=2), [box(0, 2.5)])["foreground"]


def test_rotated_translated_random_rectangles(geometry):
    rng = random.Random(140)
    for _ in range(200):
        a = box(
            rng.uniform(-25, 25),
            rng.uniform(-25, 25),
            rng.uniform(0.5, 3),
            rng.uniform(1, 6),
            rng.uniform(-math.pi, math.pi),
        )
        b = box(
            a[0] + rng.uniform(-6, 6),
            a[1] + rng.uniform(-6, 6),
            rng.uniform(0.5, 3),
            rng.uniform(1, 6),
            rng.uniform(-math.pi, math.pi),
        )
        row = geometry.measure(a, [b])["actors"][0]
        assert row["intersects"] == (independent.gap(a, b) < 0)
        area, distance = independent.area_and_distance(a, b)
        assert area == pytest.approx(row["overlap_area_m2"], abs=1e-9)
        assert distance == pytest.approx(row["distance_m"], abs=1e-9)


@pytest.mark.parametrize(
    "bad",
    [
        [0] * 6,
        [0, 0, 0, 0, 4, 1, 0],
        [0, 0, 0, 2, -4, 1, 0],
        [True, 0, 0, 2, 4, 1, 0],
        [0, 0, 0, 2, 4, 1, float("nan")],
    ],
)
def test_invalid_boxes_rejected(bad):
    with pytest.raises(ValueError):
        validate_box(bad)
    with pytest.raises(ValueError):
        independent.gap(box(), bad)


@pytest.mark.parametrize("raw", ['{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}'])
def test_invalid_json_rejected(raw):
    with pytest.raises(ValueError):
        strict_json(raw)


def test_bound_reader_known_bads(tmp_path):
    p = tmp_path / "raw"
    p.write_bytes(b"abcd")
    record = dict(bytes=4, sha256=hashlib.sha256(b"abcd").hexdigest())
    assert read_bound(tmp_path, "raw", record) == b"abcd"
    p.write_bytes(b"abce")
    with pytest.raises(ValueError, match="byte identity"):
        read_bound(tmp_path, "raw", record)
    p.unlink()
    p.symlink_to(tmp_path / "missing")
    with pytest.raises(ValueError, match="symlink"):
        read_bound(tmp_path, "raw", record)
    with pytest.raises(ValueError, match="input path"):
        read_bound(tmp_path, "../raw", record)
    p.unlink()
    with pytest.raises(FileNotFoundError):
        read_bound(tmp_path, "raw", record)


def fixture_rows():
    state = dict(
        timestamp=0.0,
        ego_box=box(yaw=0.2),
        ego_velo=2.0,
        ego_steer=0.05,
        ego_pos=[0.0, 0.0, 0.0],
        obj_boxes=[box(7)],
        accelerate=0.0,
        steer_rate=0.0,
    )
    rows = [dict(onset=0.25, duration=0.25)]
    for i in range(4):
        before = copy.deepcopy(state)
        acc, rate = -0.4, 0.02
        state["ego_velo"] += acc * 0.25
        state["ego_steer"] += rate * 0.25
        theta = state["ego_box"][6]
        state["ego_box"][0] += state["ego_velo"] * math.cos(theta) * 0.25
        state["ego_box"][1] += state["ego_velo"] * math.sin(theta) * 0.25
        state["ego_box"][6] -= state["ego_velo"] * math.tan(state["ego_steer"]) * 0.25 / 2.7
        state["ego_pos"] = [-state["ego_box"][1], 0.0, state["ego_box"][0]]
        state["accelerate"], state["steer_rate"] = acc, rate
        state["timestamp"] = (i + 1) * 0.25
        rows.append(
            dict(
                frame=i,
                time=i * 0.25,
                before=before,
                after=copy.deepcopy(state),
                control=[acc, rate],
                collision=False,
                route_completion=0.1,
            )
        )
    rows.append(dict(end="completed"))
    return rows


def test_full_synthetic_replay(geometry):
    rows = fixture_rows()
    report = analyze.episode(rows, geometry)
    result = independent.check_episode(rows, report)
    assert result["frames"] == 4 and not result["ambiguities"]
    assert report["phases"]["before_pulse"]["frames"] == 1
    assert report["phases"]["during_pulse"]["frames"] == 1
    assert report["phases"]["resumed"]["frames"] == 2
    assert not result["terminal_contact_supported"]


@pytest.mark.parametrize(
    "field",
    [
        "x",
        "speed",
        "heading",
        "control",
        "missing_phase",
        "contact",
        "relative_velocity",
        "area",
        "distance",
    ],
)
def test_changed_state_or_report_rejected(geometry, field):
    rows = fixture_rows()
    report = analyze.episode(rows, geometry)
    if field == "x":
        rows[1]["after"]["ego_box"][0] += 0.01
    elif field == "speed":
        rows[1]["after"]["ego_velo"] += 0.01
    elif field == "heading":
        rows[1]["after"]["ego_box"][6] += 0.01
    elif field == "control":
        rows[1]["control"][0] = 0.0
    elif field == "missing_phase":
        del report["phases"]["resumed"]
    elif field == "contact":
        report["timeline"][0]["after"]["actors"][0]["intersects"] = True
    elif field == "relative_velocity":
        report["terminal_relation"]["relative_center_speed_mps"] += 1.0
    elif field == "area":
        report["timeline"][0]["after"]["actors"][0]["overlap_area_m2"] += 1.0
    else:
        report["timeline"][0]["after"]["actors"][0]["distance_m"] += 1.0
    with pytest.raises(AssertionError):
        independent.check_episode(rows, report)


def test_tiny_gap_is_preserved_as_ambiguity(geometry):
    rows = fixture_rows()
    # Use an initial edge contact in this synthetic fixture; do not alter actual evidence.
    rows[1]["before"]["obj_boxes"] = [box(4 * math.cos(0.2), 4 * math.sin(0.2), yaw=0.2)]
    report = analyze.episode(rows, geometry)
    result = independent.check_episode(rows, report)
    assert result["ambiguities"] and result["ambiguities"][0]["point"] == "before"


def test_actor_comparison_tolerance_and_horizon():
    reference = fixture_rows()
    candidate = copy.deepcopy(reference)
    candidate[2]["after"]["obj_boxes"][0][0] += 1e-7
    candidate[3]["after"]["obj_boxes"][0][0] += 0.25
    p = analyze.compare_actors(reference, candidate)
    independent.close(p, independent.comparison(reference, candidate))
    assert p["first_exact_difference_time"] == 0.5
    assert p["first_over_1e_6_difference_time"] == 0.75
    assert p["max_center_displacement_m"] == 0.25
    candidate[2]["after"]["obj_boxes"].append(box(20))
    assert analyze.compare_actors(reference, candidate)["correspondence_unresolved"]


def test_no_actor_id_invented(geometry):
    rows = fixture_rows()
    for f in rows[1:-1]:
        for point in ("before", "after"):
            f[point]["obj_boxes"].append(box(30))
    report = analyze.episode(rows, geometry)
    result = independent.check_episode(rows, report)
    assert not result["single_actor"] and report["terminal_relation"] is None


def test_terminal_contact_supported_only_with_matching_flag(geometry):
    rows = fixture_rows()
    for i, f in enumerate(rows[1:-1]):
        for point in ("before", "after"):
            f[point]["obj_boxes"] = [box(5.7)]
        f["collision"] = i == 3
    report = analyze.episode(rows, geometry)
    result = independent.check_episode(rows, report)
    assert result["terminal_contact_supported"]
    rows[-2]["collision"] = False
    report = analyze.episode(rows, geometry)
    result = independent.check_episode(rows, report)
    assert not result["terminal_contact_supported"]


def test_state_continuity_rejection(geometry):
    rows = fixture_rows()
    rows[2]["before"]["obj_boxes"][0][0] += 0.1
    report = analyze.episode(rows, geometry)
    with pytest.raises(AssertionError, match="continuity"):
        independent.check_episode(rows, report)


def test_actor_comparison_forgery_rejected():
    rows = fixture_rows()
    actual = analyze.compare_actors(rows, rows)
    actual["first_over_1e_6_difference_time"] = 0.25
    with pytest.raises(AssertionError):
        independent.close(actual, independent.comparison(rows, rows))


def test_independent_module_has_no_primary_imports():
    import ast

    tree = ast.parse(Path(independent.__file__).read_text())
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module)
    assert all(
        x in {"argparse", "decimal", "hashlib", "json", "math", "pathlib", "sys"} for x in imports
    )
