"""Post-admission descriptive inventory; no new probes or causal attribution."""

from collections import Counter
import json
from pathlib import Path

from .common import BASE, read, sha, write


def describe(root):
    bindings, records = {}, []

    def load(path):
        data = read(root, path)
        bindings[str(path)] = sha(data)
        return data

    admission = json.loads(load(BASE / "proof/admission.json"))
    for result in admission["records"]:
        case = result["case"]
        folder = BASE / "proof/search_raw" / case
        sequences = json.loads(load(folder / "sequences.json"))
        late = {
            s["node"]: dict(
                node=s["node"],
                parent=s["parent"],
                token=int(token),
                state=s["trace"][-1]["state"],
                frame=s["trace"][-1]["frame"],
                requests=0,
                evaluations=0,
                maximum_valid_frame=None,
            )
            for token, s in sequences.items()
            if 24 <= s["trace"][-1]["frame"] < 32
        }
        reasons, frames, node = Counter(), Counter(), None
        for line in load(folder / "events.jsonl").splitlines():
            event = json.loads(line)
            if event["kind"] == "native_event" and event["event"]["kind"] == 3:
                node = event["event"]["node"]
                if node in late:
                    late[node]["requests"] += 1
            elif event["kind"] == "evaluation":
                reason = next((r["reason"] for r in event["trace"] if r["reason"] != "clear"), None)
                if reason:
                    reasons[reason] += 1
                for record in event["eligibility"]["records"]:
                    if record["excluded"] and record["status"] != "inherited_exclusion":
                        frames[str(record["frame"])] += 1
                if node in late:
                    late[node]["evaluations"] += 1
                    frame = event["trace"][event["valid_prefix"]]["frame"]
                    previous = late[node]["maximum_valid_frame"]
                    late[node]["maximum_valid_frame"] = (
                        frame if previous is None else max(frame, previous)
                    )
        records.append(
            dict(
                case=case,
                maximum_registered_frame=max(s["trace"][-1]["frame"] for s in sequences.values()),
                late_precheckpoint_nodes=[late[n] for n in sorted(late)],
                uniform_exclusion_evaluations_by_frame=dict(sorted(frames.items())),
                first_rejection_reasons=dict(sorted(reasons.items())),
            )
        )
    value = dict(
        status="descriptive",
        iteration=189,
        raw_commit=admission["raw_commit"],
        admission_sha256=bindings[str(BASE / "proof/admission.json")],
        inputs=bindings,
        records=records,
        scope="Post-admission complete registered-node/event inventory. No new search, masks or feasibility claim. Unexpanded does not mean feasible; rejection counts do not identify a causal mechanism.",
    )
    write(root / BASE / "proof/descriptive.json", value)
    return value


if __name__ == "__main__":
    describe(Path.cwd())
