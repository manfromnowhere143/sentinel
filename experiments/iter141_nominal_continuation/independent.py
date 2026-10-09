"""Separate Decimal outcome/prefix/control and byte-level delivery check; stdlib only."""

from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
import struct


def unique(items):
    result = {}
    for k, v in items:
        if k in result:
            raise ValueError("duplicate key")
        result[k] = v
    return result


def finite(value):
    if type(value) is D and not value.is_finite():
        raise ValueError("nonfinite")
    if type(value) is dict:
        for v in value.values():
            finite(v)
    if type(value) is list:
        for v in value:
            finite(v)


def read(path):
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError("file type")
    with p.open("rb") as f:
        raw = f.read(64 * 1024**2 + 1)
    if len(raw) > 64 * 1024**2 or not raw.endswith(b"\n"):
        raise ValueError("size/truncation")
    rows = [
        json.loads(s, parse_int=D, parse_float=D, parse_constant=D, object_pairs_hook=unique)
        for s in raw.splitlines()
    ]
    finite(rows)
    return rows


def equal(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is D:
        return abs(a - b) <= D(".000001")
    if type(a) is list:
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    if type(a) is dict:
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    return a == b


def typed(a):
    if set(a) != {"dtype", "shape", "values", "bytes_hex", "sha256"} or a["shape"] != [6, 2]:
        raise ValueError("array schema")
    if a["dtype"] not in ("<f4", "<f8"):
        raise ValueError("dtype")
    values = a["values"]
    if len(values) != 6 or any(len(v) != 2 for v in values):
        raise ValueError("shape")
    raw = struct.pack(
        "<12" + ("f" if a["dtype"] == "<f4" else "d"), *[float(x) for v in values for x in v]
    )
    if raw.hex() != a["bytes_hex"] or hashlib.sha256(raw).hexdigest() != a["sha256"]:
        raise ValueError("array bytes")


def episode(directory):
    p = Path(directory)
    a = read(p / "iter141_trace.jsonl")
    ds = read(p / "delivery141.jsonl")
    if not 3 <= len(a) <= 403 or a[0]["schema"] != "sentinel.iter141.trace.v1":
        raise ValueError("trace schema/count")
    if (
        a[0]["arm"] not in ("reference", "nominal")
        or a[0]["onset"] is not None
        or a[0]["duration"] is not None
    ):
        raise ValueError("arm")
    if len(ds) != len(a) - 2 or a[-1]["end"] != "completed" or a[-1]["frames"] != len(ds):
        raise ValueError("footer/count")
    for i, (r, d) in enumerate(zip(a[1:-1], ds)):
        if r["frame"] != i or r["time"] != D(i) / 4 or d["frame"] != i or d["time"] != r["time"]:
            raise ValueError("order/time")
        if r["before"]["timestamp"] != r["time"] or r["after"]["timestamp"] != r["time"] + D(".25"):
            raise ValueError("state time")
        if any(type(r[k]) is not bool for k in ("collision", "terminated", "truncated")):
            raise ValueError("outcome type")
        if not 0 <= r["route_completion"] <= D("1.1111111111111112"):
            raise ValueError("progress range")
        if (r["collision"] or r["route_completion"] >= 1) and not r["terminated"]:
            raise ValueError("missing termination")
        if i < len(ds) - 1 and (r["terminated"] or r["truncated"]):
            raise ValueError("post terminal")
        if i and not equal(a[i]["after"], r["before"]):
            raise ValueError("continuity")
        if d["mode"] != a[0]["arm"]:
            raise ValueError("delivery mode")
        for key in ("nominal", "proposed", "delivered"):
            typed(d[key])
        selected = d["nominal"] if d["mode"] == "nominal" else d["proposed"]
        if (
            d["delivered"] != selected
            or selected["values"] != r["incoming_plan"]
            or r["executed_plan"] != r["incoming_plan"]
        ):
            raise ValueError("delivery selection")
        control = r["control"]
        steer = r["before"]["ego_steer"]
        if (
            len(control) != 2
            or abs(control[0]) > D("3.000000001")
            or abs(control[1]) > D(".400000001")
        ):
            raise ValueError("effective control bound")
        limit = D("1.0471975511965976") + D(".000000001")
        if any(abs(x) > limit for x in (steer, steer + control[1] / 4, r["after"]["ego_steer"])):
            raise ValueError("steering bound")
    last = a[-2]
    reason = (
        "collision"
        if last["collision"]
        else "route_complete"
        if last["terminated"] and last["route_completion"] >= 1
        else "other_termination"
        if last["terminated"]
        else "truncated"
    )
    if not (last["terminated"] or last["truncated"]) or a[-1]["reason"] != reason:
        raise ValueError("terminal reason")
    return a, ds


def outcomes(a, b, ds):
    target = next(r for r in a[1:-1] if r["collision"])
    t = target["after"]["timestamp"]
    rows = b[1:-1]
    last = rows[-1]
    col = [r["after"]["timestamp"] for r in rows if r["collision"]]
    route = b[-1]["reason"] == "route_complete"
    h = [r for r in rows if r["after"]["timestamp"] == t]
    p = (
        h[0]["route_completion"]
        if h
        else last["route_completion"]
        if route and last["after"]["timestamp"] <= t
        else None
    )
    bar = p >= target["route_completion"] - D(".05") if p is not None else None
    contrast = any(d["nominal"] != d["proposed"] for d in ds)

    def f(v):
        return float(v) if v is not None else None

    return dict(
        collision_observed=bool(col),
        first_collision_time=f(col[0]) if col else None,
        terminal_reason=b[-1]["reason"],
        terminal_time=f(last["after"]["timestamp"]),
        final_route_completion=f(last["route_completion"]),
        reference_hazard_time=f(t),
        reference_hazard_progress=f(target["route_completion"]),
        hazard_progress=f(p),
        observed_hazard_horizon=p is not None,
        collision_free_through_hazard=False
        if any(c <= t for c in col)
        else True
        if p is not None
        else None,
        hazard_progress_bar_met=bar,
        action_contrast_observed=contrast,
        useful_recovery=bool(not col and route and bar is True and contrast),
        censored=b[-1]["reason"] == "truncated",
    )


def check(reference, candidate):
    a, da = episode(reference)
    b, db = episode(candidate)
    if a[0]["identity"] != b[0]["identity"]:
        raise ValueError("comparison identity")
    if a[0]["arm"] == b[0]["arm"]:
        if not equal(a, b) or da != db:
            raise ValueError("replica divergence")
        return dict(prefix="matched", scope="independent Decimal replica/control/delivery")
    if a[0]["arm"] != "reference" or b[0]["arm"] != "nominal":
        raise ValueError("comparison arms")
    changed = [i for i, d in enumerate(db) if d["nominal"] != d["proposed"]]
    if not changed:
        n = min(len(da), len(db))
        if not equal(a[1 : n + 1], b[1 : n + 1]):
            raise ValueError("no contrast prefix")
        prefix = "unobserved"
    else:
        i = changed[0]
        if i >= len(da) or not equal(a[1 : i + 1], b[1 : i + 1]):
            raise ValueError("prefix")
        if any(
            not equal(a[i + 1][k], b[i + 1][k]) for k in ("time", "before", "observation_sha256")
        ):
            raise ValueError("contrast state")
        if any(
            da[j][k] != db[j][k]
            for j in range(i + 1)
            for k in ("nominal", "proposed", "monitor_sha256")
        ):
            raise ValueError("contrast input")
        prefix = "matched"
    return dict(
        prefix=prefix,
        outcomes=outcomes(a, b, db),
        scope="independent Decimal prefix/control/outcome",
    )
