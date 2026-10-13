"""Observe the source predicate's actual mask without changing its arithmetic or return."""

import ast
import hashlib
import inspect
import textwrap


def tapped(function, callback, expected_source):
    source = textwrap.dedent(inspect.getsource(function)).strip() + "\n"
    tree = ast.parse(source)
    identity = hashlib.sha256(source.encode()).hexdigest()
    if identity != expected_source:
        raise ValueError("background_source_identity")
    node = tree.body[0]
    if (
        len(tree.body) != 1
        or not isinstance(node, ast.FunctionDef)
        or node.name != "bg_collision_det"
        or not isinstance(node.body[-1], ast.Return)
        or sum(isinstance(n, ast.Return) for n in ast.walk(node)) != 1
    ):
        raise ValueError("background_source_shape")
    node.body.insert(-1, ast.parse("_sentinel_mask_observer(mask, points, box)").body[0])
    namespace = dict(function.__globals__, _sentinel_mask_observer=callback)
    exec(compile(ast.fix_missing_locations(tree), "<sentinel163-mask-tap>", "exec"), namespace)
    return namespace[node.name]


def capture(mask, points, box):
    import numpy as np
    import torch

    if (
        points.dtype != torch.float32
        or points.ndim != 2
        or tuple(points.shape[1:]) != (3,)
        or len(points) != 276519
        or box.dtype != torch.float32
        or tuple(box.shape) != (8, 3)
        or mask.dtype != torch.bool
        or tuple(mask.shape) != (len(points),)
        or not torch.isfinite(points).all().item()
        or not torch.isfinite(box).all().item()
    ):
        raise ValueError("background_input_shape")
    raw = points.detach().cpu().contiguous().numpy().astype("<f4", copy=False).tobytes()
    values = mask.detach().cpu().numpy()
    return dict(
        population_sha256=hashlib.sha256(raw).hexdigest(),
        population_dtype="<f4",
        box=box.detach().cpu().tolist(),
        mask_encoding="packbits_little_zero_padding",
        mask_hex=np.packbits(values, bitorder="little").tobytes().hex(),
        count=int(np.count_nonzero(values)),
    )
