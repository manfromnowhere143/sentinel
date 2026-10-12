"""Admit only the explicit inventory correction; never omit a real missing source."""

import copy
import json
from pathlib import Path

import pytest

from experiments.iter157_constrained_action_library.admission_repair import algorithm, repair_plan

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "experiments/iter157_constrained_action_library"


def fixture():
    return json.loads((BASE / "PLAN.json").read_text()), json.loads(
        (BASE / "ADMISSION_CORRECTION.json").read_text()
    )


def test_actual_frozen_inventory_and_algorithm():
    plan, correction = fixture()
    result = repair_plan(ROOT, plan, correction)
    assert len(result["source_files"]) == 38
    assert {k: v for k, v in result.items() if k != "source_files"} == {
        k: v for k, v in plan.items() if k != "source_files"
    }
    assert algorithm((BASE / "check.py").read_text()) == algorithm(
        (BASE / "corrected_check.py").read_text()
    )


@pytest.mark.parametrize(
    "kind", ["removal", "hash", "inventory", "missing_original", "missing_real", "untracked_real"]
)
def test_narrow_correction_refuses_expansion(kind, tmp_path):
    plan, correction = fixture()
    plan, correction = copy.deepcopy(plan), copy.deepcopy(correction)
    if kind == "removal":
        correction["removed_non_repository_paths"] += [plan["source_files"][-1]]
    elif kind == "hash":
        correction["original_plan_sha256"] = "0" * 64
    elif kind == "inventory":
        correction["remaining_source_files"].pop()
    elif kind == "missing_original":
        plan["source_files"].remove("_classes.py")
    elif kind in {"missing_real", "untracked_real"}:
        path = "not_a_frozen_source.py"
        plan["source_files"][-1] = path
        correction["remaining_source_files"][-1] = path
    with pytest.raises(ValueError):
        repair_plan(ROOT, plan, correction)


def test_algorithm_change_not_hidden_by_inventory_repair():
    original = (BASE / "check.py").read_text()
    altered = original.replace("certain > 100", "certain > 200")
    assert algorithm(original) != algorithm(altered)
