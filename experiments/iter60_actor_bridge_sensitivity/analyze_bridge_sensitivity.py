#!/usr/bin/env python3
"""Iteration 60 actor-match bridge sensitivity analyzer."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER59_CLASSIFIABLE = "classifiable_foreground"
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


def bridge_label(distance: float) -> str:
    if distance <= MATCH_DISTANCE_M:
        return "bridge_match_possible"
    if distance <= AMBIGUOUS_DISTANCE_M:
        return "bridge_ambiguous_possible"
    return "robust_mismatch"


def classifiable_iter59_rows(iter59_report: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    if iter59_report.get("verdict") != ITER59_VERDICT:
        problems.append(f"iter59-verdict-not-{ITER59_VERDICT}")
    episodes = iter59_report.get("episodes")
    if not isinstance(episodes, list):
        problems.append("iter59-episodes-not-list")
        return [], problems
    rows = [
        row for row in episodes
        if isinstance(row, dict) and row.get("support_label") == ITER59_CLASSIFIABLE
    ]
    if len(rows) != 3:
        problems.append(f"iter59-classifiable-count-{len(rows)}")
    identities = [
        (row.get("audit_id"), row.get("scenario"))
        for row in rows
    ]
    if len(set(identities)) != len(identities):
        problems.append("iter59-classifiable-duplicate-identity")
    return rows, problems


def load_iter59_report(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-iter59-report:{path}"]
    try:
        report = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"parse-iter59-report-failed:{exc}"]
    if not isinstance(report, dict):
        return {}, ["iter59-report-not-dict"]
    return report, []


def episode_paths(proof_root: Path, audit_id: str, scenario: str) -> dict[str, Path]:
    ep_dir = proof_root / "episodes" / f"{audit_id}__{scenario}__on"
    return {
        "episode_dir": ep_dir,
        "eval": ep_dir / "eval.json",
        "decisions": ep_dir / "sentinel_iter48_decisions.jsonl",
    }


def bridge_variants(decisions: dict[str, Any], foreground: dict[str, Any]) -> list[dict[str, Any]]:
    object_id = decisions.get("monitor_object_id")
    if object_id is None:
        raise ValueError("monitor-object-not-unique")
    argmins = decisions.get("argmins")
    if not isinstance(argmins, dict):
        raise ValueError("argmins-not-dict")
    objects_by_id = argmins.get("objects_by_id")
    if not isinstance(objects_by_id, dict):
        raise ValueError("objects-by-id-not-dict")
    obj = objects_by_id.get(object_id)
    if not isinstance(obj, dict):
        raise ValueError("monitor-object-missing")

    wx, wy = ITER59.vec2(obj.get("world"), "obj.world")
    vx, vy = ITER59.vec2(obj.get("vel"), "obj.vel")
    fire_ts = require_float(decisions.get("first_fire_ts"), "first_fire_ts")
    fg_ts = require_float(foreground.get("timestamp"), "foreground.timestamp")
    lead = max(0.0, fg_ts - fire_ts)
    obs_forward = require_float(foreground["obs_box"][0], "obs_box.x")
    obs_lateral = require_float(foreground["obs_box"][1], "obs_box.y")

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
                    distance = math.hypot(
                        monitor_forward - obs_forward,
                        monitor_lateral - obs_lateral,
                    )
                    variants.append({
                        "temporal_source": temporal_source,
                        "axis_order": axis_order,
                        "forward_sign": forward_sign,
                        "lateral_sign": lateral_sign,
                        "monitor_forward_lateral": [monitor_forward, monitor_lateral],
                        "hugsim_forward_lateral": [obs_forward, obs_lateral],
                        "lead_time_s": lead,
                        "distance_m": distance,
                        "label": bridge_label(distance),
                    })
    return variants


def analyze_row(proof_root: Path, row: dict[str, Any]) -> dict[str, Any]:
    audit_id = str(row.get("audit_id"))
    scenario = str(row.get("scenario"))
    result: dict[str, Any] = {
        "audit_id": audit_id,
        "scenario": scenario,
        "iter59_bridge_distance_m": row.get("bridge_distance_m"),
        "iter59_bridge_label": row.get("bridge_label"),
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
        ev = ITER59.read_eval(paths["eval"])
        decisions = ITER59.read_decisions(paths["decisions"])
        foreground = ev["first_foreground"]
        if not isinstance(foreground, dict):
            result["problems"].append("first-foreground-missing")
            return result
        variants = bridge_variants(decisions, foreground)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        result["problems"].append(f"analysis-failed:{exc}")
        return result

    best = min(variants, key=lambda item: item["distance_m"])
    result.update({
        "variant_count": len(variants),
        "best_distance_m": best["distance_m"],
        "best_label": best["label"],
        "best_variant": {
            key: best[key]
            for key in (
                "temporal_source",
                "axis_order",
                "forward_sign",
                "lateral_sign",
                "monitor_forward_lateral",
                "hugsim_forward_lateral",
                "lead_time_s",
            )
        },
        "variants": sorted(
            variants,
            key=lambda item: (
                item["distance_m"],
                item["temporal_source"],
                item["axis_order"],
                item["forward_sign"],
                item["lateral_sign"],
            ),
        ),
    })
    return result


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    if infra_problems or len(rows) != 3 or any(row.get("problems") for row in rows):
        return "BRIDGE_SENSITIVITY_INFRA_NULL"
    labels = [row.get("best_label") for row in rows]
    if "bridge_match_possible" in labels:
        return "BRIDGE_SENSITIVE_NULL"
    if "bridge_ambiguous_possible" in labels:
        return "BRIDGE_AMBIGUOUS_NULL"
    if labels == ["robust_mismatch", "robust_mismatch", "robust_mismatch"]:
        return "BRIDGE_ROBUST_MISMATCH_COMPLETE"
    return "BRIDGE_SENSITIVITY_INFRA_NULL"


def build_report(proof_root: Path, iter59_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    if not proof_root.exists():
        infra_problems.append(f"missing-proof-root:{proof_root}")
    iter59_report, report_problems = load_iter59_report(iter59_report_path)
    infra_problems.extend(report_problems)
    iter59_rows: list[dict[str, Any]] = []
    if not report_problems:
        iter59_rows, crosscheck_problems = classifiable_iter59_rows(iter59_report)
        infra_problems.extend(crosscheck_problems)

    rows = [] if infra_problems else [analyze_row(proof_root, row) for row in iter59_rows]
    label_counts = Counter(
        row.get("best_label")
        for row in rows
        if not row.get("problems") and row.get("best_label")
    )
    verdict = choose_verdict(rows, infra_problems)
    return {
        "iteration": 60,
        "inputs": {
            "iter59_proof_root": str(proof_root),
            "iter59_report": str(iter59_report_path),
        },
        "infra_problems": infra_problems,
        "classifiable_rows": [
            {
                "audit_id": row.get("audit_id"),
                "scenario": row.get("scenario"),
                "iter59_bridge_distance_m": row.get("bridge_distance_m"),
                "iter59_bridge_label": row.get("bridge_label"),
            }
            for row in iter59_rows
        ],
        "episodes": rows,
        "summary": {
            "iter59_classifiable_rows": len(iter59_rows),
            "variant_rows_evaluated": sum(not row.get("problems") for row in rows),
            "variants_per_row": 16 if rows else 0,
            "sensitivity_counts": dict(sorted(label_counts.items())),
            "minimum_distance_m": min(
                (row["best_distance_m"] for row in rows if not row.get("problems")),
                default=None,
            ),
        },
        "verdict": verdict,
        "claim_boundary": (
            "offline sensitivity audit over the three iteration-59 classifiable rows only; "
            "no transfer, safety, deployment, benchmark, retuning, repair, or population claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 60 - actor-match bridge sensitivity",
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
    lines.extend(["", "## Classifiable Rows", ""])
    for row in report["episodes"]:
        best = row.get("best_variant", {})
        lines.append(
            f"- `{row['audit_id']}` / `{row['scenario']}`: best `{row.get('best_label')}`, "
            f"distance `{row.get('best_distance_m')}`, variant "
            f"`{best.get('temporal_source')}/{best.get('axis_order')}/"
            f"{best.get('forward_sign')}/{best.get('lateral_sign')}`, "
            f"problems `{row.get('problems')}`"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(proof_root: Path, iter59_report: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(proof_root, iter59_report)
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
        "--out",
        type=Path,
        default=Path("experiments/iter60_actor_bridge_sensitivity/proof-bridge/bridge_sensitivity_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter60_actor_bridge_sensitivity/proof-bridge/bridge_sensitivity.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter59_proof_root, args.iter59_report, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
