from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments/iter36_bridge_site_decomposition/analyze_bridge_sites.py"


def load_module():
    spec = importlib.util.spec_from_file_location("iter36_bridge_sites", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def probe(
    name: str,
    auc: float,
    ap: float,
    ba: float,
    recall: float,
    specificity: float,
) -> dict:
    return {
        "name": name,
        "heldout_auc": auc,
        "heldout_average_precision": ap,
        "heldout_balanced_accuracy": ba,
        "heldout_recall": recall,
        "heldout_specificity": specificity,
    }


def test_iter36_site_features_slice_frozen_bridge_parts():
    module = load_module()
    row = {
        "sdc_traj_query_last": list(range(1536)),
        "sdc_track_query": list(range(2000, 2256)),
    }

    assert module.site_features(row, "traj_slot_0").tolist() == list(range(0, 256))
    assert module.site_features(row, "traj_slot_5").tolist() == list(range(1280, 1536))
    assert module.site_features(row, "track_query").tolist() == list(range(2000, 2256))
    assert module.site_features(row, "all_bridge").shape == (1792,)


def test_iter36_s1_reproduction_passes_full_bridge_bars():
    module = load_module()
    report = module.evaluate_s1(probe("all_bridge", 0.95, 0.62, 0.86, 0.82, 0.84))

    assert report["pass"]
    assert report["failures"] == []


def test_iter36_s1_reproduction_rejects_weak_full_bridge():
    module = load_module()
    report = module.evaluate_s1(probe("all_bridge", 0.90, 0.40, 0.82, 0.82, 0.84))

    assert not report["pass"]
    assert any("all_bridge_auc" in failure for failure in report["failures"])
    assert any("all_bridge_average_precision" in failure for failure in report["failures"])


def test_iter36_site_metric_failures_enforce_full_bridge_margin():
    module = load_module()
    all_bridge = probe("all_bridge", 0.95, 0.60, 0.86, 0.82, 0.84)
    weak_site = probe("traj_slot_0", 0.84, 0.29, 0.77, 0.69, 0.74)

    failures = module.site_metric_failures(weak_site, all_bridge)

    assert any("heldout_auc" in failure for failure in failures)
    assert any("heldout_average_precision" in failure for failure in failures)
    assert any("all_bridge_auc_gap" in failure for failure in failures)


def test_iter36_s2_accepts_site_with_metrics_and_bootstrap():
    module = load_module()
    probes = {
        "all_bridge": probe("all_bridge", 0.95, 0.60, 0.86, 0.82, 0.84),
    }
    for name in module.site_definitions():
        if name != "all_bridge":
            probes[name] = probe(name, 0.90, 0.35, 0.80, 0.72, 0.78)
    bootstraps = {
        name: {"auc_p05": 0.80, "balanced_accuracy_p05": 0.70}
        for name in probes
        if name != "all_bridge"
    }

    report = module.evaluate_s2(probes, bootstraps)

    assert report["pass"]
    assert "traj_slot_0" in report["passing_sites"]


def test_iter36_verdict_order():
    module = load_module()

    assert module.verdict(False, None, None) == "INFRASTRUCTURE_NULL_S0_ARTIFACT_OR_COUNT_INTEGRITY"
    assert (
        module.verdict(True, {"pass": False}, None)
        == "BRIDGE_SITE_NULL_FULL_BRIDGE_REPRODUCTION_FAILED"
    )
    assert module.verdict(True, {"pass": True}, {"pass": False}) == "BRIDGE_SITE_NULL_NO_LOCALIZED_TARGET"
    assert (
        module.verdict(True, {"pass": True}, {"pass": True})
        == "BRIDGE_SITE_PASS_SITE_SPECIFIC_PREREG_AUTHORIZED"
    )
