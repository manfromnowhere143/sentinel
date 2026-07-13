#!/usr/bin/env python3
"""Iteration 64 unsupported-row temporal surface audit analyzer."""

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
EXPECTED_ROWS = (
    ("ttc_extreme_short", "scene-0038-extreme-00"),
    ("cpa_medium_b", "scene-0166-medium-00"),
)
MATCH_DISTANCE_M = 3.0
AMBIGUOUS_DISTANCE_M = 6.0
TIME_TOL = 1e-9


def _load_iter59_module() -> Any:
    repo = Path(__file__).resolve().parents[2]
    module_path = repo / "experiments" / "iter59_hugsim_actor_match_audit" / "analyze_actor_match.py"
    spec = importlib.util.spec_from_file_location("iter59_actor_match", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot-load-iter59-analyzer:{module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ITER59 = _load_iter59_module()


def require_float(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError(f"non-numeric:{field}")
    return float(value)


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


def crosscheck_reports(iter59_report: dict[str, Any], iter61_report: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    if iter59_report.get("verdict") != ITER59_VERDICT:
        problems.append(f"iter59-verdict-not-{ITER59_VERDICT}")
    if iter61_report.get("verdict") != ITER61_VERDICT:
        problems.append(f"iter61-verdict-not-{ITER61_VERDICT}")
    episodes61 = iter61_report.get("episodes")
    if not isinstance(episodes61, list):
        problems.append("iter61-episodes-not-list")
        return [], problems
    rows = [
        row for row in episodes61
        if isinstance(row, dict) and row.get("row_label") == "no_monitor_object_support"
    ]
    identities = [row_identity(row) for row in rows]
    expected = list(EXPECTED_ROWS)
    if identities != expected:
        problems.append(f"iter61-no-support-identity-mismatch:{identities}")
    return rows, problems


def episode_paths(proof_root: Path, audit_id: str, scenario: str) -> dict[str, Path]:
    ep_dir = proof_root / "episodes" / f"{audit_id}__{scenario}__on"
    return {
        "eval": ep_dir / "eval.json",
        "decisions": ep_dir / "sentinel_iter48_decisions.jsonl",
    }


def eligible_foregrounds(eval_path: Path) -> list[dict[str, Any]]:
    doc = json.loads(eval_path.read_text())
    provenance = doc.get("collision_provenance")
    if not isinstance(provenance, list):
        raise ValueError("collision-provenance-not-list")
    rows = []
    for row in provenance:
        if (
            isinstance(row, dict)
            and row.get("collision_type") == "foreground"
            and isinstance(row.get("obs_box"), list)
            and len(row["obs_box"]) >= 2
        ):
            try:
                ts = require_float(row.get("timestamp"), "foreground.timestamp")
                require_float(row["obs_box"][0], "obs_box.x")
                require_float(row["obs_box"][1], "obs_box.y")
            except (TypeError, ValueError):
                continue
            rows.append({
                "timestamp": ts,
                "obs_box": row["obs_box"],
                "obs_index": row.get("obs_index"),
                "obs_name": row.get("obs_name"),
            })
    if not rows:
        raise ValueError("eligible-foreground-missing")
    return sorted(rows, key=lambda item: item["timestamp"])


def read_decision_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if isinstance(row, dict) and "trace_error" not in row:
            rows.append(row)
    return rows


def distance_label(distance: float | None) -> str:
    if distance is None:
        return "not_evaluated"
    if distance <= MATCH_DISTANCE_M:
        return "match"
    if distance <= AMBIGUOUS_DISTANCE_M:
        return "ambiguous"
    return "no_support"


def variants_for_object(row: dict[str, Any], obj: dict[str, Any], foreground: dict[str, Any]) -> list[dict[str, Any]]:
    ts = require_float(row.get("ts", row.get("frame_index")), "row.ts")
    fg_ts = require_float(foreground.get("timestamp"), "foreground.timestamp")
    r_mat = ITER59.matrix3(row.get("l2g_r_mat"), "l2g_r_mat")
    trans_raw = row.get("l2g_t")
    if not isinstance(trans_raw, list) or len(trans_raw) < 2:
        raise ValueError("l2g_t-not-vec2")
    trans = [require_float(value, "l2g_t") for value in trans_raw]
    wx, wy = ITER59.vec2(obj.get("world"), "obj.world")
    vx, vy = ITER59.vec2(obj.get("vel"), "obj.vel")
    obs_forward = require_float(foreground["obs_box"][0], "obs_box.x")
    obs_lateral = require_float(foreground["obs_box"][1], "obs_box.y")
    lead = max(0.0, fg_ts - ts)
    variants = []
    for temporal_source, (px, py) in (
        ("frame_time", (wx, wy)),
        ("propagated_to_foreground", (wx + vx * lead, wy + vy * lead)),
    ):
        local_x, local_y = ITER59.world_to_monitor_local(px, py, r_mat, trans)
        for axis_order, (base_forward, base_lateral) in (
            ("yx", (local_y, local_x)),
            ("xy", (local_x, local_y)),
        ):
            for forward_sign in (-1, 1):
                for lateral_sign in (-1, 1):
                    monitor_forward = forward_sign * base_forward
                    monitor_lateral = lateral_sign * base_lateral
                    distance = math.hypot(monitor_forward - obs_forward, monitor_lateral - obs_lateral)
                    variants.append({
                        "decision_ts": ts,
                        "frame_index": row.get("frame_index"),
                        "object_id": obj.get("id"),
                        "object_score": obj.get("score"),
                        "foreground_timestamp": fg_ts,
                        "foreground_obs_index": foreground.get("obs_index"),
                        "foreground_obs_name": foreground.get("obs_name"),
                        "temporal_source": temporal_source,
                        "axis_order": axis_order,
                        "forward_sign": forward_sign,
                        "lateral_sign": lateral_sign,
                        "lead_time_s": lead,
                        "monitor_forward_lateral": [monitor_forward, monitor_lateral],
                        "hugsim_forward_lateral": [obs_forward, obs_lateral],
                        "distance_m": distance,
                    })
    return variants


def best_variant(variants: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not variants:
        return None
    return min(
        variants,
        key=lambda item: (
            item["distance_m"],
            item["decision_ts"],
            str(item["object_id"]),
            item["foreground_timestamp"],
            item["temporal_source"],
            item["axis_order"],
            item["forward_sign"],
            item["lateral_sign"],
        ),
    )


def row_label(best: dict[str, Any] | None, pre_contact_object_rows: int, foreground_count: int) -> str:
    if pre_contact_object_rows < 2 or foreground_count == 0 or best is None:
        return "insufficient_temporal_surface"
    if best["distance_m"] <= MATCH_DISTANCE_M:
        return "pre_contact_object_match"
    if best["distance_m"] <= AMBIGUOUS_DISTANCE_M:
        return "pre_contact_object_ambiguous"
    return "temporal_no_object_support"


def analyze_row(proof_root: Path, row: dict[str, Any]) -> dict[str, Any]:
    audit_id, scenario = row_identity(row)
    result: dict[str, Any] = {"audit_id": audit_id, "scenario": scenario, "problems": []}
    paths = episode_paths(proof_root, audit_id, scenario)
    for label in ("eval", "decisions"):
        path = paths[label]
        if not path.exists() or path.stat().st_size == 0:
            result["problems"].append(f"missing-{label}")
    if result["problems"]:
        return result
    try:
        foregrounds_all = eligible_foregrounds(paths["eval"])
        first_foreground_ts = foregrounds_all[0]["timestamp"]
        decisions = read_decision_rows(paths["decisions"])
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        result["problems"].append(f"parse-failed:{exc}")
        return result

    variants: list[dict[str, Any]] = []
    pre_contact_frames = 0
    pre_contact_object_rows = 0
    try:
        for decision in decisions:
            ts = require_float(decision.get("ts", decision.get("frame_index")), "row.ts")
            if ts >= first_foreground_ts - TIME_TOL:
                continue
            pre_contact_frames += 1
            objects = decision.get("objs")
            if not isinstance(objects, list):
                raise ValueError("objs-not-list")
            foregrounds = [foreground for foreground in foregrounds_all if foreground["timestamp"] >= ts - TIME_TOL]
            for obj in objects:
                if not isinstance(obj, dict) or "id" not in obj:
                    continue
                pre_contact_object_rows += 1
                for foreground in foregrounds:
                    variants.extend(variants_for_object(decision, obj, foreground))
    except (KeyError, TypeError, ValueError) as exc:
        result["problems"].append(f"analysis-failed:{exc}")
        return result

    best = best_variant(variants)
    label = row_label(best, pre_contact_object_rows, len(foregrounds_all))
    result.update({
        "first_foreground_ts": first_foreground_ts,
        "foreground_count": len(foregrounds_all),
        "pre_contact_frame_count": pre_contact_frames,
        "pre_contact_object_rows": pre_contact_object_rows,
        "evaluated_variant_count": len(variants),
        "row_label": label,
        "best_distance_m": best["distance_m"] if best is not None else None,
        "best_distance_label": distance_label(best["distance_m"] if best is not None else None),
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
    })
    return result


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    if infra_problems or len(rows) != 2 or any(row.get("problems") for row in rows):
        return "UNSUPPORTED_TEMPORAL_INFRA_NULL"
    labels = [row.get("row_label") for row in rows]
    if "pre_contact_object_match" in labels:
        return "UNSUPPORTED_TEMPORAL_MATCH_COMPLETE"
    if "pre_contact_object_ambiguous" in labels:
        return "UNSUPPORTED_TEMPORAL_AMBIGUOUS_NULL"
    if labels == ["temporal_no_object_support", "temporal_no_object_support"]:
        return "UNSUPPORTED_TEMPORAL_NO_SUPPORT_COMPLETE"
    if "insufficient_temporal_surface" in labels:
        return "UNSUPPORTED_TEMPORAL_SUPPORT_NULL"
    return "UNSUPPORTED_TEMPORAL_INFRA_NULL"


def build_report(proof_root: Path, iter59_report_path: Path, iter61_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    if not proof_root.exists():
        infra_problems.append(f"missing-proof-root:{proof_root}")
    iter59_report, problems59 = load_report(iter59_report_path, "iter59-report")
    iter61_report, problems61 = load_report(iter61_report_path, "iter61-report")
    infra_problems.extend(problems59)
    infra_problems.extend(problems61)
    target_rows: list[dict[str, Any]] = []
    if not problems59 and not problems61:
        target_rows, crosscheck_problems = crosscheck_reports(iter59_report, iter61_report)
        infra_problems.extend(crosscheck_problems)

    rows = [] if infra_problems else [analyze_row(proof_root, row) for row in target_rows]
    label_counts = Counter(
        row.get("row_label")
        for row in rows
        if not row.get("problems") and row.get("row_label")
    )
    verdict = choose_verdict(rows, infra_problems)
    return {
        "iteration": 64,
        "inputs": {
            "iter59_proof_root": str(proof_root),
            "iter59_report": str(iter59_report_path),
            "iter61_report": str(iter61_report_path),
        },
        "expected_rows": [
            {"audit_id": audit_id, "scenario": scenario}
            for audit_id, scenario in EXPECTED_ROWS
        ],
        "infra_problems": infra_problems,
        "episodes": rows,
        "summary": {
            "target_rows": len(target_rows),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "minimum_distance_m": min(
                (row["best_distance_m"] for row in rows if not row.get("problems") and row["best_distance_m"] is not None),
                default=None,
            ),
            "total_variants_evaluated": sum(
                row.get("evaluated_variant_count", 0)
                for row in rows
                if not row.get("problems")
            ),
        },
        "verdict": verdict,
        "claim_boundary": (
            "two-row pre-contact object-surface audit only; no transfer, safety, deployment, "
            "benchmark, actor-causality, repair, population, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 64 - unsupported-row temporal surface audit",
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
        lines.append(
            f"- `{row['audit_id']}` / `{row['scenario']}`: label `{row.get('row_label')}`, "
            f"best `{row.get('best_distance_m')}`, variants `{row.get('evaluated_variant_count')}`, "
            f"problems `{row.get('problems')}`"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    proof_root: Path,
    iter59_report: Path,
    iter61_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(proof_root, iter59_report, iter61_report)
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
        "--out",
        type=Path,
        default=Path("experiments/iter64_unsupported_temporal_surface_audit/proof-unsupported-temporal/unsupported_temporal_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter64_unsupported_temporal_surface_audit/proof-unsupported-temporal/unsupported_temporal.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter59_proof_root, args.iter59_report, args.iter61_report, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
