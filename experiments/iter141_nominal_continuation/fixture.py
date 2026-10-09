"""Bound generated driver and original monitor with synthetic model/environment stubs."""

import ast
import hashlib
import json
import os
from pathlib import Path
import pickle
from types import SimpleNamespace

import numpy as np

from experiments.iter141_nominal_continuation import client, instrument, live_trace

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "experiments/iter136_hugsim_recoverability_canary"


class Tensor:
    def __init__(self, value):
        self.value = np.asarray(value)

    def numpy(self):
        return self.value

    def detach(self):
        return self

    def cpu(self):
        return self


def monitor_namespace():
    raw = (Path(__file__).parent / "source/e2e.py.txt").read_bytes()
    text = instrument.instrument_client(raw).decode()
    segment = text[text.index("import json as _sjson") : text.index("\ndef parse_args")]
    ns = {"np": np}
    exec(compile(segment, "bound_original_monitor", "exec"), ns)
    return ns


def state(t):
    return dict(
        timestamp=t,
        ego_pos=[t, 0.0, 0.0],
        ego_rot=[0.0] * 3,
        ego_velo=1.0,
        ego_steer=0.0,
        accelerate=0.0,
        steer_rate=0.0,
        command=2,
        ego_box=[0.0] * 7,
        obj_boxes=[[1.0] * 7],
    )


def run(folder, arm, count=4):
    folder = Path(folder)
    folder.mkdir()
    source = instrument.instrument((OLD / "proof/source/HUGSIM/closed_loop.py.txt").read_bytes())
    driver = folder / "driver.py"
    driver.write_bytes(source)
    identity = json.loads((OLD / "proof/runtime_v2/identity.json.txt").read_text())
    identity["driver_sha256"] = hashlib.sha256(source).hexdigest()
    identity["client_sha256"] = hashlib.sha256(
        instrument.instrument_client((Path(__file__).parent / "source/e2e.py.txt").read_bytes())
    ).hexdigest()
    (folder / "identity.json").write_text(json.dumps(identity))
    os.environ.update(
        SENTINEL_I141_IDENTITY=str(folder / "identity.json"),
        SENTINEL_I141_ARM=arm,
        SENTINEL_I141_MODE=arm.rsplit("_", 1)[0],
        SENTINEL_ENABLED="1",
    )
    monitor = monitor_namespace()
    obs = {k: {"front": np.zeros((2, 2), dtype="float32")} for k in ("rgb", "semantic", "depth")}
    actions = []
    resets = []

    def reset():
        resets.append(True)
        return obs, state(0.0)

    def step(action):
        actions.append(action)
        i = len(actions)
        info = state(i * 0.25)
        info.update(
            rc=1.02 if i == count and arm.startswith("nominal") else 0.2,
            collision=i == count and arm.startswith("reference"),
        )
        return obs, 0.0, i == count, False, info

    def receive(_):
        i = len(actions)
        plan = np.array([[0.1 * i, 1.0 + 0.1 * i]] * 6, dtype="float32")
        result = {
            "boxes_3d": SimpleNamespace(
                gravity_center=Tensor([[100, 100, 0]] if i == 0 else [[0.1 * i, 1.0 + 0.1 * i, 0]])
            ),
            "scores_3d": Tensor([0.9]),
            "track_ids": Tensor([1]),
        }
        data = {
            "l2g_r_mat": Tensor(np.eye(3)),
            "l2g_t": Tensor([0.0, 0.0, 0.0]),
            "timestamp": i * 0.25,
        }
        delivered = client.deliver(
            plan, result, data, folder, monitor["_sentinel_i48_intervene"], monitor["_S48_ENABLED"]
        )
        # Exercise dtype-preserving actual transport serialization.
        return pickle.loads(pickle.dumps(delivered))

    (folder / "obs_pipe").touch()
    (folder / "plan_pipe").write_bytes(b"fixture")
    node = next(
        n
        for n in ast.parse(source).body
        if isinstance(n, ast.FunctionDef) and n.name == "create_gym_env"
    )
    ns = dict(
        __file__=str(driver),
        Recorder=live_trace.Recorder,
        os=os,
        pickle=SimpleNamespace(loads=receive, dumps=pickle.dumps, dump=pickle.dump),
        json=json,
        np=np,
        gymnasium=SimpleNamespace(make=lambda *a, **k: SimpleNamespace(reset=reset, step=step)),
        traj_transform_to_global=lambda *a: [],
        to_video=lambda *a: None,
        hugsim_evaluate=lambda *a: {},
        o3d=SimpleNamespace(
            io=SimpleNamespace(read_point_cloud=lambda p: SimpleNamespace(points=np.zeros((1, 3))))
        ),
    )
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(driver), "exec"), ns)
    ns["create_gym_env"]({}, str(folder))
    if len(resets) != 2 or len(actions) != count:
        raise ValueError("stub driver path incomplete")
    return actions


def main():
    import argparse
    from experiments.iter137_controller_execution_contract.verify import Replay
    from experiments.iter141_nominal_continuation import verify_live as v, independent

    p = argparse.ArgumentParser()
    p.add_argument("output", type=Path)
    args = p.parse_args()
    args.output.mkdir()
    results = {}
    captures = {}
    replay = Replay()
    for arm in ("reference_a", "reference_b", "nominal_a", "nominal_b"):
        run(args.output / arm, arm)
        captures[arm] = v.validate_episode(args.output / arm, replay)
        results[arm] = captures[arm][-1]
    a, ca, da, _ = captures["reference_a"]
    for arm in ("reference_b", "nominal_a", "nominal_b"):
        b, cb, db, _ = captures[arm]
        results[arm]["comparison"] = v.compare(a, b, ca, cb, da, db)
        secondary = independent.check(args.output / "reference_a", args.output / arm)
        if arm.startswith("nominal"):
            outcome = v.outcomes(a, b, db)
            if not outcome["useful_recovery"] or outcome != secondary["outcomes"]:
                raise ValueError("fixture outcome")
            results[arm]["synthetic_outcome"] = outcome
    print(
        json.dumps(
            dict(
                status="passed",
                scope="synthetic integration only; no live simulator construction",
                arms=results,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
