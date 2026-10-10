"""Execute bounded source slices as CPU fixtures; never import the simulator."""

import argparse
import ast
from copy import deepcopy
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import platform
import re
import stat
from types import SimpleNamespace

import numpy as np
import scipy
from scipy.interpolate import interp1d
import torch

BASE = "experiments/iter143_model_contract"
OLD = "experiments/iter136_hugsim_recoverability_canary/proof/"
ENV = OLD + "source/HUGSIM/sim/hugsim_env/envs/hug_sim.py.txt"
AGENT = OLD + "source/HUGSIM/sim/utils/agent_controller.py.txt"
PLAN = OLD + "source/HUGSIM/sim/utils/plan.py.txt"
SOLVER = OLD + "controller_source/lqr_solver.py.txt"
PARAMS = OLD + "controller_source/lqr.py.txt"
UTIL = OLD + "controller_source/utils.py.txt"
KIN = OLD + "source/HUGSIM/configs/sim/kinematic.yaml.txt"
SPLINE = BASE + "/source/spline_planner.py.txt"
INVENTORIES = [
    "experiments/iter46_hugsim_off_baseline/proof-off/frozen_scenarios.sha256",
    "experiments/iter49_hugsim_hard_tier_gate/proof-hard/frozen_scenarios_hard.sha256",
]


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    def invalid(value):
        raise ValueError("nonfinite JSON: " + value)

    result = json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)

    def finite(value):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("nonfinite value")
        if isinstance(value, dict):
            for item in value.values():
                finite(item)
        if isinstance(value, list):
            for item in value:
                finite(item)

    finite(result)
    return result


