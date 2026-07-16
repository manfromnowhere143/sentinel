from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import subprocess
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]
SOURCE_EXP = REPO / "experiments/iter135_neuroncap_blind_braking_dose_response"
VALIDATOR_PATH = SOURCE_EXP / "validate_smoke135.py"
RUNNER_PATH = SOURCE_EXP / "run_smoke135.sh"
MANIFEST_TOOL_PATH = SOURCE_EXP / "make_launch_manifest.py"
SPEC = importlib.util.spec_from_file_location("iter135_smoke_validator", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
smoke = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smoke)
MANIFEST_SPEC = importlib.util.spec_from_file_location(
    "iter135_smoke_manifest_contract", MANIFEST_TOOL_PATH
)
assert MANIFEST_SPEC is not None and MANIFEST_SPEC.loader is not None
manifest_contract = importlib.util.module_from_spec(MANIFEST_SPEC)
MANIFEST_SPEC.loader.exec_module(manifest_contract)


DOSE_FRAMES = {
    "blind_0_5x": [2],
    "blind_1_0x": [1, 2],
    "blind_1_5x": [1, 2, 3],
    "blind_2_0x": [0, 1, 2, 3],
}
TARGET = "frontal/0103/0"
IMAGE_IDS = {
    **manifest_contract.EXPECTED_IMAGE_IDS,
}


def docker_wrapper_payload() -> str:
    match = re.search(
        r"payload = r'''(#!/bin/bash\n.*?)'''\ndescriptor = os\.open",
        RUNNER_PATH.read_text(),
        flags=re.DOTALL,
    )
    assert match is not None
    return match.group(1)


def dataset_receipt() -> dict[str, object]:
    receipt: dict[str, object] = {
        "schema": manifest_contract.EXPECTED_DATASET_SCHEMA,
        "contract_sha256": manifest_contract.EXPECTED_DATASET_CONTRACT_SHA256,
        "proof_basis": manifest_contract.EXPECTED_DATASET_PROOF_BASIS,
        "identity": {
            "dataset_root": manifest_contract.EXPECTED_DATASET_ROOT,
            "dataset_realpath": manifest_contract.EXPECTED_DATASET_ROOT,
            "dataset_is_symlink": False,
            "dataset_version": manifest_contract.EXPECTED_DATASET_VERSION,
            "archive_root": manifest_contract.EXPECTED_DATASET_ARCHIVE_ROOT,
            "archive_realpath": manifest_contract.EXPECTED_DATASET_ARCHIVE_ROOT,
            "archive_is_symlink": False,
            "metadata_root": manifest_contract.EXPECTED_DATASET_METADATA_ROOT,
            "metadata_realpath": manifest_contract.EXPECTED_DATASET_METADATA_ROOT,
            "metadata_is_symlink": False,
            "map_root": manifest_contract.EXPECTED_DATASET_MAP_ROOT,
            "map_realpath": manifest_contract.EXPECTED_DATASET_MAP_ROOT,
            "map_is_symlink": False,
            **manifest_contract.EXPECTED_DATASET_MOUNT,
            "dataset_st_dev": 66308,
            "mount_st_dev": 66308,
            "root_st_dev": 66305,
        },
        "archives": {
            name: {
                "path": f"{manifest_contract.EXPECTED_DATASET_ARCHIVE_ROOT}/{name}",
                "sha256": digest,
                "bytes": byte_count,
            }
            for name, (digest, byte_count) in manifest_contract.EXPECTED_DATASET_ARCHIVES.items()
        },
        "metadata_json": {
            name: {
                "path": f"{manifest_contract.EXPECTED_DATASET_METADATA_ROOT}/{name}",
                "sha256": hashlib.sha256(f"metadata:{name}".encode()).hexdigest(),
                "bytes": len(name) + 1,
            }
            for name in manifest_contract.EXPECTED_DATASET_METADATA_FILES
        },
        "map_anchors": {
            name: {
                "path": f"{manifest_contract.EXPECTED_DATASET_MAP_ROOT}/{name}",
                "sha256": hashlib.sha256(f"map:{name}".encode()).hexdigest(),
                "bytes": len(name) + 1,
            }
            for name in manifest_contract.EXPECTED_DATASET_MAP_ANCHORS
        },
    }
    receipt["receipt_payload_sha256"] = manifest_contract._dataset_receipt_payload_sha256(
        receipt
    )
    return receipt


COMPOSE_SHA = manifest_contract.EXPECTED_COMPOSE_OUTPUT_SHA256


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def decision_rows(dose: str, expected_frames: list[int]) -> list[dict]:
    rows = [
        {
            "reset": True,
            "run": 0,
            "class": "frontal",
            "pair": "0103",
            "dose": dose,
        }
    ]
    base = [[1.25, -0.5], [2.5, 0.75]]
    for frame_index in range(5):
        scheduled = frame_index in expected_frames
        rows.append(
            {
                "frame": True,
                "scheduled": scheduled,
                "run": 0,
                "class": "frontal",
                "pair": "0103",
                "dose": dose,
                "frame_index": frame_index,
                "base_trajectory": base,
                "returned_trajectory": (
                    [[0.0, 0.0], [0.0, 0.0]] if scheduled else base
                ),
            }
        )
        if scheduled:
            rows.append(
                {
                    "brake": True,
                    "run": 0,
                    "class": "frontal",
                    "pair": "0103",
                    "dose": dose,
                    "frame_index": frame_index,
                }
            )
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def preflight_mission_state() -> dict[str, object]:
    return {
        "schema": smoke.MISSION_STATE_SCHEMA,
        "canonical_repository": smoke.CANONICAL_REPOSITORY,
        "workspace_boundary": json.loads(json.dumps(smoke.WORKSPACE_BOUNDARY)),
        "trunk": "master",
        "current_completed_iteration": 134,
        "current_result": (
            "experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md"
        ),
        "current_verdict": "PLACEBO_HARM_OR_NULL",
        "run_state": "IDLE",
        "active_hypothesis": (
            "experiments/iter135_neuroncap_blind_braking_dose_response/HYPOTHESIS.md"
        ),
        "next_program": json.loads(json.dumps(smoke.PREFLIGHT_PROGRAM)),
        "claim_state": {},
        "deprecated_pending_hypotheses": [],
        "paper_state": {},
        "storage_gate": json.loads(json.dumps(smoke.MISSION_STORAGE_GATE)),
    }


