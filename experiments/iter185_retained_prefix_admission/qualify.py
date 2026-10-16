"""Actual production metadata setup followed by complete constructed replay controls."""

import argparse
import copy
from pathlib import Path
import time

from .common import BASE, document, encode, require, write
from .context import preflight
from .audit import replay
from .controls import create
from .records import initialize, finish, failure, committed


def validate_result(result, execution, source, metadata):
    require(
        result["status"] == "supported"
        and result["source_commit"] == source
        and execution["source_commit"] == source
        and execution["stage"] == "qualification",
        "qualification_identity",
    )
    require(
        result["metadata"] == metadata
        and execution["actual_metadata_inputs"] == 12
        and execution["constructed_paths"] == 2
        and execution["rejected_corruptions"] == 5
        and execution["retained_scalar_states"] == execution["conditional_searches"] == 0,
        "qualification_scope",
    )
    require(
        [(r["mutation"], r["reason"]) for r in result["controls"]["rejected"]]
        == [
            ("mask", "scalar_mask"),
            ("state", "path_source_binding"),
            ("missing_prefix", "audited_population"),
            ("ambiguity", "join_ambiguity"),
            ("selected_root", "probe_selection"),
        ],
        "qualification_known_bads",
    )
    require(
        result["controls"]["positive"]["path_records"] == 2
        and result["controls"]["positive"]["selected_roots"] == 1,
        "qualification_positive",
    )


def admitted(root, commit, source, context):
    folder = root / BASE / "proof/qualification_raw"
    execution = committed(root, folder, commit, context["plan"])
    validate_result(document(folder, "result.json"), execution, source, context["metadata"])


def controlled_replay(folder, old, deadline):
    context = create(folder, old)
    result = replay(context, deadline)
    require(result["path_records"] == 2 and result["selected_roots"] == 1, "control_positive")
    paths = document(folder, "paths.json")
    masks = document(folder / "masks", "states.json")
    first_mask = folder / "masks" / (masks[0]["key"] + ".bin")
    saved_mask = first_mask.read_bytes()
    rejected = []
    for mutation, expected in [
        ("mask", "scalar_mask"),
        ("state", "path_source_binding"),
        ("missing_prefix", "audited_population"),
        ("ambiguity", "join_ambiguity"),
        ("selected_root", "probe_selection"),
    ]:
        bad = copy.deepcopy(paths)
        if mutation == "mask":
            first_mask.write_bytes(bytes([saved_mask[0] ^ 1]) + saved_mask[1:])
        elif mutation == "state":
            bad[-1]["trace"][-1]["state"][0] += 0.1
        elif mutation == "missing_prefix":
            bad.pop()
        elif mutation == "ambiguity":
            bad[-1]["ambiguous_joins"] = 0
        else:
            bad[-1]["selected_for_probe"] = False
        (folder / "paths.json").write_bytes(encode(bad))
        try:
            replay(context, deadline)
        except ValueError as error:
            require(str(error) == expected, "control_wrong_rejection:" + str(error))
            rejected.append(dict(mutation=mutation, reason=str(error)))
        else:
            raise ValueError("control_accepted_corruption:" + mutation)
        finally:
            first_mask.write_bytes(saved_mask)
            (folder / "paths.json").write_bytes(encode(paths))
    return dict(positive=result, rejected=rejected)


def run(root, source):
    started = time.monotonic()
    context = preflight(root, source)
    output = root / BASE / "proof/qualification_raw"
    output.parent.mkdir(exist_ok=True)
    plan = initialize(root, output, source, "qualification")
    try:
        controls = controlled_replay(
            output / "constructed", context["old"], started + plan["qualification_producer_seconds"]
        )
        write(
            output / "result.json",
            dict(
                status="supported",
                scope="Metadata and constructed qualification only; no retained-prefix scalar replay.",
                source_commit=source,
                metadata=context["metadata"],
                controls=controls,
            ),
        )
        finish(
            output,
            source,
            plan,
            "qualification",
            started,
            actual_metadata_inputs=len(context["metadata"]),
            constructed_paths=2,
            rejected_corruptions=len(controls["rejected"]),
            retained_scalar_states=0,
            conditional_searches=0,
        )
        print("Actual metadata entrypoint and full constructed replay qualified", flush=True)
    except Exception as error:
        failure(output, started, error)
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--source", required=True)
    a = p.parse_args()
    run(a.root.resolve(), a.source)
