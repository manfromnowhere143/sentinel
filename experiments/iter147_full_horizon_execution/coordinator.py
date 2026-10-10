"""Append-only pair lifecycle: initialized work cannot be silently retried or skipped."""

from pathlib import Path
import subprocess
from experiments.iter146_route_outcome_contract.check import strict
from experiments.iter145_constrained_execution.resources import file_identity
from .protocol import identity, encoded, validate


def read(path):
    return strict(file_identity(Path(path), max_bytes=4 * 1024**2, include_bytes=True)["data"])


def record(path, value):
    with Path(path).open("xb") as f:
        f.write(encoded(value) + b"\n")


def claim(root, control, document, pair, previous=None):
    validate(root, document)
    if type(pair) is not int or not 0 <= pair < len(document["slots"]) // 2:
        raise ValueError("pair_index")
    if pair:
        if (
            previous is None
            or previous.get("status") != "supported"
            or previous.get("pair") != pair - 1
            or previous.get("plan_sha256") != identity(document)
        ):
            raise ValueError("previous_pair_not_admitted")
        for key, width in (("raw_commit", 40), ("raw_inventory_sha256", 64)):
            value = previous.get(key)
            if (
                not isinstance(value, str)
                or len(value) != width
                or any(c not in "0123456789abcdef" for c in value)
            ):
                raise ValueError("prior_raw_identity")
    elif previous is not None:
        raise ValueError("unexpected_previous_pair")
    control = Path(control)
    # Parent initialization is exclusive before any worker, including preflight failures.
    record(
        control / f"pair_{pair:03d}_started.json",
        dict(pair=pair, plan_sha256=identity(document), previous=previous),
    )
    return document["slots"][pair * 2 : pair * 2 + 2]


def raw_identity(repository, commit, directory):
    if (
        not isinstance(commit, str)
        or len(commit) != 40
        or any(c not in "0123456789abcdef" for c in commit)
    ):
        raise ValueError("raw_commit")
    repository, directory = Path(repository).resolve(), Path(directory).absolute()
    records = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError("raw_symlink")
        if path.is_file():
            relative = path.relative_to(repository).as_posix()
            actual = file_identity(path, max_bytes=256 * 1024**2, allow_empty=True)
            committed = subprocess.check_output(
                ["git", "show", commit + ":" + relative], cwd=repository
            )
            import hashlib

            if actual["sha256"] != hashlib.sha256(committed).hexdigest() or actual["bytes"] != len(
                committed
            ):
                raise ValueError("raw_not_committed:" + relative)
            records[relative] = actual
    if not records:
        raise ValueError("missing_raw")
    return identity(records)
