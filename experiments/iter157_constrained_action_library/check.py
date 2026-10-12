"""Independent admission: old scalar controls plus scalar background witnesses.

Does not import the producer or Iter156 vector query. Shared support is I/O only.
"""

import argparse
from pathlib import Path
import time

import numpy as np

from experiments.iter153_action_feasibility.check import verify_search
from experiments.iter155_background_witness.check import selection
from experiments.iter155_background_witness.geometry import count_points, ground_height, vertices
from experiments.iter155_background_witness.storage import get_arrays, read_json, write_json
from .support import query_budget
from .support import OLD, bounded, committed_raw, documents, inputs, require, rss, sha


def classify(query):
    certain, possible, count = query["certain_inside"], query["possible_inside"], query["count"]
    require(
        all(type(x) is int and 0 <= x <= 276519 for x in [certain, possible, count]), "count_domain"
    )
    require(certain <= count <= possible, "count_bounds")
    return "collision" if certain > 100 else "clear" if possible <= 100 else "numerically_ambiguous"


def verify_row(row, prior, states):
    require(
        row["candidate"] == prior["candidate"]
        and row["completion_time"] == prior["completion_time"]
        and row["prior_eligible"] is prior["eligible"],
        "candidate_identity",
    )
    require(
        all(
            row[k] is None
            for k in [
                "road_compliance",
                "physical_occupancy",
                "useful_recovery",
                "information_benefit",
            ]
        ),
        "unknown_claim",
    )
    queries = row["queries"]
    require(isinstance(queries, list) and len(queries) <= len(states), "query_cardinality")
    if not prior["eligible"]:
        require(
            queries == []
            and row["verdict"] == "prior_constraints_failed"
            and row["background_complete"] is False,
            "prior_failure_erased",
        )
        return []
    require(len(queries) > 0, "missing_candidate")
    for frame, q in enumerate(queries):
        require(
            type(q["frame"]) is int
            and q["frame"] == frame
            and q["time"] == frame / 4
            and q["state"] == states[frame],
            "query_state",
        )
        require(q["mask"]["path"] == f"{prior['candidate']['id']}_{frame:03d}.bin", "mask_path")
        require(q["decision"] == classify(q), "favorable_decision")
        require(q["decision"] == "clear" or frame == len(queries) - 1, "continued_query")
    last = queries[-1]["decision"]
    expected = (
        "qualified"
        if last == "clear"
        else "background_collision"
        if last == "collision"
        else "numerically_ambiguous"
    )
    require(row["verdict"] == expected, "candidate_verdict")
    require(row["background_complete"] is (len(queries) == len(states)), "background_coverage")
    require(last != "clear" or len(queries) == len(states), "partial_qualified")
    # Exclusion needs one checked counterexample. Admission needs every sample.
    return (
        list(range(len(queries)))
        if expected == "qualified" or prior["candidate"]["id"] == "maneuver_059"
        else [len(queries) - 1]
    )


def selections(rows):
    qualified = [r for r in rows if r["verdict"] == "qualified"]
    if not qualified:
        return None, None
    primary = sorted(
        qualified,
        key=lambda r: (r["completion_time"], abs(r["candidate"]["offset"]), r["candidate"]["id"]),
    )[0]
    secondary = sorted(
        qualified,
        key=lambda r: (abs(r["candidate"]["offset"]), r["completion_time"], r["candidate"]["id"]),
    )[0]
    return primary["candidate"]["id"], secondary["candidate"]["id"]


def verify_mask(raw, q):
    packed = bounded(raw, q["mask"]["path"], 40000)
    require(
        len(packed) == (276519 + 7) // 8 and sha(packed) == q["mask"]["sha256"], "mask_identity"
    )
    bits = np.unpackbits(np.frombuffer(packed, dtype="u1"), bitorder="little")
    require(not bits[276519:].any() and int(bits[:276519].sum()) == q["count"], "mask_count")
    return packed


def resource_gate(data, plan):
    require(
        type(data["peak_rss_bytes"]) is int and 0 < data["peak_rss_bytes"] <= plan["max_rss_bytes"],
        "producer_memory",
    )
    require(
        type(data["elapsed_seconds"]) in (float, int)
        and 0 < data["elapsed_seconds"] <= plan["producer_seconds"],
        "producer_time",
    )


