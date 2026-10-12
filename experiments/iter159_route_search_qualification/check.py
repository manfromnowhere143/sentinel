"""Independent scalar path admission and mechanical witness-loss audit.

No search, guidance, proposal-generator or vector collision implementation is
imported. Full search-tree collision labels remain producer evidence.
"""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import time

from experiments.iter158_constraint_aware_search.check import verify_path
from .common import BASE, OLD, encode, git, read, require, rss, sha, source_check, write


def equivalent(a, b):
    return len(a) == len(b) and all(abs(x - y) <= 1e-10 for x, y in zip(a, b))


def key(row):
    x, y, h, v, d = row["state"]
    return math.floor(x / 2), math.floor(y / 0.5), round(h / 0.1), round(v / 0.5), round(d / 0.065)


def ordering(row):
    return (
        row["guide_distance"],
        -row["route"]["nearest"],
        row["route"]["distance"],
        abs(row["state"][4]),
        row["effort"],
        row["id"],
    )


def audit_beam(rows, width, pruning):
    representatives = {}
    for row in sorted(rows, key=ordering):
        representatives.setdefault(key(row), row)
    ordered = list(representatives.values())
    if pruning == "rank":
        return [r["id"] for r in ordered[:width]]
    require(pruning == "speed_groups", "pruning")
    group_position, layered = Counter(), []
    for row in ordered:
        group = round(row["state"][3])
        layered.append((group_position[group], ordering(row), row["id"]))
        group_position[group] += 1
    return [r[2] for r in sorted(layered)[:width]]


def witness_loss(witness, attempts, depths):
    """First lost exact prefix, not a claim that all feasible paths were lost."""
    primitive = [[float(a), r * math.pi / 12] for a in (-2, 0, 2) for r in (-1, -0.5, 0, 0.5, 1)]
    require(
        all(any(equivalent(r["action"], p) for p in primitive) for r in witness[1:]),
        "witness_proposal_coverage",
    )
    parent = 0
    by_parent = {}
    for row in attempts[1:]:
        by_parent.setdefault(row["parent"], []).append(row)
    for target in witness[1:]:
        frame = target["frame"]
        if frame > len(depths) or not depths[frame - 1]["complete"]:
            return dict(frame=frame, cause="run_stopped_before_prefix", proposal_coverage=True)
        matching = [r for r in by_parent.get(parent, []) if r["action"] == target["action"]]
        require(len(matching) == 1, "covered_witness_action_missing")
        child = matching[0]
        require(equivalent(child["state"], target["state"]), "witness_state")
        require(child["reason"] == "clear", "feasible_witness_rejected")
        if child["route"]["rc"] >= 1:
            return dict(frame=frame, cause="witness_completed", proposal_coverage=True)
        if child["id"] not in depths[frame - 1]["beam"]:
            peers = [
                r
                for r in attempts
                if r["frame"] == frame and r["reason"] == "clear" and key(r) == key(child)
            ]
            winner = min(peers, key=ordering)
            return dict(
                frame=frame,
                cause="cell_representative" if winner["id"] != child["id"] else "beam_width",
                attempt=child["id"],
                representative=winner["id"],
                proposal_coverage=True,
            )
        parent = child["id"]
    raise ValueError("witness_not_complete")


def audit_run(folder, result, witness, plan):
    attempts = [json.loads(line) for line in read(folder, "attempts.jsonl").splitlines()]
    depths = [json.loads(line) for line in read(folder, "depths.jsonl").splitlines()]
    require(len(attempts) == result["attempts"] + 1, "attempt_count")
    require(0 <= result["attempts"] <= plan["attempt_budget"], "attempt_budget")
    require(sum(r["background"] is not None for r in attempts) == result["queries"], "query_count")
    require(Counter(r["reason"] for r in attempts[1:]) == result["counts"], "counts")
    beam, by_frame = [0], {}
    for i, row in enumerate(attempts):
        require(type(row["id"]) is int and row["id"] == i, "attempt_order")
        if i:
            require(type(row["parent"]) is int and 0 <= row["parent"] < i, "parent_order")
            require(row["frame"] == attempts[row["parent"]]["frame"] + 1, "parent_depth")
        by_frame.setdefault(row["frame"], []).append(row)
    require([d["frame"] for d in depths] == list(range(1, len(depths) + 1)), "depth_sequence")
    require(all(d["complete"] is True for d in depths[:-1]), "partial_depth")
    for depth in depths:
        rows = by_frame.get(depth["frame"], [])
        require(all(r["parent"] in beam for r in rows), "expanded_pruned_parent")
        survivors = [r for r in rows if r["reason"] == "clear"]
        require(len(survivors) == depth["survivors"], "survivor_count")
        expected = audit_beam(survivors, plan["beam_width"], result["pruning"])
        if depth["complete"]:
            require(depth["beam"] == expected, "beam_replay")
            beam = expected
        else:
            require(depth["beam"] == [], "partial_beam")
    require(sum(d["complete"] for d in depths) == result["completed_depth"], "completed_depth")
    trace = json.loads(read(folder / "selected", "trace.json"))
    require(all(row == attempts[row["id"]] for row in trace), "trace_binding")
    stop = result["stop"]
    require(
        stop in {"model_complete", "beam_empty", "horizon", "attempt_budget", "time_budget"}, "stop"
    )
    if stop == "model_complete":
        require(
            result["selected"] == trace[-1]["id"] and trace[-1]["route"]["rc"] >= 1,
            "selected_identity",
        )
        require(trace[-1]["frame"] == result["completed_depth"], "selected_depth")
    else:
        require(result["selected"] is None and trace[-1]["route"]["rc"] < 1, "false_completion")
    if stop == "beam_empty":
        require(depths[-1]["complete"] and not depths[-1]["beam"], "false_beam_empty")
    if stop == "attempt_budget":
        require(result["attempts"] == plan["attempt_budget"], "false_budget")
    if stop == "horizon":
        require(result["completed_depth"] == plan["max_actions"], "false_horizon")
    return trace, witness_loss(witness, attempts, depths)


