"""Iter183 connections through the qualified, explicitly modified native RRT."""

import math
import random
import time

from experiments.iter153_action_feasibility.geometry import obstacles, route_outcome
from experiments.iter158_constraint_aware_search.search import prior_reason
from experiments.iter183_timing_eligibility.adapter import Edges
from experiments.iter186_native_branch import native, selection, transport
from .common import require, rss


class RetainingEdges(Edges):
    def __init__(self, geometry, old, plan, query, emit):
        self.evaluations = []

        def capture(kind, row):
            if kind == "evaluation":
                self.evaluations.append(row)
            emit(kind, row)

        super().__init__(geometry, old, plan, query, capture)
        self.output = emit
        self.nodes = {}
        self.sequences = {}
        self.maximum = selection.nearest(geometry["reset"], geometry["route"])
        self.endpoints = {(*geometry["reset"], 0)}

    def expired(self):
        return time.monotonic() - self.started >= self.plan["per_run_seconds"]

    def event(self, row):
        kind = row["kind"]
        if kind in (0, 1, 2):
            require(row["node"] == len(self.nodes) + 1, "registration_order")
            if kind:
                sequence = self.sequences[row["token"]]
                require(
                    sequence["parent"] == row["parent"]
                    and sequence["node"] is None
                    and [*sequence["trace"][-1]["state"], sequence["trace"][-1]["frame"]]
                    == row["state"],
                    "registration_binding",
                )
                sequence["node"] = row["node"]
            self.nodes[row["node"]] = row
            self.endpoints.add(tuple(row["state"]))
            self.maximum = max(
                self.maximum, selection.nearest(row["state"][:5], self.geometry["route"])
            )
        self.output("native_event", dict(event=row, elapsed=time.monotonic() - self.started))

    def branches(self, parent, before, target):
        require(parent in self.nodes and self.nodes[parent]["state"] == before, "callback_parent")
        self.evaluations = []
        primary = super().directed(before, target)
        extra = selection.choose(
            self.evaluations, primary, self.maximum, self.endpoints, self.geometry["route"]
        )
        rows = []
        for is_extra, record in ((False, primary), (True, extra)):
            if record is None:
                continue
            token = 2 * self.calls - (0 if is_extra else 1)
            require(token not in self.sequences, "sequence_reuse")
            self.sequences[token] = dict(
                call=self.calls, extra=is_extra, parent=parent, node=None, trace=record["trace"]
            )
            rows.append(native.branch(parent, token, record["trace"]))
        expired = self.expired()
        self.output(
            "branch_choice",
            dict(
                call=self.calls,
                parent=parent,
                extra=extra,
                tokens=[r["token"] for r in rows],
                expired=expired,
                elapsed=time.monotonic() - self.started,
            ),
        )
        return [] if expired else rows


def search(library, geometry, old, plan, query, emit, seed):
    root, route = geometry["reset"], geometry["route"]
    edges = RetainingEdges(geometry, old, plan, query, emit)
    initial = query(root)
    reason, _ = prior_reason(root, root, [0, 0], 0, geometry, old, obstacles(geometry))
    require(reason is None and initial["decision"] == "clear", "initial_rejected")
    rng = random.Random(seed)

    def heading(i):
        a, b = route[max(0, i - 1)], route[min(len(route) - 1, i + 1)]
        return math.atan2(b[0] - a[0], b[1] - a[1])

    def sample():
        i = rng.randrange(len(route))
        theta, offset = heading(i), rng.uniform(-3, 3)
        return [
            route[i][1] - offset * math.sin(theta),
            route[i][0] + offset * math.cos(theta),
            theta + rng.uniform(-0.5, 0.5),
            rng.uniform(0, 6),
            rng.uniform(-math.pi / 3, math.pi / 3),
            rng.uniform(0, plan["max_actions"]),
        ]

    xs, ys = [p[1] for p in route], [p[0] for p in route]
    goal_index = math.ceil(0.9 * len(route)) - 1
    result = native.solve(
        library,
        seed,
        [*root, 0],
        [min(xs) - 10, min(ys) - 10, -10000, 0, -math.pi / 3, 0],
        [max(xs) + 10, max(ys) + 10, 10000, 6, math.pi / 3, plan["max_actions"]],
        [
            route[goal_index][1],
            route[goal_index][0],
            heading(goal_index),
            2,
            0,
            plan["max_actions"],
        ],
        edges.branches,
        lambda state: max(0.0, 1 - route_outcome(state[:5], route)["rc"]),
        edges.stopped,
        edges.expired,
        sample,
        edges.event,
    )
    trace, tokens = transport.expand(result["rows"], edges.sequences, [*root, 0], old["dt"])
    # No new path queries: every returned state was queried in recorded connection work.
    trace[0].update(background=initial, route=route_outcome(root, route), reason="clear")
    finalization_expired = edges.expired()
    if finalization_expired:
        trace, tokens = trace[:1], []
        result.update(status=0, stop_code=2, rows=[])
    emit(
        "native_path",
        dict(
            rows=result["rows"],
            status=result["status"],
            stop_code=result["stop_code"],
            selected_tokens=tokens,
            finalization_expired=finalization_expired,
            elapsed=time.monotonic() - edges.started,
        ),
    )
    # Serialization is charged too. A late final record invalidates the worker;
    # it can never turn an expired completion into success.
    elapsed = time.monotonic() - edges.started
    complete = result["status"] == 2
    require(not complete or elapsed < plan["per_run_seconds"], "completion_after_deadline")
    require(complete == (trace[-1]["route"]["rc"] >= 1), "native_false_completion")
    registered = {k: v for k, v in edges.sequences.items() if v["node"] is not None}
    return dict(
        trace=trace,
        sequences=registered,
        complete=complete,
        native_status=result["status"],
        native_stop_code=result["stop_code"],
        attempts=edges.attempts,
        queries=edges.queries + 1,
        directed_calls=edges.calls,
        accepted_connections=len(edges.accepted),
        registered_primary=sum(not v["extra"] for v in registered.values()),
        registered_extra=sum(v["extra"] for v in registered.values()),
        selected_tokens=tokens,
        unused_attempt_budget=plan["attempt_budget"] - edges.attempts,
        elapsed_seconds=elapsed,
        peak_rss_bytes=rss(),
        stop="model_complete"
        if complete
        else ("time_budget" if result["stop_code"] == 2 else "attempt_budget"),
    )
