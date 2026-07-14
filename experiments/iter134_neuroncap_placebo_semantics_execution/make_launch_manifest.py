#!/usr/bin/env python3
"""Generate the iteration 134 launch manifest.

Binds, before any episode runs, everything the iteration 133 design contract requires:
scenario_pair_ids, scenario_classes, run_indices, arm_ids, donor_schedule_ids,
donor_exclusion_receipts, actuator_budget_summaries, patch_file_sha256, analyzer_file_sha256,
and environment_receipts.

Fails closed if the placebo patch names any risk term (G1), if any donor schedule fails to
exclude its target pair or target seed (G3), or if the scheduled budget does not equal the
released union's realized budget.

Usage: make_launch_manifest.py <out manifest.json> <donor_schedules.json> <env_receipts.json>
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# G1: a placebo that can name a risk term is not a placebo.
FORBIDDEN = [
    "aux_outputs", "objects_in_bev", "object_scores", "future_trajs", "object_ids", "ego2world",
    "cpa", "ttc", "closing", "min_score", "SENTINEL_TTC", "SENTINEL_CPA_MARGIN",
    "SENTINEL_MIN_CLOSING", "SENTINEL_MAXGAP", "SENTINEL_MIN_SCORE", "SENTINEL_RELEASE_K",
]

HASH_BOUND = [
    "server_patch_placebo.py",
    "server_patch_union_release.py",
    "analyze_placebo134.py",
    "extract_donor_schedules.py",
    "run_placebo134.sh",
    "donor_schedules.json",
]

CLASS_SEQS = {
    "stationary": ["0099", "0101", "0103", "0106", "0108", "0278", "0331", "0783", "0796", "0966"],
    "frontal": ["0103", "0106", "0110", "0346", "0923"],
    "side": ["0103", "0108", "0110", "0278", "0921"],
}
CLASSES = ["stationary", "frontal", "side"]
ARMS = [
    {"arm_id": "off", "enabled": 0, "patch": "server_patch_union_release.py"},
    {"arm_id": "union", "enabled": 1, "patch": "server_patch_union_release.py"},
    {"arm_id": "placebo", "enabled": 1, "patch": "server_patch_placebo.py"},
]
RUNS = 20
FROZEN_UNION_PARAMS = {
    "SENTINEL_MIN_SCORE": "0.3", "SENTINEL_MAXGAP": "30", "SENTINEL_CPA_MARGIN": "1.5",
    "SENTINEL_TTC": "2.5", "SENTINEL_MIN_CLOSING": "3", "SENTINEL_RELEASE_K": "4",
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    out_path, sched_path, env_path = sys.argv[1:4]
    problems = []
    sched = json.load(open(sched_path))
    env = json.load(open(env_path))

    if sched.get("verdict") != "DONOR_SCHEDULES_OK":
        problems.append(f"donor-schedules-verdict:{sched.get('verdict')}")

    # G1 leak guard on the placebo, and proof the guard is discriminating
    placebo_src = open(os.path.join(HERE, "server_patch_placebo.py")).read()
    union_src = open(os.path.join(HERE, "server_patch_union_release.py")).read()
    leaks = [t for t in FORBIDDEN if t in placebo_src]
    union_terms = [t for t in FORBIDDEN if t in union_src]
    if leaks:
        problems.append(f"g1-semantic-leak:{leaks}")
    if not union_terms:
        problems.append("g1-guard-vacuous: the guard does not fire on the semantic union")

    # G3 donor exclusion receipts
    receipts = []
    bad_excl = 0
    for key, row in sorted(sched["schedules"].items()):
        excl_pair = row["donor_seq"] != row["target_seq"]
        excl_seed = row["donor_run"] != row["target_run"]
        same_class = row["donor_class"] == row["target_class"]
        if not (excl_pair and excl_seed and same_class):
            bad_excl += 1
        receipts.append({
            "schedule_id": key,
            "donor_id": f'{row["donor_class"]}/{row["donor_seq"]}/{row["donor_run"]}',
            "excludes_target_pair": excl_pair,
            "excludes_target_seed": excl_seed,
            "same_scenario_class": same_class,
            "scheduled_brake_count": row["scheduled_brake_count"],
        })
    if bad_excl:
        problems.append(f"g3-donor-exclusion:{bad_excl}")
    if len(receipts) != len(CLASSES and [s for c in CLASSES for s in CLASS_SEQS[c]]) * RUNS:
        problems.append(f"schedule-count:{len(receipts)}")

    # actuator budget summaries
    budget = {
        "actuator_family": "threat_cleared_latched_stop_release",
        "actuator_inherited_from": "released_union",
        "actuator_expression": "[[0.0, 0.0] for _ in range(len(base))]",
        "union_total_brake_frames": sched["union_total_brake_frames"],
        "placebo_scheduled_total_brake_frames": sched["scheduled_total_brake_frames"],
        "per_class_union_brake_frames": sched["per_class_union_brake_frames"],
        "per_class_scheduled_brake_frames": sched["per_class_scheduled_brake_frames"],
        "budget_matched_exactly": (
            sched["scheduled_total_brake_frames"] == sched["union_total_brake_frames"]
            and sched["per_class_scheduled_brake_frames"] == sched["per_class_union_brake_frames"]
        ),
    }
    if not budget["budget_matched_exactly"]:
        problems.append("actuator-budget-not-matched")

    hash_bound = {}
    for name in HASH_BOUND:
        p = os.path.join(HERE, name)
        if not os.path.exists(p):
            problems.append(f"hash-bound-missing:{name}")
            continue
        hash_bound[name] = {"sha256": sha256_file(p), "bytes": os.path.getsize(p)}

    manifest = {
        "schema": "iter134.launch_manifest.v1",
        "design_contract": "iter133.neuroncap_placebo_semantics_control_design.v1",
        "verdict": "LAUNCH_MANIFEST_OK" if not problems else "LAUNCH_MANIFEST_INVALID",
        "scenario_classes": CLASSES,
        "scenario_pair_ids": [f"{c}/{s}" for c in CLASSES for s in CLASS_SEQS[c]],
        "run_indices": list(range(RUNS)),
        "arm_ids": [a["arm_id"] for a in ARMS],
        "arms": ARMS,
        "frozen_union_params": FROZEN_UNION_PARAMS,
        "planned_episodes": len([f"{c}/{s}" for c in CLASSES for s in CLASS_SEQS[c]]) * RUNS * len(ARMS),
        "donor_rule": sched["donor_rule"],
        "donor_schedule_source_sha256": [x["sha256"] for x in sched["source_log_parts"]],
        "donor_schedule_ids": [r["schedule_id"] for r in receipts],
        "donor_exclusion_receipts": receipts,
        "actuator_budget_summaries": budget,
        "g1_forbidden_terms": FORBIDDEN,
        "g1_placebo_leaks": leaks,
        "g1_union_terms_present": union_terms,
        "hash_bound_files": hash_bound,
        "patch_file_sha256": hash_bound.get("server_patch_placebo.py", {}).get("sha256"),
        "analyzer_file_sha256": hash_bound.get("analyze_placebo134.py", {}).get("sha256"),
        "environment_receipts": env,
        "done_marker": "I134_PLACEBO_DONE",
        "problem_count": len(problems),
        "problems": problems,
    }
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=1, sort_keys=True)
    print(f"{manifest['verdict']} episodes={manifest['planned_episodes']} "
          f"schedules={len(receipts)} leaks={len(leaks)} union_terms={len(union_terms)} "
          f"budget_matched={budget['budget_matched_exactly']} problems={len(problems)}")
    for p in problems[:10]:
        print("  problem:", p)
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
