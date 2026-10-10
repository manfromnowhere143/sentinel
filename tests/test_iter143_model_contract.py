"""Source-contract falsifiers; synthetic data only, no live trajectory outcomes."""

from copy import deepcopy
import json
import math
from pathlib import Path
import shutil

import pytest

from experiments.iter143_model_contract import independent as second
from experiments.iter143_model_contract import qualification as primary

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def adapters():
    blobs, _ = primary.inputs(ROOT)
    return primary.source_adapters(blobs)


@pytest.fixture
def zero_row():
    return dict(
        state=[0.0] * 5,
        control=[0.0, 0.0],
        environment_one=[0.0] * 5,
        environment_two=[0.0] * 5,
        controller_quarter=[0.0] * 5,
        controller_half=[0.0] * 5,
        applied_quarter=[0.0, 0.0],
        applied_half=[0.0, 0.0],
    )


def test_zero_row(zero_row):
    assert second.check_ego_row(zero_row)["equal_interval_max_absolute"] == 0


def test_actual_source_acceleration_order(adapters):
    env, ctrl = adapters[:2]
    state = [0.0, 0.0, 0.0, 4.0, 0.0]
    actual = env(state, [2.0, 0.0], 0.25)
    predicted, _ = ctrl(state, [2.0, 0.0], 0.25)
    assert actual == [1.125, 0.0, 0.0, 4.5, 0.0]
    assert predicted == [1.0, 0.0, 0.0, 4.5, 0.0]
    with pytest.raises(ValueError):
        second.close(actual, predicted)


def test_actual_source_steering_order(adapters):
    env, ctrl = adapters[:2]
    state = [0.0, 0.0, 0.0, 4.0, 0.0]
    actual = env(state, [0.0, 0.4], 0.25)
    predicted, _ = ctrl(state, [0.0, 0.4], 0.25)
    assert actual[2] == pytest.approx(math.tan(0.1) / 2.7)
    assert predicted[2] == 0.0


@pytest.mark.parametrize("control", [[3.0, 0.0], [-3.0, 0.0], [0.0, 0.4], [0.0, -0.4]])
def test_actual_source_declared_space_not_clipped(adapters, control):
    actual = adapters[0]([0.0, 0.0, 0.0, 4.0, 0.0], control, 0.25)
    assert actual[3] == 4 + control[0] * 0.25
    assert actual[4] == control[1] * 0.25


@pytest.mark.parametrize(
    "field",
    [
        "environment_one",
        "environment_two",
        "controller_quarter",
        "controller_half",
        "applied_quarter",
        "applied_half",
    ],
)
def test_corrupt_output_rejected(zero_row, field):
    zero_row[field][0] = 1.0
    with pytest.raises(ValueError):
        second.check_ego_row(zero_row)


def test_altered_control_rejected(zero_row):
    zero_row["control"][0] = 2.0
    with pytest.raises(ValueError):
        second.check_ego_row(zero_row)


def test_wrong_interval_rejected(adapters):
    env = adapters[0]
    with pytest.raises(ValueError):
        second.close(env([0.0, 0.0, 0.0, 4.0, 0.0], [0.0, 0.0], 0.5), [1.0, 0.0, 0.0, 4.0, 0.0])


def test_missing_output_rejected(zero_row):
    del zero_row["environment_one"]
    with pytest.raises(KeyError):
        second.check_ego_row(zero_row)


@pytest.mark.parametrize("raw", ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'])
@pytest.mark.parametrize("parser", [primary.strict_json, second.read_json])
def test_bad_json_rejected(raw, parser):
    with pytest.raises(ValueError):
        parser(raw)


def test_overflow_json_rejected():
    with pytest.raises(ValueError):
        second.read_json('{"x":1e9999}')


@pytest.mark.parametrize("value", [None, float("nan"), float("inf"), True])
def test_missing_nonfinite_boolean_scalar_rejected(value):
    with pytest.raises(ValueError):
        second.close(value, 0.0)


@pytest.fixture
def bound_root(tmp_path):
    binding = json.loads((ROOT / primary.BASE / "INPUTS.json").read_text())
    names = [
        primary.BASE + "/INPUTS.json",
        *binding["files"],
        *(r["path"] for r in binding["retrieved_sources"]),
    ]
    for name in names:
        out = tmp_path / name
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, out)
    return tmp_path