def bounded_read(root, name):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("unsafe input path")
    current = root
    for part in path.parts:
        current /= part
        if current.is_symlink():
            raise ValueError("symlink input")
    fd = os.open(current, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        meta = os.fstat(stream.fileno())
        if not stat.S_ISREG(meta.st_mode) or meta.st_size > 16 * 1024 * 1024:
            raise ValueError("input size/type")
        raw = stream.read(16 * 1024 * 1024 + 1)
    if len(raw) != meta.st_size:
        raise ValueError("input changed during read")
    return raw


def inputs(root):
    manifest_raw = bounded_read(root, BASE + "/INPUTS.json")
    manifest = strict_json(manifest_raw)
    records = dict(manifest["files"])
    records.update({x["path"]: x for x in manifest["retrieved_sources"]})
    blobs = {}
    for name, record in records.items():
        raw = bounded_read(root, name)
        if len(raw) != record["bytes"] or hashlib.sha256(raw).hexdigest() != record["sha256"]:
            raise ValueError("input identity: " + name)
        blobs[name] = raw
    runtime = strict_json(
        blobs["experiments/iter142_nominal_continuation_completion/proof/runtime_manifest.json"]
    )
    for record in manifest["retrieved_sources"]:
        if runtime["files"][record["prior_runtime_path"]] != record["sha256"]:
            raise ValueError("prior runtime identity")
    return blobs, hashlib.sha256(manifest_raw).hexdigest()


class Extractor:
    def __init__(self, blobs):
        self.blobs = blobs
        self.records = []

    def node(self, path, name, owner=None):
        tree = ast.parse(self.blobs[path])
        body = tree.body
        if owner:
            body = next(x for x in body if isinstance(x, ast.ClassDef) and x.name == owner).body
        node = deepcopy(next(x for x in body if isinstance(x, ast.FunctionDef) and x.name == name))
        self.records.append(
            dict(path=path, owner=owner, name=name, start=node.lineno, end=node.end_lineno)
        )
        return node

    @staticmethod
    def compile(nodes, namespace):
        module = ast.Module(
            body=[
                ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
                *nodes,
            ],
            type_ignores=[],
        )
        exec(compile(ast.fix_missing_locations(module), "<bound-source-slice>", "exec"), namespace)
        return namespace


def source_adapters(blobs):
    extract = Extractor(blobs)
    namespace = dict(np=np, torch=torch, math=math, deepcopy=deepcopy, interp1d=interp1d)
    cfg = {
        k.strip(): float(v)
        for line in blobs[KIN].decode().splitlines()
        for k, v in [line.split(":", 1)]
    }
    params_node = next(
        n
        for n in ast.parse(blobs[PARAMS]).body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "solver_params" for t in n.targets)
    )
    params = eval(
        compile(ast.Expression(params_node.value), PARAMS, "eval"),
        dict(np=np, ILQRSolverParameters=SimpleNamespace),
    )
    namespace["principal_value"] = extract.compile(
        [extract.node(UTIL, "principal_value")], dict(np=np)
    )["principal_value"]
    methods = [
        extract.node(SOLVER, n, "ILQRSolver")
        for n in ["_clip_inputs", "_clip_steering_angle", "_dynamics_and_jacobian"]
    ]
    compiled = extract.compile(methods, dict(namespace))
    solver = type("SourceDynamics", (), {n.name: compiled[n.name] for n in methods})()
    solver._solver_params = params
    solver._n_states, solver._n_inputs = 5, 2
    solver._input_clip_min = (-params.max_acceleration, -params.max_steering_angle_rate)
    solver._input_clip_max = (params.max_acceleration, params.max_steering_angle_rate)
    env = extract.node(ENV, "step", "HUGSimEnv")
    boundary = next(
        i
        for i, n in enumerate(env.body)
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "terminated" for t in n.targets)
    )
    env.body = env.body[:boundary]
    extract.records[-1]["executed_end"] = env.body[-1].end_lineno
    extract.records[-1]["omitted"] = "rendering, collision, route termination, observation and info"
    env_func = extract.compile([env], dict(namespace))["step"]

    def environment(state, control, dt):
        x, y, heading, velocity, steer = state
        instance = SimpleNamespace(
            timestamp=0.0,
            dt=dt,
            planner=None,
            kinematic=cfg,
            velo=velocity,
            steer=steer,
            vab=np.array([y, x], dtype=float),
            vr=np.array([0.0, heading, 0.0]),
        )
        env_func(instance, dict(acc=control[0], steer_rate=control[1]))
        return [
            float(instance.vab[1]),
            float(instance.vab[0]),
            float(instance.vr[1]),
            float(instance.velo),
            float(instance.steer),
        ]

    def controller(state, control, dt):
        params.discretization_time = dt
        out, applied, _, _ = solver._dynamics_and_jacobian(
            np.array(state, dtype=float), np.array(control, dtype=float)
        )
        return out.tolist(), applied.tolist()

    functions = [
        extract.node(AGENT, "constant_headaway"),
        extract.node(SPLINE, "compute_spline_xyvaqrt"),
    ]
    namespace = extract.compile(functions, namespace)
    attack_node = extract.node(AGENT, "update", "AttackPlanner")
    attack_func = extract.compile([attack_node], dict(namespace))["update"]
    attack_type = type("AttackPlanner", (), {"update": attack_func})
    namespace.update(
        AttackPlanner=attack_type,
        IDM=type("IDM", (), {}),
        ConstantPlanner=type("ConstantPlanner", (), {}),
        UnicyclePlanner=type("UnicyclePlanner", (), {}),
    )
    dispatch = extract.node(PLAN, "plan_traj", "planner")
    loop = next(
        n
        for n in dispatch.body
        if isinstance(n, ast.For)
        and any(
            isinstance(x, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "b2w" for t in x.targets)
            for x in n.body
        )
    )
    stop = next(
        i
        for i, n in enumerate(loop.body)
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "b2w" for t in n.targets)
    )
    loop.body = loop.body[:stop]
    dispatch.body = dispatch.body[: dispatch.body.index(loop) + 1]
    extract.records[-1]["executed_end"] = loop.body[-1].end_lineno
    extract.records[-1]["omitted"] = (
        "ground/rotation/render placement; actual controller dispatch and state assignment retained"
    )
    dispatch_func = extract.compile([dispatch], dict(namespace))["plan_traj"]
    gen = extract.node(SPLINE, "gen_trajectories", "SplinePlanner")
    gen_func = extract.compile([gen], dict(namespace, STATE_INDEX=[0, 1, 2, 4]))["gen_trajectories"]
    return (
        environment,
        controller,
        cfg,
        params,
        namespace,
        attack_type,
        dispatch_func,
        gen_func,
        extract,
    )