def make_fixture(tmp_path: Path) -> Path:
    exp = tmp_path / "iter135"
    raw = exp / smoke.RAW_REL
    raw.mkdir(parents=True)
    write_json(exp / "MISSION_STATE.json", preflight_mission_state())

    schedule = {
        "schema": "iter135.nested_dose_schedules.v1",
        "verdict": "NESTED_DOSE_SCHEDULES_OK",
        "problem_count": 0,
        "problems": [],
        "schedules": {
            dose: {
                TARGET: {
                    "dose_id": dose,
                    "target_class": "frontal",
                    "target_seq": "0103",
                    "target_run": 0,
                    "brake_frames": frames,
                }
            }
            for dose, frames in DOSE_FRAMES.items()
        },
    }
    write_json(exp / "dose_schedules.json", schedule)
    (exp / "server_patch_blind_dose.py").write_text("# frozen blind patch\n")
    (exp / "run_smoke135.sh").write_bytes(RUNNER_PATH.read_bytes())
    (exp / "validate_smoke135.py").write_bytes(VALIDATOR_PATH.read_bytes())

    dataset = dataset_receipt()
    remote_files = {
        role: {"path": path, "sha256": digest, "bytes": byte_count}
        for role, (path, digest, byte_count) in manifest_contract.EXPECTED_REMOTE_FILES.items()
    }
    remote_files["compose_script"].update(
        {
            "source_sha256": manifest_contract.EXPECTED_COMPOSE_INPUT_SHA256,
            "patcher_sha256": sha256(SOURCE_EXP / "patch_compose_dose_env.py"),
        }
    )
    environment = {
        "schema": smoke.ENV_SCHEMA,
        "verdict": smoke.ENV_VERDICT,
        "captured_at_utc": "2026-07-16T10:00:00Z",
        "capture_started_at_utc": "2026-07-16T09:59:00Z",
        "host": "sentinel-gpu",
        "problem_count": 0,
        "problems": [],
        "dataset": dataset,
        "gpu": {
            "model": "NVIDIA L4",
            "count": 1,
            "uuid": "GPU-9604ae8a-e823-3a38-5a57-0420cd29bc07",
            "driver_version": "580.159.03",
            "memory_total_mib": 23034,
        },
        "box": {
            "idle": True,
            "all_containers": 0,
            "gpu_compute_processes": 0,
            "known_evaluation_processes": 0,
        },
        "storage": {
            "remote_output_free_bytes": 120 * 1024**3,
            "projected_output_bytes": manifest_contract.PROJECTED_OUTPUT_BYTES,
            "minimum_reserve_bytes": manifest_contract.MINIMUM_RESERVE_BYTES,
            "local_free_bytes": 45 * 1024**3,
            "remote_output_free_gib": 120.0,
            "projected_output_gib": manifest_contract.PROJECTED_OUTPUT_BYTES / 1024**3,
            "minimum_reserve_gib": 25.0,
            "local_free_gib": 45.0,
            **manifest_contract.EXPECTED_STORAGE_IDENTITY,
        },
        "storage_devices": {
            "filesystem_st_dev": 66308,
            "mount_st_dev": 66308,
            "root_st_dev": 66305,
        },
        "repositories": json.loads(json.dumps(manifest_contract.EXPECTED_REPOSITORIES)),
        "remote_files": remote_files,
        "container_images": {
            name: {"image_id": image_id, "repo_digests": []}
            for name, image_id in IMAGE_IDS.items()
        },
    }
    environment["remote_files"]["compose_script"]["sha256"] = COMPOSE_SHA
    write_json(exp / "env_receipts.json", environment)
    (raw / "environment_receipt.json").write_bytes((exp / "env_receipts.json").read_bytes())

    bound = {}
    for name in (
        "dose_schedules.json",
        "server_patch_blind_dose.py",
        "run_smoke135.sh",
        "validate_smoke135.py",
        "env_receipts.json",
    ):
        path = exp / name
        bound[name] = {"source_path": name, "sha256": sha256(path), "bytes": path.stat().st_size}
    manifest_environment = json.loads(json.dumps(environment))
    manifest_environment["docker_image_ids"] = IMAGE_IDS
    pre_manifest = {
        "schema": smoke.MANIFEST_SCHEMA,
        "verdict": smoke.PRE_SMOKE_VERDICT,
        "launch_authorized": False,
        "mission_phase": "TOOLING_FROZEN_PREFLIGHT_REQUIRED",
        "mission_state": {
            "source_path": "MISSION_STATE.json",
            "sha256": sha256(exp / "MISSION_STATE.json"),
            "bytes": (exp / "MISSION_STATE.json").stat().st_size,
        },
        "git_provenance": {},
        "design": {},
        "planned_blocks": 120,
        "planned_episodes": 2400,
        "pair_order": [],
        "execution_blocks": [],
        "execution_cells": [],
        "dataset_receipt": dataset,
        "environment_receipts": manifest_environment,
        "container_images": environment["container_images"],
        "hash_bound_files": bound,
        "source_artifacts": [],
        "remote_artifacts": {},
        "storage_gate": {},
        "resource_gate": {},
        "smoke_receipt": None,
        "tooling_verification_receipt": {},
        "gates": smoke.PRE_SMOKE_GATES,
        "missing_artifacts": [str(smoke.RECEIPT_REL)],
        "problem_count": 1,
        "problems": ["smoke:receipt-missing"],
    }
    write_json(raw / "pre_smoke_manifest.json", pre_manifest)

    events = [
        {
            "event": "session_start",
            "schema": smoke.RAW_SCHEMA,
            "nonanalytic": True,
            "analytic_episode_count": 0,
            "analytic_output_root": smoke.ANALYTIC_OUTPUT_ROOT,
            "smoke_output_root": smoke.SMOKE_OUTPUT_ROOT,
            "smoke_episode_root": smoke.SMOKE_EPISODE_ROOT,
            "manifest_sha256": sha256(raw / "pre_smoke_manifest.json"),
            "canonical_runner_sha256": sha256(exp / "run_smoke135.sh"),
            "canonical_runner_identity": "66305:1001",
            "persistent_smoke_lock": "/var/lib/sentinel/i135-smoke.lock",
            "persistent_smoke_lock_identity": "66305:1002",
            "retry_policy": "one_shot_no_retry_lock_retained",
            "docker_wrapper_sha256": "a" * 64,
            "docker_binary_sha256": "b" * 64,
            "docker_binary_identity": "66305:1003",
            "container_control_root_identity": "66308:1004",
            "environment_receipt_sha256": sha256(raw / "environment_receipt.json"),
            "schedule_sha256": sha256(exp / "dose_schedules.json"),
            "blind_patch_sha256": sha256(exp / "server_patch_blind_dose.py"),
            "runner_sha256": sha256(exp / "run_smoke135.sh"),
            "validator_sha256": sha256(exp / "validate_smoke135.py"),
            "compose_sha256": COMPOSE_SHA,
            "container_image_ids": IMAGE_IDS,
            "gpu_identity": environment["gpu"],
        }
    ]
    total_ns = 0
    for ordinal, (dose, frames) in enumerate(DOSE_FRAMES.items()):
        schedule_id = f"{dose}/{TARGET}"
        start_ns = 10_000_000_000 + ordinal * 2_000_000_000
        elapsed_ns = 1_250_000_000
        end_ns = start_ns + elapsed_ns
        total_ns += elapsed_ns
        events.append(
            {
                "event": "dose_start",
                "ordinal": ordinal,
                "dose": dose,
                "schedule_id": schedule_id,
                "scenario_class": "frontal",
                "sequence": "0103",
                "run": 0,
                "runs": 1,
                "nonanalytic": True,
                "analytic_inclusion": False,
                "analytic_episode_count": 0,
                "output_root": smoke.SMOKE_EPISODE_ROOT,
                "model_log_path": f"{smoke.MODEL_LOG_ROOT}/{dose}.decisions.jsonl",
                "clock": "monotonic_ns",
                "start_ns": start_ns,
                "argv": [
                    "bash",
                    "/opt/sentinel-stack/NeuroNCAP/scripts/_docker_compose_release.sh",
                    "0103",
                    "frontal",
                    "--scenario-category=frontal",
                    "--runs",
                    "1",
                ],
            }
        )
        events.append(
            {
                "event": "dose_finish",
                "ordinal": ordinal,
                "dose": dose,
                "schedule_id": schedule_id,
                "scenario_class": "frontal",
                "sequence": "0103",
                "run": 0,
                "clock": "monotonic_ns",
                "end_ns": end_ns,
                "elapsed_ns": elapsed_ns,
                "compose_exit_code": 0,
                "env_capture_exit_code": 0,
                "container_monitor_exit_code": 0,
                "container_cleanup_exit_code": 0,
                "container_receipts": {
                    role: hashlib.sha256(f"{ordinal}:{role}".encode()).hexdigest()
                    for role in ("renderer", "model", "ncap")
                },
                "patched_server_sha256": smoke.EXPECTED_BLIND_PATCHED_SERVER_SHA256,
            }
        )
        write_jsonl(raw / f"{dose}.decisions.jsonl", decision_rows(dose, frames))
        env = {
            "PATH": "/usr/local/bin:/usr/bin",
            "SENTINEL_ENABLED": "1",
            "SENTINEL_DOSE_PAIR": "frontal/0103",
            "SENTINEL_DOSE_ID": dose,
            "SENTINEL_DOSE_SCHEDULE": "/model/dose_schedules.json",
            "SENTINEL_LOG": f"{smoke.MODEL_LOG_ROOT}/{dose}.decisions.jsonl",
            "SENTINEL_RELEASE_K": "4",
        }
        (raw / f"{dose}.model-env.bin").write_bytes(
            b"\0".join(f"{key}={value}".encode() for key, value in env.items()) + b"\0"
        )
        (raw / f"{dose}.compose.log").write_text("SMOKE COMPOSE COMPLETE\n")
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
    write_jsonl(raw / "execution.jsonl", events)
    return exp


