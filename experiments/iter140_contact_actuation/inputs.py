"""Read only the bytes bound by the retrospective protocol."""

import hashlib
import json
import math
import os
from pathlib import Path
import stat

OLD = "experiments/iter139_finite_pulse_recoverability"
SOURCE = "experiments/iter136_hugsim_recoverability_canary/proof/source/HUGSIM"
HOST = "experiments/iter136_hugsim_recoverability_canary/proof/host_runtime_1.json"
SCENARIO_PATH = (
    "/datasets/nuscenes-full/hugsim/extracted/scenarios/nuscenes/scene-0411-hard-00.yaml"
)
SCENARIO_SHA = "9f38bbdcdc49fe6ac5274a967b9a209417d621f67060357b97deacb887cf67a9"
ARMS = (
    "reference_a",
    "reference_b",
    "pulse_0_1",
    "pulse_0_2",
    "pulse_2_1",
    "pulse_2_2",
    "pulse_4_1",
    "pulse_4_2",
)


def pairs(items):
    out = {}
    for k, v in items:
        if k in out:
            raise ValueError("duplicate JSON key")
        out[k] = v
    return out


def strict_json(raw):
    def bad(value):
        raise ValueError("nonfinite JSON")

    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)

    def finite(v):
        if isinstance(v, float) and not math.isfinite(v):
            raise ValueError("overflowed JSON number")
        if isinstance(v, dict):
            for x in v.values():
                finite(x)
        elif isinstance(v, list):
            for x in v:
                finite(x)

    finite(value)
    return value


def read_bound(root, name, record):
    rel = Path(name)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("input path")
    p = Path(root)
    for part in rel.parts:
        p /= part
        if p.is_symlink():
            raise ValueError("symlink input")
    if not 0 <= record["bytes"] <= 16 * 1024 * 1024:
        raise ValueError("input size bound")
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("nonregular input")
        raw = stream.read(record["bytes"] + 1)
    if len(raw) != record["bytes"] or hashlib.sha256(raw).hexdigest() != record["sha256"]:
        raise ValueError("input byte identity: " + name)
    return raw


def load_inputs(root, manifest):
    return {name: read_bound(root, name, r) for name, r in manifest["files"].items()}


def source_contract(blobs):
    files = strict_json(strict_json(blobs[HOST])["stdout"])["files"]
    scenario = files[SCENARIO_PATH]["text"].encode()
    runtime = strict_json(blobs[OLD + "/proof/runtime_manifest.json"])
    if (
        hashlib.sha256(scenario).hexdigest() != SCENARIO_SHA
        or runtime["files"][SCENARIO_PATH] != SCENARIO_SHA
    ):
        raise ValueError("scenario binding")
    # This is the single hash-bound scenario, not a general YAML parser.
    lines = scenario.decode().splitlines()
    if (
        lines.count("- - 0") != 1
        or lines.count("  - AttackPlanner") != 1
        or lines.count("    ATTACK_FREQ: 10") != 1
    ):
        raise ValueError("registered scenario contract")
    for rel in (
        "sim/hugsim_env/envs/hug_sim.py",
        "sim/utils/plan.py",
        "sim/utils/agent_controller.py",
        "configs/sim/kinematic.yaml",
    ):
        if (
            hashlib.sha256(blobs[SOURCE + "/" + rel + ".txt"]).hexdigest()
            != runtime["files"]["/opt/sentinel-stack/HUGSIM/" + rel]
        ):
            raise ValueError("runtime source binding")
    if (
        hashlib.sha256(blobs[OLD + "/proof/score_calculator.py.txt"]).hexdigest()
        != runtime["files"]["/opt/sentinel-stack/HUGSIM/sim/utils/score_calculator.py"]
    ):
        raise ValueError("geometry source binding")
    return dict(
        scenario_sha256=SCENARIO_SHA,
        configured_actors=1,
        planner="AttackPlanner",
        attack_freq=10,
        pred_steps=20,
        dt=0.25,
        wheelbase=2.7,
        identity="source-inferred agent_0 when every state has one box; no logged actor ID",
    )


def traces(blobs):
    from experiments.iter139_finite_pulse_recoverability.trace import validate

    result = {}
    for arm in ARMS:
        raw = blobs[OLD + "/proof/live/" + arm + "/scene-0411_hard_00/iter139_trace.jsonl"]
        if not raw.endswith(b"\n"):
            raise ValueError("trace final newline")
        rows = [strict_json(line) for line in raw.splitlines()]
        validate(rows)
        result[arm] = rows
    return result
