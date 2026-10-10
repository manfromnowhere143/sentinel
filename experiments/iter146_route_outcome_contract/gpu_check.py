"""Independent verification of actual-device receipts plus full-horizon scalar replay."""

import hashlib
from pathlib import Path

from experiments.iter145_constrained_execution.independent import check, close
from .check import read, strict, verify


def verify_case(directory):
    directory = Path(directory)
    rows, summary = read(directory / "trace")
    report = verify(rows, summary)
    worker = strict((directory / "worker.json").read_bytes())
    check(worker["status"] == "completed" and worker["gpu_observed"] is True, "GPU worker")
    check(
        worker["summary"] == summary and worker["episode"] == summary["episode"], "worker binding"
    )
    check(
        worker["seed"] == 144 and worker["geos"] and worker["torch"] and worker["cuda_device"],
        "runtime binding",
    )
    check(worker["cleanup"]["status"] in ("removed", "absent"), "owned cleanup")
    deliveries = [r["value"] for r in rows if r["event"] == "delivery"]
    monitor = [r["raw"].encode() for r in rows if r["event"] == "monitor"]
    check(
        [strict(line) for line in (directory / "delivery145.jsonl").read_bytes().splitlines()]
        == deliveries,
        "client transport log",
    )
    check(
        (directory / "sentinel_iter48_decisions.jsonl").read_bytes().splitlines() == monitor,
        "monitor log",
    )
    actors = [
        r["value"] for r in rows if r["event"] == "actor" and r["value"]["event"] == "consume"
    ]
    outcomes = [r for r in rows if r["event"] == "outcome_observation"]
    renders, collisions = worker["render_events"], worker["collision_events"]
    check(
        len(renders) == 6 * (report["steps"] + 1) and len(collisions) == 2 * report["steps"],
        "device event inventory",
    )
    for tick in range(report["steps"] + 1):
        cameras = [r for r in renders if r["time"] == tick / 4]
        check(len(cameras) == 6, "camera tick count")
        for camera in cameras:
            check(
                camera["device"].startswith("cuda")
                and camera["shape"][0] == 3
                and min(camera["shape"][1:]) > 2
                and camera["elapsed_ns"] > 0,
                "CUDA render",
            )
            if tick:
                check(
                    set(camera["transforms"]) == set(actors[tick - 1]["transforms"]),
                    "render actors",
                )
                for name, matrix in camera["transforms"].items():
                    close(matrix, actors[tick - 1]["transforms"][name], 0)
        if tick:
            observed = [r for r in collisions if r["time"] == tick / 4]
            check(len(observed) == 2, "collision tick count")
            for a, b in zip(observed, outcomes[tick - 1]["collision_records"]):
                check(a["kind"] == b["kind"] and a["result"] == b["result"], "collision receipt")
                if a["kind"] == "foreground":
                    close(a["ego_box"], b["ego_box"], 0)
                    close(a["objects"], b["objects"], 0)
                else:
                    check(a["device"].startswith("cuda") and a["points"] > 0, "background device")
    report.update(
        gpu_observed=True,
        camera_calls=len(renders),
        events_sha256=hashlib.sha256((directory / "trace/events.jsonl").read_bytes()).hexdigest(),
        live_study_admitted=False,
    )
    return report
