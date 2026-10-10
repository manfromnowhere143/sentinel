"""Independent execution, monitor and qualification-slot binding checks."""

from pathlib import Path
from experiments.iter146_route_outcome_contract.gpu_check import verify_case as prior_verify
from experiments.iter146_route_outcome_contract.check import strict
from experiments.iter145_constrained_execution.independent import check, close
from .monitor import replay
from .coordinator import read


def verify_case(directory, slot, purpose):
    directory = Path(directory)
    report = prior_verify(directory)
    worker = read(directory / "worker.json")
    check(worker["slot"] == slot and worker["purpose"] == purpose, "slot identity")
    check(report["episode"] == slot["id"] and report["arm"] == slot["arm"], "episode slot")
    check(worker["summary"]["schema"] == "sentinel.iter146.summary.v2", "timing version")
    check(worker["summary"]["max_actions"] == slot["max_actions"], "horizon binding")
    check(
        worker["summary"]["stop_reason"] in ("action_cap", "source_terminal"), "qualification stop"
    )
    monitors = [
        strict(line)
        for line in (directory / "sentinel_iter48_decisions.jsonl").read_bytes().splitlines()
    ]
    monitor_report = replay(monitors)
    expected = {
        "scene-0013-easy-00.yaml": [],
        "scene-0013-extreme-00.yaml": ["AttackPlanner"],
        "scene-0013-hard-00.yaml": ["IDM"],
        "scene-0013-medium-00.yaml": ["ConstantPlanner"],
    }
    if purpose == "qualification":
        check(sorted(worker["actor_types"].values()) == expected[slot["scenario"]], "actor types")
    if slot["probe"] == "monitor_hold":
        diagnostic = [
            strict(line)
            for line in (directory / "diagnostic_inputs.jsonl").read_bytes().splitlines()
        ]
        check(len(diagnostic) == report["steps"] == 401, "hold full horizon")
        check(
            monitor_report["firings"] == monitor_report["braking_frames"] == 401,
            "hold monitor coverage",
        )
        for frame, (data, monitor) in enumerate(zip(diagnostic, monitors)):
            check(
                data["kind"] == "injected_detector_input_not_natural_perception"
                and data["frame"] == frame
                and data["time"] == frame / 4
                and data["score"] == 1
                and data["track_id"] == 147,
                "diagnostic record",
            )
            check(
                len(monitor["objs"]) == 1 and monitor["objs"][0]["id"] == 147,
                "diagnostic accepted object",
            )
            close(data["center"], monitor["traj"][0] + [0.0], 0)
            close(monitor["objs"][0]["bev"], data["center"][:2], 1e-6)
        check(
            worker["summary"]["stop_reason"] == "action_cap" and report["outcome"]["censored"],
            "hold censoring",
        )
    else:
        check(not (directory / "diagnostic_inputs.jsonl").exists(), "unexpected detector injection")
    report.update(
        monitor=monitor_report,
        actor_types=worker["actor_types"],
        purpose=purpose,
        scope="Bounded source execution; injected detector input explicitly segregated; physical validity unestablished.",
    )
    return report