def rebind_execution_headers(exp: Path) -> None:
    raw = exp / smoke.RAW_REL
    execution_path = raw / "execution.jsonl"
    rows = [json.loads(line) for line in execution_path.read_text().splitlines()]
    rows[0]["manifest_sha256"] = sha256(raw / "pre_smoke_manifest.json")
    rows[0]["environment_receipt_sha256"] = sha256(raw / "environment_receipt.json")
    write_jsonl(execution_path, rows)


def rebind_mission_state(exp: Path) -> None:
    state_path = exp / "MISSION_STATE.json"
    manifest_path = exp / smoke.RAW_REL / "pre_smoke_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["mission_state"] = {
        "source_path": "MISSION_STATE.json",
        "sha256": sha256(state_path),
        "bytes": state_path.stat().st_size,
    }
    write_json(manifest_path, manifest)
    rebind_execution_headers(exp)


def rewrite_environment_with_bound_manifest(exp: Path, environment: dict) -> None:
    raw = exp / smoke.RAW_REL
    canonical_path = exp / "env_receipts.json"
    raw_path = raw / "environment_receipt.json"
    write_json(canonical_path, environment)
    raw_path.write_bytes(canonical_path.read_bytes())

    manifest_path = raw / "pre_smoke_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["hash_bound_files"]["env_receipts.json"] = {
        "source_path": "env_receipts.json",
        "sha256": sha256(canonical_path),
        "bytes": canonical_path.stat().st_size,
    }
    manifest["dataset_receipt"] = environment["dataset"]
    manifest_environment = json.loads(json.dumps(environment))
    manifest_environment["docker_image_ids"] = IMAGE_IDS
    manifest["environment_receipts"] = manifest_environment
    manifest["container_images"] = environment["container_images"]
    write_json(manifest_path, manifest)
    rebind_execution_headers(exp)


def claimed_green_receipt(exp: Path) -> None:
    write_json(
        exp / smoke.RECEIPT_REL,
        {
            "schema": smoke.RECEIPT_SCHEMA,
            "verdict": smoke.OK_VERDICT,
            "problem_count": 0,
            "problems": [],
            "nonanalytic": True,
            "analytic_episode_count": 0,
            "model_environment_forwarded": {name: True for name in smoke.REQUIRED_MODEL_ENV},
            "pair_present_on_every_frame": True,
            "dose_results": {
                dose: {"pass_through_exact": True, "zero_actuator_exact": True}
                for dose in smoke.BLIND_DOSES
            },
        },
    )


