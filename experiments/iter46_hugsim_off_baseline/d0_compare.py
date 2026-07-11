#!/usr/bin/env python3
"""Iteration 46 D0 determinism comparator (runs ON THE BOX inside the HUGSIM pixi env).

Compares two collected episode directories of the same scenario per the frozen D0 bars in
HYPOTHESIS.md: (a) client step counts exactly equal; (b) every numeric field of eval.json
exactly equal; (c) data.pkl byte-identical SHA256, or, if bytes differ, recursive numeric
comparison of all array/scalar leaves with max abs delta exactly 0.0.

Writes a JSON report and a plain verdict file ("deterministic" | "stochastic"). Any
comparison error is conservative: the verdict becomes "stochastic" with the error recorded
(determinism that cannot be established is not assumed).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from pathlib import Path

try:  # numpy exists in the pixi env; optional for local unit tests of the pure helpers
    import numpy as _np
except Exception:  # pragma: no cover - exercised only where numpy is absent
    _np = None


def count_steps(output_txt: Path) -> int:
    """Client pipe round-trip count: lines containing the client's 'sent' step marker."""
    count = 0
    with open(output_txt, errors="replace") as fh:
        for line in fh:
            if "sent" in line:
                count += 1
    return count


def numeric_leaves_equal(a: object, b: object) -> tuple[bool, float]:
    """Recursively compare two nested structures; exact equality on all numeric leaves.

    Returns (equal, max_abs_delta). max_abs_delta is only meaningful for numeric leaves that
    could be paired; a structural mismatch returns (False, inf).
    """
    inf = float("inf")
    if _np is not None and isinstance(a, _np.ndarray) and isinstance(b, _np.ndarray):
        if a.shape != b.shape or a.dtype != b.dtype:
            return False, inf
        if a.dtype.kind in "fiu":
            if a.size == 0:
                return True, 0.0
            delta = float(_np.max(_np.abs(a.astype("float64") - b.astype("float64"))))
            return delta == 0.0, delta
        return bool((a == b).all()), 0.0
    if isinstance(a, bool) or isinstance(b, bool):
        return (a == b, 0.0 if a == b else inf)
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        delta = abs(float(a) - float(b))
        return delta == 0.0, delta
    if isinstance(a, dict) and isinstance(b, dict):
        if sorted(map(str, a.keys())) != sorted(map(str, b.keys())):
            return False, inf
        worst = 0.0
        ok = True
        for k in a:
            eq, d = numeric_leaves_equal(a[k], b[k])
            ok = ok and eq
            worst = max(worst, d if d != inf else inf)
        return ok, worst
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            return False, inf
        worst = 0.0
        ok = True
        for x, y in zip(a, b):
            eq, d = numeric_leaves_equal(x, y)
            ok = ok and eq
            worst = max(worst, d if d != inf else inf)
        return ok, worst
    # torch tensors (client-side pickles) and other array-likes: go through .tolist()
    if hasattr(a, "tolist") and hasattr(b, "tolist"):
        return numeric_leaves_equal(a.tolist(), b.tolist())
    return (a == b, 0.0 if a == b else inf)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def compare_episode_dirs(dir1: Path, dir2: Path) -> dict:
    report: dict = {"dir1": str(dir1), "dir2": str(dir2)}
    steps1 = count_steps(dir1 / "output.txt")
    steps2 = count_steps(dir2 / "output.txt")
    report["steps"] = {"run1": steps1, "run2": steps2, "equal": steps1 == steps2}

    eval1 = json.loads((dir1 / "eval.json").read_text())
    eval2 = json.loads((dir2 / "eval.json").read_text())
    eval_equal, eval_delta = numeric_leaves_equal(eval1, eval2)
    report["eval_json"] = {
        "equal": eval_equal,
        "max_abs_delta": eval_delta if eval_delta != float("inf") else "structural-mismatch",
    }

    pkl1, pkl2 = dir1 / "data.pkl", dir2 / "data.pkl"
    sha1, sha2 = sha256_file(pkl1), sha256_file(pkl2)
    pkl_report: dict = {"sha_run1": sha1, "sha_run2": sha2, "sha_equal": sha1 == sha2}
    if sha1 == sha2:
        pkl_report["equal"] = True
    else:
        with open(pkl1, "rb") as fh:
            obj1 = pickle.load(fh)
        with open(pkl2, "rb") as fh:
            obj2 = pickle.load(fh)
        pkl_equal, pkl_delta = numeric_leaves_equal(obj1, obj2)
        pkl_report["equal"] = pkl_equal
        pkl_report["max_abs_delta"] = (
            pkl_delta if pkl_delta != float("inf") else "structural-mismatch"
        )
    report["data_pkl"] = pkl_report

    deterministic = bool(
        report["steps"]["equal"] and report["eval_json"]["equal"] and report["data_pkl"]["equal"]
    )
    report["verdict"] = "deterministic" if deterministic else "stochastic"
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dir1")
    ap.add_argument("dir2")
    ap.add_argument("--out", required=True, help="JSON report path")
    ap.add_argument("--verdict-file", required=True, help="plain verdict output path")
    args = ap.parse_args()
    try:
        report = compare_episode_dirs(Path(args.dir1), Path(args.dir2))
    except Exception as exc:  # conservative: unestablishable determinism is not assumed
        report = {"verdict": "stochastic", "error": f"{type(exc).__name__}: {exc}"}
    Path(args.out).write_text(json.dumps(report, indent=2, default=str) + "\n")
    Path(args.verdict_file).write_text(report["verdict"] + "\n")
    print(f"I46_OFF_D0_VERDICT={report['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
