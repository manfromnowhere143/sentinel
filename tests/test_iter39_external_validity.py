from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments/iter39_external_validity_claim_audit/analyze_external_validity.py"


def load_module():
    spec = importlib.util.spec_from_file_location("iter39_external_validity", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def claim(module, claim_id: str, evidence_status: str = "established", external_status: str = "within_scope"):
    return {
        "claim_id": claim_id,
        "claim_text": f"{claim_id} text",
        "evidence_paths": ["README.md"] if evidence_status != "untested" else [],
        "evidence_gap": "not yet measured" if evidence_status == "untested" else "",
        "scope": "tested scope only",
        "evidence_status": evidence_status,
        "external_validity_status": external_status,
        "permitted_wording": "scoped wording",
        "forbidden_wording": "broad wording",
        "next_falsifier": "strong hostile test",
    }


def complete_ledger(module):
    rows = [claim(module, claim_id) for claim_id in module.REQUIRED_CLAIM_IDS]
    overrides = {
        "deployment_metric_scope": ("split", "split_limited"),
        "planner_transfer_vad": ("split", "failed_transfer"),
        "full_trainval_localization": ("diagnostic", "diagnostic_only"),
        "activation_intervention_status": ("active_gate", "active_not_result"),
        "sensor_input_degradation": ("untested", "untested"),
        "adversarial_perturbation": ("untested", "untested"),
        "calibration_stability": ("split", "untested"),
        "intervention_latency_cost": ("untested", "untested"),
        "deployment_tradeoffs": ("untested", "untested"),
    }
    for row in rows:
        if row["claim_id"] in overrides:
            row["evidence_status"], row["external_validity_status"] = overrides[row["claim_id"]]
            if row["evidence_status"] == "untested":
                row["evidence_paths"] = []
                row["evidence_gap"] = "not yet measured"
    return rows


def test_iter39_s1_accepts_complete_scoped_ledger():
    module = load_module()
    rows = complete_ledger(module)

    report = module.evaluate_s1(rows, root=ROOT, tracked={"README.md"})

    assert report["pass"]
    assert report["claim_count"] == len(module.REQUIRED_CLAIM_IDS)


def test_iter39_s1_rejects_missing_required_claim():
    module = load_module()
    rows = complete_ledger(module)[:-1]

    report = module.evaluate_s1(rows, root=ROOT, tracked={"README.md"})

    assert not report["pass"]
    assert "missing_claim:deployment_tradeoffs" in report["failures"]


def test_iter39_s2_rejects_planner_transfer_overclaim():
    module = load_module()
    rows = complete_ledger(module)
    for row in rows:
        if row["claim_id"] == "planner_transfer_vad":
            row["evidence_status"] = "established"
            row["external_validity_status"] = "within_scope"

    report = module.evaluate_s2(rows)

    assert not report["pass"]
    assert "planner_transfer_vad:evidence_status_must_be_split_or_null" in report["failures"]
    assert "planner_transfer_vad:external_status_must_be_failed_transfer" in report["failures"]


def test_iter39_s3_flags_broad_planner_title(tmp_path):
    module = load_module()
    doc = tmp_path / "doc.md"
    doc.write_text("# A label-free runtime safety monitor for frozen end-to-end driving planners\n")

    report = module.evaluate_s3(root=tmp_path, active_docs=["doc.md"])

    assert not report["pass"]
    assert report["findings"][0]["id"] == "planner_general_title"


def test_iter39_s3_allows_title_with_scope_marker(tmp_path):
    module = load_module()
    doc = tmp_path / "doc.md"
    doc.write_text("# A label-free runtime safety monitor for UniAD, with VAD transfer limits\n")

    report = module.evaluate_s3(root=tmp_path, active_docs=["doc.md"])

    assert report["pass"]


def test_iter39_verdict_order():
    module = load_module()

    ok = {"pass": True}
    fail = {"pass": False}

    assert module.verdict(fail, None, None, None) == "INFRASTRUCTURE_NULL_EVIDENCE_OR_STATUS_INTEGRITY"
    assert module.verdict(ok, fail, None, None) == "CLAIM_AUDIT_NULL_LEDGER_INCOMPLETE"
    assert module.verdict(ok, ok, fail, None) == "CLAIM_AUDIT_NULL_SCOPE_CLASSIFICATION"
    assert module.verdict(ok, ok, ok, fail) == "CLAIM_AUDIT_DOC_NARROWING_REQUIRED"
    assert module.verdict(ok, ok, ok, ok) == "CLAIM_AUDIT_PASS_EXTERNAL_VALIDITY_ALIGNED"
