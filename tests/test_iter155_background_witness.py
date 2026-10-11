"""Known-bads for the finite source collision witness, boundaries and evidence transport."""

import copy
import gzip
import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from experiments.iter155_background_witness import geometry as g
from experiments.iter155_background_witness.check import historical, selection
from experiments.iter155_background_witness.source import background_function, box_statements
from experiments.iter155_background_witness.storage import digest, get_arrays, put_array, read_json

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/iter155_background_witness"
SOURCE = ROOT / "experiments/iter145_constrained_execution/source/score_calculator.py.txt"
ENV = (
    ROOT
    / "experiments/iter136_hugsim_recoverability_canary/proof/source/HUGSIM/sim/hugsim_env/envs/hug_sim.py.txt"
)
TORCH = SimpleNamespace(dot=np.dot, sum=np.sum)


@pytest.mark.parametrize("count", [0, 1, 99, 100, 101, 102, 1000])
def test_source_threshold(count):
    box = np.array(g.vertices([0, 0, 0], 0), dtype=np.float32)
    points = np.tile(np.array([[0, 0.5, 0]], dtype=np.float32), (count, 1))
    native = background_function(SOURCE.read_text(), TORCH)
    mask = background_function(SOURCE.read_text(), TORCH, mask=True)(points, box)
    result = g.count_points(points.tolist(), box.tolist())
    assert result["count"] == count and result["collision"] == (count > 100)
    assert bool(native(points, box)) == result["collision"] and int(mask.sum()) == count


@pytest.mark.parametrize("yaw", [0, 0.25, -0.8, math.pi / 2])
def test_rotated_source_and_boundary(yaw):
    box = np.array(g.vertices([3, -0.2, 11], yaw), dtype=np.float32)
    center = box.mean(axis=0)
    points = np.vstack([center, box])
    mask = background_function(SOURCE.read_text(), TORCH, mask=True)(points, box)
    checked = g.count_points(points.tolist(), box.tolist())
    differences = {i for i, (a, b) in enumerate(zip(mask, checked["mask"])) if bool(a) != b}
    assert differences <= set(checked["ambiguous"]) and checked["mask"][0]
    if yaw == 0:
        assert checked["count"] == 1


@pytest.mark.parametrize(
    "face", [(0.8, 0.5, 0), (-0.8, 0.5, 0), (0, 0, 0), (0, 1.5, 0), (0, 0.5, 1.5), (0, 0.5, -1.5)]
)
def test_strict_faces(face):
    box = np.array(g.vertices([0, 0, 0], 0), dtype=np.float32)
    point = np.array([face], dtype=np.float32)
    assert not background_function(SOURCE.read_text(), TORCH)(np.tile(point, (101, 1)), box)
    assert not g.count_points(point.tolist(), box.tolist())["mask"][0]


@pytest.mark.parametrize("fault", ["nan", "inf", "short", "degenerate", "skew", "order"])
def test_bad_geometry(fault):
    box = g.vertices([0, 0, 0], 0)
    points = [[0, 0.5, 0]]
    if fault == "nan":
        points[0][0] = float("nan")
    elif fault == "inf":
        box[0][0] = float("inf")
    elif fault == "short":
        box.pop()
    elif fault == "degenerate":
        box[1] = box[0]
    elif fault == "skew":
        box[1][0] += 1
    else:
        box[3], box[7] = box[7], box[3]
    with pytest.raises(ValueError):
        g.count_points(points, box)


def test_ground_projection():
    c, s = math.cos(0.2), math.sin(0.2)
    pose = [[1, 0, 0, 2], [0, c, -s, -0.4], [0, s, c, 8], [0, 0, 0, 1]]
    height, index = g.ground_height([pose], 2, 8)
    expected = -0.4 * c * c
    assert abs(height - expected) < 1e-14 and index == 0
    with pytest.raises(ValueError):
        g.ground_height([[[0] * 4 for _ in range(4)]], 0, 0)


def test_source_box_dimensions():
    env = SimpleNamespace()
    box_statements(ENV.read_text(), env, np)
    assert np.array_equal(env.ego_verts.astype(np.float32), np.array(g.vertices([0, 0, 0], 0)))


