"""Separate prefix ancestry, scalar path and absolute native token admission."""

from experiments.iter182_late_frontier_timing.replay import row_check
from experiments.iter182_late_frontier_timing.retained import state_key
from experiments.iter172_integrated_rrt.check import outcome
from experiments.iter182_late_frontier_timing.bound_check import check_bound
from experiments.iter182_late_frontier_timing.premature_check import check_completion
from .common import encode, require


def population_check(records, connections, trials, geometry):
    highest = max(
        outcome(c["trace"][-1]["state"], geometry)["nearest"]
        for c in connections
        if c["result"] is not None and len(c["trace"]) > 1
    )
    expected = []
    for trial in trials:
        for k, row in enumerate(trial["trace"]):
            if 0 < k <= trial["eligibility"]["eligible_prefix"]:
                if outcome(row["state"], geometry)["nearest"] > highest:
                    expected.append((trial["call"], trial["id"], k))
    require(
        [(p["call"], p["evaluation"], p["prefix"]) for p in records] == expected,
        "audited_population",
    )
    return highest


def binding(record, connections, trials, reset):
    table = {c["call"]: c for c in connections}
    trial = next(
        t for t in trials if (t["call"], t["id"]) == (record["call"], record["evaluation"])
    )
    require(0 < record["prefix"] <= trial["eligibility"]["eligible_prefix"], "eligible_prefix")
    cursor, cutoff = table[record["call"]]["before"], record["call"]
    chain = list(reversed(record["chain"]))
    require(len(chain) == len(record["joins"]), "join_count")
    for number, join in zip(chain, record["joins"]):
        candidates = sorted(
            c["call"]
            for c in connections
            if c["call"] < cutoff
            and c["result"] is not None
            and len(c["trace"]) > 1
            and [*c["trace"][-1]["state"], c["trace"][-1]["frame"]] == cursor
        )
        require(candidates and number == candidates[0], "join_selection")
        require(
            join == dict(cutoff=cutoff, state_clock=cursor, choices=candidates, chosen=number),
            "join_inventory",
        )
        require(table[number]["before"][5] < cursor[5], "join_clock")
        cursor, cutoff = table[number]["before"], number
    require(cursor == [*reset, 0], "join_reset")
    require(
        record["ambiguous_joins"] == sum(len(j["choices"]) > 1 for j in record["joins"]),
        "join_ambiguity",
    )
    segments = [table[n]["trace"] for n in record["chain"]]
    segments.append(trial["trace"][: record["prefix"] + 1])
    trace = [segments[0][0]]
    for segment in segments:
        require(
            trace[-1]["state"] == segment[0]["state"] and trace[-1]["frame"] == segment[0]["frame"],
            "join_segment",
        )
        trace.extend(segment[1:])
    require(encode(trace) == encode(record["trace"]), "path_source_binding")


def path_check(trace, keys, case, old, masks):
    require(0 < len(trace) <= 97 and len(keys) == len(trace), "path_length")
    require(
        trace[0]["state"] == case["geometry"]["reset"] and trace[0]["action"] is None, "path_reset"
    )
    checks = 0
    for i, row in enumerate(trace):
        require(
            type(row["frame"]) is int
            and row["frame"] == row["id"] == i
            and row["parent"] == (None if i == 0 else i - 1),
            "path_clock",
        )
        if i:
            require(trace[i - 1]["route"]["rc"] < 1, "path_after_completion")
        require(
            row_check(row, trace[i - 1] if i else row, case, old, masks) == "clear", "path_rejected"
        )
        key = state_key(row["state"])
        require(
            keys[i] == key and key in masks and masks[key]["background"] == row["background"],
            "path_scalar_mask",
        )
        checks += sum(c["hazard_time"] == i / 4 for c in case["geometry"]["comparators"].values())
    return checks


def certificates_check(record, last, case, old):
    frame = last["frame"]
    if not 24 <= frame < 32:
        require(
            record == dict(status="outside_window", progress=None, completion=None),
            "unknown_certificate",
        )
        return False, False
    require(record["status"] == "checked", "certificate_status")
    return (
        check_bound(record["progress"], last["state"], frame, case["geometry"], old, 32),
        check_completion(record["completion"], last["state"], frame, case["geometry"], old, 32),
    )


def native_binding(native, connections, suffix, root, frame, old):
    require(
        suffix and suffix[0]["state"] == root and suffix[0]["frame"] == frame, "native_suffix_root"
    )
    rows, selected = native["rows"], native["selected_connections"]
    if not rows:
        require(len(suffix) == 1 and not selected, "empty_native_path")
        return
    require(rows[0] == [*root, frame, 0, 0, 0], "native_absolute_root")
    tokens, trace = [], [suffix[0]]
    for row in rows[1:]:
        require(
            float(row[6]).is_integer() and row[7] == 0 and int(row[6]) in connections,
            "native_sequence_token",
        )
        number = int(row[6])
        c = connections[number]
        segment = c["trace"]
        require(c["before"] == [*trace[-1]["state"], trace[-1]["frame"]], "native_sequence_parent")
        require(
            row[:6] == [*segment[-1]["state"], segment[-1]["frame"]]
            and row[8] == (len(segment) - 1) * old["dt"],
            "native_sequence_endpoint",
        )
        trace.extend(segment[1:])
        tokens.append(number)
    require(tokens == selected and trace == suffix, "native_selected_path")


def classify(complete, progress, premature, censored):
    require(
        all(type(v) is bool for v in (complete, progress, premature, censored)),
        "classification_type",
    )
    require(not (complete and (progress or premature or censored)), "contradictory_witness")
    if complete:
        return "verified_full_route_continuation"
    if progress or premature:
        return "demonstrated_timing_constraint"
    return "unobserved_continuation" if censored else "unresolved_bounded_miss"
