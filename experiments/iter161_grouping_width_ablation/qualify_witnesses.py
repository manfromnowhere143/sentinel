"""Pre-freeze feasibility control; never calls the factorial search."""

import json
from pathlib import Path
import time

import numpy as np

from experiments.iter158_constraint_aware_search.check import verify_path
from experiments.iter159_route_search_qualification.run import query_for, witness
from .common import BASE, OLD, encode, sha
from .fixtures import reflect
from .reflection import check_cases


def qualify(root):
    started = time.monotonic()
    data = (root / BASE / "CASES.json").read_bytes()
    cases = json.loads(data)
    previous = json.loads(
        (root / "experiments/iter159_route_search_qualification/CASES.json").read_bytes()
    )
    check_cases(cases, previous)
    old = json.loads((root / OLD).read_bytes())
    records = []
    for case in cases:
        if encode(reflect(reflect(case))) != encode(case):
            raise ValueError("reflection_roundtrip")
        query = query_for(case)
        rows = witness(case, old, query)
        masks = [np.packbits(query(row["state"]).mask, bitorder="little").tobytes() for row in rows]
        metrics = verify_path(
            rows,
            case["geometry"],
            old,
            case["points"],
            case["ground"],
            lambda i: masks[i],
            True,
            started + 600,
        )
        records.append(dict(case=case["id"], trace_sha256=sha(encode(rows)), **metrics))
    return dict(
        status="supported",
        scope="Constructive witness and complete-reflection qualification only",
        cases_sha256=sha(data),
        records=records,
        verified_states=sum(r["verified_states"] for r in records),
        elapsed_seconds=time.monotonic() - started,
        factorial_outcomes_acquired=False,
    )


if __name__ == "__main__":
    print(json.dumps(qualify(Path.cwd()), indent=2))
