"""Independent admission: population, corner certificates and scalar controls."""

import argparse
from collections import Counter
import json
from pathlib import Path
import time

from .bound_check import verify as verify_bound
from .common import BASE, CASES, GEOMETRY, HISTORY, OLD, encode, git, read, require, rss, sha, source_check, write
from .contract import check_plan
from .population_check import verify_population
from .probes_check import grid, verify as verify_probe
from .runtime import verify as verify_runtime


def canonical_document(data):
    value = json.loads(data)
    require(encode(value) == data, "noncanonical_record")
    return value


def state_key(row):
    return row["case"], row["frame"], tuple(float(v).hex() for v in row["state"])


def retained_witnesses(controls):
    witnesses = {}
    for item in controls:
        witnesses.setdefault(state_key(item), []).append(item["id"])
        last = item["next"]
        if last["route"]["rc"] >= 1:
            require(last["frame"] >= 32, "completed_suffix_clock")
            endpoint = dict(case=item["case"], frame=last["frame"], state=last["state"])
            witnesses.setdefault(state_key(endpoint), []).append(item["id"] + ":complete")
    return witnesses


def check_record(item, row, group, geometry, old):
    require(set(row) == {"group", "id", "certificate", "probes"} and row["group"] == group and row["id"] == item["id"], "record_identity")
    bound = row["certificate"]
    excluded = verify_bound(bound, item["state"], item["frame"], geometry, old)
    controls = grid(item["state"]) if group == "endpoints" else [item["next"]["action"]]
    require(len(row["probes"]) == len(controls), "probe_population")
    witness = False
    for observed, action in zip(row["probes"], controls):
        witness |= verify_probe(observed, item["state"], item["frame"], action, geometry, bound)
    if group == "successful_transition_controls":
        require(not excluded, "successful_transition_false_exclusion")
        observed, retained = row["probes"][0], item["next"]
        require(observed["controls_valid"] and observed["nearest"] == retained["route"]["nearest"] and observed["rc"] == retained["route"]["rc"], "retained_success_outcome")
        require(all(abs(a - b) <= 1e-12 for a, b in zip(observed["state"], retained["state"])), "retained_success_motion")
        require(retained["frame"] == item["frame"] + 1 and (observed["rc"] < 1 or retained["frame"] >= 32), "retained_success_clock")
    return dict(excluded=excluded, timing_counterexample=witness, probes=len(controls))


def committed(root, commit, plan):
    require(len(commit) == 40 and all(c in "0123456789abcdef" for c in commit), "raw_commit_id")
    prefix = str(BASE / "proof/raw")
    names = git(root, "ls-tree", "-r", "--name-only", commit, "--", prefix).decode().splitlines()
    expected = [prefix + "/" + n for n in ("execution.json", "initialized.json", "records.jsonl")]
    require(names == expected and set(p.name for p in (root / prefix).iterdir()) == {"execution.json", "initialized.json", "records.jsonl"}, "raw_inventory")
    size = 0
    for name in names:
        data = read(root, name, plan["max_output_bytes"])
        require(git(root, "show", commit + ":" + name) == data, "raw_not_committed")
        size += len(data)
    require(size <= plan["max_output_bytes"], "raw_size")
    execution = canonical_document(read(root, prefix + "/execution.json"))
    initialized = canonical_document(read(root, prefix + "/initialized.json"))
    require(set(execution) == {"status", "source_commit", "plan_sha256", "records", "scalar_probes", "elapsed_seconds", "peak_rss_bytes", "new_driving_episodes", "new_integrated_runs", "background_queries", "provider_spend"}, "execution_schema")
    require(execution["status"] == "completed" and initialized == dict(source_commit=execution["source_commit"], plan_sha256=sha(encode(plan))) and execution["plan_sha256"] == initialized["plan_sha256"], "raw_source_identity")
    source_check(root, execution["source_commit"], plan)
    git(root, "merge-base", "--is-ancestor", execution["source_commit"], commit)
    require(0 < execution["elapsed_seconds"] <= plan["producer_seconds"] and 0 < execution["peak_rss_bytes"] <= plan["max_rss_bytes"], "producer_envelope")
    require(all(type(execution[k]) is int and execution[k] >= 0 for k in ("records", "scalar_probes", "peak_rss_bytes", "new_driving_episodes", "new_integrated_runs", "background_queries", "provider_spend")), "execution_types")
    require(all(execution[k] == 0 for k in ("new_driving_episodes", "new_integrated_runs", "background_queries", "provider_spend")), "execution_scope")
    return execution


