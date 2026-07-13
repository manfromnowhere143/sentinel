"""Iteration 53 HUGSIM first-fire channel audit tests."""

import importlib.util
import json
from pathlib import Path

import pytest

EXP = Path(__file__).resolve().parents[1] / "experiments" / "iter53_hugsim_first_fire_channel_audit"

spec = importlib.util.spec_from_file_location(
    "analyze_first_fire_channel",
    EXP / "analyze_first_fire_channel.py",
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


def base_row(**overrides):
    row = {
        "on_collision": True,
        "first_on_nc_time": 2.0,
        "first_fire_channel": "ttc_only",
        "first_fire_ts": 1.0,
        "brake_frames": 1,
        "first_brake_ts": 1.0,
    }
    row.update(overrides)
    return row


@pytest.mark.parametrize(
    ("min_ttc", "min_cpa", "channel"),
    [
        (2.4, 2.0, "ttc_only"),
        (10.0, 1.4, "cpa_only"),
        (2.4, 1.4, "both"),
        (10.0, 2.0, "fired_channel_unreconstructable"),
    ],
)
def test_first_fire_channel(min_ttc, min_cpa, channel):
    assert az.first_fire_channel({"min_ttc": min_ttc, "min_cpa": min_cpa}) == channel


def test_read_decisions_records_first_fire_only(tmp_path):
    path = write_decisions(tmp_path / "decisions.jsonl", [
        {"frame_index": 0, "ts": 0.0, "fired": False, "brake": False, "release": False,
         "min_ttc": 100.0, "min_cpa": 100.0},
        {"frame_index": 1, "ts": 0.25, "fired": True, "brake": True, "release": False,
         "min_ttc": 1.5, "min_cpa": 10.0, "pre_braking": False},
        {"frame_index": 2, "ts": 0.50, "fired": True, "brake": True, "release": False,
         "min_ttc": 1.0, "min_cpa": 1.0, "pre_braking": True},
    ])
    rec = az.read_decisions(path)
    assert rec["monitor_frames"] == 3
    assert rec["fired_frames"] == 2
    assert rec["brake_frames"] == 2
    assert rec["first_fire_ts"] == pytest.approx(0.25)
    assert rec["first_fire_channel"] == "ttc_only"
    assert rec["first_fire_min_ttc"] == pytest.approx(1.5)
    assert rec["first_fire_min_cpa"] == pytest.approx(10.0)


def test_read_decisions_no_fire(tmp_path):
    path = write_decisions(tmp_path / "decisions.jsonl", [
        {"frame_index": 0, "ts": 0.0, "fired": False, "brake": False, "release": False,
         "min_ttc": 100.0, "min_cpa": 100.0},
    ])
    rec = az.read_decisions(path)
    assert rec["first_fire_channel"] == "no_fire"
    assert rec["first_fire_ts"] is None


@pytest.mark.parametrize(
    ("sample", "label"),
    [
        (base_row(on_collision=False), "no_on_collision"),
        (base_row(first_on_nc_time=None), "unknown_collision_time"),
        (base_row(first_fire_channel="no_fire", first_fire_ts=None), "no_fire"),
        (base_row(first_on_nc_time=2.0, first_fire_ts=2.25), "post_collision_fire"),
        (base_row(first_on_nc_time=2.0, first_fire_ts=1.0), "short_lead_fire"),
        (base_row(first_on_nc_time=2.0, first_fire_ts=0.75), "long_lead_fire"),
    ],
)
def test_fire_timing_label(sample, label):
    assert az.fire_timing_label(sample) == label


def test_iter52_timing_bin_recompute():
    assert az.iter52_timing_bin_from_current(
        base_row(on_collision=False)
    ) == "excluded_no_on_collision"
    assert az.iter52_timing_bin_from_current(
        base_row(brake_frames=0, first_brake_ts=None)
    ) == "no_brake_no_surface_proxy"
    assert az.iter52_timing_bin_from_current(
        base_row(first_on_nc_time=2.0, first_brake_ts=2.25)
    ) == "post_collision_first_brake"
    assert az.iter52_timing_bin_from_current(
        base_row(first_on_nc_time=2.0, first_brake_ts=1.0)
    ) == "short_lead_brake"
    assert az.iter52_timing_bin_from_current(
        base_row(first_on_nc_time=2.0, first_brake_ts=0.75)
    ) == "long_lead_brake"


def test_collect_dataset_one_pair_and_iter52_cross_check(tmp_path):
    root = tmp_path / "episodes"
    write_eval(root / "scene-0001-hard-00__off_r1" / "eval.json", hdscore=0.2)
    write_eval(
        root / "scene-0001-hard-00__on_r1" / "eval.json",
        hdscore=0.3,
        nc=1.0,
        detail_ncs=[1.0, 0.0],
    )
    write_decisions(root / "scene-0001-hard-00__on_r1" / "sentinel_iter48_decisions.jsonl", [
        {"frame_index": 0, "ts": 0.0, "fired": True, "brake": True, "release": False,
         "min_ttc": 1.0, "min_cpa": 10.0, "pre_braking": False},
    ])
    problems: list[str] = []
    rows = az.collect_dataset("toy", root, problems)
    assert len(rows) == 1
    assert rows[0]["first_fire_channel"] == "ttc_only"
    assert rows[0]["fire_timing_label"] == "short_lead_fire"
    assert "toy:pair-count:1!=52" in problems

    report = tmp_path / "iter52.json"
    report.write_text(json.dumps({
        "pairs": [{**rows[0], "timing_bin": "short_lead_brake"}],
    }))
    problems = []
    cross = az.check_iter52(rows, report, problems)
    assert problems == []
    assert cross["timing_bin_mismatches"] == 0


def test_summarize_pre_collision_channel_counts():
    rows = [
        {**base_row(first_fire_channel="ttc_only"), "delta_hd": 0.04,
         "material_gain": True, "material_loss": False,
         "first_fire_lead_time": 1.0,
         "fire_timing_label": "short_lead_fire",
         "iter52_timing_bin_recomputed": "short_lead_brake"},
        {**base_row(first_fire_channel="cpa_only", first_fire_ts=0.5), "delta_hd": -0.04,
         "material_gain": False, "material_loss": True,
         "first_fire_lead_time": 1.5,
         "fire_timing_label": "long_lead_fire",
         "iter52_timing_bin_recomputed": "long_lead_brake"},
        {**base_row(on_collision=False, first_fire_channel="no_fire", first_fire_ts=None),
         "delta_hd": 0.0, "material_gain": False, "material_loss": False,
         "first_fire_lead_time": None,
         "fire_timing_label": "no_on_collision",
         "iter52_timing_bin_recomputed": "excluded_no_on_collision"},
    ]
    summary = az.summarize(rows)
    assert summary["pairs"] == 3
    assert summary["on_collision_pairs"] == 2
    assert summary["pre_collision_fire_pairs"] == 2
    assert summary["pre_collision_fire_channel_counts"]["ttc_only"] == 1
    assert summary["pre_collision_fire_channel_counts"]["cpa_only"] == 1
