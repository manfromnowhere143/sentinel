"""Typed callbacks for the explicitly modified RRT; no physics or search policy."""

import ctypes as C

from experiments.iter158_constraint_aware_search.common import require

P = C.POINTER(C.c_double)


class Branch(C.Structure):
    _fields_ = [
        ("parent", C.c_uint64),
        ("token", C.c_uint64),
        ("steps", C.c_uint32),
        ("flags", C.c_uint32),
        ("before", C.c_double * 6),
        ("after", C.c_double * 6),
    ]


BRANCHES = C.CFUNCTYPE(C.c_int, C.c_uint64, P, P, C.POINTER(Branch))
EVENT = C.CFUNCTYPE(C.c_int, C.c_int, C.c_uint64, C.c_uint64, C.c_uint64, C.c_uint, P, P)
GOAL = C.CFUNCTYPE(C.c_double, P)
STOP = C.CFUNCTYPE(C.c_int)
SAMPLE = C.CFUNCTYPE(None, P)


def branch(parent, token, trace):
    require(type(parent) is int and 1 <= parent <= 2**53 - 1, "parent_encoding")
    require(type(token) is int and 1 <= token <= 2**53 - 1, "token_encoding")
    require(2 <= len(trace) <= 9, "sequence_length")
    return dict(
        parent=parent,
        token=token,
        steps=len(trace) - 1,
        flags=3,
        before=[*trace[0]["state"], trace[0]["frame"]],
        after=[*trace[-1]["state"], trace[-1]["frame"]],
    )


def solve(
    library, seed, start, low, high, target, branches, goal, stop, hard_stop, sample, on_event=None
):
    errors, events = [], []

    @BRANCHES
    def directed(parent, before, toward, out):
        try:
            rows = branches(int(parent), list(before[:6]), list(toward[:6]))
            require(len(rows) <= 2, "branch_count")
            for i, row in enumerate(rows):
                for name, maximum in (
                    ("parent", 2**64 - 1),
                    ("token", 2**64 - 1),
                    ("steps", 2**32 - 1),
                    ("flags", 2**32 - 1),
                ):
                    require(
                        type(row[name]) is int and 0 <= row[name] <= maximum,
                        "branch_integer:" + name,
                    )
                require(len(row["before"]) == len(row["after"]) == 6, "branch_dimensions")
                out[i] = Branch(
                    row["parent"],
                    row["token"],
                    row["steps"],
                    row["flags"],
                    (C.c_double * 6)(*row["before"]),
                    (C.c_double * 6)(*row["after"]),
                )
            return len(rows)
        except BaseException as exc:
            errors.append(exc)
            return -1

    @EVENT
    def event(kind, node, parent, token, steps, state, toward):
        try:
            row = dict(
                kind=int(kind),
                node=int(node),
                parent=int(parent),
                token=int(token),
                steps=int(steps),
                state=list(state[:6]),
                target=list(toward[:6]) if toward else None,
            )
            events.append(row)
            if on_event:
                on_event(row)
            return 0
        except BaseException as exc:
            errors.append(exc)
            return 1

    @GOAL
    def distance(state):
        try:
            return goal(list(state[:6]))
        except BaseException as exc:
            errors.append(exc)
            return 1.0

    def stopped(callback):
        try:
            return int(bool(errors) or callback())
        except BaseException as exc:
            errors.append(exc)
            return 1

    @STOP
    def ordinary():
        return stopped(stop)

    @STOP
    def hard():
        return stopped(hard_stop)

    @SAMPLE
    def sampler(out):
        try:
            values = sample()
            require(len(values) == 6, "sample_dimensions")
            for i, value in enumerate(values):
                out[i] = value
        except BaseException as exc:
            errors.append(exc)

    lib = C.CDLL(str(library))
    fn = lib.sentinel_rrt186
    fn.argtypes = [
        C.c_uint,
        P,
        P,
        P,
        P,
        BRANCHES,
        GOAL,
        STOP,
        STOP,
        SAMPLE,
        EVENT,
        P,
        C.c_int,
        C.POINTER(C.c_int),
        C.POINTER(C.c_int),
        C.POINTER(C.c_char),
    ]
    fn.restype = C.c_int
    output, length, reason, error = (
        (C.c_double * (402 * 11))(),
        C.c_int(),
        C.c_int(),
        C.create_string_buffer(512),
    )
    arrays = [(C.c_double * 6)(*values) for values in (start, low, high, target)]
    status = fn(
        seed,
        *arrays,
        directed,
        distance,
        ordinary,
        hard,
        sampler,
        event,
        output,
        402,
        C.byref(length),
        C.byref(reason),
        error,
    )
    if errors:
        raise errors[0]
    require(status >= 0, "native_exception:" + error.value.decode())
    return dict(
        status=status,
        stop_code=reason.value,
        rows=[list(output[11 * i : 11 * (i + 1)]) for i in range(length.value)],
        events=events,
    )
