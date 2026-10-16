"""Two constructed advancing prefixes; no retained scene or continuation search."""

import copy

from experiments.iter153_action_feasibility.check import motion
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter172_integrated_rrt.check import outcome
from experiments.iter182_late_frontier_timing.produce import Masks
from experiments.iter184_discarded_progress.produce import extract
from experiments.iter184_discarded_progress.retained import population
from .common import write


def create(folder, old):
    folder.mkdir()
    case = dict(
        geometry=dict(
            reset=[0.0, 0.0, 0.0, 1.3, 0.0],
            route=[[0.0, i / 4] for i in range(81)],
            ego_dimensions=[1.6, 3.0, 1.5],
            obstacles=[],
            comparators=dict(final=dict(hazard_time=8.0, rc=0.1)),
        ),
        points=[[10.0, 0.5, 10.0]],
        ground=[
            [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
        ],
    )
    query = query_for(case)
    state = case["geometry"]["reset"]
    trace = []
    for i in range(4):
        if i:
            state = motion(state, [0.0, 0.0])
        trace.append(
            dict(
                id=i,
                frame=i,
                parent=i - 1 if i else None,
                action=[0.0, 0.0] if i else None,
                state=state,
                background=summary(query(state)),
                route=outcome(state, case["geometry"]),
                reason="clear",
            )
        )
    first = dict(
        call=1,
        before=[*trace[0]["state"], 0],
        trace=copy.deepcopy(trace[:2]),
        result=dict(attempts=5, selected_evaluation=1, selected_prefix=1),
    )
    duplicate = dict(copy.deepcopy(first), call=2)
    start = dict(copy.deepcopy(trace[1]), parent=None, action=None)
    final = dict(
        call=3,
        before=[*trace[1]["state"], 1],
        trace=[start],
        result=dict(attempts=9, selected_evaluation=None, selected_prefix=0),
    )
    trial = dict(
        call=3, id=1, trace=[start] + copy.deepcopy(trace[2:]), eligibility=dict(eligible_prefix=2)
    )
    connections, trials = [first, duplicate, final], [trial]
    _, records, maxima = population(connections, trials)
    masks = Masks(folder / "masks", query)
    paths = []
    for k in (1, 2):
        path = extract(connections, trial, k)
        path.update(
            masks=masks.path(path["trace"]),
            certificates=dict(status="outside_window", progress=None, completion=None),
            selected_for_probe=k == 2,
        )
        paths.append(path)
    write(folder / "paths.json", paths)
    masks.finish()
    return dict(
        raw=folder,
        case=case,
        old=old,
        connections=connections,
        trials=trials,
        records=records,
        maxima=maxima,
        plan=dict(max_rss_bytes=1073741824),
        execution=dict(path_records=2, distinct_masks=len(masks.rows), new_motion_searches=0),
    )
