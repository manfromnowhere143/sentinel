#!/usr/bin/env python3
"""Iteration 102 HUGSIM provenance batch launch manifest preflight."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ITER101_VERDICT = "HUGSIM_PROVENANCE_BATCH_CANDIDATE_DESIGN_COMPLETE"
EXPECTED_STACK = {
    "hugsim_sha": "62c690d39fd90020e68a196bd8bcc1c4d4191f2e",
    "uniad_sim_sha": "5fb279e39912a5ac7f58e00d56b065cadcd0a749",
    "ckpt_sha": "0ad0c2f5dc9788a41c313305779ea49346aeb742d1f6bb5ad25c46f9beffc990",
    "shim_sha": "5bf69a1187478c52d49792d5871bd5732c6dd431ecd1f44b5e391f7adb80682c",
    "image_id": "f73ef3884063",
    "hugsim_patch_sha": "49eee7611e4b881d2bb6233e8767913019c6a097c6883762414005d5b2284ecd",
    "monitor_patch_sha": "6b39fd79d00c7bdb937c6d240fbc4648661b235f1a3024912d62874937146c5c",
}
EXPECTED_LAUNCHER_CONSTANTS = {
    "EPISODE_TIMEOUT": "1200",
    "DISK_MIN_GIB": "20",
    "FROZEN_HUGSIM_SHA": EXPECTED_STACK["hugsim_sha"],
    "FROZEN_UNIADSIM_SHA": EXPECTED_STACK["uniad_sim_sha"],
    "FROZEN_CKPT_SHA": EXPECTED_STACK["ckpt_sha"],
    "FROZEN_SHIM_SHA": EXPECTED_STACK["shim_sha"],
    "FROZEN_IMAGE_ID": EXPECTED_STACK["image_id"],
    "FROZEN_HUGSIM_PATCH_SHA": EXPECTED_STACK["hugsim_patch_sha"],
    "FROZEN_MONITOR_PATCH_SHA": EXPECTED_STACK["monitor_patch_sha"],
}
EXPECTED_COUNTS = {
    "selected_total_count": 13,
    "selected_new_count": 12,
    "carried_singleton_count": 1,
    "unique_scenario_count": 9,
    "duplicate_scenario_count": 4,
}
DATASET_MANIFEST_LABELS = {
    "iter48_easy_medium": "iter48",
    "iter49_hard_extreme": "iter49",
}


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


def nested_get(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    cursor: Any = data
    for key in path:
        if not isinstance(cursor, dict):
            return None
        cursor = cursor.get(key)
    return cursor


def require_equal(problems: list[str], label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        problems.append(f"{label}-mismatch:{actual!r}!={expected!r}")


def parse_sha_manifest(path: Path, label: str) -> tuple[dict[str, str], list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-{label}:{path}"]
    entries: dict[str, str] = {}
    problems: list[str] = []
    try:
        lines = path.read_text().splitlines()
    except OSError as exc:
        return {}, [f"read-{label}-failed:{path}:{exc}"]
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        if len(parts) != 2:
            problems.append(f"{label}-bad-line:{line_no}:{line}")
            continue
        digest, filename = parts
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            problems.append(f"{label}-bad-sha:{line_no}:{digest}")
            continue
        if not filename.endswith(".yaml"):
            problems.append(f"{label}-bad-filename:{line_no}:{filename}")
            continue
        entries[filename[:-5]] = digest
    return entries, problems


def parse_launcher_constants(path: Path) -> tuple[dict[str, str], list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-launcher:{path}"]
    try:
        text = path.read_text()
    except OSError as exc:
        return {}, [f"read-launcher-failed:{path}:{exc}"]
    constants: dict[str, str] = {}
    for match in re.finditer(r"(?m)^([A-Z0-9_]+)=([^\s#]+)", text):
        constants[match.group(1)] = match.group(2).strip("\"'")
    problems: list[str] = []
    for key, expected in EXPECTED_LAUNCHER_CONSTANTS.items():
        require_equal(problems, f"launcher-{key}", constants.get(key), expected)
    return constants, problems


def slug(value: Any) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")
    return text or "missing"


def selected_rows(iter101_report: dict[str, Any], problems: list[str]) -> list[dict[str, Any]]:
    require_equal(problems, "iter101-verdict", iter101_report.get("verdict"), ITER101_VERDICT)
    summary = iter101_report.get("summary")
    if not isinstance(summary, dict):
        problems.append("iter101-summary-missing")
        summary = {}
    require_equal(problems, "iter101-selected_total_count", summary.get("selected_total_count"), 13)
    require_equal(problems, "iter101-selected_new_count", summary.get("selected_new_count"), 12)
    require_equal(problems, "iter101-carried_singleton_count", summary.get("carried_singleton_count"), 1)
    require_equal(problems, "iter101-all_strata_covered", summary.get("all_strata_covered"), True)
    rows = nested_get(iter101_report, ("event", "measurements", "selected_rows"))
    if not isinstance(rows, list):
        problems.append("iter101-selected_rows-not-list")
        return []
    compact_rows: list[dict[str, Any]] = []
    required = ("dataset", "scenario", "run", "tier", "monitor_provenance_label", "selection_role")
    for idx, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            problems.append(f"iter101-selected-row-not-dict:{idx}")
            continue
        for key in required:
            if row.get(key) in (None, ""):
                problems.append(f"iter101-selected-row-missing-{key}:{idx}")
        if not isinstance(row.get("run"), int):
            problems.append(f"iter101-selected-row-run-not-int:{idx}:{row.get('run')!r}")
        compact_rows.append(row)
    return compact_rows


def check_stack(
    receipts: dict[str, Any],
    launcher_constants: dict[str, str],
    problems: list[str],
) -> dict[str, Any]:
    for key, expected in EXPECTED_STACK.items():
        require_equal(problems, f"receipt-{key}", receipts.get(key), expected)
    return {
        **EXPECTED_STACK,
        "episode_timeout": int(launcher_constants.get("EPISODE_TIMEOUT", "0") or 0),
        "disk_min_gib": int(launcher_constants.get("DISK_MIN_GIB", "0") or 0),
        "single_tenant_docker_required": True,
        "slot_id_is_primary_execution_key": True,
    }


def source_manifest_for_dataset(
    dataset: str,
    iter48_manifest: dict[str, str],
    iter49_manifest: dict[str, str],
) -> tuple[str | None, dict[str, str]]:
    if dataset == "iter48_easy_medium":
        return "iter48", iter48_manifest
    if dataset == "iter49_hard_extreme":
        return "iter49", iter49_manifest
    return None, {}


def build_slots(
    rows: list[dict[str, Any]],
    iter48_manifest: dict[str, str],
    iter49_manifest: dict[str, str],
    problems: list[str],
) -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = []
    scenario_run_pairs: set[tuple[str, int]] = set()
    for index, row in enumerate(rows, start=1):
        dataset = str(row.get("dataset"))
        scenario = str(row.get("scenario"))
        run = row.get("run")
        if not isinstance(run, int):
            run = -1
        source_label, manifest = source_manifest_for_dataset(dataset, iter48_manifest, iter49_manifest)
        if source_label is None:
            problems.append(f"unknown-dataset-for-manifest:{dataset}:{scenario}:r{run}")
            scenario_sha = None
        else:
            scenario_sha = manifest.get(scenario)
            if scenario_sha is None:
                problems.append(f"missing-scenario-sha:{source_label}:{scenario}.yaml")
        pair = (scenario, run)
        if pair in scenario_run_pairs:
            problems.append(f"duplicate-scenario-run-slot:{scenario}:r{run}")
        scenario_run_pairs.add(pair)
        slot_id = (
            f"i102_s{index:02d}_{slug(dataset)}_"
            f"{slug(row.get('monitor_provenance_label'))}_{slug(scenario)}_r{run}"
        )
        slots.append(
            {
                "slot_index": index,
                "slot_id": slot_id,
                "execution_key": slot_id,
                "destination_key": f"{slot_id}__{scenario}__on",
                "dataset": dataset,
                "scenario": scenario,
                "scenario_yaml": f"{scenario}.yaml",
                "scenario_sha256": scenario_sha,
                "scenario_manifest_source": source_label,
                "run": run,
                "tier": row.get("tier"),
                "attackplanner": row.get("attackplanner"),
                "selection_role": row.get("selection_role"),
                "monitor_provenance_label": row.get("monitor_provenance_label"),
                "stratum": [dataset, row.get("monitor_provenance_label")],
                "fire_timing_label": row.get("fire_timing_label"),
                "first_fire_channel": row.get("first_fire_channel"),
                "first_fire_ts": row.get("first_fire_ts"),
                "first_fire_lead_time": row.get("first_fire_lead_time"),
                "first_on_nc_time": row.get("first_on_nc_time"),
                "slot_policy": "preserve_even_if_scenario_repeats",
            }
        )
    return slots


def duplicate_summary(slots: list[dict[str, Any]], problems: list[str]) -> dict[str, Any]:
    scenario_counts = Counter(slot["scenario"] for slot in slots)
    duplicate_scenarios = {
        scenario: count for scenario, count in sorted(scenario_counts.items()) if count > 1
    }
    slot_ids = [slot["slot_id"] for slot in slots]
    slot_indexes = [slot["slot_index"] for slot in slots]
    if len(slot_ids) != len(set(slot_ids)):
        problems.append("slot-ids-not-unique")
    if slot_indexes != list(range(1, len(slots) + 1)):
        problems.append(f"slot-indexes-not-contiguous:{slot_indexes}")
    for scenario, count in duplicate_scenarios.items():
        tuples = {
            (slot["scenario"], slot["run"], slot["slot_id"])
            for slot in slots
            if slot["scenario"] == scenario
        }
        if len(tuples) != count:
            problems.append(f"duplicate-scenario-slots-not-distinct:{scenario}")
    return {
        "unique_scenarios": sorted(scenario_counts),
        "unique_scenario_count": len(scenario_counts),
        "duplicate_scenarios": duplicate_scenarios,
        "duplicate_scenario_count": len(duplicate_scenarios),
        "duplicate_slot_count": sum(duplicate_scenarios.values()),
    }


def classify(summary: dict[str, Any], problems: list[str]) -> str:
    if problems:
        return "launch_manifest_blocked"
    complete = (
        summary["slot_count"] == EXPECTED_COUNTS["selected_total_count"]
        and summary["selected_new_count"] == EXPECTED_COUNTS["selected_new_count"]
        and summary["carried_singleton_count"] == EXPECTED_COUNTS["carried_singleton_count"]
        and summary["unique_scenario_count"] == EXPECTED_COUNTS["unique_scenario_count"]
        and summary["duplicate_scenario_count"] == EXPECTED_COUNTS["duplicate_scenario_count"]
        and summary["scenario_sha_bound_count"] == EXPECTED_COUNTS["selected_total_count"]
    )
    return "launch_manifest_complete_with_duplicate_slot_semantics" if complete else "launch_manifest_blocked"


def choose_verdict(label: str) -> str:
    if label == "launch_manifest_complete_with_duplicate_slot_semantics":
        return "HUGSIM_PROVENANCE_BATCH_LAUNCH_MANIFEST_COMPLETE"
    return "HUGSIM_PROVENANCE_BATCH_LAUNCH_MANIFEST_BLOCKED"


def build_report(
    iter101_report_path: Path,
    iter48_manifest_path: Path,
    iter49_manifest_path: Path,
    iter59_receipts_path: Path,
    iter59_launcher_path: Path,
) -> dict[str, Any]:
    problems: list[str] = []
    iter101_report, iter101_problems = load_json(iter101_report_path, "iter101-report")
    receipts, receipt_problems = load_json(iter59_receipts_path, "iter59-receipts")
    iter48_manifest, iter48_problems = parse_sha_manifest(iter48_manifest_path, "iter48-scenarios")
    iter49_manifest, iter49_problems = parse_sha_manifest(iter49_manifest_path, "iter49-scenarios")
    launcher_constants, launcher_problems = parse_launcher_constants(iter59_launcher_path)
    problems.extend(iter101_problems + receipt_problems + iter48_problems + iter49_problems + launcher_problems)
    rows: list[dict[str, Any]] = []
    slots: list[dict[str, Any]] = []
    stack_gates: dict[str, Any] = {}
    if not problems:
        rows = selected_rows(iter101_report, problems)
        stack_gates = check_stack(receipts, launcher_constants, problems)
        slots = build_slots(rows, iter48_manifest, iter49_manifest, problems)
    role_counts = Counter(str(row.get("selection_role")) for row in rows)
    duplicate = duplicate_summary(slots, problems) if slots else {
        "unique_scenarios": [],
        "unique_scenario_count": 0,
        "duplicate_scenarios": {},
        "duplicate_scenario_count": 0,
        "duplicate_slot_count": 0,
    }
    manifest = {
        "manifest_version": 1,
        "source_iteration": 101,
        "future_launcher_requirement": "slot_id_is_primary_execution_key",
        "duplicate_slot_policy": {
            "primary_execution_key": "slot_id",
            "scenario_deduplication_allowed": False,
            "destination_paths_must_include_slot_id": True,
            "done_markers_must_include_slot_id": True,
        },
        "stack_gates": stack_gates,
        "slots": slots,
    }
    summary = {
        "slot_count": len(slots),
        "selected_new_count": role_counts.get("new_candidate", 0),
        "carried_singleton_count": role_counts.get("carried_existing_singleton", 0),
        "scenario_sha_bound_count": sum(1 for slot in slots if slot.get("scenario_sha256")),
        "stack_gate_count": len(stack_gates),
        **duplicate,
    }
    label = classify(summary, problems)
    return {
        "iteration": 102,
        "inputs": {
            "iter101_report": str(iter101_report_path),
            "iter48_manifest": str(iter48_manifest_path),
            "iter49_manifest": str(iter49_manifest_path),
            "iter59_receipts": str(iter59_receipts_path),
            "iter59_launcher": str(iter59_launcher_path),
        },
        "infra_problems": problems,
        "event": {
            "row_label": label,
            "measurements": {
                "summary": summary,
                "duplicate_slot_policy": manifest["duplicate_slot_policy"],
                "launcher_constants": {
                    key: launcher_constants.get(key) for key in sorted(EXPECTED_LAUNCHER_CONSTANTS)
                },
            },
            "problems": problems,
        },
        "summary": summary,
        "manifest": manifest,
        "verdict": choose_verdict(label),
        "claim_boundary": (
            "offline launch-manifest preflight only; no GPU approval, launch authorization, "
            "actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, "
            "benchmark, population-rate, HD-Score-invariance, real-world behavior, acquisition-value, "
            "or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 102 - HUGSIM provenance batch launch manifest",
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
            "## Launch Slots",
            "",
            "| slot | slot id | dataset | stratum | scenario | run | sha source | scenario sha |",
            "|---:|---|---|---|---|---:|---|---|",
        ]
    )
    for slot in report["manifest"]["slots"]:
        lines.append(
            f"| `{slot['slot_index']}` | `{slot['slot_id']}` | `{slot['dataset']}` | "
            f"`{slot['monitor_provenance_label']}` | `{slot['scenario']}` | `{slot['run']}` | "
            f"`{slot['scenario_manifest_source']}` | `{slot['scenario_sha256']}` |"
        )
    lines.extend(
        [
            "",
            "## Duplicate-Slot Policy",
            "",
            "Slot id is the primary execution key. Scenario-level deduplication is not allowed for "
            "this future batch because the iteration-101 schedule contains repeated scenarios with "
            "distinct selected run slots.",
            "",
            "## Boundary",
            "",
            report["claim_boundary"],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter101_report: Path,
    iter48_manifest: Path,
    iter49_manifest: Path,
    iter59_receipts: Path,
    iter59_launcher: Path,
    out: Path,
    markdown_out: Path,
    manifest_out: Path,
) -> dict[str, Any]:
    report = build_report(iter101_report, iter48_manifest, iter49_manifest, iter59_receipts, iter59_launcher)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    manifest_out.write_text(json.dumps(report["manifest"], indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iter101-report",
        type=Path,
        default=Path(
            "experiments/iter101_hugsim_provenance_batch_candidate_design/proof-design/"
            "provenance_batch_candidate_design_report.json"
        ),
    )
    parser.add_argument(
        "--iter48-manifest",
        type=Path,
        default=Path("experiments/iter48_hugsim_transfer_gate/proof-stage2/frozen_scenarios.sha256"),
    )
    parser.add_argument(
        "--iter49-manifest",
        type=Path,
        default=Path("experiments/iter49_hugsim_hard_tier_gate/proof-hard/frozen_scenarios_hard.sha256"),
    )
    parser.add_argument(
        "--iter59-receipts",
        type=Path,
        default=Path("experiments/iter59_hugsim_actor_match_audit/proof-actor-match/receipts.json"),
    )
    parser.add_argument(
        "--iter59-launcher",
        type=Path,
        default=Path("experiments/iter59_hugsim_actor_match_audit/run_actor_match_audit.sh"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter102_hugsim_provenance_batch_launch_manifest/proof-launch-manifest/"
            "provenance_batch_launch_manifest_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter102_hugsim_provenance_batch_launch_manifest/proof-launch-manifest/"
            "provenance_batch_launch_manifest.md"
        ),
    )
    parser.add_argument(
        "--manifest-out",
        type=Path,
        default=Path(
            "experiments/iter102_hugsim_provenance_batch_launch_manifest/proof-launch-manifest/"
            "provenance_batch_launch_manifest.json"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter101_report,
        args.iter48_manifest,
        args.iter49_manifest,
        args.iter59_receipts,
        args.iter59_launcher,
        args.out,
        args.markdown_out,
        args.manifest_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
