from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]
SOURCE_EXP = REPO / "experiments/iter135_neuroncap_blind_braking_dose_response"
MODULE_PATH = SOURCE_EXP / "make_launch_manifest.py"
SPEC = importlib.util.spec_from_file_location("iter135_launch_manifest", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
manifest = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manifest)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def github_pre_smoke_authority(manifest_sha256: str) -> dict[str, object]:
    commit = "f" * 40
    authority: dict[str, object] = {
        "schema": "iter135.github_pre_smoke_authority.v1",
        "repository": "manfromnowhere143/sentinel",
        "branch": "master",
        "pre_smoke_commit": commit,
        "environment_parent": "e" * 40,
        "manifest_sha256": manifest_sha256,
        "checks": [
            {
                "name": name,
                "id": check_id,
                "head_sha": commit,
                "app_slug": "github-actions",
                "status": "completed",
                "conclusion": "success",
            }
            for name, check_id in (("check (3.10)", 310), ("check (3.11)", 311))
        ],
    }
    authority["authority_payload_sha256"] = hashlib.sha256(
        json.dumps(authority, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return authority


def ready_git_receipt() -> dict:
    return {
        "schema": "iter135.git_provenance.v1",
        "verdict": "I135_GIT_PROVENANCE_OK",
        "head": "a" * 40,
        "hypothesis_commits": ["b" * 40, "c" * 40],
        "latest_hypothesis_commit": "c" * 40,
        "file_commits": {},
        "dirty_lines": [],
        "problem_count": 0,
        "problems": [],
    }


def publication_authority(commit: str, artifacts: list[dict] | None = None) -> dict:
    return {
        "schema": manifest.EXPECTED_PUBLICATION_AUTHORITY_SCHEMA,
        "repository": manifest.EXPECTED_PUBLICATION_REPOSITORY,
        "branch": manifest.EXPECTED_PUBLICATION_BRANCH,
        "source_commit": commit,
        "branch_head_sha": commit,
        "required_checks": list(manifest.EXPECTED_PUBLICATION_CHECKS),
        "checks": [
            {
                "name": name,
                "id": 510 + index,
                "status": "completed",
                "conclusion": "success",
                "head_sha": commit,
                "app_slug": "github-actions",
            }
            for index, name in enumerate(manifest.EXPECTED_PUBLICATION_CHECKS)
        ],
        "artifacts": artifacts or [],
        "verified": True,
    }


def docker_runtime_receipt() -> dict:
    return {
        "schema": manifest.EXPECTED_DOCKER_RUNTIME_SCHEMA,
        "client": {
            "invocation_path": "/usr/bin/docker",
            "physical_path": "/usr/bin/docker",
            "realpath": "/usr/bin/docker",
            "sha256": "8" * 64,
            "bytes": 38_000_000,
            "version": {
                "version": "27.5.1",
                "api_version": "1.47",
                "git_commit": "4c9b3b0",
                "go_version": "go1.22.11",
                "os": "linux",
                "arch": "amd64",
                "build_time": "2025-01-22T13:41:17.000000000+00:00",
                "context": "default",
            },
        },
        "context": {"name": "default", "endpoint": "unix:///var/run/docker.sock"},
        "daemon": {
            "info": {
                "id": "SENTINELENGINE",
                "name": "sentinel-gpu",
                "server_version": "27.5.1",
                "docker_root_dir": "/var/lib/docker",
                "driver": "overlay2",
                "operating_system": "Ubuntu 22.04.5 LTS",
                "os_type": "linux",
                "architecture": "x86_64",
                "ncpu": 8,
                "mem_total": 33_000_000_000,
                "kernel_version": "6.8.0",
                "cgroup_driver": "systemd",
                "cgroup_version": "2",
            },
            "version": {
                "platform_name": "Docker Engine - Community",
                "version": "27.5.1",
                "api_version": "1.47",
                "min_api_version": "1.24",
                "git_commit": "4c9b3b0",
                "go_version": "go1.22.11",
                "os": "linux",
                "arch": "amd64",
                "build_time": "2025-01-22T13:41:17.000000000+00:00",
                "experimental": False,
            },
        },
    }


def mission_state(phase: str = "LAUNCH_AUTHORIZED") -> dict:
    phase_actions = manifest.EXPECTED_PHASE_ACTIONS.get(phase, ((), ()))
    return {
        "schema": "sentinel.mission_state.v1",
        "canonical_repository": "/Users/danielwahnich/workspace/sentinel",
        "workspace_boundary": copy.deepcopy(manifest.EXPECTED_WORKSPACE_BOUNDARY),
        "trunk": "master",
        "current_completed_iteration": 134,
        "current_result": "experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md",
        "current_verdict": "PLACEBO_HARM_OR_NULL",
        "run_state": "IDLE",
        "active_hypothesis": manifest.ACTIVE_HYPOTHESIS,
        "next_program": {
            "iteration": 135,
            "name": manifest.EXPECTED_PROGRAM_NAME,
            "phase": phase,
            "authorized_actions": list(phase_actions[0]),
            "forbidden_actions": list(phase_actions[1]),
        },
        "claim_state": copy.deepcopy(manifest.EXPECTED_MISSION_CLAIM_STATE),
        "deprecated_pending_hypotheses": copy.deepcopy(
            manifest.EXPECTED_DEPRECATED_HYPOTHESES
        ),
        "paper_state": copy.deepcopy(manifest.EXPECTED_PAPER_STATE),
        "storage_gate": {
            "minimum_local_free_gib_before_new_proof_collection": 15,
            "remote_execution_filesystem_path": "/datasets/nuscenes-full",
            "analytic_output_root": manifest.EXPECTED_OUTPUT_ROOT,
            "minimum_remote_execution_filesystem_free_gib_before_gpu_launch": 100,
            "minimum_remote_execution_filesystem_reserve_gib_after_projected_output": 25,
            "policy": (
                "preserve committed proof and hashes; delete only hash-verified duplicates, "
                "reproducible renders, and caches"
            ),
        },
    }


def analyzer_source() -> str:
    return """ARMS = (
    "off_baseline", "released_union_semantic_reference", "blind_0_5x",
    "blind_1_0x", "blind_1_5x", "blind_2_0x",
)
PAIRS = (
    ("stationary", "0099"), ("stationary", "0101"),
    ("stationary", "0103"), ("stationary", "0106"),
    ("stationary", "0108"), ("stationary", "0278"),
    ("stationary", "0331"), ("stationary", "0783"),
    ("stationary", "0796"), ("stationary", "0966"),
    ("frontal", "0103"), ("frontal", "0106"),
    ("frontal", "0110"), ("frontal", "0346"),
    ("frontal", "0923"), ("side", "0103"),
    ("side", "0108"), ("side", "0110"),
    ("side", "0278"), ("side", "0921"),
)

def expected_execution_order():
    out = []
    for pair_index, (cls, seq) in enumerate(PAIRS):
        rotation = pair_index % len(ARMS)
        for arm in ARMS[rotation:] + ARMS[:rotation]:
            for run in range(20):
                out.append((arm, cls, seq, run))
    return out
"""


def write_host_evidence(exp: Path, state_path: Path) -> None:
    source_commit = subprocess.run(
        ("git", "-C", str(REPO), "rev-parse", "HEAD"),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    packet_state_payload = subprocess.run(
        ("git", "-C", str(REPO), "show", f"{source_commit}:MISSION_STATE.json"),
        check=True,
        capture_output=True,
    ).stdout
    packet_files: dict[str, dict[str, object]] = {}
    observed_files: dict[str, dict[str, object]] = {}
    for name in manifest.HOST_PACKET_FILE_NAMES:
        mode = 0o755 if name in manifest.HOST_PACKET_EXECUTABLE_FILES else 0o644
        if name == "MISSION_STATE.json":
            digest = hashlib.sha256(packet_state_payload).hexdigest()
            byte_count = len(packet_state_payload)
        else:
            path = exp / name
            digest = sha256(path)
            byte_count = path.stat().st_size
        row: dict[str, object] = {
            "sha256": digest,
            "bytes": byte_count,
            "mode": mode,
        }
        packet_files[name] = row
        observed_files[name] = {
            "path": f"/opt/sentinel-stack/.iter135-packet/{name}",
            **row,
        }
    packet = {
        "schema": manifest.EXPECTED_HOST_PACKET_SCHEMA,
        "source_commit": source_commit,
        "files": packet_files,
    }
    packet_path = exp / manifest.HOST_PACKET_MANIFEST_REL
    packet_path.write_text(json.dumps(packet, sort_keys=True) + "\n")
    packet_binding = {
        "path": "/opt/sentinel-stack/.iter135-packet/host_packet_manifest.json",
        "sha256": sha256(packet_path),
        "bytes": packet_path.stat().st_size,
        "mode": 0o644,
    }
    source_artifacts = []
    for name, row in packet_files.items():
        payload = packet_state_payload if name == "MISSION_STATE.json" else (exp / name).read_bytes()
        source_artifacts.append(
            {
                "path": (
                    "MISSION_STATE.json"
                    if name == "MISSION_STATE.json"
                    else f"{manifest.EXPERIMENT_REL}/{name}"
                ),
                "sha256": row["sha256"],
                "bytes": row["bytes"],
                "git_blob_oid": manifest._git_blob_oid(payload),
                "git_mode": "100755" if row["mode"] == 0o755 else "100644",
            }
        )
    source_artifacts.sort(key=lambda row: row["path"])
    preparation = {
        "schema": manifest.EXPECTED_HOST_PREPARATION_SCHEMA,
        "verdict": manifest.EXPECTED_HOST_PREPARATION_VERDICT,
        "started_at_utc": "2026-07-16T09:58:00Z",
        "finished_at_utc": "2026-07-16T09:59:00Z",
        "host": "sentinel-gpu",
        "problem_count": 0,
        "problems": [],
        "packet_manifest_sha256": packet_binding["sha256"],
        "publication_authority": publication_authority(source_commit, source_artifacts),
        "packet": {
            "schema": manifest.EXPECTED_HOST_PACKET_SCHEMA,
            "source_commit": packet["source_commit"],
            "manifest": packet_binding,
            "independently_supplied_manifest_sha256": packet_binding["sha256"],
            "files": observed_files,
        },
        "controller": observed_files["prepare_host135.py"],
        "repositories": {},
        "compose": {},
        "storage": {},
        "forbidden_paths": {},
        "actions": [],
        "invocation": {},
        "receipt_payload_sha256": None,
    }
    payload = dict(preparation)
    payload.pop("receipt_payload_sha256")
    preparation["receipt_payload_sha256"] = manifest._canonical_json_sha256(payload)
    (exp / manifest.HOST_PREPARATION_RECEIPT_REL).write_text(
        json.dumps(preparation, sort_keys=True) + "\n"
    )


def environment_receipt(exp: Path) -> dict:
    preparation_path = exp / manifest.HOST_PREPARATION_RECEIPT_REL
    packet_path = exp / manifest.HOST_PACKET_MANIFEST_REL
    preparation = json.loads(preparation_path.read_text())
    gpu = copy.deepcopy(manifest.EXPECTED_GPU_IDENTITY)
    box = {
        "idle": True,
        "all_containers": 0,
        "gpu_compute_processes": 0,
        "known_evaluation_processes": 0,
    }
    remote_files = {
        role: {"path": path, "sha256": digest, "bytes": byte_count}
        for role, (path, digest, byte_count) in manifest.EXPECTED_REMOTE_FILES.items()
    }
    remote_files["compose_script"].update(
        {
            "source_sha256": manifest.EXPECTED_COMPOSE_INPUT_SHA256,
            "patcher_sha256": sha256(exp / "patch_compose_dose_env.py"),
        }
    )
    dataset = {
        "schema": manifest.EXPECTED_DATASET_SCHEMA,
        "contract_sha256": manifest.EXPECTED_DATASET_CONTRACT_SHA256,
        "proof_basis": copy.deepcopy(manifest.EXPECTED_DATASET_PROOF_BASIS),
        "identity": {
            "dataset_root": manifest.EXPECTED_DATASET_ROOT,
            "dataset_realpath": manifest.EXPECTED_DATASET_ROOT,
            "dataset_is_symlink": False,
            "dataset_version": manifest.EXPECTED_DATASET_VERSION,
            "archive_root": manifest.EXPECTED_DATASET_ARCHIVE_ROOT,
            "archive_realpath": manifest.EXPECTED_DATASET_ARCHIVE_ROOT,
            "archive_is_symlink": False,
            "metadata_root": manifest.EXPECTED_DATASET_METADATA_ROOT,
            "metadata_realpath": manifest.EXPECTED_DATASET_METADATA_ROOT,
            "metadata_is_symlink": False,
            "map_root": manifest.EXPECTED_DATASET_MAP_ROOT,
            "map_realpath": manifest.EXPECTED_DATASET_MAP_ROOT,
            "map_is_symlink": False,
            **manifest.EXPECTED_DATASET_MOUNT,
            "dataset_st_dev": 66308,
            "mount_st_dev": 66308,
            "root_st_dev": 66305,
        },
        "archives": {
            name: {
                "path": f"{manifest.EXPECTED_DATASET_ARCHIVE_ROOT}/{name}",
                "sha256": digest,
                "bytes": byte_count,
            }
            for name, (digest, byte_count) in manifest.EXPECTED_DATASET_ARCHIVES.items()
        },
        "metadata_json": {
            name: {
                "path": f"{manifest.EXPECTED_DATASET_METADATA_ROOT}/{name}",
                "sha256": hashlib.sha256(f"metadata:{name}".encode()).hexdigest(),
                "bytes": len(f"metadata:{name}".encode()),
            }
            for name in manifest.EXPECTED_DATASET_METADATA_FILES
        },
        "map_anchors": {
            name: {
                "path": f"{manifest.EXPECTED_DATASET_MAP_ROOT}/{name}",
                "sha256": hashlib.sha256(f"map:{name}".encode()).hexdigest(),
                "bytes": len(f"map:{name}".encode()),
            }
            for name in manifest.EXPECTED_DATASET_MAP_ANCHORS
        },
    }
    dataset["receipt_payload_sha256"] = manifest._dataset_receipt_payload_sha256(dataset)
    return {
        "schema": manifest.EXPECTED_ENV_SCHEMA,
        "verdict": manifest.EXPECTED_ENV_VERDICT,
        "captured_at_utc": "2026-07-16T10:00:00Z",
        "capture_started_at_utc": "2026-07-16T09:59:00Z",
        "host": "sentinel-gpu",
        "problem_count": 0,
        "problems": [],
        "interpreter": {
            "invocation_path": "/usr/bin/python3",
            "physical_path": "/usr/bin/python3.10",
            "realpath": "/usr/bin/python3.10",
            "sha256": "9" * 64,
            "bytes": 6_831_264,
            "version": "3.10.14",
            "implementation": "CPython",
        },
        "invocation": {
            "sanitized": True,
            "isolated": True,
            "environment": copy.deepcopy(manifest.EXPECTED_CAPTURE_ENVIRONMENT),
            "argv": [
                "/usr/bin/python3.10",
                "-I",
                "/opt/sentinel-stack/iter135/capture_environment135.py",
                "--local-free-bytes",
                str(45 * 1024**3),
            ],
            "canonical_script": "/opt/sentinel-stack/iter135/capture_environment135.py",
        },
        "host_preparation": {
            "receipt_file": {
                "path": "/opt/sentinel-stack/iter135/host_preparation_receipt.json",
                "sha256": sha256(preparation_path),
                "bytes": preparation_path.stat().st_size,
            },
            "evidence": preparation,
        },
        "host_publication_authority": publication_authority(
            "f" * 40,
            [
                {
                    "path": f"{manifest.EXPERIMENT_REL}/{manifest.HOST_PACKET_MANIFEST_REL}",
                    "sha256": sha256(packet_path),
                    "bytes": packet_path.stat().st_size,
                    "git_blob_oid": manifest._git_blob_oid(packet_path.read_bytes()),
                    "git_mode": "100644",
                },
                {
                    "path": (
                        f"{manifest.EXPERIMENT_REL}/{manifest.HOST_PREPARATION_RECEIPT_REL}"
                    ),
                    "sha256": sha256(preparation_path),
                    "bytes": preparation_path.stat().st_size,
                    "git_blob_oid": manifest._git_blob_oid(
                        preparation_path.read_bytes()
                    ),
                    "git_mode": "100644",
                },
            ],
        ),
        "docker_runtime": docker_runtime_receipt(),
        "runtime_snapshots": {
            "before_dataset_hashing": {"gpu": copy.deepcopy(gpu), "box": copy.deepcopy(box)},
            "after_dataset_hashing": {"gpu": copy.deepcopy(gpu), "box": copy.deepcopy(box)},
        },
        "gpu": gpu,
        "box": box,
        "storage": {
            "remote_output_free_bytes": 120 * 1024**3,
            "projected_output_bytes": manifest.PROJECTED_OUTPUT_BYTES,
            "minimum_reserve_bytes": manifest.MINIMUM_RESERVE_BYTES,
            "local_free_bytes": 45 * 1024**3,
            "remote_output_free_gib": 120.0,
            "projected_output_gib": manifest.PROJECTED_OUTPUT_BYTES / 1024**3,
            "minimum_reserve_gib": 25.0,
            "local_free_gib": 45.0,
            **manifest.EXPECTED_STORAGE_IDENTITY,
        },
        "storage_devices": {
            "filesystem_st_dev": 66308,
            "mount_st_dev": 66308,
            "root_st_dev": 66305,
        },
        "dataset": dataset,
        "repositories": copy.deepcopy(manifest.EXPECTED_REPOSITORIES),
        "remote_files": remote_files,
        "container_images": {
            name: {"image_id": image_id, "repo_digests": []}
            for name, image_id in manifest.EXPECTED_IMAGE_IDS.items()
        },
    }


def smoke_receipt(exp: Path, env: dict) -> dict:
    schedule = json.loads((exp / "dose_schedules.json").read_text())
    smoke_state_path = exp / "MISSION_STATE.json"
    smoke_state_path.write_text(
        json.dumps(mission_state(manifest.PREFLIGHT_MISSION_PHASE), indent=1, sort_keys=True)
        + "\n"
    )
    raw_dir = exp / "smoke-evidence/raw"
    raw_dir.mkdir(parents=True)
    (raw_dir / "pre_smoke_mission_state.json").write_bytes(
        smoke_state_path.read_bytes()
    )
    (raw_dir / "environment_receipt.json").write_bytes(
        (exp / manifest.ENV_RECEIPT_REL).read_bytes()
    )

    smoke_bound_names = (
        "dose_schedules.json",
        "server_patch_blind_dose.py",
        "run_smoke135.sh",
        "validate_smoke135.py",
        "host_packet_manifest.json",
        "host_preparation_receipt.json",
        "env_receipts.json",
    )
    image_ids = {name: row["image_id"] for name, row in sorted(env["container_images"].items())}
    manifest_environment = copy.deepcopy(env)
    manifest_environment["docker_image_ids"] = image_ids
    pre_manifest = {
        "schema": manifest.SCHEMA,
        "verdict": manifest.INCOMPLETE_VERDICT,
        "launch_authorized": False,
        "mission_phase": "TOOLING_FROZEN_PREFLIGHT_REQUIRED",
        "mission_state": {
            "source_path": "MISSION_STATE.json",
            "sha256": sha256(smoke_state_path),
            "bytes": smoke_state_path.stat().st_size,
        },
        "git_provenance": {"head": "e" * 40},
        "design": {},
        "planned_blocks": 120,
        "planned_episodes": 2400,
        "pair_order": [],
        "execution_blocks": [],
        "execution_cells": [],
        "hash_bound_files": {
            name: {
                "source_path": f"{manifest.EXPERIMENT_REL}/{name}",
                "sha256": sha256(exp / name),
                "bytes": (exp / name).stat().st_size,
            }
            for name in smoke_bound_names
        },
        "source_artifacts": [],
        "remote_artifacts": {},
        "dataset_receipt": copy.deepcopy(env["dataset"]),
        "environment_receipts": manifest_environment,
        "container_images": copy.deepcopy(env["container_images"]),
        "storage_gate": {},
        "resource_gate": {},
        "smoke_receipt": None,
        "host_packet_manifest": {
            "source_path": f"{manifest.EXPERIMENT_REL}/{manifest.HOST_PACKET_MANIFEST_REL}",
            "sha256": sha256(exp / manifest.HOST_PACKET_MANIFEST_REL),
            "bytes": (exp / manifest.HOST_PACKET_MANIFEST_REL).stat().st_size,
        },
        "host_preparation_receipt": {
            "source_path": (
                f"{manifest.EXPERIMENT_REL}/{manifest.HOST_PREPARATION_RECEIPT_REL}"
            ),
            "sha256": sha256(exp / manifest.HOST_PREPARATION_RECEIPT_REL),
            "bytes": (exp / manifest.HOST_PREPARATION_RECEIPT_REL).stat().st_size,
        },
        "tooling_verification_receipt": {},
        "gates": {
            "g0_preregistration": True,
            "g1_provenance": True,
            "g2_released_behavior": True,
            "g3_schedule_integrity": True,
            "g4_semantic_leak": True,
            "g5_live_smoke": False,
            "g7_dataset_provenance": True,
            "g8_storage_environment": True,
            "g9_resource_plan": False,
            "execution_plan": True,
            "execution_consumers": True,
            "tooling_verification": True,
            "mission_state": False,
        },
        "missing_artifacts": [manifest.SMOKE_RECEIPT_REL],
        "problem_count": 1,
        "problems": ["smoke:receipt-missing"],
    }
    pre_manifest_path = raw_dir / "pre_smoke_manifest.json"
    pre_manifest_path.write_text(json.dumps(pre_manifest, indent=1, sort_keys=True) + "\n")

    selected: dict[str, tuple[str, dict]] = {}
    for dose in manifest.BLIND_ARMS:
        candidates = sorted(
            (target, row)
            for target, row in schedule["schedules"][dose].items()
            if target.endswith("/0") and row.get("brake_frames")
        )
        selected[dose] = candidates[0]

    events = [
        {
            "event": "session_start",
            "schema": "iter135.smoke_execution.v1",
            "nonanalytic": True,
            "analytic_episode_count": 0,
            "analytic_output_root": "/datasets/nuscenes-full/sentinel-i135-outoutput",
            "smoke_output_root": "/datasets/nuscenes-full/sentinel-i135-smoke-evidence",
            "smoke_episode_root": ("/datasets/nuscenes-full/sentinel-i135-smoke-evidence/episodes"),
            "manifest_sha256": sha256(pre_manifest_path),
            "canonical_runner_sha256": sha256(exp / "run_smoke135.sh"),
            "canonical_runner_identity": "66305:1001",
            "persistent_smoke_lock": "/var/lib/sentinel/i135-smoke.lock",
            "persistent_smoke_lock_identity": "66305:1002",
            "persistent_smoke_lock_sha256": "9" * 64,
            "github_pre_smoke_authority": github_pre_smoke_authority(
                sha256(pre_manifest_path)
            ),
            "retry_policy": "one_shot_no_retry_lock_retained",
            "docker_wrapper_sha256": "a" * 64,
            "docker_binary_sha256": "b" * 64,
            "docker_binary_identity": "66305:1003",
            "python_wrapper_sha256": "c" * 64,
            "python_binary_sha256": "d" * 64,
            "python_binary_identity": "66305:1005",
            "container_control_root_identity": "66308:1004",
            "environment_receipt_sha256": sha256(raw_dir / "environment_receipt.json"),
            "schedule_sha256": sha256(exp / "dose_schedules.json"),
            "blind_patch_sha256": sha256(exp / "server_patch_blind_dose.py"),
            "runner_sha256": sha256(exp / "run_smoke135.sh"),
            "validator_sha256": sha256(exp / "validate_smoke135.py"),
            "compose_sha256": env["remote_files"]["compose_script"]["sha256"],
            "container_image_ids": image_ids,
            "gpu_identity": env["gpu"],
        }
    ]
    total_ns = 0
    for ordinal, dose in enumerate(manifest.BLIND_ARMS):
        target, row = selected[dose]
        scenario_class, sequence, _run = target.split("/")
        frames = row["brake_frames"]
        schedule_id = f"{dose}/{target}"
        start_ns = 10_000_000_000 + ordinal * 2_000_000_000
        elapsed_ns = 1_250_000_000
        end_ns = start_ns + elapsed_ns
        total_ns += elapsed_ns
        identity = {
            "ordinal": ordinal,
            "dose": dose,
            "schedule_id": schedule_id,
            "scenario_class": scenario_class,
            "sequence": sequence,
            "run": 0,
        }
        events.append(
            {
                "event": "dose_start",
                **identity,
                "runs": 1,
                "nonanalytic": True,
                "analytic_inclusion": False,
                "analytic_episode_count": 0,
                "output_root": ("/datasets/nuscenes-full/sentinel-i135-smoke-evidence/episodes"),
                "model_log_path": f"/model/i135-smoke-staging/{dose}.decisions.jsonl",
                "clock": "monotonic_ns",
                "start_ns": start_ns,
                "argv": [
                    "bash",
                    "/opt/sentinel-stack/NeuroNCAP/scripts/_docker_compose_release.sh",
                    sequence,
                    scenario_class,
                    f"--scenario-category={scenario_class}",
                    "--runs",
                    "1",
                ],
            }
        )
        events.append(
            {
                "event": "dose_finish",
                **identity,
                "end_ns": end_ns,
                "elapsed_ns": elapsed_ns,
                "clock": "monotonic_ns",
                "compose_exit_code": 0,
                "env_capture_exit_code": 0,
                "container_monitor_exit_code": 0,
                "container_cleanup_exit_code": 0,
                "container_receipts": {
                    role: hashlib.sha256(f"{ordinal}:{role}".encode()).hexdigest()
                    for role in ("renderer", "model", "ncap")
                },
                "patched_server_sha256": (
                    "b636930ab2685ea31a417ab10a4eaac055bc8cecc814e38084c706c8ace09bbf"
                ),
            }
        )

        frame_limit = max(frames) + 2
        base = [[1.25, -0.5], [2.5, 0.75]]
        decisions = [
            {
                "reset": True,
                "run": 0,
                "class": scenario_class,
                "pair": sequence,
                "dose": dose,
            }
        ]
        for frame_index in range(frame_limit):
            scheduled = frame_index in frames
            decisions.append(
                {
                    "frame": True,
                    "scheduled": scheduled,
                    "run": 0,
                    "class": scenario_class,
                    "pair": sequence,
                    "dose": dose,
                    "frame_index": frame_index,
                    "base_trajectory": base,
                    "returned_trajectory": ([[0.0, 0.0], [0.0, 0.0]] if scheduled else base),
                }
            )
            if scheduled:
                decisions.append(
                    {
                        "brake": True,
                        "run": 0,
                        "class": scenario_class,
                        "pair": sequence,
                        "dose": dose,
                        "frame_index": frame_index,
                    }
                )
        (raw_dir / f"{dose}.decisions.jsonl").write_text(
            "".join(json.dumps(item, sort_keys=True) + "\n" for item in decisions)
        )
        model_environment = {
            "PATH": "/usr/local/bin:/usr/bin",
            "SENTINEL_ENABLED": "1",
            "SENTINEL_DOSE_PAIR": f"{scenario_class}/{sequence}",
            "SENTINEL_DOSE_ID": dose,
            "SENTINEL_DOSE_SCHEDULE": "/model/dose_schedules.json",
            "SENTINEL_LOG": f"/model/i135-smoke-staging/{dose}.decisions.jsonl",
            "SENTINEL_RELEASE_K": "4",
        }
        (raw_dir / f"{dose}.model-env.bin").write_bytes(
            b"\0".join(f"{key}={value}".encode() for key, value in model_environment.items())
            + b"\0"
        )
        (raw_dir / f"{dose}.compose.log").write_text("SMOKE COMPOSE COMPLETE\n")

    events.append(
        {
            "event": "session_finish",
            "status": "complete",
            "exit_code": 0,
            "dose_invocation_count": 4,
            "analytic_episode_count": 0,
            "total_gpu_elapsed_ns": total_ns,
        }
    )
    (raw_dir / "execution.jsonl").write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in events)
    )

    validator_path = exp / "validate_smoke135.py"
    spec = importlib.util.spec_from_file_location("iter135_fixture_smoke", validator_path)
    assert spec is not None and spec.loader is not None
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    return validator.recompute_smoke_receipt(exp)


def make_fixture(tmp_path: Path, phase: str = "LAUNCH_AUTHORIZED") -> tuple[Path, Path]:
    exp = tmp_path / "iter135"
    exp.mkdir(parents=True)
    for name in manifest.REQUIRED_PAYLOAD_NAMES:
        source = SOURCE_EXP / name
        target = exp / name
        if name == "run_dose135.sh":
            target.write_text("#!/bin/bash\n# execution_blocks I135BLOCK --runs 20\n")
        elif name == "analyze_dose135.py":
            target.write_text(analyzer_source())
        elif name == "verify_tooling135.py":
            target.write_text(
                "def validate_published_receipt_structure(receipt, repo_root):\n"
                "    return []\n"
            )
        elif name == "validate_smoke135.py":
            target.write_text(
                source.read_text()
                .replace(
                    'ENV_SCHEMA = "iter135.environment_receipts.v1"',
                    'ENV_SCHEMA = "iter135.environment_receipts.v3"',
                )
                .replace(
                    'MANIFEST_SCHEMA = "iter135.launch_manifest.v1"',
                    'MANIFEST_SCHEMA = "iter135.launch_manifest.v2"',
                )
            )
        else:
            target.write_bytes(source.read_bytes())

    schedule_path = exp / "dose_schedules.json"
    schedule = json.loads(schedule_path.read_text())
    raw_rows = schedule.get("schedules")
    if isinstance(raw_rows, dict) and set(raw_rows) != set(manifest.BLIND_ARMS):
        nested = {dose: {} for dose in manifest.BLIND_ARMS}
        for key, row in raw_rows.items():
            dose, target = key.split("/", 1)
            nested[dose][target] = row
        schedule["schedules"] = nested
        schedule_path.write_text(json.dumps(schedule))

    state_path = tmp_path / "MISSION_STATE.json"
    state_path.write_text(json.dumps(mission_state(phase)))
    (exp / manifest.TOOLING_RECEIPT_REL).write_text(
        json.dumps(
            {
                "schema": manifest.EXPECTED_TOOLING_SCHEMA,
                "verdict": manifest.EXPECTED_TOOLING_VERDICT,
                "problem_count": 0,
                "problems": [],
            }
        )
    )
    write_host_evidence(exp, state_path)
    env = environment_receipt(exp)
    (exp / manifest.ENV_RECEIPT_REL).write_text(json.dumps(env))
    smoke = smoke_receipt(exp, env)
    validator_path = exp / "validate_smoke135.py"
    validator_spec = importlib.util.spec_from_file_location(
        "iter135_fixture_smoke_bundle", validator_path
    )
    assert validator_spec is not None and validator_spec.loader is not None
    validator = importlib.util.module_from_spec(validator_spec)
    validator_spec.loader.exec_module(validator)
    receipt_bytes = validator.canonical_smoke_receipt_bytes(smoke)
    (exp / manifest.SMOKE_RECEIPT_REL).write_bytes(receipt_bytes)
    (exp / manifest.SMOKE_SUMMARY_REL).write_bytes(
        validator.render_smoke_summary(smoke, receipt_bytes)
    )
    return exp, state_path


def build_ready(tmp_path: Path, *, phase: str = "LAUNCH_AUTHORIZED") -> dict:
    exp, state_path = make_fixture(tmp_path, phase)
    return manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )


