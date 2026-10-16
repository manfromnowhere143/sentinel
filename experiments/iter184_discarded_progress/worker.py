"""One fresh conditional native tree; all queries retained inside search accounting."""

import argparse
import copy
from pathlib import Path

import numpy as np

from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter182_late_frontier_timing.retained import state_key
from .adapter import search
from .common import BASE, document, read, encode, write, require
from .retained import load, OLD, PREVIOUS, identity, conditional_plan
from .runtime import verify


class Queries:
    def __init__(self, vector):
        self.vector = vector
        self.rows, self.packed = {}, {}
        self.calls = 0

    def preload(self, path, audit):
        for row in path["trace"]:
            key = state_key(row["state"])
            self.rows[key] = dict(key=key, state=row["state"], background=row["background"])
            self.packed[key] = read(audit / "masks", key + ".bin", 40000)

    def __call__(self, state):
        self.calls += 1
        result = self.vector(state)
        label = summary(result)
        key = state_key(state)
        row = dict(key=key, state=list(state), background=label)
        packed = np.packbits(result.mask, bitorder="little").tobytes()
        require(
            key not in self.rows or (self.rows[key] == row and self.packed[key] == packed),
            "query_identity_conflict",
        )
        self.rows[key], self.packed[key] = row, packed
        require(len(self.rows) <= 10000, "query_population")
        return label

    def finish(self, folder):
        folder.mkdir()
        for key, packed in self.packed.items():
            (folder / (key + ".bin")).write_bytes(packed)
        write(folder / "states.json", list(self.rows.values()))


def run(root, output, index, library):
    verify(root, library)
    plan = document(root, BASE / "PLAN.json")
    case, _, _, _, maxima = load(root, plan)
    selected = maxima[index]
    audit = root / BASE / "proof/audit_raw"
    path = next(p for p in document(audit, "paths.json") if identity(p) == identity(selected))
    prefix = path["trace"]
    old = document(root, OLD)
    settings = conditional_plan(
        document(root, PREVIOUS + "PLAN.json"),
        plan["remaining_attempts"][index],
        plan["original_wall_seconds"],
    )
    query = Queries(query_for(case))
    query.preload(path, audit)
    geometry = copy.deepcopy(case["geometry"])
    geometry["reset"] = prefix[-1]["state"]
    with (output / "events.jsonl").open("xb") as stream:

        def emit(kind, row):
            stream.write(encode(dict(kind=kind, **row)))
            require(stream.tell() < plan["max_output_bytes"] // 3 - 1000000, "events_budget")

        result = search(
            library,
            geometry,
            old,
            settings,
            query,
            emit,
            plan["seeds"][index],
            start_frame=prefix[-1]["frame"],
        )
    suffix = result.pop("trace")
    require(query.calls == result["queries"] + result["path_queries"], "recorded_query_count")
    combined = copy.deepcopy(prefix + suffix[1:])
    result.update(
        root_identity=list(identity(selected)),
        seed=plan["seeds"][index],
        start_frame=prefix[-1]["frame"],
        attempt_ceiling=settings["attempt_budget"],
        wall_ceiling=settings["per_run_seconds"],
        original_wall_seconds=plan["original_wall_seconds"],
        charged_wall_seconds=result["elapsed_seconds"] + plan["original_wall_seconds"],
        query_calls=query.calls,
        distinct_scalar_candidates=len(query.rows),
        source_prefix_states=len(prefix),
    )
    query.finish(output / "masks")
    write(output / "suffix.json", suffix)
    write(output / "trace.json", combined)
    write(output / "result.json", result)
    verify(root, library)
    print({k: result[k] for k in ["root_identity", "complete", "attempts", "stop"]}, flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--index", type=int, required=True, choices=range(3))
    p.add_argument("--library", type=Path, required=True)
    a = p.parse_args()
    run(a.root.resolve(), a.output.resolve(), a.index, a.library.resolve())
