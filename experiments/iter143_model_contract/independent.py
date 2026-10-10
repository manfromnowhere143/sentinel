"""Stdlib replay of fixture measurements, using scalar and rational arithmetic."""

import argparse
from fractions import Fraction
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import stat

BASE = "experiments/iter143_model_contract"


def read_json(raw):
    def unique(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    def invalid(value):
        raise ValueError("nonfinite JSON")

    obj = json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)

    def finite(value):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("nonfinite value")
        if isinstance(value, dict):
            for v in value.values():
                finite(v)
        if isinstance(value, list):
            for v in value:
                finite(v)

    finite(obj)
    return obj


def read_bound(root, name):
    parts = Path(name)
    if parts.is_absolute() or ".." in parts.parts:
        raise ValueError("unsafe path")
    path = root
    for component in parts.parts:
        path /= component
        if path.is_symlink():
            raise ValueError("symlink")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as f:
        meta = os.fstat(f.fileno())
        if not stat.S_ISREG(meta.st_mode) or not 0 <= meta.st_size <= 16777216:
            raise ValueError("input type/size")
        result = f.read(16777217)
    if len(result) != meta.st_size:
        raise ValueError("changed input")
    return result


def check_inputs(root):
    raw = read_bound(root, BASE + "/INPUTS.json")
    binding = read_json(raw)
    result = {}
    records = list(binding["files"].items()) + [
        (r["path"], r) for r in binding["retrieved_sources"]
    ]
    for name, record in records:
        payload = read_bound(root, name)
        if (
            len(payload) != record["bytes"]
            or hashlib.sha256(payload).hexdigest() != record["sha256"]
        ):
            raise ValueError("input hash: " + name)
        result[name] = payload
    runtime = read_json(
        result["experiments/iter142_nominal_continuation_completion/proof/runtime_manifest.json"]
    )
    for r in binding["retrieved_sources"]:
        assert runtime["files"][r["prior_runtime_path"]] == r["sha256"]
    return result, hashlib.sha256(raw).hexdigest()


def close(a, b, tolerance=1e-9):
    if isinstance(b, list):
        if not isinstance(a, list) or len(a) != len(b):
            raise ValueError("shape mismatch")
        for actual, expected in zip(a, b):
            close(actual, expected, tolerance)
    elif type(a) not in (int, float) or not math.isfinite(a) or abs(a - b) > tolerance:
        raise ValueError(f"numerical disagreement: {a} versus {b}")


def transition(state, control, dt, environment):
    x, y, h, v, s = state
    a, w = control
    if not environment:
        a, w = max(-3.0, min(3.0, a)), max(-0.4, min(0.4, w))
    vn, sn = v + a * dt, s + w * dt
    if environment:
        vt, st = vn, sn
    else:
        vt, st = v, s
        sn = max(-math.pi / 3, min(math.pi / 3, sn))
    hn = h + vt * math.tan(st) * dt / 2.7
    if not environment:
        hn = (hn + math.pi) % (2 * math.pi) - math.pi
    return [x + vt * dt * math.cos(h), y + vt * dt * math.sin(h), hn, vn, sn]


def check_ego_row(row):
    state, action = row["state"], row["control"]
    if len(state) != 5 or len(action) != 2:
        raise ValueError("ego shape")
    one = transition(state, action, 0.25, True)
    two = transition(one, action, 0.25, True)
    short = transition(state, action, 0.25, False)
    long = transition(state, action, 0.5, False)
    for name, value in [
        ("environment_one", one),
        ("environment_two", two),
        ("controller_quarter", short),
        ("controller_half", long),
    ]:
        close(row[name], value)
    for name, dt, target in [("applied_quarter", 0.25, short), ("applied_half", 0.5, long)]:
        close(row[name], [max(-3, min(3, action[0])), (target[4] - state[4]) / dt])
    return dict(
        equal_interval_max_absolute=max(abs(a - b) for a, b in zip(one, short)),
        held_half_second_max_absolute=max(abs(a - b) for a, b in zip(two, long)),
        equal_interval_position_difference=math.hypot(one[0] - short[0], one[1] - short[1]),
    )