def test_execution_plan_is_exact_amended_pair_major_contract() -> None:
    blocks, cells = manifest.execution_plan()

    assert manifest.validate_execution_plan(blocks, cells) == []
    assert len(blocks) == 120
    assert len(cells) == 2400
    assert set(blocks[0]) == {
        "ordinal",
        "pair_index",
        "temporal_position",
        "arm_id",
        "scenario_class",
        "sequence",
        "run_indices",
    }
    assert set(cells[0]) == {
        "ordinal",
        "block_ordinal",
        "pair_index",
        "temporal_position",
        "arm_id",
        "scenario_class",
        "sequence",
        "run_index",
    }
    assert blocks[0] == {
        "ordinal": 0,
        "pair_index": 0,
        "temporal_position": 0,
        "arm_id": "off_baseline",
        "scenario_class": "stationary",
        "sequence": "0099",
        "run_indices": list(range(20)),
    }
    assert blocks[6]["arm_id"] == "released_union_semantic_reference"
    assert blocks[6]["pair_index"] == 1
    assert [cell["run_index"] for cell in cells[:20]] == list(range(20))
    assert all(cell["arm_id"] == "off_baseline" for cell in cells[:20])


def test_execution_plan_rejects_one_block_arm_mutation() -> None:
    blocks, cells = manifest.execution_plan()
    mutated = copy.deepcopy(blocks)
    mutated[0]["arm_id"] = "blind_2_0x"

    assert "execution:block-arm-order:0" in manifest.validate_execution_plan(mutated, cells)


