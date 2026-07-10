from __future__ import annotations

import gzip
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments/iter40_timing_cost_audit/analyze_timing_cost.py"


def load_module():
    spec = importlib.util.spec_from_file_location("iter40_timing_cost", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_gzip(path: Path, rows: list[dict]):
    with gzip.open(path, "wt") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def test_iter40_parse_decision_blocks_assigns_brake_to_previous_frame(tmp_path):
    module = load_module()
    path = tmp_path / "log.jsonl.gz"
    write_gzip(
        path,
        [
            {"reset": True, "run": 0},
            {"run": 0, "ts": 100},
            {"brake": True, "run": 0},
            {"run": 0, "ts": 200},
            {"reset": True, "run": 1},
            {"run": 1, "ts": 300},
        ],
    )

    blocks = module.parse_decision_blocks(path)

    assert len(blocks) == 2
    assert blocks[0]["brakes"][0]["after_frame"] == 0
    assert module.block_first_last_brake_ts(blocks[0]) == (100, 100)


def test_iter40_contact_ts_gt_reconstructs_crossing():
    module = load_module()
    ego = {
        "0": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
        "100000": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
        "200000": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
    }
    actors = [
        {
            "timestamps": [0, 100000, 200000],
            "poses": [
                [[1, 0, 0, 3], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
                [[1, 0, 0, 1], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
                [[1, 0, 0, 0.5], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
            ],
        }
    ]

    assert module.contact_ts_gt(actors, ego, contact_m=2.0) == 100000


def test_iter40_s1_requires_all_best_episodes():
    module = load_module()
    episodes = [
        {
            "scenario_class": "stationary",
            "scenario_id": "0001",
            "brake_frame_count": 0,
            "intervention_episode": False,
            "ego_distance_m": 10.0,
            "best_metric_present": True,
            "off_collision": False,
        }
    ]

    report = module.evaluate_s1(episodes)

    assert not report["pass"]
    assert "episode_count=1 != 400" in report["failures"]


def test_iter40_s2_accepts_measured_leadtime_coverage():
    module = load_module()
    rows = []
    for i in range(20):
        rows.append(
            {
                "scenario_class": "frontal" if i < 10 else "side",
                "scenario_id": "x",
                "run_index": i,
                "status": "measured",
                "lead_time_s": float(i),
            }
        )

    report = module.evaluate_s2(rows)

    assert report["pass"]
    assert report["measured_rows"] == 20
    assert report["lead_time_summary_s"]["median"] == 10.0


def test_iter40_verdict_order():
    module = load_module()
    ok = {"pass": True}
    fail = {"pass": False}

    assert module.verdict(fail, None, None, None) == "TIMING_COST_INFRASTRUCTURE_NULL"
    assert module.verdict(ok, fail, None, None) == "TIMING_COST_NULL_COST_COVERAGE_INCOMPLETE"
    assert module.verdict(ok, ok, fail, None) == "TIMING_COST_NULL_LEADTIME_COVERAGE_INCOMPLETE"
    assert module.verdict(ok, ok, ok, fail) == "TIMING_COST_OVERCLAIM_NULL"
    assert module.verdict(ok, ok, ok, ok) == "TIMING_COST_AUDIT_PASS_SIMULATION_SCOPE"
