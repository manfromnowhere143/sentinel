#!/usr/bin/env python3
"""Iteration 58 HUGSIM provenance instrumented canary analyzer."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

SCENARIO = "scene-0013-hard-00"
EPISODES = (f"{SCENARIO}__off_r1", f"{SCENARIO}__on_r1")
SCALAR_TOP_LEVEL = ("nc", "dac", "ttc", "c", "pdms", "rc", "hdscore")
DETAIL_KEYS = {"nc", "dac", "ttc", "c", "pdms"}


def numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def nc_min(eval_doc: dict[str, Any]) -> float:
    values = [float(eval_doc["nc"])]
    details = eval_doc.get("details", {})
    if isinstance(details, dict):
        for row in details.values():
            if isinstance(row, dict) and numeric(row.get("nc")):
                values.append(float(row["nc"]))
    return min(values)


def details_are_scalar_only(eval_doc: dict[str, Any]) -> tuple[bool, list[str]]:
    problems: list[str] = []
    details = eval_doc.get("details")
    if not isinstance(details, dict):
        return False, ["details-not-dict"]
    for ts, row in details.items():
        if not isinstance(row, dict):
            problems.append(f"details-row-not-dict:{ts}")
            continue
        extra = sorted(set(row) - DETAIL_KEYS)
        missing = sorted(DETAIL_KEYS - set(row))
        if extra:
            problems.append(f"details-extra-keys:{ts}:{','.join(extra)}")
        if missing:
            problems.append(f"details-missing-keys:{ts}:{','.join(missing)}")
        for key in DETAIL_KEYS & set(row):
            if not numeric(row[key]):
                problems.append(f"details-nonnumeric:{ts}:{key}")
    return not problems, problems


def read_episode(root: Path, episode: str) -> dict[str, Any]:
    ep_dir = root / "episodes" / episode
    eval_path = ep_dir / "eval.json"
    output_path = ep_dir / "output.txt"
    meta_path = ep_dir / "episode_meta.json"
    row: dict[str, Any] = {
        "episode": episode,
        "path": str(ep_dir),
        "files_present": {
            "eval": eval_path.exists(),
            "output": output_path.exists(),
            "meta": meta_path.exists(),
        },
        "problems": [],
    }
    if not eval_path.exists():
        row["problems"].append("missing-eval")
        return row
    ev = json.loads(eval_path.read_text())
    row["top_level_keys"] = sorted(ev.keys())
    row["scalar_metrics_present"] = all(key in ev and numeric(ev[key]) for key in SCALAR_TOP_LEVEL)
    row["nc_min"] = nc_min(ev) if row["scalar_metrics_present"] else None
    scalar_only, detail_problems = details_are_scalar_only(ev)
    row["details_scalar_only"] = scalar_only
    row["detail_problems"] = detail_problems
    provenance = ev.get("collision_provenance")
    row["provenance_present"] = "collision_provenance" in ev
    row["provenance_is_list"] = isinstance(provenance, list)
    row["provenance_count"] = len(provenance) if isinstance(provenance, list) else 0
    row["provenance_sample_keys"] = (
        sorted(provenance[0].keys()) if isinstance(provenance, list) and provenance else []
    )
    if not row["scalar_metrics_present"]:
        row["problems"].append("scalar-metrics-missing-or-nonnumeric")
    if not scalar_only:
        row["problems"].extend(detail_problems)
    if not output_path.exists():
        row["problems"].append("missing-output")
    if not meta_path.exists():
        row["problems"].append("missing-meta")
    if episode.endswith("__on_r1"):
        decisions = ep_dir / "sentinel_iter48_decisions.jsonl"
        row["decision_log_present"] = decisions.exists() and decisions.stat().st_size > 0
        if not row["decision_log_present"]:
            row["problems"].append("missing-on-decision-log")
    return row


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    if infra_problems or any(row["problems"] for row in rows):
        return "CANARY_INFRA_NULL"
    collision_rows = [row for row in rows if row.get("nc_min") is not None and row["nc_min"] < 1.0]
    provenance_rows = [row for row in collision_rows if row["provenance_is_list"] and row["provenance_count"] > 0]
    if not collision_rows or not provenance_rows:
        return "PROVENANCE_CANARY_NULL"
    return "PROVENANCE_CANARY_COMPLETE"


def build_report(root: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    receipts_path = root / "receipts.json"
    if not receipts_path.exists():
        infra_problems.append("missing-receipts")
        receipts = {}
    else:
        receipts = json.loads(receipts_path.read_text())
    rows = [read_episode(root, episode) for episode in EPISODES]
    verdict = choose_verdict(rows, infra_problems)
    return {
        "iteration": 58,
        "scenario": SCENARIO,
        "expected_episodes": list(EPISODES),
        "receipts": receipts,
        "infra_problems": infra_problems,
        "episodes": rows,
        "summary": {
            "completed_rows": sum(not row["problems"] for row in rows),
            "collision_rows": sum(row.get("nc_min") is not None and row["nc_min"] < 1.0 for row in rows),
            "provenance_rows": sum(row["provenance_is_list"] and row["provenance_count"] > 0 for row in rows),
            "on_decision_log_present": any(
                row["episode"].endswith("__on_r1") and row.get("decision_log_present") for row in rows
            ),
        },
        "verdict": verdict,
        "claim_boundary": (
            "two-episode instrumentation canary only; no transfer, safety, benchmark, "
            "actor-match, HD-Score-invariance, deployment, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 58 - HUGSIM provenance canary",
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
    lines.extend(["", "## Episodes", ""])
    for row in report["episodes"]:
        lines.append(
            f"- `{row['episode']}`: nc_min `{row.get('nc_min')}`, "
            f"provenance_count `{row.get('provenance_count')}`, problems `{row['problems']}`"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(root: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proof-root", type=Path, required=True)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter58_hugsim_provenance_instrumented_canary/"
            "proof-canary/provenance_canary_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter58_hugsim_provenance_instrumented_canary/"
            "proof-canary/provenance_canary.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.proof_root, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