def test_recompute_green_receipt_from_raw_evidence(tmp_path: Path) -> None:
    exp = make_fixture(tmp_path)
    receipt = smoke.recompute_smoke_receipt(exp)

    assert receipt["verdict"] == smoke.OK_VERDICT
    assert receipt["problem_count"] == 0
    assert receipt["gpu_elapsed_ns"] == 5_000_000_000
    assert receipt["gpu_seconds"] == 5
    assert receipt["analytic_episode_count"] == 0
    assert receipt["nonanalytic"] is True
    assert set(receipt["dose_results"]) == set(smoke.BLIND_DOSES)
    assert all(receipt["model_environment_forwarded"].values())
    assert receipt["pair_present_on_every_frame"] is True
    assert receipt["dataset_contract_sha256"] == smoke.DATASET_CONTRACT_SHA256
    assert receipt["dataset_receipt_payload_sha256"] == dataset_receipt()[
        "receipt_payload_sha256"
    ]
    assert receipt["canonical_runner_sha256"] == receipt["runner_sha256"]
    assert receipt["persistent_smoke_lock"] == "/var/lib/sentinel/i135-smoke.lock"
    assert receipt["retry_policy"] == "one_shot_no_retry_lock_retained"
    assert set(receipt["container_receipts"]) == set(smoke.BLIND_DOSES)
    observed_container_ids = {
        container_id
        for dose_receipts in receipt["container_receipts"].values()
        for container_id in dose_receipts.values()
    }
    assert len(observed_container_ids) == 12
    assert len(receipt["artifacts"]) == 15
    assert all(row["path"].startswith("smoke-evidence/raw/") for row in receipt["artifacts"])
    assert all(sha256(exp / row["path"]) == row["sha256"] for row in receipt["artifacts"])
    for dose, frames in DOSE_FRAMES.items():
        result = receipt["dose_results"][dose]
        assert result["schedule_id"] == f"{dose}/{TARGET}"
        assert result["expected_brake_frames"] == frames
        assert result["observed_brake_frames"] == frames
        assert result["pass_through_exact"] is True
        assert result["zero_actuator_exact"] is True
        assert result["frame_count"] == 5


def test_environment_and_manifest_must_use_exact_v2_schemas(tmp_path: Path) -> None:
    exp = make_fixture(tmp_path)
    environment = json.loads((exp / "env_receipts.json").read_text())
    environment["schema"] = "iter135.environment_receipts.v1"
    rewrite_environment_with_bound_manifest(exp, environment)

    receipt = smoke.recompute_smoke_receipt(exp)

    assert receipt["verdict"] == smoke.FAIL_VERDICT
    assert "environment:schema" in receipt["problems"]

    exp = make_fixture(tmp_path / "manifest")
    manifest_path = exp / smoke.RAW_REL / "pre_smoke_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["schema"] = "iter135.launch_manifest.v1"
    write_json(manifest_path, manifest)
    rebind_execution_headers(exp)

    receipt = smoke.recompute_smoke_receipt(exp)

    assert receipt["verdict"] == smoke.FAIL_VERDICT
    assert "pre-manifest:schema" in receipt["problems"]


@pytest.mark.parametrize(
    ("mutation", "expected_problem"),
    [
        ("missing-boundary", "mission-state:workspace-boundary"),
        ("isolated-from", "mission-state:workspace-boundary"),
        ("aweb-recovery-source", "mission-state:workspace-boundary"),
        ("boundary-extra", "mission-state:workspace-boundary"),
        ("top-level-extra", "mission-state:field-set"),
        ("canonical-repository", "mission-state:authority-contract"),
    ],
)
def test_smoke_replay_rejects_workspace_boundary_self_declaration(
    tmp_path: Path,
    mutation: str,
    expected_problem: str,
) -> None:
    exp = make_fixture(tmp_path)
    state_path = exp / "MISSION_STATE.json"
    state = json.loads(state_path.read_text())
    if mutation == "missing-boundary":
        del state["workspace_boundary"]
    elif mutation == "isolated-from":
        state["workspace_boundary"]["isolated_from"] = smoke.CANONICAL_REPOSITORY
    elif mutation == "aweb-recovery-source":
        state["workspace_boundary"]["recovery_sources"].append(
            "/Users/danielwahnich/workspace/aweb/MISSION_STATE.json"
        )
    elif mutation == "boundary-extra":
        state["workspace_boundary"]["aweb_bootstrap"] = "pnpm aweb:context"
    elif mutation == "top-level-extra":
        state["aweb_memory"] = "/Users/danielwahnich/workspace/aweb/CONTINUITY.md"
    else:
        state["canonical_repository"] = "/Users/danielwahnich/workspace/aweb"
    write_json(state_path, state)
    rebind_mission_state(exp)

    receipt = smoke.recompute_smoke_receipt(exp)

    assert receipt["verdict"] == smoke.FAIL_VERDICT
    assert expected_problem in receipt["problems"]
    assert "pre-manifest:mission-state-receipt" not in receipt["problems"]


def test_dataset_contract_drift_fails_after_every_hash_link_is_rebound(
    tmp_path: Path,
) -> None:
    exp = make_fixture(tmp_path)
    environment = json.loads((exp / "env_receipts.json").read_text())
    environment["dataset"]["contract_sha256"] = "0" * 64
    environment["dataset"]["receipt_payload_sha256"] = (
        manifest_contract._dataset_receipt_payload_sha256(environment["dataset"])
    )
    rewrite_environment_with_bound_manifest(exp, environment)

    receipt = smoke.recompute_smoke_receipt(exp)

    assert receipt["verdict"] == smoke.FAIL_VERDICT
    assert "environment:dataset:contract-sha256" in receipt["problems"]
    assert "environment:dataset:receipt-payload-sha256" not in receipt["problems"]
    assert "pre-manifest:dataset-link" not in receipt["problems"]


@pytest.mark.parametrize(
    ("case", "expected_problem"),
    [
        ("archive-bytes", "environment:dataset:archive:v1.0-trainval_meta.tgz:expected-bytes"),
        ("metadata-missing", "environment:dataset:metadata-set"),
        (
            "map-path",
            "environment:dataset:map:36092f0b03a857c6a3403e25b4b7aab3.png:path",
        ),
    ],
)
def test_dataset_topology_cannot_self_declare_missing_or_drifted_files(
    tmp_path: Path,
    case: str,
    expected_problem: str,
) -> None:
    exp = make_fixture(tmp_path)
    environment = json.loads((exp / "env_receipts.json").read_text())
    dataset = environment["dataset"]
    if case == "archive-bytes":
        dataset["archives"]["v1.0-trainval_meta.tgz"]["bytes"] += 1
    elif case == "metadata-missing":
        del dataset["metadata_json"]["scene.json"]
    else:
        dataset["map_anchors"]["36092f0b03a857c6a3403e25b4b7aab3.png"][
            "path"
        ] = "/datasets/nuscenes-full/maps/forged.png"
    dataset["receipt_payload_sha256"] = (
        manifest_contract._dataset_receipt_payload_sha256(dataset)
    )
    rewrite_environment_with_bound_manifest(exp, environment)

    receipt = smoke.recompute_smoke_receipt(exp)

    assert receipt["verdict"] == smoke.FAIL_VERDICT
    assert expected_problem in receipt["problems"]
    assert "environment:dataset:receipt-payload-sha256" not in receipt["problems"]


