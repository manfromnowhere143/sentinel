"""Accounted physical callbacks for released OMPL control RRT; no beam search."""

import ctypes as C
import math
import random
import time

from experiments.iter153_action_feasibility.geometry import obstacles, route_outcome
from experiments.iter153_action_feasibility.planner import reference, transition
from experiments.iter158_constraint_aware_search.common import require, rss
from experiments.iter158_constraint_aware_search.search import prior_reason, proposals

P = C.POINTER(C.c_double)
DIRECTED = C.CFUNCTYPE(C.c_int, P, P, P, P)
GOAL = C.CFUNCTYPE(C.c_double, P)
STOP = C.CFUNCTYPE(C.c_int)
SAMPLE = C.CFUNCTYPE(None, P)
WEIGHTS = (1, 1, 2, 0.5, 2, 0.01)


def distance(a, b):
    terms = [x - y for x, y in zip(a, b)]
    terms[2] = math.remainder(terms[2], 2 * math.pi)
    return math.sqrt(sum((d * w) ** 2 for d, w in zip(terms, WEIGHTS)))


class Edges:
    def __init__(self, geometry, old, plan, query, emit):
        self.geometry, self.old, self.plan, self.query, self.emit = geometry, old, plan, query, emit
        self.boxes = obstacles(geometry)
        self.path, self.arc = reference(geometry["route"], dict(offset=0, start=0, length=10), old)
        self.started = time.monotonic()
        self.attempts = self.queries = self.calls = 0
        self.exception = None

    def stopped(self):
        return (
            self.exception is not None
            or self.attempts >= self.plan["attempt_budget"]
            or time.monotonic() - self.started >= self.plan["per_run_seconds"]
        )

    def edge(self, before, action):
        require(not self.stopped(), "attempt_after_budget")
        require(len(before) == 6 and before[5].is_integer(), "absolute_clock")
        require(rss() <= self.plan["max_rss_bytes"], "memory_budget")
        self.attempts += 1
        frame = int(before[5]) + 1
        state = transition(before[:5], action, self.old)
        reason, outcome = prior_reason(
            before[:5], state, action, frame, self.geometry, self.old, self.boxes
        )
        if frame > self.plan["max_actions"]:
            reason = "horizon"
        background = None
        if reason is None:
            self.queries += 1
            background = self.query(state)
            reason = background["decision"]
        row = dict(
            id=self.attempts,
            before=before,
            frame=frame,
            action=action,
            state=state,
            route=outcome,
            reason=reason,
            background=background,
        )
        self.emit("attempt", row)
        return row

    def directed(self, before, target):
        self.calls += 1
        rows = []
        for action in proposals(before[:5], self.path, self.arc, self.old):
            if self.stopped():
                break
            row = self.edge(before, action)
            if row["reason"] == "clear":
                rows.append(row)
        chosen = (
            min(rows, key=lambda r: (distance([*r["state"], r["frame"]], target), r["id"]))
            if rows
            else None
        )
        self.emit(
            "expansion",
            dict(
                call=self.calls,
                before=before,
                target=target,
                selected=None if chosen is None else chosen["id"],
            ),
        )
        return chosen


