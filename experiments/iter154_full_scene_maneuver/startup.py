"""A rejected capacity request is distinct from an owned VM start or a scientific failure."""

from experiments.iter150_cloud_observation.cloud import VM_ID


def denied_start(before, returncode, stderr, observations):
    if (
        type(returncode) is not int
        or returncode == 0
        or "ZONE_RESOURCE_POOL_EXHAUSTED_WITH_DETAILS" not in stderr
        or str(before.get("id")) != VM_ID
        or before.get("status") != "TERMINATED"
        or not before.get("lastStartTimestamp")
        or type(observations) is not list
        or len(observations) < 2
    ):
        raise ValueError("denied_start_not_established")
    for observed in observations:
        if (
            str(observed.get("id")) != VM_ID
            or observed.get("status") != "TERMINATED"
            or observed.get("lastStartTimestamp") != before["lastStartTimestamp"]
            or observed.get("machineType") != before.get("machineType")
            or observed.get("guestAccelerators") != before.get("guestAccelerators")
        ):
            raise ValueError("possible_start_or_identity_change")
    return dict(
        status="supported",
        lifecycle="start_denied_capacity",
        new_start_observed=False,
        scientific_slots_initialized=0,
        instance=observations[-1],
        scope="Provider explicitly rejected the sole start request; two observations remain TERMINATED at the prior start. No new owned start or shutdown is claimed.",
    )


def retry_budget(repository, attempt):
    import datetime
    import math
    from pathlib import Path
    import subprocess
    import time
    from .records import read
    from experiments.iter148_recovery_study.admission import committed_file

    if type(attempt) is not int or attempt != 1:
        raise ValueError("capacity_attempt")
    repository = Path(repository).resolve()
    prior = repository / "experiments/iter154_full_scene_maneuver/proof/block_000"
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository, text=True).strip()
    names = (
        "commands/initial_identity.stdout",
        "commands/start.json",
        "commands/start.stderr",
        "commands/owned_identity.stdout",
        "commands/closure_reconcile.stdout",
        "closure.json",
        "denied_start_closure.json",
        "budget.json",
        "result.json",
        "source_packet.json",
    )
    for name in names:
        committed_file(repository, head, prior / name)
    request = read(prior / "commands/start.json")
    denied_start(
        read(prior / "commands/initial_identity.stdout"),
        request["returncode"],
        (prior / "commands/start.stderr").read_text(),
        [
            read(prior / "commands/owned_identity.stdout"),
            read(prior / "commands/closure_reconcile.stdout"),
        ],
    )
    closure, result = read(prior / "denied_start_closure.json"), read(prior / "result.json")
    if (
        closure.get("new_start_observed") is not False
        or closure.get("watchdog_process_observed_absent") is not True
        or result.get("status") != "failed"
        or result.get("pairs") != []
        or (prior / "owned.json").exists()
        or (prior / "deployment.json").exists()
        or read(prior / "source_packet.json")["commit"]
        != "ad063849c502d21967d3bc6b8590057f797e1a13"
    ):
        raise ValueError("prior_attempt_not_eligible")
    elapsed = result["elapsed_seconds"]
    if type(elapsed) not in (float, int) or not math.isfinite(elapsed) or not 0 < elapsed < 3600:
        raise ValueError("prior_envelope_invalid")
    if time.time() - datetime.datetime.fromisoformat(request["start_utc"]).timestamp() < 120:
        raise ValueError("capacity_backoff")
    return 3600 - math.ceil(elapsed)