def test_filter_and_tie():
    xyz = np.zeros((6, 3), dtype="<f4")
    feat = np.zeros((6, 12), dtype="<f4")
    opacity = np.array([0.81, 0.8, 0.9, 0.9, 0.9, 0.81], dtype="<f4")
    for row, label in enumerate([2, 2, 0, 1, 10, 2]):
        feat[row, label] = 1
    feat[5, 1] = 1
    assert selection(xyz, feat, opacity).tolist() == [True, False, False, False, False, False]


@pytest.mark.parametrize("fault", ["nan", "wrong_shape", "bad_opacity", "float64"])
def test_filter_bad(fault):
    xyz = np.zeros((2, 3), dtype="<f4")
    feat = np.ones((2, 12), dtype="<f4")
    opacity = np.ones(2, dtype="<f4")
    if fault == "nan":
        feat[0, 0] = np.nan
    elif fault == "wrong_shape":
        xyz = xyz[:1]
    elif fault == "bad_opacity":
        opacity[0] = 2
    else:
        feat = feat.astype("f8")
    with pytest.raises(ValueError):
        selection(xyz, feat, opacity)


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "bytes",
        "missing",
        "duplicate",
        "path",
        "shape",
        "dtype",
        "nonfinite",
        "bomb",
        "symlink",
    ],
)
def test_array_evidence(tmp_path, fault):
    inventory = {}
    put_array(tmp_path, "points", np.arange(12, dtype="<f4").reshape(4, 3), inventory)
    row = inventory["points"]
    chunk = row["chunks"][0]
    path = tmp_path / chunk["path"]
    if fault == "bytes":
        path.write_bytes(b"corrupt")
    elif fault == "missing":
        path.unlink()
    elif fault == "duplicate":
        row["chunks"].append(copy.deepcopy(chunk))
    elif fault == "path":
        chunk["path"] = "../escape"
    elif fault == "shape":
        row["shape"] = [True, 3]
    elif fault == "dtype":
        row["dtype"] = ">f4"
    elif fault in ("nonfinite", "bomb"):
        raw = np.full(12, np.nan, dtype="<f4").tobytes() if fault == "nonfinite" else b"x" * 10000
        encoded = gzip.compress(raw, mtime=0)
        path.write_bytes(encoded)
        chunk.update(bytes=len(encoded), sha256=digest(encoded), raw_sha256=digest(raw))
        row["sha256"] = digest(raw)
    elif fault == "symlink":
        path.unlink()
        path.symlink_to(SOURCE)
    if fault:
        with pytest.raises((ValueError, OSError)):
            get_arrays(tmp_path, inventory)
    else:
        assert np.array_equal(
            get_arrays(tmp_path, inventory)[0]["points"], np.arange(12, dtype="<f4").reshape(4, 3)
        )


