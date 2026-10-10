"""Hash-bound upstream function/class loading, CPU only; source imports omitted."""

import ast
import hashlib
from types import SimpleNamespace
import numpy as np
from scipy.interpolate import interp1d
import torch

from experiments.iter143_model_contract.qualification import (
    BASE as PRIOR,
    ENV,
    Extractor,
    bounded_read,
    strict_json,
)
from .trajectory import ContractError

BASE = "experiments/iter144_timed_trajectory"


def bound_inputs(root):
    manifest = strict_json(bounded_read(root, BASE + "/INPUTS.json"))
    addition = strict_json(bounded_read(root, BASE + "/SOURCE_ADDITION.json"))
    records = dict(manifest["files"])
    records[addition["path"]] = addition
    blobs = {}
    for path, row in records.items():
        raw = bounded_read(root, path)
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ContractError("source_identity:" + path)
        blobs[path] = raw
    return blobs


def load_sampler(root, straight=False):
    blobs = bound_inputs(root)
    ns = dict(np=np, torch=torch, interp1d=interp1d, STATE_INDEX=[0, 1, 2, 4], device="cpu")
    geometry = BASE + "/source/geometry_utils.py.txt"
    extract = Extractor(blobs)
    rotation = extract.compile([extract.node(geometry, "batch_rotate_2D")], dict(ns))[
        "batch_rotate_2D"
    ]
    ns["GeoUtils"] = SimpleNamespace(batch_rotate_2D=rotation)
    # All sampler class methods run unchanged. Only imports, plots and __main__ omitted.
    for path in [PRIOR + "/source/forward_sampler.py.txt", PRIOR + "/source/spline_planner.py.txt"]:
        nodes = [
            n for n in ast.parse(blobs[path]).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))
        ]
        Extractor.compile(nodes, ns)
    kw = dict(dx_grid=[0.0], dy_grid=[0.0], acce_grid=[0.0], dyaw_grid=[0.0]) if straight else {}
    sampler = ns["SplinePlanner"]("cpu", N_seg=20, seed=144, **kw)
    if straight:
        sampler.forward_sampler = ns["ForwardSampler"](
            dt=0.1, acce_grid=[0.0], dhm_grid=[0.0], dhf_grid=[0.0], device="cpu"
        )
    return sampler


def environment_prefix(root):
    blobs = bound_inputs(root)
    extract = Extractor(blobs)
    node = extract.node(ENV, "step", "HUGSimEnv")
    boundary = next(
        i
        for i, n in enumerate(node.body)
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "terminated" for t in n.targets)
    )
    node.body = node.body[:boundary]
    return extract.compile([node], dict(np=np))["step"]
