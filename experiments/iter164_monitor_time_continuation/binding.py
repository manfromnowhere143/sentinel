"""Independent historical binding: decision, applied control, state, clock and actors."""

import json

from experiments.iter153_action_feasibility.check import near, motion
from .common import read, require, sha


def bind_history(root, spec, trace, geometry, plan):
    data = read(root, spec["trace_path"])
    decisions = read(root, spec["decision_path"])
    require(
        sha(data) == spec["trace_sha256"] and sha(decisions) == spec["decision_sha256"],
        "historical_bytes",
    )
    events = [json.loads(line) for line in data.splitlines()]
    ds = [json.loads(line) for line in decisions.splitlines()]
    require([r["seq"] for r in events] == list(range(len(events))), "historical_event_order")
    require(
        events[0]["episode"] == spec["episode"]
        and events[0]["arm"] == "monitor"
        and events[0]["seed"] == 144
        and events[0]["route"] == geometry["route"],
        "historical_header",
    )
    start = plan["start_frame"]
    require(
        [d["frame_index"] for d in ds[: start + 1]] == list(range(start + 1)), "decision_sequence"
    )
    require(all(type(d["fired"]) is bool for d in ds[: start + 1]), "decision_bool")
    require(not any(d["fired"] for d in ds[:start]) and ds[start]["fired"] is True, "first_fire")
    require(all(d["ts"] == i / 4 for i, d in enumerate(ds[: start + 1])), "decision_clock")
    reset = [r for r in events if r["event"] == "reset"]
    require(len(reset) == 1 and reset[0]["time"] == 0, "historical_reset")
    near(reset[0]["state"], geometry["reset"], 0)
    require(len(trace) == start + 1, "prefix_inventory")
    steps = [r for r in events if r["event"] == "step" and r["frame"] <= start]
    controls = [r for r in events if r["event"] == "control" and r["frame"] < start]
    observations = [r for r in events if r["event"] == "observation" and r["frame"] <= start]
    outcomes = [r for r in events if r["event"] == "outcome_observation" and r["frame"] <= start]
    monitors = [r for r in events if r["event"] == "monitor" and r["frame"] <= start]
    actors = [
        r["value"]
        for r in events
        if r["event"] == "actor"
        and r["value"]["event"] == "consume"
        and r["value"]["time"] <= start / 4
    ]
    require(
        [r["frame"] for r in steps] == list(range(1, start + 1))
        and [r["frame"] for r in controls] == list(range(start)),
        "prefix_action_inventory",
    )
    require(
        [r["frame"] for r in observations] == list(range(start + 1))
        and [r["frame"] for r in monitors] == list(range(start + 1)),
        "prefix_observation_inventory",
    )
    require(
        [r["frame"] for r in outcomes] == list(range(1, start + 1))
        and [a["time"] for a in actors] == [i / 4 for i in range(1, start + 1)],
        "prefix_outcome_actor_inventory",
    )
    require(len(actors) > 0, "empty_prefix")
    first_actor = actors[0]
    require(
        all(
            a["states"] == first_actor["states"] and a["transforms"] == first_actor["transforms"]
            for a in actors
        ),
        "actor_stationarity",
    )
    for frame, (observation, monitor) in enumerate(zip(observations, monitors)):
        require(json.loads(monitor["raw"]) == ds[frame], "monitor_record_binding")
        require(
            observation["time"] == observation["info"]["timestamp"] == frame / 4,
            "observation_clock",
        )
        near(observation["info"]["obj_boxes"], geometry["obstacles"], 0)
        near(observation["info"]["ego_box"][3:6], geometry["ego_dimensions"], 0)
    near(trace[0]["state"], reset[0]["state"], 0)
    error = 0.0
    for frame, (step, control, outcome) in enumerate(zip(steps, controls, outcomes), 1):
        action = [step["applied"]["acc"], step["applied"]["steer_rate"]]
        require(
            trace[frame]["action"] == action == control["result"]["applied"], "historical_action"
        )
        require(
            control["result"]["application_time"]
            == step["time"]
            == step["info"]["timestamp"]
            == outcome["time"]
            == frame / 4,
            "applied_clock",
        )
        require(control["seq"] < step["seq"] < outcome["seq"], "historical_application_order")
        near(trace[frame - 1]["state"], step["before"], 0)
        near(trace[frame]["state"], step["after"], 0)
        expected = motion(step["before"], action)
        error = max(error, max(abs(a - b) for a, b in zip(expected, step["after"])))
        near(expected, step["after"])
        near(step["info"]["obj_boxes"], geometry["obstacles"], 0)
        near(
            [step["info"]["ego_box"][0], step["info"]["ego_box"][1], step["info"]["ego_box"][6]],
            [step["after"][0], -step["after"][1], -step["after"][2]],
        )
        near(step["info"]["ego_box"][3:6], geometry["ego_dimensions"], 0)
        require(
            outcome["collision"] is False
            and outcome["off_route"] is False
            and outcome["source_completion"] is False,
            "historical_prefix_outcome",
        )
        require(
            outcome["nearest_index"] == trace[frame]["route"]["nearest"], "historical_route_index"
        )
        near(
            [outcome["rc"], outcome["route_distance"]],
            [trace[frame]["route"]["rc"], trace[frame]["route"]["distance"]],
        )
    next_control = next(r for r in events if r["event"] == "control" and r["frame"] == start)
    require(next_control["result"]["application_time"] == (start + 1) / 4, "first_suffix_clock")
    return dict(
        episode=spec["episode"],
        preserved_actions=start,
        first_fire_time=start / 4,
        first_alterable_application_time=(start + 1) / 4,
        maximum_motion_error=error,
        actor_stationary_in_retained_prefix=True,
        historical_outcomes="no collision or off-route observed",
    )
