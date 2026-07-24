#!/usr/bin/env python3
"""gen-17 supply-chain replay gate for iteration-135 CI hardening.

Offline, deterministic, fail-closed. This re-derives the exact pinned identity of the CI
toolchain from repository bytes — the SHA-pinned GitHub Actions in the workflow and the
sha256 of each content-addressed dependency lock — and refuses any drift from the committed
manifest ``tools/ci/supply-chain-manifest.json``.

A green run is validation evidence, not authority. It does not prove upstream authenticity,
reproducible builds, or SLSA conformance; it proves the committed CI inputs match their
recorded content-addressed identities and that no workflow action has reverted to a mutable
tag.

Usage:
    python tools/ci/verify_supply_chain.py            # verify; exit 1 on any drift
    python tools/ci/verify_supply_chain.py --write    # (re)generate the manifest from bytes
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/ci.yml"
MANIFEST = ROOT / "tools/ci/supply-chain-manifest.json"
LOCKS = {
    "3.10": "tools/ci/requirements-ci-py310.lock",
    "3.11": "tools/ci/requirements-ci-py311.lock",
}
PINNED_ACTIONS = ("actions/checkout", "actions/setup-python")
_USES = re.compile(r"uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@(\S+)")
_SHA40 = re.compile(r"^[0-9a-f]{40}$")


class SupplyChainError(ValueError):
    """A supply-chain input could not be read or is structurally invalid."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def derive(root: Path) -> dict[str, Any]:
    """Re-derive the supply-chain identity from repository bytes under ``root``."""
    workflow_path = root / ".github/workflows/ci.yml"
    if not workflow_path.is_file():
        raise SupplyChainError("workflow ci.yml is absent")
    workflow_text = workflow_path.read_text("utf-8")

    actions: dict[str, str] = {}
    for owner_repo, ref in _USES.findall(workflow_text):
        if owner_repo in PINNED_ACTIONS:
            actions[owner_repo] = ref

    locks: dict[str, str] = {}
    for version, relative in LOCKS.items():
        lock_path = root / relative
        if not lock_path.is_file():
            raise SupplyChainError(f"lock is absent: {relative}")
        locks[version] = _sha256_bytes(lock_path.read_bytes())

    return {
        "schema": "sentinel.supply_chain_manifest.v1",
        "pinned_actions": actions,
        "lock_sha256": locks,
    }


def verify(root: Path) -> list[str]:
    """Return a sorted list of problem strings; empty means the manifest replays exactly."""
    problems: list[str] = []
    try:
        derived = derive(root)
    except SupplyChainError as exc:
        return [f"supply_chain:derive:{exc}"]

    # Every pinned action must be an exact 40-hex commit SHA, never a mutable tag.
    for owner_repo in PINNED_ACTIONS:
        ref = derived["pinned_actions"].get(owner_repo)
        if ref is None:
            problems.append(f"supply_chain:action_missing:{owner_repo}")
        elif not _SHA40.match(ref):
            problems.append(f"supply_chain:action_not_sha_pinned:{owner_repo}:{ref}")

    manifest_path = root / "tools/ci/supply-chain-manifest.json"
    if not manifest_path.is_file():
        problems.append("supply_chain:manifest_absent")
        return sorted(set(problems))
    try:
        committed = json.loads(manifest_path.read_text("utf-8"))
    except (OSError, ValueError) as exc:
        return sorted({*problems, f"supply_chain:manifest_unreadable:{type(exc).__name__}"})

    if committed != derived:
        problems.append("supply_chain:manifest_drift")
    return sorted(set(problems))


def _canonical(document: dict[str, Any]) -> str:
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="regenerate the manifest from bytes")
    args = parser.parse_args(argv)

    if args.write:
        MANIFEST.write_text(_canonical(derive(ROOT)), "utf-8")
        print(f"wrote {MANIFEST.relative_to(ROOT)}")
        return 0

    problems = verify(ROOT)
    if problems:
        print("SUPPLY_CHAIN_VERIFICATION_FAILED", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    print("SUPPLY_CHAIN_VERIFICATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
