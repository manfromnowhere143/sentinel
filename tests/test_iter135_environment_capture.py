from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
ITER135 = REPO / "experiments/iter135_neuroncap_blind_braking_dose_response"
MODULE_PATH = ITER135 / "capture_environment135.py"
SPEC = importlib.util.spec_from_file_location("iter135_environment_capture", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
capture = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = capture
SPEC.loader.exec_module(capture)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def nul_rows(rows: list[str]) -> bytes:
    return b"" if not rows else b"\0".join(row.encode() for row in rows) + b"\0"


class FakeRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.repositories: dict[str, dict[str, Any]] = {}
        self.images: dict[str, dict[str, Any]] = {}
        self.gpu_row = (
            f"{capture.EXPECTED_GPU_MODEL}, {capture.EXPECTED_GPU_UUID}, "
            f"{capture.EXPECTED_GPU_DRIVER}, {capture.EXPECTED_GPU_MEMORY_MIB}\n"
        ).encode()
        self.compute = b""
        self.containers = b""
        self.processes = b"500 1 python capture_environment135.py\n1 0 /sbin/init\n"
        self.mount = {
            "target": None,
            "source": "/dev/test-evidence",
            "fstype": "ext4",
            "uuid": "11111111-2222-3333-4444-555555555555",
        }
        self.fail_prefix: str | None = None

    def __call__(self, argv: list[str] | tuple[str, ...]) -> bytes:
        command = tuple(argv)
        self.calls.append(command)
        if self.fail_prefix is not None and command[0] == self.fail_prefix:
            raise capture.CaptureError(f"injected:{self.fail_prefix}")
        if command[0] == "git":
            repo = command[command.index("-C") + 1]
            args = command[command.index("-C") + 2 :]
            state = self.repositories[repo]
            if args == ("rev-parse", "--show-toplevel"):
                return f"{repo}\n".encode()
            if args == ("rev-parse", "HEAD"):
                return f"{state['head']}\n".encode()
            if args == ("diff", "--cached", "--name-only", "-z"):
                return nul_rows(state["staged"])
            if args == ("diff", "--name-only", "-z"):
                return nul_rows(state["dirty"])
            if args == ("ls-files", "--others", "--exclude-standard", "-z"):
                return nul_rows(state["untracked"])
        if command[:3] == ("docker", "image", "inspect"):
            return json.dumps([self.images[command[3]]]).encode()
        if command == ("docker", "ps", "-aq", "--no-trunc"):
            return self.containers
        if command[0] == "nvidia-smi" and "--query-gpu=" in command[1]:
            return self.gpu_row
        if command[0] == "nvidia-smi" and "--query-compute-apps=pid" in command:
            return self.compute
        if command == ("ps", "-eo", "pid=,ppid=,args="):
            return self.processes
        if command[0] == "findmnt":
            return json.dumps({"filesystems": [self.mount]}).encode()
        raise AssertionError(f"unexpected command: {command}")


def patch_constants() -> dict[str, str]:
    names = {
        "ANCHOR",
        "REPLACEMENT",
        "OUTPUT_DECLARATION_ANCHOR",
        "OUTPUT_DECLARATION_REPLACEMENT",
        "OUTPUT_MOUNT_ANCHOR",
        "OUTPUT_MOUNT_REPLACEMENT",
        "OUTPUT_LOG_ANCHOR",
        "OUTPUT_LOG_REPLACEMENT",
    }
    return capture._literal_assignments((ITER135 / "patch_compose_dose_env.py").read_bytes(), names)


def compose_pair() -> tuple[bytes, bytes]:
    values = patch_constants()
    source = (
        "#!/bin/bash\n"
        + values["OUTPUT_DECLARATION_ANCHOR"]
        + "renderer block\n"
        + "if [ $SHOULD_START_MODEL == true ]; then\n"
        + "docker run "
        + values["ANCHOR"]
        + "-e SENTINEL_TTC model\n"
        + "docker run --rm --gpus all \\\n"
        + values["OUTPUT_MOUNT_ANCHOR"]
        + values["OUTPUT_LOG_ANCHOR"]
    )
    final = source
    for anchor_name, replacement_name in (
        ("ANCHOR", "REPLACEMENT"),
        ("OUTPUT_DECLARATION_ANCHOR", "OUTPUT_DECLARATION_REPLACEMENT"),
        ("OUTPUT_MOUNT_ANCHOR", "OUTPUT_MOUNT_REPLACEMENT"),
        ("OUTPUT_LOG_ANCHOR", "OUTPUT_LOG_REPLACEMENT"),
    ):
        final = final.replace(values[anchor_name], values[replacement_name], 1)
    return source.encode(), final.encode()


def fixture(
    tmp_path: Path,
) -> tuple[capture.Contract, capture.Hooks, FakeRunner, dict[str, Path]]:
    root = tmp_path.resolve()
    files = root / "files"
    files.mkdir()
    repositories = {
        "uniad": root / "UniAD",
        "neuroncap": root / "NeuroNCAP",
        "neurad": root / "neurad-studio",
    }
    for path in repositories.values():
        path.mkdir()
    backup = repositories["neurad"] / "Dockerfile.bak"
    backup.write_bytes(b"frozen backup\n")
    source, final = compose_pair()
    patcher_source = (ITER135 / "patch_compose_dose_env.py").read_text()
    patcher_source = patcher_source.replace(
        "9f8804b523faa8ec3b6770a69b4b4bc9595c2b36e4b98422a588b9a3e1fe8e5d",
        digest(source),
    ).replace(
        "a5ed766b8a4c7efd7b33cdb6a9bdf9a5878f63604695758ff5f2268b770cfada",
        digest(final),
    )
    patcher_path = files / "patcher.py"
    patcher_path.write_text(patcher_source)
    compose_path = files / "_docker_compose_release.sh"
    compose_path.write_bytes(final)
    payload_path = files / "runtime.py"
    payload_path.write_bytes(b"print('runtime')\n")

    mount = root / "evidence-mount"
    mount.mkdir()
    output = mount / "sentinel-i135-outoutput"
    output.mkdir()
    archive_root = mount / "archives"
    metadata_root = mount / "v1.0-trainval"
    map_root = mount / "maps"
    archive_root.mkdir()
    metadata_root.mkdir()
    map_root.mkdir()
    archive_contract = {
        "v1.0-trainval_meta.tgz": ("4" * 64, 461_678_030),
        "v1.0-trainval01_blobs.tgz": ("5" * 64, 31_579_122_687),
    }
    for name in archive_contract:
        (archive_root / name).write_bytes(f"test fixture for {name}\n".encode())
    metadata_names = ("scene.json", "sample.json")
    for name in metadata_names:
        (metadata_root / name).write_text(json.dumps({"fixture": name}) + "\n")
    map_names = ("36092f0b03a857c6a3403e25b4b7aab3.png",)
    for name in map_names:
        (map_root / name).write_bytes(f"fixture:{name}\n".encode())
    expected_repositories = {
        "uniad": {
            "path": str(repositories["uniad"]),
            "head": "a" * 40,
            "staged_paths": [],
            "dirty_tracked_paths": ["shim.py"],
            "required_untracked_paths": [],
        },
        "neuroncap": {
            "path": str(repositories["neuroncap"]),
            "head": "b" * 40,
            "staged_paths": [],
            "dirty_tracked_paths": ["docker/Dockerfile", "scripts/compose.sh"],
            "required_untracked_paths": [],
        },
        "neurad": {
            "path": str(repositories["neurad"]),
            "head": "c" * 40,
            "staged_paths": [],
            "dirty_tracked_paths": ["Dockerfile"],
            "required_untracked_paths": ["Dockerfile.bak"],
        },
    }
    image_ids = {
        "ncap:latest": "sha256:" + "1" * 64,
        "neurad:latest": "sha256:" + "2" * 64,
        "uniad:latest": "sha256:" + "3" * 64,
    }
    contract = capture.Contract(
        schema="iter135.environment_receipts.test.v1",
        ready_verdict="I135_ENVIRONMENT_PREFLIGHT_OK",
        remote_files={
            "compose_script": (str(compose_path), digest(final), len(final)),
            "neurad_dockerfile_backup": (
                str(backup),
                digest(backup.read_bytes()),
                backup.stat().st_size,
            ),
            "runtime": (
                str(payload_path),
                digest(payload_path.read_bytes()),
                payload_path.stat().st_size,
            ),
        },
        repositories=expected_repositories,
        required_untracked_bindings={("neurad", "Dockerfile.bak"): "neurad_dockerfile_backup"},
        storage_identity={
            "filesystem_path": str(output),
            "filesystem_realpath": str(output),
            "filesystem_is_symlink": False,
            "filesystem_empty": True,
            "mount_target": str(mount),
            "mount_source": "/dev/test-evidence",
            "mount_fstype": "ext4",
            "mount_uuid": "11111111-2222-3333-4444-555555555555",
        },
        dataset_schema="iter135.nuscenes_dataset_receipt.test.v1",
        dataset_contract_sha256="",
        dataset_root=str(mount),
        dataset_version="v1.0-trainval",
        dataset_archive_root=str(archive_root),
        dataset_metadata_root=str(metadata_root),
        dataset_map_root=str(map_root),
        dataset_mount={
            "mount_target": str(mount),
            "mount_source": "/dev/test-evidence",
            "mount_fstype": "ext4",
            "mount_uuid": "11111111-2222-3333-4444-555555555555",
        },
        dataset_proof_basis={
            "iteration": 28,
            "result_path": "fixture/RESULT.md",
            "receipt_directory": "fixture/uploads",
            "archive_count": 2,
            "archive_total_bytes": sum(row[1] for row in archive_contract.values()),
        },
        dataset_archives=archive_contract,
        dataset_metadata_files=metadata_names,
        dataset_map_anchors=map_names,
        image_ids=image_ids,
        compose_input_sha256=digest(source),
        compose_output_sha256=digest(final),
        projected_output_bytes=100,
        minimum_remote_free_bytes=200,
        minimum_reserve_bytes=50,
        minimum_local_free_bytes=150,
    )
    contract = replace(
        contract,
        dataset_contract_sha256=capture._canonical_json_sha256(
            capture._dataset_contract_payload(contract)
        ),
    )
    runner = FakeRunner()
    runner.mount["target"] = str(mount)
    for repo_id, expected in expected_repositories.items():
        runner.repositories[expected["path"]] = {
            "head": expected["head"],
            "staged": list(expected["staged_paths"]),
            "dirty": list(expected["dirty_tracked_paths"]),
            "untracked": (
                ["outoutput/old/run_0/metrics.json"]
                if repo_id == "neuroncap"
                else list(expected["required_untracked_paths"])
            ),
        }
    for name, image_id in image_ids.items():
        runner.images[name] = {
            "Id": image_id,
            "RepoDigests": [f"{name.rsplit(':', 1)[0]}@{image_id}"],
        }
    runner.images["ncap:latest"]["RepoDigests"] = []
    runner.images["neurad:latest"]["RepoDigests"] = [
        "neurad@sha256:" + "e" * 64,
        "neurad@sha256:" + "d" * 64,
    ]
    fixed_time = datetime(2026, 7, 16, 10, 0, tzinfo=UTC)

    def dataset_read(path: Path) -> tuple[dict[str, Any], list[str]]:
        if path.parent == archive_root:
            archive_sha256, archive_bytes = contract.dataset_archives[path.name]
            return {
                "path": str(path),
                "sha256": archive_sha256,
                "bytes": archive_bytes,
            }, []
        return capture._read_dataset_file(path)

    hooks = capture.Hooks(
        run=runner,
        hostname=lambda: capture.EXPECTED_HOST,
        disk_free=lambda _path: 1_000,
        device=lambda path: 1 if path == Path("/") else 2,
        now=lambda: fixed_time,
        pid=lambda: 500,
        dataset_read=dataset_read,
    )
    return (
        contract,
        hooks,
        runner,
        {
            "output": output,
            "mount": mount,
            "payload": payload_path,
            "compose": compose_path,
            "backup": backup,
            "patcher": patcher_path,
            "dataset_root": mount,
            "archive_root": archive_root,
            "metadata_root": metadata_root,
            "map_root": map_root,
        },
    )


def run_capture(
    contract: capture.Contract,
    hooks: capture.Hooks,
    *,
    local_free_bytes: int = 500,
) -> dict[str, Any]:
    patcher_path = Path(contract.remote_files["compose_script"][0]).parent / "patcher.py"
    return capture.capture_environment(
        contract,
        local_free_bytes=local_free_bytes,
        patcher_path=patcher_path,
        hooks=hooks,
    )


def test_green_capture_is_raw_exact_and_read_only(tmp_path: Path) -> None:
    contract, hooks, runner, paths = fixture(tmp_path)

    receipt = run_capture(contract, hooks)

    assert receipt["verdict"] == contract.ready_verdict
    assert receipt["problem_count"] == 0
    assert receipt["problems"] == []
    assert receipt["gpu"] == {
        "model": capture.EXPECTED_GPU_MODEL,
        "count": 1,
        "uuid": capture.EXPECTED_GPU_UUID,
        "driver_version": capture.EXPECTED_GPU_DRIVER,
        "memory_total_mib": capture.EXPECTED_GPU_MEMORY_MIB,
    }
    assert receipt["box"]["all_containers"] == 0
    assert receipt["box"]["gpu_compute_processes"] == 0
    assert receipt["box"]["known_evaluation_processes"] == 0
    assert set(receipt["box"]) == {
        "idle",
        "all_containers",
        "gpu_compute_processes",
        "known_evaluation_processes",
    }
    assert receipt["container_images"]["ncap:latest"]["repo_digests"] == []
    assert receipt["container_images"]["neurad:latest"]["repo_digests"] == [
        "neurad@sha256:" + "d" * 64,
        "neurad@sha256:" + "e" * 64,
    ]
    assert receipt["storage_devices"] == {
        "filesystem_st_dev": 2,
        "mount_st_dev": 2,
        "root_st_dev": 1,
    }
    assert receipt["dataset"]["schema"] == contract.dataset_schema
    assert receipt["dataset"]["contract_sha256"] == contract.dataset_contract_sha256
    assert set(receipt["dataset"]["archives"]) == set(contract.dataset_archives)
    assert set(receipt["dataset"]["metadata_json"]) == set(contract.dataset_metadata_files)
    assert set(receipt["dataset"]["map_anchors"]) == set(contract.dataset_map_anchors)
    assert receipt["dataset"]["identity"] == {
        "dataset_root": contract.dataset_root,
        "dataset_realpath": contract.dataset_root,
        "dataset_is_symlink": False,
        "dataset_version": contract.dataset_version,
        "archive_root": contract.dataset_archive_root,
        "archive_realpath": contract.dataset_archive_root,
        "archive_is_symlink": False,
        "metadata_root": contract.dataset_metadata_root,
        "metadata_realpath": contract.dataset_metadata_root,
        "metadata_is_symlink": False,
        "map_root": contract.dataset_map_root,
        "map_realpath": contract.dataset_map_root,
        "map_is_symlink": False,
        **contract.dataset_mount,
        "dataset_st_dev": 2,
        "mount_st_dev": 2,
        "root_st_dev": 1,
    }
    assert receipt["dataset"]["receipt_payload_sha256"] == (
        capture._dataset_receipt_payload_sha256(receipt["dataset"])
    )
    assert receipt["remote_files"]["compose_script"]["source_sha256"] == (
        contract.compose_input_sha256
    )
    assert receipt["remote_files"]["compose_script"]["patcher_sha256"] == digest(
        paths["patcher"].read_bytes()
    )
    flattened = " ".join(" ".join(command) for command in runner.calls)
    for forbidden in ("docker run", "git checkout", "git reset", " mkdir ", " rm "):
        assert forbidden not in flattened


def test_remote_byte_drift_and_symlink_are_rejected(tmp_path: Path) -> None:
    contract, hooks, _runner, paths = fixture(tmp_path)
    paths["payload"].write_bytes(b"mutated\n")
    target = paths["backup"].with_name("backup-target")
    target.write_bytes(paths["backup"].read_bytes())
    paths["backup"].unlink()
    paths["backup"].symlink_to(target)

    receipt = run_capture(contract, hooks)

    assert "remote-file:runtime:sha256" in receipt["problems"]
    assert "remote-file:runtime:bytes" in receipt["problems"]
    assert any(
        problem.startswith("remote-file:neurad_dockerfile_backup:path:symlink:")
        for problem in receipt["problems"]
    )
    assert any(
        problem.startswith("remote-file:neurad_dockerfile_backup:path:realpath:")
        for problem in receipt["problems"]
    )


def test_repository_head_status_and_untracked_code_are_rejected(tmp_path: Path) -> None:
    contract, hooks, runner, _paths = fixture(tmp_path)
    uniad = str(contract.repositories["uniad"]["path"])
    neurad = str(contract.repositories["neurad"]["path"])
    runner.repositories[uniad].update(
        {
            "head": "f" * 40,
            "staged": ["runtime.py"],
            "dirty": ["inference/server.py"],
            "untracked": ["evil.py"],
        }
    )
    runner.repositories[neurad]["untracked"] = []

    receipt = run_capture(contract, hooks)

    for problem in (
        "repository:uniad:head",
        "repository:uniad:staged-paths",
        "repository:uniad:dirty-tracked-paths",
        "repository:uniad:unexpected-untracked:1",
        "repository:neurad:required-untracked",
    ):
        assert problem in receipt["problems"]


def test_image_gpu_container_and_evaluator_drift_are_rejected(tmp_path: Path) -> None:
    contract, hooks, runner, _paths = fixture(tmp_path)
    runner.images["uniad:latest"]["Id"] = "sha256:" + "f" * 64
    runner.images["ncap:latest"]["RepoDigests"] = ["not-a-distribution-digest"]
    duplicate = "neurad@sha256:" + "a" * 64
    runner.images["neurad:latest"]["RepoDigests"] = [duplicate, duplicate]
    runner.gpu_row = (
        f"NVIDIA L4, GPU-ffffffff-ffff-ffff-ffff-ffffffffffff, "
        f"{capture.EXPECTED_GPU_DRIVER}, {capture.EXPECTED_GPU_MEMORY_MIB}\n"
    ).encode()
    runner.containers = b"a" * 64 + b"\n"
    runner.compute = b"4321\n"
    runner.processes += b"700 1 python /opt/sentinel-stack/NeuroNCAP/main.py\n"

    receipt = run_capture(contract, hooks)

    for problem in (
        "image:uniad:latest:id",
        "image:ncap:latest:repo-digests-schema",
        "image:neurad:latest:repo-digests-duplicate",
        "gpu:identity",
        "idle:containers-present",
        "idle:gpu-process-present",
        "idle:evaluator-process-present",
    ):
        assert problem in receipt["problems"]
    assert receipt["container_images"]["neurad:latest"]["repo_digests"] == [duplicate]
    assert receipt["box"]["idle"] is False


def test_storage_mount_device_emptiness_and_local_free_fail_closed(tmp_path: Path) -> None:
    contract, hooks, runner, paths = fixture(tmp_path)
    (paths["output"] / "unexpected").write_text("occupied")
    runner.mount["source"] = "/dev/root"
    bad_hooks = replace(
        hooks,
        device=lambda _path: 1,
        disk_free=lambda _path: 149,
    )

    receipt = run_capture(contract, bad_hooks, local_free_bytes=149)

    for problem in (
        "storage:identity:filesystem_empty",
        "storage:identity:mount_source",
        "storage:not-dedicated-device",
        "storage:projected-reserve",
        "storage:local-free",
    ):
        assert problem in receipt["problems"]


def test_dataset_archive_byte_proof_drift_fails_closed_without_large_fixture(
    tmp_path: Path,
) -> None:
    contract, hooks, _runner, _paths = fixture(tmp_path)
    original_reader = hooks.dataset_read
    target_name = next(iter(contract.dataset_archives))

    def drifted_reader(path: Path) -> tuple[dict[str, Any], list[str]]:
        row, problems = original_reader(path)
        if path.name == target_name:
            row = {**row, "sha256": "f" * 64, "bytes": row["bytes"] + 1}
        return row, problems

    receipt = run_capture(contract, replace(hooks, dataset_read=drifted_reader))

    assert f"dataset:archive:{target_name}:expected-sha256" in receipt["problems"]
    assert f"dataset:archive:{target_name}:expected-bytes" in receipt["problems"]


def test_dataset_exact_metadata_set_and_physical_map_anchor_fail_closed(
    tmp_path: Path,
) -> None:
    contract, hooks, _runner, paths = fixture(tmp_path)
    (paths["metadata_root"] / "self-declared.json").write_text("{}\n")
    map_name = contract.dataset_map_anchors[0]
    anchor = paths["map_root"] / map_name
    replacement_path = paths["dataset_root"] / "map-replacement.png"
    replacement_path.write_bytes(anchor.read_bytes())
    anchor.unlink()
    anchor.symlink_to(replacement_path)

    receipt = run_capture(contract, hooks)

    assert "dataset:metadata:file-set" in receipt["problems"]
    assert f"dataset:maps:nonphysical-file:{map_name}" in receipt["problems"]
    assert any(
        problem.startswith(f"dataset:map:{map_name}:path:symlink:")
        for problem in receipt["problems"]
    )


def test_dataset_contract_digest_and_device_identity_fail_closed(tmp_path: Path) -> None:
    contract, hooks, runner, _paths = fixture(tmp_path)
    runner.mount["uuid"] = "00000000-0000-0000-0000-000000000000"
    bad_contract = replace(contract, dataset_version="v1.0-mini")
    bad_hooks = replace(hooks, device=lambda _path: 1)

    receipt = run_capture(bad_contract, bad_hooks)

    assert "dataset:contract-sha256" in receipt["problems"]
    assert "dataset:identity:mount_uuid" in receipt["problems"]
    assert "dataset:not-dedicated-device" in receipt["problems"]


def test_compose_preimage_or_patcher_drift_cannot_self_assert(tmp_path: Path) -> None:
    contract, hooks, _runner, _paths = fixture(tmp_path)
    contract = replace(contract, compose_input_sha256="0" * 64)

    receipt = run_capture(contract, hooks)

    assert "compose:source-sha256" in receipt["problems"]
    assert receipt["remote_files"]["compose_script"]["source_sha256"] != "0" * 64


def test_command_failure_is_incomplete_not_green(tmp_path: Path) -> None:
    contract, hooks, runner, _paths = fixture(tmp_path)
    runner.fail_prefix = "docker"

    receipt = run_capture(contract, hooks)

    assert receipt["verdict"] == capture.INCOMPLETE_VERDICT
    assert receipt["problem_count"] > 0
    assert any(problem.startswith("image:") for problem in receipt["problems"])
    assert any(problem.startswith("idle:containers:") for problem in receipt["problems"])


def test_atomic_writer_replaces_regular_file_without_temp_residue(tmp_path: Path) -> None:
    output = tmp_path.resolve() / "env_receipts.json"
    output.write_text("old\n")
    receipt = {"schema": "test", "problem_count": 0, "problems": []}

    capture.atomic_write_json(output, receipt)

    assert json.loads(output.read_text()) == receipt
    assert list(output.parent.glob(f".{output.name}.*.tmp")) == []
    assert output.stat().st_mode & 0o777 == 0o600


def test_canonical_contract_loads_exact_82_role_topology() -> None:
    contract = capture.load_contract()

    assert len(contract.remote_files) == 82
    assert sum(role.startswith("scenario:") for role in contract.remote_files) == 20
    assert sum(role.startswith("renderer:") for role in contract.remote_files) == 42
    assert set(contract.repositories) == {"uniad", "neuroncap", "neurad"}
    assert contract.required_untracked_bindings == {
        ("neurad", "Dockerfile.bak"): "neurad_dockerfile_backup"
    }
    assert contract.schema == "iter135.environment_receipts.v2"
    assert contract.dataset_root == "/datasets/nuscenes-full"
    assert contract.dataset_version == "v1.0-trainval"
    assert contract.dataset_contract_sha256 == (capture.EXPECTED_CANONICAL_DATASET_CONTRACT_SHA256)
    assert len(contract.dataset_archives) == 11
    assert sum(row[1] for row in contract.dataset_archives.values()) == 314_886_603_672
    assert len(contract.dataset_metadata_files) == 13
    assert len(contract.dataset_map_anchors) == 4


def test_local_free_cli_value_is_mandatory_and_nonnegative() -> None:
    parser = capture._nonnegative_integer

    assert parser("123") == 123
    for value in ("-1", "1.5", "secret"):
        try:
            parser(value)
        except Exception:
            pass
        else:
            raise AssertionError(f"invalid explicit byte count accepted: {value}")
