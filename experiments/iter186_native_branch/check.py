"""Independent native-event/sequence reconstruction and retained scalar admission."""

import argparse
import copy
import math
from pathlib import Path
import time

from experiments.iter185_retained_prefix_admission.context import preflight
from experiments.iter185_retained_prefix_admission.audit import replay as scalar_replay
from .common import BASE, document, require, write, rss, read, sha
from .records import committed

PARENT_SOURCE = "df50a6b9123ca2389952da795b384225a4f9d980"


def tree(result):
    nodes, tokens, request = {}, set(), None
    for event in result["events"]:
        kind, node = event["kind"], event["node"]
        require(all(math.isfinite(v) for v in event["state"]), "event_finite")
        if kind == 3:
            require(
                node in nodes
                and event["parent"] == node
                and event["state"] == nodes[node]["state"],
                "request_parent",
            )
            request = node
            continue
        require(kind in (0, 1, 2) and node == len(nodes) + 1, "native_node_order")
        if kind == 0:
            require(
                node == 1 and event["parent"] == event["token"] == event["steps"] == 0, "event_root"
            )
        else:
            parent, token = event["parent"], event["token"]
            require(parent == request and parent in nodes, "event_parent")
            require(
                type(token) is int and 1 <= token <= 2**53 - 1 and token not in tokens,
                "event_token",
            )
            require(
                type(event["steps"]) is int
                and 1 <= event["steps"] <= 8
                and event["state"][5] == nodes[parent]["state"][5] + event["steps"],
                "event_duration",
            )
            if kind == 2:
                require(
                    all(event["state"] != n["state"] for n in nodes.values()), "event_duplicate"
                )
            tokens.add(token)
        nodes[node] = event
    previous, used = 0, set()
    for row in result["rows"]:
        require(len(row) == 11 and all(math.isfinite(v) for v in row), "row_encoding")
        require(all(float(row[i]).is_integer() for i in (6, 7, 8, 9)), "row_integer")
        node = int(row[7])
        require(node in nodes and node not in used, "row_node")
        expected = nodes[node]
        require(
            row[:6] == expected["state"]
            and row[6] == expected["token"]
            and row[8] == expected["parent"] == previous
            and row[9] == expected["steps"]
            and row[10] == expected["steps"] / 4,
            "row_binding",
        )
        previous = node
        used.add(node)
    return nodes


def fields(trace):
    return [(r["state"], r["frame"], r["action"]) for r in trace]


def retained(record, original):
    require(
        [record[k] for k in ("call", "evaluation", "prefix", "original_ambiguous_joins")]
        == [original[k] for k in ("call", "evaluation", "prefix", "ambiguous_joins")],
        "retained_identity",
    )
    result = record["native"]
    require(result["status"] == 2 and result["stop_code"] == 3, "retained_status")
    nodes = tree(result)
    sequences = record["sequences"]
    require(
        set(sequences) == {str(r["token"]) for r in nodes.values() if r["kind"]},
        "sequence_inventory",
    )
    source = original["trace"]
    by_frame = {r["frame"]: i for i, r in enumerate(source)}
    for token, sequence in sequences.items():
        node = nodes[sequence["node"]]
        parent = nodes[sequence["parent"]]
        trace = sequence["trace"]
        require(
            node["parent"] == parent["node"] and node["token"] == int(token), "sequence_identity"
        )
        require(len(trace) == node["steps"] + 1 and 2 <= len(trace) <= 9, "sequence_steps")
        require(
            [*trace[0]["state"], trace[0]["frame"]] == parent["state"]
            and [*trace[-1]["state"], trace[-1]["frame"]] == node["state"],
            "sequence_join",
        )
        start = by_frame[trace[0]["frame"]]
        require(fields(trace) == fields(source[start : start + len(trace)]), "sequence_source")
    recovered, tokens = [source[0]], []
    for row in result["rows"][1:]:
        token = int(row[6])
        segment = sequences[str(token)]["trace"]
        require(fields([recovered[-1]]) == fields([segment[0]]), "expanded_join")
        recovered.extend(segment[1:])
        tokens.append(token)
    require(fields(recovered) == fields(source) and record["tokens"] == tokens, "expanded_source")
    require(
        record["transported_states"] == len(source)
        and record["new_motion_searches"] == record["new_mask_queries"] == 0,
        "retained_accounting",
    )
    return len(source)


def selection(records):
    require(len(records) == 10 and len({r["name"] for r in records}) == 10, "selection_population")
    selected = 0
    for record in records:
        args, actual = record["inputs"], record["result"]
        candidates = []
        primary, route = args["primary"], args["route"]

        def nearest(row):
            x, y = row["state"][:2]
            return min(((x - p[1]) ** 2 + (y - p[0]) ** 2, i) for i, p in enumerate(route))[1]

        if primary and (nearest(primary["trace"][-1]) + 1) < 0.9 * len(route):
            maximum = max(args["current_max"], nearest(primary["trace"][-1]))
            present = [tuple(s) for s in args["endpoints"]]
            present += [(*r["state"], r["frame"]) for r in primary["trace"]]
            for trial in args["evaluations"]:
                if trial["interrupted"] is not None or not trial["eligibility"]["complete"]:
                    continue
                for k in range(
                    1, min(trial["valid_prefix"], trial["eligibility"]["eligible_prefix"]) + 1
                ):
                    point = trial["trace"][k]
                    if (
                        nearest(point) > maximum
                        and (*point["state"], point["frame"]) not in present
                    ):
                        candidates.append((-nearest(point), point["frame"], trial["id"], k, trial))
            candidates.sort(key=lambda c: c[:4])
        if not candidates:
            require(actual is None, "selection_false_extra")
        else:
            index, _, evaluation, k, trial = candidates[0]
            require(
                actual
                == dict(
                    evaluation=evaluation,
                    prefix=k,
                    nearest_index=-index,
                    maximum_after_primary=maximum,
                    trace=trial["trace"][: k + 1],
                ),
                "selection_rank",
            )
            selected += 1
    require(selected == 1, "selection_expected_population")


