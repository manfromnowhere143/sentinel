from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter102_hugsim_provenance_batch_launch_manifest"
    / "analyze_provenance_batch_launch_manifest.py"
)
SPEC = importlib.util.spec_from_file_location("iter102_manifest", MODULE_PATH)
assert SPEC is not None
manifest = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(manifest)


ROWS = [
    ("iter48_easy_medium", "no_fire", "scene-0013-easy-00", 1),
    ("iter48_easy_medium", "no_fire", "scene-0013-easy-00", 2),
    ("iter48_easy_medium", "unique_cpa_object", "scene-0038-medium-01", 1),
    ("iter48_easy_medium", "unique_cpa_object", "scene-0062-medium-00", 2),
    ("iter48_easy_medium", "unique_ttc_object", "scene-0051-easy-00", 1),
    ("iter48_easy_medium", "unique_ttc_object", "scene-0051-easy-00", 2),
    ("iter49_hard_extreme", "no_fire", "scene-0041-extreme-00", 2),
    ("iter49_hard_extreme", "no_fire", "scene-0062-hard-00", 1),
    ("iter49_hard_extreme", "unique_cpa_object", "scene-0013-extreme-00", 1),
    ("iter49_hard_extreme", "unique_cpa_object", "scene-0013-extreme-00", 2),
    ("iter49_hard_extreme", "unique_ttc_object", "scene-0038-hard-00", 1),
    ("iter49_hard_extreme", "unique_ttc_object", "scene-0038-hard-00", 2),
    ("iter49_hard_extreme", "both_distinct_objects", "scene-0138-extreme-00", 1),
]


def _sha(seed: int) -> str:
    return f"{seed:064x}"[-64:]


def _row(dataset: str, label: str, scenario: str, run: int) -> dict:
    return {
        "dataset": dataset,
        "scenario": scenario,
        "run": run,
        "tier": "easy" if dataset == "iter48_easy_medium" else "hard",
        "attackplanner": dataset == "iter49_hard_extreme",
        "monitor_provenance_label": label,
        "selection_role": "carried_existing_singleton" if label == "both_distinct_objects" else "new_candidate",
        "first_fire_channel": "no_fire" if label == "no_fire" else "ttc_only",
        "fire_timing_label": "no_fire" if label == "no_fire" else "post_collision_fire",
        "first_fire_ts": None if label == "no_fire" else 2.0,
        "first_fire_lead_time": None if label == "no_fire" else -1.0,
        "first_on_nc_time": 1.0,
    }


def _iter101_report(rows: list[dict] | None = None, *, verdict: str = manifest.ITER101_VERDICT) -> dict:
    selected = rows if rows is not None else [_row(*row) for row in ROWS]
    return {
        "verdict": verdict,
        "summary": {
            "selected_total_count": len(selected),
            "selected_new_count": sum(row["selection_role"] == "new_candidate" for row in selected),
            "carried_singleton_count": sum(row["selection_role"] == "carried_existing_singleton" for row in selected),
            "all_strata_covered": True,
        },
        "event": {"measurements": {"selected_rows": selected}},
    }


def _launcher_text(**overrides: str) -> str:
    constants = {
        **manifest.EXPECTED_LAUNCHER_CONSTANTS,
        **overrides,
    }
    return "\n".join(f"{key}={value}" for key, value in constants.items()) + "\n"


def _write_inputs(
    tmp_path: Path,
    *,
    rows: list[dict] | None = None,
    omit_sha_scenario: str | None = None,
    receipt_overrides: dict | None = None,
    launcher_overrides: dict[str, str] | None = None,
) -> tuple[Path, Path, Path, Path, Path]:
    iter101 = tmp_path / "iter101.json"
    iter48 = tmp_path / "iter48.sha256"
    iter49 = tmp_path / "iter49.sha256"
    receipts = tmp_path / "receipts.json"
    launcher = tmp_path / "launcher.sh"
    iter101.write_text(json.dumps(_iter101_report(rows)))
    iter48_lines = []
    iter49_lines = []
    for idx, (_, _, scenario, _) in enumerate(ROWS, start=1):
        if scenario == omit_sha_scenario:
            continue
        line = f"{_sha(idx)}  {scenario}.yaml"
        if "easy" in scenario or "medium" in scenario:
            iter48_lines.append(line)
        else:
            iter49_lines.append(line)
    iter48.write_text("\n".join(iter48_lines) + "\n")
    iter49.write_text("\n".join(iter49_lines) + "\n")
    receipt_payload = {**manifest.EXPECTED_STACK, **(receipt_overrides or {})}
    receipts.write_text(json.dumps(receipt_payload))
    launcher.write_text(_launcher_text(**(launcher_overrides or {})))
    return iter101, iter48, iter49, receipts, launcher


def test_launch_manifest_complete_with_duplicate_slots(tmp_path: Path) -> None:
    report = manifest.build_report(*_write_inputs(tmp_path))

    assert report["verdict"] == "HUGSIM_PROVENANCE_BATCH_LAUNCH_MANIFEST_COMPLETE"
    assert report["summary"]["slot_count"] == 13
    assert report["summary"]["unique_scenario_count"] == 9
    assert report["summary"]["duplicate_scenario_count"] == 4
    assert report["summary"]["scenario_sha_bound_count"] == 13
    assert report["manifest"]["duplicate_slot_policy"]["scenario_deduplication_allowed"] is False
    assert len({slot["slot_id"] for slot in report["manifest"]["slots"]}) == 13


def test_launch_manifest_blocks_missing_scenario_sha(tmp_path: Path) -> None:
    report = manifest.build_report(*_write_inputs(tmp_path, omit_sha_scenario="scene-0062-hard-00"))

    assert report["verdict"] == "HUGSIM_PROVENANCE_BATCH_LAUNCH_MANIFEST_BLOCKED"
    assert "missing-scenario-sha:iter49:scene-0062-hard-00.yaml" in report["infra_problems"]


def test_launch_manifest_blocks_stack_drift(tmp_path: Path) -> None:
    report = manifest.build_report(*_write_inputs(tmp_path, receipt_overrides={"image_id": "wrong"}))

    assert report["verdict"] == "HUGSIM_PROVENANCE_BATCH_LAUNCH_MANIFEST_BLOCKED"
    assert "receipt-image_id-mismatch:'wrong'!='f73ef3884063'" in report["infra_problems"]


def test_launch_manifest_blocks_launcher_constant_drift(tmp_path: Path) -> None:
    report = manifest.build_report(*_write_inputs(tmp_path, launcher_overrides={"DISK_MIN_GIB": "1"}))

    assert report["verdict"] == "HUGSIM_PROVENANCE_BATCH_LAUNCH_MANIFEST_BLOCKED"
    assert "launcher-DISK_MIN_GIB-mismatch:'1'!='20'" in report["infra_problems"]


def test_launch_manifest_blocks_duplicate_scenario_run_slot(tmp_path: Path) -> None:
    rows = [_row(*row) for row in ROWS]
    rows[1]["run"] = 1
    report = manifest.build_report(*_write_inputs(tmp_path, rows=rows))

    assert report["verdict"] == "HUGSIM_PROVENANCE_BATCH_LAUNCH_MANIFEST_BLOCKED"
    assert "duplicate-scenario-run-slot:scene-0013-easy-00:r1" in report["infra_problems"]
