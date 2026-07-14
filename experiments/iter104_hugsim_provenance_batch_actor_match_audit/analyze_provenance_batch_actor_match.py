#!/usr/bin/env python3
"""Iteration 104 HUGSIM provenance batch actor-match support audit."""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

ITER103_VERDICT = "HUGSIM_PROVENANCE_BATCH_EXECUTION_COMPLETE"
COMPLETE_VERDICT = "HUGSIM_PROVENANCE_BATCH_ACTOR_MATCH_AUDIT_COMPLETE"
SUPPORT_NULL_VERDICT = "HUGSIM_PROVENANCE_BATCH_ACTOR_MATCH_SUPPORT_NULL"
INFRA_NULL_VERDICT = "HUGSIM_PROVENANCE_BATCH_ACTOR_MATCH_INFRA_NULL"
MIN_CLASSIFIABLE = 4


def load_iter59_module() -> Any:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "iter59_hugsim_actor_match_audit"
        / "analyze_actor_match.py"
    )
    spec = importlib.util.spec_from_file_location("iter59_actor_match", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot-load-iter59-analyzer:{module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ITER59 = load_iter59_module()


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


def load_manifest_slots(manifest: dict[str, Any], problems: list[str]) -> list[dict[str, Any]]:
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
    require_equal(problems, "manifest-slot-count", len(slots), 13)
    require_equal(
        problems,
        "manifest-slot-indexes",
        [slot.get("slot_index") for slot in slots if isinstance(slot, dict)],
        list(range(1, 14)),
    )
    return [slot for slot in slots if isinstance(slot, dict)]


def crosscheck_iter103(iter103_report: dict[str, Any], slots: list[dict[str, Any]], problems: list[str]) -> None:
    require_equal(problems, "iter103-verdict", iter103_report.get("verdict"), ITER103_VERDICT)
    summary = iter103_report.get("summary")
    if not isinstance(summary, dict):
        problems.append("iter103-summary-missing")
        summary = {}
    require_equal(problems, "iter103-completed-slot-count", summary.get("completed_slot_count"), 13)
    require_equal(problems, "iter103-artifact-count", summary.get("slot_proof_artifact_complete_count"), 13)
    require_equal(problems, "iter103-provenance-key-count", summary.get("collision_provenance_key_count"), 13)
    require_equal(problems, "iter103-slot-order", summary.get("collected_slot_ids_match_manifest"), True)
    iter103_slots = iter103_report.get("slots")
    if not isinstance(iter103_slots, list):
        problems.append("iter103-slots-not-list")
        return
    manifest_ids = [slot.get("slot_id") for slot in slots]
    iter103_ids = [slot.get("slot_id") for slot in iter103_slots if isinstance(slot, dict)]
    require_equal(problems, "iter103-manifest-slot-ids", iter103_ids, manifest_ids)


def slot_dir(proof_root: Path, slot: dict[str, Any]) -> Path:
    return proof_root / f"{slot['slot_id']}__{slot['scenario']}__on"


def classify_slots(slots: list[dict[str, Any]], proof_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for slot in slots:
        row = ITER59.classify_episode(slot_dir(proof_root, slot), str(slot["slot_id"]), str(slot["scenario"]))
        row.update(
            {
                "slot_index": slot.get("slot_index"),
                "slot_id": slot.get("slot_id"),
                "run": slot.get("run"),
                "dataset": slot.get("dataset"),
                "selection_role": slot.get("selection_role"),
                "stratum": slot.get("stratum"),
            }
        )
        rows.append(row)
    return rows


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    if infra_problems or any(row.get("problems") for row in rows):
        return INFRA_NULL_VERDICT
    classifiable = sum(row.get("support_label") == "classifiable_foreground" for row in rows)
    if classifiable < MIN_CLASSIFIABLE:
        return SUPPORT_NULL_VERDICT
    return COMPLETE_VERDICT


def build_report(manifest_path: Path, iter103_report_path: Path, proof_root: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    manifest, manifest_problems = load_json(manifest_path, "iter102-manifest")
    iter103_report, iter103_problems = load_json(iter103_report_path, "iter103-report")
    infra_problems.extend(manifest_problems + iter103_problems)
    slots: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    if not infra_problems:
        slots = load_manifest_slots(manifest, infra_problems)
        crosscheck_iter103(iter103_report, slots, infra_problems)
        rows = classify_slots(slots, proof_root)
    support_counts = Counter(row.get("support_label") for row in rows)
    bridge_counts = Counter(
        row.get("bridge_label")
        for row in rows
        if row.get("support_label") == "classifiable_foreground"
    )
    verdict = choose_verdict(rows, infra_problems)
    summary = {
        "slot_count": len(rows),
        "completed_rows": sum(not row.get("problems") for row in rows),
        "classifiable_foreground": support_counts.get("classifiable_foreground", 0),
        "support_counts": dict(sorted(support_counts.items())),
        "bridge_counts": dict(sorted(bridge_counts.items())),
        "actor_match": bridge_counts.get("actor_match", 0),
        "actor_mismatch": bridge_counts.get("actor_mismatch", 0),
        "actor_ambiguous": bridge_counts.get("actor_ambiguous", 0),
        "min_classifiable_bar": MIN_CLASSIFIABLE,
    }
    return {
        "iteration": 104,
        "inputs": {
            "manifest": str(manifest_path),
            "iter103_report": str(iter103_report_path),
            "proof_root": str(proof_root),
            "iter59_analyzer": str(
                Path("experiments/iter59_hugsim_actor_match_audit/analyze_actor_match.py")
            ),
        },
        "infra_problems": infra_problems,
        "episodes": rows,
        "summary": summary,
        "verdict": verdict,
        "claim_boundary": (
            "bounded 13-slot actor-match support audit only; no repair, threshold-value, transfer, "
            "safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, "
            "real-world behavior, first-responder behavior, acquisition-value, retuning, or "
            "production claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 104 - HUGSIM provenance batch actor-match support audit",
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
            "| slot | scenario | run | support | bridge | distance m | monitor object | foreground |",
            "|---:|---|---:|---|---|---:|---|---|",
        ]
    )
    for row in report["episodes"]:
        lines.append(
            f"| `{row.get('slot_index')}` | `{row.get('scenario')}` | `{row.get('run')}` | "
            f"`{row.get('support_label')}` | `{row.get('bridge_label')}` | "
            f"`{row.get('bridge_distance_m')}` | `{row.get('monitor_object_id')}` | "
            f"`{row.get('first_foreground_obs_name')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    manifest: Path,
    iter103_report: Path,
    proof_root: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(manifest, iter103_report, proof_root)
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
        "--iter103-report",
        type=Path,
        default=Path(
            "experiments/iter103_hugsim_provenance_batch_execution/proof-execution/"
            "provenance_batch_execution_report.json"
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
            "experiments/iter104_hugsim_provenance_batch_actor_match_audit/proof-actor-match/"
            "provenance_batch_actor_match_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter104_hugsim_provenance_batch_actor_match_audit/proof-actor-match/"
            "provenance_batch_actor_match.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.manifest,
        args.iter103_report,
        args.proof_root,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