@pytest.mark.parametrize("checker", [primary.inputs, second.check_inputs])
def test_changed_input_rejected(bound_root, checker):
    path = bound_root / primary.ENV
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError):
        checker(bound_root)


@pytest.mark.parametrize("reader", [primary.bounded_read, second.read_bound])
def test_symlink_rejected(tmp_path, reader):
    (tmp_path / "file").write_text("x")
    (tmp_path / "link").symlink_to("file")
    with pytest.raises(ValueError):
        reader(tmp_path, "link")


def actor_fixture():
    # Hand-specified zero-origin clock channels and straight motion at four m/s.
    rows = dict(
        spline=[[8 * i / 19, 0.0, 4.0, 0.0, 0.0, 0.0, 2 * i / 19] for i in range(20)],
        fallback=[[0.4 * i, 0.0, math.pi / 2, 4.0] for i in range(20)],
        low_speed=[[i / 10, 0.0, 1.0, 0.0, 0.0, 0.0, i / 10] for i in range(1, 20)],
        dispatch=[],
        generations=[],
    )
    for i in range(21):
        rows["dispatch"].append(
            dict(
                time=i / 4,
                dt=0.1,
                requested_replan=i % 10 == 0,
                generation_count=i // 10 + 1,
                pointer_after=i % 10 + 2,
                attacked_states=[[0.0, float(j), 0.0, 4.0] for j in range(20)],
                actor_state=[0.0, 8 * (i + 1) / 19, 0.0, 0.0, 4.0],
            )
        )
    rows["generations"] = [
        dict(horizon=2.0, state=[0.0, 80 * i / 19, 4.0, math.pi / 2], dyn_filter=True)
        for i in range(3)
    ]
    return rows


def test_actor_clock_fixture():
    assert second.check_actor(actor_fixture())["reset_consumes_first_future_sample"] is True


@pytest.mark.parametrize("key", ["spline", "fallback", "low_speed", "dispatch", "generations"])
def test_actor_missing_row_rejected(key):
    rows = actor_fixture()
    rows[key].pop()
    with pytest.raises(ValueError):
        second.check_actor(rows)


def test_wrong_actor_time_channel_rejected():
    rows = actor_fixture()
    rows["spline"][1][-1] = 0.25
    with pytest.raises(ValueError):
        second.check_actor(rows)


def test_actor_duplicate_dispatch_rejected():
    rows = actor_fixture()
    rows["dispatch"][1] = deepcopy(rows["dispatch"][0])
    with pytest.raises(ValueError):
        second.check_actor(rows)


@pytest.mark.parametrize("reader", [primary.bounded_read, second.read_bound])
def test_oversized_input_rejected(tmp_path, reader):
    with (tmp_path / "large").open("wb") as f:
        f.truncate(16777217)
    with pytest.raises(ValueError):
        reader(tmp_path, "large")


def test_inventory_conflicting_hash_rejected(monkeypatch):
    blobs = {
        primary.INVENTORIES[0]: ("a" * 64 + "  scene-0013-easy-00.yaml\n").encode(),
        primary.INVENTORIES[1]: ("b" * 64 + "  scene-0013-easy-00.yaml\n").encode(),
    }
    monkeypatch.setattr(primary, "inputs", lambda root: (blobs, "synthetic"))
    with pytest.raises(ValueError, match="conflicting"):
        primary.inventory(Path("."))


def test_inventory_malformed_name_rejected(monkeypatch):
    blobs = {
        primary.INVENTORIES[0]: ("a" * 64 + "  broken.yaml\n").encode(),
        primary.INVENTORIES[1]: b"",
    }
    monkeypatch.setattr(primary, "inputs", lambda root: (blobs, "synthetic"))
    with pytest.raises(ValueError, match="malformed"):
        primary.inventory(Path("."))
