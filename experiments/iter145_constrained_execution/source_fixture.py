"""Bound full retained environment methods with explicitly scoped CPU substitutes."""

import ast
from copy import deepcopy
import hashlib
import json
import math
from types import SimpleNamespace
import numpy as np
import torch
from scipy.spatial.transform import Rotation
from experiments.iter144_timed_trajectory.source import bound_inputs, load_sampler
from experiments.iter143_model_contract.qualification import Extractor, ENV

ACTORS = "experiments/iter136_hugsim_recoverability_canary/proof/source/HUGSIM/sim/utils/agent_controller.py.txt"
UTILS = "experiments/iter136_hugsim_recoverability_canary/proof/source/HUGSIM/sim/utils/sim_utils.py.txt"


class FixturePolygon:
    """CPU separating-axis substitute for unavailable local Shapely/GEOS."""

    def __init__(self, points):
        self.points = np.asarray(list(points), dtype=float)

    def intersects(self, other):
        for polygon in (self.points, other.points):
            for a, b in zip(polygon, np.roll(polygon, 1, axis=0)):
                axis = np.array([a[1]-b[1], b[0]-a[0]])
                first, second = self.points @ axis, other.points @ axis
                if max(first) < min(second) or max(second) < min(first):
                    return False
        return True


def source_namespace(root):
    blobs = bound_inputs(root)
    additions = json.loads((root / "experiments/iter145_constrained_execution/SOURCE_ADDITIONS.json").read_text())
    for row in additions:
        data = (root / row["path"]).read_bytes()
        if len(data) != row["bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise ValueError("additional source identity")
        blobs[row["path"]] = data
    extract = Extractor(blobs)
    ns = dict(np=np, torch=torch, nn=torch.nn, F=torch.nn.functional, math=math,
              deepcopy=deepcopy, SCR=Rotation, gymnasium=SimpleNamespace(Env=object),
              SplinePlanner=type(load_sampler(root)), ShapelyPolygon=FixturePolygon)
    path = "experiments/iter145_constrained_execution/source/dynamic_utils.py.txt"
    extract.compile([n for n in ast.parse(blobs[path]).body if isinstance(n, ast.ClassDef) and n.name == "unicycle"], ns)
    nodes = [n for n in ast.parse(blobs[ACTORS]).body if isinstance(n, (ast.ClassDef, ast.FunctionDef))]
    extract.compile(nodes, ns)
    extract.compile([extract.node(UTILS, "rt2pose"), extract.node(UTILS, "pose2rt")], ns)
    extract.compile([extract.node("experiments/iter145_constrained_execution/source/score_calculator.py.txt", "create_rectangle"), extract.node(ENV, "fg_collision_det")], ns)
    # The whole HUGSimEnv class is compiled unchanged; its asset-loading constructor
    # is intentionally not invoked in this CPU fixture.
    extract.compile([n for n in ast.parse(blobs[ENV]).body if isinstance(n, ast.ClassDef) and n.name == "HUGSimEnv"], ns)
    return ns


def fixture(root, *, speed=4.0, heading=0.0, actors=("AttackPlanner", "ConstantPlanner", "IDM", "UnicyclePlanner")):
    ns = source_namespace(root)
    env = ns["HUGSimEnv"].__new__(ns["HUGSimEnv"])
    env.dt = 0.25
    env.kinematic = dict(dt=.25, Lr=1.35, Lf=1.35, min_acc=-2., max_acc=2.,
                         min_steer=-math.pi/12, max_steer=math.pi/12, start_steer=0.0)
    env.start_vr = np.array([0., heading, 0.])
    env.start_vab, env.start_velo = np.zeros(2), speed
    env.vr, env.vab, env.velo = env.start_vr.copy(), env.start_vab.copy(), speed
    env.steer, env.timestamp, env.last_accel, env.last_steer_rate = 0., 0., 0., 0.
    env.whl, env.ego_verts = np.array([1.6, 1.5, 3.]), np.zeros((8, 3))
    poses = np.tile(np.eye(4), (100, 1, 1))
    poses[:, 0, 3] = np.arange(100) * math.sin(heading)
    poses[:, 2, 3] = np.arange(100) * math.cos(heading)
    env.ground_model = (poses, 0., [2]*100)
    env.cam_rect, env.data_type = np.eye(4), "nuscenes"
    env.cam_params = {name: dict(v2c=np.eye(4), intrinsic={}) for name in (
        "CAM_FRONT", "CAM_FRONT_LEFT", "CAM_FRONT_RIGHT", "CAM_BACK", "CAM_BACK_LEFT", "CAM_BACK_RIGHT")}
    stats, controllers, routes, wlhs = {}, {}, {}, {}
    for index, kind in enumerate(actors):
        name = f"agent_{index}"
        value = torch.tensor([15.+index*10, 20., 0., .2, 3.], dtype=torch.float64)
        if kind == "UnicyclePlanner":
            ctrl = ns[kind].__new__(ns[kind])
            stamps = torch.arange(0, 20.25, .25)
            centers = torch.stack([15.+index*10+3*stamps, 20.+stamps*.1], dim=-1)
            angles = torch.zeros((len(stamps), 3)); angles[:, 2] = stamps*.02
            ctrl.uc_model = ns["unicycle"](stamps, centers, angles)
            ctrl.speed, ctrl.t = 1., 0.
            a,b,v,_,yaw,_ = ctrl.uc_model.forward(0.)
            value = torch.tensor([a,b,0.,yaw,v], dtype=torch.float64)
        else:
            ctrl = ns[kind]()
        stats[name], controllers[name] = value, ctrl
        routes[name] = torch.tensor([[float(value[0]), 20.+i, .2] for i in range(200)], dtype=torch.float64) if kind == "IDM" else None
        wlhs[name] = [2., 4., 1.5]
    env.planner = SimpleNamespace(dt=.25, PREDICT_STEPS=20, NUM_NEIGHBORS=3, stats=stats,
                                  controller=controllers, route=routes, wlhs=wlhs, rectify_angle=0.,
                                  ground_height=lambda a,b: 0.)
    env.render_kwargs, env.points = {}, None
    calls = []
    def render(**kwargs):
        calls.append(dict(kind="render", time=env.timestamp, planning_id=id(kwargs["planning"]),
                          matrices={n: m.tolist() for n,m in kwargs["planning"][0].items()}))
        return dict(render=torch.zeros((3,2,2)), feats=torch.zeros((2,2,2)), depth=torch.ones((1,2,2)))
    env.render_fn = render
    ns["create_cam"] = lambda intrinsic, c2w: c2w
    ns["bg_collision_det"] = lambda points, verts: False
    source_foreground = ns["fg_collision_det"]
    def foreground(box, objects):
        calls.append(dict(kind="collision", time=env.timestamp, planning_id=id(env.render_kwargs["planning"]), boxes=deepcopy(objects)))
        return source_foreground(box, objects)
    ns["fg_collision_det"] = foreground
    return env, calls
