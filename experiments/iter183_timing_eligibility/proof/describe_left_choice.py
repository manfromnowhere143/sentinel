"""Bind the matched left-call program inventory across parent and candidate."""

import copy
import json
from pathlib import Path

from experiments.iter183_timing_eligibility.common import encode, git, read, require, sha, write


def programs(events):
    return [
        {k: v for k, v in row.items() if k not in {"selected_prefix", "eligibility"}}
        for row in events
        if row["kind"] == "evaluation" and row["call"] == 91
    ]


def main():
    root = Path.cwd()
    sources = [
        (
            "36383c3dd420ab7a8d7efad4c4808c3bae37c09b",
            "experiments/iter181_checkpoint_prefix_selection/proof/search_raw/bend_left/events.jsonl",
        ),
        (
            "172cf0f5449e4171c3f9a25bc45d6e6cb7f03bd5",
            "experiments/iter183_timing_eligibility/proof/search_raw/bend_left/events.jsonl",
        ),
    ]
    inventories, hashes = [], []
    for commit, name in sources:
        data = read(root, name)
        require(data == git(root, "show", commit + ":" + name), "source_identity")
        inventories.append([json.loads(line) for line in data.splitlines()])
        hashes.append(dict(commit=commit, path=name, sha256=sha(data)))
    old, new = inventories
    old_programs, new_programs = programs(old), programs(new)
    require(old_programs and encode(old_programs) == encode(new_programs), "matched_programs")
    corrupted = copy.deepcopy(new_programs)
    corrupted[0]["trace"][-1]["state"][0] += 0.001
    require(encode(corrupted) != encode(old_programs), "known_bad_changed_state")
    connections = [
        next(r for r in events if r["kind"] == "connection" and r["call"] == 91)
        for events in inventories
    ]
    require(
        all(connections[0][k] == connections[1][k] for k in ("before", "target", "task", "budget")),
        "matched_request",
    )
    parent, candidate = [r["result"] for r in connections]
    require(
        (parent["selected_evaluation"], parent["selected_prefix"]) == (12, 6)
        and (candidate["selected_evaluation"], candidate["selected_prefix"]) == (1, 8),
        "selected_identity",
    )
    rejected = next(
        r for r in new if r["kind"] == "evaluation" and r["call"] == 91 and r["id"] == 12
    )
    certificate = next(r for r in rejected["eligibility"]["records"] if r["prefix"] == 6)
    require(
        certificate["excluded"] is True and certificate["completion"]["excluded"] is True,
        "premature_certificate",
    )
    write(
        root / "experiments/iter183_timing_eligibility/proof/left_choice_notes.json",
        dict(
            status="supported",
            scope="Descriptive matched-request/program identity after independent admissions; one exposed case.",
            sources=hashes,
            call=91,
            matched_evaluations=len(old_programs),
            matched_programs_sha256=sha(encode(old_programs)),
            parent=dict(evaluation=12, prefix=6, frame=connections[0]["trace"][-1]["frame"]),
            candidate=dict(evaluation=1, prefix=8, frame=connections[1]["trace"][-1]["frame"]),
            rejected_parent_choice=certificate,
            known_bad_changed_state_rejected=True,
            boundary="This local choice avoids the admitted early-completion trap. The candidate subsequently completes the left case; no general selection, allocation or superiority claim.",
        ),
    )
    print(
        json.dumps(dict(matched_evaluations=len(old_programs), parent_frame=29, candidate_frame=31))
    )


if __name__ == "__main__":
    main()