def test_dataset_generator_contract_cannot_self_declare_archive_or_root_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archives = dict(manifest.EXPECTED_DATASET_ARCHIVES)
    archives.pop("v1.0-trainval10_blobs.tgz")
    archives["self-declared.tgz"] = ("f" * 64, 41_727_447_974)
    monkeypatch.setattr(manifest, "EXPECTED_DATASET_ARCHIVES", archives)
    monkeypatch.setattr(manifest, "EXPECTED_DATASET_ROOT", "/datasets/nuscenes")

    problems = manifest.dataset_contract_problems()

    assert "dataset-contract:archive-set" in problems
    assert "dataset-contract:sha256" in problems


def test_dataset_generator_replays_all_committed_iter28_archive_proofs() -> None:
    assert manifest.dataset_contract_problems() == []
    assert manifest.iter28_dataset_proof_problems(REPO) == []


def test_publication_authority_rejects_red_or_unbound_matrix_check() -> None:
    commit = "a" * 40
    authority = publication_authority(commit)
    assert manifest.validate_publication_authority(
        authority, expected_commit=commit, expected_artifacts=[]
    ) == []

    red = copy.deepcopy(authority)
    red["checks"][0]["conclusion"] = "failure"
    assert "publication-authority:check:check (3.10):conclusion" in (
        manifest.validate_publication_authority(
            red, expected_commit=commit, expected_artifacts=[]
        )
    )

    wrong_head = copy.deepcopy(authority)
    wrong_head["checks"][1]["head_sha"] = "b" * 40
    assert "publication-authority:check:check (3.11):head-sha" in (
        manifest.validate_publication_authority(
            wrong_head, expected_commit=commit, expected_artifacts=[]
        )
    )


