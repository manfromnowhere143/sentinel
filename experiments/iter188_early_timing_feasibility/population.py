"""Freeze every registered endpoint and every successful-path transition root.

No new bound, motion evaluation, control proposal or outcome inference.
"""

import json

from .common import CASES, GEOMETRY, HISTORY, PARENT, read, require


def collect(root):
    geometries = {c["id"]: c["geometry"] for c in json.loads(read(root, GEOMETRY))}
    endpoints, controls = [], []
    for case in CASES:
        geometry = geometries[case]
        endpoints.append(dict(id=f"{case}:1", case=case, node=1, parent=0, token=0,
                              origin="root", frame=0, state=geometry["reset"]))
        sequence = json.loads(read(root, HISTORY[187] + f"/proof/search_raw/{case}/sequences.json"))
        for token, segment in sorted(sequence.items(), key=lambda row: row[1]["node"]):
            last = segment["trace"][-1]
            endpoints.append(dict(id=f"{case}:{segment['node']}", case=case,
                                  node=segment["node"], parent=segment["parent"], token=int(token),
                                  origin="extra" if segment["extra"] else "primary",
                                  frame=last["frame"], state=last["state"]))
    for iteration, directory in HISTORY.items():
        admission = json.loads(read(root, directory + "/proof/admission.json"))
        require(admission["phase"] == "closed" and admission["complete_cases"] == 3, "prior_admission")
        records = {r["case"]: r for r in admission["records"]}
        for case in CASES:
            if not records[case]["complete"]:
                continue
            path = directory + f"/proof/search_raw/{case}/selected/trace.json"
            trace = json.loads(read(root, path))
            for offset, row in enumerate(trace[:-1]):
                controls.append(dict(id=f"{iteration}:{case}:{offset}", iteration=iteration,
                                     case=case, path=path, offset=offset, frame=row["frame"],
                                     state=row["state"], next=trace[offset + 1]))
    require(len({r["id"] for r in endpoints}) == len(endpoints), "endpoint_duplicates")
    return dict(schema="sentinel.iter188.population.v1", parent_commit=PARENT,
                rule="Every Iter187 native root and registered primary/extra endpoint, without outcome or frame filtering; every nonterminal row of every admitted Iter178/183/187 completed path.",
                endpoints=endpoints, successful_transition_controls=controls)
