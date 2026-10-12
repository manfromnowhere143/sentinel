"""Content bindings and historical ancestry; no dynamics or geometry."""

import json
from pathlib import Path

from experiments.iter158_constraint_aware_search.common import (
    encode,
    git,
    read,
    require,
    rss,
    sha,
    write,
)

BASE = Path("experiments/iter160_continuation_preservation")
PREVIOUS = Path("experiments/iter159_route_search_qualification")
OLD = Path("experiments/iter153_action_feasibility/PLAN.json")


def source_check(root, plan, source):
    require(len(source) == 40 and all(c in "0123456789abcdef" for c in source), "source_encoding")
    for name in [str(BASE / "PLAN.json"), *plan["source_files"], *plan["input_files"]]:
        data = read(root, name)
        require(git(root, "show", source + ":" + name) == data, "source_changed:" + name)
        if name in plan["input_files"]:
            require(sha(data) == plan["input_files"][name], "input_identity:" + name)


def prefix(rows, identity):
    selected = []
    while True:
        require(type(identity) is int and 0 <= identity < len(rows), "ancestry_index")
        row = rows[identity]
        require(row["id"] == identity and row["reason"] == "clear", "ancestry_row")
        selected.append({k: row[k] for k in ("frame", "action", "state")})
        if row["parent"] is None:
            require(identity == 0, "ancestry_reset")
            break
        require(type(row["parent"]) is int and 0 <= row["parent"] < identity, "ancestry_parent")
        identity = row["parent"]
    selected.reverse()
    require([r["frame"] for r in selected] == list(range(len(selected))), "ancestry_frames")
    require(selected[0]["action"] is None, "ancestry_reset_action")
    return selected


def validate_inputs(root, inputs):
    admission = json.loads(read(root, PREVIOUS / "proof/admission.json"))
    require(
        sha(read(root, PREVIOUS / "proof/admission.json")) == inputs["admission_sha256"],
        "admission_identity",
    )
    records = {r["name"]: r for r in admission["records"]}
    require(
        len(inputs["pairs"]) == 5 and len({p["id"] for p in inputs["pairs"]}) == 5,
        "pair_population",
    )
    seen = []
    for pair in inputs["pairs"]:
        witness = json.loads(
            read(root, PREVIOUS / "proof/raw" / (pair["case"] + "_witness") / "trace.json")
        )
        frame = pair["frame"]
        require(
            pair["discarded_prefix"]
            == [{k: r[k] for k in ("frame", "action", "state")} for r in witness[: frame + 1]],
            "witness_prefix",
        )
        require(pair["suffix"] == [r["action"] for r in witness[frame + 1 :]], "suffix_binding")
        require(pair["discarded_prefix"][-1]["state"] == pair["discarded_state"], "discarded_state")
        require(
            pair["representative_prefix"][-1]["state"] == pair["representative_state"],
            "representative_state",
        )
        for binding in pair["bindings"]:
            name = binding["run"]
            seen.append(name)
            loss = records[name]["witness_loss"]
            require(
                records[name]["case"] == pair["case"]
                and loss["cause"] == "cell_representative"
                and loss["frame"] == frame
                and loss["attempt"] == binding["attempt"]
                and loss["representative"] == binding["representative"],
                "loss_binding",
            )
            data = read(root, PREVIOUS / "proof/raw" / name / "attempts.jsonl")
            require(sha(data) == binding["attempts_sha256"], "attempt_identity")
            rows = [json.loads(line) for line in data.splitlines()]
            require(
                prefix(rows, binding["attempt"]) == pair["discarded_prefix"], "discarded_ancestry"
            )
            require(
                prefix(rows, binding["representative"]) == pair["representative_prefix"],
                "representative_ancestry",
            )
    require(len(seen) == 16 and set(seen) == set(records), "binding_population")


__all__ = [
    "BASE",
    "PREVIOUS",
    "OLD",
    "encode",
    "git",
    "read",
    "require",
    "rss",
    "sha",
    "write",
    "source_check",
    "prefix",
    "validate_inputs",
]
