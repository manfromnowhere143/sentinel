"""Prospective client output reduction; monitor/model calculation remains source-bound."""

import ast
from experiments.iter145_constrained_execution.client import instrument as delivery_instrument


def instrument(raw):
    source = delivery_instrument(raw).decode()
    tree = ast.parse(source)
    body = next(n.body for n in ast.walk(tree) if isinstance(n, ast.While))
    start = next(
        i
        for i, node in enumerate(body)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "process" for t in node.targets)
    )
    nodes = body[start : start + 3]
    expected = ast.parse(
        "process = multiprocessing.Process(target=save_visualize_img, args=(results[0], raw_images, save_fn))\nvis_process_pool.append(process)\nprocess.start()\n"
    ).body
    if [ast.dump(n) for n in nodes] != [ast.dump(n) for n in expected]:
        raise ValueError("visualization_source_anchor")
    lines = source.splitlines(keepends=True)
    del lines[nodes[0].lineno - 1 : nodes[-1].end_lineno]
    result = "".join(lines)
    altered = ast.parse(result)
    del body[start : start + 3]
    if ast.dump(tree) != ast.dump(altered):
        raise ValueError("unexpected_client_delta")
    compile(result, "iter146_client.py", "exec")
    return result.encode()