def test_publication_authority_requires_persisted_git_blob_identity_and_mode() -> None:
    commit = "a" * 40
    artifact = {
        "path": f"{manifest.EXPERIMENT_REL}/host_packet_manifest.json",
        "sha256": "b" * 64,
        "bytes": 123,
        "git_blob_oid": "c" * 40,
        "git_mode": "100644",
    }
    authority = publication_authority(commit, [artifact])

    assert manifest.validate_publication_authority(authority) == []
    for field in ("git_blob_oid", "git_mode"):
        hostile = copy.deepcopy(authority)
        del hostile["artifacts"][0][field]
        assert "publication-authority:artifacts" in (
            manifest.validate_publication_authority(hostile)
        )
    hostile_oid = copy.deepcopy(authority)
    hostile_oid["artifacts"][0]["git_blob_oid"] = "d" * 64
    assert "publication-authority:artifacts" in (
        manifest.validate_publication_authority(hostile_oid)
    )
    hostile_mode = copy.deepcopy(authority)
    hostile_mode["artifacts"][0]["git_mode"] = "100664"
    assert "publication-authority:artifacts" in (
        manifest.validate_publication_authority(hostile_mode)
    )


def test_docker_runtime_receipt_rejects_client_or_daemon_drift() -> None:
    runtime = docker_runtime_receipt()
    assert manifest.validate_docker_runtime_receipt(runtime) == []

    binary_drift = copy.deepcopy(runtime)
    binary_drift["client"]["physical_path"] = "/tmp/docker"
    assert "environment:docker-runtime:client:realpath-drift" in (
        manifest.validate_docker_runtime_receipt(binary_drift)
    )

    daemon_drift = copy.deepcopy(runtime)
    daemon_drift["daemon"]["version"]["version"] = "28.0.0"
    assert "environment:docker-runtime:daemon-version-drift" in (
        manifest.validate_docker_runtime_receipt(daemon_drift)
    )

    architecture_drift = copy.deepcopy(runtime)
    architecture_drift["daemon"]["version"]["arch"] = "arm64"
    assert "environment:docker-runtime:daemon-arch-drift" in (
        manifest.validate_docker_runtime_receipt(architecture_drift)
    )