def search(library, geometry, old, plan, query, emit, seed, start_frame=0):
    require(0 <= start_frame < plan["max_actions"] <= 401, "start_frame")
    root = geometry["reset"]
    initial = query(root)
    reason, _ = prior_reason(root, root, [0, 0], start_frame, geometry, old, obstacles(geometry))
    require(reason is None and initial["decision"] == "clear", "initial_rejected")
    edges = Edges(geometry, old, plan, query, emit)
    rng = random.Random(seed)
    route = geometry["route"]

    def heading(i):
        a, b = route[max(0, i - 1)], route[min(len(route) - 1, i + 1)]
        return math.atan2(b[0] - a[0], b[1] - a[1])

    errors = []

    @DIRECTED
    def directed(before, target, after, control):
        try:
            row = edges.directed([before[i] for i in range(6)], [target[i] for i in range(6)])
            if row is None:
                return 0
            for i, value in enumerate([*row["state"], row["frame"]]):
                after[i] = value
            control[0], control[1] = row["action"]
            return 1
        except BaseException as e:
            edges.exception = e
            errors.append(e)
            return 0

    @GOAL
    def goal(state):
        try:
            return max(0.0, 1 - route_outcome([state[i] for i in range(5)], route)["rc"])
        except BaseException as e:
            edges.exception = e
            errors.append(e)
            return 1.0

    @STOP
    def stop():
        return int(edges.stopped())

    @SAMPLE
    def sample(out):
        try:
            i = rng.randrange(len(route))
            theta = heading(i)
            offset = rng.uniform(-3, 3)
            values = [
                route[i][1] - offset * math.sin(theta),
                route[i][0] + offset * math.cos(theta),
                theta + rng.uniform(-0.5, 0.5),
                rng.uniform(0, 6),
                rng.uniform(-math.pi / 3, math.pi / 3),
                rng.uniform(start_frame, plan["max_actions"]),
            ]
            for j, value in enumerate(values):
                out[j] = value
        except BaseException as e:
            edges.exception = e
            errors.append(e)

    xs = [p[1] for p in route]
    ys = [p[0] for p in route]
    low = [min(xs) - 10, min(ys) - 10, -10000, 0, -math.pi / 3, start_frame]
    high = [max(xs) + 10, max(ys) + 10, 10000, 6, math.pi / 3, plan["max_actions"]]
    goal_index = math.ceil(0.9 * len(route)) - 1
    target = [
        route[goal_index][1],
        route[goal_index][0],
        heading(goal_index),
        2,
        0,
        plan["max_actions"],
    ]
    native = C.CDLL(str(library))
    fn = native.sentinel_rrt
    fn.argtypes = [
        C.c_uint,
        P,
        P,
        P,
        P,
        DIRECTED,
        GOAL,
        STOP,
        SAMPLE,
        P,
        C.c_int,
        C.POINTER(C.c_int),
        C.POINTER(C.c_char),
    ]
    fn.restype = C.c_int

    def arr(vals):
        return (C.c_double * len(vals))(*vals)

    output = (C.c_double * (402 * 9))()
    length = C.c_int()
    error = C.create_string_buffer(512)
    status = fn(
        seed,
        arr([*root, start_frame]),
        arr(low),
        arr(high),
        arr(target),
        directed,
        goal,
        stop,
        sample,
        output,
        402,
        C.byref(length),
        error,
    )
    if errors:
        raise errors[0]
    require(status >= 0, "native_exception:" + error.value.decode())
    trace = []
    if length.value == 0:
        values = [[*root, start_frame, 0, 0, 0]]
    else:
        values = [[output[9 * i + j] for j in range(9)] for i in range(length.value)]
    for i, row in enumerate(values):
        state = row[:5]
        frame = start_frame + i
        require(row[5] == frame and (i == 0 or row[8] == old["dt"]), "native_clock")
        trace.append(
            dict(
                id=frame,
                parent=frame - 1 if i else None,
                frame=frame,
                action=row[6:8] if i else None,
                state=state,
                route=route_outcome(state, route),
                background=query(state),
                reason="clear",
            )
        )
    complete = status == 2
    require(complete == (trace[-1]["route"]["rc"] >= 1), "native_false_completion")
    elapsed = time.monotonic() - edges.started
    return dict(
        trace=trace,
        complete=complete,
        native_status=status,
        attempts=edges.attempts,
        queries=edges.queries + 1,
        path_queries=len(trace),
        directed_calls=edges.calls,
        elapsed_seconds=elapsed,
        peak_rss_bytes=rss(),
        stop="model_complete"
        if complete
        else ("attempt_budget" if edges.attempts >= plan["attempt_budget"] else "time_budget"),
    )
