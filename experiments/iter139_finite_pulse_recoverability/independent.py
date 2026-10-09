"""Separate Decimal prefix and endpoint computation; imports no producer or primary checker."""

from decimal import Decimal
import json
from pathlib import Path


def unique(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError("duplicate key")
        out[k] = v
    return out


def read(path):
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError("file type")
    with p.open("rb") as f:
        raw = f.read(16 * 1024**2 + 1)
    if len(raw) > 16 * 1024**2 or not raw.endswith(b"\n"):
        raise ValueError("size/truncation")
    rows = [
        json.loads(
            s,
            parse_int=Decimal,
            parse_float=Decimal,
            parse_constant=Decimal,
            object_pairs_hook=unique,
        )
        for s in raw.splitlines()
    ]
    if not 3 <= len(rows) <= 403 or rows[0]["schema"] != "sentinel.iter139.trace.v1":
        raise ValueError("schema/count")
    h = rows[0]
    ref = h["arm"] == "reference"
    if not (
        ref
        and h["onset"] is None
        and h["duration"] is None
        or h["arm"] == "pulse"
        and type(h["onset"]) is Decimal
        and h["onset"] in (0, 2, 4)
        and type(h["duration"]) is Decimal
        and h["duration"] in (1, 2)
    ):
        raise ValueError("pulse contract")
    if rows[-1]["end"] != "completed" or rows[-1]["frames"] != len(rows) - 2:
        raise ValueError("footer")
    for i, r in enumerate(rows[1:-1]):
        if type(r["frame"]) is not Decimal or r["frame"] != i or r["time"] != Decimal(i) / 4:
            raise ValueError("frame/time")
        if r["before"]["timestamp"] != r["time"] or r["after"]["timestamp"] != r["time"] + Decimal(
            ".25"
        ):
            raise ValueError("state time")
        if any(type(r[k]) is not bool for k in ("collision", "terminated", "truncated")):
            raise ValueError("missing Boolean outcome")
        rc = r["route_completion"]
        if (
            type(rc) is not Decimal
            or not rc.is_finite()
            or not 0 <= rc <= Decimal("1.1111111111111112")
        ):
            raise ValueError("raw progress")
        if (r["collision"] or rc >= 1) and not r["terminated"]:
            raise ValueError("missing termination")
        if i < len(rows) - 3 and (r["terminated"] or r["truncated"]):
            raise ValueError("post-terminal frame")
        active = not ref and h["onset"] <= r["time"] < h["onset"] + h["duration"]
        wanted = [[Decimal(0), Decimal(0)]] * 6 if active else r["incoming_plan"]
        if r["executed_plan"] != wanted:
            raise ValueError("pulse execution")
    last = rows[-2]
    reason = (
        "collision"
        if last["collision"]
        else "route_complete"
        if last["terminated"] and last["route_completion"] >= 1
        else "other_termination"
        if last["terminated"]
        else "truncated"
    )
    if not (last["terminated"] or last["truncated"]) or rows[-1]["reason"] != reason:
        raise ValueError("terminal reason")
    return rows


def equal(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is Decimal:
        if not a.is_finite() or not b.is_finite():
            raise ValueError("nonfinite")
        return abs(a - b) <= Decimal(".000001")
    if type(a) is list:
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    if type(a) is dict:
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    return a == b


def outcomes(a, b):
    target = next(r for r in a[1:-1] if r["collision"])
    t = target["after"]["timestamp"]
    rows = b[1:-1]
    last = rows[-1]
    s = b[0]["onset"]
    d = b[0]["duration"]
    col = [r["after"]["timestamp"] for r in rows if r["collision"]]
    route = b[-1]["reason"] == "route_complete"
    hazard = [r for r in rows if r["after"]["timestamp"] == t]
    p = (
        hazard[0]["route_completion"]
        if hazard
        else last["route_completion"]
        if route and last["after"]["timestamp"] <= t
        else None
    )
    seen = p is not None
    hazard_free = False if any(c <= t for c in col) else True if seen else None
    active = [r for r in rows if s is not None and s <= r["time"] < s + d]
    resume = s is not None and any(r["time"] >= s + d for r in rows)
    complete = s is not None and len(active) == d * 4 and resume
    bar = p >= target["route_completion"] - Decimal(".05") if p is not None else None
    useful = not col and route and bar is True and complete and len(active) <= 8
    def f(x):
        return float(x) if x is not None else None
    return dict(
        collision_observed=bool(col),
        first_collision_time=f(col[0]) if col else None,
        terminal_reason=b[-1]["reason"],
        terminal_time=f(last["after"]["timestamp"]),
        final_route_completion=f(last["route_completion"]),
        reference_hazard_time=f(t),
        reference_hazard_progress=f(target["route_completion"]),
        hazard_progress=f(p),
        observed_hazard_horizon=seen,
        collision_free_through_hazard=hazard_free,
        hazard_progress_bar_met=bar,
        onset_reached=s is not None and any(r["time"] == s for r in rows),
        assigned_override_frames=int(d * 4) if d else 0,
        realized_override_frames=len(active),
        changed_plan_frames=sum(r["incoming_plan"] != r["executed_plan"] for r in active),
        override_seconds=len(active) * 0.25,
        resumption_observed=resume,
        complete_pulse_observed=complete,
        useful_recovery=bool(useful),
        censored=b[-1]["reason"] == "truncated",
    )


def check(reference, candidate):
    a, b = read(reference), read(candidate)
    if a[0]["arm"] != "reference" or a[0]["identity"] != b[0]["identity"]:
        raise ValueError("identity/reference")
    if b[0]["arm"] == "reference":
        if not equal(a, b):
            raise ValueError("reference divergence")
        return dict(prefix="matched", scope="independent Decimal driving trace equality")
    index = int(b[0]["onset"] * 4)
    if min(len(a), len(b)) - 2 <= index:
        prefix = "unobserved"
    else:
        if not equal(a[1 : index + 1], b[1 : index + 1]):
            raise ValueError("prefix divergence")
        for key in ("time", "before", "observation_sha256", "incoming_plan"):
            if not equal(a[index + 1][key], b[index + 1][key]):
                raise ValueError("onset divergence")
        prefix = "matched"
    return dict(
        prefix=prefix,
        outcomes=outcomes(a, b),
        scope="independent pulse timing, prefix and endpoint calculation",
    )
