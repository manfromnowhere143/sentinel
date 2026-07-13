"""Iteration 58 HUGSIM provenance canary analyzer tests."""

import importlib.util
import json
import sys
from pathlib import Path

EXP = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter58_hugsim_provenance_instrumented_canary"
)

spec = importlib.util.spec_from_file_location(
    "analyze_provenance_canary", EXP / "analyze_provenance_canary.py"
)
az = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = az
spec.loader.exec_module(az)


def write_episode(root: Path, episode: str, *, provenance=True, nc=0.0, decision=False):
    ep = root / "episodes" / episode
    ep.mkdir(parents=True)
    ev = {
        "nc": nc,
        "dac": 1.0,
        "ttc": 1.0,
        "c": 1.0,
        "pdms": 1.0,
        "rc": 1.0,
        "hdscore": 1.0,
        "details": {"0.0": {"nc": nc, "dac": 1.0, "ttc": 1.0, "c": 1.0, "pdms": 1.0}},
    }
    if provenance:
        ev["collision_provenance"] = [{"source": "nc", "collision_type": "foreground"}]
    (ep / "eval.json").write_text(json.dumps(ev))
    (ep / "output.txt").write_text("sent\n")
    (ep / "episode_meta.json").write_text("{}")
    if decision:
        (ep / "sentinel_iter48_decisions.jsonl").write_text('{"frame":0}\n')


def test_complete_when_collision_provenance_top_level(tmp_path):
    (tmp_path / "receipts.json").write_text("{}")
    write_episode(tmp_path, "scene-0013-hard-00__off_r1", provenance=True)
    write_episode(tmp_path, "scene-0013-hard-00__on_r1", provenance=True, decision=True)
    report = az.build_report(tmp_path)
    assert report["verdict"] == "PROVENANCE_CANARY_COMPLETE"
    assert report["summary"]["provenance_rows"] == 2


def test_null_when_collision_has_no_provenance(tmp_path):
    (tmp_path / "receipts.json").write_text("{}")
    write_episode(tmp_path, "scene-0013-hard-00__off_r1", provenance=False)
    write_episode(tmp_path, "scene-0013-hard-00__on_r1", provenance=False, decision=True)
    report = az.build_report(tmp_path)
    assert report["verdict"] == "PROVENANCE_CANARY_NULL"


def test_infra_null_when_details_contain_extra_keys(tmp_path):
    (tmp_path / "receipts.json").write_text("{}")
    write_episode(tmp_path, "scene-0013-hard-00__off_r1", provenance=True)
    write_episode(tmp_path, "scene-0013-hard-00__on_r1", provenance=True, decision=True)
    ev_path = tmp_path / "episodes" / "scene-0013-hard-00__off_r1" / "eval.json"
    ev = json.loads(ev_path.read_text())
    ev["details"]["0.0"]["collision_provenance"] = []
    ev_path.write_text(json.dumps(ev))
    report = az.build_report(tmp_path)
    assert report["verdict"] == "CANARY_INFRA_NULL"
    assert "details-extra-keys:0.0:collision_provenance" in report["episodes"][0]["problems"]
