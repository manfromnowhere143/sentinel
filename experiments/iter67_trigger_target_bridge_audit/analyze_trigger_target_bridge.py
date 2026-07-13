#!/usr/bin/env python3
"""Iteration 67 trigger-target bridge audit analyzer."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER61_VERDICT = "OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE"
ITER64_VERDICT = "UNSUPPORTED_TEMPORAL_MATCH_COMPLETE"
ITER65_VERDICT = "TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE"
ITER66_VERDICT = "MATCHED_OBJECT_TIMELINE_MIXED_COMPLETE"
EXPECTED_TARGETS = (
    {"audit_id": "ttc_extreme_short", "scenario": "scene-0038-extreme-00", "target_object_id": 2},
    {"audit_id": "cpa_medium_b", "scenario": "scene-0166-medium-00", "target_object_id": 6},
)
MATCH_DISTANCE_M = 3.0
AMBIGUOUS_DISTANCE_M = 6.0
TIME_TOL = 1e-9


def _load_module(relative_path: str, module_name: str) -> Any:
    repo = Path(__file__).resolve().parents[2]
    module_path = repo / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot-load-module:{module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ITER64 = _load_module(
    "experiments/iter64_unsupported_temporal_surface_audit/analyze_unsupported_temporal.py",
    "iter64_unsupported_temporal",
)
ITER65 = _load_module(
    "experiments/iter65_temporal_alignment_audit/analyze_temporal_alignment.py",
    "iter65_temporal_alignment",
)


def require_float(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError(f"non-numeric:{field}")
    return float(value)


def same_object_id(left: Any, right: Any) -> bool:
    return str(left) == str(right)


def load_report(path: Path, label: str) -> tuple[dict[str, Any], list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-{label}:{path}"]
    try:
        report = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"parse-{label}-failed:{exc}"]
    if not isinstance(report, dict):
        return {}, [f"{label}-not-dict"]
    return report, []


def row_identity(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("audit_id")), str(row.get("scenario"))


def expected_rows() -> list[tuple[str, str]]:
    return [(target["audit_id"], target["scenario"]) for target in EXPECTED_TARGETS]


def expected_target_identities() -> list[tuple[str, str, str]]:
    return [
        (target["audit_id"], target["scenario"], str(target["target_object_id"]))
        for target in EXPECTED_TARGETS
    ]


def crosscheck_reports(
    iter59_report: dict[str, Any],
    iter61_report: dict[str, Any],
    iter64_report: dict[str, Any],
    iter65_report: dict[str, Any],
    iter66_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    if iter59_report.get("verdict") != ITER59_VERDICT:
        problems.append(f"iter59-verdict-not-{ITER59_VERDICT}")
    if iter61_report.get("verdict") != ITER61_VERDICT:
        problems.append(f"iter61-verdict-not-{ITER61_VERDICT}")
    if iter64_report.get("verdict") != ITER64_VERDICT:
        problems.append(f"iter64-verdict-not-{ITER64_VERDICT}")
    if iter65_report.get("verdict") != ITER65_VERDICT:
        problems.append(f"iter65-verdict-not-{ITER65_VERDICT}")
    if iter66_report.get("verdict") != ITER66_VERDICT:
        problems.append(f"iter66-verdict-not-{ITER66_VERDICT}")

    episodes61 = iter61_report.get("episodes")
    if not isinstance(episodes61, list):
        problems.append("iter61-episodes-not-list")
    else:
        rows61 = [
            row for row in episodes61
            if isinstance(row, dict) and row.get("row_label") == "no_monitor_object_support"
        ]
        identities61 = [row_identity(row) for row in rows61]
        if identities61 != expected_rows():
            problems.append(f"iter61-no-support-identity-mismatch:{identities61}")

    episodes64 = iter64_report.get("episodes")
    if not isinstance(episodes64, list):
        problems.append("iter64-episodes-not-list")
    else:
        rows64 = [row for row in episodes64 if isinstance(row, dict)]
        identities64 = [row_identity(row) for row in rows64]
        if identities64 != expected_rows():
            problems.append(f"iter64-identity-mismatch:{identities64}")
        for row, target in zip(rows64, EXPECTED_TARGETS, strict=False):
            variant = row.get("best_variant")
            if row.get("row_label") != "pre_contact_object_match":
                problems.append(f"iter64-row-not-match:{row_identity(row)}:{row.get('row_label')}")
            if not isinstance(variant, dict):
                problems.append(f"iter64-best-variant-missing:{row_identity(row)}")
            elif not same_object_id(variant.get("object_id"), target["target_object_id"]):
                problems.append(f"iter64-object-mismatch:{row_identity(row)}:{variant.get('object_id')}")

    episodes65 = iter65_report.get("episodes")
    if not isinstance(episodes65, list):
        problems.append("iter65-episodes-not-list")
    else:
        rows65 = [row for row in episodes65 if isinstance(row, dict)]
        identities65 = [
            (str(row.get("audit_id")), str(row.get("scenario")), str(row.get("matched_object_id")))
            for row in rows65
        ]
        if identities65 != expected_target_identities():
            problems.append(f"iter65-target-identity-mismatch:{identities65}")
        for row in rows65:
            if row.get("row_label") != "matched_object_subthreshold":
                problems.append(f"iter65-row-not-subthreshold:{row_identity(row)}:{row.get('row_label')}")

    episodes66 = iter66_report.get("episodes")
    if not isinstance(episodes66, list):
        problems.append("iter66-episodes-not-list")
        return [], problems
    rows66 = [row for row in episodes66 if isinstance(row, dict)]
    identities66 = [
        (str(row.get("audit_id")), str(row.get("scenario")), str(row.get("target_object_id")))
        for row in rows66
    ]
    if identities66 != expected_target_identities():
        problems.append(f"iter66-target-identity-mismatch:{identities66}")
    for row in rows66:
        first_fire = row.get("first_fire")
        if not isinstance(first_fire, dict) or first_fire.get("first_fire_object_id") is None:
            problems.append(f"iter66-first-fire-missing:{row_identity(row)}")
    return rows66, problems


def episode_paths(proof_root: Path, audit_id: str, scenario: str) -> dict[str, Path]:
    ep_dir = proof_root / "episodes" / f"{audit_id}__{scenario}__on"
    return {
        "eval": ep_dir / "eval.json",
        "decisions": ep_dir / "sentinel_iter48_decisions.jsonl",
    }


def distance_label(distance: float | None) -> str:
    if distance is None:
        return "missing"
    if distance <= MATCH_DISTANCE_M:
        return "match"
    if distance <= AMBIGUOUS_DISTANCE_M:
        return "ambiguous"
    return "no_support"


def object_variants(
    decisions: list[dict[str, Any]],
    foregrounds: list[dict[str, Any]],
    object_id: Any,
    first_foreground_ts: float,
    *,
    only_ts: float | None = None,
) -> tuple[list[dict[str, Any]], int, int]:
    variants: list[dict[str, Any]] = []
    frame_count = 0
    object_rows = 0
    for decision in decisions:
        ts = require_float(decision.get("ts", decision.get("frame_index")), "decision.ts")
        if ts >= first_foreground_ts - TIME_TOL:
            continue
        if only_ts is not None and abs(ts - only_ts) > TIME_TOL:
            continue
        frame_count += 1
        objects = decision.get("objs")
        if not isinstance(objects, list):
            raise ValueError("objs-not-list")
        foregrounds_for_ts = [foreground for foreground in foregrounds if foreground["timestamp"] >= ts - TIME_TOL]
        for obj in objects:
            if not isinstance(obj, dict) or not same_object_id(obj.get("id"), object_id):
                continue
            object_rows += 1
            for foreground in foregrounds_for_ts:
                variants.extend(ITER64.variants_for_object(decision, obj, foreground))
    return variants, frame_count, object_rows


def summarize_bridge_surface(
    decisions: list[dict[str, Any]],
    foregrounds: list[dict[str, Any]],
    object_id: Any,
    first_foreground_ts: float,
    *,
    only_ts: float | None = None,
) -> dict[str, Any]:
    variants, frame_count, object_rows = object_variants(
        decisions,
        foregrounds,
        object_id,
        first_foreground_ts,
        only_ts=only_ts,
    )
    best = ITER64.best_variant(variants)
    distance = best["distance_m"] if best is not None else None
    return {
        "object_id": object_id,
        "frame_count": frame_count,
        "object_rows": object_rows,
        "variant_count": len(variants),
        "best_distance_m": distance,
        "distance_label": distance_label(distance),
        "best_variant": best,
        "top_variants": sorted(
            variants,
            key=lambda item: (
                item["distance_m"],
                item["decision_ts"],
                str(item["object_id"]),
                item["foreground_timestamp"],
            ),
        )[:8],
    }


def row_label(target_surface: dict[str, Any], trigger_surface: dict[str, Any], same_object: bool) -> str:
    target_label = target_surface["distance_label"]
    trigger_label = trigger_surface["distance_label"]
    if target_label == "missing" or trigger_label == "missing":
        return "trigger_target_bridge_insufficient"
    if same_object:
        if target_label == "match":
            return "same_object_target_trigger_match"
        return "same_object_target_trigger_nonmatch"
    if target_label == "match" and trigger_label == "match":
        return "split_target_match_trigger_match"
    if target_label == "match" and trigger_label == "ambiguous":
        return "split_target_match_trigger_ambiguous"
    if target_label == "match" and trigger_label == "no_support":
        return "split_target_match_trigger_no_support"
    return "trigger_target_bridge_insufficient"


def analyze_row(proof_root: Path, iter66_row: dict[str, Any]) -> dict[str, Any]:
    audit_id, scenario = row_identity(iter66_row)
    target_object_id = iter66_row.get("target_object_id")
    first_fire = iter66_row.get("first_fire")
    result: dict[str, Any] = {
        "audit_id": audit_id,
        "scenario": scenario,
        "target_object_id": target_object_id,
        "problems": [],
    }
    if not isinstance(first_fire, dict):
        result["problems"].append("first-fire-not-dict")
        result["row_label"] = "trigger_target_bridge_insufficient"
        return result
    trigger_object_id = first_fire.get("first_fire_object_id")
    first_fire_ts = first_fire.get("first_fire_ts")
    result.update({
        "trigger_object_id": trigger_object_id,
        "first_fire_ts": first_fire_ts,
        "first_fire_channel": first_fire.get("first_fire_channel"),
        "trigger_target_same_object": same_object_id(trigger_object_id, target_object_id),
    })
    paths = episode_paths(proof_root, audit_id, scenario)
    for label in ("eval", "decisions"):
        path = paths[label]
        if not path.exists() or path.stat().st_size == 0:
            result["problems"].append(f"missing-{label}")
    if result["problems"]:
        result["row_label"] = "trigger_target_bridge_insufficient"
        return result

    try:
        foregrounds = ITER64.eligible_foregrounds(paths["eval"])
        first_foreground_ts = foregrounds[0]["timestamp"]
        decisions = ITER64.read_decision_rows(paths["decisions"])
        first_fire_summary, first_fire_problems = ITER65.summarize_first_fire(paths["decisions"], target_object_id)
        result["first_fire_reconstructed"] = first_fire_summary
        result["problems"].extend(first_fire_problems)
        if not first_fire_summary or not same_object_id(first_fire_summary.get("first_fire_object_id"), trigger_object_id):
            result["problems"].append("first-fire-trigger-crosscheck-mismatch")
        target_surface = summarize_bridge_surface(decisions, foregrounds, target_object_id, first_foreground_ts)
        trigger_surface = summarize_bridge_surface(decisions, foregrounds, trigger_object_id, first_foreground_ts)
        first_fire_trigger_surface = summarize_bridge_surface(
            decisions,
            foregrounds,
            trigger_object_id,
            first_foreground_ts,
            only_ts=require_float(first_fire_ts, "first_fire_ts"),
        )
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        result["problems"].append(f"analysis-failed:{exc}")
        result["row_label"] = "trigger_target_bridge_insufficient"
        return result

    label = row_label(target_surface, trigger_surface, result["trigger_target_same_object"])
    result.update({
        "first_foreground_ts": first_foreground_ts,
        "target_surface": target_surface,
        "trigger_surface": trigger_surface,
        "first_fire_trigger_surface": first_fire_trigger_surface,
        "row_label": label,
    })
    return result


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    if infra_problems or len(rows) != 2 or any(row.get("problems") for row in rows):
        return "TRIGGER_TARGET_BRIDGE_AUDIT_BLOCKED"
    labels = [row.get("row_label") for row in rows]
    if any(label == "trigger_target_bridge_insufficient" for label in labels):
        return "TRIGGER_TARGET_BRIDGE_AUDIT_BLOCKED"
    same_rows = [row for row in rows if row.get("trigger_target_same_object")]
    split_rows = [row for row in rows if not row.get("trigger_target_same_object")]
    if same_rows and split_rows:
        return "TRIGGER_TARGET_SAME_AND_SPLIT_COMPLETE"
    if same_rows:
        return "TRIGGER_TARGET_ALL_SAME_COMPLETE"
    if split_rows:
        return "TRIGGER_TARGET_ALL_SPLIT_COMPLETE"
    return "TRIGGER_TARGET_BRIDGE_AUDIT_BLOCKED"


def build_report(
    proof_root: Path,
    iter59_report_path: Path,
    iter61_report_path: Path,
    iter64_report_path: Path,
    iter65_report_path: Path,
    iter66_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    if not proof_root.exists():
        infra_problems.append(f"missing-proof-root:{proof_root}")
    iter59_report, problems59 = load_report(iter59_report_path, "iter59-report")
    iter61_report, problems61 = load_report(iter61_report_path, "iter61-report")
    iter64_report, problems64 = load_report(iter64_report_path, "iter64-report")
    iter65_report, problems65 = load_report(iter65_report_path, "iter65-report")
    iter66_report, problems66 = load_report(iter66_report_path, "iter66-report")
    infra_problems.extend(problems59)
    infra_problems.extend(problems61)
    infra_problems.extend(problems64)
    infra_problems.extend(problems65)
    infra_problems.extend(problems66)
    iter66_rows: list[dict[str, Any]] = []
    if not infra_problems:
        iter66_rows, crosscheck_problems = crosscheck_reports(
            iter59_report,
            iter61_report,
            iter64_report,
            iter65_report,
            iter66_report,
        )
        infra_problems.extend(crosscheck_problems)

    rows = [] if infra_problems else [analyze_row(proof_root, row) for row in iter66_rows]
    label_counts = Counter(row.get("row_label") for row in rows if row.get("row_label"))
    verdict = choose_verdict(rows, infra_problems)
    return {
        "iteration": 67,
        "inputs": {
            "iter59_proof_root": str(proof_root),
            "iter59_report": str(iter59_report_path),
            "iter61_report": str(iter61_report_path),
            "iter64_report": str(iter64_report_path),
            "iter65_report": str(iter65_report_path),
            "iter66_report": str(iter66_report_path),
        },
        "expected_targets": list(EXPECTED_TARGETS),
        "infra_problems": infra_problems,
        "episodes": rows,
        "summary": {
            "target_rows": len(iter66_rows),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "same_object_rows": sum(bool(row.get("trigger_target_same_object")) for row in rows if not row.get("problems")),
            "split_object_rows": sum(
                not bool(row.get("trigger_target_same_object"))
                for row in rows
                if not row.get("problems")
            ),
            "target_match_rows": sum(
                row.get("target_surface", {}).get("distance_label") == "match"
                for row in rows
                if not row.get("problems")
            ),
            "trigger_match_rows": sum(
                row.get("trigger_surface", {}).get("distance_label") == "match"
                for row in rows
                if not row.get("problems")
            ),
        },
        "verdict": verdict,
        "claim_boundary": (
            "two-row trigger/target bridge audit only; no transfer, safety, deployment, "
            "benchmark, actor-causality, repair, population, HD-Score-invariance, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 67 - trigger-target bridge audit",
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
    lines.extend(["", "## Rows", ""])
    for row in report["episodes"]:
        target = row.get("target_surface")
        if not isinstance(target, dict):
            target = {}
        trigger = row.get("trigger_surface")
        if not isinstance(trigger, dict):
            trigger = {}
        first_fire_trigger = row.get("first_fire_trigger_surface")
        if not isinstance(first_fire_trigger, dict):
            first_fire_trigger = {}
        lines.append(
            f"- `{row['audit_id']}` / `{row['scenario']}`: label `{row.get('row_label')}`, "
            f"target `{row.get('target_object_id')}` best `{target.get('best_distance_m')}` "
            f"({target.get('distance_label')}), trigger `{row.get('trigger_object_id')}` best "
            f"`{trigger.get('best_distance_m')}` ({trigger.get('distance_label')}), "
            f"first-fire trigger best `{first_fire_trigger.get('best_distance_m')}` "
            f"({first_fire_trigger.get('distance_label')}), problems `{row.get('problems')}`"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    proof_root: Path,
    iter59_report: Path,
    iter61_report: Path,
    iter64_report: Path,
    iter65_report: Path,
    iter66_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(proof_root, iter59_report, iter61_report, iter64_report, iter65_report, iter66_report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iter59-proof-root",
        type=Path,
        default=Path("experiments/iter59_hugsim_actor_match_audit/proof-actor-match"),
    )
    parser.add_argument(
        "--iter59-report",
        type=Path,
        default=Path("experiments/iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json"),
    )
    parser.add_argument(
        "--iter61-report",
        type=Path,
        default=Path("experiments/iter61_monitor_object_surface_audit/proof-object-surface/object_surface_report.json"),
    )
    parser.add_argument(
        "--iter64-report",
        type=Path,
        default=Path(
            "experiments/iter64_unsupported_temporal_surface_audit/proof-unsupported-temporal/"
            "unsupported_temporal_report.json"
        ),
    )
    parser.add_argument(
        "--iter65-report",
        type=Path,
        default=Path("experiments/iter65_temporal_alignment_audit/proof-alignment/temporal_alignment_report.json"),
    )
    parser.add_argument(
        "--iter66-report",
        type=Path,
        default=Path("experiments/iter66_matched_object_timeline_audit/proof-timeline/timeline_report.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/iter67_trigger_target_bridge_audit/proof-trigger-target/trigger_target_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter67_trigger_target_bridge_audit/proof-trigger-target/trigger_target.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter59_proof_root,
        args.iter59_report,
        args.iter61_report,
        args.iter64_report,
        args.iter65_report,
        args.iter66_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
