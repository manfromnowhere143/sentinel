"""One-shot ordered coordinator; raw commit identity is returned, never guessed."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess

ARMS = ("reference_b", "nominal_a", "nominal_b")
BRANCH = "research/iter142-nominal-continuation"


def candidate(repo, branch, source):
    if not isinstance(branch, str) or not branch.startswith("research/"):
        raise ValueError("candidate branch")
    if not isinstance(source, str) or not re.fullmatch("[0-9a-f]{40}", source):
        raise ValueError("source commit identity")
    tip = (
        subprocess.check_output(
            ["git", "rev-parse", "--verify", "refs/heads/" + branch + "^{commit}"], cwd=repo
        )
        .decode()
        .strip()
    )
    subprocess.run(["git", "merge-base", "--is-ancestor", source, tip], cwd=repo, check=True)
    return tip


def commit_identity(value):
    if not isinstance(value, str) or not re.fullmatch("[0-9a-f]{40}", value):
        raise ValueError("raw commit identity")
    return value


def admitted(arm, report):
    if not isinstance(report, dict) or report.get("status") != "validated":
        raise ValueError("missing or failed verification")
    if arm == "reference_b" and report.get("verdict") != "REPLAY_MATCHED":
        raise ValueError("reference pair not admitted")
    if arm.startswith("nominal_") and report.get("prefix") != "matched":
        raise ValueError("nominal prefix not admitted")
    if arm == "nominal_b" and report.get("nominal_replica", {}).get("prefix") != "matched":
        raise ValueError("nominal pair not admitted")


def run_schedule(directory, source, backend, branch=BRANCH):
    """Backend supplies bounded operations. Any error leaves the start marker in place."""
    directory = Path(directory)
    backend.preflight(branch, source)
    directory.mkdir(parents=True, exist_ok=True)
    marker = directory / "schedule_started.json"
    with marker.open("x") as f:
        json.dump(dict(branch=branch, source_commit=source, arms=ARMS), f)
        f.flush()
        os.fsync(f.fileno())
    reports = {}
    with (directory / "events.jsonl").open("x") as events:

        def event(kind, **data):
            events.write(json.dumps(dict(kind=kind, **data), sort_keys=True) + "\n")
            events.flush()
            os.fsync(events.fileno())

        arm = None
        try:
            for arm in ARMS:
                event("launch_requested", arm=arm)
                backend.launch(arm)
                result = backend.wait(arm)
                # Failed completed processes still have their raw/partial evidence retained.
                backend.collect(arm)
                commit = commit_identity(backend.commit(arm))
                backend.check_commit(commit, arm)
                event("raw_committed", arm=arm, raw_commit=commit)
                if not isinstance(result, dict) or result.get("returncode") != 0:
                    raise ValueError("episode failed or completion missing")
                report = backend.verify(arm)
                admitted(arm, report)
                reports[arm] = report
                event("validated", arm=arm, raw_commit=commit)
            event("schedule_complete")
        except Exception as exc:
            event("failed", arm=arm, error_type=type(exc).__name__, error=str(exc)[:2000])
            raise
    return reports


def committed_files(repo, commit, directory, records):
    import hashlib
    from pathlib import PurePosixPath

    commit_identity(commit)
    if not records:
        raise ValueError("empty raw inventory")
    for name, record in records.items():
        path = PurePosixPath(directory) / name
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("raw inventory path")
        raw = subprocess.check_output(["git", "show", commit + ":" + str(path)], cwd=repo)
        if len(raw) != record["bytes"] or hashlib.sha256(raw).hexdigest() != record["sha256"]:
            raise ValueError("raw commit content mismatch")
