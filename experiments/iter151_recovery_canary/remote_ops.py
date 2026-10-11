"""Fresh runtime preparation and exclusive launch within the registered owned root."""

import os
from pathlib import Path
import shutil
import subprocess
import time

from .admission import BASE, PLAN, basis, identity, remaining, validate_plan
from .records import read, record
from .ownership import check_service
from experiments.iter150_cloud_observation.native import file

CONTROL = Path("/datasets/nuscenes-full/hugsim/iter151_canary_20261011")
HUGSIM = Path("/opt/sentinel-stack/HUGSIM")
PYTHON = str(HUGSIM / ".pixi/envs/default/bin/python")


def environment(control):
    return dict(
        os.environ,
        PYTHONPATH=str(control / "packet") + ":" + str(HUGSIM),
        OPENBLAS_NUM_THREADS="1",
        OMP_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
    )


def idle():
    rows = {}
    for name, argv in (
        ("containers", ["docker", "ps", "-q"]),
        ("gpu_processes", ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"]),
    ):
        q = subprocess.run(argv, capture_output=True, text=True, timeout=15)
        rows[name] = dict(returncode=q.returncode, stdout=q.stdout, stderr=q.stderr)
        if q.returncode or q.stdout.strip():
            raise ValueError("occupied_host:" + name)
    return rows


def prepare(control, source):
    """Executed with the existing simulator Python after byte-verified packet extraction."""
    from experiments.iter145_constrained_execution.resources import file_identity
    from experiments.iter145_constrained_execution.gpu_batch import check_files
    from experiments.iter147_full_horizon_execution.client import instrument

    control = Path(control)
    if control != CONTROL:
        raise ValueError("control_root")
    idle()
    if shutil.disk_usage(control).free < 100 * 1024**3:
        raise ValueError("remote_capacity")
    packet = control / "packet"
    qualification = basis(packet)
    assets = read(control / "asset_inventory.json")
    if assets["status"] != "supported":
        raise ValueError("asset_basis")
    files, aliases = {}, {}
    for name, row in assets["files"].items():
        if row["role"] in ("actor_model", "actor_dimensions"):
            aliases[name] = row
            name = row["physical_path"]
        files[name] = dict(sha256=row["sha256"], bytes=row["bytes"])
    shutil.copytree("/root/.unified_data_cache", control / "map_cache")
    for name, row in list(files.items()):
        if name.startswith("/root/.unified_data_cache/"):
            copied = control / "map_cache" / Path(name).relative_to("/root/.unified_data_cache")
            if file_identity(copied) != row:
                raise ValueError("map_copy")
            files[str(copied)] = row
    with (control / "e2e147.py").open("xb") as stream:
        stream.write(
            instrument(
                (
                    packet
                    / "experiments/iter145_constrained_execution/source/released_client.py.txt"
                ).read_bytes()
            )
        )
    with (control / "nuscenes_base.yaml").open("x") as stream:
        stream.write(
            "realcar_path: /datasets/nuscenes-full/hugsim/3DRealCar\nmodel_base: /datasets/nuscenes-full/hugsim/extracted/scenes/nuscenes\nHD_map:\n  path: /datasets/nuscenes-full\n  version: nusc_trainval\n"
        )
    document = validate_plan(read(packet / BASE / "STUDY_PLAN.json"))
    record(control / "plan.json", document)
    for path in packet.rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            files[str(path)] = file_identity(path, allow_empty=True)
    for name in (
        "plan.json",
        "e2e147.py",
        "nuscenes_base.yaml",
        "asset_inventory.json",
        "map_inventory.json",
    ):
        files[str(control / name)] = file_identity(control / name)
    manifest = dict(
        source_commit=source,
        files=files,
        actor_aliases=aliases,
        actor_files=read(packet / "experiments/iter145_constrained_execution/ACTOR_FILES.json"),
        cases=sorted({s["scenario"] for s in document["slots"]}),
    )
    record(control / "execution_manifest.json", manifest)
    check_files(manifest)
    # Imports exercise the already-installed environment; this does not create a simulator.
    q = subprocess.run(
        [
            PYTHON,
            "-c",
            "from hugsim_env.envs.hug_sim import HUGSimEnv; from experiments.iter151_recovery_canary.worker import dispatch; print('ENVIRONMENT_IMPORT_PASSED')",
        ],
        cwd=HUGSIM,
        env=environment(control),
        capture_output=True,
        text=True,
        timeout=90,
    )
    if q.returncode:
        raise ValueError("runtime_import:" + q.stderr)
    report = dict(
        status="supported",
        control=str(control),
        source_commit=source,
        qualification_sha256=qualification,
        manifest_sha256=file(control, "execution_manifest.json", 4 * 1024**2)["sha256"],
        files=len(files),
        environment_import=dict(stdout=q.stdout, stderr=q.stderr, returncode=q.returncode),
    )
    record(control / "deployment.json", report)
    return report


def launch(control, permit):
    control = Path(control)
    pair = permit["pair"]
    envelope = read(control / f"block_{permit['block']:03d}_envelope.json")
    remaining(envelope["deadline_monotonic"], time.monotonic())
    if (
        permit["envelope_sha256"] != identity(envelope)
        or permit["manifest_sha256"]
        != file(control, "execution_manifest.json", 4 * 1024**2)["sha256"]
        or permit["plan_sha256"] != PLAN
    ):
        raise ValueError("launch_binding")
    if read(control / "host_qualification.json")["status"] != "supported":
        raise ValueError("host_qualification")
    idle()
    name = f"pair_{pair:03d}"
    record(control / (name + "_clearance.json"), permit)
    clearance = file(control, name + "_clearance.json", 4 * 1024**2)["sha256"]
    unit = envelope["pair_units"][str(pair)]
    argv = [
        PYTHON,
        "-u",
        "-m",
        "experiments.iter151_recovery_canary.pair",
        "--control",
        str(control),
        "--manifest-sha256",
        permit["manifest_sha256"],
        "--clearance-sha256",
        clearance,
        "--pair",
        str(pair),
        "--unit",
        unit,
    ]
    command = [
        "systemd-run",
        "--unit",
        unit,
        "--property=RuntimeMaxSec=2500",
        "--property=KillMode=control-group",
        "--working-directory=" + str(HUGSIM),
    ]
    for key in ("PYTHONPATH", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        command.append("--setenv=" + key + "=" + environment(control)[key])
    command.extend(argv)
    record(
        control / (name + "_launch_intent.json"),
        dict(argv=command, maximum_launch_commands=1, envelope_sha256=identity(envelope)),
    )
    q = subprocess.run(command, capture_output=True, text=True, timeout=15)
    report = dict(returncode=q.returncode, stdout=q.stdout, stderr=q.stderr, unit=unit)
    record(control / (name + "_launch_reply.json"), report)
    if q.returncode:
        raise ValueError("pair_launch:" + q.stderr)
    report["service"] = check_service(unit)
    return report


def postflight(control):
    from experiments.iter145_constrained_execution.resources import file_identity, actor_identity

    control = Path(control)
    manifest = read(control / "execution_manifest.json")
    changed, owned = [], []
    for name, expected in manifest["files"].items():
        if file_identity(Path(name), allow_empty=expected["bytes"] == 0) != expected:
            (owned if name.startswith(str(control / "map_cache") + "/") else changed).append(name)
    actors = Path("/datasets/nuscenes-full/hugsim/3DRealCar")
    for name, row in manifest["actor_aliases"].items():
        actual = actor_identity(
            actors, Path(name).parent.relative_to(actors), Path(name).name, manifest["actor_files"]
        )
        if actual["sha256"] != row["sha256"] or actual["physical_path"] != row["physical_path"]:
            changed.append(name)
    processes = idle()
    return dict(
        status="supported" if not changed else "failed",
        files=len(manifest["files"]),
        changed_original_files=changed,
        changed_owned_cache=owned,
        idle=processes,
        free_bytes=shutil.disk_usage(control).free,
    )