def low_speed_probe(gen, n=20, tf=2.0):
    class SyntheticSampler:
        dt = 0.1

        def sample_trajs(self, state, steps):
            t = torch.arange(1, steps + 1, dtype=torch.float64) * self.dt
            rows = torch.stack([t, t * 0, t * 0 + 1, t * 0, t * 0, t * 0, t], dim=-1)
            return rows[None, None]

    low = SimpleNamespace(
        N_seg=n,
        device="cpu",
        low_speed_threshold=2.0,
        forward_sampler=SyntheticSampler(),
        gen_terminals=lambda x, tf: torch.tensor([[0.0, 0.0, 1.0, 0.0]], dtype=torch.float64),
        calc_trajectories=lambda x, tf, xf, n: torch.zeros((1, n, 7), dtype=torch.float64),
        feasible_flag=lambda t, xf: torch.zeros(1, dtype=torch.bool),
    )
    low_rows, _ = gen(low, torch.tensor([0.0, 0.0, 1.0, 0.0], dtype=torch.float64), tf)

    return low_rows


def dispatch_probe(ns, attack_type, dispatch, cfg, steps=21):
    spline = ns["compute_spline_xyvaqrt"]
    generation_calls = []
    dispatch_calls = []

    class CandidateGenerator:
        def gen_trajectories(self, x0, tf, lanes, dyn_filter):
            generation_calls.append(
                dict(horizon=float(tf), state=x0.tolist(), dyn_filter=dyn_filter)
            )
            speed, angle = float(x0[2]), float(x0[3])
            xc = torch.tensor(
                [[float(x0[0]), speed * math.cos(angle), 0.0, 0.0]], dtype=torch.float64
            )
            yc = torch.tensor(
                [[float(x0[1]), speed * math.sin(angle), 0.0, 0.0]], dtype=torch.float64
            )
            traj = spline(xc, yc, torch.tensor([tf], dtype=torch.float64), N=20)
            return traj[:, 1:], None

    attack = attack_type()
    attack.device, attack.predict_steps, attack.best_k = "cpu", 20, 1
    attack.exec_traj, attack.exec_pointer, attack.planner = None, 1, CandidateGenerator()
    original_update = attack.update

    def record_update(**kwargs):
        dispatch_calls.append(
            dict(
                dt=kwargs["dt"],
                requested_replan=kwargs["new_plan"],
                attacked_states=kwargs["attacked_states"].tolist(),
            )
        )
        return original_update(**kwargs)

    attack.update = record_update
    planner = SimpleNamespace(
        stats={"agent_0": torch.tensor([0.0, 0.0, 0.0, 0.0, 4.0], dtype=torch.float32)},
        controller={"agent_0": attack},
        route={"agent_0": None},
        dt=cfg["dt"],
        PREDICT_STEPS=20,
        NUM_NEIGHBORS=3,
        ATTACK_FREQ=10,
        unified_map=None,
    )
    schedule = []
    for i in range(steps):
        t = i * cfg["dt"]
        dispatch(planner, t, torch.tensor([0.0, 0.0, 0.0, 4.0], dtype=torch.float32))
        schedule.append(
            dict(
                time=t,
                **dispatch_calls[-1],
                generation_count=len(generation_calls),
                pointer_after=attack.exec_pointer,
                actor_state=planner.stats["agent_0"].tolist(),
            )
        )
    return schedule, generation_calls