def check_actor(actor):
    if len(actor["spline"]) != 20 or len(actor["fallback"]) != 20 or len(actor["low_speed"]) != 19:
        raise ValueError("actor row count")
    for i, row in enumerate(actor["spline"]):
        t = float(Fraction(2 * i, 19))
        close(row, [4 * t, 0.0, 4.0, 0.0, 0.0, 0.0, t], 1e-6)
    for i, row in enumerate(actor["fallback"]):
        close(row, [float(Fraction(2 * i, 5)), 0.0, math.pi / 2, 4.0], 1e-6)
    for i, row in enumerate(actor["low_speed"], 1):
        t = float(Fraction(i, 10))
        close(row, [t, 0.0, 1.0, 0.0, 0.0, 0.0, t], 1e-6)
    if len(actor["dispatch"]) != 21 or len(actor["generations"]) != 3:
        raise ValueError("dispatch count")
    for i, row in enumerate(actor["dispatch"]):
        close(row["time"], i / 4)
        close(row["dt"], 0.1)
        assert row["requested_replan"] is (i % 10 == 0)
        assert row["generation_count"] == i // 10 + 1
        assert row["pointer_after"] == i % 10 + 2
        close(row["attacked_states"], [[0.0, float(j), 0.0, 4.0] for j in range(20)], 1e-6)
        close(row["actor_state"], [0.0, float(Fraction(8 * (i + 1), 19)), 0.0, 0.0, 4.0], 1e-6)
    for i, row in enumerate(actor["generations"]):
        close(row["horizon"], 2.0)
        close(row["state"], [0.0, float(Fraction(80 * i, 19)), 4.0, math.pi / 2], 1e-6)
        assert row["dyn_filter"] is True
    return dict(
        forecast_dt=0.25,
        forecast_last_time=4.75,
        spline_dt=float(Fraction(2, 19)),
        spline_last_time=2.0,
        low_speed_and_fallback_dt=0.1,
        low_speed_and_fallback_last_time=1.9,
        spline_max_time_mismatch=2.75,
        low_speed_and_fallback_max_time_mismatch=2.85,
        constant_speed_fixture_stored_speed=4.0,
        spline_execution_speed=float(Fraction(32, 19)),
        fallback_execution_speed=1.6,
        spline_speed_ratio=float(Fraction(8, 19)),
        fallback_speed_ratio=0.4,
        reset_consumes_first_future_sample=True,
        observed_probe_replan_times=[0.0, 2.5, 5.0],
        scope="synthetic source-slice execution; historical candidate type and physical actor speed are unobserved",
    )


def check_inventory(blobs, proposed, identity):
    assert proposed["schema"] == "sentinel.iter143.case_inventory.v1"
    assert proposed["input_manifest_sha256"] == identity
    rows = {}
    for path, raw in blobs.items():
        if not path.endswith(".sha256"):
            continue
        for line in raw.decode().splitlines():
            digest, name = line.split()
            assert len(digest) == 64 and all(c in "0123456789abcdef" for c in digest)
            fields = name.removesuffix(".yaml").split("-")
            assert name.endswith(".yaml") and len(fields) == 4 and fields[0] == "scene"
            _, scene, tier, variant = fields
            assert len(scene) == 4 and scene.isdigit() and len(variant) == 2 and variant.isdigit()
            assert tier in ["easy", "medium", "hard", "extreme"]
            if name in rows:
                assert rows[name]["sha256"] == digest
            rows[name] = dict(
                name=name,
                sha256=digest,
                scene=scene,
                tier=tier,
                variant=variant,
                exposure="historical_development",
                local_asset_availability="unobserved",
                role="closed_case_excluded" if scene == "0411" else "development_reserve",
            )
    scenes = sorted({r["scene"] for r in rows.values()} - {"0411"})
    pilot = scenes[:3]
    for row in rows.values():
        if row["scene"] in pilot:
            row["role"] = "proposed_pilot"
    assert proposed["rows"] == [rows[n] for n in sorted(rows)]
    assert proposed["pilot_scenes"] == pilot and proposed["held_out_unexposed_scenes"] == []
    return dict(
        scenarios=len(rows),
        base_scenes=len({r["scene"] for r in rows.values()}),
        eligible_development_scenes=len(scenes),
        pilot_scenes=pilot,
        pilot_scenarios=sum(r["role"] == "proposed_pilot" for r in rows.values()),
        excluded_scenarios=sum(r["role"] == "closed_case_excluded" for r in rows.values()),
        reserve_scenarios=sum(r["role"] == "development_reserve" for r in rows.values()),
        unexposed_holdout_scenes=0,
        current_asset_availability="unobserved",
    )


