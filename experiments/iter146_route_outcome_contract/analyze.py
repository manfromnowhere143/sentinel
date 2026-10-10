"""Independent replay and replica checks for the explicitly synthetic qualification."""

import argparse
import json
from pathlib import Path

from .check import read, strict, verify
from .compare import replicas


def analyze(root):
    population = strict((root / "population.json").read_bytes())
    if population["status"] != "completed" or len(population["cases"]) != 18:
        raise ValueError("population incomplete")
    reports, retained = {}, []
    for case in population["cases"]:
        report = verify(*read(root / case["name"]))
        reports[case["name"]] = report
        retained.append({k: v for k, v in report.items() if k not in ("scientific", "route")})
    for kind in ("completion", "censor"):
        for arm in ("nominal", "monitor", "brake_t0", "brake_t2_5"):
            replicas([reports[f"{kind}__{arm}__{r}"] for r in (1, 2)])
    return dict(
        status="supported",
        cases=retained,
        replica_pairs=8,
        steps=sum(r["steps"] for r in retained),
        maximum_stationarity=max(r["max_stationarity"] for r in retained),
        gpu_observed=False,
        live_study_admitted=False,
        scope=population["scope"],
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = analyze(a.raw)
    with a.output.open("x") as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}))
