#!/usr/bin/env python3
"""Iteration 62 non-trigger ranking audit analyzer."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER61_VERDICT = "OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE"
TARGET_AUDIT_ID = "ttc_extreme_b"
TARGET_SCENARIO = "scene-0383-extreme-00"
TARGET_MATCHED_OBJECT_ID = 16
TTC_THRESH = 2.5
CPA_MARGIN = 1.5
TTC_BORDERLINE = 5.0
CPA_BORDERLINE = 3.0


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


def crosscheck_reports(iter59_report: dict[str, Any], iter61_report: dict[str, Any]) -> tuple[int | None, list[str]]:
    problems: list[str] = []
    if iter59_report.get("verdict") != ITER59_VERDICT:
        problems.append(f"iter59-verdict-not-{ITER59_VERDICT}")
    if iter61_report.get("verdict") != ITER61_VERDICT:
        problems.append(f"iter61-verdict-not-{ITER61_VERDICT}")
    episodes = iter61_report.get("episodes")
    if not isinstance(episodes, list):
        problems.append("iter61-episodes-not-list")
        return None, problems
    matched_rows = [
        row for row in episodes
        if isinstance(row, dict) and row.get("row_label") == "nontrigger_object_match"
    ]
    if len(matched_rows) != 1:
        problems.append(f"iter61-nontrigger-match-count-{len(matched_rows)}")
        return None, problems
    row = matched_rows[0]
    if row.get("audit_id") != TARGET_AUDIT_ID or row.get("scenario") != TARGET_SCENARIO:
        problems.append(f"iter61-target-row-mismatch:{row.get('audit_id')}/{row.get('scenario')}")
    variant = row.get("best_nontrigger_variant")
    if not isinstance(variant, dict):
        problems.append("iter61-best-nontrigger-variant-missing")
        return None, problems
    matched_id = variant.get("object_id")
    if matched_id != TARGET_MATCHED_OBJECT_ID:
        problems.append(f"iter61-matched-object-not-{TARGET_MATCHED_OBJECT_ID}:{matched_id}")
    return matched_id if isinstance(matched_id, int) else None, problems


def target_paths(proof_root: Path) -> dict[str, Path]:
    ep_dir = proof_root / "episodes" / f"{TARGET_AUDIT_ID}__{TARGET_SCENARIO}__on"
    return {
        "episode_dir": ep_dir,
        "decisions": ep_dir / "sentinel_iter48_decisions.jsonl",
    }


def object_metrics(first_fire_row: dict[str, Any]) -> list[dict[str, Any]]:
    r_mat = ITER59.matrix3(first_fire_row.get("l2g_r_mat"), "l2g_r_mat")
    trans_raw = first_fire_row.get("l2g_t")
    if not isinstance(trans_raw, list) or len(trans_raw) < 2:
        raise ValueError("l2g_t-not-vec2")
    trans = [require_float(value, "l2g_t") for value in trans_raw]
    params = first_fire_row.get("params")
    if not isinstance(params, dict):
        raise ValueError("params-not-dict")
    dt = require_float(params.get("dt"), "params.dt")
    min_closing = require_float(params.get("min_closing"), "params.min_closing")
    traj = first_fire_row.get("traj")
    if not isinstance(traj, list) or not traj:
        raise ValueError("traj-not-list")
    plan_world = []
    for point in traj:
        px, py = ITER59.vec2(point, "traj")
        plan_world.append(ITER59.transform_xy(px, py, r_mat, trans))
    objs = first_fire_row.get("objs")
    if not isinstance(objs, list):
        raise ValueError("objs-not-list")

    rows: list[dict[str, Any]] = []
    for obj in objs:
        if not isinstance(obj, dict):
            raise ValueError("obj-not-dict")
        oid = obj.get("id")
        wx, wy = ITER59.vec2(obj.get("world"), "obj.world")
        vx, vy = ITER59.vec2(obj.get("vel"), "obj.vel")
        min_cpa = math.inf
        cpa_horizon_index = None
        for idx, (ego_x, ego_y) in enumerate(plan_world):
            horizon = (idx + 1) * dt
            ax = wx + vx * horizon
            ay = wy + vy * horizon
            dist = math.hypot(ego_x - ax, ego_y - ay)
            if dist < min_cpa:
                min_cpa = dist
                cpa_horizon_index = idx + 1

        ego_x, ego_y = trans[0], trans[1]
        dx, dy = ego_x - wx, ego_y - wy
        gap = math.hypot(dx, dy)
        closing = None
        ttc = None
        if gap > 1e-3:
            closing_value = (vx * dx + vy * dy) / gap
            if closing_value > max(min_closing, 0.5):
                closing = closing_value
                ttc = gap / closing_value
        rows.append({
            "object_id": oid,
            "score": obj.get("score"),
            "world": [wx, wy],
            "velocity": [vx, vy],
            "min_cpa": min_cpa,
            "cpa_horizon_index": cpa_horizon_index,
            "gap": gap,
            "closing": closing,
            "ttc": ttc,
            "cpa_cross": min_cpa < CPA_MARGIN,
            "ttc_cross": ttc is not None and ttc < TTC_THRESH,
        })

    cpa_sorted = sorted(rows, key=lambda row: (row["min_cpa"], str(row["object_id"])))
    for rank, row in enumerate(cpa_sorted, start=1):
        row["cpa_rank"] = rank
    ttc_sorted = sorted(
        (row for row in rows if row["ttc"] is not None),
        key=lambda row: (row["ttc"], str(row["object_id"])),
    )
    for rank, row in enumerate(ttc_sorted, start=1):
        row["ttc_rank"] = rank
    for row in rows:
        row.setdefault("ttc_rank", None)
    return sorted(rows, key=lambda row: str(row["object_id"]))


def matched_label(row: dict[str, Any]) -> str:
    if row["cpa_cross"] or row["ttc_cross"]:
        return "matched_object_hazard_present"
    if row["min_cpa"] < CPA_BORDERLINE or (row["ttc"] is not None and row["ttc"] < TTC_BORDERLINE):
        return "matched_object_borderline"
    return "matched_object_subthreshold"


def choose_verdict(label: str | None, infra_problems: list[str], row_problems: list[str]) -> str:
    if infra_problems or row_problems or label is None:
        return "NONTRIGGER_RANKING_INFRA_NULL"
    if label == "matched_object_hazard_present":
        return "MATCHED_OBJECT_HAZARD_PRESENT_COMPLETE"
    if label == "matched_object_borderline":
        return "MATCHED_OBJECT_BORDERLINE_NULL"
    if label == "matched_object_subthreshold":
        return "MATCHED_OBJECT_SUBTHRESHOLD_COMPLETE"
    return "NONTRIGGER_RANKING_INFRA_NULL"


def build_report(proof_root: Path, iter59_report_path: Path, iter61_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    if not proof_root.exists():
        infra_problems.append(f"missing-proof-root:{proof_root}")
    iter59_report, problems59 = load_report(iter59_report_path, "iter59-report")
    iter61_report, problems61 = load_report(iter61_report_path, "iter61-report")
    infra_problems.extend(problems59)
    infra_problems.extend(problems61)
    matched_id = None
    if not problems59 and not problems61:
        matched_id, crosscheck_problems = crosscheck_reports(iter59_report, iter61_report)
        infra_problems.extend(crosscheck_problems)

    row_problems: list[str] = []
    objects: list[dict[str, Any]] = []
    matched_object: dict[str, Any] | None = None
    trigger_object_id = None
    first_fire_channel = None
    if not infra_problems:
        paths = target_paths(proof_root)
        if not paths["decisions"].exists() or paths["decisions"].stat().st_size == 0:
            row_problems.append("missing-decisions")
        else:
            try:
                decisions = ITER59.read_decisions(paths["decisions"])
                first_fire_row = decisions.get("first_fire_row")
                if not isinstance(first_fire_row, dict):
                    row_problems.append("first-fire-row-missing")
                else:
                    first_fire_channel = decisions.get("first_fire_channel")
                    trigger_object_id = decisions.get("monitor_object_id")
                    objects = object_metrics(first_fire_row)
                    for row in objects:
                        row["is_trigger_object"] = row["object_id"] == trigger_object_id
                        row["is_matched_nontrigger_object"] = row["object_id"] == matched_id
                    matched = [row for row in objects if row["object_id"] == matched_id]
                    if len(matched) != 1:
                        row_problems.append(f"matched-object-count-{len(matched)}")
                    else:
                        matched_object = matched[0]
            except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                row_problems.append(f"analysis-failed:{exc}")

    label = matched_label(matched_object) if matched_object is not None else None
    verdict = choose_verdict(label, infra_problems, row_problems)
    return {
        "iteration": 62,
        "inputs": {
            "iter59_proof_root": str(proof_root),
            "iter59_report": str(iter59_report_path),
            "iter61_report": str(iter61_report_path),
        },
        "target": {
            "audit_id": TARGET_AUDIT_ID,
            "scenario": TARGET_SCENARIO,
            "matched_object_id": matched_id,
            "trigger_object_id": trigger_object_id,
            "first_fire_channel": first_fire_channel,
        },
        "infra_problems": infra_problems,
        "row_problems": row_problems,
        "objects": objects,
        "matched_object": matched_object,
        "matched_object_label": label,
        "summary": {
            "object_count": len(objects),
            "matched_object_label": label,
            "matched_object_cpa_rank": matched_object.get("cpa_rank") if matched_object else None,
            "matched_object_ttc_rank": matched_object.get("ttc_rank") if matched_object else None,
            "matched_object_min_cpa": matched_object.get("min_cpa") if matched_object else None,
            "matched_object_ttc": matched_object.get("ttc") if matched_object else None,
        },
        "verdict": verdict,
        "claim_boundary": (
            "one-row first-fire object ranking audit only; no transfer, safety, deployment, "
            "benchmark, actor-causality, repair, population, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 62 - non-trigger ranking audit",
        "",
        f"Verdict: `{report['verdict']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    if report["infra_problems"] or report["row_problems"]:
        lines.extend(["", "## Problems", ""])
        lines.extend(f"- `{problem}`" for problem in report["infra_problems"])
        lines.extend(f"- `{problem}`" for problem in report["row_problems"])
    matched = report.get("matched_object")
    if isinstance(matched, dict):
        lines.extend([
            "",
            "## Matched Object",
            "",
            f"- `object_id`: `{matched.get('object_id')}`",
            f"- `min_cpa`: `{matched.get('min_cpa')}`",
            f"- `cpa_rank`: `{matched.get('cpa_rank')}`",
            f"- `ttc`: `{matched.get('ttc')}`",
            f"- `ttc_rank`: `{matched.get('ttc_rank')}`",
            f"- `cpa_cross`: `{matched.get('cpa_cross')}`",
            f"- `ttc_cross`: `{matched.get('ttc_cross')}`",
        ])
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
        default=Path("experiments/iter62_nontrigger_ranking_audit/proof-ranking/nontrigger_ranking_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter62_nontrigger_ranking_audit/proof-ranking/nontrigger_ranking.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter59_proof_root,
        args.iter59_report,
        args.iter61_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
