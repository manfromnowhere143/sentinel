"""Scalar reverse-mode replay and KKT verification, independent of candidate code."""

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path


def check(ok, why):
    if not ok:
        raise ValueError(why)


def close(a, b, tol=1e-8):
    if isinstance(b, (list, tuple)):
        check(isinstance(a, (list, tuple)) and len(a) == len(b), "shape")
        for x, y in zip(a, b):
            close(x, y, tol)
    else:
        check(
            type(a) in (int, float) and math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tol,
            "numeric replay",
        )


def motion(initial, inputs):
    states = [list(initial)]
    for acc, rate in inputs:
        x, y, h, v, d = states[-1]
        v += acc / 4
        d += rate / 4
        states.append(
            [x + v * math.cos(h) / 4, y + v * math.sin(h) / 4, h + v * math.tan(d) / 10.8, v, d]
        )
    return states


def cost_gradient(initial, inputs, ref):
    states = motion(initial, inputs)
    errors = []
    value = 0.0
    for state, target in zip(states, ref):
        e = [x - y for x, y in zip(state, target)]
        e[2] = math.atan2(math.sin(e[2]), math.cos(e[2]))
        errors.append(e)
        value += e[0] ** 2 + e[1] ** 2 + 10 * e[2] ** 2
    value += sum(a * a + 10 * r * r for a, r in inputs)
    gradients = [None] * len(inputs)
    lam = [2 * errors[-1][0], 2 * errors[-1][1], 20 * errors[-1][2], 0.0, 0.0]
    for k in reversed(range(len(inputs))):
        h = states[k][2]
        v, d = states[k + 1][3:]
        c, s = math.cos(h), math.sin(h)
        tan = math.tan(d)
        sec = 1 / math.cos(d) ** 2
        a, r = inputs[k]
        gradients[k] = [
            2 * a + lam[0] * c / 16 + lam[1] * s / 16 + lam[2] * tan / 43.2 + lam[3] / 4,
            20 * r + lam[2] * v * sec / 43.2 + lam[4] / 4,
        ]
        lam = [
            2 * errors[k][0] + lam[0],
            2 * errors[k][1] + lam[1],
            20 * errors[k][2] - lam[0] * v * s / 4 + lam[1] * v * c / 4 + lam[2],
            lam[0] * c / 4 + lam[1] * s / 4 + lam[2] * tan / 10.8 + lam[3],
            lam[2] * v * sec / 10.8 + lam[4],
        ]
    return value, list(itertools.chain.from_iterable(gradients)), states


