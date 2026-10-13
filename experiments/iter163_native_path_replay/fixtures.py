"""Actual retained source methods with explicit CPU render/background/height substitutes."""

from pathlib import Path
from unittest.mock import patch
import numpy as np
import torch
from experiments.iter145_constrained_execution.source_fixture import fixture
from experiments.iter146_route_outcome_contract.check import read
from .contract import packet
from .records import read as document
from .admission import BASE
from .runner import run


def environment(root, geometry, *, background=False):
    env, calls = fixture(Path(root), speed=1.0, actors=("ConstantPlanner",))
    points = np.array(geometry["route"])
    poses = np.tile(np.eye(4), (len(points), 1, 1))
    poses[:, 0, 3], poses[:, 2, 3] = points[:, 0], points[:, 1]
    env.ground_model = (poses, 0.0, [2] * len(points))
    box = geometry["obstacles"][0]
    env.planner.stats["agent_0"] = torch.tensor(
        [-box[1], box[0], -box[2], 0.2800000011920929, 0.0], dtype=torch.float64
    )
    env.planner.wlhs["agent_0"] = box[3:6]
    env.step.__func__.__globals__["bg_collision_det"] = lambda points, verts: background
    return env, calls


def execute(root, output, *, background=False, mutate=lambda env: None, full_background=False):
    selected, geometry = packet(root)
    slot = document(Path(root) / BASE / "STUDY_PLAN.json")["slots"][0]
    env, calls = environment(root, geometry, background=background)
    if full_background:
        import ast
        from .background import tapped, capture
        from .background_check import population
        from experiments.iter155_background_witness.source import box_statements

        binding, points, ground = population(root)
        env.points = torch.tensor(points, dtype=torch.float32)
        env.ground_model = (np.array(ground), 0.0, [2] * len(ground))
        native = Path(root) / binding["source_path"]
        tree = ast.parse(native.read_text())
        node = next(
            n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "bg_collision_det"
        )
        namespace = {"torch": torch}
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(native), "exec"), namespace)
        box_statements((Path(root) / binding["raw_path"] / "hug_sim.py.txt").read_text(), env, np)
        captured = []
        predicate = tapped(
            namespace["bg_collision_det"],
            lambda m, p, b: captured.append(capture(m, p, b)),
            binding["predicate_ast_sha256"],
        )

        def measured(points, box):
            result = predicate(points, box)
            calls.append(
                dict(
                    kind="background",
                    time=float(env.timestamp),
                    points=len(points),
                    result=bool(result),
                    **captured.pop(),
                )
            )
            return result

        env.step.__func__.__globals__["bg_collision_det"] = measured
    mutate(env)
    with patch.object(torch.Tensor, "cuda", lambda self, *a, **k: self):
        summary = run(
            env, output=output, slot=slot, selected=selected, geometry=geometry, device="cpu"
        )
    rows, retained = read(output)
    assert retained == summary
    return rows, summary, selected, geometry, slot, calls
