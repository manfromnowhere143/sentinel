"""Frozen, bounded acquisition of native interface qualification records."""

import argparse
import copy
from pathlib import Path
import subprocess
import sys
import time

from experiments.iter185_retained_prefix_admission.context import preflight as retained_preflight
from .common import BASE, document, require, write, read, sha
from .records import initialize, finish, failure
from .runtime import verify
from .selection import choose

PARENT_SOURCE = "df50a6b9123ca2389952da795b384225a4f9d980"
PATHS = Path("experiments/iter184_discarded_progress/proof/audit_retry_raw/paths.json")
MUTATIONS = (
    "parent",
    "before",
    "token",
    "reused_token",
    "duration",
    "flags",
    "finite",
    "duplicate",
    "count",
)
EXPIRIES = (
    "initial",
    "before_callback",
    "after_callback",
    "after_primary",
    "after_extra",
    "after_goal",
)


def selection_controls():
    def state(x, frame):
        return dict(state=[float(x), 0.0, 0.0, 1.0, 0.0], frame=frame, action=[0.0, 0.0])

    def trial(i, x, frame):
        return dict(
            id=i,
            trace=[state(0, 0), state(x, frame)],
            valid_prefix=1,
            interrupted=None,
            eligibility=dict(eligible_prefix=1, complete=True),
        )

    base = dict(
        evaluations=[trial(3, 8, 3), trial(2, 8, 2), trial(1, 8, 2)],
        primary=dict(trace=[state(0, 0), state(2, 1)]),
        current_max=1,
        endpoints=[],
        route=[[0.0, float(i)] for i in range(12)],
    )
    result = []
    for name in (
        "ties",
        "prior_extra_maximum",
        "primary_maximum",
        "duplicates",
        "invalid",
        "ineligible",
        "interrupted",
        "unfinished",
        "primary_complete",
        "no_primary",
    ):
        values = copy.deepcopy(base)
        if name == "prior_extra_maximum":
            values["current_max"] = 8
        elif name == "primary_maximum":
            values["primary"]["trace"][-1] = state(8, 1)
        elif name == "duplicates":
            values["endpoints"] = [[*state(8, f)["state"], f] for f in (2, 3)]
        elif name in ("invalid", "ineligible", "interrupted", "unfinished"):
            for r in values["evaluations"]:
                if name == "invalid":
                    r["valid_prefix"] = r["eligibility"]["eligible_prefix"] = 0
                elif name == "ineligible":
                    r["eligibility"]["eligible_prefix"] = 0
                elif name == "interrupted":
                    r["interrupted"] = "time_budget"
                else:
                    r["eligibility"]["complete"] = False
        elif name == "primary_complete":
            values["primary"]["trace"][-1] = state(10, 1)
        elif name == "no_primary":
            values["primary"] = None
        args = dict(values, endpoints={tuple(v) for v in values["endpoints"]})
        result.append(dict(name=name, inputs=values, result=choose(**args)))
    return result


def run(root, source, library, parent_library, prefix):
    started = time.monotonic()
    output = root / BASE / "proof/qualification_raw"
    output.parent.mkdir(exist_ok=True)
    plan = initialize(root, output, source, "qualification")
    try:
        for name, expected in plan["input_files"].items():
            require(sha(read(root, name)) == expected, "input_identity:" + name)
        runtime = verify(root, library, parent_library, prefix)
        context = retained_preflight(root, PARENT_SOURCE)
        require(len(document(context["raw"], "paths.json")) == 15, "retained_population")
        jobs = [
            (p + "_" + v, p, v == "parent", None)
            for p in ("empty", "approximate", "exact")
            for v in ("parent", "candidate")
        ]
        jobs += [("extra", "extra", False, None)]
        jobs += [("reject_" + m, "reject_" + m, False, None) for m in MUTATIONS]
        jobs += [("expiry_" + m, "expiry_" + m, False, None) for m in EXPIRIES]
        jobs += [(f"retained_{i:02}", "retained", False, i) for i in range(15)]
        executions = []
        for name, mode, parent, index in jobs:
            require(
                time.monotonic() - started < plan["qualification_producer_seconds"],
                "producer_deadline",
            )
            command = [
                sys.executable,
                "-m",
                "experiments.iter186_native_branch.worker",
                "--library",
                str(parent_library if parent else library),
                "--mode",
                mode,
                "--output",
                str(output / (name + ".json")),
            ]
            if parent:
                command.append("--parent")
            if index is not None:
                command += ["--index", str(index), "--paths", str(root / PATHS)]
            timeout = min(
                plan["child_seconds"],
                plan["qualification_producer_seconds"] - (time.monotonic() - started),
            )
            with (
                (output / (name + ".stdout")).open("xb") as stdout,
                (output / (name + ".stderr")).open("xb") as stderr,
            ):
                child = subprocess.run(
                    command, cwd=root, stdout=stdout, stderr=stderr, timeout=timeout
                )
            executions.append(dict(name=name, returncode=child.returncode, reaped=True))
            require(child.returncode == 0, "child_failure:" + name)
        write(output / "selection.json", selection_controls())
        require(verify(root, library, parent_library, prefix) == runtime, "runtime_changed")
        write(output / "children.json", executions)
        finish(
            output,
            source,
            plan,
            "qualification",
            started,
            child_processes=len(jobs),
            retained_paths=15,
            compatibility_pairs=3,
            native_rejections=9,
            deadline_controls=6,
            selection_controls=10,
            new_motion_searches=0,
            new_mask_queries=0,
            bridge_sha256=runtime["bridge_sha256"],
            all_children_reaped=True,
        )
        print("Native qualification raw retained; independent admission pending", flush=True)
    except Exception as error:
        failure(output, started, error)
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--library", type=Path, required=True)
    p.add_argument("--parent-library", type=Path, required=True)
    p.add_argument("--prefix", type=Path, required=True)
    a = p.parse_args()
    run(
        a.root.resolve(),
        a.source,
        a.library.resolve(),
        a.parent_library.resolve(),
        a.prefix.resolve(),
    )