def check_raw(folder, paths):
    callback_count = 0
    for profile, status in (("empty", 0), ("approximate", 1), ("exact", 2)):
        parent, candidate = [
            document(folder, profile + "_" + version + ".json")
            for version in ("parent", "candidate")
        ]
        require(parent == candidate and parent["status"] == status, "zero_extra_compatibility")
        require(0 < parent["directed_calls"] <= 12, "compatibility_calls")
        callback_count += len(parent["callbacks"])
    extra = document(folder, "extra.json")
    tree(extra)
    require(
        extra["status"] == 2
        and extra["stop_code"] == 3
        and [r[7:10] for r in extra["rows"]] == [[1, 0, 0], [3, 1, 1], [4, 3, 1]]
        and [r[6] for r in extra["rows"]] == [0, 2, 3],
        "extra_exact_ancestry",
    )
    reasons = dict(
        parent="branch_parent",
        before="branch_parent",
        token="branch_token",
        reused_token="branch_token",
        duration="branch_duration",
        flags="branch_eligibility",
        finite="branch_finite",
        duplicate="branch_duplicate",
        count="branch_count",
    )
    for mutation, reason in reasons.items():
        row = document(folder, "reject_" + mutation + ".json")
        require(
            row["status"] == "rejected" and row["reason"].split(":")[-1] == reason,
            "corruption_not_rejected:" + mutation,
        )
    expiries = dict(
        initial=0, before_callback=0, after_callback=1, after_primary=1, after_extra=1, after_goal=1
    )
    for expiry, calls in expiries.items():
        row = document(folder, "expiry_" + expiry + ".json")
        tree(row)
        require(
            row["status"] == 0
            and row["stop_code"] == 2
            and not row["rows"]
            and row["directed_calls"] == calls,
            "deadline_precedence:" + expiry,
        )
    selection(document(folder, "selection.json"))
    require(len(paths) == 15, "retained_population")
    count = sum(
        retained(document(folder, f"retained_{i:02}.json"), path) for i, path in enumerate(paths)
    )
    return dict(
        compatibility_pairs=3,
        matching_callbacks=callback_count,
        native_rejections=9,
        deadline_controls=6,
        selection_controls=10,
        retained_paths=15,
        transported_states=count,
    )


def known_bads(folder, paths):
    original = document(folder, "retained_00.json")
    rejected = []
    for name in ("parent", "token", "duration", "control"):
        bad = copy.deepcopy(original)
        if name == "parent":
            bad["native"]["rows"][-1][8] = 999
        elif name == "token":
            bad["native"]["rows"][-1][6] = 999
        elif name == "duration":
            bad["native"]["rows"][-1][10] += 0.25
        else:
            next(iter(bad["sequences"].values()))["trace"][1]["action"][0] += 0.1
        try:
            retained(bad, paths[0])
        except ValueError as error:
            rejected.append(dict(mutation=name, reason=str(error)))
        else:
            raise ValueError("checker_accepted_corruption:" + name)
    return rejected


def check(root, commit):
    started = time.monotonic()
    plan = document(root, BASE / "PLAN.json")
    folder = root / BASE / "proof/qualification_raw"
    execution = committed(root, folder, commit, plan)
    for name, expected in plan["input_files"].items():
        require(sha(read(root, name)) == expected, "input_identity:" + name)
    require(
        execution["child_processes"] == 37
        and execution["all_children_reaped"] is True
        and execution["new_motion_searches"] == execution["new_mask_queries"] == 0,
        "execution_population",
    )
    children = document(folder, "children.json")
    require(
        len(children) == 37
        and len({c["name"] for c in children}) == 37
        and all(c["returncode"] == 0 and c["reaped"] is True for c in children),
        "child_closure",
    )
    for child in children:
        resources = document(folder, child["name"] + ".resources.json")
        require(
            0 < resources["elapsed_seconds"] <= plan["child_seconds"]
            and 0 < resources["peak_rss_bytes"] <= plan["max_rss_bytes"],
            "child_resources",
        )
    context = preflight(root, PARENT_SOURCE)
    paths = document(context["raw"], "paths.json")
    result = check_raw(folder, paths)
    rejected = known_bads(folder, paths)
    replay = scalar_replay(context, started + plan["checker_seconds"])
    require(
        replay["path_records"] == 15
        and replay["verified_states"] == result["transported_states"] == 350
        and replay["distinct_scalar_states"] == 82,
        "scalar_population",
    )
    require(
        time.monotonic() - started <= plan["checker_seconds"] and rss() <= plan["max_rss_bytes"],
        "checker_resources",
    )
    result.update(
        iteration=186,
        phase="closed",
        status="supported",
        source_commit=execution["source_commit"],
        raw_commit=commit,
        checker_known_bads=rejected,
        scalar_replay=replay,
        bridge_sha256=execution["bridge_sha256"],
        integrated_completed=3,
        integrated_cases=4,
        qualified_for_source_comparison=False,
        new_integrated_runs=0,
        new_motion_searches=0,
        new_mask_queries=0,
        actual_history_intervention=None,
        response_delay=None,
        superiority=None,
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
    )
    write(root / BASE / "proof/admission.json", result)
    print(
        {
            k: result[k]
            for k in ("status", "retained_paths", "transported_states", "matching_callbacks")
        },
        flush=True,
    )
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--raw-commit", required=True)
    a = p.parse_args()
    check(a.root.resolve(), a.raw_commit)
