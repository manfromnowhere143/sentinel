"""Exercise archive -> exact Git bytes -> scientific replay -> receipt without cloud access."""

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from .admission import BASE, history
from .collection import extract
from .execute import commit
from .records import read, record
from .replay import admit


def rehearse(repository):
    repository = Path(repository).resolve()
    base = repository / BASE
    block = base / "proof/block_000"
    document = read(base / "STUDY_PLAN.json")
    original = read(base / "proof/admissions/pair_000.json")
    with tempfile.TemporaryDirectory(prefix="sentinel151-retention-") as name:
        root = Path(name).resolve()
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        for key, value in (("user.name", "Fixture"), ("user.email", "fixture@example.invalid")):
            subprocess.run(["git", "config", key, value], cwd=root, check=True)
        destination = root / BASE / "proof/study_raw/pair_000"
        extract(
            block / "pair_000_raw.tar.gz", destination, read(block / "pair_000_collection.json")
        )
        captured = destination / "e2e147.py"
        before = captured.read_bytes()
        raw_commit = commit(root, [destination], "Retain actual captured bytes before replay")
        raw = subprocess.check_output(
            ["git", "show", raw_commit + ":" + captured.relative_to(root).as_posix()], cwd=root
        )
        if raw != before:
            raise ValueError("captured_bytes_changed")
        whitespace = subprocess.run(
            ["git", "show", "--check", raw_commit], cwd=root, capture_output=True, text=True
        )
        if whitespace.returncode == 0:
            raise ValueError("missing_regression_trigger")
        receipt = admit(root, destination, document, 0, raw_commit, [], destination.parent)
        if (
            receipt["raw_inventory_sha256"] != original["raw_inventory_sha256"]
            or receipt["steps"] != original["steps"]
        ):
            raise ValueError("replay_changed")
        directory = root / BASE / "proof/admissions"
        directory.mkdir()
        record(directory / "pair_000.json", receipt)
        receipt_commit = commit(root, [directory], "Retain admitted fixture receipt")
        history(document, [receipt], 1)
        return dict(
            status="supported",
            scope="local replay of the same two retained episodes; zero new outcomes",
            archive_sha256=read(block / "pair_000_collection.json")["sha256"],
            captured_client_sha256=hashlib.sha256(raw).hexdigest(),
            captured_client_bytes_preserved=True,
            legacy_whitespace_check_returncode=whitespace.returncode,
            raw_inventory_sha256=receipt["raw_inventory_sha256"],
            replayed_actions=receipt["steps"],
            raw_commit=raw_commit,
            receipt_commit=receipt_commit,
            ephemeral_git_commits=True,
            source_sha256=hashlib.sha256((base / "execute.py").read_bytes()).hexdigest(),
            cloud_access=False,
        )


if __name__ == "__main__":
    print(json.dumps(rehearse(Path.cwd()), indent=2))
