"""Independent program proposals, complete rollout accounting and selected path."""

from collections import Counter
import copy
import math
import struct
from experiments.iter153_action_feasibility.check import near
from experiments.iter172_integrated_rrt.check import evaluation, distance
from experiments.iter177_pose_aware_seed.seed_check import expected_seed
from experiments.iter173_matched_connector_cost.check import expected_proposal
from experiments.iter179_frontier_continuation_audit.replay import row_check, path_check
from experiments.iter179_frontier_continuation_audit.retained import state_key
from .common import require, encode
from .target_check import check_target


def program_check(record, events, combined, retained, case, old, plan, masks):
    result = record["result"]
    root = retained[-1]
    frame, state = root["frame"], root["state"]
    task = check_target(record["target"], state, frame, case["geometry"], plan["target_frame"])
    n = task["terminal_frame"]
    connection = dict(
        before=[*state, frame], target=[*record["target"]["state"], plan["target_frame"]], task=task
    )
    evs, requests, cache, pending = [], [], {}, None
    attempts = hits = 0
    for event_index, row in enumerate(events):
        if row["kind"] == "request":
            require(pending is None and len(requests) < plan["max_proposals"], "request_order")
            index = len(requests)
            expected = (
                expected_seed(state, task) if index == 0 else expected_proposal(state, task, index)
            )
            require(
                row["id"] == index + 1
                and row["caller"] == ("initial" if index == 0 else "forward_proposal"),
                "request_identity",
            )
            near(row["values"], expected, 2e-14 if index == 0 else 2e-15)
            requests.append(row)
            key = struct.pack(">" + str(len(row["values"])) + "d", *row["values"])
            if row["stopped"] is not None:
                require(
                    event_index == len(events) - 1
                    and row["evaluation"] is None
                    and row["cached"] is False,
                    "stopped_request",
                )
                require(
                    row["stopped"] == result["stop"] == result["generator_stop"], "stop_binding"
                )
                if row["stopped"] == "attempt_budget":
                    require(
                        key not in cache and attempts + n > plan["per_root_attempts"],
                        "reservation_stop",
                    )
                else:
                    require(row["stopped"] == "time_budget", "request_stop")
            elif row["cached"]:
                require(cache.get(key) == row["evaluation"], "cache_identity")
                hits += 1
            else:
                require(
                    row["cached"] is False
                    and key not in cache
                    and row["evaluation"] == len(evs) + 1,
                    "new_evaluation_identity",
                )
                require(attempts + n <= plan["per_root_attempts"], "unreserved_rollout")
                pending = (key, row)
        else:
            require(row["kind"] == "evaluation" and pending is not None, "evaluation_order")
            key, request = pending
            require(
                row["id"] == request["evaluation"] and row["values"] == request["values"],
                "evaluation_pair",
            )
            attempts += evaluation(row, connection, case, old)
            for i, item in enumerate(row["trace"]):
                row_check(item, row["trace"][i - 1] if i else item, case, old, masks)
                require(
                    item["background"] is None or state_key(item["state"]) in masks,
                    "all_query_masks",
                )
            if row["full"]:
                cache[key] = row["id"]
            pending = None
            evs.append(row)
    require(pending is None and requests, "incomplete_events")
    require(
        result["start_frame"] == frame and result["target_frame"] == plan["target_frame"],
        "result_clock",
    )
    require(
        result["evaluations"] == len(evs)
        and result["requests"] == len(requests)
        and result["cache_hits"] == hits
        and result["attempts"] == attempts <= plan["per_root_attempts"],
        "program_accounting",
    )
    require(
        result["queries"]
        == 1 + sum(r["background"] is not None for e in evs for r in e["trace"][1:]),
        "program_queries",
    )
    require(
        result["counts"] == dict(Counter(r["reason"] for e in evs for r in e["trace"][1:])),
        "program_counts",
    )
    winners = [e for e in evs if e["full"] and e["valid_prefix"] == n and e["interrupted"] is None]
    require(
        type(result["witness"]) is bool and result["witness"] == bool(winners), "program_witness"
    )
    if winners:
        require(
            len(winners) == 1
            and winners[0] is evs[-1]
            and events[-1] is evs[-1]
            and result["stop"] == "checkpoint_witness",
            "first_checkpoint_witness",
        )
        chosen, prefix = winners[0], n
        expected_stop = (
            "model_complete"
            if chosen["world_complete"]
            else ("qualified_candidate" if chosen["target_complete"] else None)
        )
        require(result["generator_stop"] == expected_stop, "generator_witness_stop")
    else:
        require(
            result["stop"] == result["generator_stop"]
            and result["stop"] in ("attempt_budget", "time_budget"),
            "program_stop",
        )
        if result["stop"] == "attempt_budget":
            require(
                requests[-1]["stopped"] == "attempt_budget"
                and plan["per_root_attempts"] - attempts < n,
                "program_budget",
            )
        else:
            require(
                requests[-1]["stopped"] == "time_budget"
                or (evs and evs[-1]["interrupted"] == "time_budget"),
                "program_censor",
            )
        candidates = [e for e in evs if e["selected_prefix"]]

        def rank(e):
            r = e["trace"][e["selected_prefix"]]
            return (
                not e["world_complete"],
                distance([*r["state"], r["frame"]], connection["target"]),
                e["id"],
                e["selected_prefix"],
            )

        chosen = min(candidates, key=rank) if candidates else None
        prefix = chosen["selected_prefix"] if chosen else 0
    require(
        result["selected_evaluation"] == (chosen["id"] if chosen else None)
        and result["selected_prefix"] == prefix,
        "returned_selection",
    )
    suffix = chosen["trace"][: prefix + 1] if chosen else []
    expected = copy.deepcopy(retained + (suffix[1:] if suffix else []))
    for i, row in enumerate(expected):
        row.update(id=i, parent=i - 1 if i else None)
    require(encode(combined) == encode(expected), "program_path_binding")
    path_check(combined, record["masks"], case, old, masks)
    require(
        result["witness"] == (combined[-1]["frame"] == plan["target_frame"]), "program_terminal"
    )
    require(
        type(result["evaluator_elapsed_seconds"]) in (int, float)
        and math.isfinite(result["evaluator_elapsed_seconds"])
        and 0 <= result["evaluator_elapsed_seconds"] <= record["search_seconds"],
        "program_clock",
    )
    return result["witness"]
