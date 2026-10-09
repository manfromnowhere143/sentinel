"""Pinned foreground collision functions, isolated from simulator imports."""

import ast
import hashlib
import math

import numpy as np
from shapely.geometry import Polygon


def validate_box(box):
    if (
        not isinstance(box, list)
        or len(box) != 7
        or any(type(x) not in (int, float) or not math.isfinite(x) for x in box)
        or any(box[k] <= 0 for k in (3, 4, 5))
    ):
        raise ValueError("invalid box")


class SourceGeometry:
    def __init__(self, rectangle_source, environment_source):
        namespace = dict(np=np, ShapelyPolygon=Polygon)
        self.ast_hashes = {}
        for raw, name in [
            (rectangle_source, "create_rectangle"),
            (environment_source, "fg_collision_det"),
        ]:
            nodes = [
                n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef) and n.name == name
            ]
            if len(nodes) != 1 or nodes[0].decorator_list:
                raise ValueError("source function")
            self.ast_hashes[name] = hashlib.sha256(
                ast.dump(nodes[0], include_attributes=False).encode()
            ).hexdigest()
            exec(
                compile(ast.Module(body=nodes, type_ignores=[]), "<bound-source-function>", "exec"),
                namespace,
            )
        self.rectangle = namespace["create_rectangle"]
        self.foreground = namespace["fg_collision_det"]

    def polygon(self, box):
        validate_box(box)
        x, y, _, width, length, _, yaw = box
        return self.rectangle(x, y, width, length, yaw)

    def measure(self, ego, objects):
        ep = self.polygon(ego)
        measurements = []
        for index, obj in enumerate(objects):
            op = self.polygon(obj)
            measurements.append(
                dict(
                    index=index,
                    intersects=bool(ep.intersects(op)),
                    distance_m=float(ep.distance(op)),
                    overlap_area_m2=float(ep.intersection(op).area),
                )
            )
        union = any(x["intersects"] for x in measurements)
        if union != bool(self.foreground(ego, objects)):
            raise ValueError("source geometry internal mismatch")
        return dict(foreground=union, actors=measurements)
