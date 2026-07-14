#!/usr/bin/env python3
"""Iteration 103 HUGSIM provenance batch execution proof analyzer."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

EXPECTED_MANIFEST_SHA = "ddbc9960fe0b50b95842bd2c8b2e26b5e7ed00abba65f8f97b5ed6515c428870"
EXPECTED_STACK = {
    "hugsim_sha": "62c690d39fd90020e68a196bd8bcc1c4d4191f2e",
    "uniad_sim_sha": "5fb279e39912a5ac7f58e00d56b065cadcd0a749",
    "ckpt_sha": "0ad0c2f5dc9788a41c313305779ea49346aeb742d1f6bb5ad25c46f9beffc990",
    "shim_sha": "5bf69a1187478c52d49792d5871bd5732c6dd431ecd1f44b5e391f7adb80682c",
    "image_id": "f73ef3884063",
    "hugsim_patch_sha": "49eee7611e4b881d2bb6233e8767913019c6a097c6883762414005d5b2284ecd",
    "monitor_patch_sha": "6b39fd79d00c7bdb937c6d240fbc4648661b235f1a3024912d62874937146c5c",
}
EXPECTED_SLOT_COUNT = 13
DONE_MARKER = "I103_PROVENANCE_BATCH_DONE"
PATCH_MARKER = "SENTINEL_I48_UNION_PATCH_LOADED enabled=1"
DECISION_MARKER = "SENTINEL_I48_DECISION frame="


def load_json(path: Path, label: str) -> tuple[dict[str, Any], list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-{label}:{path}"]
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"read-{label}-failed:{path}:{exc}"]
    if not isinstance(data, dict):
        return {}, [f"{label}-not-dict"]
    return data, []


def require_equal(problems: list[str], label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        problems.append(f"{label}-mismatch:{actual!r}!={expected!r}")


def read_text(path: Path, label: str) -> tuple[str, list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return "", [f"missing-{label}:{path}"]
    try:
        return path.read_text(errors="replace"), []
    except OSError as exc:
        return "", [f"read-{label}-failed:{path}:{exc}"]


def manifest_slots(manifest: dict[str, Any], problems: list[str]) -> list[dict[str, Any]]:
    slots = manifest.get("slots")
    policy = manifest.get("duplicate_slot_policy")
    if not isinstance(slots, list):
        problems.append("manifest-slots-not-list")
        return []
    if not isinstance(policy, dict):
        problems.append("manifest-duplicate-policy-missing")
    else:
        require_equal(problems, "manifest-primary-key", policy.get("primary_execution_key"), "slot_id")
        require_equal(problems, "manifest-scenario-dedup", policy.get("scenario_deduplication_allowed"), False)
    require_equal(problems, "manifest-slot-count", len(slots), EXPECTED_SLOT_COUNT)
    indexes = [slot.get("slot_index") for slot in slots if isinstance(slot, dict)]
    require_equal(problems, "manifest-slot-indexes", indexes, list(range(1, EXPECTED_SLOT_COUNT + 1)))
    return [slot for slot in slots if isinstance(slot, dict)]


def check_receipts(receipts: dict[str, Any], problems: list[str]) -> None:
    require_equal(problems, "receipt-manifest-sha", receipts.get("manifest_sha"), EXPECTED_MANIFEST_SHA)
    require_equal(problems, "receipt-slot-count", receipts.get("slot_count"), EXPECTED_SLOT_COUNT)
    for key, expected in EXPECTED_STACK.items():
        require_equal(problems, f"receipt-{key}", receipts.get(key), expected)


def load_slot_proof(slot: dict[str, Any], proof_root: Path, problems: list[str]) -> dict[str, Any]:
    slot_id = str(slot.get("slot_id"))
    scenario = str(slot.get("scenario"))
    slot_dir = proof_root / f"{slot_id}__{scenario}__on"
    row: dict[str, Any] = {
        "slot_index": slot.get("slot_index"),
        "slot_id": slot_id,
        "scenario": scenario,
        "run": slot.get("run"),
        "slot_dir": str(slot_dir),
        "complete": False,
    }
    if not slot_dir.is_dir():
        problems.append(f"missing-slot-dir:{slot_id}:{slot_dir}")
        return row
    meta, meta_problems = load_json(slot_dir / "episode_meta.json", f"{slot_id}-episode-meta")
    eval_data, eval_problems = load_json(slot_dir / "eval.json", f"{slot_id}-eval")
    output, output_problems = read_text(slot_dir / "output.txt", f"{slot_id}-output")
    decisions_path = slot_dir / "sentinel_iter48_decisions.jsonl"
    problems.extend(meta_problems + eval_problems + output_problems)
    if not decisions_path.exists() or decisions_path.stat().st_size == 0:
        problems.append(f"missing-{slot_id}-decisions:{decisions_path}")
    if meta:
        require_equal(problems, f"{slot_id}-meta-slot-id", meta.get("slot_id"), slot_id)
        require_equal(problems, f"{slot_id}-meta-scenario", meta.get("scenario"), scenario)
        if meta.get("failed") is True:
            problems.append(f"{slot_id}-meta-failed")
        row["attempt"] = meta.get("attempt")
        row["steps"] = meta.get("steps")
    if output:
        if PATCH_MARKER not in output:
            problems.append(f"{slot_id}-patch-marker-missing")
        if DECISION_MARKER not in output:
            problems.append(f"{slot_id}-decision-marker-missing")
    if eval_data:
        if "collision_provenance" not in eval_data:
            problems.append(f"{slot_id}-collision-provenance-key-missing")
        provenance = eval_data.get("collision_provenance")
        row["collision_provenance_rows"] = len(provenance) if isinstance(provenance, list) else 0
        hdscore = eval_data.get("hdscore")
        row["hdscore"] = hdscore if isinstance(hdscore, (int, float)) and math.isfinite(hdscore) else None
    row["complete"] = not any(problem.startswith(slot_id) or f":{slot_id}:" in problem for problem in problems)
    return row


def check_proof_sidecars(proof_root: Path, problems: list[str]) -> dict[str, Any]:
    sidecars = {
        "receipts": proof_root / "receipts.json",
        "frozen_manifest": proof_root / "frozen_manifest.sha256",
        "frozen_scenarios": proof_root / "frozen_scenarios_iter103.sha256",
        "run_log": proof_root / "i103-provenance-batch-run.log",
        "heavy_manifest": proof_root / "heavy_manifest_iter103.txt",
    }
    summary: dict[str, Any] = {}
    for label, path in sidecars.items():
        if not path.exists() or path.stat().st_size == 0:
            problems.append(f"missing-{label}:{path}")
            summary[f"{label}_present"] = False
        else:
            summary[f"{label}_present"] = True
    if sidecars["frozen_manifest"].exists():
        text, text_problems = read_text(sidecars["frozen_manifest"], "frozen-manifest")
        problems.extend(text_problems)
        if EXPECTED_MANIFEST_SHA not in text:
            problems.append("frozen-manifest-sha-missing")
    if sidecars["run_log"].exists():
        text, text_problems = read_text(sidecars["run_log"], "run-log")
        problems.extend(text_problems)
        if DONE_MARKER not in text:
            problems.append("run-log-done-marker-missing")
    return summary


def classify(summary: dict[str, Any], problems: list[str]) -> str:
    if problems:
        return "provenance_batch_execution_infra_null"
    complete = (
        summary["completed_slot_count"] == EXPECTED_SLOT_COUNT
        and summary["slot_proof_artifact_complete_count"] == EXPECTED_SLOT_COUNT
        and summary["collision_provenance_key_count"] == EXPECTED_SLOT_COUNT
        and summary["collected_slot_ids_match_manifest"] is True
        and summary["duplicate_scenario_group_count"] == 4
    )
    return "provenance_batch_execution_complete" if complete else "provenance_batch_execution_infra_null"


def choose_verdict(label: str) -> str:
    if label == "provenance_batch_execution_complete":
        return "HUGSIM_PROVENANCE_BATCH_EXECUTION_COMPLETE"
    return "HUGSIM_PROVENANCE_BATCH_EXECUTION_INFRA_NULL"


def build_report(manifest_path: Path, proof_root: Path) -> dict[str, Any]:
    problems: list[str] = []
    manifest, manifest_problems = load_json(manifest_path, "manifest")
    receipts, receipt_problems = load_json(proof_root / "receipts.json", "receipts")
    problems.extend(manifest_problems + receipt_problems)
    slots = manifest_slots(manifest, problems) if manifest else []
    if receipts:
        check_receipts(receipts, problems)
    sidecar_summary = check_proof_sidecars(proof_root, problems)
    rows = [load_slot_proof(slot, proof_root, problems) for slot in slots]
    expected_slot_ids = [str(slot.get("slot_id")) for slot in slots]
    collected_slot_ids = [row["slot_id"] for row in rows if row.get("complete") is True]
    scenario_counts = Counter(str(slot.get("scenario")) for slot in slots)
    summary = {
        **sidecar_summary,
        "manifest_slot_count": len(slots),
        "completed_slot_count": sum(row.get("complete") is True for row in rows),
        "slot_proof_artifact_complete_count": sum(row.get("complete") is True for row in rows),
        "collision_provenance_key_count": sum("collision_provenance_rows" in row for row in rows),
        "collision_provenance_total_rows": sum(int(row.get("collision_provenance_rows") or 0) for row in rows),
        "hdscore_present_count": sum(row.get("hdscore") is not None for row in rows),
        "collected_slot_ids_match_manifest": collected_slot_ids == expected_slot_ids,
        "unique_scenario_count": len(scenario_counts),
        "duplicate_scenario_group_count": sum(1 for count in scenario_counts.values() if count > 1),
        "duplicate_slot_count": sum(count for count in scenario_counts.values() if count > 1),
    }
    label = classify(summary, problems)
    return {
        "iteration": 103,
        "inputs": {"manifest": str(manifest_path), "proof_root": str(proof_root)},
        "infra_problems": problems,
        "event": {
            "row_label": label,
            "measurements": {"summary": summary, "slots": rows},
            "problems": problems,
        },
        "summary": summary,
        "slots": rows,
        "verdict": choose_verdict(label),
        "claim_boundary": (
            "HUGSIM provenance batch execution proof only; no actor-causality, actor-match "
            "interpretation, repair, threshold-value, transfer, safety, deployment, robustness, "
            "benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder "
            "behavior, acquisition-value, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 103 - HUGSIM provenance batch execution",
        "",
        f"Verdict: `{report['verdict']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    if report["infra_problems"]:
        lines.extend(["", "## Infrastructure Problems", ""])
        lines.extend(f"- `{problem}`" for problem in report["infra_problems"])
    lines.extend(
        [
            "",
            "## Slots",
            "",
            "| slot | slot id | scenario | run | complete | provenance rows | hdscore |",
            "|---:|---|---|---:|---|---:|---:|",
        ]
    )
    for row in report["slots"]:
        lines.append(
            f"| `{row['slot_index']}` | `{row['slot_id']}` | `{row['scenario']}` | "
            f"`{row['run']}` | `{row['complete']}` | `{row.get('collision_provenance_rows')}` | "
            f"`{row.get('hdscore')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(manifest: Path, proof_root: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(manifest, proof_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(
            "experiments/iter102_hugsim_provenance_batch_launch_manifest/proof-launch-manifest/"
            "provenance_batch_launch_manifest.json"
        ),
    )
    parser.add_argument(
        "--proof-root",
        type=Path,
        default=Path("experiments/iter103_hugsim_provenance_batch_execution/proof-execution"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter103_hugsim_provenance_batch_execution/proof-execution/"
            "provenance_batch_execution_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter103_hugsim_provenance_batch_execution/proof-execution/"
            "provenance_batch_execution.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.manifest, args.proof_root, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
