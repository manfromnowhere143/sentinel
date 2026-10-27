"""Independent population reconstruction from native events and admitted paths."""

import json

from .common import CASES, GEOMETRY, HISTORY, PARENT, read, require


def verify_population(root, population):
    require(set(population) == {"schema", "parent_commit", "rule", "endpoints", "successful_transition_controls"}, "population_schema")
    require(population["schema"] == "sentinel.iter188.population.v1" and population["parent_commit"] == PARENT, "population_parent")
    cases = {r["id"]: r["geometry"] for r in json.loads(read(root, GEOMETRY))}
    expected = []
    for case in CASES:
        nodes = {}
        events = read(root, HISTORY[187] + f"/proof/search_raw/{case}/events.jsonl").splitlines()
        for encoded in events:
            row = json.loads(encoded)
            if row["kind"] != "native_event" or row["event"]["kind"] not in (0, 1, 2):
                continue
            event = row["event"]
            node = event["node"]
            require(node not in nodes and len(event["state"]) == 6 and float(event["state"][5]).is_integer(), "native_node_identity")
            if event["kind"] == 0:
                require(not nodes and node == 1 and event["parent"] == event["token"] == 0 and event["state"] == [*cases[case]["reset"], 0], "native_root")
            else:
                require(event["parent"] in nodes and nodes[event["parent"]]["frame"] < event["state"][5], "native_parent")
            nodes[node] = dict(id=f"{case}:{node}", case=case, node=node, parent=event["parent"],
                               token=event["token"], origin={0: "root", 1: "primary", 2: "extra"}[event["kind"]],
                               frame=int(event["state"][5]), state=event["state"][:5])
        expected.extend(nodes[n] for n in sorted(nodes))
    require(population["endpoints"] == expected, "complete_endpoint_population")
    controls = []
    paths = []
    for iteration in (178, 183, 187):
        directory = HISTORY[iteration]
        admission = json.loads(read(root, directory + "/proof/admission.json"))
        require(admission["iteration"] == iteration and admission["phase"] == "closed" and admission["complete_cases"] == 3 and admission["total_cases"] == 4, "admitted_history")
        require({r["case"] for r in admission["records"]} == set(CASES), "history_population")
        prior = json.loads(read(root, directory + "/PLAN.json"))
        require(prior["cases"] == list(CASES) and prior["fixture_version"] == "full-reflection-v1", "history_fixture")
        for case in CASES:
            outcome = next(r for r in admission["records"] if r["case"] == case)
            require(type(outcome["complete"]) is bool, "history_complete_type")
            if not outcome["complete"]:
                continue
            path = directory + f"/proof/search_raw/{case}/selected/trace.json"
            trace = json.loads(read(root, path))
            require(trace[0]["state"] == cases[case]["reset"] and trace[-1]["route"]["rc"] >= 1 and trace[-1]["frame"] >= 32, "successful_history")
            paths.append(path)
            for i in range(len(trace) - 1):
                require(trace[i]["frame"] == i and trace[i + 1]["frame"] == i + 1 and trace[i]["route"]["rc"] < 1, "history_clock")
                controls.append(dict(id=f"{iteration}:{case}:{i}", iteration=iteration, case=case,
                                     path=path, offset=i, frame=i, state=trace[i]["state"], next=trace[i + 1]))
    require(population["successful_transition_controls"] == controls, "complete_success_control_population")
    return dict(endpoints=len(expected), successful_paths=len(paths), successful_transition_controls=len(controls))
