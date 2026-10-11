"""Exact new-plan admission; historical scientific validators are left unchanged."""

import math
from pathlib import Path
import re

from experiments.iter149_observation_recovery.recovery import digest, encode
from experiments.iter150_cloud_observation.native import file
from .records import read, record

BASE = "experiments/iter152_recovery_continuation"
PLAN = "e624a85b84e732ae0481a72819d3e992e55b6c14bff798527f591b89f4205dfa"


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
    if (
        type(pair) is not int
        or not 0 <= pair <= 7
        or type(receipts) is not list
        or len(receipts) != pair
    ):
        raise ValueError("pair_order")
    previous = identity(document["historical_comparator"])
    for index, receipt in enumerate(receipts):
        if (
            receipt.get("status") != "supported"
            or type(receipt.get("pair")) is not int
            or receipt["pair"] != index
            or receipt.get("plan_sha256") != PLAN
            or receipt.get("previous_receipt_sha256") != previous
            or receipt.get("replica_check") != "supported"
            or receipt.get("historical_comparator_sha256")
            != identity(document["historical_comparator"])
            or receipt.get("historical_slots_counted_as_new") != 0
        ):
            raise ValueError("unadmitted_history")
        for key, width in (("raw_commit", 40), ("raw_inventory_sha256", 64)):
            if not isinstance(receipt.get(key), str) or not re.fullmatch(
                "[0-9a-f]{" + str(width) + "}", receipt[key]
            ):
                raise ValueError("history_identity")
        if index in (2, 6) and receipt.get("scenario_comparison_status") != "supported":
            raise ValueError("scenario_comparison_missing")
        previous = identity(receipt)
    return previous


def remaining(deadline, now):
    if (
        any(type(v) not in (int, float) or not math.isfinite(v) for v in (deadline, now))
        or deadline - now <= 2800
    ):
        raise ValueError("pair_time_reserve")


def claim(root, control, document, pair, receipts, qualification, block, manifest):
    validate_plan(document)
    if (
        type(pair) is not int
        or not 0 <= pair < 7
        or type(block) is not int
        or block != (0 if pair < 3 else 1)
    ):
        raise ValueError("execution_block")
    if basis(root) != qualification:
        raise ValueError("qualification_binding")
    previous = history(document, receipts, pair)
    control = Path(control)
    if sorted(p.name for p in control.glob("pair_*_started.json")) != [
        f"pair_{i:03d}_started.json" for i in range(pair)
    ]:
        raise ValueError("initialized_history")
    from experiments.iter148_recovery_study.admission import completed_pair

    for i in range(pair):
        marker = read(control / f"pair_{i:03d}_started.json")
        expected = dict(
            pair=i,
            block=0 if i < 3 else 1,
            plan_sha256=PLAN,
            previous_receipt_sha256=identity(receipts[i - 1])
            if i
            else identity(document["historical_comparator"]),
            qualification_sha256=qualification,
            manifest_sha256=manifest,
        )
        if identity(marker) != identity(expected):
            raise ValueError("started_receipt_changed")
        completed_pair(control, document, i)
    record(
        control / f"pair_{pair:03d}_started.json",
        dict(
            pair=pair,
            block=block,
            plan_sha256=PLAN,
            previous_receipt_sha256=previous,
            qualification_sha256=qualification,
            manifest_sha256=manifest,
        ),
    )
    return document["slots"][pair * 2 : pair * 2 + 2]
