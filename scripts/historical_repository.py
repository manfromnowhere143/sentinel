"""Read-only validation of the archived Iter134/135 control contract.

The modern README describes later research. It cannot be used as the input to a
July point-in-time audit. This view has its own actual Git HEAD, index and files;
no probe is mocked, no accepted commit is rewritten, and no live-host observation
is inferred. Current source tests still run in the caller's checkout.
"""
from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import Iterator


HISTORICAL_COMMIT = "8c118b74c699bf0f139f9bd659192bad06b895f8"
CANONICAL_REMOTE = "https://github.com/manfromnowhere143/sentinel.git"


def git(repo: Path, *args: str) -> bytes:
    return subprocess.check_output(
        ["git", "-c", "core.hooksPath=/dev/null", "-C", str(repo), *args],
        stderr=subprocess.PIPE, timeout=60,
    )


@contextmanager
def historical_repository(repo: Path) -> Iterator[Path]:
    """Materialize the declared immutable view, without copying large run logs."""
    repo = repo.resolve()
    git(repo, "cat-file", "-e", f"{HISTORICAL_COMMIT}^{{commit}}")
    with TemporaryDirectory(prefix="sentinel-historical-contract-") as directory:
        view = Path(directory) / "repository"
        subprocess.run(
            ["git", "-c", "core.hooksPath=/dev/null", "clone", "--shared", "--no-checkout",
             str(repo), str(view)], check=True, capture_output=True, timeout=60,
        )
        # Sparse materialization affects only checkout cost. The complete original
        # Git objects remain available, including all large evidence and history.
        paths = []
        for line in git(view, "ls-tree", "-rl", HISTORICAL_COMMIT).decode().splitlines():
            metadata, path = line.split("\t", 1)
            if int(metadata.split()[3]) <= 1024 * 1024:
                paths.append("/" + path)
        git(view, "config", "core.sparseCheckout", "true")
        git(view, "config", "core.sparseCheckoutCone", "false")
        (view / ".git/info/sparse-checkout").write_text("\n".join(paths) + "\n")
        git(view, "checkout", "-B", "master", HISTORICAL_COMMIT)
        git(view, "update-ref", "refs/remotes/origin/master", HISTORICAL_COMMIT)
        git(view, "remote", "set-url", "origin", CANONICAL_REMOTE)
        if git(view, "status", "--porcelain=v1"):
            raise ValueError("historical materialization is not clean")
        if git(view, "rev-parse", "HEAD").decode().strip() != HISTORICAL_COMMIT:
            raise ValueError("historical revision mismatch")
        yield view


def archived_state_errors(repo: Path) -> list[str]:
    """Verify archived bytes and run the original validator at its original scope."""
    expected = git(repo, "show", f"{HISTORICAL_COMMIT}:MISSION_STATE.json")
    if (repo / "MISSION_STATE.json").read_bytes() != expected:
        return ["historical mission bytes changed; declare and validate a new contract"]
    with historical_repository(repo) as view:
        command = (
            "import json,sys;sys.path.insert(0,'scripts');"
            "from mission_state import load_state,validate_state;"
            "print(json.dumps(validate_state(load_state())))"
        )
        result = subprocess.run(
            [sys.executable, "-I", "-B", "-S", "-c", command], cwd=view,
            check=True, capture_output=True, text=True, timeout=120,
        )
        return json.loads(result.stdout)
