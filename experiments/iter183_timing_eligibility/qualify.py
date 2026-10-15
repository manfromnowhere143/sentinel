"""Fixed exposed controls and constructed cost profile; no planner search."""

import argparse
import json
import math
from pathlib import Path
import statistics
import time

from .common import BASE, git, read, require, sha, write
from .contract import PARENT, check_contract
from .eligibility import Eligibility
from .eligibility_check import EligibilityReplay

CASES = "experiments/iter161_grouping_width_ablation/CASES.json"
OLD = "experiments/iter153_action_feasibility/PLAN.json"
PATHS = [(178, c) for c in ("bend_left", "chicane_left", "chicane_right")] + [
    (181, c) for c in ("chicane_left", "chicane_right")
]
PREFIX = {
    178: "experiments/iter178_root_domain_consistency/",
    181: "experiments/iter181_checkpoint_prefix_selection/",
}
AUDIT = "experiments/iter182_late_frontier_timing/"


def input_names():
    names = [CASES, OLD, AUDIT + "proof/admission.json"]
    names += [PREFIX[i] + "proof/admission.json" for i in (178, 181)]
    names += [PREFIX[i] + f"proof/search_raw/{case}/selected/trace.json" for i, case in PATHS]
    names += [
        AUDIT + f"proof/audit_raw/bend_left/probe_{call:03}/trace.json"
        for call in (104, 110, 128, 134)
    ]
    names += [AUDIT + f"proof/audit_raw/{case}/paths.json" for case in ("bend_left", "bend_right")]
    return names


def inputs(root):
    manifest = json.loads(read(root, BASE / "CONTROL_INPUTS.json"))
    require(
        manifest["parent_commit"] == PARENT and set(manifest["files"]) == set(input_names()),
        "control_inventory",
    )
    for name, digest in manifest["files"].items():
        value = read(root, name)
        require(
            sha(value) == digest and value == git(root, "show", PARENT + ":" + name),
            "control_input_identity",
        )
    return {name: json.loads(read(root, name)) for name in input_names()}


def single(producer, checker, state, frame, deadline):
    rows = [dict(frame=frame - 1), dict(frame=frame, state=state)]
    claim = producer.scan(rows, 1, None, deadline)
    row = dict(
        trace=rows,
        valid_prefix=1,
        eligibility=claim,
        interrupted=None if claim["complete"] else "time_budget",
    )
    checker.check(row)
    require(claim["complete"], "qualification_deadline")
    return claim


def profile_geometry(turn):
    angle = turn * math.pi / 2
    route = [[float(i * math.sin(angle)), float(i * math.cos(angle))] for i in range(100)]
    return dict(
        reset=[0.0, 0.0, angle, 4.0, 0.0],
        route=route,
        comparators=dict(first=dict(hazard_time=4.0, rc=0.3), final=dict(hazard_time=8.0, rc=0.8)),
        ego_dimensions=[1.6, 3.0, 1.5],
        obstacles=[],
    )


