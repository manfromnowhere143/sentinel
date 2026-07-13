#!/usr/bin/env python3
"""Iteration 94 HUGSIM active-row surface margin arbitration."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER91_VERDICT = "HUGSIM_ACTIVE_GAP_PATH_PROVENANCE_DECOMPOSITION_COMPLETE"
ITER92_VERDICT = "HUGSIM_PATH_PROXIMITY_ARBITRATION_SPLIT_COMPLETE"
ITER93_VERDICT = "HUGSIM_SURFACE_WINNER_ALIGNMENT_MIXED_COMPLETE"

FIXED_ROW = {
    "audit_id": "ttc_medium_a",
    "scenario": "scene-0071-medium-01",
    "event_role": "active",
    "replay_alignment": "nearest_before_bridge_ts",
    "replay_ts": 5.75,
}


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


def expected_key() -> tuple[str, str, str]:
    return (FIXED_ROW["audit_id"], FIXED_ROW["scenario"], FIXED_ROW["event_role"])


def find_fixed_row(report: dict[str, Any], label: str, problems: list[str]) -> dict[str, Any] | None:
    events = report.get("events")
    if not isinstance(events, list):
        problems.append(f"{label}-events-not-list")
        return None
    matches = [row for row in events if isinstance(row, dict) and row_key(row) == expected_key()]
    if len(matches) != 1:
        problems.append(f"{label}-fixed-row-count:{len(matches)}")
        return None
    row = matches[0]
    replay_ts = row.get("replay_ts")
    if not finite_number(replay_ts) or not math.isclose(float(replay_ts), float(FIXED_ROW["replay_ts"]), abs_tol=1e-6):
        problems.append(f"{label}-replay-ts-mismatch:{replay_ts}")
    if row.get("replay_alignment") != FIXED_ROW["replay_alignment"]:
        problems.append(f"{label}-replay-alignment-mismatch:{row.get('replay_alignment')}")
    if row.get("problems"):
        problems.append(f"{label}-row-problems:{row.get('problems')}")
    return row


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
    ttc = candidate.get("ttc")
    if ttc is not None and not finite_number(ttc):
        problems.append(f"{label}-ttc-malformed:{ttc}")


def finite_ttc(candidate: dict[str, Any]) -> bool:
    return finite_number(candidate.get("ttc"))


def source_checks(
    iter91_report: dict[str, Any],
    iter92_report: dict[str, Any],
    iter93_report: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    problems: list[str] = []
    if iter91_report.get("verdict") != ITER91_VERDICT:
        problems.append(f"iter91-verdict-not-{ITER91_VERDICT}")
    if iter92_report.get("verdict") != ITER92_VERDICT:
        problems.append(f"iter92-verdict-not-{ITER92_VERDICT}")
    if iter93_report.get("verdict") != ITER93_VERDICT:
        problems.append(f"iter93-verdict-not-{ITER93_VERDICT}")
    for label, report in (("iter91", iter91_report), ("iter92", iter92_report), ("iter93", iter93_report)):
        if report.get("infra_problems"):
            problems.append(f"{label}-infra-problems:{report.get('infra_problems')}")

    row91 = find_fixed_row(iter91_report, "iter91", problems)
    row92 = find_fixed_row(iter92_report, "iter92", problems)
    row93 = find_fixed_row(iter93_report, "iter93", problems)
    if row91 is not None and row91.get("row_label") != "path_active_provenance_far_with_bridge_nonactive":
        problems.append(f"iter91-row-label-mismatch:{row91.get('row_label')}")
    if row92 is not None and row92.get("row_label") != "path_best_active_no_bridge":
        problems.append(f"iter92-row-label-mismatch:{row92.get('row_label')}")
    if row93 is not None and row93.get("row_label") != "surface_follows_path_active_no_bridge":
        problems.append(f"iter93-row-label-mismatch:{row93.get('row_label')}")
    if row93 is not None and row93.get("surface_matches_path") is not True:
        problems.append(f"iter93-surface-matches-path-not-true:{row93.get('surface_matches_path')}")
    if row93 is not None and row93.get("surface_matches_provenance") is not False:
        problems.append(f"iter93-surface-matches-provenance-not-false:{row93.get('surface_matches_provenance')}")

    if row91 is not None and row92 is not None and row93 is not None:
        active_candidates = row91.get("active_candidates")
        if not isinstance(active_candidates, list) or len(active_candidates) != 1:
            problems.append(
                f"iter91-active-candidate-count:{len(active_candidates) if isinstance(active_candidates, list) else 'not-list'}"
            )
        else:
            active_object = active_candidates[0].get("object_id") if isinstance(active_candidates[0], dict) else None
            path_object = (row92.get("path_best") or {}).get("object_id") if isinstance(row92.get("path_best"), dict) else None
            surface_object = (
                (row93.get("surface_best") or {}).get("object_id")
                if isinstance(row93.get("surface_best"), dict)
                else None
            )
            if not same_object_id(active_object, path_object) or not same_object_id(active_object, surface_object):
                problems.append(
                    "active-path-surface-object-mismatch:"
                    f"active={active_object}:path={path_object}:surface={surface_object}"
                )
    return row91, row92, row93, problems


def classify_measurements(measurements: dict[str, Any], problems: list[str]) -> str:
    if problems:
        return "active_row_surface_margin_insufficient"
    if measurements["bridge_surface_near"]:
        return "active_row_bridge_candidate_surface_near"
    if (
        measurements["active_candidate_count"] == 1
        and measurements["active_same_as_path_and_surface"]
        and measurements["active_state"] == "active"
        and measurements["active_bridge_band"] == "no_support"
        and measurements["active_cpa_margin_negative"]
        and measurements["bridge_supported_count"] > 0
        and measurements["bridge_all_nonactive"]
        and measurements["bridge_all_positive_active_cpa_margin"]
        and measurements["bridge_all_no_finite_ttc"]
        and measurements["active_lower_cpa_than_all_bridge"]
        and measurements["active_better_cpa_rank_than_all_bridge"]
    ):
        return "active_row_cpa_margin_overrides_provenance"
    return "active_row_surface_margin_mixed"


def analyze_row(row91: dict[str, Any], row92: dict[str, Any], row93: dict[str, Any]) -> dict[str, Any]:
    problems: list[str] = []
    active_candidates = row91.get("active_candidates")
    bridge_candidates = row91.get("bridge_supported_candidates")
    if not isinstance(active_candidates, list):
        problems.append("iter91-active-candidates-not-list")
        active_candidates = []
    if not isinstance(bridge_candidates, list):
        problems.append("iter91-bridge-supported-candidates-not-list")
        bridge_candidates = []

    for index, candidate in enumerate(active_candidates):
        validate_candidate(candidate if isinstance(candidate, dict) else None, f"active-candidate-{index}", problems)
    for index, candidate in enumerate(bridge_candidates):
        validate_candidate(candidate if isinstance(candidate, dict) else None, f"bridge-candidate-{index}", problems)

    active = active_candidates[0] if len(active_candidates) == 1 and isinstance(active_candidates[0], dict) else None
    compact_active = compact_candidate(active)
    compact_bridge = [
        compact_candidate(candidate if isinstance(candidate, dict) else None)
        for candidate in bridge_candidates
        if isinstance(candidate, dict)
    ]
    if len(active_candidates) != int(row91.get("active_object_count", len(active_candidates))):
        problems.append(f"iter91-active-count-mismatch:{row91.get('active_object_count')}:{len(active_candidates)}")
    if len(bridge_candidates) != int(row91.get("bridge_supported_count", len(bridge_candidates))):
        problems.append(f"iter91-bridge-count-mismatch:{row91.get('bridge_supported_count')}:{len(bridge_candidates)}")

    path_object = (row92.get("path_best") or {}).get("object_id") if isinstance(row92.get("path_best"), dict) else None
    surface_object = (row93.get("surface_best") or {}).get("object_id") if isinstance(row93.get("surface_best"), dict) else None
    active_object = active.get("object_id") if active is not None else None

    bridge_dicts = [candidate for candidate in bridge_candidates if isinstance(candidate, dict)]
    bridge_margins = [
        (candidate.get("active_cpa_margin_m"), candidate.get("object_id"))
        for candidate in bridge_dicts
        if finite_number(candidate.get("active_cpa_margin_m"))
    ]
    min_bridge_margin, min_bridge_margin_object = (None, None)
    if bridge_margins:
        min_bridge_margin, min_bridge_margin_object = min((float(margin), object_id) for margin, object_id in bridge_margins)

    active_min_cpa = active.get("min_cpa") if active is not None else None
    active_cpa_rank = active.get("cpa_rank") if active is not None else None
    active_cpa_margin = active.get("active_cpa_margin_m") if active is not None else None
    bridge_all_nonactive = all(candidate.get("state") not in {"active", "borderline"} for candidate in bridge_dicts)
    bridge_active_or_borderline_count = sum(candidate.get("state") in {"active", "borderline"} for candidate in bridge_dicts)
    bridge_finite_ttc_count = sum(finite_ttc(candidate) for candidate in bridge_dicts)
    bridge_nonpositive_margin_count = sum(
        finite_number(candidate.get("active_cpa_margin_m")) and float(candidate["active_cpa_margin_m"]) <= 0
        for candidate in bridge_dicts
    )
    active_lower_cpa = bool(
        finite_number(active_min_cpa)
        and bridge_dicts
        and all(finite_number(candidate.get("min_cpa")) and float(active_min_cpa) < float(candidate["min_cpa"]) for candidate in bridge_dicts)
    )
    active_better_rank = bool(
        finite_number(active_cpa_rank)
        and bridge_dicts
        and all(
            finite_number(candidate.get("cpa_rank")) and float(active_cpa_rank) < float(candidate["cpa_rank"])
            for candidate in bridge_dicts
        )
    )

    measurements = {
        "active_candidate_count": len(active_candidates),
        "bridge_supported_count": len(bridge_candidates),
        "active_object_id": active_object,
        "path_best_object_id": path_object,
        "surface_best_object_id": surface_object,
        "active_same_as_path_and_surface": (
            active_object is not None
            and path_object is not None
            and surface_object is not None
            and same_object_id(active_object, path_object)
            and same_object_id(active_object, surface_object)
        ),
        "active_state": active.get("state") if active is not None else None,
        "active_bridge_band": bridge_band(active),
        "active_min_cpa": active_min_cpa,
        "active_cpa_rank": active_cpa_rank,
        "active_ttc": active.get("ttc") if active is not None else None,
        "active_cpa_margin_m": active_cpa_margin,
        "active_cpa_margin_negative": finite_number(active_cpa_margin) and float(active_cpa_margin) < 0,
        "min_bridge_active_cpa_margin_m": min_bridge_margin,
        "min_bridge_active_cpa_margin_object_id": min_bridge_margin_object,
        "bridge_active_or_borderline_count": bridge_active_or_borderline_count,
        "bridge_finite_ttc_count": bridge_finite_ttc_count,
        "bridge_nonpositive_active_cpa_margin_count": bridge_nonpositive_margin_count,
        "bridge_all_nonactive": bridge_all_nonactive,
        "bridge_all_positive_active_cpa_margin": bool(
            bridge_dicts
            and all(
                finite_number(candidate.get("active_cpa_margin_m"))
                and float(candidate["active_cpa_margin_m"]) > 0
                for candidate in bridge_dicts
            )
        ),
        "bridge_all_no_finite_ttc": bool(bridge_dicts and bridge_finite_ttc_count == 0),
        "bridge_surface_near": bridge_active_or_borderline_count > 0
        or bridge_nonpositive_margin_count > 0
        or bridge_finite_ttc_count > 0,
        "active_lower_cpa_than_all_bridge": active_lower_cpa,
        "active_better_cpa_rank_than_all_bridge": active_better_rank,
    }
    label = classify_measurements(measurements, problems)
    return {
        "audit_id": FIXED_ROW["audit_id"],
        "scenario": FIXED_ROW["scenario"],
        "event_role": FIXED_ROW["event_role"],
        "replay_alignment": FIXED_ROW["replay_alignment"],
        "replay_ts": FIXED_ROW["replay_ts"],
        "active_candidate": compact_active,
        "bridge_supported_candidates": compact_bridge,
        "measurements": measurements,
        "row_label": label,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    if infra_problems or len(rows) != 1 or any(row.get("problems") for row in rows):
        return "HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_BLOCKED"
    label = rows[0].get("row_label")
    if label == "active_row_cpa_margin_overrides_provenance":
        return "HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_ARBITRATION_COMPLETE"
    if label == "active_row_bridge_candidate_surface_near":
        return "HUGSIM_ACTIVE_ROW_BRIDGE_CANDIDATE_SURFACE_NEAR_COMPLETE"
    if label == "active_row_surface_margin_mixed":
        return "HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_MIXED_COMPLETE"
    return "HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_BLOCKED"


def build_report(iter91_report_path: Path, iter92_report_path: Path, iter93_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter91_report, problems91 = load_report(iter91_report_path, "iter91-report")
    iter92_report, problems92 = load_report(iter92_report_path, "iter92-report")
    iter93_report, problems93 = load_report(iter93_report_path, "iter93-report")
    infra_problems.extend(problems91 + problems92 + problems93)
    rows: list[dict[str, Any]] = []
    if not infra_problems:
        row91, row92, row93, source_problems = source_checks(iter91_report, iter92_report, iter93_report)
        infra_problems.extend(source_problems)
        if not infra_problems and row91 is not None and row92 is not None and row93 is not None:
            rows = [analyze_row(row91, row92, row93)]
    label_counts = Counter(row.get("row_label") for row in rows)
    measurements = rows[0].get("measurements", {}) if rows else {}
    return {
        "iteration": 94,
        "inputs": {
            "iter91_report": str(iter91_report_path),
            "iter92_report": str(iter92_report_path),
            "iter93_report": str(iter93_report_path),
        },
        "fixed_row": dict(FIXED_ROW),
        "infra_problems": infra_problems,
        "events": rows,
        "summary": {
            "target_rows": 1 if not infra_problems else 0,
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "active_candidate_count": measurements.get("active_candidate_count", 0),
            "bridge_supported_count": measurements.get("bridge_supported_count", 0),
            "bridge_active_or_borderline_count": measurements.get("bridge_active_or_borderline_count", 0),
            "bridge_finite_ttc_count": measurements.get("bridge_finite_ttc_count", 0),
            "bridge_nonpositive_active_cpa_margin_count": measurements.get(
                "bridge_nonpositive_active_cpa_margin_count",
                0,
            ),
            "active_object_id": measurements.get("active_object_id"),
            "active_cpa_margin_m": measurements.get("active_cpa_margin_m"),
            "min_bridge_active_cpa_margin_m": measurements.get("min_bridge_active_cpa_margin_m"),
            "min_bridge_active_cpa_margin_object_id": measurements.get("min_bridge_active_cpa_margin_object_id"),
            "active_lower_cpa_than_all_bridge": measurements.get("active_lower_cpa_than_all_bridge"),
            "active_better_cpa_rank_than_all_bridge": measurements.get("active_better_cpa_rank_than_all_bridge"),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "one-row descriptive active-row margin arbitration only; no actor-causality, repair, "
            "threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, "
            "HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, "
            "or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 94 - HUGSIM active-row surface margin arbitration",
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
            "## Event",
            "",
            "| audit id | event | active object | active margin | bridge count | min bridge margin | bridge finite TTC | label | problems |",
            "|---|---|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in report["events"]:
        measurements = row.get("measurements") or {}
        lines.append(
            f"| `{row['audit_id']}` | `{row['event_role']}` | `{measurements.get('active_object_id')}` | "
            f"`{measurements.get('active_cpa_margin_m')}` | `{measurements.get('bridge_supported_count')}` | "
            f"`{measurements.get('min_bridge_active_cpa_margin_m')}` | "
            f"`{measurements.get('bridge_finite_ttc_count')}` | `{row['row_label']}` | "
            f"`{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(iter91_report: Path, iter92_report: Path, iter93_report: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(iter91_report, iter92_report, iter93_report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iter91-report",
        type=Path,
        default=Path(
            "experiments/iter91_hugsim_active_gap_geometry_decomposition/proof-geometry/"
            "active_gap_geometry_report.json"
        ),
    )
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
        "--out",
        type=Path,
        default=Path(
            "experiments/iter94_hugsim_active_row_surface_margin_arbitration/proof-margin/"
            "active_row_surface_margin_arbitration_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter94_hugsim_active_row_surface_margin_arbitration/proof-margin/"
            "active_row_surface_margin_arbitration.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter91_report, args.iter92_report, args.iter93_report, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