def certificate(record):
    inputs = record["inputs"]
    n = len(inputs)
    u = list(itertools.chain.from_iterable(inputs))
    d0 = record["initial_state"][4]
    value, g, states = cost_gradient(record["initial_state"], inputs, record["reference"])
    close(record["objective"], value)
    close(record["states"], states)
    cert = record["certificate"]
    close(cert["gradient"], g)
    limits = [2.0, math.pi / 12] * n
    rows = []
    bounds = []
    for sign in (1.0, -1.0):
        for j in range(2 * n):
            row = [0.0] * (2 * n)
            row[j] = sign
            rows.append(row)
            bounds.append(limits[j])
    for sign in (1.0, -1.0):
        for k in range(n):
            rows.append([sign / 4 if j % 2 == 1 and j // 2 <= k else 0.0 for j in range(2 * n)])
            bounds.append(math.pi / 3 - sign * d0)
    slack = [b - sum(x * y for x, y in zip(row, u)) for row, b in zip(rows, bounds)]
    close(cert["slack"], slack)
    multipliers = cert["multipliers"]
    check(len(multipliers) == len(rows), "multiplier length")
    check(
        all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in multipliers),
        "dual feasibility",
    )
    stationarity = max(
        abs(g[j] + sum(row[j] * v for row, v in zip(rows, multipliers))) for j in range(2 * n)
    )
    complement = max(abs(s * v) for s, v in zip(slack, multipliers))
    violation = max(0.0, -min(slack))
    close(cert["stationarity_inf"], stationarity)
    close(cert["complementarity_inf"], complement)
    close(cert["max_violation"], violation)
    certified = stationarity <= 1e-6 and complement <= 1e-7 and violation <= 1e-9
    check(cert["admitted"] == certified, "false certificate")
    check(record["admitted"] == (certified and record["library_success"]), "false admission")
    check(1 <= record["iterations"] <= 100, "iteration cap")
    if record["admitted"]:
        close(record["applied"], inputs[0])
        check(record["stop_reason"] == "kkt_converged", "wrong stop")
    else:
        check(record["applied"] is None, "uncertified actuation")
    check(0 < record["solver_ns"] <= record["complete_call_ns"], "timing order")
    for h in record["history"]:
        close(
            h["objective"],
            cost_gradient(record["initial_state"], h["inputs"], record["reference"])[0],
        )
    if "refinement" in record:
        check(
            record["iterations"] == record["slsqp_iterations"] + len(record["refinement"]),
            "combined iteration count",
        )
        check(len(record["refinement"]) <= 8, "refinement bound")
        previous = record["history"][-1]["inputs"] if record["history"] else record["warm_inputs"]
        for h in record["refinement"]:
            before, g_before, _ = cost_gradient(
                record["initial_state"], previous, record["reference"]
            )
            after = cost_gradient(record["initial_state"], h["inputs"], record["reference"])[0]
            close(h["objective"], after)
            close(h["previous_objective"], before)
            check(0 < h["alpha"] <= 1 and 0 <= h["backtracks"] < 20, "refinement line search")
            step = [y - x for a, b in zip(previous, h["inputs"]) for x, y in zip(a, b)]
            slope = sum(g * d / h["alpha"] for g, d in zip(g_before, step))
            close(h["slope"], slope)
            check(
                slope < 0
                and after
                <= before + 1e-4 * h["alpha"] * slope + 2e-14 * max(1.0, abs(before)) + 1e-14,
                "refinement descent",
            )
            previous = h["inputs"]
        close(previous, record["inputs"])
    close(
        record["warm_objective"],
        cost_gradient(record["initial_state"], record["warm_inputs"], record["reference"])[0],
    )
    check(value <= record["warm_objective"] + 1e-8 or not record["admitted"], "objective increase")
    return dict(stationarity=stationarity, complementarity=complement, violation=violation)


def validate(raw, old):
    check(
        raw["status"] == "completed" and raw["schema"] == "sentinel.iter145.optimizer_raw.v1",
        "raw schema",
    )
    check(len(raw["baseline"]) == 8 and len(raw["candidate"]) == 28, "case count")
    references = []
    for row in old["solver"]:
        references.append(row["record"])
    references += [r["controller"] for r in old["integration"]["rows"]]
    metrics = []
    for i, (row, prior) in enumerate(zip(raw["candidate"], references)):
        check(
            row["kind"] == ("replica" if i < 8 else "integration")
            and row["index"] == (i if i < 8 else i - 8),
            "case identity",
        )
        expected_ref = [
            [b, a, math.pi / 2 - h, v, 0.0] for a, b, h, v in prior["reference"]["states"]
        ]
        r = row["result"]
        close(r["initial_state"], prior["initial_state"], 0)
        close(r["reference"], expected_ref, 0)
        metrics.append(certificate(r))
    for i in range(0, 8, 2):
        a, b = [raw["candidate"][j]["result"] for j in (i, i + 1)]
        for key in ["inputs", "states", "objective"]:
            close(a[key], b[key], 1e-9)
        check(
            a["stop_reason"] == b["stop_reason"] and a["iterations"] == b["iterations"],
            "replica stop",
        )
    baselines = []
    for index, (row, prior) in enumerate(zip(raw["baseline"], old["solver"])):
        check(row["index"] == index, "baseline identity")
        close(row["history"][-1]["inputs"], prior["record"]["inputs"], 1e-10)
        check(
            row["execution"]["stop_reason"] == prior["record"]["stop_reason"],
            "baseline stop changed",
        )
        values = []
        for h in row["history"]:
            value = cost_gradient(row["initial_state"], h["inputs"], row["reference"])[0]
            close(value, h["objective"])
            values.append(value)
        increases = [b - a for a, b in zip(values, values[1:]) if b > a + 1e-10]
        baselines.append(
            dict(
                index=index,
                stop_reason=row["execution"]["stop_reason"],
                objective_increases=len(increases),
                largest_objective_increase=max(increases, default=0.0),
                final_objective=values[-1],
                candidate_objective=raw["candidate"][index]["result"]["objective"],
            )
        )
    check([r["index"] for r in raw["longitudinal"]] == [0, 1, 4, 5], "convex subproblem inventory")
    for row in raw["longitudinal"]:
        r = raw["candidate"][row["index"]]["result"]
        check(row["success"], "convex comparator failure")
        close(r["objective"], row["objective"], 1e-7)
        close([u[0] for u in r["inputs"]], row["inputs"], 1e-5)
    good = sum(r["result"]["admitted"] for r in raw["candidate"])
    return dict(
        status="supported" if good == 28 else "failed",
        verdict="CONSTRAINED_CONTROLLER_QUALIFIED"
        if good == 28
        else "CONSTRAINED_CONTROLLER_REJECTED",
        independent_validation="passed",
        admitted=good,
        total=28,
        replica_pairs=4,
        baseline=baselines,
        max_stationarity=max(r["stationarity"] for r in metrics),
        max_violation=max(r["violation"] for r in metrics),
        max_complementarity=max(r["complementarity"] for r in metrics),
        iterations=[r["result"]["iterations"] for r in raw["candidate"]],
        complete_call_ms=[r["result"]["complete_call_ns"] / 1e6 for r in raw["candidate"]],
        scope="registered local constrained stationarity and replay; no global nonlinear optimum or vehicle deadline",
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    try:
        raw = json.loads(a.raw.read_text())
        data = (
            a.root / "experiments/iter144_timed_trajectory/proof/raw_qualification.json"
        ).read_bytes()
        check(hashlib.sha256(data).hexdigest() == raw["input_sha256"], "prior raw identity")
        result = validate(raw, json.loads(data))
        code = 0 if result["status"] == "supported" else 1
    except (KeyError, ValueError, IndexError, TypeError) as e:
        result = dict(status="invalid", error=str(e))
        code = 2
    with a.output.open("x") as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps(result))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
