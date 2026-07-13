#!/usr/bin/env python3
"""Iteration 80 HUGSIM selected-object all-provenance bridge audit."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER77_VERDICT = "HUGSIM_EVENT_SET_FOREGROUND_SUPPORT_MIXED_COMPLETE"
ITER79_VERDICT = "HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE"
FIXED_EVENTS = (
    {
        "audit_id": "both_distinct_extreme",
        "scenario": "scene-0138-extreme-00",
        "role": "pre",
        "event_ts": 5.0,
        "selected_object_id": 5,
        "selected_state": "borderline",
        "support_object_id": 9,
        "support_band": "ambiguous",
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "role": "pre",
        "event_ts": 2.5,
        "selected_object_id": 6,
        "selected_state": "borderline",
        "support_object_id": 10,
        "support_band": "match",
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "role": "active",
        "event_ts": 5.0,
        "selected_object_id": 24,
        "selected_state": "active",
        "support_object_id": 10,
        "support_band": "match",
    },
)


def _load_module(relative_path: str, module_name: str) -> Any:
    repo = Path(__file__).resolve().parents[2]
    module_path = repo / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot-load-module:{module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ITER79 = _load_module(
    "experiments/iter79_hugsim_selected_surface_decomposition/analyze_selected_surface_decomposition.py",
    "iter79_selected_surface_decomposition",
)
SWITCH = ITER79.SWITCH
surface_margin = ITER79.surface_margin


def same_object_id(left: Any, right: Any) -> bool:
    return str(left) == str(right)


def event_index(rows: Any, problems: list[str]) -> dict[tuple[str, str, str], dict[str, Any]]:
    if not isinstance(rows, list):
        problems.append("iter79-events-not-list")
        return {}
    index: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            problems.append("iter79-event-not-dict")
            continue
        audit_id = row.get("audit_id")
        scenario = row.get("scenario")
        role = row.get("event_role")
        if not isinstance(audit_id, str) or not isinstance(scenario, str) or not isinstance(role, str):
            problems.append(f"iter79-event-key-missing:{row}")
            continue
        key = (audit_id, scenario, role)
        if key in index:
            problems.append(f"duplicate-iter79-event:{key}")
        index[key] = row
    return index


def load_all_provenance(eval_path: Path, problems: list[str]) -> list[dict[str, Any]]:
    if not eval_path.exists() or eval_path.stat().st_size == 0:
        problems.append(f"missing-eval:{eval_path}")
        return []
    try:
        doc = json.loads(eval_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        problems.append(f"read-eval-failed:{eval_path}:{exc}")
        return []
    provenance = doc.get("collision_provenance")
    if not isinstance(provenance, list):
        problems.append("collision-provenance-not-list")
        return []
    rows: list[dict[str, Any]] = []
    for idx, item in enumerate(provenance):
        if not isinstance(item, dict):
            continue
        obs_box = item.get("obs_box")
        if not isinstance(obs_box, list) or len(obs_box) < 2:
            continue
        timestamp = surface_margin.number(item.get("timestamp"), f"provenance.timestamp:{idx}", problems)
        obs_x = surface_margin.number(obs_box[0], f"provenance.obs_box.x:{idx}", problems)
        obs_y = surface_margin.number(obs_box[1], f"provenance.obs_box.y:{idx}", problems)
        if timestamp is None or obs_x is None or obs_y is None:
            continue
        collision_type = item.get("collision_type")
        rows.append(item | {"timestamp": timestamp, "collision_type": str(collision_type)})
    if not rows:
        problems.append("eligible-provenance-missing")
    return sorted(rows, key=lambda row: (float(row["timestamp"]), str(row.get("collision_type"))))


def compact_variant(variant: dict[str, Any] | None) -> dict[str, Any] | None:
    if variant is None:
        return None
    compact = SWITCH.compact_variant(variant)
    if compact is None:
        return None
    return compact | {
        "collision_type": variant.get("collision_type"),
        "provenance_index": variant.get("provenance_index"),
    }


def selected_bridge(
    event_row: dict[str, Any],
    event_ts: float,
    selected_obj: dict[str, Any],
    role: str,
    provenance_rows: list[dict[str, Any]],
    problems: list[str],
) -> dict[str, Any]:
    variants: list[dict[str, Any]] = []
    for idx, provenance in enumerate(provenance_rows):
        try:
            for variant in SWITCH.bridge_variants(event_row, event_ts, selected_obj, role, provenance):
                variants.append(
                    variant
                    | {
                        "collision_type": provenance.get("collision_type"),
                        "provenance_index": idx,
                    }
                )
        except (KeyError, TypeError, ValueError) as exc:
            problems.append(f"{role}-selected-object-bridge-failed:{exc}")
    best = SWITCH.best_variant(variants)
    distance = best["distance_m"] if best is not None else None
    type_counts = Counter(str(row.get("collision_type")) for row in provenance_rows)
    return {
        "role": role,
        "event_ts": event_ts,
        "selected_object_id": selected_obj.get("id"),
        "provenance_count": len(provenance_rows),
        "provenance_type_counts": dict(sorted(type_counts.items())),
        "evaluated_variant_count": len(variants),
        "best_variant": compact_variant(best),
        "best_distance_m": distance,
        "distance_band": SWITCH.distance_band(distance),
    }


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter77_report: dict[str, Any],
    iter79_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    expected_verdicts = {
        "iter59": (iter59_report, ITER59_VERDICT),
        "iter77": (iter77_report, ITER77_VERDICT),
        "iter79": (iter79_report, ITER79_VERDICT),
    }
    for label, (report, verdict) in expected_verdicts.items():
        if report.get("verdict") != verdict:
            problems.append(f"{label}-verdict-not-{verdict}")
        if report.get("infra_problems"):
            problems.append(f"{label}-infra-problems:{report.get('infra_problems')}")

    iter59_index = surface_margin.index_rows(iter59_report.get("episodes"), "iter59", problems)
    iter77_index = surface_margin.index_rows(iter77_report.get("episodes"), "iter77", problems)
    iter79_index = event_index(iter79_report.get("events"), problems)
    if len(iter79_index) != len(FIXED_EVENTS):
        problems.append(f"iter79-event-count-mismatch:{len(iter79_index)}")

    selected: list[dict[str, Any]] = []
    for event in FIXED_EVENTS:
        row_key = (event["audit_id"], event["scenario"])
        event_key = (event["audit_id"], event["scenario"], event["role"])
        row59 = iter59_index.get(row_key)
        row77 = iter77_index.get(row_key)
        row79 = iter79_index.get(event_key)
        if row59 is None:
            problems.append(f"missing-iter59-row:{row_key}")
            continue
        if row77 is None:
            problems.append(f"missing-iter77-row:{row_key}")
            continue
        if row79 is None:
            problems.append(f"missing-iter79-event:{event_key}")
            continue
        if row79.get("problems"):
            problems.append(f"iter79-event-problems:{event_key}:{row79.get('problems')}")
        if not same_object_id(row79.get("selected_object_id"), event["selected_object_id"]):
            problems.append(f"iter79-selected-object-mismatch:{event_key}:{row79.get('selected_object_id')}")
        if not same_object_id(row79.get("support_object_id"), event["support_object_id"]):
            problems.append(f"iter79-support-object-mismatch:{event_key}:{row79.get('support_object_id')}")
        if row79.get("selected_state") != event["selected_state"]:
            problems.append(f"iter79-selected-state-mismatch:{event_key}:{row79.get('selected_state')}")
        if row79.get("support_state") != "subthreshold":
            problems.append(f"iter79-support-state-mismatch:{event_key}:{row79.get('support_state')}")
        event_ts = surface_margin.number(row79.get("event_ts"), "iter79.event_ts", problems)
        if event_ts is not None and not math.isclose(event_ts, float(event["event_ts"]), abs_tol=1e-6):
            problems.append(f"iter79-event-ts-mismatch:{event_key}:{event_ts}")
        event_set = row77.get(f"{event['role']}_event_set")
        if not isinstance(event_set, dict):
            problems.append(f"iter77-event-set-missing:{event_key}")
        else:
            best = event_set.get("best_variant")
            if not isinstance(best, dict):
                problems.append(f"iter77-best-variant-missing:{event_key}")
            elif not same_object_id(best.get("object_id"), event["support_object_id"]):
                problems.append(f"iter77-support-object-mismatch:{event_key}:{best.get('object_id')}")
            if event_set.get("distance_band") != event["support_band"]:
                problems.append(f"iter77-support-band-mismatch:{event_key}:{event_set.get('distance_band')}")
        selected.append({"event": event, "iter59": row59, "iter79": row79})
    if len(selected) != len(FIXED_EVENTS):
        problems.append(f"fixed-event-count-mismatch:{len(selected)}")
    return selected, problems


def classify(distance_band: str, problems: list[str]) -> str:
    if problems or distance_band == "missing":
        return "selected_all_provenance_insufficient"
    if distance_band == "match":
        return "selected_all_provenance_match"
    if distance_band == "ambiguous":
        return "selected_all_provenance_ambiguous"
    if distance_band == "no_support":
        return "selected_all_provenance_no_support"
    return "selected_all_provenance_insufficient"


def analyze_event(item: dict[str, Any]) -> dict[str, Any]:
    event = item["event"]
    row59 = item["iter59"]
    row79 = item["iter79"]
    role = str(event["role"])
    problems: list[str] = []
    event_ts = surface_margin.number(row79.get("event_ts"), "event_ts", problems)
    episode_dir = row59.get("episode_dir")
    if not isinstance(episode_dir, str) or not episode_dir:
        problems.append("episode-dir-missing")
        decision_rows: list[dict[str, Any]] = []
        provenance_rows: list[dict[str, Any]] = []
    else:
        ep_dir = Path(episode_dir)
        decision_rows, row_problems = SWITCH.load_decision_rows(ep_dir / "sentinel_iter48_decisions.jsonl")
        provenance_rows = load_all_provenance(ep_dir / "eval.json", problems)
        problems.extend(row_problems)
    event_row = SWITCH.find_decision_row(decision_rows, event_ts, role, problems) if event_ts is not None else None
    selected_obj: dict[str, Any] | None = None
    bridge: dict[str, Any] = {}
    if event_row is not None and event_ts is not None:
        selected_obj = SWITCH.select_object(event_row, event["selected_object_id"], f"{role}.selected", problems)
        if selected_obj is not None:
            bridge = selected_bridge(event_row, event_ts, selected_obj, role, provenance_rows, problems)
    distance_band = str(bridge.get("distance_band", "missing"))
    row_label = classify(distance_band, problems)
    type_counts = Counter(str(row.get("collision_type")) for row in provenance_rows)
    return {
        "audit_id": event["audit_id"],
        "scenario": event["scenario"],
        "event_role": role,
        "event_ts": event_ts,
        "selected_object_id": event["selected_object_id"],
        "selected_state": event["selected_state"],
        "support_object_id": event["support_object_id"],
        "support_band": event["support_band"],
        "provenance_count": len(provenance_rows),
        "provenance_type_counts": dict(sorted(type_counts.items())),
        "selected_all_provenance_bridge": bridge,
        "row_label": row_label,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_EVENTS)
        or any(row.get("problems") for row in rows)
        or "selected_all_provenance_insufficient" in labels
    ):
        return "HUGSIM_SELECTED_ALL_PROVENANCE_BLOCKED"
    if "selected_all_provenance_match" in labels:
        return "HUGSIM_SELECTED_ALL_PROVENANCE_MATCH_COMPLETE"
    if "selected_all_provenance_ambiguous" in labels:
        return "HUGSIM_SELECTED_ALL_PROVENANCE_AMBIGUOUS_COMPLETE"
    if all(label == "selected_all_provenance_no_support" for label in labels):
        return "HUGSIM_SELECTED_ALL_PROVENANCE_NO_SUPPORT_COMPLETE"
    return "HUGSIM_SELECTED_ALL_PROVENANCE_MIXED_COMPLETE"


def build_report(
    iter59_report_path: Path,
    iter77_report_path: Path,
    iter79_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = surface_margin.load_report(iter59_report_path, "iter59-report")
    iter77_report, problems77 = surface_margin.load_report(iter77_report_path, "iter77-report")
    iter79_report, problems79 = surface_margin.load_report(iter79_report_path, "iter79-report")
    infra_problems.extend(problems59 + problems77 + problems79)
    selected: list[dict[str, Any]] = []
    if not infra_problems:
        selected, source_problems = crosscheck_sources(iter59_report, iter77_report, iter79_report)
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_event(item) for item in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    provenance_type_counts: Counter[str] = Counter()
    for row in rows:
        provenance_type_counts.update(row.get("provenance_type_counts", {}))
    return {
        "iteration": 80,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter77_report": str(iter77_report_path),
            "iter79_report": str(iter79_report_path),
        },
        "fixed_events": list(FIXED_EVENTS),
        "infra_problems": infra_problems,
        "events": rows,
        "summary": {
            "target_events": len(selected),
            "evaluated_events": sum(not row.get("problems") for row in rows),
            "event_label_counts": dict(sorted(label_counts.items())),
            "provenance_type_counts": dict(sorted(provenance_type_counts.items())),
            "match_events": sum(row.get("row_label") == "selected_all_provenance_match" for row in rows),
            "ambiguous_events": sum(
                row.get("row_label") == "selected_all_provenance_ambiguous" for row in rows
            ),
            "no_support_events": sum(
                row.get("row_label") == "selected_all_provenance_no_support" for row in rows
            ),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "three-event descriptive selected-object all-provenance bridge audit only; no "
            "actor-causality, repair, threshold-value, transfer, safety, deployment, robustness, "
            "benchmark, population, HD-Score-invariance, commercial-value, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 80 - HUGSIM selected-object all-provenance bridge audit",
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
        "| audit id | event | selected id | selected state | support id | provenance types | best class | best distance | band | label | problems |",
        "|---|---|---:|---|---:|---|---|---:|---|---|---|",
    ])
    for row in report["events"]:
        bridge = row.get("selected_all_provenance_bridge") or {}
        best = bridge.get("best_variant") or {}
        lines.append(
            f"| `{row['audit_id']}` | `{row['event_role']}` | `{row['selected_object_id']}` | "
            f"`{row['selected_state']}` | `{row['support_object_id']}` | "
            f"`{row.get('provenance_type_counts')}` | `{best.get('collision_type')}` | "
            f"`{bridge.get('best_distance_m')}` | `{bridge.get('distance_band')}` | "
            f"`{row['row_label']}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter59_report: Path,
    iter77_report: Path,
    iter79_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter59_report, iter77_report, iter79_report)
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
        "--iter77-report",
        type=Path,
        default=Path("experiments/iter77_hugsim_event_object_set_bridge/proof-set/set_report.json"),
    )
    parser.add_argument(
        "--iter79-report",
        type=Path,
        default=Path("experiments/iter79_hugsim_selected_surface_decomposition/proof-selected/selected_report.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/iter80_hugsim_selected_all_provenance_bridge/proof-all-provenance/all_provenance_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter80_hugsim_selected_all_provenance_bridge/proof-all-provenance/all_provenance.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter59_report,
        args.iter77_report,
        args.iter79_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
