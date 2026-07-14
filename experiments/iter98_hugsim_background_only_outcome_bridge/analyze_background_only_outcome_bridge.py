#!/usr/bin/env python3
"""Iteration 98 HUGSIM background-only outcome bridge."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER69_VERDICT = "HUGSIM_MECHANISM_TAXONOMY_COMPLETE"
ITER70_VERDICT = "HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE"

FIXED_ROW = {"audit_id": "cpa_medium_a", "scenario": "scene-0071-medium-00"}


def load_report(path: Path, label: str) -> tuple[dict[str, Any], list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-{label}:{path}"]
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"read-{label}-failed:{path}:{exc}"]
    if not isinstance(data, dict):
        return {}, [f"{label}-not-dict"]
    return data, []


def row_key(row: dict[str, Any]) -> tuple[Any, Any]:
    return (row.get("audit_id"), row.get("scenario"))


def index_rows(rows: Any, label: str, problems: list[str]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    if not isinstance(rows, list):
        problems.append(f"{label}-rows-not-list")
        return {}
    index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        if not isinstance(row, dict):
            problems.append(f"{label}-row-not-dict")
            continue
        audit_id, scenario = row_key(row)
        if not isinstance(audit_id, str) or not isinstance(scenario, str):
            problems.append(f"{label}-row-key-missing:{row}")
            continue
        index.setdefault((audit_id, scenario), []).append(row)
    return index


def exactly_one(
    index: dict[tuple[str, str], list[dict[str, Any]]],
    key: tuple[str, str],
    label: str,
    problems: list[str],
) -> dict[str, Any] | None:
    rows = index.get(key, [])
    if len(rows) != 1:
        problems.append(f"{label}-row-count:{key}:{len(rows)}")
        return None
    row = rows[0]
    if row.get("problems"):
        problems.append(f"{label}-row-problems:{key}:{row.get('problems')}")
    if row.get("detail_problems"):
        problems.append(f"{label}-row-detail-problems:{key}:{row.get('detail_problems')}")
    return row


def require_equal(
    problems: list[str],
    label: str,
    key: tuple[str, str],
    field: str,
    actual: Any,
    expected: Any,
) -> None:
    if actual != expected:
        problems.append(f"{label}-{field}-mismatch:{key}:{actual!r}!={expected!r}")


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter69_report: dict[str, Any],
    iter70_report: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    problems: list[str] = []
    if iter59_report.get("verdict") != ITER59_VERDICT:
        problems.append(f"iter59-verdict-not-{ITER59_VERDICT}")
    if iter69_report.get("verdict") != ITER69_VERDICT:
        problems.append(f"iter69-verdict-not-{ITER69_VERDICT}")
    if iter70_report.get("verdict") != ITER70_VERDICT:
        problems.append(f"iter70-verdict-not-{ITER70_VERDICT}")
    for label, report in (("iter59", iter59_report), ("iter69", iter69_report), ("iter70", iter70_report)):
        if report.get("infra_problems"):
            problems.append(f"{label}-infra-problems:{report.get('infra_problems')}")

    iter59_index = index_rows(iter59_report.get("episodes"), "iter59", problems)
    iter69_index = index_rows(iter69_report.get("episodes"), "iter69", problems)
    iter70_index = index_rows(iter70_report.get("episodes"), "iter70", problems)
    key = (FIXED_ROW["audit_id"], FIXED_ROW["scenario"])
    row59 = exactly_one(iter59_index, key, "iter59", problems)
    row69 = exactly_one(iter69_index, key, "iter69", problems)
    row70 = exactly_one(iter70_index, key, "iter70", problems)
    if row59 is None or row69 is None or row70 is None:
        return row59, row69, row70, problems

    require_equal(problems, "iter59", key, "support_label", row59.get("support_label"), "background_collision_only")
    require_equal(problems, "iter59", key, "foreground_count", row59.get("foreground_count"), 0)
    require_equal(problems, "iter59", key, "first_foreground_ts", row59.get("first_foreground_ts"), None)
    require_equal(problems, "iter59", key, "monitor_object_id", row59.get("monitor_object_id"), 11)
    require_equal(
        problems,
        "iter59",
        key,
        "monitor_provenance_label",
        row59.get("monitor_provenance_label"),
        "unique_ttc_object",
    )
    require_equal(problems, "iter59", key, "first_fire_ts", row59.get("first_fire_ts"), 3.5)
    require_equal(problems, "iter59", key, "first_fire_channel", row59.get("first_fire_channel"), "ttc_only")
    require_equal(problems, "iter59", key, "fired_frames", row59.get("fired_frames"), 4)
    require_equal(problems, "iter59", key, "brake_frames", row59.get("brake_frames"), 11)

    require_equal(problems, "iter69", key, "mechanism_label", row69.get("mechanism_label"), "background_collision_only")
    require_equal(problems, "iter69", key, "iter59_support_label", row69.get("iter59_support_label"), "background_collision_only")
    require_equal(problems, "iter69", key, "first_fire_ts", row69.get("first_fire_ts"), 3.5)
    require_equal(problems, "iter69", key, "first_fire_channel", row69.get("first_fire_channel"), "ttc_only")
    require_equal(problems, "iter69", key, "monitor_object_id", row69.get("monitor_object_id"), 11)

    report70 = row70.get("report") if isinstance(row70.get("report"), dict) else {}
    decision70 = row70.get("decision_log") if isinstance(row70.get("decision_log"), dict) else {}
    require_equal(
        problems,
        "iter70",
        key,
        "structural_label",
        row70.get("structural_label"),
        "foreground_absent_background_only",
    )
    require_equal(problems, "iter70", key, "iter59_support_label", row70.get("iter59_support_label"), "background_collision_only")
    require_equal(problems, "iter70", key, "report.foreground_count", report70.get("foreground_count"), 0)
    require_equal(problems, "iter70", key, "report.first_foreground_ts", report70.get("first_foreground_ts"), None)
    require_equal(problems, "iter70", key, "report.first_fire_ts", report70.get("first_fire_ts"), 3.5)
    require_equal(problems, "iter70", key, "report.monitor_object_id", report70.get("monitor_object_id"), 11)
    require_equal(
        problems,
        "iter70",
        key,
        "report.monitor_provenance_label",
        report70.get("monitor_provenance_label"),
        "unique_ttc_object",
    )
    require_equal(problems, "iter70", key, "decision_log.first_fire_ts", decision70.get("first_fire_ts"), 3.5)
    require_equal(problems, "iter70", key, "decision_log.first_fire_channel", decision70.get("first_fire_channel"), "ttc_only")
    require_equal(problems, "iter70", key, "decision_log.fired_frames", decision70.get("fired_frames"), 4)
    require_equal(problems, "iter70", key, "decision_log.brake_frames", decision70.get("brake_frames"), 11)
    require_equal(problems, "iter70", key, "pre_or_at_foreground_fire", row70.get("pre_or_at_foreground_fire"), False)
    return row59, row69, row70, problems


def classify_row(measurements: dict[str, Any], problems: list[str]) -> str:
    if problems:
        return "background_only_outcome_insufficient"
    labels_background = (
        measurements["iter59_support_label"] == "background_collision_only"
        and measurements["iter69_mechanism_label"] == "background_collision_only"
        and measurements["iter70_structural_label"] == "foreground_absent_background_only"
    )
    foreground_absent = (
        measurements["iter59_foreground_count"] == 0
        and measurements["iter70_foreground_count"] == 0
        and measurements["iter59_first_foreground_ts"] is None
        and measurements["iter70_first_foreground_ts"] is None
    )
    monitor_object_preserved = (
        measurements["iter59_monitor_object_id"]
        == measurements["iter69_monitor_object_id"]
        == measurements["iter70_monitor_object_id"]
        == 11
        and measurements["iter59_monitor_provenance_label"] == "unique_ttc_object"
        and measurements["iter70_monitor_provenance_label"] == "unique_ttc_object"
    )
    if not (labels_background and foreground_absent and monitor_object_preserved):
        return "background_only_outcome_mixed"
    live_fire = (
        measurements["iter59_first_fire_ts"] == 3.5
        and measurements["iter69_first_fire_ts"] == 3.5
        and measurements["iter70_report_first_fire_ts"] == 3.5
        and measurements["iter70_decision_first_fire_ts"] == 3.5
        and measurements["iter59_first_fire_channel"] == "ttc_only"
        and measurements["iter69_first_fire_channel"] == "ttc_only"
        and measurements["iter70_decision_first_fire_channel"] == "ttc_only"
        and measurements["iter59_fired_frames"] == 4
        and measurements["iter70_fired_frames"] == 4
        and measurements["iter59_brake_frames"] == 11
        and measurements["iter70_brake_frames"] == 11
    )
    if live_fire:
        return "background_only_ttc_fire_foreground_absent"
    no_fire = (
        measurements["iter59_first_fire_ts"] is None
        and measurements["iter69_first_fire_ts"] is None
        and measurements["iter70_report_first_fire_ts"] is None
        and measurements["iter70_decision_first_fire_ts"] is None
        and measurements["iter59_fired_frames"] == 0
        and measurements["iter70_fired_frames"] == 0
    )
    if no_fire:
        return "background_only_foreground_absent_no_fire"
    return "background_only_outcome_mixed"


def analyze_row(row59: dict[str, Any], row69: dict[str, Any], row70: dict[str, Any]) -> dict[str, Any]:
    row_problems: list[str] = []
    report70 = row70.get("report") if isinstance(row70.get("report"), dict) else {}
    decision70 = row70.get("decision_log") if isinstance(row70.get("decision_log"), dict) else {}
    if not report70:
        row_problems.append("iter70-report-missing")
    if not decision70:
        row_problems.append("iter70-decision-log-missing")
    measurements = {
        "iter59_support_label": row59.get("support_label"),
        "iter69_mechanism_label": row69.get("mechanism_label"),
        "iter69_support_label": row69.get("iter59_support_label"),
        "iter70_structural_label": row70.get("structural_label"),
        "iter70_support_label": row70.get("iter59_support_label"),
        "iter59_foreground_count": row59.get("foreground_count"),
        "iter70_foreground_count": report70.get("foreground_count"),
        "iter59_first_foreground_ts": row59.get("first_foreground_ts"),
        "iter70_first_foreground_ts": report70.get("first_foreground_ts"),
        "iter59_first_fire_ts": row59.get("first_fire_ts"),
        "iter69_first_fire_ts": row69.get("first_fire_ts"),
        "iter70_report_first_fire_ts": report70.get("first_fire_ts"),
        "iter70_decision_first_fire_ts": decision70.get("first_fire_ts"),
        "iter59_first_fire_channel": row59.get("first_fire_channel"),
        "iter69_first_fire_channel": row69.get("first_fire_channel"),
        "iter70_decision_first_fire_channel": decision70.get("first_fire_channel"),
        "iter59_fired_frames": row59.get("fired_frames"),
        "iter70_fired_frames": decision70.get("fired_frames"),
        "iter59_brake_frames": row59.get("brake_frames"),
        "iter70_brake_frames": decision70.get("brake_frames"),
        "iter59_monitor_object_id": row59.get("monitor_object_id"),
        "iter69_monitor_object_id": row69.get("monitor_object_id"),
        "iter70_monitor_object_id": report70.get("monitor_object_id"),
        "iter59_monitor_provenance_label": row59.get("monitor_provenance_label"),
        "iter70_monitor_provenance_label": report70.get("monitor_provenance_label"),
        "iter70_pre_or_at_foreground_fire": row70.get("pre_or_at_foreground_fire"),
        "foreground_support_absent": row59.get("foreground_count") == 0 and report70.get("foreground_count") == 0,
        "monitor_fire_present": row59.get("first_fire_ts") is not None and decision70.get("fired_frames", 0) > 0,
    }
    return {
        "audit_id": row59.get("audit_id"),
        "scenario": row59.get("scenario"),
        "measurements": measurements,
        "row_label": classify_row(measurements, row_problems),
        "problems": row_problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != 1
        or any(row.get("problems") for row in rows)
        or "background_only_outcome_insufficient" in labels
    ):
        return "HUGSIM_BACKGROUND_ONLY_OUTCOME_BRIDGE_BLOCKED"
    if labels == ["background_only_ttc_fire_foreground_absent"]:
        return "HUGSIM_BACKGROUND_ONLY_OUTCOME_BRIDGE_COMPLETE"
    if labels == ["background_only_foreground_absent_no_fire"]:
        return "HUGSIM_BACKGROUND_ONLY_OUTCOME_NO_FIRE_COMPLETE"
    return "HUGSIM_BACKGROUND_ONLY_OUTCOME_MIXED_COMPLETE"


def build_report(iter59_report_path: Path, iter69_report_path: Path, iter70_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = load_report(iter59_report_path, "iter59-report")
    iter69_report, problems69 = load_report(iter69_report_path, "iter69-report")
    iter70_report, problems70 = load_report(iter70_report_path, "iter70-report")
    infra_problems.extend(problems59 + problems69 + problems70)
    row59 = row69 = row70 = None
    if not infra_problems:
        row59, row69, row70, source_problems = crosscheck_sources(iter59_report, iter69_report, iter70_report)
        infra_problems.extend(source_problems)
    rows = [] if infra_problems or row59 is None or row69 is None or row70 is None else [analyze_row(row59, row69, row70)]
    label_counts = Counter(row.get("row_label") for row in rows)
    return {
        "iteration": 98,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter69_report": str(iter69_report_path),
            "iter70_report": str(iter70_report_path),
        },
        "fixed_rows": [FIXED_ROW],
        "infra_problems": infra_problems,
        "events": rows,
        "summary": {
            "target_rows": 1 if row59 is not None and row69 is not None and row70 is not None else 0,
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "background_only_rows": sum(
                row.get("measurements", {}).get("iter70_structural_label") == "foreground_absent_background_only"
                for row in rows
            ),
            "foreground_absent_rows": sum(
                row.get("measurements", {}).get("foreground_support_absent") is True for row in rows
            ),
            "monitor_fire_rows": sum(row.get("measurements", {}).get("monitor_fire_present") is True for row in rows),
            "ttc_only_fire_rows": sum(
                row.get("measurements", {}).get("iter70_decision_first_fire_channel") == "ttc_only" for row in rows
            ),
            "preserved_monitor_object_rows": sum(
                row.get("measurements", {}).get("iter59_monitor_object_id")
                == row.get("measurements", {}).get("iter69_monitor_object_id")
                == row.get("measurements", {}).get("iter70_monitor_object_id")
                == 11
                for row in rows
            ),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "one-row descriptive background-only provenance/timing bridge only; no actor-causality, "
            "repair, threshold-value, transfer, safety, deployment, robustness, benchmark, "
            "population-rate, HD-Score-invariance, commercial-value, real-world behavior, "
            "first-responder behavior, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 98 - HUGSIM background-only outcome bridge",
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
            "## Events",
            "",
            "| audit id | scenario | foreground count | first fire | channel | fired frames | monitor object | label | problems |",
            "|---|---|---:|---:|---|---:|---:|---|---|",
        ]
    )
    for row in report["events"]:
        measurements = row.get("measurements") or {}
        lines.append(
            f"| `{row['audit_id']}` | `{row['scenario']}` | "
            f"`{measurements.get('iter70_foreground_count')}` | "
            f"`{measurements.get('iter70_decision_first_fire_ts')}` | "
            f"`{measurements.get('iter70_decision_first_fire_channel')}` | "
            f"`{measurements.get('iter70_fired_frames')}` | "
            f"`{measurements.get('iter70_monitor_object_id')}` | "
            f"`{row['row_label']}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(iter59_report: Path, iter69_report: Path, iter70_report: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(iter59_report, iter69_report, iter70_report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iter59-report",
        type=Path,
        default=Path("experiments/iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json"),
    )
    parser.add_argument(
        "--iter69-report",
        type=Path,
        default=Path("experiments/iter69_hugsim_mechanism_taxonomy/proof-taxonomy/taxonomy_report.json"),
    )
    parser.add_argument(
        "--iter70-report",
        type=Path,
        default=Path("experiments/iter70_hugsim_structural_timing_audit/proof-structural/structural_report.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter98_hugsim_background_only_outcome_bridge/proof-background-outcome/"
            "background_only_outcome_bridge_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter98_hugsim_background_only_outcome_bridge/proof-background-outcome/"
            "background_only_outcome_bridge.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter59_report, args.iter69_report, args.iter70_report, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
