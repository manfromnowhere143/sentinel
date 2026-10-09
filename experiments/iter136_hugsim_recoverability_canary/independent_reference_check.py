"""Separate implementation of the numeric/exact comparison for a complete reference pair.

This deliberately does not import the main recorder or validator. Run it in addition to
the main schema validator. It checks reference equality, not branch benefit or full schema.
"""

import argparse
from decimal import Decimal
import json
from pathlib import Path


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def flatten(value, path=()):
    if isinstance(value, dict):
        yield path, ("dict", tuple(sorted(value)))
        for key in sorted(value):
            yield from flatten(value[key], path+(key,))
    elif isinstance(value, list):
        yield path, ("list", len(value))
        for index, item in enumerate(value):
            yield from flatten(item, path+(index,))
    elif isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("nonfinite value")
        yield path, ("number", value)
    else:
        yield path, (type(value).__name__, value)


def read(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("trace file type")
    with path.open("rb") as stream:
        raw = stream.read(16*1024*1024 + 1)
    if len(raw) > 16*1024*1024 or not raw.endswith(b"\n"):
        raise ValueError("trace size or truncation")
    data = [json.loads(row, parse_float=Decimal, parse_int=Decimal,
                       parse_constant=Decimal, object_pairs_hook=unique) for row in raw.splitlines()]
    if not 3 <= len(data) <= 403 or data[0].get("arm") != "reference":
        raise ValueError("reference trace required")
    if data[0].get("stop_at") is not None or data[-1].get("end") != "completed":
        raise ValueError("incomplete reference")
    if data[-1].get("frames") != Decimal(len(data)-2):
        raise ValueError("frame count")
    for i, frame in enumerate(data[1:-1]):
        if frame.get("frame") != Decimal(i) or frame.get("time") != Decimal(i)/4:
            raise ValueError("frame order/time")
    return dict(flatten(data))


def check(left_path, right_path):
    left, right = read(left_path), read(right_path)
    if left.keys() != right.keys():
        return {"matched": False, "reason": "structure"}
    for path, (kind, value) in left.items():
        other_kind, other = right[path]
        equal = kind == other_kind and (
            abs(value-other) <= Decimal("0.000001") if kind == other_kind == "number"
            else value == other
        )
        if not equal:
            return {"matched": False, "first_difference": list(path)}
    return {"matched": True, "scope": "complete reference trace comparison only"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.reference, args.candidate), sort_keys=True, indent=2))
