#!/usr/bin/env python3
"""Iteration 99 HUGSIM structural bridge coverage audit."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ITER70_VERDICT = "HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE"
ITER96_VERDICT = "HUGSIM_BRANCH_TAXONOMY_LATE_FIRE_OUTCOME_BRIDGE_COMPLETE"
ITER97_VERDICT = "HUGSIM_SURFACE_SILENT_OUTCOME_MARGIN_BRIDGE_COMPLETE"
ITER98_VERDICT = "HUGSIM_BACKGROUND_ONLY_OUTCOME_BRIDGE_COMPLETE"

FIXED_ROWS = (
    {"audit_id": "mixed_extreme", "scenario": "scene-0062-extreme-00"},
    {"audit_id": "both_distinct_extreme", "scenario": "scene-0138-extreme-00"},
    {"audit_id": "nofire_hard_control", "scenario": "scene-0041-hard-00"},
    {"audit_id": "cpa_medium_a", "scenario": "scene-0071-medium-00"},
    {"audit_id": "ttc_medium_a", "scenario": "scene-0071-medium-01"},
)

EXPECTED_BRIDGE_KEYS = {
    "iter96_late_fire": {
        ("both_distinct_extreme", "scene-0138-extreme-00"),
        ("ttc_medium_a", "scene-0071-medium-01"),
    },
    "iter97_surface_silent": {
        ("mixed_extreme", "scene-0062-extreme-00"),
        ("nofire_hard_control", "scene-0041-hard-00"),
    },
    "iter98_background_only": {
        ("cpa_medium_a", "scene-0071-medium-00"),
    },
}

EXPECTED_SOURCE_FOR_LABEL = {
    "foreground_present_late_fire": "iter96_late_fire",
    "foreground_present_surface_silent": "iter97_surface_silent",
    "foreground_absent_background_only": "iter98_background_only",
}

COMPLETION_LABEL_FOR_SOURCE = {
    "iter96_late_fire": "structural_late_fire_bridge_covered",
    "iter97_surface_silent": "structural_surface_silent_bridge_covered",
    "iter98_background_only": "structural_background_only_bridge_covered",
}


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


def string_key(row: dict[str, Any]) -> tuple[str, str] | None:
    audit_id, scenario = row_key(row)
    if not isinstance(audit_id, str) or not isinstance(scenario, str):
        return None
    return (audit_id, scenario)


def index_rows(rows: Any, label: str, problems: list[str]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    if not isinstance(rows, list):
        problems.append(f"{label}-rows-not-list")
        return {}
    index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        if not isinstance(row, dict):
            problems.append(f"{label}-row-not-dict")
            continue
        key = string_key(row)
        if key is None:
            problems.append(f"{label}-row-key-missing:{row}")
            continue
        index.setdefault(key, []).append(row)
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
    return row


def check_verdicts_and_infra(
    iter70_report: dict[str, Any],
    iter96_report: dict[str, Any],
    iter97_report: dict[str, Any],
    iter98_report: dict[str, Any],
) -> list[str]:
    problems: list[str] = []
    expected = (
        ("iter70", iter70_report, ITER70_VERDICT),
        ("iter96", iter96_report, ITER96_VERDICT),
        ("iter97", iter97_report, ITER97_VERDICT),
        ("iter98", iter98_report, ITER98_VERDICT),
    )
    for label, report, verdict in expected:
        if report.get("verdict") != verdict:
            problems.append(f"{label}-verdict-not-{verdict}")
        if report.get("infra_problems"):
            problems.append(f"{label}-infra-problems:{report.get('infra_problems')}")
    return problems


def check_iter70_rows(iter70_report: dict[str, Any], problems: list[str]) -> list[dict[str, Any]]:
    index = index_rows(iter70_report.get("episodes"), "iter70", problems)
    fixed_keys = {(row["audit_id"], row["scenario"]) for row in FIXED_ROWS}
    rows = []
    for key in fixed_keys:
        row = exactly_one(index, key, "iter70", problems)
        if row is not None:
            rows.append(row)
    observed_keys = set(index)
    extra_keys = observed_keys - fixed_keys
    if extra_keys:
        problems.append(f"iter70-extra-rows:{sorted(extra_keys)}")
    label_counts = Counter(row.get("structural_label") for row in rows)
    expected_counts = {
        "foreground_absent_background_only": 1,
        "foreground_present_late_fire": 2,
        "foreground_present_surface_silent": 2,
    }
    if dict(sorted(label_counts.items())) != expected_counts:
        problems.append(f"iter70-structural-label-counts-mismatch:{dict(sorted(label_counts.items()))}")
    if len(rows) != len(FIXED_ROWS):
        problems.append(f"iter70-fixed-row-count-mismatch:{len(rows)}")
    return rows


def collect_bridge_events(
    report: dict[str, Any],
    source: str,
    problems: list[str],
) -> list[dict[str, Any]]:
    events = report.get("events")
    if not isinstance(events, list):
        problems.append(f"{source}-events-not-list")
        return []
    collected: list[dict[str, Any]] = []
    keys: set[tuple[str, str]] = set()
    for event in events:
        if not isinstance(event, dict):
            problems.append(f"{source}-event-not-dict")
            continue
        key = string_key(event)
        if key is None:
            problems.append(f"{source}-event-key-missing:{event}")
            continue
        if event.get("problems"):
            problems.append(f"{source}-event-problems:{key}:{event.get('problems')}")
        keys.add(key)
        collected.append({"source": source, "key": key, "event": event})
    expected_keys = EXPECTED_BRIDGE_KEYS[source]
    if keys != expected_keys:
        problems.append(f"{source}-coverage-keys-mismatch:observed={sorted(keys)} expected={sorted(expected_keys)}")
    return collected


def normalize_bridge_measurements(source: str, event: dict[str, Any]) -> dict[str, Any]:
    measurements = event.get("measurements")
    if isinstance(measurements, dict):
        base = dict(measurements)
    else:
        base = {}
    for field in ("first_foreground_ts", "first_fire_ts", "first_fire_channel", "fire_minus_foreground_s"):
        if field in event:
            base.setdefault(field, event.get(field))
    base["bridge_source"] = source
    base["bridge_row_label"] = event.get("row_label")
    return base


def classify_row(row70: dict[str, Any], bridge_hits: list[dict[str, Any]], row_problems: list[str]) -> str:
    if row_problems:
        return "structural_bridge_coverage_insufficient"
    structural_label = row70.get("structural_label")
    expected_source = EXPECTED_SOURCE_FOR_LABEL.get(str(structural_label))
    if not bridge_hits:
        return "structural_bridge_uncovered"
    if len(bridge_hits) != 1 or bridge_hits[0].get("source") != expected_source:
        return "structural_bridge_duplicate_or_incompatible"
    return COMPLETION_LABEL_FOR_SOURCE[str(expected_source)]


def analyze_row(row70: dict[str, Any], bridge_hits: list[dict[str, Any]]) -> dict[str, Any]:
    row_problems: list[str] = []
    structural_label = row70.get("structural_label")
    if structural_label not in EXPECTED_SOURCE_FOR_LABEL:
        row_problems.append(f"unknown-structural-label:{structural_label}")
    report70 = row70.get("report") if isinstance(row70.get("report"), dict) else {}
    decision70 = row70.get("decision_log") if isinstance(row70.get("decision_log"), dict) else {}
    if not report70:
        row_problems.append("iter70-report-missing")
    bridge_measurements = [
        normalize_bridge_measurements(str(hit["source"]), hit["event"]) for hit in bridge_hits
    ]
    measurements = {
        "structural_label": structural_label,
        "iter59_support_label": row70.get("iter59_support_label"),
        "iter70_first_foreground_ts": report70.get("first_foreground_ts"),
        "iter70_first_fire_ts": report70.get("first_fire_ts"),
        "iter70_first_fire_channel": decision70.get("first_fire_channel"),
        "bridge_hit_count": len(bridge_hits),
        "bridge_sources": [hit["source"] for hit in bridge_hits],
        "bridge_row_labels": [hit["event"].get("row_label") for hit in bridge_hits],
        "bridge_measurements": bridge_measurements,
        "covered_exactly_once": len(bridge_hits) == 1,
        "bridge_source_compatible": len(bridge_hits) == 1
        and bridge_hits[0].get("source") == EXPECTED_SOURCE_FOR_LABEL.get(str(structural_label)),
    }
    return {
        "audit_id": row70.get("audit_id"),
        "scenario": row70.get("scenario"),
        "measurements": measurements,
        "row_label": classify_row(row70, bridge_hits, row_problems),
        "problems": row_problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_ROWS)
        or any(row.get("problems") for row in rows)
        or "structural_bridge_coverage_insufficient" in labels
    ):
        return "HUGSIM_STRUCTURAL_BRIDGE_COVERAGE_BLOCKED"
    if "structural_bridge_duplicate_or_incompatible" in labels:
        return "HUGSIM_STRUCTURAL_BRIDGE_COVERAGE_MIXED_COMPLETE"
    if "structural_bridge_uncovered" in labels:
        return "HUGSIM_STRUCTURAL_BRIDGE_COVERAGE_PARTIAL_COMPLETE"
    expected_label_counts = {
        "structural_background_only_bridge_covered": 1,
        "structural_late_fire_bridge_covered": 2,
        "structural_surface_silent_bridge_covered": 2,
    }
    if dict(sorted(Counter(labels).items())) == expected_label_counts:
        return "HUGSIM_STRUCTURAL_BRIDGE_COVERAGE_COMPLETE"
    return "HUGSIM_STRUCTURAL_BRIDGE_COVERAGE_MIXED_COMPLETE"


def build_report(
    iter70_report_path: Path,
    iter96_report_path: Path,
    iter97_report_path: Path,
    iter98_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter70_report, problems70 = load_report(iter70_report_path, "iter70-report")
    iter96_report, problems96 = load_report(iter96_report_path, "iter96-report")
    iter97_report, problems97 = load_report(iter97_report_path, "iter97-report")
    iter98_report, problems98 = load_report(iter98_report_path, "iter98-report")
    infra_problems.extend(problems70 + problems96 + problems97 + problems98)
    rows70: list[dict[str, Any]] = []
    bridge_hits_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    if not infra_problems:
        infra_problems.extend(check_verdicts_and_infra(iter70_report, iter96_report, iter97_report, iter98_report))
        rows70 = check_iter70_rows(iter70_report, infra_problems)
        for report, source in (
            (iter96_report, "iter96_late_fire"),
            (iter97_report, "iter97_surface_silent"),
            (iter98_report, "iter98_background_only"),
        ):
            for hit in collect_bridge_events(report, source, infra_problems):
                bridge_hits_by_key[hit["key"]].append(hit)
    rows = [] if infra_problems else [analyze_row(row, bridge_hits_by_key[row_key(row)]) for row in rows70]
    label_counts = Counter(row.get("row_label") for row in rows)
    source_counts = Counter(
        source
        for row in rows
        for source in row.get("measurements", {}).get("bridge_sources", [])
    )
    return {
        "iteration": 99,
        "inputs": {
            "iter70_report": str(iter70_report_path),
            "iter96_report": str(iter96_report_path),
            "iter97_report": str(iter97_report_path),
            "iter98_report": str(iter98_report_path),
        },
        "fixed_rows": list(FIXED_ROWS),
        "infra_problems": infra_problems,
        "events": rows,
        "summary": {
            "target_rows": len(rows70),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "bridge_source_counts": dict(sorted(source_counts.items())),
            "covered_rows": sum(row.get("measurements", {}).get("covered_exactly_once") is True for row in rows),
            "compatible_rows": sum(row.get("measurements", {}).get("bridge_source_compatible") is True for row in rows),
            "uncovered_rows": sum(row.get("row_label") == "structural_bridge_uncovered" for row in rows),
            "duplicate_or_incompatible_rows": sum(
                row.get("row_label") == "structural_bridge_duplicate_or_incompatible" for row in rows
            ),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "five-row descriptive structural-bridge coverage audit only; no actor-causality, "
            "repair, threshold-value, transfer, safety, deployment, robustness, benchmark, "
            "population-rate, HD-Score-invariance, commercial-value, real-world behavior, "
            "first-responder behavior, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 99 - HUGSIM structural bridge coverage audit",
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
            "| audit id | scenario | structural label | bridge source | bridge label | coverage label | problems |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for row in report["events"]:
        measurements = row.get("measurements") or {}
        lines.append(
            f"| `{row['audit_id']}` | `{row['scenario']}` | "
            f"`{measurements.get('structural_label')}` | "
            f"`{measurements.get('bridge_sources')}` | "
            f"`{measurements.get('bridge_row_labels')}` | "
            f"`{row['row_label']}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter70_report: Path,
    iter96_report: Path,
    iter97_report: Path,
    iter98_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter70_report, iter96_report, iter97_report, iter98_report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iter70-report",
        type=Path,
        default=Path("experiments/iter70_hugsim_structural_timing_audit/proof-structural/structural_report.json"),
    )
    parser.add_argument(
        "--iter96-report",
        type=Path,
        default=Path("experiments/iter96_hugsim_branch_outcome_bridge/proof-outcome/branch_outcome_bridge_report.json"),
    )
    parser.add_argument(
        "--iter97-report",
        type=Path,
        default=Path(
            "experiments/iter97_hugsim_surface_silent_outcome_margin_bridge/proof-silent-outcome/"
            "surface_silent_outcome_margin_bridge_report.json"
        ),
    )
    parser.add_argument(
        "--iter98-report",
        type=Path,
        default=Path(
            "experiments/iter98_hugsim_background_only_outcome_bridge/proof-background-outcome/"
            "background_only_outcome_bridge_report.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter99_hugsim_structural_bridge_coverage_audit/proof-coverage/"
            "structural_bridge_coverage_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter99_hugsim_structural_bridge_coverage_audit/proof-coverage/"
            "structural_bridge_coverage.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter70_report,
        args.iter96_report,
        args.iter97_report,
        args.iter98_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
