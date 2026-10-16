"""Fixed constructed native workloads, independent of the four development scenes."""

import argparse
import ctypes as C
import json
from pathlib import Path
import random

from . import native
from experiments.iter158_constraint_aware_search.common import require

SEED = 20261016
START = [0.0, 0.0, 0.0, 1.0, 0.0, 0.0]
LOW = [-100.0, -100.0, -100.0, 0.0, -2.0, 0.0]
HIGH = [100.0, 100.0, 100.0, 6.0, 2.0, 96.0]
TARGET = [2.0, 0.0, 0.0, 1.0, 0.0, 1.0]


def row(parent, token, before, x, steps=1):
    after = list(before)
    after[0], after[5] = x, before[5] + steps
    return dict(parent=parent, token=token, steps=steps, flags=3, before=before, after=after)


class Script:
    def __init__(self, profile):
        self.profile, self.calls, self.log = profile, 0, []
        self.rng = random.Random(SEED)

    def sample(self):
        out = [
            self.rng.uniform(-2, 8),
            self.rng.uniform(-1, 1),
            0.0,
            1.0,
            0.0,
            self.rng.uniform(0, 8),
        ]
        self.log.append(dict(kind="sample", state=out))
        return out

    def stop(self):
        result = self.calls >= 12
        self.log.append(dict(kind="stop", value=result))
        return result

    def goal(self, state):
        distance = 0.0 if self.profile == "exact" and state[0] >= 5 else abs(20 - state[0])
        self.log.append(dict(kind="goal", state=state, distance=distance))
        return distance

    def branches(self, parent, before, target):
        self.calls += 1
        self.log.append(dict(kind="directed", before=before, target=target, call=self.calls))
        if self.profile == "empty" or self.calls % 4 == 0:
            return []
        result = row(
            parent, self.calls, before, before[0] + 0.25 * self.calls + 0.5, 1 + self.calls % 3
        )
        return [result]


def original(library, script):
    """Direct call to the retained binary, without importing the successor producer."""
    p = C.POINTER(C.c_double)
    directed_type = C.CFUNCTYPE(C.c_int, p, p, p, p)
    goal_type = C.CFUNCTYPE(C.c_double, p)
    stop_type = C.CFUNCTYPE(C.c_int)
    sample_type = C.CFUNCTYPE(None, p)
    errors = []

    @directed_type
    def directed(before, target, after, control):
        try:
            rows = script.branches(0, list(before[:6]), list(target[:6]))
            if not rows:
                return 0
            r = rows[0]
            for i, value in enumerate(r["after"]):
                after[i] = value
            control[0] = r["token"]
            return r["steps"]
        except BaseException as exc:
            errors.append(exc)
            return 0

    @goal_type
    def goal(state):
        return script.goal(list(state[:6]))

    @stop_type
    def stop():
        return int(bool(errors) or script.stop())

    @sample_type
    def sample(out):
        for i, value in enumerate(script.sample()):
            out[i] = value

    lib = C.CDLL(str(library))
    fn = lib.sentinel_rrt
    fn.argtypes = [
        C.c_uint,
        p,
        p,
        p,
        p,
        directed_type,
        goal_type,
        stop_type,
        sample_type,
        p,
        C.c_int,
        C.POINTER(C.c_int),
        C.POINTER(C.c_char),
    ]
    fn.restype = C.c_int
    output, length, error = (C.c_double * (402 * 9))(), C.c_int(), C.create_string_buffer(512)
    arrays = [(C.c_double * 6)(*v) for v in (START, LOW, HIGH, TARGET)]
    status = fn(SEED, *arrays, directed, goal, stop, sample, output, 402, C.byref(length), error)
    if errors:
        raise errors[0]
    require(status >= 0, "parent_native:" + error.value.decode())
    rows = [list(output[9 * i : 9 * (i + 1)]) for i in range(length.value)]
    return dict(status=status, rows=rows)


def compatibility(library, profile, parent=False):
    script = Script(profile)
    if parent:
        result = original(library, script)
    else:
        candidate = native.solve(
            library,
            SEED,
            START,
            LOW,
            HIGH,
            TARGET,
            script.branches,
            script.goal,
            script.stop,
            lambda: False,
            script.sample,
        )
        require(candidate["stop_code"] == (3 if candidate["status"] == 2 else 1), "stop_code")
        result = dict(
            status=candidate["status"], rows=[[*r[:7], 0.0, r[10]] for r in candidate["rows"]]
        )
    return dict(result, callbacks=script.log, directed_calls=script.calls)


def extra(library, mutation=None, expiry=None):
    calls, expired, registered = 0, False, []

    def branches(parent, before, target):
        nonlocal calls, expired
        calls += 1
        primary = row(parent, 1 if calls == 1 else 3, before, 1.0 if calls == 1 else 3.0)
        rows = [primary, row(parent, 2, before, 2.0)] if calls == 1 else [primary]
        if mutation and calls == 1:
            b = rows[1]
            if mutation == "parent":
                b["parent"] += 9
            elif mutation == "before":
                b["before"] = [99.0, *before[1:]]
            elif mutation == "token":
                b["token"] = 0
            elif mutation == "reused_token":
                b["token"] = rows[0]["token"]
            elif mutation == "duration":
                b["steps"] = 2
            elif mutation == "flags":
                b["flags"] = 1
            elif mutation == "finite":
                b["after"][0] = float("nan")
            elif mutation == "duplicate":
                b["after"] = list(rows[0]["after"])
            elif mutation == "count":
                rows.append(b)
            else:
                raise ValueError("unknown_fixture_mutation")
        if expiry == "after_callback":
            expired = True
        return rows

    def event(r):
        nonlocal expired
        registered.append(r)
        if (expiry, r["kind"]) in (
            ("before_callback", 3),
            ("after_primary", 1),
            ("after_extra", 2),
        ):
            expired = True

    def goal(state):
        nonlocal expired
        if expiry == "after_goal":
            expired = True
        return 0.0 if state[0] >= 3.0 else 3.0 - state[0]

    result = native.solve(
        library,
        SEED,
        START,
        LOW,
        HIGH,
        TARGET,
        branches,
        goal,
        lambda: calls >= 2,
        lambda: expiry == "initial" or expired,
        lambda: TARGET,
        event,
    )
    return dict(result, directed_calls=calls)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--profile", choices=("empty", "approximate", "exact"), required=True)
    parser.add_argument("--parent", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    value = compatibility(args.library, args.profile, args.parent)
    args.output.write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    )