def run(root):
    raw = root / BASE / "proof/qualification_raw"
    raw.parent.mkdir(exist_ok=True)
    raw.mkdir(exist_ok=False)
    started = time.monotonic()
    write(
        raw / "initialized.json",
        dict(scope="Fixed retained controls and constructed cost profile; zero integrated runs"),
    )
    try:
        check_contract(root, json.loads(read(root, BASE / "PLAN.json")))
        source = inputs(root)
        old = source[OLD]
        cases = {c["id"]: c for c in source[CASES]}
        origin = time.monotonic()
        producers = {n: Eligibility(c["geometry"], old, origin) for n, c in cases.items()}
        checkers = {n: EligibilityReplay(c["geometry"], old, 60) for n, c in cases.items()}
        observations = []
        paths = [(PREFIX[i] + f"proof/search_raw/{c}/selected/trace.json", c) for i, c in PATHS]
        paths += [
            (AUDIT + f"proof/audit_raw/bend_left/probe_{call:03}/trace.json", "bend_left")
            for call in (104, 110, 128, 134)
        ]
        for name, case in paths:
            for row in source[name]:
                if 24 <= row["frame"] < 32:
                    claim = single(
                        producers[case], checkers[case], row["state"], row["frame"], origin + 60
                    )
                    require(claim["eligible_prefix"] == 1, "retained_witness_false_exclusion")
                    observations.append(
                        dict(
                            path=name,
                            case=case,
                            frame=row["frame"],
                            state=row["state"],
                            eligibility=claim,
                        )
                    )
        require(len(observations) == 72, "retained_witness_population")
        exclusions = {
            (r["case"], r["call"]): r for r in source[AUDIT + "proof/admission.json"]["records"]
        }
        roots = []
        for case in ("bend_left", "bend_right"):
            for path in source[AUDIT + f"proof/audit_raw/{case}/paths.json"]:
                last = path["trace"][-1]
                claim = single(
                    producers[case], checkers[case], last["state"], last["frame"], origin + 60
                )
                expected = exclusions[case, path["call"]]
                require(
                    (claim["eligible_prefix"] == 0)
                    == (expected["progress_excluded"] or expected["premature_completion_excluded"]),
                    "retained_root_classification",
                )
                roots.append(
                    dict(
                        case=case,
                        call=path["call"],
                        state=last["state"],
                        frame=last["frame"],
                        eligibility=claim,
                    )
                )
        require(
            len(roots) == 7 and sum(r["eligibility"]["eligible_prefix"] == 0 for r in roots) == 3,
            "retained_root_population",
        )
        write(raw / "retained_controls.json", dict(paths=observations, roots=roots))

        origin = time.monotonic()
        synthetic = [profile_geometry(i) for i in range(4)]
        producer = [Eligibility(g, old, origin) for g in synthetic]
        checker = [EligibilityReplay(g, old, 60) for g in synthetic]
        records, samples = [], {"cold": [], "warm": []}
        for pass_name in ("cold", "warm"):
            for turn, geometry in enumerate(synthetic):
                for frame in range(24, 32):
                    for velocity in (0.0, 2.0, 4.0, 6.0):
                        for station in (60, 85):
                            p = geometry["route"][station]
                            state = [p[1], p[0], turn * math.pi / 2, velocity, 0.0]
                            rows = [dict(frame=frame - 1), dict(frame=frame, state=state)]
                            tick = time.perf_counter()
                            claim = producer[turn].scan(rows, 1, None, origin + 60)
                            elapsed = time.perf_counter() - tick
                            checker[turn].check(
                                dict(
                                    trace=rows,
                                    valid_prefix=1,
                                    eligibility=claim,
                                    interrupted=None if claim["complete"] else "time_budget",
                                )
                            )
                            require(
                                claim["complete"]
                                and claim["records"][0]["hit"] == (pass_name == "warm"),
                                "profile_cache",
                            )
                            samples[pass_name].append(elapsed)
                            records.append(
                                dict(
                                    pass_name=pass_name,
                                    turn=turn,
                                    frame=frame,
                                    state=state,
                                    seconds=elapsed,
                                    eligibility=claim,
                                )
                            )
        require(all(len(v) == 256 for v in samples.values()), "profile_population")
        write(raw / "profile.json", dict(geometries=synthetic, records=records))
        summary = {
            name: dict(
                count=len(values),
                total_seconds=sum(values),
                median_seconds=statistics.median(values),
                p95_seconds=sorted(values)[math.ceil(0.95 * len(values)) - 1],
                maximum_seconds=max(values),
            )
            for name, values in samples.items()
        }
        result = dict(
            status="supported",
            retained_path_records=72,
            retained_roots=7,
            verified_exclusions=3,
            false_exclusions=0,
            constructed_inputs=256,
            profile=summary,
            elapsed_seconds=time.monotonic() - started,
            new_integrated_schedules=0,
            new_motion_searches=0,
            new_driving_episodes=0,
            scope="Exposed bound controls and finite constructed computation costs; not integrated performance or real-time evidence.",
        )
        write(raw / "result.json", result)
        print(json.dumps(result), flush=True)
    except Exception as error:
        write(raw / "failure.json", dict(status="invalid", error=f"{type(error).__name__}:{error}"))
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    run(parser.parse_args().root.resolve())
