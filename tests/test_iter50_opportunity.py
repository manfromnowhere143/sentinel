"""Iteration 50 collision-opportunity audit tooling tests (synthetic fixtures only)."""

import importlib.util
import json
from pathlib import Path

import pytest

EXP = Path(__file__).resolve().parents[1] / "experiments" / "iter50_collision_opportunity_audit"

spec = importlib.util.spec_from_file_location("analyze_opportunity", EXP / "analyze_opportunity.py")
az = importlib.util.module_from_spec(spec)
spec.loader.exec_module(az)


def write_eval(root: Path, episode: str, nc_steps, ttc_steps=None, hdscore=0.5) -> Path:
    ttc_steps = ttc_steps if ttc_steps is not None else [1.0] * len(nc_steps)
    d = root / episode
    d.mkdir(parents=True, exist_ok=True)
    details = {f"{(i + 1) * 0.25:.2f}": {"nc": nc, "ttc": ttc, "dac": 1.0, "c": 1.0, "pdms": 1.0}
               for i, (nc, ttc) in enumerate(zip(nc_steps, ttc_steps))}
    ev = {"nc": nc_steps[-1], "dac": 1.0, "ttc": ttc_steps[-1], "c": 1.0, "pdms": 1.0,
          "rc": hdscore, "hdscore": hdscore, "details": details}
    (d / "eval.json").write_text(json.dumps(ev))
    return d / "eval.json"


# --- frozen primary/secondary definitions -----------------------------------------------

def test_primary_opportunity_from_details_step(tmp_path):
    p = write_eval(tmp_path, "scene-0001-easy-00__off_r1", nc_steps=[1.0, 0.0, 1.0])
    rec = az.read_off_opportunity(p)
    assert rec["nc_min"] == 0.0 and rec["primary_opportunity"]


def test_primary_opportunity_from_top_level_only(tmp_path):
    p = tmp_path / "e" / "eval.json"
    p.parent.mkdir()
    p.write_text(json.dumps({"nc": 0.5, "ttc": 1.0, "hdscore": 0.1, "details": {}}))
    assert az.read_off_opportunity(p)["primary_opportunity"]


def test_no_opportunity_clean_episode(tmp_path):
    p = write_eval(tmp_path, "scene-0002-easy-00__off_r1", nc_steps=[1.0, 1.0])
    rec = az.read_off_opportunity(p)
    assert not rec["primary_opportunity"] and not rec["secondary_near_miss"]


def test_secondary_near_miss_requires_no_primary(tmp_path):
    p = write_eval(tmp_path, "a__off_r1", nc_steps=[1.0, 1.0], ttc_steps=[1.0, 0.0])
    rec = az.read_off_opportunity(p)
    assert not rec["primary_opportunity"] and rec["secondary_near_miss"]
    p2 = write_eval(tmp_path, "b__off_r1", nc_steps=[0.0, 1.0], ttc_steps=[0.0, 1.0])
    rec2 = az.read_off_opportunity(p2)
    assert rec2["primary_opportunity"] and not rec2["secondary_near_miss"]


def test_missing_nc_field_raises(tmp_path):
    p = tmp_path / "e" / "eval.json"
    p.parent.mkdir()
    p.write_text(json.dumps({"ttc": 1.0, "hdscore": 0.1, "details": {}}))
    with pytest.raises(KeyError):
        az.read_off_opportunity(p)


def test_non_numeric_nc_raises(tmp_path):
    p = tmp_path / "e" / "eval.json"
    p.parent.mkdir()
    p.write_text(json.dumps({"nc": "1.0", "ttc": 1.0, "hdscore": 0.1, "details": {}}))
    with pytest.raises(ValueError):
        az.read_off_opportunity(p)


def test_circularity_guard_rejects_on_arm_path(tmp_path):
    p = write_eval(tmp_path, "scene-0001-easy-00__on_r1", nc_steps=[1.0])
    with pytest.raises(ValueError, match="circularity"):
        az.read_off_opportunity(p)


# --- Spearman + bootstrap ----------------------------------------------------------------

def test_spearman_perfect_monotone():
    assert az.spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert az.spearman([1, 2, 3, 4], [40, 30, 20, 10]) == pytest.approx(-1.0)


