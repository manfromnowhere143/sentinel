#!/usr/bin/env python3
"""Iteration 95 HUGSIM non-active surface branch arbitration."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER92_VERDICT = "HUGSIM_PATH_PROXIMITY_ARBITRATION_SPLIT_COMPLETE"
ITER93_VERDICT = "HUGSIM_SURFACE_WINNER_ALIGNMENT_MIXED_COMPLETE"
ITER94_VERDICT = "HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_ARBITRATION_COMPLETE"

FIXED_ROWS = (
    {
        "audit_id": "both_distinct_extreme",
        "scenario": "scene-0138-extreme-00",
        "event_role": "pre",
        "replay_alignment": "exact_bridge_ts",
        "replay_ts": 5.5,
        "iter92_label": "path_best_no_bridge_provenance_best_nonactive",
        "iter93_label": "surface_follows_provenance_nonactive",
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "event_role": "pre",
        "replay_alignment": "exact_bridge_ts",
        "replay_ts": 4.0,
        "iter92_label": "path_best_bridge_supported_nonactive",
        "iter93_label": "surface_follows_path_nonactive",
    },
)


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def same_object_id(left: Any, right: Any) -> bool:
    return str(left) == str(right)


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


def row_key(row: dict[str, Any]) -> tuple[Any, Any, Any]:
    return (row.get("audit_id"), row.get("scenario"), row.get("event_role"))


def event_index(rows: Any, label: str, problems: list[str]) -> dict[tuple[str, str, str], dict[str, Any]]:
    if not isinstance(rows, list):
        problems.append(f"{label}-events-not-list")
        return {}
    index: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            problems.append(f"{label}-event-not-dict")
            continue
        audit_id, scenario, event_role = row_key(row)
        if not isinstance(audit_id, str) or not isinstance(scenario, str) or not isinstance(event_role, str):
            problems.append(f"{label}-event-key-missing:{row}")
            continue
        key = (audit_id, scenario, event_role)
        if key in index:
            problems.append(f"{label}-duplicate-event:{key}")
        index[key] = row
    return index


def bridge_band(candidate: dict[str, Any] | None) -> Any:
    if not isinstance(candidate, dict):
        return None
    direct = candidate.get("bridge_band")
    if direct is not None:
        return direct
    bridge = candidate.get("bridge_geometry")
    if isinstance(bridge, dict):
        return bridge.get("distance_band")
    return None


def bridge_distance(candidate: dict[str, Any] | None) -> Any:
    if not isinstance(candidate, dict):
        return None
    direct = candidate.get("bridge_best_distance_m")
    if direct is not None:
        return direct
    bridge = candidate.get("bridge_geometry")
    if isinstance(bridge, dict):
        return bridge.get("best_distance_m")
    return None


def compact_candidate(candidate: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(candidate, dict):
        return None
    return {
        "object_id": candidate.get("object_id"),
        "state": candidate.get("state"),
        "joint_class": candidate.get("joint_class"),
        "bridge_band": bridge_band(candidate),
        "bridge_best_distance_m": bridge_distance(candidate),
        "min_cpa": candidate.get("min_cpa"),
        "cpa_rank": candidate.get("cpa_rank"),
        "ttc": candidate.get("ttc"),
        "ttc_rank": candidate.get("ttc_rank"),
        "active_cpa_margin_m": candidate.get("active_cpa_margin_m"),
        "active_ttc_margin_s": candidate.get("active_ttc_margin_s"),
    }


def validate_candidate(candidate: dict[str, Any] | None, label: str, problems: list[str]) -> None:
    if not isinstance(candidate, dict):
        problems.append(f"{label}-not-dict")
        return
    if candidate.get("object_id") is None:
        problems.append(f"{label}-object-id-missing")
    if not isinstance(candidate.get("state"), str):
        problems.append(f"{label}-state-missing")
    if not isinstance(bridge_band(candidate), str):
        problems.append(f"{label}-bridge-band-missing")
    for field in ("min_cpa", "cpa_rank", "active_cpa_margin_m"):
        if not finite_number(candidate.get(field)):
            problems.append(f"{label}-{field}-not-finite:{candidate.get(field)}")
    for field in ("ttc", "active_ttc_margin_s"):
        value = candidate.get(field)
        if value is not None and not finite_number(value):
            problems.append(f"{label}-{field}-malformed:{value}")


def finite_ttc(candidate: dict[str, Any]) -> bool:
    return finite_number(candidate.get("ttc"))


def closer_bridge(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_distance = bridge_distance(left)
    right_distance = bridge_distance(right)
    return finite_number(left_distance) and finite_number(right_distance) and float(left_distance) < float(right_distance)


def lower_cpa(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return finite_number(left.get("min_cpa")) and finite_number(right.get("min_cpa")) and float(left["min_cpa"]) < float(right["min_cpa"])


def better_cpa_rank(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return finite_number(left.get("cpa_rank")) and finite_number(right.get("cpa_rank")) and float(left["cpa_rank"]) < float(right["cpa_rank"])


def crosscheck_sources(
    iter92_report: dict[str, Any],
    iter93_report: dict[str, Any],
    iter94_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    if iter92_report.get("verdict") != ITER92_VERDICT:
        problems.append(f"iter92-verdict-not-{ITER92_VERDICT}")
    if iter93_report.get("verdict") != ITER93_VERDICT:
        problems.append(f"iter93-verdict-not-{ITER93_VERDICT}")
    if iter94_report.get("verdict") != ITER94_VERDICT:
        problems.append(f"iter94-verdict-not-{ITER94_VERDICT}")
    for label, report in (("iter92", iter92_report), ("iter93", iter93_report), ("iter94", iter94_report)):
        if report.get("infra_problems"):
            problems.append(f"{label}-infra-problems:{report.get('infra_problems')}")

    iter92_index = event_index(iter92_report.get("events"), "iter92", problems)
    iter93_index = event_index(iter93_report.get("events"), "iter93", problems)
    selected: list[dict[str, Any]] = []
    for target in FIXED_ROWS:
        key = (target["audit_id"], target["scenario"], target["event_role"])
        row92 = iter92_index.get(key)
        row93 = iter93_index.get(key)
        if row92 is None:
            problems.append(f"missing-iter92-row:{key}")
            continue
        if row93 is None:
            problems.append(f"missing-iter93-row:{key}")
            continue
        for label, row in (("iter92", row92), ("iter93", row93)):
            replay_ts = row.get("replay_ts")
            if not finite_number(replay_ts) or not math.isclose(float(replay_ts), float(target["replay_ts"]), abs_tol=1e-6):
                problems.append(f"{label}-replay-ts-mismatch:{key}:{replay_ts}")
            if row.get("replay_alignment") != target["replay_alignment"]:
                problems.append(f"{label}-replay-alignment-mismatch:{key}:{row.get('replay_alignment')}")
            if row.get("problems"):
                problems.append(f"{label}-row-problems:{key}:{row.get('problems')}")
        if row92.get("row_label") != target["iter92_label"]:
            problems.append(f"iter92-label-mismatch:{key}:{row92.get('row_label')}")
        if row93.get("row_label") != target["iter93_label"]:
            problems.append(f"iter93-label-mismatch:{key}:{row93.get('row_label')}")
        selected.append({"target": target, "iter92": row92, "iter93": row93})
    if len(selected) != len(FIXED_ROWS):
        problems.append(f"fixed-row-count-mismatch:{len(selected)}")
    return selected, problems


def classify_row(measurements: dict[str, Any], path: dict[str, Any], provenance: dict[str, Any], problems: list[str]) -> str:
    if problems:
        return "nonactive_surface_branch_insufficient"
    if (
        measurements["surface_matches_provenance"]
        and not measurements["surface_matches_path"]
        and provenance.get("state") == "borderline"
        and finite_ttc(provenance)
        and not finite_ttc(path)
        and (measurements["path_lower_cpa_than_provenance"] or measurements["path_better_cpa_rank_than_provenance"])
        and measurements["provenance_closer_bridge_than_path"]
    ):
        return "nonactive_surface_provenance_ttc_borderline_over_path_cpa"
    if (
        measurements["surface_matches_path"]
        and not measurements["surface_matches_provenance"]
        and path.get("state") == "subthreshold"
        and provenance.get("state") == "subthreshold"
        and not finite_ttc(path)
        and not finite_ttc(provenance)
        and measurements["path_lower_cpa_than_provenance"]
        and measurements["path_better_cpa_rank_than_provenance"]
        and measurements["provenance_closer_bridge_than_path"]
    ):
        return "nonactive_surface_path_cpa_over_provenance_bridge"
    return "nonactive_surface_branch_mixed_other"


def analyze_target(item: dict[str, Any]) -> dict[str, Any]:
    target = item["target"]
    row92 = item["iter92"]
    row93 = item["iter93"]
    problems: list[str] = []
    path = row92.get("path_best")
    provenance = row92.get("provenance_best")
    surface = row92.get("surface_best")
    for label, candidate in (("path-best", path), ("provenance-best", provenance), ("surface-best", surface)):
        validate_candidate(candidate if isinstance(candidate, dict) else None, label, problems)
    if not isinstance(path, dict) or not isinstance(provenance, dict) or not isinstance(surface, dict):
        path, provenance, surface = {}, {}, {}

    row93_surface = row93.get("surface_best")
    if not isinstance(row93_surface, dict):
        problems.append("iter93-surface-best-not-dict")
    elif not same_object_id(surface.get("object_id"), row93_surface.get("object_id")):
        problems.append(f"iter92-iter93-surface-object-mismatch:{surface.get('object_id')}:{row93_surface.get('object_id')}")

    surface_matches_path = same_object_id(surface.get("object_id"), path.get("object_id"))
    surface_matches_provenance = same_object_id(surface.get("object_id"), provenance.get("object_id"))
    if row93.get("surface_matches_path") is not surface_matches_path:
        problems.append(f"iter93-surface-matches-path-mismatch:{row93.get('surface_matches_path')}:{surface_matches_path}")
    if row93.get("surface_matches_provenance") is not surface_matches_provenance:
        problems.append(
            f"iter93-surface-matches-provenance-mismatch:{row93.get('surface_matches_provenance')}:{surface_matches_provenance}"
        )

    measurements = {
        "surface_matches_path": surface_matches_path,
        "surface_matches_provenance": surface_matches_provenance,
        "path_has_finite_ttc": finite_ttc(path),
        "provenance_has_finite_ttc": finite_ttc(provenance),
        "path_lower_cpa_than_provenance": lower_cpa(path, provenance),
        "path_better_cpa_rank_than_provenance": better_cpa_rank(path, provenance),
        "provenance_closer_bridge_than_path": closer_bridge(provenance, path),
        "path_bridge_distance_m": bridge_distance(path),
        "provenance_bridge_distance_m": bridge_distance(provenance),
        "path_min_cpa": path.get("min_cpa"),
        "provenance_min_cpa": provenance.get("min_cpa"),
        "path_cpa_rank": path.get("cpa_rank"),
        "provenance_cpa_rank": provenance.get("cpa_rank"),
    }
    label = classify_row(measurements, path, provenance, problems)
    return {
        "audit_id": target["audit_id"],
        "scenario": target["scenario"],
        "event_role": target["event_role"],
        "replay_alignment": target["replay_alignment"],
        "replay_ts": target["replay_ts"],
        "path_best": compact_candidate(path),
        "provenance_best": compact_candidate(provenance),
        "surface_best": compact_candidate(surface),
        "measurements": measurements,
        "row_label": label,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_ROWS)
        or any(row.get("problems") for row in rows)
        or "nonactive_surface_branch_insufficient" in labels
    ):
        return "HUGSIM_NONACTIVE_SURFACE_BRANCH_BLOCKED"
    provenance_label = "nonactive_surface_provenance_ttc_borderline_over_path_cpa"
    path_label = "nonactive_surface_path_cpa_over_provenance_bridge"
    if labels.count(provenance_label) == 1 and labels.count(path_label) == 1:
        return "HUGSIM_NONACTIVE_SURFACE_BRANCH_ARBITRATION_SPLIT_COMPLETE"
    if all(label == provenance_label for label in labels):
        return "HUGSIM_NONACTIVE_SURFACE_BRANCH_PROVENANCE_ONLY_COMPLETE"
    if all(label == path_label for label in labels):
        return "HUGSIM_NONACTIVE_SURFACE_BRANCH_PATH_ONLY_COMPLETE"
    return "HUGSIM_NONACTIVE_SURFACE_BRANCH_MIXED_OTHER_COMPLETE"


def build_report(iter92_report_path: Path, iter93_report_path: Path, iter94_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter92_report, problems92 = load_report(iter92_report_path, "iter92-report")
    iter93_report, problems93 = load_report(iter93_report_path, "iter93-report")
    iter94_report, problems94 = load_report(iter94_report_path, "iter94-report")
    infra_problems.extend(problems92 + problems93 + problems94)
    selected: list[dict[str, Any]] = []
    if not infra_problems:
        selected, source_problems = crosscheck_sources(iter92_report, iter93_report, iter94_report)
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_target(item) for item in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    return {
        "iteration": 95,
        "inputs": {
            "iter92_report": str(iter92_report_path),
            "iter93_report": str(iter93_report_path),
            "iter94_report": str(iter94_report_path),
        },
        "fixed_rows": list(FIXED_ROWS),
        "infra_problems": infra_problems,
        "events": rows,
        "summary": {
            "target_rows": len(selected),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "surface_matches_path_events": sum(row.get("measurements", {}).get("surface_matches_path") is True for row in rows),
            "surface_matches_provenance_events": sum(
                row.get("measurements", {}).get("surface_matches_provenance") is True for row in rows
            ),
            "provenance_finite_ttc_events": sum(
                row.get("measurements", {}).get("provenance_has_finite_ttc") is True for row in rows
            ),
            "path_cpa_rank_better_events": sum(
                row.get("measurements", {}).get("path_better_cpa_rank_than_provenance") is True for row in rows
            ),
            "provenance_closer_bridge_events": sum(
                row.get("measurements", {}).get("provenance_closer_bridge_than_path") is True for row in rows
            ),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "two-row descriptive non-active surface branch arbitration only; no actor-causality, "
            "repair, threshold-value, transfer, safety, deployment, robustness, benchmark, "
            "population-rate, HD-Score-invariance, commercial-value, real-world behavior, "
            "first-responder behavior, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 95 - HUGSIM non-active surface branch arbitration",
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
            "| audit id | event | surface object | matches path | matches provenance | path CPA rank | provenance TTC | label | problems |",
            "|---|---|---:|---|---|---:|---|---|---|",
        ]
    )
    for row in report["events"]:
        measurements = row.get("measurements") or {}
        surface = row.get("surface_best") or {}
        provenance = row.get("provenance_best") or {}
        lines.append(
            f"| `{row['audit_id']}` | `{row['event_role']}` | `{surface.get('object_id')}` | "
            f"`{measurements.get('surface_matches_path')}` | `{measurements.get('surface_matches_provenance')}` | "
            f"`{measurements.get('path_cpa_rank')}` | `{provenance.get('ttc')}` | `{row['row_label']}` | "
            f"`{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(iter92_report: Path, iter93_report: Path, iter94_report: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(iter92_report, iter93_report, iter94_report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iter92-report",
        type=Path,
        default=Path(
            "experiments/iter92_hugsim_path_proximity_arbitration/proof-arbitration/"
            "path_proximity_arbitration_report.json"
        ),
    )
    parser.add_argument(
        "--iter93-report",
        type=Path,
        default=Path(
            "experiments/iter93_hugsim_surface_winner_alignment/proof-alignment/"
            "surface_winner_alignment_report.json"
        ),
    )
    parser.add_argument(
        "--iter94-report",
        type=Path,
        default=Path(
            "experiments/iter94_hugsim_active_row_surface_margin_arbitration/proof-margin/"
            "active_row_surface_margin_arbitration_report.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter95_hugsim_nonactive_surface_branch_arbitration/proof-branch/"
            "nonactive_surface_branch_arbitration_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter95_hugsim_nonactive_surface_branch_arbitration/proof-branch/"
            "nonactive_surface_branch_arbitration.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter92_report, args.iter93_report, args.iter94_report, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