def test_pre_smoke_dataset_receipt_must_equal_raw_and_embedded_environment(
    tmp_path: Path,
) -> None:
    exp = make_fixture(tmp_path)
    manifest_path = exp / smoke.RAW_REL / "pre_smoke_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["dataset_receipt"]["identity"]["dataset_version"] = "v1.0-mini"
    manifest["dataset_receipt"]["receipt_payload_sha256"] = (
        manifest_contract._dataset_receipt_payload_sha256(manifest["dataset_receipt"])
    )
    write_json(manifest_path, manifest)
    rebind_execution_headers(exp)

    receipt = smoke.recompute_smoke_receipt(exp)

    assert receipt["verdict"] == smoke.FAIL_VERDICT
    assert "pre-manifest:dataset-link" in receipt["problems"]
    assert "pre-manifest:environment-link" not in receipt["problems"]


def test_missing_durable_session_identity_fails_closed(tmp_path: Path) -> None:
    exp = make_fixture(tmp_path)
    path = exp / smoke.RAW_REL / "execution.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    del rows[0]["docker_binary_identity"]
    write_jsonl(path, rows)

    receipt = smoke.recompute_smoke_receipt(exp)

    assert receipt["verdict"] == smoke.FAIL_VERDICT
    assert "execution:session-start-field-set" in receipt["problems"]
    assert "execution:docker-binary-identity" in receipt["problems"]


@pytest.mark.parametrize(
    ("field", "value", "expected_problem"),
    [
        (
            "persistent_smoke_lock",
            "/tmp/i135-smoke.lock",
            "execution:persistent-lock-path",
        ),
        ("retry_policy", "automatic_retry", "execution:retry-policy"),
        ("docker_wrapper_sha256", "sha256:not-a-digest", "execution:docker-wrapper-sha256"),
        ("canonical_runner_sha256", "f" * 64, "execution:canonical-runner-hash"),
    ],
)
def test_durable_session_provenance_drift_fails_closed(
    tmp_path: Path,
    field: str,
    value: str,
    expected_problem: str,
) -> None:
    exp = make_fixture(tmp_path)
    path = exp / smoke.RAW_REL / "execution.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0][field] = value
    write_jsonl(path, rows)

    receipt = smoke.recompute_smoke_receipt(exp)

    assert receipt["verdict"] == smoke.FAIL_VERDICT
    assert expected_problem in receipt["problems"]


@pytest.mark.parametrize(
    ("case", "expected_problem"),
    [
        ("missing-role", "execution:blind_0_5x:container-receipt-set"),
        ("duplicate", "execution:blind_0_5x:container-receipt-duplicates"),
        ("malformed", "execution:blind_0_5x:container-receipt:ncap"),
        ("cross-dose-reuse", "execution:blind_1_0x:container-receipt-reuse"),
    ],
)
def test_container_receipts_require_exact_unique_durable_ids(
    tmp_path: Path,
    case: str,
    expected_problem: str,
) -> None:
    exp = make_fixture(tmp_path)
    path = exp / smoke.RAW_REL / "execution.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    first = rows[2]["container_receipts"]
    if case == "missing-role":
        del first["ncap"]
    elif case == "duplicate":
        first["ncap"] = first["model"]
    elif case == "malformed":
        first["ncap"] = "sha256:" + "a" * 64
    else:
        rows[4]["container_receipts"]["renderer"] = first["renderer"]
    write_jsonl(path, rows)

    receipt = smoke.recompute_smoke_receipt(exp)

    assert receipt["verdict"] == smoke.FAIL_VERDICT
    assert expected_problem in receipt["problems"]


@pytest.mark.parametrize(
    ("field", "expected_problem"),
    [
        ("container_monitor_exit_code", "execution:blind_0_5x:container-monitor-exit"),
        ("container_cleanup_exit_code", "execution:blind_0_5x:container-cleanup-exit"),
    ],
)
def test_container_monitor_and_cleanup_must_both_finish_green(
    tmp_path: Path,
    field: str,
    expected_problem: str,
) -> None:
    exp = make_fixture(tmp_path)
    path = exp / smoke.RAW_REL / "execution.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[2][field] = 1
    write_jsonl(path, rows)

    receipt = smoke.recompute_smoke_receipt(exp)

    assert receipt["verdict"] == smoke.FAIL_VERDICT
    assert expected_problem in receipt["problems"]


def test_event_identity_is_exactly_the_six_frozen_fields() -> None:
    row = {
        "ordinal": 3,
        "dose": "blind_2_0x",
        "schedule_id": "blind_2_0x/frontal/0103/0",
        "scenario_class": "frontal",
        "sequence": "0103",
        "run": 0,
    }

    assert smoke._event_identity(row) == (
        3,
        "blind_2_0x",
        "blind_2_0x/frontal/0103/0",
        "frontal",
        "0103",
        0,
    )


def test_claimed_booleans_cannot_rescue_value_or_byte_drift(tmp_path: Path) -> None:
    exp = make_fixture(tmp_path)
    claimed_green_receipt(exp)
    path = exp / smoke.RAW_REL / "blind_1_0x.decisions.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    frame = next(row for row in rows if row.get("frame") and not row["scheduled"])
    # Numerically equal to the base under Python equality, but a different JSON token (1 vs 1.25).
    frame["returned_trajectory"] = [[1, -0.5], [2.5, 0.75]]
    write_jsonl(path, rows)

    receipt = smoke.recompute_smoke_receipt(exp)

    assert receipt["verdict"] == smoke.FAIL_VERDICT
    assert receipt["dose_results"]["blind_1_0x"]["pass_through_exact"] is False
    assert any("pass-through-drift" in problem for problem in receipt["problems"])


def test_claimed_booleans_cannot_rescue_empty_decisions(tmp_path: Path) -> None:
    exp = make_fixture(tmp_path)
    claimed_green_receipt(exp)
    (exp / smoke.RAW_REL / "blind_0_5x.decisions.jsonl").write_bytes(b"")

    receipt = smoke.recompute_smoke_receipt(exp)

    assert receipt["verdict"] == smoke.FAIL_VERDICT
    assert any("decisions:blind_0_5x:empty" in problem for problem in receipt["problems"])
    assert receipt["dose_results"]["blind_0_5x"]["frame_count"] == 0


def test_raw_container_env_must_prove_release_k_and_assigned_dose(tmp_path: Path) -> None:
    exp = make_fixture(tmp_path)
    claimed_green_receipt(exp)
    path = exp / smoke.RAW_REL / "blind_1_5x.model-env.bin"
    payload = path.read_bytes().replace(b"SENTINEL_RELEASE_K=4", b"SENTINEL_RELEASE_K=5")
    path.write_bytes(payload)

    receipt = smoke.recompute_smoke_receipt(exp)

    assert receipt["verdict"] == smoke.FAIL_VERDICT
    assert receipt["model_environment_forwarded"]["SENTINEL_RELEASE_K"] is False
    assert "environment:blind_1_5x:SENTINEL_RELEASE_K" in receipt["problems"]


