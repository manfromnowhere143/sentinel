"""Iteration 51 HUGSIM transfer-failure taxonomy tests."""

import importlib.util
import json
from pathlib import Path

import pytest

EXP = Path(__file__).resolve().parents[1] / "experiments" / "iter51_hugsim_failure_taxonomy"

spec = importlib.util.spec_from_file_location(
    "analyze_failure_taxonomy",
    EXP / "analyze_failure_taxonomy.py",
)
az = importlib.util.module_from_spec(spec)
spec.loader.exec_module(az)


def write_eval(path: Path, *, hdscore=0.5, nc=1.0, detail_ncs=None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if detail_ncs is None:
        detail_ncs = [nc]
    details = {
        f"{(idx + 1) * 0.25:.2f}": {"nc": val}
        for idx, val in enumerate(detail_ncs)
    }
    path.write_text(json.dumps({
        "hdscore": hdscore,
        "nc": nc,
        "details": details,
    }))
    return path


def write_decisions(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    return path


def base_pair(**overrides):
    pair = {
        "off_primary_collision": True,
        "on_primary_collision": True,
        "delta_hd": 0.0,
        "brake_frames": 1,
        "first_brake_ts": 0.25,
        "off_first_nc_time": 0.5,
    }
    pair.update(overrides)
    return pair


def test_eval_primary_collision_from_details_and_first_time(tmp_path):
    path = write_eval(tmp_path / "eval.json", nc=1.0, detail_ncs=[1.0, 0.5, 0.0])
    rec = az.read_eval_metrics(path)
    assert rec["primary_collision"]
    assert rec["nc_min"] == 0.0
    assert rec["first_nc_time"] == pytest.approx(0.5)
    assert rec["first_nc_source"] == "details"


def test_eval_top_level_only_collision_has_no_first_time(tmp_path):
    path = write_eval(tmp_path / "eval.json", nc=0.5, detail_ncs=[1.0, 1.0])
    rec = az.read_eval_metrics(path)
    assert rec["primary_collision"]
    assert rec["first_nc_time"] is None
    assert rec["first_nc_source"] == "top_level_only"


def test_eval_rejects_non_numeric_nc(tmp_path):
    path = tmp_path / "eval.json"
    path.write_text(json.dumps({"hdscore": 1.0, "nc": "bad", "details": {}}))
    with pytest.raises(ValueError, match="non-numeric nc"):
        az.read_eval_metrics(path)


def test_decision_summary_ignores_trace_error_and_records_firsts(tmp_path):
    path = write_decisions(tmp_path / "decisions.jsonl", [
        {"trace_error": "x"},
        {"frame_index": 0, "ts": 0.0, "fired": False, "brake": False, "release": False,
         "min_ttc": 10.0, "min_cpa": 5.0, "objs": []},
        {"frame_index": 1, "ts": 0.25, "fired": True, "brake": True, "release": False,
         "min_ttc": 2.0, "min_cpa": 1.5, "objs": [{"id": 1}]},
        {"frame_index": 2, "ts": 0.5, "fired": False, "brake": True, "release": True,
         "min_ttc": 4.0, "min_cpa": 3.0, "objs": []},
    ])
    rec = az.read_decision_summary(path)
    assert rec["monitor_frames"] == 3
    assert rec["fired_frames"] == 1
    assert rec["brake_frames"] == 2
    assert rec["release_frames"] == 1
    assert rec["first_fire_ts"] == pytest.approx(0.25)
    assert rec["first_brake_ts"] == pytest.approx(0.25)
    assert rec["brake_fraction"] == pytest.approx(2 / 3)
    assert rec["min_monitor_ttc"] == pytest.approx(2.0)
    assert rec["min_monitor_cpa"] == pytest.approx(1.5)
    assert rec["object_rows"] == 1


@pytest.mark.parametrize(
    ("pair", "category"),
    [
        (base_pair(off_primary_collision=False, on_primary_collision=True),
         "induced_collision"),
        (base_pair(off_primary_collision=False, on_primary_collision=False),
         "clean_no_off_opportunity"),
        (base_pair(on_primary_collision=False, delta_hd=0.031),
         "converted_collision_material_gain"),
        (base_pair(on_primary_collision=False, delta_hd=0.030),
         "converted_collision_no_material_gain"),
        (base_pair(brake_frames=0), "persistent_collision_no_brake"),
        (base_pair(first_brake_ts=0.75, off_first_nc_time=0.5),
         "persistent_collision_late_by_proxy"),
        (base_pair(first_brake_ts=0.25, off_first_nc_time=0.5),
         "persistent_collision_early_by_proxy"),
        (base_pair(first_brake_ts=0.25, off_first_nc_time=None),
         "persistent_collision_late_by_proxy"),
    ],
)
def test_assign_category_order(pair, category):
    assert az.assign_category(pair) == category


def test_enrich_pair_secondary_flags():
    pair = az.enrich_pair(base_pair(delta_hd=-0.04, brake_frames=3))
    assert pair["category"] == "persistent_collision_early_by_proxy"
    assert pair["material_loss"]
    assert pair["score_loss_under_brake"]
    assert pair["persistent_collision"]
    assert not pair["converted_collision"]


def test_summary_dominance_uses_off_opportunity_pairs_only():
    pairs = []
    for _ in range(4):
        pairs.append(az.enrich_pair(base_pair(delta_hd=0.0)))
    for _ in range(6):
        pairs.append(az.enrich_pair(
            base_pair(off_primary_collision=False, on_primary_collision=False, delta_hd=0.0)
        ))
    summary = az.summarize_pairs(pairs)
    assert summary["off_opportunity_pairs"] == 4
    assert summary["dominant_category"] == "persistent_collision_early_by_proxy"
    assert summary["dominant_category_fraction"] == pytest.approx(1.0)


def test_attackplanner_scenario_rule():
    assert az.is_attackplanner_scenario("scene-0013-extreme-00")
    assert az.is_attackplanner_scenario("scene-0041-hard-00")
    assert az.is_attackplanner_scenario("scene-0411-hard-00")
    assert not az.is_attackplanner_scenario("scene-0051-hard-00")


def test_collect_dataset_cross_checks_transfer_mean(tmp_path):
    root = tmp_path / "episodes"
    write_eval(root / "scene-0001-hard-00__off_r1" / "eval.json", hdscore=0.2, nc=0.0)
    write_eval(root / "scene-0001-hard-00__on_r1" / "eval.json", hdscore=0.5, nc=0.0)
    write_decisions(root / "scene-0001-hard-00__on_r1" / "sentinel_iter48_decisions.jsonl", [
        {"frame_index": 0, "ts": 0.0, "fired": False, "brake": False, "release": False},
    ])
    transfer = tmp_path / "transfer.json"
    transfer.write_text(json.dumps({"primary": {"pairs": 1, "point_mean": 0.3}}))
    problems: list[str] = []
    pairs = az.collect_dataset("toy", root, transfer, problems)
    assert len(pairs) == 1
    assert "toy:pair-count:1!=52" in problems
    assert not any(problem.startswith("toy:transfer-mean-mismatch") for problem in problems)
