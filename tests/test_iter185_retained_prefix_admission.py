"""Complete production metadata readers and constructed admission/rejection path."""

import copy
import json
from pathlib import Path
import time

import pytest

from experiments.iter185_retained_prefix_admission import context, qualify
from experiments.iter185_retained_prefix_admission.common import BASE, document, encode, sha
from tests.test_iter169_full_horizon_control import OLD

ROOT = Path(__file__).resolve().parents[1]


def metadata(monkeypatch):
    plan = document(ROOT, BASE / "PLAN.json")
    manifest = document(ROOT, BASE / "RUNTIME.json")
    monkeypatch.setattr(context, "runtime_identity", lambda: manifest["python_runtime"])
    return plan


def test_all_actual_metadata_reader_inputs(monkeypatch):
    plan = metadata(monkeypatch)
    values, rows = context.metadata(ROOT, plan)
    assert len(rows) == 12 and set(values) == set(context.names())
    assert {r["path"] for r in rows if not r["canonical"]} == context.LEGACY
    assert values[context.OLD] == OLD


@pytest.mark.parametrize(
    "name",
    [
        context.OLD,
        context.PRIOR + "RUNTIME.json",
        context.PRIOR + "proof/audit_retry_raw/paths.json",
    ],
)
def test_bound_metadata_changes_rejected_before_parse(monkeypatch, name):
    plan = metadata(monkeypatch)
    read = context.read
    monkeypatch.setattr(
        context,
        "read",
        lambda root, path: read(root, path) + b" " if str(path) == name else read(root, path),
    )
    with pytest.raises(ValueError, match="metadata_hash"):
        context.metadata(ROOT, plan)


def test_missing_metadata_input_rejected(monkeypatch):
    plan = metadata(monkeypatch)
    plan["metadata_files"].pop(context.OLD)
    with pytest.raises(ValueError, match="metadata_inventory"):
        context.metadata(ROOT, plan)


def test_noncanonical_new_record_still_rejected(monkeypatch):
    plan = metadata(monkeypatch)
    name = context.PRIOR + "proof/audit_retry_raw/initialized.json"
    read = context.read
    changed = json.dumps(json.loads(read(ROOT, name)), indent=2).encode()
    plan["metadata_files"][name] = sha(changed)
    monkeypatch.setattr(
        context, "read", lambda root, path: changed if str(path) == name else read(root, path)
    )
    with pytest.raises(ValueError, match="canonical_metadata"):
        context.metadata(ROOT, plan)


def test_legacy_parser_remains_structurally_strict(monkeypatch):
    plan = metadata(monkeypatch)
    name = context.PRIOR + "RUNTIME.json"
    read = context.read
    changed = b'{"x":1,"x":2}\n'
    plan["metadata_files"][name] = sha(changed)
    monkeypatch.setattr(
        context, "read", lambda root, path: changed if str(path) == name else read(root, path)
    )
    with pytest.raises(ValueError):
        context.metadata(ROOT, plan)


def test_runtime_version_mismatch_rejected(monkeypatch):
    plan = metadata(monkeypatch)
    monkeypatch.setattr(context, "runtime_identity", lambda: {})
    with pytest.raises(ValueError, match="checker_runtime"):
        context.metadata(ROOT, plan)


def test_full_metadata_then_constructed_replay_entrypoint(tmp_path, monkeypatch):
    plan = metadata(monkeypatch)
    values, inventory = context.metadata(ROOT, plan)
    controls = qualify.controlled_replay(
        tmp_path / "constructed", values[context.OLD], time.monotonic() + 60
    )
    result = dict(status="supported", source_commit="a" * 40, metadata=inventory, controls=controls)
    execution = dict(
        source_commit="a" * 40,
        stage="qualification",
        actual_metadata_inputs=12,
        constructed_paths=2,
        rejected_corruptions=5,
        retained_scalar_states=0,
        conditional_searches=0,
    )
    qualify.validate_result(result, execution, "a" * 40, inventory)
    assert len(controls["rejected"]) == 5
    for key in [
        "source_commit",
        "stage",
        "actual_metadata_inputs",
        "constructed_paths",
        "rejected_corruptions",
        "retained_scalar_states",
        "conditional_searches",
    ]:
        changed = copy.deepcopy(execution)
        changed[key] = "wrong" if isinstance(changed[key], str) else changed[key] + 1
        with pytest.raises(ValueError, match="qualification_"):
            qualify.validate_result(result, changed, "a" * 40, inventory)
    for field in ["rejected", "positive"]:
        changed = copy.deepcopy(result)
        if field == "rejected":
            changed["controls"][field].pop()
        else:
            changed["controls"][field]["selected_roots"] = 2
        with pytest.raises(ValueError, match="qualification_"):
            qualify.validate_result(changed, execution, "a" * 40, inventory)


@pytest.mark.parametrize(
    "field,value",
    [
        ("remaining_attempts", [7386, 5465, 3929]),
        ("seeds", [1, 2, 3]),
        ("original_wall_seconds", 0),
        ("retained_raw_commit", "0" * 40),
        ("producer_source_commit", "0" * 40),
    ],
)
def test_scientific_schedule_and_provenance_unchanged(field, value):
    plan = document(ROOT, BASE / "PLAN.json")
    context.check_plan(plan)
    plan[field] = value
    with pytest.raises(ValueError, match="fixed_contract"):
        context.check_plan(plan)


def test_new_runtime_manifest_preserves_exact_values():
    historical = (ROOT / context.PRIOR / "RUNTIME.json").read_bytes()
    canonical = (ROOT / BASE / "RUNTIME.json").read_bytes()
    assert historical != canonical and json.loads(historical) == json.loads(canonical)
    assert encode(json.loads(canonical)) == canonical