def test_duplicate_json(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text('{"x":1,"x":2}')
    with pytest.raises(ValueError):
        read_json(p)


@pytest.mark.parametrize("fault", [None, "height", "filter", "state", "trace", "replica"])
def test_historical_binding(fault):
    plan = json.loads((BASE / "STUDY_PLAN.json").read_text())
    if fault == "height":
        plan["frames"][0]["ego_pos"][1] += 0.1
    elif fault == "filter":
        plan["frames"][0]["background"] = True
    elif fault == "state":
        plan["frames"][0]["state"][0] += 1
    elif fault == "trace":
        plan["frames"][0]["trace_sha256"] = "0" * 64
    elif fault == "replica":
        plan["frames"][0]["replica"] = 2
    if fault:
        with pytest.raises(ValueError):
            historical(ROOT, plan)
    else:
        historical(ROOT, plan)


@pytest.fixture(scope="module")
def witness(tmp_path_factory):
    from scipy.spatial.transform import Rotation
    from experiments.iter155_background_witness.check import verify

    raw = tmp_path_factory.mktemp("witness155")
    plan = json.loads((BASE / "STUDY_PLAN.json").read_text())
    plan["expected_selected_points"] = 101
    frame = plan["frames"][1]
    pos = frame["ego_pos"]
    points = np.tile(np.array([[pos[0], pos[1] + 0.5, pos[2] + 1.2]], dtype="<f4"), (101, 1))
    features = np.zeros((101, 12), dtype="<f4")
    features[:, 2] = 1
    arrays = {}
    for name, value in [
        ("population_xyz", points),
        ("selected_xyz", points),
        ("population_features", features),
        ("population_opacity", np.ones(101, dtype="<f4")),
        ("selection", np.ones(101, dtype="u1")),
    ]:
        put_array(raw, name, value, arrays)
    ground = np.tile(np.eye(4), (1252, 1, 1))
    ground[:, :3, 3] = 1000
    for j, f in enumerate(plan["frames"][:2]):
        ground[j, :3, 3] = f["ego_pos"]
    put_array(raw, "ground_poses", ground.astype("<f8"), arrays)
    record = {
        "status": "completed",
        "arrays": arrays,
        "new_driving_episodes": 0,
        "constructor_reset_step_render_calls": 0,
        "frames": [],
        "sources": {},
        "population_points": 101,
        "selected_points": 101,
        "numeric_environment": {
            "fixture": "NumPy CPU source-body evaluation; synthetic points and ground, no GPU outcome"
        },
    }
    env = SimpleNamespace()
    box_statements(ENV.read_text(), env, np)
    for f in plan["frames"][:2]:
        rotation = [0, f["state"][2], 0]
        box = (
            (Rotation.from_euler("XYZ", rotation).as_matrix() @ env.ego_verts.T).T + f["ego_pos"]
        ).astype("<f4")
        mask = background_function(SOURCE.read_text(), TORCH, mask=True)(points, box).astype("u1")
        count = int(mask.sum())
        put_array(raw, f"box_{f['frame']}", box, arrays)
        put_array(raw, f"mask_{f['frame']}", mask, arrays)
        record["frames"].append(
            {
                "frame": f["frame"],
                "time": f["time"],
                "rotation": rotation,
                "position": f["ego_pos"],
                "count": count,
                "collision": count > 100,
                "points": 101,
            }
        )
    assets = {}
    for name in [
        "hug_sim.py.txt",
        "score_calculator.py.txt",
        "sim_utils.py.txt",
        "gaussian_model.py.txt",
        "ground_model.py.txt",
    ]:
        data = (
            ENV.read_bytes()
            if name == "hug_sim.py.txt"
            else SOURCE.read_bytes()
            if name == "score_calculator.py.txt"
            else b"synthetic source identity fixture\n"
        )
        (raw / name).write_bytes(data)
        original = "/fixture/" + name
        identity = {"bytes": len(data), "sha256": digest(data)}
        assets[original] = identity
        record["sources"][name] = dict(identity, original=original)
    for name in ["scene.pth", "ground_param.pkl"]:
        assets["/datasets/nuscenes-full/hugsim/extracted/scenes/nuscenes/scene-0013/" + name] = {
            "sha256": "0" * 64,
            "bytes": 1,
        }
    record["configuration"] = {"scene_sha256": "0" * 64, "ground_sha256": "0" * 64}
    record["preflight_files"] = record["postflight_files"] = len(assets)
    (raw / "witness.json").write_text(json.dumps(record))
    result = verify(ROOT, raw, plan, assets)
    assert result["status"] == "supported" and [r["source_count"] for r in result["frames"]] == [
        0,
        101,
    ]
    return raw, plan, assets


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "extra",
        "missing",
        "selection",
        "point_drop",
        "height",
        "box",
        "mask",
        "count",
        "false_success",
        "source",
        "scene",
        "frame",
        "array_dtype",
    ],
)
def test_full_admission_known_bads(witness, tmp_path, fault):
    import shutil
    from experiments.iter155_background_witness.check import verify

    source, plan, assets = witness
    raw = tmp_path / "raw"
    shutil.copytree(source, raw)
    record = json.loads((raw / "witness.json").read_text())
    if fault == "extra":
        (raw / "unexpected").write_text("x")
    elif fault == "missing":
        (raw / "box_12_000.bin.gz").unlink()
    elif fault in ("selection", "point_drop", "height", "box", "mask", "array_dtype"):
        arrays = get_arrays(raw, record["arrays"])[0]
        name = {
            "selection": "selection",
            "point_drop": "selected_xyz",
            "height": "ground_poses",
            "box": "box_13",
            "mask": "mask_13",
            "array_dtype": "box_13",
        }[fault]
        value = arrays[name].copy()
        if fault == "selection":
            value[0] = 0
        elif fault == "point_drop":
            value = value[:-1]
        elif fault == "height":
            value[0, 1, 3] += 0.1
        elif fault == "box":
            value[0, 0] += 0.1
        elif fault == "mask":
            value[0] = 0
        else:
            value = value.astype("<f8")
        for chunk in record["arrays"][name]["chunks"]:
            (raw / chunk["path"]).unlink()
        put_array(raw, name, value, record["arrays"])
    elif fault == "count":
        record["frames"][0]["count"] = True
    elif fault == "false_success":
        record["status"] = "failed"
    elif fault == "source":
        record["sources"]["hug_sim.py.txt"]["sha256"] = "0" * 64
    elif fault == "scene":
        record["configuration"]["scene_sha256"] = "1" * 64
    elif fault == "frame":
        record["frames"].reverse()
    (raw / "witness.json").write_text(json.dumps(record))
    if fault:
        with pytest.raises((ValueError, OSError)):
            verify(ROOT, raw, plan, assets)
    else:
        assert verify(ROOT, raw, plan, assets)["status"] == "supported"


