"""Constructed forensic probe of the unchanged Iter15 helper, not a driving trial.

Extract only the literal HELPERS string; never execute the server patch installer.
All logs go to a temporary directory. No provider, simulator or source is changed.
"""

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import platform
import tempfile
from types import SimpleNamespace

import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    relative = "experiments/iter15_latch_release/server_patch_union_release.py"
    raw = (args.repo / relative).read_bytes()
    tree = ast.parse(raw)
    helpers = [
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "HELPERS" for t in node.targets)
    ]
    assert len(helpers) == 1
    nominal = [[1.0, 0.0], [2.0, 0.0]]
    cases = {
        "all_fields_missing": {},
        "objects_missing": {"object_scores": [1.0], "object_ids": [1]},
        "objects_null": {"objects_in_bev": None, "object_scores": [1.0]},
        "valid_empty": {"objects_in_bev": [], "object_scores": [], "object_ids": []},
        "present_threat": {
            "objects_in_bev": [[1.0, 0.0]],
            "object_scores": [1.0],
            "object_ids": [1],
        },
        "decoder_exception": "constructed_exception",
    }
    results = {}
    settings = {
        "SENTINEL_ENABLED": "1",
        "SENTINEL_CPA_MARGIN": "1.5",
        "SENTINEL_TTC": "2.5",
        "SENTINEL_MIN_CLOSING": "3.0",
        "SENTINEL_MAXGAP": "30.0",
        "SENTINEL_MIN_SCORE": "0.3",
        "SENTINEL_RELEASE_K": "4",
    }
    os.environ.update(settings)
    with tempfile.TemporaryDirectory(prefix="sentinel-forensic-inputs-") as temp:
        for name, value in cases.items():
            log = Path(temp) / (name + ".jsonl")
            os.environ["SENTINEL_LOG"] = str(log)
            namespace = {}
            exec(compile(helpers[0], relative + ":HELPERS", "exec"), namespace)
            namespace["_sentinel_run"].update(braking=True, clear=0)

            def to_json(value=value):
                if value == "constructed_exception":
                    raise ValueError("constructed auxiliary decoder failure")
                return value

            out = SimpleNamespace(
                trajectory=np.array(nominal), aux_outputs=SimpleNamespace(to_json=to_json)
            )
            trace = []
            for frame in range(1, 5):
                data = SimpleNamespace(ego2world=np.eye(4), timestamp=frame * 500000)
                returned = namespace["_sentinel_intervene"](out, data)
                trace.append(
                    {
                        "frame": frame,
                        "returned_nominal": returned == nominal,
                        "returned_brake": returned == [[0.0, 0.0], [0.0, 0.0]],
                        "braking_latch": namespace["_sentinel_run"]["braking"],
                        "clear_count": namespace["_sentinel_run"]["clear"],
                    }
                )
            results[name] = {
                "input": value,
                "trace": trace,
                "log": [json.loads(s) for s in log.read_text().splitlines()],
            }
    for name in ("all_fields_missing", "objects_missing", "objects_null", "valid_empty"):
        assert [r["returned_nominal"] for r in results[name]["trace"]] == [
            False,
            False,
            False,
            True,
        ]
    assert all(r["returned_brake"] for r in results["present_threat"]["trace"])
    assert all(
        r["returned_nominal"] and r["braking_latch"] for r in results["decoder_exception"]["trace"]
    )
    print(
        json.dumps(
            {
                "status": "supported",
                "scope": "constructed legacy-helper behavior only",
                "source": relative,
                "source_sha256": hashlib.sha256(raw).hexdigest(),
                "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "python": platform.python_version(),
                "numpy": np.__version__,
                "settings": settings,
                "cases": results,
                "limits": [
                    "No claim about occurrence or causal effect in historical driving episodes.",
                    "No new integrated run, deployment, physical test or Iter191 change.",
                    "Missing source data and valid empty observations follow the same release path.",
                    "Decoder errors return the nominal plan even while the braking latch is set.",
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