def test_duplicate_or_analytic_invocation_fails_closed(tmp_path: Path) -> None:
    exp = make_fixture(tmp_path)
    path = exp / smoke.RAW_REL / "execution.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[1]["analytic_inclusion"] = True
    rows.insert(3, dict(rows[1]))
    write_jsonl(path, rows)

    receipt = smoke.recompute_smoke_receipt(exp)

    assert receipt["verdict"] == smoke.FAIL_VERDICT
    assert any(problem.startswith("execution:event-count:") for problem in receipt["problems"])
    assert "execution:blind_0_5x:invocation-contract" in receipt["problems"]


def test_wall_clock_or_wrong_patched_server_hash_fails_closed(tmp_path: Path) -> None:
    exp = make_fixture(tmp_path)
    path = exp / smoke.RAW_REL / "execution.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[1]["clock"] = "wall_epoch_ns"
    rows[2]["patched_server_sha256"] = "9" * 64
    write_jsonl(path, rows)

    receipt = smoke.recompute_smoke_receipt(exp)

    assert receipt["verdict"] == smoke.FAIL_VERDICT
    assert "execution:blind_0_5x:invocation-contract" in receipt["problems"]
    assert "execution:blind_0_5x:patched-server-hash" in receipt["problems"]


def test_live_gpu_identity_is_bound_to_environment_receipt(tmp_path: Path) -> None:
    exp = make_fixture(tmp_path)
    path = exp / smoke.RAW_REL / "execution.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]["gpu_identity"]["memory_total_mib"] += 1
    write_jsonl(path, rows)

    receipt = smoke.recompute_smoke_receipt(exp)

    assert receipt["verdict"] == smoke.FAIL_VERDICT
    assert "execution:gpu-identity" in receipt["problems"]


def test_schedule_and_brake_rows_are_recomputed_not_claimed(tmp_path: Path) -> None:
    exp = make_fixture(tmp_path)
    claimed_green_receipt(exp)
    path = exp / smoke.RAW_REL / "blind_2_0x.decisions.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows = [row for row in rows if not (row.get("brake") and row["frame_index"] == 2)]
    write_jsonl(path, rows)

    receipt = smoke.recompute_smoke_receipt(exp)

    assert receipt["verdict"] == smoke.FAIL_VERDICT
    assert any("brake-row-set" in problem for problem in receipt["problems"])
    assert any("row-order" in problem for problem in receipt["problems"])


def test_compose_error_and_artifact_mutation_fail_closed(tmp_path: Path) -> None:
    exp = make_fixture(tmp_path)
    path = exp / smoke.RAW_REL / "blind_0_5x.compose.log"
    path.write_text("Traceback (most recent call last):\nRuntimeError: injected\n")

    receipt = smoke.recompute_smoke_receipt(exp)

    assert receipt["verdict"] == smoke.FAIL_VERDICT
    assert "compose-log:blind_0_5x:runtime-error" in receipt["problems"]
    artifact = next(row for row in receipt["artifacts"] if row["path"].endswith(path.name))
    assert artifact["sha256"] == sha256(path)


def test_runner_is_one_shot_hash_gated_and_syntax_valid() -> None:
    text = RUNNER_PATH.read_text()

    assert "SENTINEL_SMOKE_INPUT_MANIFEST_SHA256" in text
    assert "manifest-required-tooling-set" in text
    assert "remote:{role}:drift" in text
    assert "path.resolve(strict=True) != path" in text
    assert '"docker", "image", "inspect"' in text
    assert "NVIDIA L4" in text
    assert "gpu-compute-process-present" in text
    assert "gpu-compute-process-probe-failed" in text
    assert "--query-gpu=name,uuid,driver_version,memory.total" in text
    assert "live GPU identity drift" in text
    assert "docker exec \"$MODEL_CONTAINER_ID\" sh -c 'env -0'" in text
    assert "sentinel-i135-smoke-evidence" in text
    assert "sentinel-i135-outoutput" in text
    assert "/opt/sentinel-stack/NeuroNCAP" in text
    assert "/opt/sentinel-stack/neuro-ncap" not in text
    assert text.count("--runs 1") == 1
    assert "--runs 20" not in text
    assert "while IFS=$'\\t' read" in text
    assert "one-shot-path-exists" in text
    assert '"git", "-c", f"safe.directory={path}"' in text
    assert '"neurad": ["Dockerfile.bak"]' in text
    assert 'item.startswith("outoutput/")' in text
    assert "unexpected-untracked" in text
    assert "untracked != required_untracked" in text
    assert "any(path not in untracked" not in text
    assert "time.monotonic_ns()" in text
    assert "date +%s%N" not in text
    assert smoke.EXPECTED_BLIND_PATCHED_SERVER_SHA256 in text
    assert 'python3 - "$EXECUTION_LOG" "$REASON"' in text
    assert 'sys.argv[2]' in text
    assert "rm -rf \"$RAW_DIR\"" not in text
    assert "assert_no_conflicting_containers" in text
    assert "assert_docker_empty" in text
    assert "assert_immutable_images" in text
    assert "assert_gpu_compute_idle" in text
    assert "OWNED_CONTAINER_IDS=()" in text
    assert "OWNED_CONTAINER_ROLES=()" in text
    assert "capture_owned_containers" in text
    assert "{{.Name}}|{{.Config.Image}}" in text
    assert 'docker rm -f "$ID"' in text
    assert "docker rm -f renderer model ncap" not in text
    assert 'docker rm -f "$NAME"' not in text
    assert 'MODEL_IMAGE=$EXPECTED_UNIAD_IMAGE_ID' in text
    assert 'RENDERING_IMAGE=$EXPECTED_NEURAD_IMAGE_ID' in text
    assert 'NCAP_IMAGE=$EXPECTED_NCAP_IMAGE_ID' in text
    assert "sha256:f73ef38840631211983ea0dde0cf1ecdfa6dbc84ef6cd0bfb900427da6d601cb" in text
    assert "sha256:4b36caf2054d37b4febeddeae08b310f906ec632fec4095b5dc4497323433e5c" in text
    assert "sha256:c7ffab2e73d3896b1a6cdfbcd2db0910c250a9cbf078cc61a4b43baa6f6d92ce" in text
    assert "I135_SMOKE_PREEXISTING_CONTAINER" in text
    assert "I135_SMOKE_CONTAINER_OWNERSHIP_FAIL" in text
    assert 'if ! ALL_CONTAINER_IDS=$(docker ps -aq --no-trunc)' in text
    assert "if ! GPU_COMPUTE_PIDS=$(nvidia-smi" in text
    assert text.index("No mutation happens above this line") < text.index(
        "SMOKE_LOCK_ID=$(python3"
    )
    subprocess.run(["bash", "-n", str(RUNNER_PATH)], check=True)