def run(root, raw, proposed):
    blobs, identity = check_inputs(root)
    assert raw["schema"] == "sentinel.iter143.raw.v1" and raw["input_manifest_sha256"] == identity
    c = raw["constants"]
    assert c == dict(
        environment_dt=0.25,
        controller_dt=0.5,
        wheelbase=2.7,
        declared_acc=[-2.0, 2.0],
        declared_steering_rate=[-math.pi / 12, math.pi / 12],
        controller_acc=3.0,
        controller_steering_rate=0.4,
    )
    cases = list(
        itertools.product(
            [0.0, 4.0], [0.0, 0.3], [0.0, 0.2], [[0.0, 0.0], [2.0, 0.2], [-2.0, -0.2], [3.0, 0.4]]
        )
    )
    assert len(raw["ego"]) == len(cases) == 32
    checked = []
    for i, (row, (v, h, s, action)) in enumerate(zip(raw["ego"], cases)):
        assert row["id"] == i and row["state"] == [0.0, 0.0, h, v, s] and row["control"] == action
        checked.append(dict(id=i, **check_ego_row(row)))
    bounds = [
        [2.0, 0.0],
        [-2.0, 0.0],
        [0.0, math.pi / 12],
        [0.0, -math.pi / 12],
        [3.0, 0.0],
        [-3.0, 0.0],
        [0.0, 0.4],
        [0.0, -0.4],
    ]
    assert len(raw["limits"]) == len(bounds)
    for row, control in zip(raw["limits"], bounds):
        assert row["control"] == control and row["before"] == [0.0, 0.0, 0.0, 4.0, 0.0]
        close(row["after"], transition(row["before"], control, 0.25, True))
    actor = check_actor(raw["actor"])
    inventory = check_inventory(blobs, proposed, identity)
    contradictions = dict(
        equal_interval_transition=any(x["equal_interval_max_absolute"] > 1e-9 for x in checked),
        same_time_actor_comparison=actor["spline_max_time_mismatch"] > 1e-6,
        declared_control_enforcement=any(
            abs(r["control"][0]) > 2 or abs(r["control"][1]) > math.pi / 12 for r in raw["limits"]
        ),
    )
    mismatch = any(contradictions.values())
    return dict(
        status="contradicted" if mismatch else "supported",
        verdict="COMMON_MODEL_CONTRACT_REJECTED"
        if mismatch
        else "SOURCE_CONTRACT_FIXTURES_MATCHED",
        independent_validation="passed",
        input_manifest_sha256=identity,
        contradictions=contradictions,
        ego_cases=checked,
        ego_mismatch_counts=dict(
            equal_interval=sum(r["equal_interval_max_absolute"] > 1e-9 for r in checked),
            held_half_second=sum(r["held_half_second_max_absolute"] > 1e-9 for r in checked),
        ),
        outside_declared_limit_integrated_unchanged=4,
        actor=actor,
        inventory=inventory,
        physical_qualification="unestablished",
        live_episodes=0,
        cloud_access=False,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--inventory", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    try:
        raw = a.raw.read_bytes()
        inventory = a.inventory.read_bytes()
        report = run(a.root, read_json(raw), read_json(inventory))
        report.update(
            raw_sha256=hashlib.sha256(raw).hexdigest(),
            case_inventory_sha256=hashlib.sha256(inventory).hexdigest(),
        )
        code = 0
    except (ValueError, KeyError, TypeError, AssertionError, OSError) as exc:
        report = dict(
            status="invalid",
            verdict="MODEL_CONTRACT_INVALID",
            error_type=type(exc).__name__,
            error=str(exc),
        )
        code = 2
    with a.output.open("x") as f:
        json.dump(report, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    print(
        json.dumps(dict(status=report["status"], verdict=report["verdict"], output=str(a.output)))
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