def check(root, raw, commit):
    started = time.monotonic()
    plan = json.loads(read(root, BASE / "PLAN.json"))
    names = (
        git(root, "ls-tree", "-r", "--name-only", commit, "--", raw.relative_to(root).as_posix())
        .decode()
        .splitlines()
    )
    actual_names = {p.relative_to(root).as_posix() for p in raw.rglob("*") if p.is_file()}
    require(set(names) == actual_names, "raw_inventory")
    size = 0
    for name in names:
        data = read(root, name)
        size += len(data)
        require(git(root, "show", commit + ":" + name) == data, "raw_not_committed")
    require(size <= plan["max_output_bytes"], "output_budget")
    execution = json.loads(read(raw, "execution.json"))
    initialized = json.loads(read(raw, "initialized.json"))
    source_check(root, plan, execution["source_commit"])
    git(root, "merge-base", "--is-ancestor", execution["source_commit"], commit)
    require(execution["status"] == "completed", "execution_status")
    require(execution["plan_sha256"] == sha(encode(plan)), "plan_identity")
    require(
        initialized["source_commit"] == execution["source_commit"]
        and initialized["plan_sha256"] == execution["plan_sha256"]
        and initialized["cases_sha256"] == sha(read(root, BASE / "CASES.json")),
        "initialization_identity",
    )
    require(0 < execution["elapsed_seconds"] <= plan["producer_seconds"], "producer_time")
    require(0 < execution["peak_rss_bytes"] <= plan["max_rss_bytes"], "producer_memory")
    cases = json.loads(read(root, BASE / "CASES.json"))
    require(len(cases) == 4 and len({c["id"] for c in cases}) == 4, "case_population")
    old = json.loads(read(root, OLD))
    admitted, witnesses, expected, states = [], [], {"execution.json", "initialized.json"}, 0
    deadline = started + plan["checker_seconds"]

    def replay(folder, trace, case, complete):
        for name in ["trace.json", *(f"mask_{i:03d}.bin" for i in range(len(trace)))]:
            expected.add((folder / name).relative_to(raw).as_posix())
        metrics = verify_path(
            trace,
            case["geometry"],
            old,
            case["points"],
            case["ground"],
            lambda i: read(folder, f"mask_{i:03d}.bin"),
            complete,
            deadline,
        )
        return metrics

    for case in cases:
        folder = raw / (case["id"] + "_witness")
        trace = json.loads(read(folder, "trace.json"))
        metrics = replay(folder, trace, case, True)
        require(metrics["progress_checks"] == 2, "witness_checkpoints")
        require(
            all(
                equivalent(r["action"], case["witness_actions"][i]) for i, r in enumerate(trace[1:])
            ),
            "witness_actions",
        )
        witnesses.append(dict(case=case["id"], **metrics))
        states += metrics["verified_states"]
        for ranking, pruning in plan["arms"]:
            name = f"{case['id']}_{ranking}_{pruning}"
            folder = raw / name
            result = json.loads(read(folder, "result.json"))
            require(
                result["name"] == name
                and result["case"] == case["id"]
                and result["ranking"] == ranking
                and result["pruning"] == pruning,
                "arm_identity",
            )
            require(0 < result["elapsed_seconds"] <= plan["per_run_seconds"] + 5, "run_time")
            for filename in ("attempts.jsonl", "depths.jsonl", "result.json"):
                expected.add(f"{name}/{filename}")
            selected, loss = audit_run(folder, result, trace, plan)
            complete = result["stop"] == "model_complete"
            metrics = replay(folder / "selected", selected, case, complete)
            states += metrics["verified_states"]
            admitted.append(dict(**result, **metrics, complete=complete, witness_loss=loss))
            require(rss() <= plan["max_rss_bytes"], "checker_memory")
    require(
        [r["name"] for r in execution["records"]] == [r["name"] for r in admitted],
        "record_population",
    )
    for recorded, verified in zip(execution["records"], admitted):
        require(all(verified[k] == v for k, v in recorded.items()), "record_binding")
    require(
        {p.relative_to(raw).as_posix() for p in raw.rglob("*") if p.is_file()} == expected,
        "raw_file_set",
    )
    candidate = [r for r in admitted if r["ranking"] == "route" and r["pruning"] == "speed_groups"]
    qualified = all(r["complete"] for r in candidate)
    require(time.monotonic() <= deadline, "checker_deadline")
    return dict(
        iteration=159,
        status="supported" if qualified else "contradicted",
        phase="closed",
        claim="The registered route/speed-group arm completes all four fixtures.",
        source_commit=execution["source_commit"],
        raw_commit=commit,
        cases=4,
        runs=len(admitted),
        candidate_completions=sum(r["complete"] for r in candidate),
        complete_runs=sum(r["complete"] for r in admitted),
        incomplete_runs=sum(not r["complete"] for r in admitted),
        verified_states=states,
        witnesses=witnesses,
        records=admitted,
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
        all_pruning_independently_replayed=False,
        beam_selection_from_retained_scores_replayed=True,
        background_between_samples=None,
        native_recovery=None,
        road_compliance=None,
        information_benefit=None,
        transfer=None,
        new_driving_episodes=0,
        provider_spend=0,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True, type=Path)
    p.add_argument("--raw", required=True, type=Path)
    p.add_argument("--raw-commit", required=True)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    write(args.output, check(args.root.resolve(), args.raw.resolve(), args.raw_commit))