def test_runner_rejects_copied_or_path_aliased_execution_before_mutation() -> None:
    text = RUNNER_PATH.read_text()

    assert 'RUNNER_SOURCE=$I135/run_smoke135.sh' in text
    assert '"$RUNNER_SOURCE" "$0" "${BASH_SOURCE[0]}"' in text
    assert 'expected = Path("/opt/sentinel-stack/iter135/run_smoke135.sh")' in text
    assert "canonical != expected or argv0 != expected or bash_source != expected" in text
    assert "path.resolve(strict=True) != expected" in text
    assert "runner inode drift" in text
    assert "runner manifest receipt drift" in text
    assert "os.O_NOFOLLOW" in text
    assert "canonical-runner-binding" in text
    binding = text.index("RUNNER_BINDING=$(python3")
    provenance = text.index("TARGET_PLAN=$(python3")
    mutation = text.index("SMOKE_LOCK_ID=$(python3")
    assert binding < provenance < mutation


def test_runner_publishes_and_retains_durable_one_shot_lock() -> None:
    text = RUNNER_PATH.read_text()

    assert "LOCK=/var/lib/sentinel/i135-smoke.lock" in text
    assert "/var/lock/sentinel-i135-smoke.lock" not in text
    assert '"schema": "iter135.smoke_lock.v1"' in text
    assert '"retry_policy": "one_shot_no_retry_lock_retained"' in text
    assert "os.link(temporary, lock, follow_symlinks=False)" in text
    assert "os.fsync(stream.fileno())" in text
    assert "os.fsync(parent_descriptor)" in text
    assert "os.chmod(temporary, 0o444)" in text
    assert "Once the durable one-shot path is published it is never removed" in text
    assert 'rm -f "$LOCK"' not in text
    assert 'rmdir "$LOCK"' not in text
    assert 'mkdir "$LOCK"' not in text
    assert "lock_retained=$LOCK" in text
    lock_publish = text.index("SMOKE_LOCK_ID=$(python3")
    first_output_mutation = text.index('mkdir -m 0755 "$SMOKE_OUTPUT_ROOT"')
    assert lock_publish < first_output_mutation


def test_runner_uses_labeled_cidfile_ownership_and_id_only_cleanup() -> None:
    text = RUNNER_PATH.read_text()

    for label in (
        "--label sentinel.mission=iter135",
        'sentinel.manifest=$SENTINEL_MANIFEST_SHA256',
        "--label sentinel.mode=nonanalytic-smoke",
        'sentinel.dose=$SENTINEL_SMOKE_DOSE_ORDINAL',
        'sentinel.role=$ROLE',
    ):
        assert label in text
    assert '--cidfile "$CID_FILE"' in text
    assert "SENTINEL_DOCKER_WRAPPER_SHA256" in text
    assert "SENTINEL_CONTAINER_CONTROL_ROOT_ID" in text
    assert "wrapper-identity-drift" in text
    assert "unexpected-command:$COMMAND" in text
    assert "container_control_root_identity" in text
    assert "verify_container_receipts" in text
    assert "captured_container_receipts_json" in text
    assert "container cid was not captured live" in text
    assert '"container_receipts": json.loads(container_receipts_json)' in text
    assert "OWNED_CONTAINER_IDS" in text
    assert "OWNED_CONTAINER_ROLES" in text
    assert 'docker rm -f "$ID"' in text
    assert "REMAINING_IDS" in text
    assert "REMAINING_ROLES" in text
    assert "docker rm -f renderer model ncap" not in text
    assert 'docker rm -f "$NAME"' not in text
    capture_function = text[
        text.index("capture_owned_containers()") : text.index(
            "assert_no_conflicting_containers()"
        )
    ]
    assert "--filter \"name=^/" not in capture_function


