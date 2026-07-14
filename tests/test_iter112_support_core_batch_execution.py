from __future__ import annotations

import importlib.util
import json
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter112_hugsim_support_core_batch_execution"
    / "analyze_support_core_batch_execution.py"
)
SPEC = importlib.util.spec_from_file_location("iter112_execution", MODULE_PATH)
assert SPEC is not None
execution = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(execution)


ROWS = [
    (
        "i111_s01_iter49_hard_extreme_exact_ttc_classifiable_anchor_short_lead_fire_ttc_only_scene_0411_hard_00_r2",
        "scene-0411-hard-00",
        2,
        "exact_ttc_classifiable_anchor",
    ),
    (
        "i111_s02_iter49_hard_extreme_exact_ttc_classifiable_anchor_long_lead_fire_ttc_only_scene_0411_extreme_00_r1",
        "scene-0411-extreme-00",
        1,
        "exact_ttc_classifiable_anchor",
    ),
    (
        "i111_s03_iter49_hard_extreme_exact_ttc_classifiable_anchor_long_lead_fire_ttc_only_scene_0038_hard_00_r1",
        "scene-0038-hard-00",
        1,
        "exact_ttc_classifiable_anchor",
    ),
    (
        "i111_s04_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0038_extreme_00_r1",
        "scene-0038-extreme-00",
        1,
        "ttc_classifiable_scenario_analogue",
    ),
    (
        "i111_s05_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0038_extreme_00_r2",
        "scene-0038-extreme-00",
        2,
        "ttc_classifiable_scenario_analogue",
    ),
    (
        "i111_s06_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0383_extreme_00_r2",
        "scene-0383-extreme-00",
        2,
        "ttc_classifiable_scenario_analogue",
    ),
    (
        "i111_s07_iter49_hard_extreme_ttc_classifiable_scenario_analogue_short_lead_fire_ttc_only_scene_0411_hard_00_r1",
        "scene-0411-hard-00",
        1,
        "ttc_classifiable_scenario_analogue",
    ),
    (
        "i111_s08_iter49_hard_extreme_ttc_classifiable_scenario_analogue_long_lead_fire_ttc_only_scene_0411_extreme_00_r2",
        "scene-0411-extreme-00",
        2,
        "ttc_classifiable_scenario_analogue",
    ),
]


def _sha(seed: int) -> str:
    return f"{seed:064x}"[-64:]


def _manifest() -> dict:
    return {
        "duplicate_slot_policy": {
            "primary_execution_key": "slot_id",
            "scenario_deduplication_allowed": False,
        },
        "slots": [
            {
                "design_label": design_label,
                "run": run,
                "scenario": scenario,
                "scenario_sha256": _sha(idx),
                "slot_id": slot_id,
                "slot_index": idx,
            }
            for idx, (slot_id, scenario, run, design_label) in enumerate(ROWS, start=1)
        ],
    }


def _write_slot(root: Path, slot: dict, *, collision_key: bool = True, patch_marker: bool = True) -> None:
    slot_dir = root / f"{slot['slot_id']}__{slot['scenario']}__on"
    slot_dir.mkdir(parents=True)
    (slot_dir / "episode_meta.json").write_text(
        json.dumps(
            {
                "attempt": 1,
                "hdscore": 0.5,
                "scenario": slot["scenario"],
                "slot_id": slot["slot_id"],
                "steps": 10,
            }
        )
    )
    output = "sent\nSENTINEL_I48_DECISION frame=1\n"
    if patch_marker:
        output += "SENTINEL_I48_UNION_PATCH_LOADED enabled=1\n"
    (slot_dir / "output.txt").write_text(output)
    eval_payload = {"hdscore": 0.5}
    if collision_key:
        eval_payload["collision_provenance"] = [{"timestamp": 1.0}]
    (slot_dir / "eval.json").write_text(json.dumps(eval_payload))
    (slot_dir / "sentinel_iter48_decisions.jsonl").write_text('{"frame": 1}\n')


