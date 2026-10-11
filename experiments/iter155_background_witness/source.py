"""Extract exact bound native method bodies without constructing a driving environment."""

import ast
import copy


def background_function(source, torch, mask=False):
    tree = ast.parse(source)
    function = next(
        n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "bg_collision_det"
    )
    function = copy.deepcopy(function)
    if mask:
        if not isinstance(function.body[-1], ast.Return):
            raise ValueError("source_return")
        function.body[-1] = ast.Return(value=ast.Name(id="mask", ctx=ast.Load()))
    module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    namespace = {"torch": torch}
    exec(compile(module, "bound_background_source", "exec"), namespace)
    return namespace["bg_collision_det"]


def box_statements(source, env, np):
    tree = ast.parse(source)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "HUGSimEnv")
    init = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
    nodes = []
    for node in init.body:
        target = (
            node.targets[0]
            if isinstance(node, ast.Assign)
            else node.target
            if isinstance(node, ast.AugAssign)
            else None
        )
        if (
            isinstance(target, ast.Attribute)
            and isinstance(target.value, ast.Name)
            and target.value.id == "self"
            and target.attr in ("ego_verts", "whl")
        ):
            nodes.append(node)
    if len(nodes) != 3:
        raise ValueError("source_box_statements")
    exec(
        compile(ast.Module(body=nodes, type_ignores=[]), "bound_box_source", "exec"),
        {"self": env, "np": np},
    )
