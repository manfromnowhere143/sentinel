"""Post-admission description of existing records; no search or new admission."""

import hashlib
import json
import math
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
BASE = "experiments/iter180_equal_work_continuation/"
INPUTS = {}


def retained(commit, path):
    data = subprocess.check_output(["git", "show", commit + ":" + path], cwd=ROOT)
    assert data == (ROOT / path).read_bytes()
    INPUTS[path] = dict(commit=commit, sha256=hashlib.sha256(data).hexdigest())
    return data


def metric(row, target):
    values = [*row["state"], row["frame"]]
    differences = [a - b for a, b in zip(values, target)]
    differences[2] = math.remainder(differences[2], 2 * math.pi)
    return math.sqrt(sum((d * w) ** 2 for d, w in zip(differences, (1, 1, 2, 0.5, 2, 0.01))))


def describe():
    original = "1ba6a4e90db895fe2991eeb2df26fc3b48ccdeba"
    raw = "b9a86860a6b58c676c55620cf8ce9aa83a941128"
    admitted = "a133930242bca149801a1fbd9bb808ff2a8a36a1"
    events = [
        json.loads(line)
        for line in retained(
            original,
            "experiments/iter178_root_domain_consistency/proof/search_raw/bend_right/events.jsonl",
        ).splitlines()
    ]
    retained(original, "experiments/iter178_root_domain_consistency/connection.py")
    retained(original, "experiments/iter167_planner_terminal_contract/adapter.py")
    admission = json.loads(retained(admitted, BASE + "proof/admission.json"))
    assert admission["status"] == "null" and admission["raw_commit"] == raw
    runs = json.loads(retained(raw, BASE + "proof/study_raw/runs.json"))
    run = next(r for r in runs if r["call"] == 51 and r["arm"] == "program")
    assert run["index"] == 3 and run["result"]["witness"] is True
    path = json.loads(retained(raw, BASE + "proof/study_raw/run_03/trace.json"))
    evaluations = [e for e in events if e["kind"] == "evaluation" and e["call"] == 67]
    connection = next(e for e in events if e["kind"] == "connection" and e["call"] == 67)
    clear = [
        e
        for e in events
        if e["kind"] == "evaluation"
        and e["trace"][0]["frame"] >= 12
        and all(r["reason"] == "clear" for r in e["trace"])
    ]
    assert len(clear) == 1 and clear[0]["call"] == 67 and clear[0]["id"] == 28
    witness = clear[0]
    assert witness["valid_prefix"] == 4 and witness["selected_prefix"] == 1
    fields = ("frame", "state", "action", "route", "reason", "background")
    assert all(
        {k: row[k] for k in fields} == {k: path[row["frame"]][k] for k in fields}
        for row in witness["trace"][1:]
    )
    assert witness["trace"][0]["state"] == path[12]["state"]
    candidates = []
    for e in evaluations:
        options = list(range(1, e["valid_prefix"] + 1)) if e["interrupted"] is None else []
        selected = (
            min(options, key=lambda k: (metric(e["trace"][k], connection["target"]), k))
            if options
            else 0
        )
        if e["world_complete"]:
            selected = e["valid_prefix"]
        assert selected == e["selected_prefix"]
        if selected:
            candidates.append(
                (
                    not e["world_complete"],
                    metric(e["trace"][selected], connection["target"]),
                    e["id"],
                    selected,
                )
            )
    best = min(candidates)
    assert best[2:] == (6, 1)
    assert connection["result"]["selected_evaluation"] == 6
    assert connection["trace"][-1]["frame"] == 13
    return dict(
        status="descriptive",
        scope="Read-only post-admission comparison of committed records. No additional search, integrated result or causal estimate.",
        inputs=INPUTS,
        admission_commit=admitted,
        source_root_call=51,
        original_request_call=67,
        original_evaluations=len(evaluations),
        original_attempts=connection["result"]["attempts"],
        sole_fully_clear_late_evaluation=dict(call=67, evaluation=28, frames=[12, 13, 14, 15, 16]),
        checkpoint_path_matches_admitted_program_suffix_exactly=True,
        admitted_program_run_index=3,
        original_selected_evaluation=6,
        original_selected_prefix=1,
        original_returned_frame=13,
        original_selected_distance=best[1],
        witness_selected_prefix=1,
        witness_prefix_distances=[
            dict(frame=r["frame"], distance=metric(r, connection["target"]))
            for r in witness["trace"][1:]
        ],
        result="A valid frame-16 continuation was generated within the original 128-transition call, but sampled-target prefix ranking returned a frame-13 state from another evaluation.",
        boundary="This identifies a recorded selection loss, not proof that retaining the checkpoint path completes the integrated case or preserves the other three successes.",
    )


if __name__ == "__main__":
    output = describe()
    destination = ROOT / BASE / "proof/selection_notes.json"
    with destination.open("x") as stream:
        stream.write(json.dumps(output, indent=2) + "\n")
    print(json.dumps({k: v for k, v in output.items() if k != "inputs"}, indent=2))
