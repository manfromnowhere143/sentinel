"""Iteration 54 HUGSIM provenance support audit tests."""

import importlib.util
import json
from pathlib import Path

EXP = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter54_hugsim_provenance_support_audit"
)

spec = importlib.util.spec_from_file_location(
    "analyze_provenance_support",
    EXP / "analyze_provenance_support.py",
)
az = importlib.util.module_from_spec(spec)
spec.loader.exec_module(az)


def decision_row(**overrides):
    row = {
        "frame_index": 0,
        "ts": 0.0,
        "fired": True,
        "brake": True,
        "min_cpa": 0.5,
        "min_ttc": 1_000_000_000.0,
        "params": {"dt": 0.5, "min_closing": 3.0},
        "l2g_r_mat": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        "l2g_t": [0.0, 0.0, 0.0],
        "traj": [[0.0, 1.0], [0.0, 2.0]],
        "objs": [{"id": 7, "world": [0.0, 0.5], "vel": [0.0, 0.0]}],
    }
    row.update(overrides)
    return row


def write_json(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return path


def write_decisions(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    return path


def eval_doc(*, nc=1.0, identity=False):
    row = {"nc": nc, "dac": 1.0, "ttc": 1.0, "c": 1.0, "pdms": 1.0}
    if identity:
        row["collision_agents"] = [{"track_id": 4}]
    return {
        "hdscore": 0.5,
        "nc": nc,
        "details": {"0.25": row},
    }


def test_reconstructs_unique_cpa_object():
    row = decision_row()
    rec = az.reconstruct_argmins(row)
    assert [item["id"] for item in rec["cpa_argmins"]] == [7]
    assert rec["ttc_argmins"] == []
    assert az.monitor_provenance_label("cpa_only", [7], []) == "unique_cpa_object"


def test_reconstructs_unique_ttc_object():
    row = decision_row(
        min_cpa=10.0,
        min_ttc=2.0,
        objs=[{"id": 8, "world": [0.0, 10.0], "vel": [0.0, -5.0]}],
    )
    rec = az.reconstruct_argmins(row)
    assert [item["id"] for item in rec["ttc_argmins"]] == [8]
    assert az.monitor_provenance_label("ttc_only", [], [8]) == "unique_ttc_object"


def test_labels_ambiguous_cpa_object():
    row = decision_row(
        objs=[
            {"id": 1, "world": [0.0, 0.5], "vel": [0.0, 0.0]},
            {"id": 2, "world": [0.0, 0.5], "vel": [0.0, 0.0]},
        ],
    )
    rec = az.reconstruct_argmins(row)
    ids = [item["id"] for item in rec["cpa_argmins"]]
    assert ids == [1, 2]
    assert az.monitor_provenance_label("cpa_only", ids, []) == "ambiguous_cpa_object"


def test_collision_actor_support_detection(tmp_path):
    no_actor = az.read_eval(write_json(tmp_path / "no_actor.json", eval_doc()))
    with_actor = az.read_eval(write_json(tmp_path / "with_actor.json", eval_doc(identity=True)))
    assert no_actor["collision_actor_support_label"] == "collision_actor_not_logged"
    assert with_actor["collision_actor_support_label"] == "collision_actor_supported"
    assert "details.0.25.collision_agents" in with_actor["collision_actor_identity_fields"]


def test_read_decisions_no_fire(tmp_path):
    path = write_decisions(tmp_path / "decisions.jsonl", [
        decision_row(fired=False, brake=False, min_cpa=10.0),
    ])
    rec = az.read_decisions(path)
    assert rec["first_fire_channel"] == "no_fire"
    assert rec["monitor_provenance_label"] == "no_fire"


def test_collect_dataset_and_iter53_cross_check(tmp_path, monkeypatch):
    monkeypatch.setattr(az, "EXPECTED_PAIRS_PER_DATASET", 1)
    root = tmp_path / "episodes"
    on_dir = root / "scene-0001-hard-00__on_r1"
    write_json(on_dir / "eval.json", eval_doc(nc=0.0))
    write_decisions(on_dir / "sentinel_iter48_decisions.jsonl", [decision_row()])
    problems: list[str] = []
    rows = az.collect_dataset("toy", root, problems)
    assert problems == []
    assert rows[0]["monitor_provenance_label"] == "unique_cpa_object"
    assert rows[0]["collision_actor_support_label"] == "collision_actor_not_logged"

    report = tmp_path / "iter53.json"
    report.write_text(json.dumps({
        "pairs": [{
            "dataset": "toy",
            "scenario": "scene-0001-hard-00",
            "run": 1,
            "first_fire_channel": "cpa_only",
            "fire_timing_label": rows[0]["fire_timing_label"],
        }],
    }))
    cross = az.check_iter53(rows, report, problems)
    assert problems == []
    assert cross["channel_mismatches"] == 0


def test_choose_verdict_support_null_vs_complete():
    base = {"on_collision": True}
    assert az.choose_verdict(["bad"], []) == "PROVENANCE_SUPPORT_INFRASTRUCTURE_NULL"
    assert az.choose_verdict([], [
        {**base, "collision_actor_support_label": "collision_actor_not_logged"},
    ]) == "PROVENANCE_SUPPORT_NULL"
    assert az.choose_verdict([], [
        {**base, "collision_actor_support_label": "collision_actor_supported"},
    ]) == "PROVENANCE_SUPPORT_COMPLETE"
