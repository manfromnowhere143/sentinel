"""Post-admission known-bads for the frozen exploratory artifact envelope."""

import json
from pathlib import Path
import shutil

import pytest
from experiments.iter193_history_delay import frontier_audit as audit

ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = [
    str(audit.BASE / "frontier_audit.py"),
    str(audit.BASE / "FRONTIER_AUDIT.md"),
    "tests/test_iter193_frontier_audit.py",
]


@pytest.mark.parametrize(
    "kind,error",
    [
        ("missing", "audit_raw_inventory"),
        ("extra", "audit_raw_inventory"),
        ("changed", "audit_raw_changed"),
        ("identity", "audit_execution_identity"),
        ("source", "audit_source_changed"),
        ("resource", "audit_producer_resources"),
    ],
)
def test_corrupt_envelope_rejected(tmp_path, monkeypatch, kind, error):
    original = ROOT / audit.OUTPUT
    folder = tmp_path / audit.OUTPUT
    shutil.copytree(original, folder)
    original_bytes = {
        str(p.relative_to(ROOT)): p.read_bytes() for p in original.rglob("*") if p.is_file()
    }
    for name in SOURCE_FILES:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    receipt = folder / "execution.json"
    if kind == "missing":
        (folder / "path/mask_000.bin").unlink()
    elif kind == "extra":
        (folder / "unexpected").write_bytes(b"extra")
    elif kind == "changed":
        (folder / "path/mask_000.bin").write_bytes(b"changed")
    elif kind == "source":
        (tmp_path / SOURCE_FILES[0]).write_bytes(b"changed")
    else:
        value = json.loads(receipt.read_text())
        value["primary_raw_commit" if kind == "identity" else "peak_rss_bytes"] = (
            "0" * 40 if kind == "identity" else 2**31
        )
        receipt.write_text(json.dumps(value))
        original_bytes[str(audit.OUTPUT / "execution.json")] = receipt.read_bytes()

    def git(root, command, *args):
        if command == "ls-tree":
            return ("\n".join(original_bytes) + "\n").encode()
        name = args[0].split(":", 1)[1]
        return original_bytes[name] if name in original_bytes else (ROOT / name).read_bytes()

    # Isolate artifact-envelope gates; the primary/runtime bindings have their own controls.
    monkeypatch.setattr(audit, "git", git)
    monkeypatch.setattr(audit, "bind_primary", lambda root: None)
    monkeypatch.setattr(audit, "verify", lambda root: None)
    with pytest.raises(ValueError, match=error):
        audit.check(tmp_path, "a" * 40)
