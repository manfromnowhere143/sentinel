"""Exact retained reference fixtures, old optimization history and new solver results."""

import argparse
import hashlib
import json
from pathlib import Path
import platform
import time
import numpy as np
import scipy
from scipy.optimize import lsq_linear

from experiments.iter144_timed_trajectory.control import MatchedController
from .optimizer import ConstrainedController


def reference(record):
    return np.array([[b, a, np.pi / 2 - h, v, 0.0] for a, b, h, v in record["reference"]["states"]])


def run(root):
    oldpath = root / "experiments/iter144_timed_trajectory/proof/raw_qualification.json"
    raw = json.loads(oldpath.read_text())
    old = []
    new = []
    for index, row in enumerate(raw["solver"]):
        record = row["record"]
        state = np.array(record["initial_state"])
        ref = reference(record)
        baseline = MatchedController()
        start = time.perf_counter_ns()
        solutions = baseline.solver.solve(state, ref)
        old.append(
            dict(
                index=index,
                initial_state=state.tolist(),
                reference=ref.tolist(),
                history=[
                    dict(objective=float(s.tracking_cost), inputs=s.input_trajectory.tolist())
                    for s in solutions
                ],
                execution=baseline.solver.execution,
                elapsed_ns=time.perf_counter_ns() - start,
            )
        )
        new.append(
            dict(kind="replica", index=index, result=ConstrainedController().solve(state, ref))
        )
    for index, row in enumerate(raw["integration"]["rows"]):
        record = row["controller"]
        new.append(
            dict(
                kind="integration",
                index=index,
                result=ConstrainedController().solve(record["initial_state"], reference(record)),
            )
        )
    # Independent convex straight longitudinal least-squares comparator, box constraints.
    longitudinal = []
    n = 19
    dt = 0.25
    G = np.zeros((20, n))
    for i in range(1, 20):
        for j in range(i):
            G[i, j] = (i - j) * dt * dt
    for index in [0, 1, 4, 5]:
        r = raw["solver"][index]["record"]
        s = r["initial_state"]
        ref = reference(r)
        target = ref[:, 0] - s[0] - s[3] * np.arange(20) * dt
        fit = lsq_linear(
            np.vstack([G, np.eye(n)]),
            np.r_[target, np.zeros(n)],
            bounds=(-2, 2),
            tol=1e-12,
            max_iter=100,
            lsq_solver="exact",
        )
        longitudinal.append(
            dict(
                index=index,
                inputs=fit.x.tolist(),
                objective=float(2 * fit.cost),
                success=bool(fit.success),
                optimality=float(fit.optimality),
            )
        )
    return dict(
        schema="sentinel.iter145.optimizer_raw.v1",
        status="completed",
        input_sha256=hashlib.sha256(oldpath.read_bytes()).hexdigest(),
        environment=dict(
            python=platform.python_version(),
            numpy=np.__version__,
            scipy=scipy.__version__,
            platform=platform.platform(),
        ),
        baseline=old,
        candidate=new,
        longitudinal=longitudinal,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    try:
        result = run(a.root)
        code = 0
    except Exception as e:
        result = dict(status="invalid", error_type=type(e).__name__, error=str(e))
        code = 2
    with a.output.open("x") as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps(dict(status=result["status"], returncode=code)))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