def _write_proof(
    tmp_path: Path,
    *,
    missing_slot_index: int | None = None,
    collision_key: bool = True,
    done_marker: bool = True,
    receipt_overrides: dict | None = None,
) -> tuple[Path, Path]:
    manifest_path = tmp_path / "manifest.json"
    proof_root = tmp_path / "proof"
    proof_root.mkdir()
    manifest = _manifest()
    manifest_path.write_text(json.dumps(manifest))
    receipts = {
        "manifest_sha": execution.EXPECTED_MANIFEST_SHA,
        "slot_count": 8,
        **execution.EXPECTED_STACK,
        **(receipt_overrides or {}),
    }
    (proof_root / "receipts.json").write_text(json.dumps(receipts))
    (proof_root / "frozen_manifest.sha256").write_text(
        f"{execution.EXPECTED_MANIFEST_SHA}  iter112_support_core_launch_manifest.json\n"
    )
    (proof_root / "frozen_scenarios_iter112.sha256").write_text(
        "\n".join(f"{slot['scenario_sha256']}  {slot['scenario']}.yaml" for slot in manifest["slots"]) + "\n"
    )
    (proof_root / "i112-support-core-batch-run.log").write_text(
        "I112_START\n" + (execution.DONE_MARKER if done_marker else "I112_STILL_RUNNING") + "\n"
    )
    (proof_root / "heavy_manifest_iter112.txt").write_text("disk summary\n")
    for idx, slot in enumerate(manifest["slots"], start=1):
        if idx == missing_slot_index:
            continue
        _write_slot(proof_root, slot, collision_key=collision_key)
    return manifest_path, proof_root


def test_support_core_batch_execution_complete(tmp_path: Path) -> None:
    report = execution.build_report(*_write_proof(tmp_path))

    assert report["verdict"] == "HUGSIM_SUPPORT_CORE_BATCH_EXECUTION_COMPLETE"
    assert report["summary"]["completed_slot_count"] == 8
    assert report["summary"]["collision_provenance_key_count"] == 8
    assert report["summary"]["duplicate_scenario_group_count"] == 3


def test_support_core_batch_execution_blocks_missing_slot(tmp_path: Path) -> None:
    report = execution.build_report(*_write_proof(tmp_path, missing_slot_index=6))

    assert report["verdict"] == "HUGSIM_SUPPORT_CORE_BATCH_EXECUTION_INFRA_NULL"
    assert any(problem.startswith("missing-slot-dir:") for problem in report["infra_problems"])


def test_support_core_batch_execution_blocks_missing_collision_key(tmp_path: Path) -> None:
    report = execution.build_report(*_write_proof(tmp_path, collision_key=False))

    assert report["verdict"] == "HUGSIM_SUPPORT_CORE_BATCH_EXECUTION_INFRA_NULL"
    assert any(problem.endswith("-collision-provenance-key-missing") for problem in report["infra_problems"])


def test_support_core_batch_execution_blocks_missing_done_marker(tmp_path: Path) -> None:
    report = execution.build_report(*_write_proof(tmp_path, done_marker=False))

    assert report["verdict"] == "HUGSIM_SUPPORT_CORE_BATCH_EXECUTION_INFRA_NULL"
    assert "run-log-done-marker-missing" in report["infra_problems"]


def test_support_core_batch_execution_blocks_receipt_drift(tmp_path: Path) -> None:
    report = execution.build_report(*_write_proof(tmp_path, receipt_overrides={"manifest_sha": "wrong"}))

    assert report["verdict"] == "HUGSIM_SUPPORT_CORE_BATCH_EXECUTION_INFRA_NULL"
    assert (
        "receipt-manifest-sha-mismatch:'wrong'!='a33888b174684b65758e74c949b05b695fda40ef3ddf0c7d9ee439a6ee818e99'"
        in report["infra_problems"]
    )
