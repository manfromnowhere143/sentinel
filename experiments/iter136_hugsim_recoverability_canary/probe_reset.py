"""Execute the pinned reset method with explicit lightweight state/renderer stubs."""

from __future__ import annotations

import argparse
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parent
HUGSIM_COMMIT = "62c690d39fd90020e68a196bd8bcc1c4d4191f2e"
RESET_SHA256 = "c42ef368852754bdec76c81254b72dcda45eccef058dce015ea549c0b17c7d12"


def load_reset(proof: Path = ROOT / "proof"):
    inventory = json.loads((proof / "source_inventory.json").read_text())
    entries = [r for r in inventory if r["repository"] == "hyzhou404/HUGSIM"
               and r["path"] == "sim/hugsim_env/envs/hug_sim.py"]
    if len(entries) != 1 or entries[0]["commit"] != HUGSIM_COMMIT:
        raise ValueError("source identity")
    entry = entries[0]
    path = proof / entry["retained_path"]
    if path.is_symlink() or not path.resolve().is_relative_to(proof.resolve()):
        raise ValueError("source path")
    raw = path.read_bytes()
    if len(raw) > 1_000_000 or not (
        hashlib.sha256(raw).hexdigest() == entry["sha256"] == RESET_SHA256
    ):
        raise ValueError("source bytes")
    tree = ast.parse(raw)
    methods = [f for c in tree.body if isinstance(c, ast.ClassDef)
               for f in c.body if isinstance(f, ast.FunctionDef) and f.name == "reset"]
    if len(methods) != 1:
        raise ValueError("reset method count")
    method = methods[0]
    module = ast.Module(body=[method], type_ignores=[])
    namespace = {"deepcopy": deepcopy}
    exec(compile(module, str(path), "exec"), namespace)
    return namespace["reset"], method, entry


class ActorStub:
    """A state-advancing planner stub; not a model of real actor dynamics."""

    def __init__(self):
        self.calls = 0

    def plan_traj(self, timestamp, ego_state):
        self.calls += 1
        return {"actor_update_count": self.calls}


def fixture():
    actor = ActorStub()
    env = SimpleNamespace(
        start_vr=[0.0, 0.0, 0.0], start_vab=[0.0, 0.0], start_velo=3.0,
        vr=[1.0, 2.0, 3.0], vab=[7.0, 8.0], velo=9.0, timestamp=99.0,
        steer=0.4, last_accel=-1.0, last_steer_rate=0.2,
        planner=actor, render_kwargs={}, ego_state="fixture-ego",
    )
    env._get_obs = lambda: deepcopy(env.render_kwargs)
    env._get_info = lambda: {
        "timestamp": env.timestamp, "steer": env.steer,
        "last_accel": env.last_accel, "last_steer_rate": env.last_steer_rate,
        "actor_update_count": actor.calls,
    }
    return env


def probe(proof: Path = ROOT / "proof") -> dict:
    reset, method, identity = load_reset(proof)
    env = fixture()
    first = reset(env, seed=136)
    second = reset(env, seed=136)
    clean_a, clean_b = fixture(), fixture()
    seed_a = reset(clean_a, seed=136)
    seed_b = reset(clean_b, seed=137)
    reads_seed = any(isinstance(n, ast.Name) and n.id == "seed"
                     and isinstance(n.ctx, ast.Load) for n in ast.walk(method))
    return {
        "schema": "sentinel.iter136.reset_probe.v1",
        "scope": "exact pinned reset method with stub observation and actor planner",
        "source": identity,
        "first_reset": first, "second_reset": second,
        "repeated_reset_equal": first == second,
        "steering_and_control_history_retained": second[1]["steer"] == 0.4
        and second[1]["last_accel"] == -1.0 and second[1]["last_steer_rate"] == 0.2,
        "seed_parameter_read_by_method": reads_seed,
        "fresh_fixture_outputs_equal_across_two_seeds": seed_a == seed_b,
        "live_simulation_observed": False,
        "decision": "REQUIRE_FRESH_PROCESS_REPLAY_VALIDATION",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proof", type=Path, default=ROOT / "proof")
    args = parser.parse_args()
    print(json.dumps(probe(args.proof), sort_keys=True, indent=2, allow_nan=False))
