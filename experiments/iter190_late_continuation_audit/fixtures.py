"""Constructed stop/wait success and obstruction controls; no retained-root probes."""

import time
from experiments.iter153_action_feasibility.geometry import route_outcome
from experiments.iter153_action_feasibility.planner import transition
from experiments.iter159_route_search_qualification.run import query_for
from .masks import Queries
from .probe import run


def case(blocked=False):
    return dict(
        id="constructed_blocked" if blocked else "constructed_clear",
        geometry=dict(
            reset=[16.5, 0.0, 0.0, 0.0, 0.0],
            route=[[0.0, i / 4] for i in range(81)],
            ego_dimensions=[1.6, 3.0, 1.5],
            obstacles=[],
            comparators={"final": {"hazard_time": 8, "rc": 0.7}},
        ),
        points=[[0.0, 0.5, 19.2]] * 101 if blocked else [[50.0, 0.5, 50.0]],
        ground=[
            [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
        ],
    )


def produce(folder, old, method, blocked=False, cap=2048):
    folder.mkdir()
    c = case(blocked)
    q = Queries(folder / "masks", query_for(c))
    state = c["geometry"]["reset"]
    prefix = []
    for frame in range(27):
        if frame:
            state = transition(state, [0.0, 0.0], old)
        prefix.append(
            dict(
                id=frame,
                parent=frame - 1 if frame else None,
                frame=frame,
                state=state,
                action=[0.0, 0.0] if frame else None,
                route=route_outcome(state, c["geometry"]["route"]),
                background=q(state),
                reason="clear",
            )
        )
    result = run(method, state, 26, c["geometry"], old, cap, q, time.monotonic() + 20, 1073741824)
    q.finish()
    return c, prefix, result
