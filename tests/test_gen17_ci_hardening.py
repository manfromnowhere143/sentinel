"""Known-bad controls for the gen-17 content-addressed CI hardening.

Every gate carries a proof that it fires (Law 11). The supply-chain replay gate
``tools/ci/verify_supply_chain.py`` must refuse each drift class below, and must pass on the
exact committed bytes. These tests are offline and deterministic; they mutate copies in a
temporary tree and never touch the real workflow or GitHub.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO / "tools/ci/verify_supply_chain.py"
MIRROR_FILES = (
    ".github/workflows/ci.yml",
    "tools/ci/requirements-ci-py310.lock",
    "tools/ci/requirements-ci-py311.lock",
    "tools/ci/supply-chain-manifest.json",
)
CHECKOUT_SHA = "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"


def _load_module():
    spec = importlib.util.spec_from_file_location("verify_supply_chain", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


sc = _load_module()


def _mirror(root: Path) -> Path:
    for relative in MIRROR_FILES:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((REPO / relative).read_bytes())
    return root


def test_real_repository_supply_chain_replays_clean() -> None:
    assert sc.verify(REPO) == []


def test_positive_control_mirror_is_clean(tmp_path: Path) -> None:
    assert sc.verify(_mirror(tmp_path)) == []


def test_mutable_action_tag_is_refused(tmp_path: Path) -> None:
    root = _mirror(tmp_path)
    workflow = root / ".github/workflows/ci.yml"
    workflow.write_text(workflow.read_text("utf-8").replace(CHECKOUT_SHA, "actions/checkout@v4"))
    problems = sc.verify(root)
    assert any("action_not_sha_pinned:actions/checkout" in problem for problem in problems)


def test_lock_edit_is_refused(tmp_path: Path) -> None:
    root = _mirror(tmp_path)
    lock = root / "tools/ci/requirements-ci-py311.lock"
    lock.write_text(lock.read_text("utf-8") + "\n# tampered\n")
    assert "supply_chain:manifest_drift" in sc.verify(root)


def test_missing_manifest_is_refused(tmp_path: Path) -> None:
    root = _mirror(tmp_path)
    (root / "tools/ci/supply-chain-manifest.json").unlink()
    assert "supply_chain:manifest_absent" in sc.verify(root)


def test_missing_action_is_refused(tmp_path: Path) -> None:
    root = _mirror(tmp_path)
    workflow = root / ".github/workflows/ci.yml"
    kept = [line for line in workflow.read_text("utf-8").splitlines() if "setup-python@" not in line]
    workflow.write_text("\n".join(kept) + "\n")
    problems = sc.verify(root)
    assert any("action_missing:actions/setup-python" in problem for problem in problems)


def test_locks_are_hash_pinned_and_fully_pinned() -> None:
    for relative in ("tools/ci/requirements-ci-py310.lock", "tools/ci/requirements-ci-py311.lock"):
        text = (REPO / relative).read_text("utf-8")
        assert "--hash=sha256:" in text
        requirement_lines = [
            line
            for line in text.splitlines()
            if line and not line.startswith((" ", "\t", "#", "-"))
        ]
        assert requirement_lines, relative
        assert all("==" in line for line in requirement_lines), relative
