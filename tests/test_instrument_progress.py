"""Corruption controls for automatic presentation admission; no research execution."""
import copy
import json
import subprocess
from pathlib import Path

import pytest

from scripts.instrument_progress import export

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    descriptor = json.loads(subprocess.check_output(["git", "-C", str(ROOT), "show", "76545d92dd523b543fd281353e114c4ba7adfffb:instrument/progress.json"]))
    commit = descriptor["evidenceCommit"]
    files = {}

    def read(path):
        if path not in files:
            files[path] = subprocess.check_output(["git", "-C", str(ROOT), "show", f"{commit}:{path}"])
        return files[path]

    return descriptor, files, read


def test_export_retains_unknowns_and_archive():
    descriptor, _, read = fixture()
    packet = export(descriptor, read, "2026-10-12T00:00:00Z")
    assert packet["iteration"] == 156
    assert len(packet["records"]) == 163
    assert [x["value"] for x in packet["metrics"]] == [115, 276519, 300, 0]
    assert [x["value"] for x in packet["breakdown"]] == [26, 266, 8]
    assert packet["status"] == "supported"
    assert "unknown" in packet["boundary"]


@pytest.mark.parametrize("kind", ["open", "wrong_iteration", "status", "identity", "missing", "null", "float", "negative", "disagreement", "path", "html", "archive"])
def test_corruptions_refused(kind):
    descriptor, files, read = fixture()
    descriptor = copy.deepcopy(descriptor)
    path = descriptor["directory"] + "/STATE.json"
    state = json.loads(read(path))
    if kind == "open":
        state["phase"] = "running"
    elif kind == "wrong_iteration":
        state["iteration"] = 157
    elif kind == "status":
        state["status"] = "failed"
    elif kind == "identity":
        state["raw_commit"] = "0" * 40
    elif kind == "missing":
        del state["unique_states"]
    elif kind in {"null", "float", "negative", "disagreement"}:
        state["unique_states"] = {"null": None, "float": 115.0, "negative": -1, "disagreement": 116}[kind]
    elif kind == "path":
        descriptor["directory"] += "/../other"
    elif kind == "html":
        descriptor["summary"] = "<script>claim()</script>"
    elif kind == "archive":
        files["README.md"] = b"# Incomplete archive\n"
    files[path] = json.dumps(state).encode()
    with pytest.raises((ValueError, KeyError)):
        export(descriptor, read, "2026-10-12T00:00:00Z")


def test_current_descriptor_covers_closed_research():
    # Adding a new closed result requires its display contract in the same change.
    descriptor = json.loads((ROOT / "instrument/progress.json").read_text())
    results = list((ROOT / "experiments").glob("iter*/RESULT.md"))
    import re
    latest = max(int(re.match(r"iter(\d+)", p.parent.name)[1]) for p in results)
    assert descriptor["iteration"] == latest
    descriptor["evidenceCommit"] = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"]).decode().strip()
    def read(path):
        target = ROOT / path
        if target.is_dir():
            return subprocess.check_output(["git", "-C", str(ROOT), "show", "HEAD:" + path])
        return target.read_bytes()
    export(descriptor, read, "2026-10-12T00:00:00Z")
