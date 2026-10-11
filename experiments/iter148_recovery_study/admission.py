"""Study admission from bound evidence and a complete ordered receipt chain."""

from pathlib import Path
import hashlib
import re
from experiments.iter147_full_horizon_execution.protocol import plan, identity
from experiments.iter147_full_horizon_execution.coordinator import read, record
from experiments.iter145_constrained_execution.resources import file_identity

BASE = "experiments/iter148_recovery_study"
GIB = 1024**3


def study_plan(root):
    return plan(root, "study")


def validate_plan(root, document):
    if identity(document) != identity(study_plan(root)):
        raise ValueError("study_plan_changed")
    return document


def verify_inputs(root):
    root = Path(root)
    manifest = read(root / BASE / "INPUTS.json")
    for name, expected in manifest["files"].items():
        if name.startswith("/") or ".." in Path(name).parts:
            raise ValueError("input_path")
        actual = file_identity(root / name, max_bytes=16 * 1024**2, allow_empty=True)
        if actual != expected:
            raise ValueError("qualified_input_changed:" + name)
    return identity(manifest)


def basis(root):
    digest = verify_inputs(root)
    receipt = read(Path(root) / BASE / "QUALIFICATION.json")
    expected = dict(
        status="supported",
        inputs_sha256=digest,
        iter147_pairs=4,
        iter147_steps=912,
        iter146_pairs=4,
        iter146_steps=192,
        raw_before_replay=True,
    )
    if identity(receipt) != identity(expected):
        raise ValueError("qualification_receipt")
    return identity(receipt)


def history(document, receipts, pair):
    if (
        type(receipts) is not list
        or type(pair) is not int
        or not 0 <= pair <= 56
        or len(receipts) != pair
    ):
        raise ValueError("pair_order")
    previous = None
    for index, receipt in enumerate(receipts):
        if (
            receipt.get("status") != "supported"
            or type(receipt.get("pair")) is not int
            or receipt["pair"] != index
            or receipt.get("plan_sha256") != identity(document)
            or receipt.get("previous_receipt_sha256") != previous
        ):
            raise ValueError("unadmitted_history")
        for field, width in (("raw_commit", 40), ("raw_inventory_sha256", 64)):
            if not isinstance(receipt.get(field), str) or not re.fullmatch(
                "[0-9a-f]{" + str(width) + "}", receipt[field]
            ):
                raise ValueError("history_identity")
        if index % 4 == 3 and receipt.get("scenario_comparison_status") != "supported":
            raise ValueError("scenario_comparison_missing")
        previous = identity(receipt)
    return previous


def claim(root, control, document, pair, receipts, qualification_sha256, block):
    validate_plan(root, document)
    if basis(root) != qualification_sha256:
        raise ValueError("qualification_binding")
    if type(block) is not int or not 0 <= block < 14 or type(pair) is not int or pair // 4 != block:
        raise ValueError("execution_block")
    previous = history(document, receipts, pair)
    control = Path(control)
    # All previous starts must still exist: a new directory cannot erase initialized work.
    observed = sorted(p.name for p in control.glob("pair_*_started.json"))
    expected = [f"pair_{i:03d}_started.json" for i in range(pair)]
    if observed != expected:
        raise ValueError("initialized_history")
    for i in range(pair):
        started = read(control / f"pair_{i:03d}_started.json")
        expected_start = dict(
            pair=i,
            block=i // 4,
            plan_sha256=identity(document),
            previous_receipt_sha256=identity(receipts[i - 1]) if i else None,
            qualification_sha256=qualification_sha256,
        )
        if identity(started) != identity(expected_start):
            raise ValueError("started_receipt_changed")
        completed_pair(control, document, i)
    record(
        control / f"pair_{pair:03d}_started.json",
        dict(
            pair=pair,
            block=block,
            plan_sha256=identity(document),
            previous_receipt_sha256=previous,
            qualification_sha256=qualification_sha256,
        ),
    )
    return document["slots"][pair * 2 : pair * 2 + 2]


def local_capacity(free_bytes):
    if type(free_bytes) is not int or free_bytes < 17 * GIB:
        raise ValueError("local_collection_reserve")
    return True


def remaining_budget(seconds):
    import math

    if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds <= 2600:
        raise ValueError("pair_time_reserve")
    return True


def committed_file(repository, commit, path):
    import subprocess

    if not isinstance(commit, str) or not re.fullmatch("[0-9a-f]{40}", commit):
        raise ValueError("git_identity")
    path = Path(path)
    actual = file_identity(path, max_bytes=16 * 1024**2, include_bytes=True)
    expected = subprocess.check_output(
        ["git", "show", commit + ":" + path.relative_to(repository).as_posix()], cwd=repository
    )
    if actual["sha256"] != hashlib.sha256(expected).hexdigest():
        raise ValueError("receipt_not_committed")
    return actual["data"]


def completed_pair(directory, document, pair):
    receipt = read(Path(directory) / f"pair_{pair:03d}_result.json")
    if (
        receipt.get("status") != "completed"
        or type(receipt.get("pair")) is not int
        or receipt["pair"] != pair
        or receipt.get("plan_sha256") != identity(document)
        or len(receipt.get("cases", [])) != 2
    ):
        raise ValueError("parent_pair_incomplete")
    for row, slot in zip(receipt["cases"], document["slots"][pair * 2 : pair * 2 + 2]):
        if (
            identity(row.get("slot")) != identity(slot)
            or type(row.get("returncode")) is not int
            or row["returncode"] != 0
            or row.get("deadline_exceeded") is not False
            or row.get("cleanup") != {"status": "absent"}
        ):
            raise ValueError("parent_worker_failure")
    return receipt
