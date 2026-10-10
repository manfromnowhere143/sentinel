"""Admission for measured asset/resource evidence. No provider or execution side effects."""

import hashlib
import math
import os
from pathlib import Path
import stat
from experiments.iter144_timed_trajectory.trajectory import ContractError

HOST = dict(id="3834622546652649531", name="sentinel-gpu", project="sunlit-unison-487018-b0",
            zone="us-west1-a", machine_type="g2-standard-8", accelerator="nvidia-l4", accelerator_count=1)
IMAGE = "sha256:2fc5cd574b7510c813fecee64d5568fddec8255a4b638dbca758b67696cb1d14"


def number(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ContractError("missing_or_nonfinite_resource")
    return float(value)


def file_identity(path, *, max_bytes=16*1024**3, include_bytes=False):
    """No-follow each path component and final fd; detect replacement while hashing."""
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise ContractError("asset_path")
    descriptors = []
    try:
        fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY); descriptors.append(fd)
        for part in path.parts[1:-1]:
            fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            descriptors.append(fd)
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        descriptors.append(fd); before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= max_bytes:
            raise ContractError("asset_type_or_size")
        digest = hashlib.sha256(); total = 0; chunks = []
        while True:
            block = os.read(fd, min(1024**2, max_bytes+1-total))
            if not block:
                break
            total += len(block); digest.update(block)
            if include_bytes:
                chunks.append(block)
            if total > max_bytes:
                raise ContractError("asset_size_changed")
        after = os.fstat(fd)
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
        if total != before.st_size or any(getattr(before,k) != getattr(after,k) for k in fields):
            raise ContractError("asset_changed_while_reading")
        result = dict(sha256=digest.hexdigest(), bytes=total)
        if include_bytes:
            result["data"] = b"".join(chunks)
        return result
    finally:
        for fd in reversed(descriptors):
            os.close(fd)


def asset_gate(inventory, assets):
    expected = {r["name"]: r["sha256"] for r in inventory["rows"] if r["role"] == "proposed_pilot"}
    if len(expected) != 14 or set(assets["scenarios"]) != set(expected):
        raise ContractError("asset_population")
    if assets.get("observation_kind") != "host_readback" or not assets.get("files"):
        raise ContractError("assets_unobserved")
    for name, row in assets["scenarios"].items():
        if row["sha256"] != expected[name] or not row.get("dependencies"):
            raise ContractError("scenario_identity_or_dependencies")
        if not row.get("controller_types") or any(k not in ("AttackPlanner", "ConstantPlanner", "IDM", "UnicyclePlanner") for k in row["controller_types"]):
            raise ContractError("scenario_actor_types")
        if row.get("unresolved_dependencies") != []:
            raise ContractError("unresolved_asset_dependencies")
        for path in row["dependencies"]:
            record = assets["files"].get(path)
            if (not isinstance(record, dict) or record.get("status") != "observed"
                    or number(record.get("bytes")) <= 0 or len(record.get("sha256", "")) != 64):
                raise ContractError("asset_missing_or_invalid")
    required = {"scene", "ground", "scene_config", "actor_model", "actor_dimensions", "planner_checkpoint", "runtime_source", "camera_config", "kinematic_config"}
    if not required <= set(assets.get("roles", [])) or assets.get("image_id") != IMAGE:
        raise ContractError("asset_role_or_image_identity")
    return True


def resource_gate(observation, envelope, *, now):
    if observation.get("observation_kind") != "host_readback" or any(observation.get(k) != v for k,v in HOST.items()):
        raise ContractError("resource_host_identity")
    if observation.get("state") != "RUNNING" or observation.get("containers") != [] or observation.get("gpu_processes") != []:
        raise ContractError("host_not_available")
    age = number(now) - number(observation.get("observed_epoch"))
    if not 0 <= age <= 300:
        raise ContractError("stale_resource_observation")
    local, remote = [number(observation.get(k)) for k in ("local_free_gib", "remote_free_gib")]
    output, seconds, rate, cap = [number(envelope.get(k)) for k in ("max_output_gib", "max_seconds", "hourly_upper_usd", "max_cost_usd")]
    if output <= 0 or seconds <= 0 or rate <= 0 or cap <= 0 or local < 15 or remote < 100 or remote-output < 25:
        raise ContractError("resource_capacity")
    if seconds*rate/3600 > cap:
        raise ContractError("resource_cost_cap")
    if (envelope.get("capacity_attempts") != 1 or envelope.get("smoke_attempts") != 1
            or not isinstance(envelope.get("source_commit"), str) or len(envelope["source_commit"]) != 40
            or envelope.get("cleanup_owner") != "sentinel.iter145"
            or not isinstance(envelope.get("price_source_sha256"), str) or len(envelope["price_source_sha256"]) != 64):
        raise ContractError("execution_binding_incomplete")
    deadline = number(observation.get("owned_shutdown_epoch"))
    if observation.get("shutdown_owner") != "sentinel.iter145" or not now+seconds+120 <= deadline <= now+seconds+300:
        raise ContractError("shutdown_deadline_or_owner")
    return True


def study_projection(smoke, *, slots=112, actions=401):
    """Explicit conservative proposal from measured smoke, never live admission."""
    if smoke.get("status") != "supported" or smoke.get("gpu_observed") is not True:
        raise ContractError("gpu_measurements_unavailable")
    initialization = number(smoke.get("initialization_seconds"))
    steps = [number(x) for x in smoke["step_seconds"]]
    sizes = [number(x) for x in smoke["step_output_bytes"]]
    if initialization <= 0 or not steps or min(steps) <= 0 or len(steps) != len(sizes) or min(sizes) < 0:
        raise ContractError("incomplete_resource_measurements")
    return dict(status="proposed", slots=slots, actions=actions, multiplier=2,
                seconds=2*slots*(initialization+actions*max(steps)),
                output_gib=2*slots*(number(smoke["initial_output_bytes"])+actions*max(sizes))/2**30,
                limitation="Engineering projection from bounded smoke; full-study variation remains unobserved.")
