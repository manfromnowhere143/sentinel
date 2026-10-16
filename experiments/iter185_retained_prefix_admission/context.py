"""All actual entrypoint metadata, exact byte bindings before structural parsing."""

from experiments.iter150_cloud_observation.native import parse
from experiments.iter171_centered_shooting.runtime import identity as runtime_identity
from experiments.iter184_discarded_progress.records import committed as retained_raw
from experiments.iter184_discarded_progress.retained import load, OLD, PREVIOUS
from experiments.iter184_discarded_progress.contract import check_plan as retained_contract
from .common import BASE, document, read, require, encode, sha, git, source_check

PRIOR = "experiments/iter184_discarded_progress/"
PARENT = "643e5eec7eb99767a02cdf28aebf39644457e47e"
RAW = "e5d9f7611e3d401e1b2e72c9e5d59ff7b4ee0ab6"
PRODUCER = "777d6de8e9d8f254c83ab86e9cac987feedb3480"
LEGACY = {OLD, PRIOR + "RUNTIME.json"}


def names():
    return [
        PRIOR + "PLAN.json",
        PRIOR + "RUNTIME.json",
        OLD,
        "experiments/iter161_grouping_width_ablation/CASES.json",
        PREVIOUS + "PLAN.json",
        PREVIOUS + "proof/admission.json",
        PREVIOUS + "proof/frontier_notes.json",
        PREVIOUS + "proof/search_raw/bend_right/result.json",
        *[
            PRIOR + "proof/audit_retry_raw/" + n
            for n in ["initialized.json", "execution.json", "paths.json", "masks/states.json"]
        ],
    ]


def metadata(root, plan):
    require(set(plan["metadata_files"]) == set(names()), "metadata_inventory")
    values, inventory = {}, []
    for name in names():
        raw = read(root, name)
        require(sha(raw) == plan["metadata_files"][name], "metadata_hash:" + name)
        value = parse(raw)
        canonical = encode(value) == raw
        require(name in LEGACY or canonical, "canonical_metadata:" + name)
        values[name] = value
        inventory.append(
            dict(
                path=name, sha256=sha(raw), canonical=canonical, historical_encoding=name in LEGACY
            )
        )
    require(
        values[PRIOR + "RUNTIME.json"] == document(root, BASE / "RUNTIME.json"),
        "runtime_manifest_equivalence",
    )
    require(
        runtime_identity() == values[PRIOR + "RUNTIME.json"]["python_runtime"], "checker_runtime"
    )
    return values, inventory


def check_plan(plan):
    expected = dict(
        iteration=185,
        status="preregistered",
        parent_commit=PARENT,
        retained_raw_commit=RAW,
        producer_source_commit=PRODUCER,
        probe_roots=[[83, 8, 7], [98, 8, 6], [110, 2, 1]],
        remaining_attempts=[7385, 5465, 3929],
        seeds=[20261015] * 3,
        original_wall_seconds=12.51213537500007,
        audit_checker_seconds=900,
        qualification_producer_seconds=300,
        search_producer_seconds=900,
        search_checker_seconds=3600,
        max_output_bytes=268435456,
        max_rss_bytes=1073741824,
        minimum_free_bytes=2147483648,
    )
    require(all(plan.get(k) == v for k, v in expected.items()), "fixed_contract")


def preflight(root, source):
    plan = document(root, BASE / "PLAN.json")
    check_plan(plan)
    source_check(root, plan, source)
    git(root, "merge-base", "--is-ancestor", PARENT, source)
    git(root, "merge-base", "--is-ancestor", source, "HEAD")
    values, inventory = metadata(root, plan)
    prior_plan = values[PRIOR + "PLAN.json"]
    retained_contract(root, prior_plan)
    raw = root / PRIOR / "proof/audit_retry_raw"
    execution = retained_raw(root, raw, RAW, prior_plan)
    require(execution["source_commit"] == PRODUCER, "producer_identity")
    require(
        execution["path_records"] == 15 and execution["distinct_masks"] == 82,
        "retained_collection_counts",
    )
    case, connections, trials, records, maxima = load(root, prior_plan)
    require(
        plan["probe_roots"] == prior_plan["probe_roots"]
        and plan["remaining_attempts"] == prior_plan["remaining_attempts"]
        and plan["seeds"] == prior_plan["seeds"]
        and plan["original_wall_seconds"] == prior_plan["original_wall_seconds"],
        "unchanged_conditional_schedule",
    )
    return dict(
        plan=plan,
        metadata=inventory,
        execution=execution,
        raw=raw,
        case=case,
        connections=connections,
        trials=trials,
        records=records,
        maxima=maxima,
        old=values[OLD],
        parent=values[PREVIOUS + "PLAN.json"],
    )
