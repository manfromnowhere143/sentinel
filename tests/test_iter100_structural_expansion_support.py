from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter100_hugsim_structural_expansion_support_audit"
    / "analyze_structural_expansion_support.py"
)
SPEC = importlib.util.spec_from_file_location("iter100_expansion", MODULE_PATH)
assert SPEC is not None
expansion = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(expansion)


def _iter54_report(*, collision_supported: int = 0) -> dict:
    return {
        "verdict": expansion.ITER54_VERDICT,
        "infrastructure_problems": [],
        "summaries": {
            "combined": {
                "pairs": 104,
                "on_collision_pairs": 92,
                "collision_actor_support_counts": {
                    "collision_actor_supported": collision_supported,
                    "collision_actor_not_logged": 104 - collision_supported,
                },
                "collision_actor_support_on_collision_counts": {
                    "collision_actor_supported": 0,
                    "collision_actor_not_logged": 92,
                },
                "monitor_provenance_counts": {
                    "unique_ttc_object": 40,
                    "unique_cpa_object": 36,
                    "both_distinct_objects": 1,
                    "unique_both_same_object": 0,
                    "no_fire": 27,
                    "argmin_reconstruction_failed": 0,
                    "schema_unsupported": 0,
                },
                "collision_actor_identity_fields": [],
            }
        },
    }


def _iter59_report() -> dict:
    return {
        "verdict": expansion.ITER59_VERDICT,
        "infra_problems": [],
        "summary": {
            "completed_rows": 8,
            "support_counts": {
                "classifiable_foreground": 3,
                "no_monitor_fire": 2,
                "post_collision_fire": 2,
                "background_collision_only": 1,
            },
        },
    }


def _iter99_report() -> dict:
    return {
        "verdict": expansion.ITER99_VERDICT,
        "infra_problems": [],
        "summary": {
            "target_rows": 5,
            "covered_rows": 5,
            "compatible_rows": 5,
            "uncovered_rows": 0,
            "duplicate_or_incompatible_rows": 0,
        },
    }


def _reports(
    tmp_path: Path,
    *,
    iter54_verdict: str = expansion.ITER54_VERDICT,
    collision_supported: int = 0,
) -> tuple[Path, Path, Path]:
    iter54 = _iter54_report(collision_supported=collision_supported)
    iter54["verdict"] = iter54_verdict
    iter54_path = tmp_path / "iter54.json"
    iter59_path = tmp_path / "iter59.json"
    iter99_path = tmp_path / "iter99.json"
    iter54_path.write_text(json.dumps(iter54))
    iter59_path.write_text(json.dumps(_iter59_report()))
    iter99_path.write_text(json.dumps(_iter99_report()))
    return iter54_path, iter59_path, iter99_path


def test_structural_expansion_support_boundary_null(tmp_path: Path) -> None:
    report = expansion.build_report(*_reports(tmp_path))

    assert report["verdict"] == "HUGSIM_STRUCTURAL_EXPANSION_SUPPORT_BOUNDARY_NULL"
    assert report["event"]["row_label"] == "expansion_boundary_no_collision_actor_support"
    assert report["summary"]["broad_committed_transfer_pairs"] == 104
    assert report["summary"]["monitor_side_supported_pairs"] == 77
    assert report["summary"]["collision_actor_supported_pairs"] == 0
    assert report["summary"]["new_instrumentation_required_for_larger_structural_bridge"] is True


def test_structural_expansion_support_blocks_bad_iter54_verdict(tmp_path: Path) -> None:
    report = expansion.build_report(*_reports(tmp_path, iter54_verdict="WRONG"))

    assert report["verdict"] == "HUGSIM_STRUCTURAL_EXPANSION_SUPPORT_BLOCKED"
    assert "iter54-verdict-not-PROVENANCE_SUPPORT_NULL" in report["infra_problems"]


def test_structural_expansion_support_blocks_changed_collision_count(tmp_path: Path) -> None:
    report = expansion.build_report(*_reports(tmp_path, collision_supported=1))

    assert report["verdict"] == "HUGSIM_STRUCTURAL_EXPANSION_SUPPORT_BLOCKED"
    assert any(problem.startswith("iter54-collision_actor_supported-mismatch:") for problem in report["infra_problems"])