def test_generated_docker_wrapper_injects_provenance_and_rejects_copy(
    tmp_path: Path,
) -> None:
    control = tmp_path / "control"
    control.mkdir(mode=0o700)
    cid_dir = control / "dose-0"
    cid_dir.mkdir(mode=0o700)
    wrapper = control / "docker"
    wrapper.write_text(docker_wrapper_payload())
    wrapper.chmod(0o500)
    fake_docker = tmp_path / "real-docker"
    fake_docker.write_text(
        """#!/bin/bash
set -euo pipefail
printf '%s\n' "$@" > "$FAKE_DOCKER_ARGS"
PREVIOUS=
for ARG in "$@"; do
  if [ "$PREVIOUS" = "--cidfile" ]; then
    printf '%s\n' "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee" > "$ARG"
  fi
  PREVIOUS=$ARG
done
"""
    )
    fake_docker.chmod(0o500)
    tool_bin = tmp_path / "bin"
    tool_bin.mkdir()
    portable_stat = tool_bin / "stat"
    portable_stat.write_text(
        """#!/usr/bin/env python3
import os
import sys

if len(sys.argv) != 4 or sys.argv[1:3] != ["-Lc", "%d:%i"]:
    raise SystemExit(64)

identity = os.stat(sys.argv[3], follow_symlinks=True)
print(f"{identity.st_dev}:{identity.st_ino}")
"""
    )
    portable_stat.chmod(0o500)
    args_path = tmp_path / "docker.args"
    manifest_sha = "1" * 64
    environment = {
        **os.environ,
        "PATH": f"{tool_bin}:{os.environ['PATH']}",
        "FAKE_DOCKER_ARGS": str(args_path),
        "SENTINEL_DOCKER_BIN": str(fake_docker),
        "SENTINEL_DOCKER_BIN_ID": (
            f"{fake_docker.stat().st_dev}:{fake_docker.stat().st_ino}"
        ),
        "SENTINEL_DOCKER_BIN_SHA256": sha256(fake_docker),
        "SENTINEL_DOCKER_WRAPPER_SHA256": sha256(wrapper),
        "SENTINEL_MANIFEST_SHA256": manifest_sha,
        "SENTINEL_SMOKE_DOSE_ORDINAL": "0",
        "SENTINEL_CONTAINER_CONTROL_ROOT": str(control),
        "SENTINEL_CONTAINER_CONTROL_ROOT_ID": (
            f"{control.stat().st_dev}:{control.stat().st_ino}"
        ),
        "SENTINEL_CONTAINER_CID_DIR": str(cid_dir),
    }
    completed = subprocess.run(
        [
            str(wrapper),
            "run",
            "--name",
            "model",
            "sha256:f73ef38840631211983ea0dde0cf1ecdfa6dbc84ef6cd0bfb900427da6d601cb",
            "python",
            "-V",
        ],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    observed = args_path.read_text().splitlines()
    assert observed[0] == "run"
    assert "sentinel.mission=iter135" in observed
    assert f"sentinel.manifest={manifest_sha}" in observed
    assert "sentinel.mode=nonanalytic-smoke" in observed
    assert "sentinel.dose=0" in observed
    assert "sentinel.role=model" in observed
    cid_index = observed.index("--cidfile")
    assert observed[cid_index + 1] == str(cid_dir / "model.cid")
    assert (cid_dir / "model.cid").read_text().strip() == "e" * 64

    unexpected = subprocess.run(
        [str(wrapper), "rm", "model"],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert unexpected.returncode == 125
    assert "unexpected-command:rm" in unexpected.stderr

    copied = control / "copied-docker"
    copied.write_text(docker_wrapper_payload())
    copied.chmod(0o500)
    copied_environment = {**environment, "SENTINEL_DOCKER_WRAPPER_SHA256": sha256(copied)}
    copied_run = subprocess.run(
        [copied, "run", "--name", "model"],
        env=copied_environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert copied_run.returncode == 125
    assert "wrapper-identity-drift" in copied_run.stderr


def test_runner_has_exact_required_command_floor() -> None:
    text = RUNNER_PATH.read_text()
    match = re.search(
        r"for REQUIRED_COMMAND in (.*?); do\n  command -v",
        text,
        flags=re.DOTALL,
    )
    assert match is not None
    observed = match.group(1).replace("\\\n", " ").split()
    assert observed == [
        "awk",
        "bash",
        "cp",
        "dirname",
        "docker",
        "env",
        "findmnt",
        "git",
        "grep",
        "mkdir",
        "mv",
        "nvidia-smi",
        "ps",
        "python3",
        "readlink",
        "rm",
        "sed",
        "sha256sum",
        "sleep",
        "stat",
        "timeout",
        "touch",
        "tr",
        "wc",
    ]


def test_runner_requires_exact_pre_smoke_authority_and_live_host_contract() -> None:
    text = RUNNER_PATH.read_text()

    assert 'MISSION_STATE_SOURCE=$I135/MISSION_STATE.json' in text
    assert 'manifest.get("mission_phase") != "TOOLING_FROZEN_PREFLIGHT_REQUIRED"' in text
    assert '"tooling_verification": True' in text
    assert '"g5_live_smoke": False' in text
    assert "mission-state-authority-contract" in text
    assert '"workspace_boundary"' in text
    assert '"isolated_from": "/Users/danielwahnich/workspace/aweb"' in text
    assert '"recovery_sources": ["MISSION_STATE.json", "CONTINUITY.md", "HANDOFF.md"]' in text
    assert '"cross_workspace_access_requires_explicit_operator_request": True' in text
    assert "pnpm aweb:context" not in text
    assert "/Users/danielwahnich/workspace/aweb/MISSION_STATE.json" not in text
    assert "expected_authorized_actions" in text
    assert "expected_forbidden_actions" in text
    assert "I135_TOOLING_VERIFICATION_OK" in text
    assert 'tooling.get("schema") != "iter135.tooling_verification.v2"' in text
    assert "iter135.tooling_verification.v1" not in text
    assert "environment-live-host" in text
    assert "environment-frozen-gpu" in text
    assert "environment-box-contract" in text
    assert "live-storage-device-drift" in text
    assert "/dev/nvme0n2" in text
    assert "9a98277e-b21f-4ffc-8f14-3f2235b43103" in text
    assert "live-storage-free" in text
    assert "100 * 1024**3" in text
    assert "25 * 1024**3" in text


def test_runner_requires_v2_dataset_provenance_without_self_declaration() -> None:
    text = RUNNER_PATH.read_text()

    assert 'manifest.get("schema") != "iter135.launch_manifest.v2"' in text
    assert 'environment.get("schema") != "iter135.environment_receipts.v2"' in text
    assert '"dataset_receipt"' in text
    assert '"dataset"' in text
    assert '"g7_dataset_provenance": True' in text
    assert "validate_dataset_receipt" in text
    assert "manifest-dataset-receipt-drift" in text
    assert "dataset-validator-frozen-constant-drift" in text
    assert "ae22656f62044fbc649a5ef8976c708249b6c62dabe475fb8c347b7558fe3e8b" in text
    assert "live-dataset-device-drift" in text
    assert "live-dataset-mount-identity" in text
    assert "live-dataset-sha256" in text
    assert "smoke runtime dataset identity drift" in text
    assert "final provenance receipt drift" in text
    assert "NUSCENES_PATH=/datasets/nuscenes-full" in text
    assert "NUSCENES_PATH=/datasets/nuscenes\n" not in text


def test_runner_rehashes_runtime_inputs_around_every_dose_and_rechecks_green() -> None:
    text = RUNNER_PATH.read_text()

    assert "verify_smoke_runtime_inputs()" in text
    assert "smoke runtime selected role-set drift" in text
    assert "smoke runtime schedule drift" in text
    assert "smoke runtime blind patch drift" in text
    assert "smoke runtime image identity drift" in text
    assert '"$EXPECTED_BLIND_PATCHED_SERVER_SHA256" before' in text
    assert '"$EXPECTED_BLIND_PATCHED_SERVER_SHA256" after' in text
    assert text.count("verify_smoke_runtime_inputs") == 3
    assert "final-docker-not-empty" in text
    assert "final-gpu-not-idle" in text
    assert "final-evaluator-not-idle" in text
    assert "final-green-boundary-drift" in text
    green_gate = text.rindex("final-green-boundary-drift")
    done_marker = text.index('touch "$SMOKE_OUTPUT_ROOT/I135_LIVE_SMOKE_DONE"')
    assert green_gate < done_marker


@pytest.mark.parametrize("name", ["run_smoke135.sh", "validate_smoke135.py"])
def test_pre_smoke_manifest_must_hash_bind_new_pipeline(tmp_path: Path, name: str) -> None:
    exp = make_fixture(tmp_path)
    manifest_path = exp / smoke.RAW_REL / "pre_smoke_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    del manifest["hash_bound_files"][name]
    write_json(manifest_path, manifest)
    execution_path = exp / smoke.RAW_REL / "execution.jsonl"
    rows = [json.loads(line) for line in execution_path.read_text().splitlines()]
    rows[0]["manifest_sha256"] = sha256(manifest_path)
    write_jsonl(execution_path, rows)

    receipt = smoke.recompute_smoke_receipt(exp)

    assert receipt["verdict"] == smoke.FAIL_VERDICT
    assert f"pre-manifest:hash:{name}" in receipt["problems"]
