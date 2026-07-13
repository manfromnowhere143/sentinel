from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter64_unsupported_temporal_surface_audit"
    / "analyze_unsupported_temporal.py"
)
SPEC = importlib.util.spec_from_file_location("iter64_unsupported_temporal", MODULE_PATH)
assert SPEC is not None
unsupported = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(unsupported)


def _eval_doc(obs_forward: float = 10.0) -> dict:
    return {
        "collision_provenance": [
            {
                "timestamp": 3.0,
                "collision_type": "foreground",
                "obs_index": 0,
                "obs_name": "car",
                "obs_box": [obs_forward, 0.0],
            }
        ]
    }


def _decision_row(ts: float, object_y: float | None) -> dict:
    objs = []
    if object_y is not None:
        objs.append({"id": 1, "score": 0.7, "world": [0.0, object_y], "vel": [0.0, 0.0]})
    return {
        "frame_index": int(ts),
        "ts": ts,
        "l2g_r_mat": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        "l2g_t": [0.0, 0.0, 0.0],
        "objs": objs,
    }


def _proof_and_reports(tmp_path: Path, row_values: list[list[float | None]]) -> tuple[Path, Path, Path]:
    proof_root = tmp_path / "proof"
    proof_root.mkdir()
    rows61 = []
    for (audit_id, scenario), values in zip(unsupported.EXPECTED_ROWS, row_values, strict=True):
        ep = proof_root / "episodes" / f"{audit_id}__{scenario}__on"
        ep.mkdir(parents=True)
        (ep / "eval.json").write_text(json.dumps(_eval_doc()))
        decisions = [_decision_row(float(idx), object_y) for idx, object_y in enumerate(values)]
        (ep / "sentinel_iter48_decisions.jsonl").write_text(
            "\n".join(json.dumps(row) for row in decisions) + "\n"
        )
        rows61.append({"audit_id": audit_id, "scenario": scenario, "row_label": "no_monitor_object_support"})
    iter59_report = tmp_path / "iter59_report.json"
    iter59_report.write_text(json.dumps({"verdict": "ACTOR_MATCH_AUDIT_COMPLETE"}))
    iter61_report = tmp_path / "iter61_report.json"
    iter61_report.write_text(json.dumps({
        "verdict": "OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE",
        "episodes": rows61,
    }))
    return proof_root, iter59_report, iter61_report


def test_unsupported_temporal_match_complete_when_any_row_matches(tmp_path: Path) -> None:
    proof_root, iter59, iter61 = _proof_and_reports(tmp_path, [[20.0, 10.0, 20.0], [100.0, 100.0, 100.0]])

    report = unsupported.build_report(proof_root, iter59, iter61)

    assert report["verdict"] == "UNSUPPORTED_TEMPORAL_MATCH_COMPLETE"
    assert report["episodes"][0]["row_label"] == "pre_contact_object_match"
    assert report["episodes"][0]["best_distance_m"] == 0.0


def test_unsupported_temporal_ambiguous_when_no_match_but_close(tmp_path: Path) -> None:
    proof_root, iter59, iter61 = _proof_and_reports(tmp_path, [[14.0, 20.0, 20.0], [100.0, 100.0, 100.0]])

    report = unsupported.build_report(proof_root, iter59, iter61)

    assert report["verdict"] == "UNSUPPORTED_TEMPORAL_AMBIGUOUS_NULL"
    assert report["episodes"][0]["row_label"] == "pre_contact_object_ambiguous"


def test_unsupported_temporal_no_support_complete_when_both_rows_far(tmp_path: Path) -> None:
    proof_root, iter59, iter61 = _proof_and_reports(tmp_path, [[100.0, 100.0, 100.0], [90.0, 90.0, 90.0]])

    report = unsupported.build_report(proof_root, iter59, iter61)

    assert report["verdict"] == "UNSUPPORTED_TEMPORAL_NO_SUPPORT_COMPLETE"
    assert report["summary"]["row_label_counts"] == {"temporal_no_object_support": 2}


def test_unsupported_temporal_support_null_when_surface_insufficient(tmp_path: Path) -> None:
    proof_root, iter59, iter61 = _proof_and_reports(tmp_path, [[None, 100.0, None], [90.0, 90.0, 90.0]])

    report = unsupported.build_report(proof_root, iter59, iter61)

    assert report["verdict"] == "UNSUPPORTED_TEMPORAL_SUPPORT_NULL"
    assert report["episodes"][0]["row_label"] == "insufficient_temporal_surface"


def test_unsupported_temporal_infra_null_when_crosscheck_fails(tmp_path: Path) -> None:
    proof_root, iter59, iter61 = _proof_and_reports(tmp_path, [[100.0, 100.0, 100.0], [90.0, 90.0, 90.0]])
    iter61.write_text(json.dumps({"verdict": "WRONG", "episodes": []}))

    report = unsupported.build_report(proof_root, iter59, iter61)

    assert report["verdict"] == "UNSUPPORTED_TEMPORAL_INFRA_NULL"
    assert "iter61-verdict-not-OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE" in report["infra_problems"]
