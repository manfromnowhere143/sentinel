#!/usr/bin/env python3
"""Iteration 61 monitor object surface audit analyzer."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER60_VERDICT = "BRIDGE_AMBIGUOUS_NULL"
ITER59_CLASSIFIABLE = "classifiable_foreground"
EXPECTED_ROWS = (
    ("ttc_extreme_short", "scene-0038-extreme-00"),
    ("cpa_medium_b", "scene-0166-medium-00"),
    ("ttc_extreme_b", "scene-0383-extreme-00"),
)
MATCH_DISTANCE_M = 3.0
AMBIGUOUS_DISTANCE_M = 6.0


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


def crosscheck_reports(iter59_report: dict[str, Any], iter60_report: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    if iter59_report.get("verdict") != ITER59_VERDICT:
        problems.append(f"iter59-verdict-not-{ITER59_VERDICT}")
    if iter60_report.get("verdict") != ITER60_VERDICT:
        problems.append(f"iter60-verdict-not-{ITER60_VERDICT}")

    episodes59 = iter59_report.get("episodes")
    if not isinstance(episodes59, list):
        problems.append("iter59-episodes-not-list")
        return [], problems
    rows59 = [
        row for row in episodes59
        if isinstance(row, dict) and row.get("support_label") == ITER59_CLASSIFIABLE
    ]
    identities59 = [row_identity(row) for row in rows59]
    expected = list(EXPECTED_ROWS)
    if identities59 != expected:
        problems.append(f"iter59-classifiable-identity-mismatch:{identities59}")

    rows60_raw = iter60_report.get("classifiable_rows")
    if not isinstance(rows60_raw, list):
        problems.append("iter60-classifiable-rows-not-list")
    else:
        identities60 = [
            row_identity(row)
            for row in rows60_raw
            if isinstance(row, dict)
        ]
        if identities60 != expected:
            problems.append(f"iter60-classifiable-identity-mismatch:{identities60}")
    return rows59, problems


def episode_paths(proof_root: Path, audit_id: str, scenario: str) -> dict[str, Path]:
    ep_dir = proof_root / "episodes" / f"{audit_id}__{scenario}__on"
    return {
        "episode_dir": ep_dir,
        "eval": ep_dir / "eval.json",
        "decisions": ep_dir / "sentinel_iter48_decisions.jsonl",
    }


def eligible_foregrounds(eval_doc: dict[str, Any], first_fire_ts: float) -> list[dict[str, Any]]:
    provenance = eval_doc.get("collision_provenance")
    if not isinstance(provenance, list):
        return []
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
            if ts >= first_fire_ts:
                rows.append(row)
    return sorted(rows, key=lambda item: float(item["timestamp"]))


def distance_label(distance: float | None) -> str:
    if distance is None:
        return "not_evaluated"
    if distance <= MATCH_DISTANCE_M:
        return "match"
    if distance <= AMBIGUOUS_DISTANCE_M:
        return "ambiguous"
    return "no_support"


def object_foreground_variants(
    obj: dict[str, Any],
    object_id: Any,
    foreground: dict[str, Any],
    argmins: dict[str, Any],
    first_fire_ts: float,
    object_role: str,
) -> list[dict[str, Any]]:
    wx, wy = ITER59.vec2(obj.get("world"), "obj.world")
    vx, vy = ITER59.vec2(obj.get("vel"), "obj.vel")
    fg_ts = require_float(foreground.get("timestamp"), "foreground.timestamp")
    lead = max(0.0, fg_ts - first_fire_ts)
    obs_forward = require_float(foreground["obs_box"][0], "obs_box.x")
    obs_lateral = require_float(foreground["obs_box"][1], "obs_box.y")
    obs_index = foreground.get("obs_index")
    obs_name = foreground.get("obs_name")

    variants: list[dict[str, Any]] = []
    for temporal_source, (px, py) in (
        ("first_fire", (wx, wy)),
        ("propagated_to_foreground", (wx + vx * lead, wy + vy * lead)),
    ):
        local_x, local_y = ITER59.world_to_monitor_local(px, py, argmins["r_mat"], argmins["trans"])
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
                        "object_id": object_id,
                        "object_role": object_role,
                        "foreground_timestamp": fg_ts,
                        "foreground_obs_index": obs_index,
                        "foreground_obs_name": obs_name,
                        "temporal_source": temporal_source,
                        "axis_order": axis_order,
                        "forward_sign": forward_sign,
                        "lateral_sign": lateral_sign,
                        "monitor_forward_lateral": [monitor_forward, monitor_lateral],
                        "hugsim_forward_lateral": [obs_forward, obs_lateral],
                        "lead_time_s": lead,
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
            str(item["object_id"]),
            item["foreground_timestamp"],
            item["temporal_source"],
            item["axis_order"],
            item["forward_sign"],
            item["lateral_sign"],
        ),
    )


def compact_variant(variant: dict[str, Any] | None) -> dict[str, Any] | None:
    if variant is None:
        return None
    fields = (
        "object_id",
        "object_role",
        "foreground_timestamp",
        "foreground_obs_index",
        "foreground_obs_name",
        "temporal_source",
        "axis_order",
        "forward_sign",
        "lateral_sign",
        "monitor_forward_lateral",
        "hugsim_forward_lateral",
        "lead_time_s",
        "distance_m",
    )
    return {field: variant[field] for field in fields}


def row_label(trigger_best: dict[str, Any] | None, nontrigger_best: dict[str, Any] | None) -> str:
    trigger_distance = trigger_best["distance_m"] if trigger_best is not None else None
    nontrigger_distance = nontrigger_best["distance_m"] if nontrigger_best is not None else None
    if trigger_distance is not None and trigger_distance <= MATCH_DISTANCE_M:
        return "trigger_object_match"
    if nontrigger_distance is not None and nontrigger_distance <= MATCH_DISTANCE_M:
        return "nontrigger_object_match"
    if trigger_distance is not None and trigger_distance <= AMBIGUOUS_DISTANCE_M:
        return "trigger_object_ambiguous"
    if nontrigger_distance is not None and nontrigger_distance <= AMBIGUOUS_DISTANCE_M:
        return "nontrigger_object_ambiguous"
    return "no_monitor_object_support"


def analyze_row(proof_root: Path, row: dict[str, Any]) -> dict[str, Any]:
    audit_id, scenario = row_identity(row)
    result: dict[str, Any] = {
        "audit_id": audit_id,
        "scenario": scenario,
        "problems": [],
    }
    paths = episode_paths(proof_root, audit_id, scenario)
    for label in ("eval", "decisions"):
        path = paths[label]
        if not path.exists() or path.stat().st_size == 0:
            result["problems"].append(f"missing-{label}")
    if result["problems"]:
        return result

    try:
        reconstructed = ITER59.classify_episode(paths["episode_dir"], audit_id, scenario)
        if reconstructed.get("support_label") != ITER59_CLASSIFIABLE:
            result["problems"].append(f"reconstructed-support-{reconstructed.get('support_label')}")
            return result
        decisions = ITER59.read_decisions(paths["decisions"])
        eval_doc = json.loads(paths["eval"].read_text())
        first_fire_ts = require_float(decisions.get("first_fire_ts"), "first_fire_ts")
        trigger_id = decisions.get("monitor_object_id")
        argmins = decisions.get("argmins")
        first_fire_row = decisions.get("first_fire_row")
        if trigger_id is None:
            result["problems"].append("trigger-object-missing")
            return result
        if not isinstance(argmins, dict):
            result["problems"].append("argmins-not-dict")
            return result
        if not isinstance(first_fire_row, dict) or not isinstance(first_fire_row.get("objs"), list):
            result["problems"].append("first-fire-objs-missing")
            return result
        objects = [
            obj for obj in first_fire_row["objs"]
            if isinstance(obj, dict) and "id" in obj
        ]
        foregrounds = eligible_foregrounds(eval_doc, first_fire_ts)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        result["problems"].append(f"analysis-failed:{exc}")
        return result

    object_ids = [obj.get("id") for obj in objects]
    if trigger_id not in object_ids:
        result["problems"].append("trigger-object-not-in-first-fire-set")
    if not foregrounds:
        result["problems"].append("eligible-foregrounds-missing")
    if result["problems"]:
        return result

    trigger_variants: list[dict[str, Any]] = []
    nontrigger_variants: list[dict[str, Any]] = []
    for obj in objects:
        object_id = obj.get("id")
        role = "trigger" if object_id == trigger_id else "nontrigger"
        for foreground in foregrounds:
            variants = object_foreground_variants(obj, object_id, foreground, argmins, first_fire_ts, role)
            if role == "trigger":
                trigger_variants.extend(variants)
            else:
                nontrigger_variants.extend(variants)

    all_variants = trigger_variants + nontrigger_variants
    trigger_best = best_variant(trigger_variants)
    nontrigger_best = best_variant(nontrigger_variants)
    overall_best = best_variant(all_variants)
    label = row_label(trigger_best, nontrigger_best)
    top_variants = sorted(
        all_variants,
        key=lambda item: (
            item["distance_m"],
            item["object_role"],
            str(item["object_id"]),
            item["foreground_timestamp"],
        ),
    )[:8]
    result.update({
        "trigger_object_id": trigger_id,
        "object_count": len(objects),
        "nontrigger_object_count": len(objects) - 1,
        "foreground_count": len(foregrounds),
        "evaluated_variant_count": len(all_variants),
        "row_label": label,
        "trigger_min_distance_m": trigger_best["distance_m"] if trigger_best is not None else None,
        "trigger_distance_label": distance_label(trigger_best["distance_m"] if trigger_best is not None else None),
        "nontrigger_min_distance_m": nontrigger_best["distance_m"] if nontrigger_best is not None else None,
        "nontrigger_distance_label": distance_label(
            nontrigger_best["distance_m"] if nontrigger_best is not None else None
        ),
        "overall_min_distance_m": overall_best["distance_m"] if overall_best is not None else None,
        "best_trigger_variant": compact_variant(trigger_best),
        "best_nontrigger_variant": compact_variant(nontrigger_best),
        "best_overall_variant": compact_variant(overall_best),
        "top_variants": [compact_variant(variant) for variant in top_variants],
    })
    return result


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    if infra_problems or len(rows) != 3 or any(row.get("problems") for row in rows):
        return "OBJECT_SURFACE_INFRA_NULL"
    labels = [row.get("row_label") for row in rows]
    if "trigger_object_match" in labels:
        return "OBJECT_SURFACE_TRIGGER_MATCH_COMPLETE"
    if "nontrigger_object_match" in labels:
        return "OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE"
    if any(label in {"trigger_object_ambiguous", "nontrigger_object_ambiguous"} for label in labels):
        return "OBJECT_SURFACE_AMBIGUOUS_NULL"
    if labels == ["no_monitor_object_support", "no_monitor_object_support", "no_monitor_object_support"]:
        return "OBJECT_SURFACE_NO_SUPPORT_COMPLETE"
    return "OBJECT_SURFACE_INFRA_NULL"


def build_report(proof_root: Path, iter59_report_path: Path, iter60_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    if not proof_root.exists():
        infra_problems.append(f"missing-proof-root:{proof_root}")
    iter59_report, problems59 = load_report(iter59_report_path, "iter59-report")
    iter60_report, problems60 = load_report(iter60_report_path, "iter60-report")
    infra_problems.extend(problems59)
    infra_problems.extend(problems60)
    classifiable_rows: list[dict[str, Any]] = []
    if not problems59 and not problems60:
        classifiable_rows, crosscheck_problems = crosscheck_reports(iter59_report, iter60_report)
        infra_problems.extend(crosscheck_problems)

    rows = [] if infra_problems else [analyze_row(proof_root, row) for row in classifiable_rows]
    label_counts = Counter(
        row.get("row_label")
        for row in rows
        if not row.get("problems") and row.get("row_label")
    )
    verdict = choose_verdict(rows, infra_problems)
    return {
        "iteration": 61,
        "inputs": {
            "iter59_proof_root": str(proof_root),
            "iter59_report": str(iter59_report_path),
            "iter60_report": str(iter60_report_path),
        },
        "infra_problems": infra_problems,
        "expected_rows": [
            {"audit_id": audit_id, "scenario": scenario}
            for audit_id, scenario in EXPECTED_ROWS
        ],
        "episodes": rows,
        "summary": {
            "classifiable_rows": len(classifiable_rows),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "minimum_overall_distance_m": min(
                (row["overall_min_distance_m"] for row in rows if not row.get("problems")),
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
            "offline object-surface audit over the three iteration-59 classifiable rows only; "
            "no transfer, safety, deployment, benchmark, actor-causality, repair, population, "
            "or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 61 - monitor object surface audit",
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
            f"trigger min `{row.get('trigger_min_distance_m')}`, "
            f"nontrigger min `{row.get('nontrigger_min_distance_m')}`, "
            f"overall min `{row.get('overall_min_distance_m')}`, problems `{row.get('problems')}`"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    proof_root: Path,
    iter59_report: Path,
    iter60_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(proof_root, iter59_report, iter60_report)
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
        "--iter60-report",
        type=Path,
        default=Path("experiments/iter60_actor_bridge_sensitivity/proof-bridge/bridge_sensitivity_report.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/iter61_monitor_object_surface_audit/proof-object-surface/object_surface_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter61_monitor_object_surface_audit/proof-object-surface/object_surface.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter59_proof_root,
        args.iter59_report,
        args.iter60_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