def test_spearman_average_ranks_ties():
    # x has a tie; known rho for this configuration
    rho = az.spearman([1.0, 1.0, 2.0], [1.0, 2.0, 3.0])
    assert rho == pytest.approx(0.866025, abs=1e-5)


def test_spearman_zero_variance_is_zero():
    assert az.spearman([1.0, 1.0, 1.0], [1.0, 2.0, 3.0]) == 0.0


def test_bootstrap_deterministic():
    x = [0.1, 0.3, 0.5, 0.7, 0.9, 0.2, 0.4, 0.6]
    y = [1.0, 2.0, 2.5, 3.0, 4.0, 1.5, 2.2, 2.8]
    assert az.bootstrap_rho(x, y) == az.bootstrap_rho(x, y)


def test_a1_verdict_bars():
    assert az.a1_verdict(0.7, [0.2, 0.9]) == "A1_CONFIRMED"
    assert az.a1_verdict(0.7, [-0.1, 0.9]) == "A1_ABSENT"  # CI includes zero
    assert az.a1_verdict(0.4, [0.1, 0.6]) == "A1_ABSENT"  # rho below bar
    assert az.a1_verdict(-0.6, [-0.9, -0.2]) == "A1_INVERTED"
    assert az.a1_verdict(0.0, [-0.4, 0.4]) == "A1_ABSENT"


# --- A2 classification bar ---------------------------------------------------------------

def _rows(n_primary: int, n_total: int = 52):
    return ([{"primary_opportunity": True, "secondary_near_miss": False, "tier": "easy"}] * n_primary
            + [{"primary_opportunity": False, "secondary_near_miss": False, "tier": "easy"}]
            * (n_total - n_primary))


def test_classification_bar_boundary():
    scarce = az.summarize_set(_rows(12))
    present = az.summarize_set(_rows(13))
    assert scarce["primary_opportunity_fraction"] < az.OPPORTUNITY_FRACTION_BAR
    assert present["primary_opportunity_fraction"] >= az.OPPORTUNITY_FRACTION_BAR


def test_summarize_set_counts():
    rows = _rows(5, 10)
    s = az.summarize_set(rows)
    assert s["episodes"] == 10 and s["primary_opportunity_count"] == 5
    assert s["primary_opportunity_fraction"] == 0.5
    assert s["per_tier"]["easy"]["episodes"] == 10


def test_episode_tier_parsing():
    assert az.episode_tier("scene-0051-medium-01") == "medium"
    assert az.episode_tier("scene-0013-extreme-00") == "extreme"


# --- infrastructure-null path -------------------------------------------------------------

def test_collect_set_records_problems_on_missing_eval(tmp_path):
    entries = [("gone__off_r1", tmp_path / "gone" / "eval.json")]
    problems: list[str] = []
    rows = az.collect_hugsim_set(entries, problems)
    assert rows == [] and problems == ["missing-eval:gone__off_r1"]


def test_collect_set_records_problems_on_bad_nc(tmp_path):
    p = tmp_path / "bad__off_r1" / "eval.json"
    p.parent.mkdir()
    p.write_text(json.dumps({"nc": None, "ttc": 1.0, "hdscore": 0.1, "details": {}}))
    problems: list[str] = []
    rows = az.collect_hugsim_set([("bad__off_r1", p)], problems)
    assert rows == [] and len(problems) == 1 and problems[0].startswith("bad-eval:")


def test_paired_deltas_use_off_labels_only(tmp_path):
    off = write_eval(tmp_path, "scene-0001-easy-00__off_r1", nc_steps=[0.0], hdscore=0.2)
    write_eval(tmp_path, "scene-0001-easy-00__on_r1", nc_steps=[1.0], hdscore=0.6)
    problems: list[str] = []
    off_rows = az.collect_hugsim_set([("scene-0001-easy-00__off_r1", off)], problems)
    deltas = az.paired_deltas_iter48(tmp_path, off_rows, problems)
    assert problems == []
    assert deltas == [{"pair": "scene-0001-easy-00__r1",
                       "delta_hd": pytest.approx(0.4),
                       "off_primary_opportunity": True}]
