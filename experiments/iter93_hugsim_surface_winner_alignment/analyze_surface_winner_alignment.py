#!/usr/bin/env python3
"""Iteration 93 HUGSIM surface-winner selector-alignment audit."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER92_VERDICT = "HUGSIM_PATH_PROXIMITY_ARBITRATION_SPLIT_COMPLETE"
EXPECTED_ITER92_LABELS = {
    "path_best_no_bridge_provenance_best_nonactive": 1,
    "path_best_bridge_supported_nonactive": 1,
    "path_best_active_no_bridge": 1,
}
FIXED_ROWS = (
    {
        "audit_id": "both_distinct_extreme",
        "scenario": "scene-0138-extreme-00",
        "role": "pre",
        "replay_ts": 5.5,
        "alignment": "exact_bridge_ts",
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "role": "pre",
        "replay_ts": 4.0,
        "alignment": "exact_bridge_ts",
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "role": "active",
        "replay_ts": 5.75,
        "alignment": "nearest_before_bridge_ts",
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


def event_index(rows: Any, problems: list[str]) -> dict[tuple[str, str, str], dict[str, Any]]:
    if not isinstance(rows, list):
        problems.append("iter92-events-not-list")
        return {}
    index: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            problems.append("iter92-event-not-dict")
            continue
        audit_id = row.get("audit_id")
        scenario = row.get("scenario")
        role = row.get("event_role")
        if not isinstance(audit_id, str) or not isinstance(scenario, str) or not isinstance(role, str):
            problems.append(f"iter92-event-key-missing:{row}")
            continue
        key = (audit_id, scenario, role)
        if key in index:
            problems.append(f"duplicate-iter92-event:{key}")
        index[key] = row
    return index


def candidate_object_id(candidate: Any, label: str, problems: list[str]) -> Any:
    if not isinstance(candidate, dict):
        problems.append(f"{label}-candidate-not-dict")
        return None
    object_id = candidate.get("object_id")
    if object_id is None:
        problems.append(f"{label}-object-id-missing")
    return object_id


def bridge_band(candidate: dict[str, Any] | None) -> Any:
    if not isinstance(candidate, dict):
        return None
    bridge = candidate.get("bridge_geometry")
    if not isinstance(bridge, dict):
        return None
    return bridge.get("distance_band")


def compact_selector(candidate: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(candidate, dict):
        return None
    return {
        "object_id": candidate.get("object_id"),
        "state": candidate.get("state"),
        "joint_class": candidate.get("joint_class"),
        "min_cpa": candidate.get("min_cpa"),
        "cpa_rank": candidate.get("cpa_rank"),
        "ttc": candidate.get("ttc"),
        "ttc_rank": candidate.get("ttc_rank"),
        "bridge_band": bridge_band(candidate),
        "bridge_best_distance_m": (
            candidate.get("bridge_geometry", {}).get("best_distance_m")
            if isinstance(candidate.get("bridge_geometry"), dict)
            else None
        ),
    }


def classify_row(
    surface: dict[str, Any] | None,
    path: dict[str, Any] | None,
    provenance: dict[str, Any] | None,
    surface_matches_path: bool,
    surface_matches_provenance: bool,
    path_matches_provenance: bool,
    problems: list[str],
) -> str:
    if problems or surface is None or path is None or provenance is None:
        return "surface_winner_alignment_insufficient"
    state = surface.get("state")
    if surface_matches_path and surface_matches_provenance and path_matches_provenance:
        if state == "active":
            return "surface_path_provenance_same_active"
        return "surface_path_provenance_same_nonactive"
    if surface_matches_path and not surface_matches_provenance:
        if state == "active" and bridge_band(surface) not in {"match", "ambiguous"}:
            return "surface_follows_path_active_no_bridge"
        return "surface_follows_path_nonactive"
    if surface_matches_provenance and not surface_matches_path and state != "active":
        return "surface_follows_provenance_nonactive"
    return "surface_winner_alignment_insufficient"


def crosscheck_sources(iter92_report: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    if iter92_report.get("verdict") != ITER92_VERDICT:
        problems.append(f"iter92-verdict-not-{ITER92_VERDICT}")
    if iter92_report.get("infra_problems"):
        problems.append(f"iter92-infra-problems:{iter92_report.get('infra_problems')}")
    summary = iter92_report.get("summary") or {}
    if int(summary.get("path_provenance_same_object_events", -1)) != 0:
        problems.append("iter92-path-provenance-same-object-events-not-zero")
    label_counts = Counter(row.get("row_label") for row in iter92_report.get("events", []))
    if dict(label_counts) != EXPECTED_ITER92_LABELS:
        problems.append(f"iter92-label-counts-mismatch:{dict(label_counts)}")

    iter92_index = event_index(iter92_report.get("events"), problems)
    if len(iter92_index) != len(FIXED_ROWS):
        problems.append(f"iter92-event-count-mismatch:{len(iter92_index)}")

    selected: list[dict[str, Any]] = []
    for target in FIXED_ROWS:
        key = (target["audit_id"], target["scenario"], target["role"])
        row92 = iter92_index.get(key)
        if row92 is None:
            problems.append(f"missing-iter92-event:{key}")
            continue
        if row92.get("problems"):
            problems.append(f"iter92-event-problems:{key}:{row92.get('problems')}")
        replay_ts = row92.get("replay_ts")
        if finite_number(replay_ts) and not math.isclose(float(replay_ts), float(target["replay_ts"]), abs_tol=1e-6):
            problems.append(f"iter92-replay-ts-mismatch:{key}:{replay_ts}")
        if not finite_number(replay_ts):
            problems.append(f"iter92-replay-ts-missing:{key}")
        if row92.get("replay_alignment") != target["alignment"]:
            problems.append(f"iter92-alignment-mismatch:{key}:{row92.get('replay_alignment')}")
        selected.append({"target": target, "iter92": row92})
    if len(selected) != len(FIXED_ROWS):
        problems.append(f"fixed-row-count-mismatch:{len(selected)}")
    return selected, problems


def analyze_target(item: dict[str, Any]) -> dict[str, Any]:
    target = item["target"]
    row92 = item["iter92"]
    problems: list[str] = []
    path = row92.get("path_best")
    provenance = row92.get("provenance_best")
    surface = row92.get("surface_best")
    path_id = candidate_object_id(path, "path-best", problems)
    provenance_id = candidate_object_id(provenance, "provenance-best", problems)
    surface_id = candidate_object_id(surface, "surface-best", problems)
    surface_matches_path = surface_id is not None and path_id is not None and same_object_id(surface_id, path_id)
    surface_matches_provenance = (
        surface_id is not None and provenance_id is not None and same_object_id(surface_id, provenance_id)
    )
    path_matches_provenance = path_id is not None and provenance_id is not None and same_object_id(path_id, provenance_id)
    label = classify_row(
        surface if isinstance(surface, dict) else None,
        path if isinstance(path, dict) else None,
        provenance if isinstance(provenance, dict) else None,
        surface_matches_path,
        surface_matches_provenance,
        path_matches_provenance,
        problems,
    )
    return {
        "audit_id": target["audit_id"],
        "scenario": target["scenario"],
        "event_role": target["role"],
        "replay_ts": target["replay_ts"],
        "replay_alignment": target["alignment"],
        "path_best": compact_selector(path if isinstance(path, dict) else None),
        "provenance_best": compact_selector(provenance if isinstance(provenance, dict) else None),
        "surface_best": compact_selector(surface if isinstance(surface, dict) else None),
        "surface_matches_path": surface_matches_path,
        "surface_matches_provenance": surface_matches_provenance,
        "path_matches_provenance": path_matches_provenance,
        "row_label": label,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_ROWS)
        or any(row.get("problems") for row in rows)
        or "surface_winner_alignment_insufficient" in labels
    ):
        return "HUGSIM_SURFACE_WINNER_ALIGNMENT_BLOCKED"
    if "surface_path_provenance_same_active" in labels:
        return "HUGSIM_SURFACE_WINNER_ALIGNMENT_ACTIVE_COINCIDENT_COMPLETE"
    path_labels = {"surface_follows_path_active_no_bridge", "surface_follows_path_nonactive"}
    provenance_labels = {"surface_follows_provenance_nonactive"}
    if all(label in path_labels for label in labels):
        return "HUGSIM_SURFACE_WINNER_ALIGNMENT_PATH_ONLY_COMPLETE"
    if all(label in provenance_labels for label in labels):
        return "HUGSIM_SURFACE_WINNER_ALIGNMENT_PROVENANCE_ONLY_COMPLETE"
    if any(label in path_labels for label in labels) and any(label in provenance_labels for label in labels):
        return "HUGSIM_SURFACE_WINNER_ALIGNMENT_MIXED_COMPLETE"
    return "HUGSIM_SURFACE_WINNER_ALIGNMENT_BLOCKED"


def build_report(iter92_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter92_report, problems92 = load_report(iter92_report_path, "iter92-report")
    infra_problems.extend(problems92)
    selected: list[dict[str, Any]] = []
    if not infra_problems:
        selected, source_problems = crosscheck_sources(iter92_report)
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_target(item) for item in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    return {
        "iteration": 93,
        "inputs": {"iter92_report": str(iter92_report_path)},
        "fixed_rows": list(FIXED_ROWS),
        "infra_problems": infra_problems,
        "events": rows,
        "summary": {
            "target_rows": len(selected),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "surface_matches_path_events": sum(row.get("surface_matches_path") is True for row in rows),
            "surface_matches_provenance_events": sum(row.get("surface_matches_provenance") is True for row in rows),
            "path_matches_provenance_events": sum(row.get("path_matches_provenance") is True for row in rows),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "three-row descriptive selector-alignment audit only; no actor-causality, repair, "
            "threshold-value, transfer, safety, deployment, robustness, benchmark, population, "
            "HD-Score-invariance, commercial-value, real-world behavior, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 93 - HUGSIM surface-winner alignment audit",
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
    lines.extend([
        "",
        "## Events",
        "",
        "| audit id | event | surface best | surface state | surface bridge | matches path | matches provenance | label | problems |",
        "|---|---|---:|---|---|---|---|---|---|",
    ])
    for row in report["events"]:
        surface = row.get("surface_best") or {}
        lines.append(
            f"| `{row['audit_id']}` | `{row['event_role']}` | `{surface.get('object_id')}` | "
            f"`{surface.get('state')}` | `{surface.get('bridge_band')}` | "
            f"`{row.get('surface_matches_path')}` | `{row.get('surface_matches_provenance')}` | "
            f"`{row['row_label']}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(iter92_report: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(iter92_report)
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
        "--out",
        type=Path,
        default=Path(
            "experiments/iter93_hugsim_surface_winner_alignment/proof-alignment/"
            "surface_winner_alignment_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter93_hugsim_surface_winner_alignment/proof-alignment/"
            "surface_winner_alignment.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter92_report, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
