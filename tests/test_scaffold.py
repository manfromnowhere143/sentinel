"""Scaffold smoke test — keeps CI green from day one; real engine/method tests land per iteration."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_preregistration_frozen():
    """The pre-registered target + win bar must exist before any result."""
    pre = (ROOT / "PREREGISTRATION.md").read_text()
    assert "NeuroNCAP" in pre and "frozen" in pre.lower()


def test_architecture_documented():
    assert (ROOT / "docs" / "ARCHITECTURE.md").exists()