def test_all_green_receipts_and_authorized_state_are_required_for_launch(tmp_path: Path) -> None:
    report = build_ready(tmp_path)

    assert report["schema"] == "iter135.launch_manifest.v2"
    assert report["verdict"] == manifest.READY_VERDICT
    assert report["launch_authorized"] is True
    assert report["problem_count"] == 0
    assert report["problems"] == []
    assert all(report["gates"].values())
    assert report["gates"]["tooling_verification"] is True
    assert report["tooling_verification_receipt"] is not None
    assert report["host_packet_manifest"] == report["hash_bound_files"][
        manifest.HOST_PACKET_MANIFEST_REL
    ]
    assert report["host_preparation_receipt"] == report["hash_bound_files"][
        manifest.HOST_PREPARATION_RECEIPT_REL
    ]
    assert report["planned_blocks"] == 120
    assert report["planned_episodes"] == 2400
    assert report["design"]["retry_policy"] == ("no_automatic_retry_abort_on_first_block_failure")
    assert report["design"]["allowed_retries"] == 0
    assert set(manifest.REQUIRED_PAYLOAD_NAMES) <= set(report["hash_bound_files"])
    assert len(report["remote_artifacts"]) == len(manifest.EXPECTED_REMOTE_FILES) == 82
    assert {row["role"] for row in report["remote_artifacts"]} == set(
        manifest.EXPECTED_REMOTE_FILES
    )
    assert set(report["container_images"]) == set(manifest.EXPECTED_IMAGE_IDS)
    assert report["gates"]["g7_dataset_provenance"] is True
    assert report["dataset_receipt"] == report["environment_receipts"]["dataset"]
    assert report["dataset_receipt"]["contract_sha256"] == (
        manifest.EXPECTED_DATASET_CONTRACT_SHA256
    )
    assert len(report["dataset_receipt"]["archives"]) == 11
    assert (
        sum(row["bytes"] for row in report["dataset_receipt"]["archives"].values())
        == manifest.EXPECTED_DATASET_ARCHIVE_TOTAL_BYTES
    )


