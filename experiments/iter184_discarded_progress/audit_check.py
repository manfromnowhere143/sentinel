"""Independent prefix acquisition admission; no producer imports."""

import argparse
from pathlib import Path
import time

from experiments.iter179_frontier_continuation_audit.check import scalar_masks
from experiments.iter171_centered_shooting.runtime import identity as runtime_identity
from .common import BASE, document, write, require, rss, read, git, sha
from .records import committed
from .retained import load, OLD, identity
from .contract import check_plan
from .replay import population_check, binding, path_check, certificates_check


def check(root, commit):
    started = time.monotonic()
    plan = document(root, BASE / "PLAN.json")
    check_plan(root, plan)
    require(
        runtime_identity() == document(root, BASE / "RUNTIME.json")["python_runtime"],
        "checker_runtime",
    )
    raw = root / BASE / "proof/audit_retry_raw"
    execution = committed(root, raw, commit, plan)
    case, connections, trials, records, maxima = load(root, plan)
    old = document(root, OLD)
    deadline = started + plan["audit_checker_seconds"]
    masks = scalar_masks(raw, case, deadline)
    paths = document(raw, "paths.json")
    high = population_check(paths, connections, trials, case["geometry"])
    used, rows = set(), []
    for path, record in zip(paths, records):
        require(time.monotonic() < deadline, "audit_checker_deadline")
        require(identity(path) == identity(record), "path_identity")
        binding(path, connections, trials, case["geometry"]["reset"])
        checks = path_check(path["trace"], path["masks"], case, old, masks)
        progress, premature = certificates_check(path["certificates"], path["trace"][-1], case, old)
        selected = identity(path) in [identity(m) for m in maxima]
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
    require(
        used == set(masks)
        and execution["path_records"] == len(paths)
        and execution["distinct_masks"] == len(masks)
        and execution["new_motion_searches"] == 0,
        "audit_accounting",
    )
    require(time.monotonic() < deadline and rss() <= plan["max_rss_bytes"], "checker_resources")
    result = dict(
        iteration=184,
        phase="prefix_admitted",
        status="supported",
        raw_commit=commit,
        source_commit=execution["source_commit"],
        path_records=len(paths),
        maximum_retained_nearest_index=high,
        verified_states=sum(r["verified_states"] for r in rows),
        distinct_scalar_states=len(masks),
        scalar_classifications=len(masks) * len(case["points"]),
        selected_roots=sum(r["selected_for_probe"] for r in rows),
        records=rows,
        qualified_for_source_comparison=False,
        full_route_continuations=None,
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
    name = str(BASE / "proof/audit_admission.json")
    data = read(root, name)
    require(data == git(root, "show", commit + ":" + name), "audit_admission_commit")
    result = document(root, name)
    execution = committed(root, root / BASE / "proof/audit_retry_raw", result["raw_commit"], plan)
    require(
        result["status"] == "supported"
        and result["phase"] == "prefix_admitted"
        and result["path_records"] == 15
        and result["selected_roots"] == 3
        and result["source_commit"] == execution["source_commit"],
        "prefix_not_admitted",
    )
    git(root, "merge-base", "--is-ancestor", result["raw_commit"], commit)
    git(root, "merge-base", "--is-ancestor", commit, "HEAD")
    return result, sha(data)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--raw-commit", required=True)
    a = p.parse_args()
    check(a.root.resolve(), a.raw_commit)
