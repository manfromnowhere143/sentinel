#!/usr/bin/env python3
"""Iteration 39 external-validity claim audit.

This analyzer is intentionally conservative. It does not infer new science from prose; it checks
that the manually curated claim ledger is complete, evidence-scoped, and consistent with the
campaign's strongest skeptical reading, then scans active story documents for a small set of
high-risk overclaim patterns.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_CLAIM_IDS = [
    "uniad_collision_prediction",
    "released_union_full14_benchmark",
    "deployment_metric_scope",
    "frontal_mitigation_not_prevention",
    "rss_formal_envelope",
    "planner_transfer_vad",
    "candidate_diversity_plan_b",
    "full_trainval_localization",
    "activation_intervention_status",
    "sensor_input_degradation",
    "adversarial_perturbation",
    "calibration_stability",
    "intervention_latency_cost",
    "deployment_tradeoffs",
]

ALLOWED_EVIDENCE_STATUS = {
    "established",
    "split",
    "null",
    "diagnostic",
    "active_gate",
    "untested",
    "unsupported",
}

ALLOWED_EXTERNAL_STATUS = {
    "within_scope",
    "split_limited",
    "failed_transfer",
    "diagnostic_only",
    "active_not_result",
    "untested",
}

FROZEN_INPUTS = [
    "README.md",
    "docs/REPORT.md",
    "docs/CAMPAIGN.md",
    "docs/NEXT_PHASE.md",
    "docs/paper/MANUSCRIPT.md",
    "experiments/VERIFICATION.md",
    "experiments/iter2_monitor/G1_RESULT.md",
    "experiments/iter2_monitor/RESULT.md",
    "experiments/iter3_progress/RESULT.md",
    "experiments/iter8_union/RESULT.md",
    "experiments/union_validation/RESULT.md",
    "experiments/iter9_evade/RESULT.md",
    "experiments/iter10_brakevade/RESULT.md",
    "experiments/iter11_early_evade/RESULT.md",
    "experiments/iter12_plan_selection/RESULT.md",
    "experiments/iter13_rss_baseline/RESULT.md",
    "experiments/vad_generalization/RESULT.md",
    "experiments/full14_benchmark/RESULT.md",
    "experiments/iter15_latch_release/RESULT.md",
    "experiments/iter16_soft_stop/RESULT.md",
    "experiments/full14_power/RESULT.md",
    "experiments/iter17_threat_routing/RESULT.md",
    "experiments/iter18_tracker/RESULT.md",
    "experiments/iter19_diversity_head/RESULT.md",
    "experiments/iter20_vad_tracker_portability/RESULT.md",
    "experiments/iter21_bev_diversity_head/RESULT.md",
    "experiments/iter29_trainval_risk_support_atlas/RESULT.md",
    "experiments/iter30_full_trainval_lowdiv_localization/RESULT.md",
    "experiments/iter31_full_trainval_bridge_intervention/RESULT.md",
    "experiments/iter32_prefix_replay_baseline_recovery/RESULT.md",
    "experiments/iter33_prefix_preserving_bridge_intervention/RESULT.md",
    "experiments/iter34_direction_specificity_audit/RESULT.md",
    "experiments/iter35_response_heterogeneity_audit/RESULT.md",
    "experiments/iter36_bridge_site_decomposition/RESULT.md",
    "experiments/iter37_track_query_site_intervention/RESULT.md",
    "experiments/iter38_track_query_opposite_direction/HYPOTHESIS.md",
    "experiments/iter38_track_query_opposite_direction/proof-direction/direction_report.json",
    "experiments/iter38_track_query_opposite_direction/proof-canary/canary_report.json",
]

ACTIVE_DOCS = [
    "README.md",
    "docs/REPORT.md",
    "docs/paper/MANUSCRIPT.md",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def git_tracked_paths(root: Path = ROOT) -> set[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return set(result.stdout.splitlines())


def path_failures(paths: list[str], tracked: set[str], root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    for rel in paths:
        if not (root / rel).exists():
            failures.append(f"missing_path:{rel}")
        if rel not in tracked:
            failures.append(f"untracked_path:{rel}")
    return failures


def run_docs_guard(root: Path = ROOT) -> dict[str, Any]:
    result = subprocess.run(
        ["python3", "scripts/validate_docs.py"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "pass": result.returncode == 0,
    }


def evaluate_s0(root: Path = ROOT, tracked: set[str] | None = None, run_docs: bool = True) -> dict[str, Any]:
    tracked = git_tracked_paths(root) if tracked is None else tracked
    failures = path_failures(FROZEN_INPUTS, tracked, root)

    iter37_text = (root / "experiments/iter37_track_query_site_intervention/RESULT.md").read_text()
    if "Status: `CALIBRATION_NULL_NO_USABLE_ALPHA`" not in iter37_text:
        failures.append("iter37_status_not_calibration_null")

    canary_path = root / "experiments/iter38_track_query_opposite_direction/proof-canary/canary_report.json"
    canary = load_json(canary_path) if canary_path.exists() else {}
    if canary.get("s0_canary_pass") is not True:
        failures.append("iter38_s0_canary_pass_not_true")
    if canary.get("failure_count") != 0:
        failures.append("iter38_s0_canary_failure_count_nonzero")
    if canary.get("alpha0p50_changed_track_query_sha_rows") != 24:
        failures.append("iter38_alpha0p50_changed_track_query_sha_rows_not_24")
    if canary.get("alpha0p50_unchanged_sdc_traj_query_last_sha_rows") != 24:
        failures.append("iter38_alpha0p50_wrong_site_guard_not_24")

    active_story = "\n".join((root / path).read_text(errors="replace") for path in ACTIVE_DOCS)
    if "calibration authorized but not launched" not in active_story:
        failures.append("iter38_calibration_not_launched_boundary_missing")
    if "no calibration result or safety claim" not in active_story:
        failures.append("iter38_no_calibration_result_boundary_missing")

    docs_guard = run_docs_guard(root) if run_docs else {"pass": True, "stdout": "not_run"}
    if not docs_guard["pass"]:
        failures.append("docs_guard_failed")

    return {
        "pass": not failures,
        "failures": failures,
        "docs_guard": docs_guard,
        "frozen_inputs_checked": len(FROZEN_INPUTS),
        "active_docs_checked": ACTIVE_DOCS,
    }


def rows_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("claim_id")): row for row in rows}


def evaluate_s1(rows: list[dict[str, Any]], root: Path = ROOT, tracked: set[str] | None = None) -> dict[str, Any]:
    tracked = git_tracked_paths(root) if tracked is None else tracked
    by_id = rows_by_id(rows)
    failures: list[str] = []

    for claim_id in REQUIRED_CLAIM_IDS:
        if claim_id not in by_id:
            failures.append(f"missing_claim:{claim_id}")

    for claim_id, row in by_id.items():
        if claim_id not in REQUIRED_CLAIM_IDS:
            failures.append(f"unexpected_claim:{claim_id}")
        evidence_status = row.get("evidence_status")
        external_status = row.get("external_validity_status")
        if evidence_status not in ALLOWED_EVIDENCE_STATUS:
            failures.append(f"{claim_id}:invalid_evidence_status:{evidence_status}")
        if external_status not in ALLOWED_EXTERNAL_STATUS:
            failures.append(f"{claim_id}:invalid_external_validity_status:{external_status}")

        evidence_paths = row.get("evidence_paths", [])
        if not isinstance(evidence_paths, list):
            failures.append(f"{claim_id}:evidence_paths_not_list")
            evidence_paths = []
        if evidence_status != "untested" and not evidence_paths:
            failures.append(f"{claim_id}:non_untested_claim_has_no_evidence_paths")
        if evidence_status == "untested" and not row.get("evidence_gap"):
            failures.append(f"{claim_id}:untested_claim_missing_evidence_gap")
        for rel in evidence_paths:
            if rel not in tracked:
                failures.append(f"{claim_id}:untracked_evidence_path:{rel}")
            if not (root / rel).exists():
                failures.append(f"{claim_id}:missing_evidence_path:{rel}")

        for key in ("claim_text", "scope", "permitted_wording", "forbidden_wording", "next_falsifier"):
            if not row.get(key):
                failures.append(f"{claim_id}:missing_{key}")

        scope = str(row.get("scope", "")).lower()
        if evidence_status == "established" and any(
            phrase in scope
            for phrase in ("any planner", "all planners", "production", "real vehicle", "sensor degradation")
        ):
            failures.append(f"{claim_id}:established_scope_inflated:{row.get('scope')}")

    return {
        "pass": not failures,
        "failures": failures,
        "required_claim_ids": REQUIRED_CLAIM_IDS,
        "claim_count": len(rows),
    }


def evaluate_s2(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = rows_by_id(rows)
    failures: list[str] = []

    def row(claim_id: str) -> dict[str, Any]:
        return by_id.get(claim_id, {})

    vad = row("planner_transfer_vad")
    if vad.get("evidence_status") not in {"split", "null"}:
        failures.append("planner_transfer_vad:evidence_status_must_be_split_or_null")
    if vad.get("external_validity_status") != "failed_transfer":
        failures.append("planner_transfer_vad:external_status_must_be_failed_transfer")

    deployment = row("deployment_metric_scope")
    if deployment.get("evidence_status") not in {"split", "null"}:
        failures.append("deployment_metric_scope:evidence_status_must_be_split_or_null")
    if deployment.get("external_validity_status") != "split_limited":
        failures.append("deployment_metric_scope:external_status_must_be_split_limited")

    localization = row("full_trainval_localization")
    if localization.get("evidence_status") != "diagnostic":
        failures.append("full_trainval_localization:evidence_status_must_be_diagnostic")
    if localization.get("external_validity_status") != "diagnostic_only":
        failures.append("full_trainval_localization:external_status_must_be_diagnostic_only")

    interventions = row("activation_intervention_status")
    if interventions.get("evidence_status") not in {"active_gate", "null"}:
        failures.append("activation_intervention_status:evidence_status_must_be_active_gate_or_null")
    if interventions.get("external_validity_status") != "active_not_result":
        failures.append("activation_intervention_status:external_status_must_be_active_not_result")

    for claim_id in (
        "sensor_input_degradation",
        "adversarial_perturbation",
        "intervention_latency_cost",
        "deployment_tradeoffs",
    ):
        candidate = row(claim_id)
        if candidate.get("evidence_status") != "untested":
            failures.append(f"{claim_id}:evidence_status_must_be_untested")
        if candidate.get("external_validity_status") != "untested":
            failures.append(f"{claim_id}:external_status_must_be_untested")

    calibration = row("calibration_stability")
    if calibration.get("evidence_status") not in {"split", "untested"}:
        failures.append("calibration_stability:evidence_status_must_be_split_or_untested")
    if calibration.get("external_validity_status") != "untested":
        failures.append("calibration_stability:external_status_must_be_untested_beyond_frozen_grids")

    return {"pass": not failures, "failures": failures}


OVERCLAIM_PATTERNS = [
    {
        "id": "planner_general_title",
        "regex": re.compile(r"runtime safety monitor for frozen end-to-end driving planners", re.I),
        "allowed_markers": ("UniAD", "VAD", "limit", "transfer"),
        "context": "line",
    },
    {
        "id": "planner_agnostic",
        "regex": re.compile(r"\b(planner-agnostic|any planner|all planners)\b", re.I),
        "allowed_markers": ("not planner-agnostic", "no claim"),
        "context": "window",
    },
    {
        "id": "plug_and_play_unqualified",
        "regex": re.compile(r"plug-and-play", re.I),
        "allowed_markers": ("frozen planner", "VAD", "selectivity", "not a plug-in"),
        "context": "window",
    },
    {
        "id": "deployment_positive_without_boundary",
        "regex": re.compile(r"deployment-positive monitor", re.I),
        "allowed_markers": ("achievable", "voided", "not-yet-safe", "safety gate"),
        "context": "window",
    },
    {
        "id": "production_or_certification_readiness",
        "regex": re.compile(r"\b(production-ready|deployment-ready|certification-ready|certified)\b", re.I),
        "allowed_markers": (),
        "context": "window",
    },
    {
        "id": "sensor_or_adversarial_robustness",
        "regex": re.compile(r"robust (to|under).*(sensor|degradation|adversarial)", re.I),
        "allowed_markers": (),
        "context": "window",
    },
]


def line_number_at(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def context_for(text: str, start: int, end: int, mode: str) -> str:
    if mode == "line":
        line_start = text.rfind("\n", 0, start) + 1
        line_end = text.find("\n", end)
        if line_end == -1:
            line_end = len(text)
        return text[line_start:line_end]
    return text[max(0, start - 260) : min(len(text), end + 260)]


def evaluate_s3(root: Path = ROOT, active_docs: list[str] | None = None) -> dict[str, Any]:
    active_docs = ACTIVE_DOCS if active_docs is None else active_docs
    findings: list[dict[str, Any]] = []
    for rel in active_docs:
        text = (root / rel).read_text(errors="replace")
        for pattern in OVERCLAIM_PATTERNS:
            for match in pattern["regex"].finditer(text):
                context = context_for(text, match.start(), match.end(), str(pattern["context"]))
                context_lower = context.lower()
                if any(marker.lower() in context_lower for marker in pattern["allowed_markers"]):
                    continue
                findings.append(
                    {
                        "id": pattern["id"],
                        "path": rel,
                        "line": line_number_at(text, match.start()),
                        "match": match.group(0),
                        "context": " ".join(context.strip().split()),
                    }
                )
    return {
        "pass": not findings,
        "findings": findings,
        "active_docs": active_docs,
    }


def evaluate_s4(s3_report: dict[str, Any]) -> dict[str, Any]:
    if not s3_report["pass"]:
        return {
            "recommendation": "narrow_active_docs_before_any_gpu_or_model_work",
            "primary_next_step": "publish_doc_narrowing",
            "iteration38_calibration_priority": "paused_until_active_docs_are_aligned",
        }
    return {
        "recommendation": "prioritize_external_validity_falsification_over_incremental_mechanism_search",
        "primary_next_step": "offline_latency_and_intervention_cost_audit_over_committed_decision_logs",
        "iteration38_calibration_priority": "allowed_by_iter38_but_not_primary_without_new_justification",
    }


def verdict(s0: dict[str, Any], s1: dict[str, Any] | None, s2: dict[str, Any] | None, s3: dict[str, Any] | None) -> str:
    if not s0["pass"]:
        return "INFRASTRUCTURE_NULL_EVIDENCE_OR_STATUS_INTEGRITY"
    if s1 is None or not s1["pass"]:
        return "CLAIM_AUDIT_NULL_LEDGER_INCOMPLETE"
    if s2 is None or not s2["pass"]:
        return "CLAIM_AUDIT_NULL_SCOPE_CLASSIFICATION"
    if s3 is None or not s3["pass"]:
        return "CLAIM_AUDIT_DOC_NARROWING_REQUIRED"
    return "CLAIM_AUDIT_PASS_EXTERNAL_VALIDITY_ALIGNED"


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    ledger_path = Path(args.ledger)
    if not ledger_path.is_absolute():
        ledger_path = root / ledger_path
    rows = load_json(ledger_path)
    tracked = git_tracked_paths(root)

    s0 = evaluate_s0(root=root, tracked=tracked, run_docs=not args.skip_docs_guard)
    s1 = evaluate_s1(rows, root=root, tracked=tracked) if s0["pass"] else None
    s2 = evaluate_s2(rows) if s1 and s1["pass"] else None
    s3 = evaluate_s3(root=root) if s2 and s2["pass"] else None
    s4 = evaluate_s4(s3 or {"pass": False})

    return {
        "verdict": verdict(s0, s1, s2, s3),
        "command_line": " ".join(sys.argv),
        "ledger_path": str(ledger_path.relative_to(root)),
        "s0": s0,
        "s1": s1,
        "s2": s2,
        "s3": s3,
        "s4": s4,
        "claim_boundary": (
            "This is an offline claim-scope audit over committed evidence and active docs. "
            "It creates no new planner, sensor, adversarial, deployment, or safety evidence."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument(
        "--ledger",
        default="experiments/iter39_external_validity_claim_audit/proof-audit/claim_ledger.json",
    )
    parser.add_argument(
        "--out",
        default="experiments/iter39_external_validity_claim_audit/proof-audit/external_validity_report.json",
    )
    parser.add_argument("--skip-docs-guard", action="store_true")
    args = parser.parse_args()

    report = build_report(args)
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = Path(args.root) / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": report["verdict"], "out": str(out_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