def test_non_authorized_mission_phase_cannot_be_overridden_by_green_evidence(
    tmp_path: Path,
) -> None:
    report = build_ready(tmp_path, phase="TOOLING_FROZEN_PREFLIGHT_REQUIRED")

    assert report["launch_authorized"] is False
    assert report["verdict"] == manifest.INCOMPLETE_VERDICT
    assert report["gates"]["mission_state"] is False
    assert report["mission_phase"] == manifest.PREFLIGHT_MISSION_PHASE
    assert not any(problem.startswith("mission-state:phase:") for problem in report["problems"])


def test_frozen_host_packet_and_smoke_replay_survive_launch_state_transition(
    tmp_path: Path,
) -> None:
    exp, state_path = make_fixture(tmp_path, phase=manifest.PREFLIGHT_MISSION_PHASE)
    packet_before = (exp / manifest.HOST_PACKET_MANIFEST_REL).read_bytes()
    smoke_before = (exp / manifest.SMOKE_RECEIPT_REL).read_bytes()

    state_path.write_text(json.dumps(mission_state(manifest.EXPECTED_MISSION_PHASE)))
    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert report["verdict"] == manifest.READY_VERDICT
    assert report["launch_authorized"] is True
    assert report["problems"] == []
    assert (exp / manifest.HOST_PACKET_MANIFEST_REL).read_bytes() == packet_before
    assert (exp / manifest.SMOKE_RECEIPT_REL).read_bytes() == smoke_before


def test_unknown_mission_phase_is_rejected_as_a_problem(tmp_path: Path) -> None:
    report = build_ready(tmp_path, phase="UNREVIEWED_PHASE")

    assert report["launch_authorized"] is False
    assert report["gates"]["mission_state"] is False
    assert any(problem.startswith("mission-state:phase:") for problem in report["problems"])


def test_mission_phase_actions_are_exact_and_cannot_claim_authority(tmp_path: Path) -> None:
    exp, state_path = make_fixture(tmp_path)
    state = json.loads(state_path.read_text())
    state["next_program"]["authorized_actions"] = ["launch anything"]
    state["next_program"]["forbidden_actions"] = []
    state_path.write_text(json.dumps(state))

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert "mission-state:authorized-actions" in report["problems"]
    assert "mission-state:forbidden-actions" in report["problems"]
    assert report["launch_authorized"] is False


@pytest.mark.parametrize(
    "mutation",
    ["missing", "isolated-from", "recovery-source", "extra-field"],
)
def test_workspace_boundary_is_exact_and_cannot_cross_into_aweb(
    tmp_path: Path,
    mutation: str,
) -> None:
    exp, state_path = make_fixture(tmp_path)
    state = json.loads(state_path.read_text())
    if mutation == "missing":
        del state["workspace_boundary"]
    elif mutation == "isolated-from":
        state["workspace_boundary"]["isolated_from"] = (
            "/Users/danielwahnich/workspace/sentinel"
        )
    elif mutation == "recovery-source":
        state["workspace_boundary"]["recovery_sources"].append(
            "/Users/danielwahnich/workspace/aweb/MISSION_STATE.json"
        )
    else:
        state["workspace_boundary"]["aweb_bootstrap"] = "pnpm aweb:context"
    state_path.write_text(json.dumps(state))

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert "mission-state:workspace-boundary" in report["problems"]
    assert report["gates"]["mission_state"] is False
    assert report["launch_authorized"] is False


def test_mission_state_rejects_extra_top_level_field(tmp_path: Path) -> None:
    exp, state_path = make_fixture(tmp_path)
    state = json.loads(state_path.read_text())
    state["aweb_state"] = "/Users/danielwahnich/workspace/aweb/MISSION_STATE.json"
    state_path.write_text(json.dumps(state))

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert "mission-state:field-set" in report["problems"]
    assert report["gates"]["mission_state"] is False


@pytest.mark.parametrize(
    ("field", "value", "problem"),
    [
        ("claim_state", {"production_readiness": "ESTABLISHED"}, "mission-state:claim-state"),
        ("deprecated_pending_hypotheses", [], "mission-state:deprecated-hypotheses"),
        ("paper_state", {"status": "SUBMISSION_READY"}, "mission-state:paper-state"),
    ],
)
def test_manifest_consumer_freezes_exact_claim_paper_and_deprecated_state(
    field: str, value: object, problem: str
) -> None:
    state = mission_state()
    state[field] = value

    assert problem in manifest.validate_mission_state(state)


