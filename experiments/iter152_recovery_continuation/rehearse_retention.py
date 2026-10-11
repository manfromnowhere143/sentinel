"""Real captured bytes through the new commit helper and original scientific replay."""

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from experiments.iter151_recovery_canary.replay import admit as historical_admit
from .admission import BASE
from .collection import extract
from .execute import commit
from .records import read, record
from .baseline import verify


def rehearse(repository):
    repository = Path(repository).resolve()
    historical = verify(repository)
    block = repository / "experiments/iter151_recovery_canary/proof/block_000"
    with tempfile.TemporaryDirectory(prefix="sentinel152-retention-") as name:
        root = Path(name).resolve()
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        for key, value in (("user.name", "Fixture"), ("user.email", "fixture@example.invalid")):
            subprocess.run(["git", "config", key, value], cwd=root, check=True)
        destination = root / BASE / "proof/historical_fixture"
        binding = read(block / "pair_000_collection.json")
        extract(block / "pair_000_raw.tar.gz", destination, binding)
        captured = destination / "e2e147.py"
        original = captured.read_bytes()
        raw_commit = commit(root, [destination], "Preserve original captured fixture bytes")
        committed = subprocess.check_output(
            ["git", "show", raw_commit + ":" + captured.relative_to(root).as_posix()], cwd=root
        )
        if original != committed:
            raise ValueError("retention_changed_bytes")
        whitespace = subprocess.run(
            ["git", "show", "--check", raw_commit], cwd=root, capture_output=True
        )
        if whitespace.returncode == 0:
            raise ValueError("missing_regression_trigger")
        receipt = historical_admit(
            root,
            destination,
            read(destination / "plan.json"),
            0,
            raw_commit,
            [],
            destination.parent,
        )
        if receipt["steps"] != sum(r["steps"] for r in historical):
            raise ValueError("replay_changed")
        receipt_path = root / BASE / "proof/historical_fixture_receipt.json"
        record(receipt_path, receipt)
        receipt_commit = commit(root, [receipt_path], "Commit historical fixture admission")
        return dict(
            status="supported",
            scientific_outcomes=0,
            cloud_access=False,
            scope="New retention helper; original historical scientific contract and episode IDs.",
            continuation_admission_scope="Separately tested seven-pair chain; no new live outcome.",
            replayed_actions=receipt["steps"],
            captured_bytes_preserved=True,
            archive_sha256=binding["sha256"],
            captured_client_sha256=hashlib.sha256(original).hexdigest(),
            legacy_whitespace_check_returncode=whitespace.returncode,
            raw_commit=raw_commit,
            receipt_commit=receipt_commit,
            ephemeral_git_commits=True,
        )


if __name__ == "__main__":
    print(json.dumps(rehearse(Path.cwd()), indent=2))