def probes(root):
    blobs, identity = inputs(root)
    environment, controller, cfg, params, ns, attack_type, dispatch, gen, extract = source_adapters(
        blobs
    )
    frozen_controller_dt = 0.5
    assert params.discretization_time == frozen_controller_dt
    ego = []
    for index, (v, heading, steering, control) in enumerate(
        itertools.product(
            [0.0, 4.0], [0.0, 0.3], [0.0, 0.2], [(0.0, 0.0), (2.0, 0.2), (-2.0, -0.2), (3.0, 0.4)]
        )
    ):
        state = [0.0, 0.0, heading, v, steering]
        one = environment(state, control, cfg["dt"])
        quarter, applied_quarter = controller(state, control, cfg["dt"])
        half, applied_half = controller(state, control, frozen_controller_dt)
        ego.append(
            dict(
                id=index,
                state=state,
                control=list(control),
                environment_one=one,
                controller_quarter=quarter,
                applied_quarter=applied_quarter,
                environment_two=environment(one, control, cfg["dt"]),
                controller_half=half,
                applied_half=applied_half,
            )
        )
    limits = []
    for control in [
        (2.0, 0.0),
        (-2.0, 0.0),
        (0.0, math.pi / 12),
        (0.0, -math.pi / 12),
        (3.0, 0.0),
        (-3.0, 0.0),
        (0.0, 0.4),
        (0.0, -0.4),
    ]:
        state = [0.0, 0.0, 0.0, 4.0, 0.0]
        limits.append(
            dict(control=list(control), before=state, after=environment(state, control, cfg["dt"]))
        )
    spline = ns["compute_spline_xyvaqrt"]
    trajectory = spline(
        torch.tensor([[0.0, 4.0, 0.0, 0.0]], dtype=torch.float64),
        torch.zeros((1, 4), dtype=torch.float64),
        torch.tensor([2.0], dtype=torch.float64),
        N=20,
    )[0]
    fallback = ns["constant_headaway"](
        torch.tensor([[0.0, 0.0, math.pi / 2, 4.0]], dtype=torch.float64), 20, 0.1
    )[0]

    low_rows = low_speed_probe(gen)

    schedule, generation_calls = dispatch_probe(ns, attack_type, dispatch, cfg)

    return dict(
        schema="sentinel.iter143.raw.v1",
        input_manifest_sha256=identity,
        environment=dict(
            python=platform.python_version(),
            platform=platform.platform(),
            numpy=np.__version__,
            torch=torch.__version__,
            scipy=scipy.__version__,
            device="cpu",
        ),
        extractions=extract.records,
        constants=dict(
            environment_dt=cfg["dt"],
            controller_dt=frozen_controller_dt,
            wheelbase=cfg["Lf"] + cfg["Lr"],
            declared_acc=[cfg["min_acc"], cfg["max_acc"]],
            declared_steering_rate=[
                -math.radians(cfg["min_steer"]),
                math.radians(cfg["max_steer"]),
            ],
            controller_acc=params.max_acceleration,
            controller_steering_rate=params.max_steering_angle_rate,
        ),
        ego=ego,
        limits=limits,
        actor=dict(
            spline=trajectory.tolist(),
            fallback=fallback.tolist(),
            low_speed=low_rows[0].tolist(),
            dispatch=schedule,
            generations=generation_calls,
        ),
        substitutions=[
            "CPU arrays and state-only source slices; no renderer, collision or ground",
            "single straight synthetic actor candidate; no full sampling/filtering policy",
            "synthetic linear forward sampler and empty spline candidates for resampling isolation",
            "supplied scenario constants and no map; no historical actor candidate identity",
        ],
    )


def inventory(root):
    blobs, identity = inputs(root)
    rows = {}
    for path in INVENTORIES:
        for line in blobs[path].decode().splitlines():
            match = re.fullmatch(
                r"([a-f0-9]{64})  (scene-(\d{4})-(easy|medium|hard|extreme)-(\d{2})\.yaml)", line
            )
            if not match:
                raise ValueError("malformed inventory")
            digest, name, scene, tier, variant = match.groups()
            if name in rows and rows[name]["sha256"] != digest:
                raise ValueError("conflicting scenario identity")
            rows[name] = dict(
                name=name,
                sha256=digest,
                scene=scene,
                tier=tier,
                variant=variant,
                exposure="historical_development",
                local_asset_availability="unobserved",
                role="closed_case_excluded" if scene == "0411" else "development_reserve",
            )
    scenes = sorted({r["scene"] for r in rows.values() if r["scene"] != "0411"})
    pilot = scenes[:3]
    for row in rows.values():
        if row["scene"] in pilot:
            row["role"] = "proposed_pilot"
    return dict(
        schema="sentinel.iter143.case_inventory.v1",
        input_manifest_sha256=identity,
        rows=[rows[k] for k in sorted(rows)],
        pilot_scenes=pilot,
        held_out_unexposed_scenes=[],
        selection="first three eligible base scene IDs lexically; all their inventory rows; no outcome lookup",
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--inventory", action="store_true")
    a = p.parse_args()
    try:
        result = inventory(a.root) if a.inventory else probes(a.root)
        code = 0
    except Exception as exc:
        result = dict(
            status="invalid",
            verdict="MODEL_CONTRACT_INVALID",
            error_type=type(exc).__name__,
            error=str(exc),
        )
        code = 2
    with a.output.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(output=str(a.output), returncode=code)))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