def admit(root, raw, raw_commit):
    started = time.monotonic()
    plan, _, _ = documents(root)
    inputs(root, plan)
    data = read_json(raw / "predictions.json")
    names = committed_raw(root, raw, raw_commit, plan, data)
    require(
        data["schema"] == "sentinel.iter157.predictions.v1"
        and data["status"] == "completed"
        and data["candidates"] == 75
        and data["new_driving_episodes"] == 0,
        "producer_scope",
    )
    resource_gate(data, plan)
    require(
        read_json(raw / "initialized.json")
        == dict(source_commit=data["source_commit"], plan_sha256=data["plan_sha256"]),
        "initialization_identity",
    )
    prior = verify_search(root, root / OLD / "proof/search_000", plan["prior_raw_commit"])
    require(
        prior["eligible_model_candidates"] == 14 and prior["verified_model_actions"] == 10012,
        "prior_replay",
    )
    raw155 = root / "experiments/iter155_background_witness/proof/raw"
    arrays, _ = get_arrays(raw155, read_json(raw155 / "witness.json")["arrays"])
    chosen = selection(
        arrays["population_xyz"], arrays["population_features"], arrays["population_opacity"]
    )
    points = arrays["selected_xyz"]
    require(
        np.array_equal(chosen.astype("u1"), arrays["selection"])
        and np.array_equal(points, arrays["population_xyz"][chosen]),
        "complete_population",
    )
    require(
        len(points) == 276519 and sha(points.tobytes()) == data["population_sha256"],
        "population_identity",
    )
    point_list = points.tolist()
    rows, checked = [], []
    expected_files = {"initialized.json", "predictions.json"}
    for old in prior["results"]:
        name = old["candidate"]["id"]
        expected_files.add(name + ".json")
        row = read_json(raw / (name + ".json"))
        states = read_json(root / OLD / f"proof/search_000/{name}_1.json")["states"]
        indices = verify_row(row, old, states)
        for q in row["queries"]:
            expected_files.add(q["mask"]["path"])
            verify_mask(raw, q)
        for i in indices:
            if time.monotonic() - started > plan["checker_seconds"]:
                raise TimeoutError("checker_deadline")
            q = row["queries"][i]
            state = states[i]
            height, nearest = ground_height(arrays["ground_poses"].tolist(), state[1], state[0])
            box = vertices((state[1], height, state[0]), state[2])
            require(
                nearest == q["ground_nearest_index"]
                and abs(height - q["height"]) < 1e-9
                and np.array_equal(np.asarray(box, dtype="<f4"), np.asarray(q["box"], dtype="<f4")),
                "source_geometry",
            )
            scalar = count_points(point_list, box)
            require(
                scalar["count"] == q["count"]
                and scalar["certain_inside"] == q["certain_inside"]
                and scalar["possible_inside"] == q["possible_inside"]
                and len(scalar["ambiguous"]) == q["ambiguous_points"],
                "scalar_counts",
            )
            packed = np.packbits(
                np.asarray(scalar["mask"], dtype="u1"), bitorder="little"
            ).tobytes()
            require(packed == bounded(raw, q["mask"]["path"], 40000), "scalar_full_mask")
            checked.append(
                dict(
                    candidate=name, frame=i, time=i / 4, count=scalar["count"], decision=classify(q)
                )
            )
            print(name, i, scalar["count"], flush=True)
            require(rss() <= plan["max_rss_bytes"], "memory_budget")
        rows.append({k: v for k, v in row.items() if k != "queries"})
    require({Path(n).name for n in names} == expected_files, "raw_file_set")
    require(
        data["queried_states"]
        == sum(len(read_json(raw / (r["candidate"]["id"] + ".json"))["queries"]) for r in rows),
        "query_population",
    )
    query_budget(data["queried_states"], plan["maximum_queries"])
    primary, alternate = selections(rows)
    require(data["selected"] == primary and data["alternate_selected"] == alternate, "ranking")
    negative = [r for r in checked if r["candidate"] == "maneuver_059"]
    require(
        len(negative) == 14
        and all(r["decision"] == "clear" for r in negative[:-1])
        and negative[-1]["count"] == 273
        and negative[-1]["time"] == 3.25,
        "negative_control",
    )
    counts = {
        verdict: sum(r["verdict"] == verdict for r in rows)
        for verdict in [
            "qualified",
            "background_collision",
            "numerically_ambiguous",
            "prior_constraints_failed",
        ]
    }
    counts["rejected"] = counts["background_collision"] + counts["prior_constraints_failed"]
    counts["uncertain"] = counts["numerically_ambiguous"]
    status = (
        "supported"
        if counts["qualified"]
        else "inconclusive"
        if counts["numerically_ambiguous"]
        else "null"
    )
    require(time.monotonic() - started <= plan["checker_seconds"], "checker_deadline")
    return dict(
        schema="sentinel.iter157.admission.v1",
        status=status,
        source_commit=data["source_commit"],
        raw_commit=raw_commit,
        candidates=75,
        previously_eligible=14,
        qualified=counts["qualified"],
        new_driving_episodes=0,
        counts=counts,
        selected=primary,
        alternate_selected=alternate,
        candidates_checked=rows,
        queried_states=data["queried_states"],
        scalar_masks_checked=len(checked),
        scalar_checks=checked,
        elapsed_seconds=time.monotonic() - started,
        peak_rss_bytes=rss(),
        physical_occupancy=None,
        road_compliance=None,
        useful_recovery=None,
        information_benefit=None,
        scope="One exposed-scene finite source-model library. Independent scalar exclusion witnesses and all samples of qualified actions; not native recovery.",
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--raw-commit", required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = admit(args.root.resolve(), args.raw.resolve(), args.raw_commit)
    write_json(args.output, result)
    print({k: v for k, v in result.items() if k not in ["candidates_checked", "scalar_checks"]})
