"""Iteration 52 ON-collision timing audit tests."""

import importlib.util
import json
from pathlib import Path

import pytest

EXP = Path(__file__).resolve().parents[1] / "experiments" / "iter52_hugsim_on_collision_timing_audit"

spec = importlib.util.spec_from_file_location(
    "analyze_on_collision_timing",
    EXP / "analyze_on_collision_timing.py",
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
    path.write_text(json.dumps({"hdscore": hdscore, "nc": nc, "details": details}))
    return path


def write_decisions(path: Path, rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    return path


def row(**overrides):
    base = {
        "on_collision": True,
        "first_on_nc_time": 2.0,
        "first_brake_ts": 1.0,
        "brake_frames": 1,
        "surface_proxy_rows": 0,
    }
    base.update(overrides)
    return base


def test_read_eval_collision_time_from_details(tmp_path):
    path = write_eval(tmp_path / "eval.json", nc=1.0, detail_ncs=[1.0, 0.5, 0.0])
    rec = az.read_eval(path)
    assert rec["collision"]
    assert rec["nc_min"] == 0.0
    assert rec["first_nc_time"] == pytest.approx(0.5)
    assert rec["first_nc_source"] == "details"


def test_read_eval_top_level_only_collision_has_unknown_time(tmp_path):
    path = write_eval(tmp_path / "eval.json", nc=0.5, detail_ncs=[1.0, 1.0])
    rec = az.read_eval(path)
    assert rec["collision"]
    assert rec["first_nc_time"] is None
    assert rec["first_nc_source"] == "top_level_only"


def test_decision_surface_proxy_and_first_brake(tmp_path):
    path = write_decisions(tmp_path / "decisions.jsonl", [
        {"trace_error": "skip"},
        {"frame_index": 0, "ts": 0.0, "fired": False, "brake": False, "release": False,
         "min_ttc": 2.4, "min_cpa": 1.6},
        {"frame_index": 1, "ts": 0.25, "fired": True, "brake": True, "release": False,
         "min_ttc": 2.4, "min_cpa": 1.4},
        {"frame_index": 2, "ts": 0.50, "fired": False, "brake": True, "release": True,
         "min_ttc": 3.0, "min_cpa": 1.0},
    ])
    rec = az.read_decisions(path)
    assert rec["monitor_frames"] == 3
    assert rec["fired_frames"] == 1
    assert rec["brake_frames"] == 2
    assert rec["release_frames"] == 1
    assert rec["surface_proxy_rows"] == 1
    assert rec["first_surface_proxy_ts"] == pytest.approx(0.25)
    assert rec["first_brake_ts"] == pytest.approx(0.25)


@pytest.mark.parametrize(
    ("sample", "timing_bin"),
    [
        (row(on_collision=False), "excluded_no_on_collision"),
        (row(first_on_nc_time=None), "unknown_collision_time"),
        (row(brake_frames=0, surface_proxy_rows=0, first_brake_ts=None),
         "no_brake_no_surface_proxy"),
        (row(brake_frames=0, surface_proxy_rows=2, first_brake_ts=None),
         "no_brake_surface_proxy_present"),
        (row(first_on_nc_time=2.0, first_brake_ts=2.25), "post_collision_first_brake"),
        (row(first_on_nc_time=2.0, first_brake_ts=1.0), "short_lead_brake"),
        (row(first_on_nc_time=2.0, first_brake_ts=0.75), "long_lead_brake"),
    ],
)
def test_assign_timing_bin(sample, timing_bin):
    assert az.assign_timing_bin(sample) == timing_bin


def test_summarize_families_and_bin_stats():
    rows = []
    for timing_bin in [
        "no_brake_no_surface_proxy",
        "post_collision_first_brake",
        "short_lead_brake",
        "long_lead_brake",
        "excluded_no_on_collision",
    ]:
        r = {
            "on_collision": timing_bin != "excluded_no_on_collision",
            "timing_bin": timing_bin,
            "delta_hd": 0.04 if timing_bin == "long_lead_brake" else -0.04,
            "material_gain": timing_bin == "long_lead_brake",
            "material_loss": timing_bin != "long_lead_brake",
            "lead_time": 2.0 if timing_bin == "long_lead_brake" else None,
            "brake_frames": 3 if "brake" in timing_bin else 0,
        }
        rows.append(r)
    summary = az.summarize(rows)
    assert summary["pairs"] == 5
    assert summary["on_collision_pairs"] == 4
    assert summary["excluded_no_on_collision"] == 1
    assert summary["absent_or_post_collision_brake_family"] == 2
    assert summary["pre_collision_brake_family"] == 2
    assert summary["bin_stats"]["long_lead_brake"]["material_gain_pairs"] == 1


def test_collect_dataset_builds_one_pair_and_reports_count_problem(tmp_path):
    root = tmp_path / "episodes"
    write_eval(root / "scene-0001-hard-00__off_r1" / "eval.json", hdscore=0.2)
    write_eval(
        root / "scene-0001-hard-00__on_r1" / "eval.json",
        hdscore=0.3,
        nc=1.0,
        detail_ncs=[1.0, 0.0],
    )
    write_decisions(root / "scene-0001-hard-00__on_r1" / "sentinel_iter48_decisions.jsonl", [
        {"frame_index": 0, "ts": 0.0, "fired": False, "brake": False, "release": False,
         "min_ttc": 10.0, "min_cpa": 10.0},
    ])
    problems: list[str] = []
    rows = az.collect_dataset("toy", root, problems)
    assert len(rows) == 1
    assert rows[0]["timing_bin"] == "no_brake_no_surface_proxy"
    assert "toy:pair-count:1!=52" in problems


def test_iter51_cross_report_checks_on_collision_count(tmp_path):
    report = tmp_path / "iter51.json"
    report.write_text(json.dumps({"pairs": [{"on_primary_collision": True}, {}]}))
    problems: list[str] = []
    cross = az.check_iter51_cross_report(
        [{"on_collision": True}, {"on_collision": False}],
        report,
        problems,
    )
    assert problems == []
    assert cross["iter51_pairs"] == 2
    assert cross["iter51_on_collision_pairs"] == 1
