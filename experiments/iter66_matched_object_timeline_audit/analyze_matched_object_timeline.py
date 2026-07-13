#!/usr/bin/env python3
"""Iteration 66 matched-object hazard timeline audit analyzer."""

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
EXPECTED_TARGETS = (
    {"audit_id": "ttc_extreme_short", "scenario": "scene-0038-extreme-00", "object_id": 2},
    {"audit_id": "cpa_medium_b", "scenario": "scene-0166-medium-00", "object_id": 6},
)
EVER_ACTIVE_LABEL = "target_object_ever_active_hazard"
NEVER_ACTIVE_LABEL = "target_object_visible_never_active"
INSUFFICIENT_LABEL = "target_object_insufficient_presence"
TIME_TOL = 1e-9
CPA_MARGIN = 1.5
TTC_THRESH = 2.5
CPA_BORDERLINE = 3.0
TTC_BORDERLINE = 5.0


def _load_module(relative_path: str, module_name: str) -> Any:
    repo = Path(__file__).resolve().parents[2]
    module_path = repo / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot-load-module:{module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ITER59 = _load_module(
    "experiments/iter59_hugsim_actor_match_audit/analyze_actor_match.py",
    "iter59_actor_match",
)
ITER62 = _load_module(
    "experiments/iter62_nontrigger_ranking_audit/analyze_nontrigger_ranking.py",
    "iter62_nontrigger_ranking",
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


def target_identity(target: dict[str, Any]) -> tuple[str, str, str]:
    return str(target.get("audit_id")), str(target.get("scenario")), str(target.get("object_id"))


def row_identity(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("audit_id")), str(row.get("scenario"))


def expected_identities() -> list[tuple[str, str, str]]:
    return [target_identity(target) for target in EXPECTED_TARGETS]


def crosscheck_reports(
    iter59_report: dict[str, Any],
    iter61_report: dict[str, Any],
    iter64_report: dict[str, Any],
    iter65_report: dict[str, Any],
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

    episodes61 = iter61_report.get("episodes")
    if not isinstance(episodes61, list):
        problems.append("iter61-episodes-not-list")
    else:
        rows61 = [
            row for row in episodes61
            if isinstance(row, dict) and row.get("row_label") == "no_monitor_object_support"
        ]
        identities61 = [row_identity(row) for row in rows61]
        expected_rows = [(target["audit_id"], target["scenario"]) for target in EXPECTED_TARGETS]
        if identities61 != expected_rows:
            problems.append(f"iter61-no-support-identity-mismatch:{identities61}")

    episodes64 = iter64_report.get("episodes")
    if not isinstance(episodes64, list):
        problems.append("iter64-episodes-not-list")
    else:
        rows64 = [row for row in episodes64 if isinstance(row, dict)]
        identities64 = [row_identity(row) for row in rows64]
        expected_rows = [(target["audit_id"], target["scenario"]) for target in EXPECTED_TARGETS]
        if identities64 != expected_rows:
            problems.append(f"iter64-identity-mismatch:{identities64}")
        for row, target in zip(rows64, EXPECTED_TARGETS, strict=False):
            variant = row.get("best_variant")
            if row.get("row_label") != "pre_contact_object_match":
                problems.append(f"iter64-row-not-match:{row_identity(row)}:{row.get('row_label')}")
            if not isinstance(variant, dict):
                problems.append(f"iter64-best-variant-missing:{row_identity(row)}")
            elif not same_object_id(variant.get("object_id"), target["object_id"]):
                problems.append(f"iter64-object-mismatch:{row_identity(row)}:{variant.get('object_id')}")

    episodes65 = iter65_report.get("episodes")
    if not isinstance(episodes65, list):
        problems.append("iter65-episodes-not-list")
        return [], problems
    rows65 = [row for row in episodes65 if isinstance(row, dict)]
    identities65 = [
        (str(row.get("audit_id")), str(row.get("scenario")), str(row.get("matched_object_id")))
        for row in rows65
    ]
    if identities65 != expected_identities():
        problems.append(f"iter65-target-identity-mismatch:{identities65}")
    for row in rows65:
        if row.get("row_label") != "matched_object_subthreshold":
            problems.append(f"iter65-row-not-subthreshold:{row_identity(row)}:{row.get('row_label')}")
        if "matched_decision_ts" not in row:
            problems.append(f"iter65-matched-decision-missing:{row_identity(row)}")
    return rows65, problems


def episode_paths(proof_root: Path, audit_id: str, scenario: str) -> dict[str, Path]:
    ep_dir = proof_root / "episodes" / f"{audit_id}__{scenario}__on"
    return {
        "eval": ep_dir / "eval.json",
        "decisions": ep_dir / "sentinel_iter48_decisions.jsonl",
    }


def first_foreground_timestamp(eval_path: Path) -> float:
    doc = json.loads(eval_path.read_text())
    provenance = doc.get("collision_provenance")
    if not isinstance(provenance, list):
        raise ValueError("collision-provenance-not-list")
    timestamps: list[float] = []
    for row in provenance:
        if (
            isinstance(row, dict)
            and row.get("collision_type") == "foreground"
            and isinstance(row.get("obs_box"), list)
            and len(row["obs_box"]) >= 2
        ):
            try:
                require_float(row["obs_box"][0], "obs_box.x")
                require_float(row["obs_box"][1], "obs_box.y")
                timestamps.append(require_float(row.get("timestamp"), "foreground.timestamp"))
            except (TypeError, ValueError):
                continue
    if not timestamps:
        raise ValueError("eligible-foreground-missing")
    return min(timestamps)


def read_decision_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if isinstance(row, dict) and "trace_error" not in row:
            rows.append(row)
    return rows


def object_metric_for_row(row: dict[str, Any], object_id: Any) -> dict[str, Any] | None:
    objects = ITER62.object_metrics(row)
    matched = [item for item in objects if same_object_id(item.get("object_id"), object_id)]
    if len(matched) > 1:
        raise ValueError(f"object-{object_id}-duplicate")
    if not matched:
        return None
    metric = matched[0]
    cpa_cross = bool(metric.get("cpa_cross"))
    ttc_cross = bool(metric.get("ttc_cross"))
    min_cpa = require_float(metric.get("min_cpa"), "metric.min_cpa")
    ttc = metric.get("ttc")
    if ttc is not None:
        ttc = require_float(ttc, "metric.ttc")
    metric["hazard_cross"] = cpa_cross or ttc_cross
    metric["cpa_borderline"] = not cpa_cross and min_cpa < CPA_BORDERLINE
    metric["ttc_borderline"] = not ttc_cross and ttc is not None and ttc < TTC_BORDERLINE
    metric["borderline"] = bool(metric["cpa_borderline"] or metric["ttc_borderline"])
    return metric


def relative_time(event_ts: float | None, reference_ts: float | None) -> str:
    if event_ts is None:
        return "none"
    if reference_ts is None:
        return "reference_missing"
    if event_ts < reference_ts - TIME_TOL:
        return "before"
    if abs(event_ts - reference_ts) <= TIME_TOL:
        return "same"
    return "after"


def summarize_first_fire(decisions_path: Path, object_id: Any) -> tuple[dict[str, Any] | None, list[str]]:
    summary, problems = ITER65.summarize_first_fire(decisions_path, object_id)
    return summary, problems


def analyze_row(proof_root: Path, iter65_row: dict[str, Any]) -> dict[str, Any]:
    audit_id, scenario = row_identity(iter65_row)
    object_id = iter65_row.get("matched_object_id")
    matched_ts = require_float(iter65_row.get("matched_decision_ts"), "iter65.matched_decision_ts")
    result: dict[str, Any] = {
        "audit_id": audit_id,
        "scenario": scenario,
        "target_object_id": object_id,
        "matched_decision_ts": matched_ts,
        "problems": [],
    }
    paths = episode_paths(proof_root, audit_id, scenario)
    for label in ("eval", "decisions"):
        path = paths[label]
        if not path.exists() or path.stat().st_size == 0:
            result["problems"].append(f"missing-{label}")
    if result["problems"]:
        result["row_label"] = INSUFFICIENT_LABEL
        return result

    first_fire_summary, first_fire_problems = summarize_first_fire(paths["decisions"], object_id)
    result["first_fire"] = first_fire_summary
    result["problems"].extend(first_fire_problems)
    try:
        first_foreground_ts = first_foreground_timestamp(paths["eval"])
        decision_rows = read_decision_rows(paths["decisions"])
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        result["problems"].append(f"parse-failed:{exc}")
        result["row_label"] = INSUFFICIENT_LABEL
        return result

    frames: list[dict[str, Any]] = []
    try:
        for index, row in enumerate(decision_rows):
            ts = require_float(row.get("ts", row.get("frame_index")), "decision.ts")
            if ts >= first_foreground_ts - TIME_TOL:
                continue
            metric = object_metric_for_row(row, object_id)
            record: dict[str, Any] = {
                "frame_index": row.get("frame_index", index),
                "ts": ts,
                "object_present": metric is not None,
                "fired": bool(row.get("fired")),
                "brake": bool(row.get("brake")),
            }
            if metric is not None:
                record.update(metric)
            frames.append(record)
    except (KeyError, TypeError, ValueError) as exc:
        result["problems"].append(f"analysis-failed:{exc}")
        result["row_label"] = INSUFFICIENT_LABEL
        return result

    present_frames = [frame for frame in frames if frame["object_present"]]
    hazard_frames = [frame for frame in present_frames if frame.get("hazard_cross")]
    borderline_frames = [frame for frame in present_frames if frame.get("borderline")]
    if hazard_frames:
        label = EVER_ACTIVE_LABEL
    elif present_frames:
        label = NEVER_ACTIVE_LABEL
    else:
        label = INSUFFICIENT_LABEL

    first_hazard_ts = hazard_frames[0]["ts"] if hazard_frames else None
    first_borderline_ts = borderline_frames[0]["ts"] if borderline_frames else None
    first_fire_ts = first_fire_summary.get("first_fire_ts") if isinstance(first_fire_summary, dict) else None
    result.update({
        "first_foreground_ts": first_foreground_ts,
        "row_label": label,
        "pre_contact_frame_count": len(frames),
        "present_frame_count": len(present_frames),
        "absent_frame_count": sum(not frame["object_present"] for frame in frames),
        "hazard_frame_count": len(hazard_frames),
        "borderline_frame_count": len(borderline_frames),
        "first_present_ts": present_frames[0]["ts"] if present_frames else None,
        "last_present_ts": present_frames[-1]["ts"] if present_frames else None,
        "first_hazard_ts": first_hazard_ts,
        "first_borderline_ts": first_borderline_ts,
        "first_hazard_relative_to_matched_ts": relative_time(first_hazard_ts, matched_ts),
        "first_hazard_relative_to_first_fire": relative_time(first_hazard_ts, first_fire_ts),
        "first_borderline_relative_to_matched_ts": relative_time(first_borderline_ts, matched_ts),
        "first_borderline_relative_to_first_fire": relative_time(first_borderline_ts, first_fire_ts),
        "min_cpa": min((frame["min_cpa"] for frame in present_frames), default=None),
        "min_ttc": min((frame["ttc"] for frame in present_frames if frame.get("ttc") is not None), default=None),
        "frames": frames,
    })
    return result


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    if infra_problems or len(rows) != 2 or any(row.get("problems") for row in rows):
        return "MATCHED_OBJECT_TIMELINE_AUDIT_BLOCKED"
    labels = [row.get("row_label") for row in rows]
    if labels == [EVER_ACTIVE_LABEL, EVER_ACTIVE_LABEL]:
        return "MATCHED_OBJECT_TIMELINE_EVER_HAZARD_COMPLETE"
    if labels == [NEVER_ACTIVE_LABEL, NEVER_ACTIVE_LABEL]:
        return "MATCHED_OBJECT_TIMELINE_NEVER_HAZARD_COMPLETE"
    if all(label in {EVER_ACTIVE_LABEL, NEVER_ACTIVE_LABEL, INSUFFICIENT_LABEL} for label in labels):
        return "MATCHED_OBJECT_TIMELINE_MIXED_COMPLETE"
    return "MATCHED_OBJECT_TIMELINE_AUDIT_BLOCKED"


def build_report(
    proof_root: Path,
    iter59_report_path: Path,
    iter61_report_path: Path,
    iter64_report_path: Path,
    iter65_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    if not proof_root.exists():
        infra_problems.append(f"missing-proof-root:{proof_root}")
    iter59_report, problems59 = load_report(iter59_report_path, "iter59-report")
    iter61_report, problems61 = load_report(iter61_report_path, "iter61-report")
    iter64_report, problems64 = load_report(iter64_report_path, "iter64-report")
    iter65_report, problems65 = load_report(iter65_report_path, "iter65-report")
    infra_problems.extend(problems59)
    infra_problems.extend(problems61)
    infra_problems.extend(problems64)
    infra_problems.extend(problems65)
    iter65_rows: list[dict[str, Any]] = []
    if not infra_problems:
        iter65_rows, crosscheck_problems = crosscheck_reports(
            iter59_report,
            iter61_report,
            iter64_report,
            iter65_report,
        )
        infra_problems.extend(crosscheck_problems)

    rows = [] if infra_problems else [analyze_row(proof_root, row) for row in iter65_rows]
    label_counts = Counter(row.get("row_label") for row in rows if row.get("row_label"))
    verdict = choose_verdict(rows, infra_problems)
    return {
        "iteration": 66,
        "inputs": {
            "iter59_proof_root": str(proof_root),
            "iter59_report": str(iter59_report_path),
            "iter61_report": str(iter61_report_path),
            "iter64_report": str(iter64_report_path),
            "iter65_report": str(iter65_report_path),
        },
        "expected_targets": list(EXPECTED_TARGETS),
        "infra_problems": infra_problems,
        "episodes": rows,
        "summary": {
            "target_rows": len(iter65_rows),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "total_pre_contact_frames": sum(
                row.get("pre_contact_frame_count", 0)
                for row in rows
                if not row.get("problems")
            ),
            "total_present_frames": sum(
                row.get("present_frame_count", 0)
                for row in rows
                if not row.get("problems")
            ),
            "total_hazard_frames": sum(
                row.get("hazard_frame_count", 0)
                for row in rows
                if not row.get("problems")
            ),
            "total_borderline_frames": sum(
                row.get("borderline_frame_count", 0)
                for row in rows
                if not row.get("problems")
            ),
        },
        "verdict": verdict,
        "claim_boundary": (
            "two-row target-object temporal surface audit only; no transfer, safety, deployment, "
            "benchmark, actor-causality, repair, population, HD-Score-invariance, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 66 - matched-object hazard timeline audit",
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
        first_fire = row.get("first_fire")
        if not isinstance(first_fire, dict):
            first_fire = {}
        lines.append(
            f"- `{row['audit_id']}` / `{row['scenario']}` / object `{row.get('target_object_id')}`: "
            f"label `{row.get('row_label')}`, present `{row.get('present_frame_count')}`/"
            f"`{row.get('pre_contact_frame_count')}`, hazard `{row.get('hazard_frame_count')}`, "
            f"borderline `{row.get('borderline_frame_count')}`, min_cpa `{row.get('min_cpa')}`, "
            f"min_ttc `{row.get('min_ttc')}`, first_fire `{first_fire.get('first_fire_channel')}` "
            f"at `{first_fire.get('first_fire_ts')}`, problems `{row.get('problems')}`"
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
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(proof_root, iter59_report, iter61_report, iter64_report, iter65_report)
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
        "--out",
        type=Path,
        default=Path("experiments/iter66_matched_object_timeline_audit/proof-timeline/timeline_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter66_matched_object_timeline_audit/proof-timeline/timeline.md"),
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
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