@pytest.mark.parametrize("payload", ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'])
def test_manifest_json_loader_rejects_duplicate_and_nonfinite_state(
    tmp_path: Path, payload: str
) -> None:
    path = tmp_path / "MISSION_STATE.json"
    path.write_text(payload)
    problems: list[str] = []

    assert manifest._load_json(path, "MISSION_STATE.json", problems) is None
    assert problems and problems[0].startswith("invalid-json:MISSION_STATE.json:ValueError")


def test_pre_smoke_phase_has_exactly_one_missing_evidence_problem(tmp_path: Path) -> None:
    exp, state_path = make_fixture(tmp_path, phase=manifest.PREFLIGHT_MISSION_PHASE)
    (exp / manifest.SMOKE_RECEIPT_REL).unlink()

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert report["launch_authorized"] is False
    assert report["mission_phase"] == manifest.PREFLIGHT_MISSION_PHASE
    assert report["missing_artifacts"] == [manifest.SMOKE_RECEIPT_REL]
    assert report["problem_count"] == 1
    assert report["problems"] == ["smoke:receipt-missing"]


def test_missing_future_evidence_is_reported_without_fabricated_receipts(tmp_path: Path) -> None:
    exp = tmp_path / "iter135"
    exp.mkdir()
    (exp / "HYPOTHESIS.md").write_bytes((SOURCE_EXP / "HYPOTHESIS.md").read_bytes())
    state_path = tmp_path / "MISSION_STATE.json"
    state_path.write_text(json.dumps(mission_state()))

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert report["launch_authorized"] is False
    assert manifest.ENV_RECEIPT_REL in report["missing_artifacts"]
    assert manifest.SMOKE_RECEIPT_REL in report["missing_artifacts"]
    assert manifest.TOOLING_RECEIPT_REL in report["missing_artifacts"]
    assert report["remote_artifacts"] == []
    assert report["dataset_receipt"] is None
    assert report["container_images"] is None
    assert report["smoke_receipt"] is None


@pytest.mark.parametrize("mutation", ["packet-byte", "packet-link", "embedded-evidence"])
def test_host_packet_and_preparation_cross_binding_fail_closed(
    tmp_path: Path, mutation: str
) -> None:
    exp, state_path = make_fixture(tmp_path)
    packet_path = exp / manifest.HOST_PACKET_MANIFEST_REL
    preparation_path = exp / manifest.HOST_PREPARATION_RECEIPT_REL
    env_path = exp / manifest.ENV_RECEIPT_REL
    if mutation == "packet-byte":
        packet = json.loads(packet_path.read_text())
        packet["files"]["authorize_launch135.py"]["sha256"] = "0" * 64
        packet_path.write_text(json.dumps(packet, sort_keys=True) + "\n")
    elif mutation == "packet-link":
        preparation = json.loads(preparation_path.read_text())
        preparation["packet_manifest_sha256"] = "0" * 64
        preparation_path.write_text(json.dumps(preparation, sort_keys=True) + "\n")
    else:
        env = json.loads(env_path.read_text())
        env["host_preparation"]["evidence"]["host"] = "forged-host"
        env_path.write_text(json.dumps(env, sort_keys=True) + "\n")

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert report["launch_authorized"] is False
    assert any(
        problem.startswith(("host-packet:", "host-preparation:", "environment:"))
        for problem in report["problems"]
    )


def test_environment_image_or_checkpoint_drift_fails_closed(tmp_path: Path) -> None:
    exp, state_path = make_fixture(tmp_path)
    env_path = exp / manifest.ENV_RECEIPT_REL
    env = json.loads(env_path.read_text())
    env["container_images"]["uniad:latest"]["image_id"] = "sha256:" + "f" * 64
    env["remote_files"]["checkpoint"]["sha256"] = "e" * 64
    env_path.write_text(json.dumps(env))

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert report["launch_authorized"] is False
    assert "environment:image:uniad:latest:id-drift" in report["problems"]
    assert "environment:remote-file:checkpoint:expected-sha256" in report["problems"]


def test_tooling_verification_receipt_claims_fail_closed(tmp_path: Path) -> None:
    exp, state_path = make_fixture(tmp_path)
    receipt_path = exp / manifest.TOOLING_RECEIPT_REL
    receipt = json.loads(receipt_path.read_text())
    receipt["verdict"] = "FORGED_GREEN"
    receipt_path.write_text(json.dumps(receipt))

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert report["launch_authorized"] is False
    assert report["gates"]["tooling_verification"] is False
    assert "tooling-verification:verdict" in report["problems"]


@pytest.mark.parametrize(
    ("verifier_source", "expected_problem"),
    [
        (
            "def validate_published_receipt_structure(receipt, repo_root):\n"
            "    return ['published-structure-bad']\n"
            "def validate_receipt(receipt, repo_root):\n"
            "    return []\n",
            "tooling-verification:replay:0:published-structure-bad",
        ),
        (
            "def validate_receipt(receipt, repo_root):\n"
            "    return []\n",
            "tooling-verification:replay-error:AttributeError",
        ),
    ],
)
def test_tooling_receipt_uses_published_structure_validator_and_fails_closed(
    tmp_path: Path,
    verifier_source: str,
    expected_problem: str,
) -> None:
    exp, state_path = make_fixture(tmp_path)
    (exp / "verify_tooling135.py").write_text(verifier_source)

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert report["launch_authorized"] is False
    assert report["gates"]["tooling_verification"] is False
    assert expected_problem in report["problems"]


def test_environment_repository_head_and_normalized_status_drift_fail_closed(
    tmp_path: Path,
) -> None:
    exp, state_path = make_fixture(tmp_path)
    env_path = exp / manifest.ENV_RECEIPT_REL
    env = json.loads(env_path.read_text())
    env["repositories"]["uniad"]["head"] = "f" * 40
    env["repositories"]["uniad"]["dirty_tracked_paths"].append("inference/server.py")
    env["repositories"]["neurad"]["staged_paths"] = ["Dockerfile"]
    env["repositories"]["neurad"]["required_untracked_paths"] = []
    env_path.write_text(json.dumps(env))

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert report["launch_authorized"] is False
    assert "environment:repository:uniad:head" in report["problems"]
    assert "environment:repository:uniad:dirty_tracked_paths" in report["problems"]
    assert "environment:repository:neurad:staged_paths" in report["problems"]
    assert "environment:repository:neurad:required_untracked_paths" in report["problems"]
    assert "environment:required-untracked-set" in report["problems"]


def test_environment_load_bearing_runtime_file_drift_fails_closed(tmp_path: Path) -> None:
    exp, state_path = make_fixture(tmp_path)
    env_path = exp / manifest.ENV_RECEIPT_REL
    env = json.loads(env_path.read_text())
    env["remote_files"]["neuroncap_engine"]["sha256"] = "e" * 64
    env["remote_files"]["uniad_runner"]["bytes"] += 1
    env_path.write_text(json.dumps(env))

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert "environment:remote-file:neuroncap_engine:expected-sha256" in report["problems"]
    assert "environment:remote-file:uniad_runner:expected-bytes" in report["problems"]


def test_environment_scenario_identity_drift_fails_closed(tmp_path: Path) -> None:
    exp, state_path = make_fixture(tmp_path)
    env_path = exp / manifest.ENV_RECEIPT_REL
    env = json.loads(env_path.read_text())
    env["remote_files"]["scenario:side/0921"]["sha256"] = "d" * 64
    env_path.write_text(json.dumps(env))

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert "environment:remote-file:scenario:side/0921:expected-sha256" in report["problems"]


def test_environment_renderer_triple_drift_fails_closed(tmp_path: Path) -> None:
    exp, state_path = make_fixture(tmp_path)
    env_path = exp / manifest.ENV_RECEIPT_REL
    env = json.loads(env_path.read_text())
    env["remote_files"]["renderer:0346:checkpoint"]["bytes"] -= 8
    env_path.write_text(json.dumps(env))

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert "environment:remote-file:renderer:0346:checkpoint:expected-bytes" in report["problems"]


def test_environment_rejects_any_noncanonical_patched_compose(tmp_path: Path) -> None:
    exp, state_path = make_fixture(tmp_path)
    env_path = exp / manifest.ENV_RECEIPT_REL
    env = json.loads(env_path.read_text())
    env["remote_files"]["compose_script"]["sha256"] = "d" * 64
    env_path.write_text(json.dumps(env))

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert report["launch_authorized"] is False
    assert "environment:compose-output-sha256" in report["problems"]


def test_environment_dedicated_storage_identity_drift_fails_closed(tmp_path: Path) -> None:
    exp, state_path = make_fixture(tmp_path)
    env_path = exp / manifest.ENV_RECEIPT_REL
    env = json.loads(env_path.read_text())
    env["storage"]["mount_source"] = "/dev/root"
    env["storage"]["mount_uuid"] = "00000000-0000-0000-0000-000000000000"
    env["storage"]["filesystem_is_symlink"] = True
    env_path.write_text(json.dumps(env))

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert "environment:storage-identity:mount_source" in report["problems"]
    assert "environment:storage-identity:mount_uuid" in report["problems"]
    assert "environment:storage-identity:filesystem_is_symlink" in report["problems"]


def test_dataset_receipt_cannot_self_declare_set_path_digest_version_or_device(
    tmp_path: Path,
) -> None:
    exp, state_path = make_fixture(tmp_path)
    env_path = exp / manifest.ENV_RECEIPT_REL
    env = json.loads(env_path.read_text())
    dataset = env["dataset"]
    archive_name = "v1.0-trainval10_blobs.tgz"
    metadata_name = manifest.EXPECTED_DATASET_METADATA_FILES[0]
    map_name = manifest.EXPECTED_DATASET_MAP_ANCHORS[0]
    dataset["contract_sha256"] = "f" * 64
    dataset["identity"]["dataset_version"] = "v1.0-mini"
    dataset["identity"]["mount_uuid"] = "00000000-0000-0000-0000-000000000000"
    dataset["identity"]["dataset_st_dev"] = 1
    dataset["archives"][archive_name].update(
        {
            "path": f"/datasets/nuscenes/{archive_name}",
            "sha256": "e" * 64,
            "bytes": 1,
        }
    )
    dataset["metadata_json"].pop(metadata_name)
    dataset["metadata_json"]["self-declared.json"] = {
        "path": "/datasets/nuscenes-full/v1.0-trainval/self-declared.json",
        "sha256": "d" * 64,
        "bytes": 2,
    }
    dataset["map_anchors"][map_name]["path"] = f"/tmp/{map_name}"
    dataset["receipt_payload_sha256"] = manifest._dataset_receipt_payload_sha256(dataset)
    env_path.write_text(json.dumps(env))

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert report["launch_authorized"] is False
    assert report["gates"]["g7_dataset_provenance"] is False
    for problem in (
        "environment:dataset:contract-sha256",
        "environment:dataset:identity:dataset_version",
        "environment:dataset:identity:mount_uuid",
        "environment:dataset:device-identity",
        "environment:dataset:storage-device-link",
        f"environment:dataset:archive:{archive_name}:path",
        f"environment:dataset:archive:{archive_name}:expected-sha256",
        f"environment:dataset:archive:{archive_name}:expected-bytes",
        "environment:dataset:metadata-set",
        f"environment:dataset:metadata:{metadata_name}:missing",
        f"environment:dataset:map:{map_name}:path",
    ):
        assert problem in report["problems"]


def test_dataset_receipt_payload_digest_detects_unbound_extracted_file_drift(
    tmp_path: Path,
) -> None:
    exp, state_path = make_fixture(tmp_path)
    env_path = exp / manifest.ENV_RECEIPT_REL
    env = json.loads(env_path.read_text())
    metadata_name = manifest.EXPECTED_DATASET_METADATA_FILES[-1]
    env["dataset"]["metadata_json"][metadata_name]["sha256"] = "c" * 64
    env_path.write_text(json.dumps(env))

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert "environment:dataset:receipt-payload-sha256" in report["problems"]


def test_environment_gpu_identity_schema_drift_fails_closed(tmp_path: Path) -> None:
    exp, state_path = make_fixture(tmp_path)
    env_path = exp / manifest.ENV_RECEIPT_REL
    env = json.loads(env_path.read_text())
    del env["gpu"]["uuid"]
    env["unexpected_field"] = "must-not-be-accepted"
    env_path.write_text(json.dumps(env))

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert report["launch_authorized"] is False
    assert "environment:field-set" in report["problems"]
    assert "environment:gpu-field-set" in report["problems"]


def test_environment_exact_host_and_gpu_identity_drift_fails_closed(tmp_path: Path) -> None:
    exp, state_path = make_fixture(tmp_path)
    env_path = exp / manifest.ENV_RECEIPT_REL
    env = json.loads(env_path.read_text())
    env["host"] = "evil-gpu"
    env["gpu"].update(
        {
            "uuid": "GPU-ffffffff-ffff-ffff-ffff-ffffffffffff",
            "driver_version": "1.2.3",
            "memory_total_mib": 1,
        }
    )
    env_path.write_text(json.dumps(env))

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    for problem in (
        "environment:host",
        "environment:gpu-uuid",
        "environment:gpu-driver",
        "environment:gpu-memory",
    ):
        assert problem in report["problems"]


@pytest.mark.parametrize(
    ("started", "captured"),
    [
        ("Z", "Z"),
        ("2026-07-16T10:00:01Z", "2026-07-16T10:00:00Z"),
        ("2026-07-16T09:59:00.1Z", "2026-07-16T10:00:00Z"),
    ],
)
def test_environment_timestamps_are_canonical_and_ordered(
    tmp_path: Path, started: str, captured: str
) -> None:
    exp, state_path = make_fixture(tmp_path)
    env_path = exp / manifest.ENV_RECEIPT_REL
    env = json.loads(env_path.read_text())
    env["capture_started_at_utc"] = started
    env["captured_at_utc"] = captured
    env_path.write_text(json.dumps(env))

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert any(
        problem in report["problems"]
        for problem in ("environment:captured-at", "environment:capture-started-at")
    )


def test_environment_box_and_storage_device_claims_fail_closed(tmp_path: Path) -> None:
    exp, state_path = make_fixture(tmp_path)
    env_path = exp / manifest.ENV_RECEIPT_REL
    env = json.loads(env_path.read_text())
    env["box"]["known_evaluation_processes"] = 1
    env["storage_devices"] = {
        "filesystem_st_dev": -1,
        "mount_st_dev": -1,
        "root_st_dev": 2,
    }
    env_path.write_text(json.dumps(env))

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert "environment:box-idle" in report["problems"]
    assert "environment:storage-device-identity" in report["problems"]


def test_stored_smoke_claim_cannot_override_fresh_recomputation(tmp_path: Path) -> None:
    exp, state_path = make_fixture(tmp_path)
    smoke_path = exp / manifest.SMOKE_RECEIPT_REL
    smoke = json.loads(smoke_path.read_text())
    smoke["dose_results"]["blind_1_0x"]["observed_brake_frames"] = [999]
    smoke_path.write_text(json.dumps(smoke))

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert report["launch_authorized"] is False
    assert "smoke:recomputation-mismatch" in report["problems"]


def test_raw_smoke_mutation_is_recomputed_and_fails_closed(tmp_path: Path) -> None:
    exp, state_path = make_fixture(tmp_path)
    decision_path = exp / "smoke-evidence/raw/blind_1_0x.decisions.jsonl"
    rows = [json.loads(line) for line in decision_path.read_text().splitlines()]
    frame = next(row for row in rows if row.get("frame") and row.get("scheduled") is False)
    frame["returned_trajectory"] = [[999.0, 0.0], [999.0, 0.0]]
    decision_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert report["launch_authorized"] is False
    assert "smoke:recomputation-mismatch" in report["problems"]
    assert "smoke:dose:blind_1_0x:pass-through" in report["problems"]


def test_final_manifest_requires_exact_generated_smoke_summary(tmp_path: Path) -> None:
    exp, state_path = make_fixture(tmp_path)
    summary_path = exp / manifest.SMOKE_SUMMARY_REL
    summary_path.unlink()

    missing = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )
    assert missing["launch_authorized"] is False
    assert "smoke:summary-missing" in missing["problems"]
    assert manifest.SMOKE_SUMMARY_REL in missing["missing_artifacts"]

    exp, state_path = make_fixture(tmp_path / "mutated")
    summary_path = exp / manifest.SMOKE_SUMMARY_REL
    summary_path.write_bytes(summary_path.read_bytes() + b"\n")
    mutated = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )
    assert mutated["launch_authorized"] is False
    assert "smoke:summary-mismatch" in mutated["problems"]


