"""Exact new-plan admission; historical scientific validators are left unchanged."""

import math
from pathlib import Path

from experiments.iter149_observation_recovery.recovery import digest, encode
from experiments.iter150_cloud_observation.native import file
from .records import read, record

BASE = "experiments/iter154_full_scene_maneuver"
PLAN = "0a11a0efad0ee1a2389ec777d558bbdd7b1f51d361189d9e682851c14cbc2629"


def identity(value):
    return digest(encode(value))


def validate_plan(document):
    if identity(document) != PLAN:
        raise ValueError("canary_plan_changed")
    return document


def basis(root):
    root = Path(root)
    manifest = read(root / BASE / "INPUTS.json")
    for name, expected in manifest["files"].items():
        if file(root, name, 16 * 1024**2) != expected:
            raise ValueError("qualified_input_changed:" + name)
    receipt = read(root / BASE / "QUALIFICATION.json")
    if (
        receipt.get("status") != "supported"
        or receipt.get("inputs_sha256") != identity(manifest)
        or receipt.get("plan_sha256") != PLAN
        or receipt.get("scientific_outcomes") != 0
    ):
        raise ValueError("qualification_binding")
    return identity(receipt)


def history(document, receipts, pair):
    validate_plan(document)
    if type(pair) is not int or pair != 0 or receipts != []:
        raise ValueError("pair_order")
    return identity(document["historical_comparator"])


def remaining(deadline, now):
    if (
        any(type(v) not in (int, float) or not math.isfinite(v) for v in (deadline, now))
        or deadline - now <= 2800
    ):
        raise ValueError("pair_time_reserve")


def claim(root, control, document, pair, receipts, qualification, block, manifest):
    validate_plan(document)
    if type(block) is not int or block != 0:
        raise ValueError("execution_block")
    previous = history(document, receipts, pair)
    if basis(root) != qualification:
        raise ValueError("qualification_binding")
    control = Path(control)
    if list(control.glob("pair_*_started.json")):
        raise ValueError("initialized_history")
    record(
        control / "pair_000_started.json",
        dict(
            pair=0,
            block=0,
            plan_sha256=PLAN,
            previous_receipt_sha256=previous,
            qualification_sha256=qualification,
            manifest_sha256=manifest,
        ),
    )
    return document["slots"]
