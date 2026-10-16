"""Corrected orchestration around unchanged independent scalar prefix replay."""

import argparse
from pathlib import Path
import time

from experiments.iter179_frontier_continuation_audit.check import scalar_masks
from experiments.iter184_discarded_progress.retained import identity
from experiments.iter184_discarded_progress.replay import (
    population_check,
    binding,
    path_check,
    certificates_check,
)
from .common import BASE, document, read, write, require, rss, git, sha, source_check
from .context import preflight, RAW, PRODUCER, check_plan


def replay(context, deadline):
    raw, case, old = context["raw"], context["case"], context["old"]
    masks = scalar_masks(raw, case, deadline)
    paths = document(raw, "paths.json")
    high = population_check(paths, context["connections"], context["trials"], case["geometry"])
    require(len(paths) == len(context["records"]), "complete_prefix_population")
    used, rows = set(), []
    for path, record in zip(paths, context["records"]):
        require(time.monotonic() < deadline, "audit_checker_deadline")
        require(identity(path) == identity(record), "path_identity")
        binding(path, context["connections"], context["trials"], case["geometry"]["reset"])
        checks = path_check(path["trace"], path["masks"], case, old, masks)
        progress, premature = certificates_check(path["certificates"], path["trace"][-1], case, old)
        selected = identity(path) in [identity(m) for m in context["maxima"]]
        require(path["selected_for_probe"] is selected, "probe_selection")
        used.update(path["masks"])
        rows.append(
            dict(
                call=path["call"],
                evaluation=path["evaluation"],
                prefix=path["prefix"],
                frame=path["trace"][-1]["frame"],
                selected_for_probe=selected,
                progress_excluded=progress,
                premature_excluded=premature,
                timing_applicable=path["certificates"]["status"] == "checked",
                verified_states=len(path["trace"]),
                checkpoint_checks=checks,
                ambiguous_joins=path["ambiguous_joins"],
                continuation=None,
            )
        )
    execution = context["execution"]
    require(
        used == set(masks)
        and execution["path_records"] == len(paths)
        and execution["distinct_masks"] == len(masks)
        and execution["new_motion_searches"] == 0,
        "audit_accounting",
    )
    require(
        time.monotonic() < deadline and rss() <= context["plan"]["max_rss_bytes"],
        "checker_resources",
    )
    return dict(
        path_records=len(paths),
        maximum_retained_nearest_index=high,
        verified_states=sum(r["verified_states"] for r in rows),
        distinct_scalar_states=len(masks),
        scalar_classifications=len(masks) * len(case["points"]),
        selected_roots=sum(r["selected_for_probe"] for r in rows),
        records=rows,
    )


def check(root, source, qualification_commit):
    started = time.monotonic()
    context = preflight(root, source)
    from .qualify import admitted as qualification_admitted

    qualification_admitted(root, qualification_commit, source, context)
    result = replay(context, started + context["plan"]["audit_checker_seconds"])
    require(
        result["path_records"] == 15
        and result["distinct_scalar_states"] == 82
        and result["selected_roots"] == 3,
        "fixed_admission_population",
    )
    result.update(
        iteration=185,
        phase="prefix_admitted",
        status="supported",
        raw_commit=RAW,
        producer_source_commit=PRODUCER,
        source_commit=source,
        validator_source_commit=source,
        metadata=context["metadata"],
        qualification_commit=qualification_commit,
        qualified_for_source_comparison=False,
        full_route_continuations=None,
        corrected_scope="Retained Iter184 prefix admission only; original failure preserved.",
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
    )
    write(root / BASE / "proof/audit_admission.json", result)
    print(
        {
            k: result[k]
            for k in ["status", "path_records", "distinct_scalar_states", "selected_roots"]
        },
        flush=True,
    )
    return result


def admitted(root, commit, plan):
    check_plan(plan)
    name = str(BASE / "proof/audit_admission.json")
    data = read(root, name)
    require(data == git(root, "show", commit + ":" + name), "audit_admission_commit")
    result = document(root, name)
    require(
        result["status"] == "supported"
        and result["phase"] == "prefix_admitted"
        and result["iteration"] == 185
        and result["path_records"] == 15
        and result["distinct_scalar_states"] == 82
        and result["selected_roots"] == 3
        and result["raw_commit"] == RAW
        and result["producer_source_commit"] == PRODUCER
        and result["validator_source_commit"] == result["source_commit"],
        "prefix_not_admitted",
    )
    source_check(root, plan, result["validator_source_commit"])
    git(root, "merge-base", "--is-ancestor", result["validator_source_commit"], commit)
    git(root, "merge-base", "--is-ancestor", commit, "HEAD")
    return result, sha(data)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--qualification-commit", required=True)
    a = p.parse_args()
    check(a.root.resolve(), a.source, a.qualification_commit)
