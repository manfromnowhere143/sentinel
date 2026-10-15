"""Accounted physical callbacks for released OMPL control RRT; no beam search."""

import ctypes as C
import math
import random
import time

from experiments.iter153_action_feasibility.geometry import obstacles, route_outcome
from experiments.iter158_constraint_aware_search.common import require, rss
from experiments.iter158_constraint_aware_search.search import prior_reason
from experiments.iter172_integrated_rrt.connection import Evaluator, task_for
from experiments.iter177_pose_aware_seed.forward import solve as forward

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


def terminal_frame(geometry, old):
    frames = [c["hazard_time"] / old["dt"] for c in geometry["comparators"].values()]
    require(all(float(f).is_integer() for f in frames), "checkpoint_off_grid")
    return int(max(frames, default=0))


class Edges:
    def __init__(self, geometry, old, plan, query, emit):
        self.geometry, self.old, self.plan, self.query, self.emit = geometry, old, plan, query, emit
        self.started = time.monotonic()
        self.attempts = self.queries = self.calls = 0
        self.exception = None
        self.reservation_stop = False
        self.accepted = {}

    def stopped(self):
        return (
            self.exception is not None
            or self.reservation_stop
            or self.attempts >= self.plan["attempt_budget"]
            or time.monotonic() - self.started >= self.plan["per_run_seconds"]
        )

    def directed(self, before, target):
        require(not self.stopped(), "call_after_budget")
        self.calls += 1
        task = task_for(before, target, self.plan)
        remaining = self.plan["attempt_budget"] - self.attempts
        if task is None or remaining < task["terminal_frame"]:
            self.reservation_stop = task is not None
            self.emit(
                "connection",
                dict(
                    call=self.calls,
                    before=before,
                    target=target,
                    task=task,
                    budget=remaining,
                    result=None,
                    stop="horizon" if task is None else "attempt_reservation",
                ),
            )
            return None
        budget = min(self.plan["connection_attempt_budget"], remaining)

        def emit(kind, row):
            self.emit(kind, dict(call=self.calls, **row))

        evaluator = Evaluator(
            self.geometry,
            before,
            target,
            task,
            self.old,
            self.plan,
            budget,
            self.started + self.plan["per_run_seconds"],
            self.query,
            emit,
        )
        result = forward(evaluator, True, self.plan["max_proposals"])
        self.attempts += result["attempts"]
        self.queries += result["queries"]
        trace = result.pop("trace")
        record = dict(
            call=self.calls,
            before=before,
            target=target,
            task=task,
            budget=budget,
            result=result,
            trace=trace,
            stop=result["stop"],
        )
        self.emit("connection", record)
        if len(trace) > 1:
            self.accepted[self.calls] = record
            return record
        return None


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
            endpoint = row["trace"][-1]
            for i, value in enumerate([*endpoint["state"], endpoint["frame"]]):
                after[i] = value
            control[0] = row["call"]
            return len(row["trace"]) - 1
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
    native_rows = [[output[9 * i + j] for j in range(9)] for i in range(length.value)]
    trace, selected_connections = expand_path(native_rows, edges.accepted, root, start_frame, old)
    for row in trace:
        row["background"] = query(row["state"])
        row["route"] = route_outcome(row["state"], route)
        row["reason"] = "clear"
    emit(
        "native_path",
        dict(rows=native_rows, selected_connections=selected_connections, status=status),
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
        accepted_connections=len(edges.accepted),
        selected_connections=selected_connections,
        unused_attempt_budget=plan["attempt_budget"] - edges.attempts,
        elapsed_seconds=elapsed,
        peak_rss_bytes=rss(),
        stop="model_complete"
        if complete
        else (
            "attempt_budget"
            if edges.attempts >= plan["attempt_budget"] or edges.reservation_stop
            else "time_budget"
        ),
    )


def expand_path(rows, accepted, root, start_frame, old):
    initial = dict(id=start_frame, parent=None, frame=start_frame, action=None, state=root)
    if not rows:
        return [initial], []
    require(rows[0][:6] == [*root, start_frame] and rows[0][6:] == [0, 0, 0], "native_root")
    trace, ids = [initial], []
    for row in rows[1:]:
        require(
            float(row[6]).is_integer() and row[7] == 0 and int(row[6]) in accepted, "native_token"
        )
        record = accepted[int(row[6])]
        segment = record["trace"]
        require(record["before"] == [*trace[-1]["state"], trace[-1]["frame"]], "native_parent")
        require(row[:6] == [*segment[-1]["state"], segment[-1]["frame"]], "native_endpoint")
        require(row[8] == (len(segment) - 1) * old["dt"], "native_duration")
        trace.extend(dict(r) for r in segment[1:])
        ids.append(record["call"])
    return trace, ids