@pytest.mark.parametrize(
    "fault", [None, "archive_hash", "extra_member", "member_hash", "traversal", "link", "truncated"]
)
def test_collection(tmp_path, fault):
    import io
    import tarfile
    from experiments.iter155_background_witness.execute import extract_archive

    data = b"finite evidence"
    buffer = io.BytesIO()
    name = "../escape" if fault == "traversal" else "witness.json"
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        member = tarfile.TarInfo(name)
        member.size = len(data)
        if fault == "link":
            member.type = tarfile.SYMTYPE
            member.linkname = "/tmp/escape"
            member.size = 0
        tar.addfile(member, io.BytesIO(data))
        if fault == "extra_member":
            tar.addfile(tarfile.TarInfo("extra"))
    raw = buffer.getvalue()
    inventory = {
        "bytes": len(raw),
        "sha256": digest(raw),
        "files": {name: {"bytes": len(data), "sha256": digest(data)}},
    }
    if fault == "archive_hash":
        inventory["sha256"] = "0" * 64
    elif fault == "member_hash":
        inventory["files"][name]["sha256"] = "0" * 64
    elif fault == "truncated":
        raw = raw[:-5]
    if fault:
        with pytest.raises((ValueError, OSError)):
            extract_archive(raw, tmp_path / "raw", inventory)
    else:
        extract_archive(raw, tmp_path / "raw", inventory)
        assert (tmp_path / "raw/witness.json").read_bytes() == data
        with pytest.raises(FileExistsError):
            extract_archive(raw, tmp_path / "raw", inventory)


def test_raw_before_replay(witness):
    from experiments.iter155_background_witness.check import verify

    raw, plan, assets = witness
    with pytest.raises(ValueError):
        verify(ROOT, raw, plan, assets, raw_commit="HEAD")


@pytest.mark.parametrize("fault", [None, "late", "initialized", "watchdog", "not_denied", "clock"])
def test_retry_envelope(fault):
    from experiments.iter155_background_witness.execute import retry_wait

    budget = {"started_monotonic": 100, "deadline_monotonic": 1900}
    result = {
        "lifecycle": "start_denied_capacity",
        "watchdog_exit": 0,
        "extraction_launched": False,
        "finished_monotonic": 130,
    }
    now = 160
    plan = {"capacity_retry_wait_seconds": 120}
    if fault == "late":
        now = 1000
    elif fault == "initialized":
        result["extraction_launched"] = True
    elif fault == "watchdog":
        result["watchdog_exit"] = None
    elif fault == "not_denied":
        result["lifecycle"] = "failed"
    elif fault == "clock":
        now = 129
    if fault:
        with pytest.raises(ValueError):
            retry_wait(budget, result, now, plan)
    else:
        assert retry_wait(budget, result, now, plan) == 90