def check(root, commit):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    check_plan(root, plan)
    verify_runtime(root)
    execution = committed(root, commit, plan)
    population = json.loads(read(root, BASE / "POPULATION.json"))
    population_counts = verify_population(root, population)
    cases = {c["id"]: c["geometry"] for c in json.loads(read(root, GEOMETRY))}
    old = json.loads(read(root, OLD))
    rows = [canonical_document(line) for line in read(root, BASE / "proof/raw/records.jsonl").splitlines(keepends=True)]
    require(len(rows) == len(population["endpoints"]) + len(population["successful_transition_controls"]) == execution["records"], "record_population")
    suffixes = retained_witnesses(population["successful_transition_controls"])
    results, cursor, probes = [], 0, 0
    for group in ("endpoints", "successful_transition_controls"):
        for item in population[group]:
            require(time.monotonic() - started < plan["checker_seconds"] and rss() <= plan["max_rss_bytes"], "checker_resources")
            row = rows[cursor]
            cursor += 1
            checked = check_record(item, row, group, cases[item["case"]], old)
            probes += checked["probes"]
            if group != "endpoints":
                continue
            witnesses = suffixes.get(state_key(item), [])
            require(not (checked["excluded"] and witnesses), "retained_suffix_false_exclusion")
            classification = "excluded" if checked["excluded"] else ("retained_completion" if witnesses else "unknown")
            results.append(dict(**item, classification=classification, bound_reason=row["certificate"]["reason"],
                                timing_counterexample=checked["timing_counterexample"], retained_suffixes=witnesses))
    require(probes == execution["scalar_probes"], "scalar_probe_accounting")
    prior = json.loads(read(root, HISTORY[187] + "/proof/admission.json"))
    counts = Counter(r["classification"] for r in results)
    early = sum(r["classification"] == "excluded" and r["frame"] < 24 and r["origin"] != "root" for r in results)
    by_case = []
    for case in CASES:
        selected = next(r for r in prior["records"] if r["case"] == case)["selected_tokens"][-1]
        current = [r for r in results if r["case"] == case]
        returned = [r for r in current if r["token"] == selected]
        require(len(returned) == 1, "returned_endpoint_identity")
        by_case.append(dict(case=case, total=len(current), excluded=sum(r["classification"] == "excluded" for r in current),
                            early_excluded=sum(r["classification"] == "excluded" and r["frame"] < 24 for r in current),
                            retained_completion=sum(r["classification"] == "retained_completion" for r in current),
                            unknown=sum(r["classification"] == "unknown" for r in current),
                            returned_endpoint=returned[0],
                            excluded_by_origin={origin: sum(r["classification"] == "excluded" and r["origin"] == origin for r in current) for origin in ("root", "primary", "extra")}))
    elapsed = time.monotonic() - started
    require(elapsed <= plan["checker_seconds"] and rss() <= plan["max_rss_bytes"], "checker_final_resources")
    return dict(iteration=188, phase="closed", status="supported" if early else "null",
                claim="At least one registered endpoint before frame 24 is necessarily unable to continue through the final checkpoint under the declared one-step source/numerical model.",
                source_commit=execution["source_commit"], raw_commit=commit,
                total_endpoints=len(results), registered_endpoints=sum(r["origin"] != "root" for r in results),
                excluded_endpoints=counts["excluded"], early_excluded_endpoints=early,
                retained_completion_endpoints=counts["retained_completion"], unknown_endpoints=counts["unknown"],
                timing_counterexample_endpoints=sum(r["timing_counterexample"] for r in results),
                successful_paths=population_counts["successful_paths"], successful_transition_controls=population_counts["successful_transition_controls"],
                false_exclusions=0, scalar_probes=probes, certificate_records=len(rows), records=by_case, endpoints=results,
                elapsed_seconds=elapsed, peak_rss_bytes=rss(), new_driving_episodes=0, new_integrated_runs=0,
                background_queries=0, provider_spend=0, qualified_for_source_comparison=False,
                retained_complete_cases=3, retained_total_cases=4,
                causal_attribution=None, actual_history_intervention=None, superiority=None,
                boundary="Exposed model endpoints; necessary one-step exclusion or retained admitted completion suffix. Unknown does not mean feasible. No planner change, collision re-query, new integrated credit, population or competitive claim.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-commit", required=True)
    args = parser.parse_args()
    root = Path.cwd()
    try:
        result = check(root, args.raw_commit)
        write(root / BASE / "proof/admission.json", result)
        print(json.dumps({k: result[k] for k in ("status", "total_endpoints", "excluded_endpoints", "early_excluded_endpoints", "retained_completion_endpoints", "unknown_endpoints", "successful_transition_controls", "scalar_probes")}))
    except Exception as exc:
        write(root / BASE / "proof/admission_failure.json", dict(status="invalid", error=f"{type(exc).__name__}:{exc}", raw_commit=args.raw_commit))
        raise