def test_manifest_is_deterministic_and_build_does_not_write_launch_file(tmp_path: Path) -> None:
    exp, state_path = make_fixture(tmp_path)
    kwargs = {
        "repo_root": REPO,
        "experiment_dir": exp,
        "mission_state_path": state_path,
        "git_provenance": ready_git_receipt(),
    }

    first = manifest.build_manifest(**kwargs)
    second = manifest.build_manifest(**kwargs)

    assert first == second
    assert not (exp / "launch_manifest.json").exists()


def test_per_cell_launcher_contract_is_rejected_even_with_other_green_receipts(
    tmp_path: Path,
) -> None:
    exp, state_path = make_fixture(tmp_path)
    (exp / "run_dose135.sh").write_text(
        "#!/bin/bash\n# execution_cells I135PAIR --runs 1 --run-index 0\n"
    )

    report = manifest.build_manifest(
        repo_root=REPO,
        experiment_dir=exp,
        mission_state_path=state_path,
        git_provenance=ready_git_receipt(),
    )

    assert report["launch_authorized"] is False
    assert "consumer:launcher-missing:execution_blocks" in report["problems"]
    assert "consumer:launcher-missing:I135BLOCK" in report["problems"]
    assert "consumer:launcher-missing:--runs 20" in report["problems"]
