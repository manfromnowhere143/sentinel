"""Hostile tests for the frozen Iteration-135 raw-proof collector."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import shutil
import subprocess
import tarfile
from pathlib import Path

import pytest

from experiments.iter135_neuroncap_blind_braking_dose_response import collect_proof135 as c


TEST_FREE_BYTES = 20 * 1024**3
PRIOR_SMOKE_SECONDS = 7
ELAPSED_SECONDS = 360
PROJECTED_OUTPUT_BYTES = 72_380_432_384
DEFAULT_MANIFEST_SHA256 = "a" * 64
DEFAULT_DATASET_SNAPSHOT_SHA256 = "b" * 64
DEFAULT_DOCKER_SNAPSHOT_SHA256 = "c" * 64
DEFAULT_DATASET_SNAPSHOT_ID = "66308:13501"
DEFAULT_DOCKER_SNAPSHOT_ID = "66308:13502"
DEFAULT_LOCK_ID = "66308:13503"


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def _dataset_receipt() -> dict:
    identity = {
        "dataset_root": c.EXPECTED_DATASET_ROOT,
        "dataset_realpath": c.EXPECTED_DATASET_ROOT,
        "dataset_is_symlink": False,
        "dataset_version": c.EXPECTED_DATASET_VERSION,
        "archive_root": c.EXPECTED_DATASET_ARCHIVE_ROOT,
        "archive_realpath": c.EXPECTED_DATASET_ARCHIVE_ROOT,
        "archive_is_symlink": False,
        "metadata_root": c.EXPECTED_DATASET_METADATA_ROOT,
        "metadata_realpath": c.EXPECTED_DATASET_METADATA_ROOT,
        "metadata_is_symlink": False,
        "map_root": c.EXPECTED_DATASET_MAP_ROOT,
        "map_realpath": c.EXPECTED_DATASET_MAP_ROOT,
        "map_is_symlink": False,
        **c.EXPECTED_DATASET_MOUNT,
        "dataset_st_dev": 66_308,
        "mount_st_dev": 66_308,
        "root_st_dev": 66_305,
    }
    archives = {
        name: {
            "path": f"{c.EXPECTED_DATASET_ARCHIVE_ROOT}/{name}",
            "sha256": digest,
            "bytes": byte_count,
        }
        for name, (digest, byte_count) in c.EXPECTED_DATASET_ARCHIVES.items()
    }
    metadata = {
        name: {
            "path": f"{c.EXPECTED_DATASET_METADATA_ROOT}/{name}",
            "sha256": hashlib.sha256(f"metadata:{name}".encode()).hexdigest(),
            "bytes": index + 1,
        }
        for index, name in enumerate(c.EXPECTED_DATASET_METADATA_FILES)
    }
    maps = {
        name: {
            "path": f"{c.EXPECTED_DATASET_MAP_ROOT}/{name}",
            "sha256": hashlib.sha256(f"map:{name}".encode()).hexdigest(),
            "bytes": index + 101,
        }
        for index, name in enumerate(c.EXPECTED_DATASET_MAP_ANCHORS)
    }
    receipt = {
        "schema": c.DATASET_SCHEMA,
        "contract_sha256": c.EXPECTED_DATASET_CONTRACT_SHA256,
        "proof_basis": c.EXPECTED_DATASET_PROOF_BASIS,
        "identity": identity,
        "archives": archives,
        "metadata_json": metadata,
        "map_anchors": maps,
    }
    receipt["receipt_payload_sha256"] = c._canonical_json_sha256(receipt)
    return receipt


def _manifest() -> dict:
    execution_cells = []
    ordinal = 0
    for block in c.expected_blocks():
        for run in c.RUNS:
            execution_cells.append(
                {
                    "ordinal": ordinal,
                    "block_ordinal": block["ordinal"],
                    "pair_index": block["pair_index"],
                    "temporal_position": block["temporal_position"],
                    "arm_id": block["arm_id"],
                    "scenario_class": block["scenario_class"],
                    "sequence": block["sequence"],
                    "run_index": run,
                }
            )
            ordinal += 1
    gates = {
        "g0_preregistration": True,
        "g1_provenance": True,
        "g2_released_behavior": True,
        "g3_schedule_integrity": True,
        "g4_semantic_leak": True,
        "g5_live_smoke": True,
        "g7_dataset_provenance": True,
        "g8_storage_environment": True,
        "g9_resource_plan": True,
        "execution_plan": True,
        "execution_consumers": True,
        "tooling_verification": True,
        "mission_state": True,
    }
    collector = Path(c.__file__).resolve()
    dataset = _dataset_receipt()
    return {
        "schema": c.MANIFEST_SCHEMA,
        "verdict": "I135_TOOLING_MANIFEST_OK",
        "launch_authorized": True,
        "mission_phase": "LAUNCH_AUTHORIZED",
        "planned_blocks": 120,
        "planned_episodes": 2400,
        "problem_count": 0,
        "problems": [],
        "missing_artifacts": [],
        "design": {
            "retry_policy": "no_automatic_retry_abort_on_first_block_failure",
            "allowed_retries": 0,
        },
        "execution_blocks": c.expected_blocks(),
        "execution_cells": execution_cells,
        "gates": gates,
        "dataset_receipt": dataset,
        "environment_receipts": {
            "schema": c.ENVIRONMENT_SCHEMA,
            "dataset": dataset,
        },
        "hash_bound_files": {
            "collect_proof135.py": {
                "sha256": hashlib.sha256(collector.read_bytes()).hexdigest(),
                "bytes": collector.stat().st_size,
            },
            "env_receipts.json": {
                "source_path": "env_receipts.json",
                "sha256": "e" * 64,
                "bytes": 135,
            },
        },
        "storage_gate": {
            "minimum_remote_free_gib": 100,
            "minimum_reserve_gib": 25,
            "minimum_local_free_gib": 15,
            "observed_remote_free_gib": 130,
            "projected_output_gib": 5,
            "minimum_remote_free_bytes": 100 * 1024**3,
            "projected_output_bytes": PROJECTED_OUTPUT_BYTES,
            "minimum_reserve_bytes": 25 * 1024**3,
        },
        "resource_gate": {
            "total_gpu_ceiling_seconds": c.TOTAL_GPU_CEILING_SECONDS,
            "prior_smoke_gpu_seconds": PRIOR_SMOKE_SECONDS,
            "remaining_analytic_seconds": c.TOTAL_GPU_CEILING_SECONDS - PRIOR_SMOKE_SECONDS,
        },
    }


def _runtime_evidence(
    manifest_sha256: str, manifest: dict
) -> dict[str, tuple[bytes, str]]:
    dataset = manifest["dataset_receipt"]
    files = {}
    inode = 20_000
    for prefix, group_name in (
        ("archive", "archives"),
        ("metadata", "metadata_json"),
        ("map", "map_anchors"),
    ):
        for name, receipt in sorted(dataset[group_name].items()):
            inode += 1
            files[f"{prefix}:{name}"] = {
                **receipt,
                "st_dev": dataset["identity"]["dataset_st_dev"],
                "st_ino": inode,
                "st_mode": 0o444,
                "st_mtime_ns": 1_350_000_000 + inode,
                "st_ctime_ns": 1_350_100_000 + inode,
            }
    dataset_snapshot = {
        "schema": c.DATASET_RUNTIME_SCHEMA,
        "manifest_sha256": manifest_sha256,
        "dataset_receipt_payload_sha256": dataset["receipt_payload_sha256"],
        "dataset_root": {
            "path": c.EXPECTED_DATASET_ROOT,
            "st_dev": dataset["identity"]["dataset_st_dev"],
            "st_ino": 19_999,
            "st_mode": 0o755,
            "st_mtime_ns": 1_350_000_000,
            "st_ctime_ns": 1_350_100_000,
        },
        "files": files,
    }
    docker_info = {
        "ID": "sentinel-daemon-135",
        "Name": "sentinel-host",
        "ServerVersion": "27.5.1",
        "DockerRootDir": "/var/lib/docker",
        "Driver": "overlay2",
        "OperatingSystem": "Ubuntu 22.04",
        "OSType": "linux",
        "Architecture": "x86_64",
        "NCPU": 16,
        "MemTotal": 64 * 1024**3,
        "KernelVersion": "6.8.0",
        "CgroupDriver": "systemd",
        "CgroupVersion": "2",
    }
    docker_snapshot = {
        "schema": c.DOCKER_RUNTIME_SCHEMA,
        "manifest_sha256": manifest_sha256,
        "client": {
            "path": "/usr/bin/docker",
            "sha256": "d" * 64,
            "st_dev": 66_305,
            "st_ino": 30_001,
        },
        "context": "default",
        "endpoint": "unix:///var/run/docker.sock",
        "socket": {
            "declared_path": "/var/run/docker.sock",
            "realpath": "/run/docker.sock",
            "st_dev": 66_305,
            "st_ino": 30_002,
            "st_mode": 0o660,
            "st_uid": 0,
            "st_gid": 999,
        },
        "daemon_info": docker_info,
        "daemon_version": {
            "Platform": {"Name": "Docker Engine - Community"},
            "Version": "27.5.1",
            "ApiVersion": "1.47",
            "MinAPIVersion": "1.24",
            "GitCommit": "sentinel135",
            "GoVersion": "go1.22.11",
            "Os": "linux",
            "Arch": "amd64",
            "BuildTime": "2026-07-16T00:00:00Z",
            "Experimental": False,
        },
    }
    dataset_payload = c._canonical_runtime_snapshot(dataset_snapshot)
    docker_payload = c._canonical_runtime_snapshot(docker_snapshot)
    lock = {
        "schema": c.ANALYTIC_LOCK_SCHEMA,
        "manifest_sha256": manifest_sha256,
        "dataset_runtime_snapshot_sha256": hashlib.sha256(dataset_payload).hexdigest(),
        "docker_runtime_snapshot_sha256": hashlib.sha256(docker_payload).hexdigest(),
        "pid": 135,
        "created_at_utc": "2026-07-16T00:00:00Z",
    }
    lock_payload = (json.dumps(lock, sort_keys=True) + "\n").encode()
    return {
        "dataset_runtime_snapshot": (dataset_payload, DEFAULT_DATASET_SNAPSHOT_ID),
        "docker_runtime_snapshot": (docker_payload, DEFAULT_DOCKER_SNAPSHOT_ID),
        "analytic_lock": (lock_payload, DEFAULT_LOCK_ID),
    }


def _make_log(
    path: Path,
    manifest_sha256: str = DEFAULT_MANIFEST_SHA256,
    runtime_evidence: dict[str, tuple[bytes, str]] | None = None,
) -> None:
    runtime_snapshot = f"{c.RUNTIME_SNAPSHOT_ROOT}/i135-runtime-{manifest_sha256}"
    if runtime_evidence is None:
        dataset_sha = DEFAULT_DATASET_SNAPSHOT_SHA256
        docker_sha = DEFAULT_DOCKER_SNAPSHOT_SHA256
        dataset_id = DEFAULT_DATASET_SNAPSHOT_ID
        docker_id = DEFAULT_DOCKER_SNAPSHOT_ID
        lock_id = DEFAULT_LOCK_ID
    else:
        dataset_payload, dataset_id = runtime_evidence["dataset_runtime_snapshot"]
        docker_payload, docker_id = runtime_evidence["docker_runtime_snapshot"]
        _lock_payload, lock_id = runtime_evidence["analytic_lock"]
        dataset_sha = hashlib.sha256(dataset_payload).hexdigest()
        docker_sha = hashlib.sha256(docker_payload).hexdigest()
    lines = [
        "I135_INVOCATION_START at=2026-07-16T00:00:00Z pid=135 "
        f"manifest_sha256={manifest_sha256}\n",
        "I135_LIVE_IDLE_OK gpu=NVIDIA_L4 count=1 compute_processes=0 evaluators=0\n",
        f"I135_PREFLIGHT_OK manifest_sha256={manifest_sha256} "
        "blocks=120 cells=2400 payloads=14 remote=6\n",
        f"I135_RUNTIME_SNAPSHOT_OK manifest_sha256={manifest_sha256} "
        f"path={runtime_snapshot}\n",
        f"I135_DATASET_SNAPSHOT_OK sha256={dataset_sha} id={dataset_id} files=28\n",
        f"I135_DOCKER_SNAPSHOT_OK sha256={docker_sha} id={docker_id}\n",
        f"I135_ANALYTIC_ARMED lock={c.EXPECTED_LAUNCH_LOCK} lock_id={lock_id} "
        f"output_root={c.EXPECTED_OUTPUT_ROOT}\n",
        "I135_DATASET_RUNTIME_OK phase=analytic-arm files=28\n",
        "I135_DOCKER_RUNTIME_OK phase=analytic-arm daemon_id=sentinel-daemon-135\n",
    ]
    for block in c.expected_blocks():
        ordinal = block["ordinal"]
        arm = block["arm_id"]
        scenario_class = block["scenario_class"]
        pair = block["sequence"]
        lines.append("I135_DATASET_RUNTIME_OK phase=before files=28\n")
        lines.append(
            "I135_DOCKER_RUNTIME_OK phase=before daemon_id=sentinel-daemon-135\n"
        )
        lines.append(
            f"I135_BLOCK_START ordinal={ordinal} arm={arm} pair={scenario_class}/{pair}\n"
        )
        lines.append(f"##### I135BLOCK {arm} {scenario_class} {pair} #####\n")
        lines.extend(
            f"ncap_score: {run / 10:.1f},  impact_speed: 0.0, reference_speed: 1.0\n"
            for run in c.RUNS
        )
        lines.append(f"I135_BLOCK_VALIDATION_OK arm={arm} pair={scenario_class}/{pair}\n")
        lines.append(
            f"I135_BLOCK_OK ordinal={ordinal} arm={arm} pair={scenario_class}/{pair} runs=20\n"
        )
        lines.append("I135_DATASET_RUNTIME_OK phase=after files=28\n")
        lines.append(
            "I135_DOCKER_RUNTIME_OK phase=after daemon_id=sentinel-daemon-135\n"
        )
    lines.append("I135_DATASET_RUNTIME_OK phase=before-done files=28\n")
    lines.append(
        "I135_DOCKER_RUNTIME_OK phase=before-done daemon_id=sentinel-daemon-135\n"
    )
    lines.append(
        "I135_DONE_METADATA at=2026-07-16T01:00:00Z "
        f"manifest_sha256={manifest_sha256} runtime_snapshot={runtime_snapshot} "
        f"dataset_runtime_snapshot_sha256={dataset_sha} "
        f"dataset_runtime_snapshot_id={dataset_id} "
        f"docker_runtime_snapshot_sha256={docker_sha} "
        f"docker_runtime_snapshot_id={docker_id} "
        f"launch_lock_retained={c.EXPECTED_LAUNCH_LOCK} "
        f"launch_lock_id={lock_id} "
        f"elapsed_seconds={ELAPSED_SECONDS} prior_smoke_gpu_seconds={PRIOR_SMOKE_SECONDS} "
        "blocks=120 episodes=2400 "
        f"output_root={c.EXPECTED_OUTPUT_ROOT} output_device={c.EXPECTED_OUTPUT_DEVICE} "
        f"output_uuid={c.EXPECTED_OUTPUT_UUID} start_free_bytes={120 * 1024**3} "
        f"end_free_bytes={110 * 1024**3} output_bytes={10 * 1024**3}\n"
    )
    lines.append("I135_DOSE_DONE\n")
    path.write_text("".join(lines), encoding="utf-8")


def _log_facts(manifest_sha256: str = DEFAULT_MANIFEST_SHA256) -> dict:
    return {
        "launch_manifest_sha256": manifest_sha256,
        "prior_smoke_gpu_seconds": PRIOR_SMOKE_SECONDS,
        "remaining_analytic_seconds": c.TOTAL_GPU_CEILING_SECONDS - PRIOR_SMOKE_SECONDS,
        "total_gpu_ceiling_seconds": c.TOTAL_GPU_CEILING_SECONDS,
        "minimum_remote_free_bytes": 100 * 1024**3,
        "projected_output_bytes": PROJECTED_OUTPUT_BYTES,
        "minimum_reserve_bytes": 25 * 1024**3,
    }


def _make_decisions(root: Path) -> None:
    for arm in c.ARMS:
        for scenario_class, pair in c.canonical_pairs():
            rows = []
            if arm not in c.BLIND_ARMS:
                rows.append(
                    {
                        "block_identity": True,
                        "arm": arm,
                        "class": scenario_class,
                        "pair": pair,
                    }
                )
            for run in c.RUNS:
                row = {"reset": True, "run": run}
                if arm in c.BLIND_ARMS:
                    row.update({"class": scenario_class, "pair": pair, "dose": arm})
                rows.append(row)
            path = root / c.ARM_SHORT[arm] / f"{scenario_class}-{pair}.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )


def _make_runs(root: Path) -> None:
    payloads = {
        "ego_poses.json": b"{}\n",
        "metrics.json": b"{}\n",
        "actors.json": b"[]\n",
    }
    for arm, scenario_class, pair, run in c.expected_cells():
        run_dir = root / c.ARM_RUN_DIR[arm] / f"{scenario_class}-{pair}" / f"run_{run}"
        run_dir.mkdir(parents=True, exist_ok=True)
        for name, payload in payloads.items():
            (run_dir / name).write_bytes(payload)


@pytest.fixture(scope="module")
def complete_collection(tmp_path_factory):
    root = tmp_path_factory.mktemp("i135-complete-proof")
    manifest = root / "launch_manifest.json"
    manifest_value = _manifest()
    manifest.write_text(json.dumps(manifest_value, indent=2, sort_keys=True) + "\n")
    log = root / "sentinel-i135.log"
    decisions = root / "decisions"
    runs = root / "runs"
    runtime_evidence = _runtime_evidence(c.sha256_file(manifest), manifest_value)
    _make_log(log, c.sha256_file(manifest), runtime_evidence)
    _make_decisions(decisions)
    _make_runs(runs)
    proof_a = root / "proof-a"
    proof_b = root / "proof-b"
    for proof in (proof_a, proof_b):
        c.collect_proof(
            run_log=log,
            decision_root=decisions,
            runs_root=runs,
            launch_manifest=manifest,
            proof_dir=proof,
            free_bytes_provider=lambda _path: TEST_FREE_BYTES,
            runtime_evidence_provider=lambda _path, role: runtime_evidence[role],
        )
    return {
        "root": root,
        "manifest": manifest,
        "log": log,
        "decisions": decisions,
        "runs": runs,
        "proof_a": proof_a,
        "proof_b": proof_b,
        "runtime_evidence": runtime_evidence,
    }


def test_collection_is_complete_deterministic_and_identity_preserving(complete_collection):
    proof_a = complete_collection["proof_a"]
    proof_b = complete_collection["proof_b"]
    names = sorted(path.name for path in proof_a.iterdir())
    assert names == sorted(
        [
            "SHA256SUMS.txt",
            "i135-runs.tar.gz",
            "analytic_lock.json",
            "dataset_runtime_snapshot.json",
            "docker_runtime_snapshot.json",
            "launch_validity_receipt.json",
            "raw_proof_receipt.json",
            "sentinel-i135.log.gz",
            *c.DECISION_FILENAMES.values(),
        ]
    )
    for name in names:
        assert (proof_a / name).read_bytes() == (proof_b / name).read_bytes()

    raw = json.loads((proof_a / "raw_proof_receipt.json").read_text())
    assert raw["schema"] == c.SCHEMA
    assert raw["verdict"] == "I135_RAW_PROOF_COMPLETE"
    assert raw["completion"] == {
        "analytic_cells": 2400,
        "decision_blocks": 120,
        "decision_resets": 2400,
        "done_marker": c.DONE_MARKER,
        "done_marker_count": 1,
        "run_archive_cells": 2400,
        "run_archive_members": 7200,
        "successful_blocks": 120,
    }
    assert set(raw["artifacts"]) == {
        "i135_log",
        "i135_runs",
        "analytic_lock",
        "dataset_runtime_snapshot",
        "docker_runtime_snapshot",
        "validity_receipt",
        *(f"decision_{arm}" for arm in c.ARMS),
    }

    checksums = c._parse_checksums(proof_a / "SHA256SUMS.txt")
    assert set(checksums) == set(names) - {"SHA256SUMS.txt"}
    for name, digest in checksums.items():
        assert c.sha256_file(proof_a / name) == digest

    with gzip.open(proof_a / c.DECISION_FILENAMES["off_baseline"], "rt") as handle:
        first = json.loads(next(handle))
    assert first == {
        "arm": "off_baseline",
        "block_identity": True,
        "class": "stationary",
        "pair": "0099",
    }
    with gzip.open(proof_a / c.DECISION_FILENAMES["blind_1_0x"], "rt") as handle:
        first_blind = json.loads(next(handle))
    assert first_blind == {
        "class": "stationary",
        "dose": "blind_1_0x",
        "pair": "0099",
        "reset": True,
        "run": 0,
    }

    with tarfile.open(proof_a / "i135-runs.tar.gz", "r:gz") as archive:
        members = archive.getmembers()
    assert len(members) == 7200
    assert all(member.mtime == 0 and member.uid == 0 and member.gid == 0 for member in members)
    assert [member.name for member in members[:3]] == [
        "i135-off/stationary-0099/run_0/ego_poses.json",
        "i135-off/stationary-0099/run_0/metrics.json",
        "i135-off/stationary-0099/run_0/actors.json",
    ]
    for role, filename in c.RUNTIME_EVIDENCE_FILENAMES.items():
        assert (proof_a / filename).read_bytes() == complete_collection["runtime_evidence"][
            role
        ][0]
    assert raw["source_receipts"]["launcher_log"]["dataset_runtime_check_counts"] == {
        "analytic-arm": 1,
        "before": 120,
        "after": 120,
        "before-done": 1,
    }
    assert raw["source_receipts"]["runtime_evidence"]["analytic_lock"][
        "source_id"
    ] == DEFAULT_LOCK_ID


def test_validity_receipt_is_mechanically_derived(complete_collection):
    proof = complete_collection["proof_a"]
    receipt = json.loads((proof / "launch_validity_receipt.json").read_text())
    assert receipt["schema"] == c.VALIDITY_SCHEMA
    assert receipt["gates"] == {gate: True for gate in c.REQUIRED_MANIFEST_GATES}
    assert "G7" not in receipt["gates"]
    assert receipt["dataset_provenance"]["manifest_gate"] == "g7_dataset_provenance"
    assert receipt["dataset_provenance"]["passed"] is True
    assert receipt["dataset_provenance"]["runtime_snapshot_contract"]["file_count"] == 28
    assert receipt["docker_runtime_provenance"]["context"] == "default"
    assert receipt["analytic_lock_provenance"]["source_id"] == DEFAULT_LOCK_ID
    assert receipt["analytic_gpu_hours"] == pytest.approx(ELAPSED_SECONDS / 3600)
    assert receipt["total_gpu_hours_including_smoke"] == pytest.approx(
        (ELAPSED_SECONDS + PRIOR_SMOKE_SECONDS) / 3600
    )
    assert receipt["remote_projected_reserve_gib"] == 125
    assert receipt["local_free_gib_at_collection"] == 20
    assert receipt["retry_policy_violations"] == 0
    assert receipt["unexpected_falsifiers"] == []
    assert "derivation" in receipt


@pytest.mark.parametrize(
    ("mutation", "problem"),
    [
        (lambda manifest: manifest.update(schema="iter135.launch_manifest.v1"), "schema"),
        (
            lambda manifest: manifest["gates"].pop("g7_dataset_provenance"),
            "gate-set",
        ),
        (
            lambda manifest: manifest["gates"].update(g7_dataset_provenance=False),
            "gate-not-green:g7_dataset_provenance",
        ),
        (lambda manifest: manifest.pop("dataset_receipt"), "dataset-environment-mismatch"),
    ],
)
def test_manifest_v2_requires_distinct_dataset_gate_and_receipt(tmp_path, mutation, problem):
    manifest = _manifest()
    mutation(manifest)
    path = tmp_path / "launch_manifest.json"
    path.write_text(json.dumps(manifest, sort_keys=True) + "\n")

    with pytest.raises(c.ProofCollectionError, match=problem):
        c.validate_manifest(path)


def test_manifest_rejects_dataset_environment_and_frozen_archive_drift(tmp_path):
    mismatched = _manifest()
    environment_dataset = json.loads(
        json.dumps(mismatched["dataset_receipt"])
    )
    mismatched["environment_receipts"]["dataset"] = environment_dataset
    environment_dataset["identity"]["dataset_realpath"] = "/datasets/substituted"
    mismatch_path = tmp_path / "environment-mismatch.json"
    mismatch_path.write_text(json.dumps(mismatched, sort_keys=True) + "\n")
    with pytest.raises(c.ProofCollectionError, match="dataset-environment-mismatch"):
        c.validate_manifest(mismatch_path)

    drifted = _manifest()
    dataset = drifted["dataset_receipt"]
    first_archive = next(iter(c.EXPECTED_DATASET_ARCHIVES))
    dataset["archives"][first_archive]["sha256"] = "0" * 64
    payload = dict(dataset)
    payload.pop("receipt_payload_sha256")
    dataset["receipt_payload_sha256"] = c._canonical_json_sha256(payload)
    drifted["environment_receipts"]["dataset"] = dataset
    drift_path = tmp_path / "archive-drift.json"
    drift_path.write_text(json.dumps(drifted, sort_keys=True) + "\n")
    with pytest.raises(c.ProofCollectionError, match="expected-sha256"):
        c.validate_manifest(drift_path)


def test_log_requires_every_dataset_runtime_check_phase(tmp_path):
    path = tmp_path / "missing-runtime-check.log"
    _make_log(path)
    path.write_text(
        path.read_text().replace(
            "I135_DATASET_RUNTIME_OK phase=before files=28\n",
            "",
            1,
        )
    )

    with pytest.raises(c.ProofCollectionError, match="dataset-runtime-check-counts"):
        c.validate_run_log(path, _log_facts())


def test_runtime_evidence_binds_snapshot_and_lock_bytes_to_logged_source_ids(tmp_path):
    manifest_value = _manifest()
    manifest_path = tmp_path / "launch_manifest.json"
    manifest_path.write_text(json.dumps(manifest_value, sort_keys=True) + "\n")
    manifest, manifest_facts = c.validate_manifest(manifest_path)
    evidence = _runtime_evidence(c.sha256_file(manifest_path), manifest_value)
    log_path = tmp_path / "sentinel-i135.log"
    _make_log(log_path, c.sha256_file(manifest_path), evidence)
    log_receipt = c.validate_run_log(log_path, manifest_facts)
    payloads = {role: row[0] for role, row in evidence.items()}
    source_ids = {role: row[1] for role, row in evidence.items()}

    receipts = c.validate_runtime_evidence_payloads(
        payloads,
        source_ids=source_ids,
        manifest=manifest,
        manifest_facts=manifest_facts,
        log_receipt=log_receipt,
    )
    assert receipts["dataset_runtime_snapshot"]["file_count"] == 28
    assert receipts["analytic_lock"]["source_id"] == DEFAULT_LOCK_ID

    drifted_ids = {**source_ids, "dataset_runtime_snapshot": "66308:99999"}
    with pytest.raises(c.ProofCollectionError, match="dataset:source-id"):
        c.validate_runtime_evidence_payloads(
            payloads,
            source_ids=drifted_ids,
            manifest=manifest,
            manifest_facts=manifest_facts,
            log_receipt=log_receipt,
        )

    lock = json.loads(payloads["analytic_lock"])
    lock["dataset_runtime_snapshot_sha256"] = "0" * 64
    drifted_payloads = {
        **payloads,
        "analytic_lock": (json.dumps(lock, sort_keys=True) + "\n").encode(),
    }
    with pytest.raises(c.ProofCollectionError, match="analytic-lock:dataset"):
        c.validate_runtime_evidence_payloads(
            drifted_payloads,
            source_ids=source_ids,
            manifest=manifest,
            manifest_facts=manifest_facts,
            log_receipt=log_receipt,
        )


def test_collection_free_space_gate_has_no_production_environment_bypass(tmp_path, monkeypatch):
    monkeypatch.setenv("SENTINEL_TEST_FREE_BYTES", str(100 * 1024**3))
    proof = tmp_path / "proof"
    with pytest.raises(c.ProofCollectionError, match="local-free-space"):
        c.collect_proof(
            run_log=tmp_path / "missing-log",
            decision_root=tmp_path / "missing-decisions",
            runs_root=tmp_path / "missing-runs",
            launch_manifest=tmp_path / "missing-manifest",
            proof_dir=proof,
            free_bytes_provider=lambda _path: c.MINIMUM_LOCAL_FREE_BYTES - 1,
        )
    assert not proof.exists()


def test_log_with_any_abort_fails_even_if_a_done_marker_exists(tmp_path):
    path = tmp_path / "hostile.log"
    _make_log(path)
    lines = path.read_text().splitlines(keepends=True)
    lines.insert(-1, "I135_ABORT injected-after-success\n")
    path.write_text("".join(lines))
    facts = _log_facts()
    with pytest.raises(c.ProofCollectionError, match="failure-marker"):
        c.validate_run_log(path, facts)


@pytest.mark.parametrize(
    ("old", "new", "problem"),
    [
        (
            f"manifest_sha256={DEFAULT_MANIFEST_SHA256}",
            f"manifest_sha256={'b' * 64}",
            "invocation-manifest-sha256",
        ),
        (
            f"end_free_bytes={110 * 1024**3}",
            "end_free_bytes=1",
            "end-free-below-reserve",
        ),
        (
            f"episodes=2400 output_root={c.EXPECTED_OUTPUT_ROOT}",
            "episodes=2400 output_root=/tmp/substituted",
            "done-output_root",
        ),
        (
            f"launch_lock_retained={c.EXPECTED_LAUNCH_LOCK}",
            "launch_lock_retained=/tmp/removed-lock",
            "done-launch_lock_retained",
        ),
        (
            f"dataset_runtime_snapshot_id={DEFAULT_DATASET_SNAPSHOT_ID}",
            "dataset_runtime_snapshot_id=66308:99999",
            "done-dataset_runtime_snapshot_id",
        ),
        (
            f"launch_lock_id={DEFAULT_LOCK_ID}",
            "launch_lock_id=66308:99999",
            "done-launch_lock_id",
        ),
    ],
)
def test_log_replay_binds_manifest_runtime_and_storage_metadata(tmp_path, old, new, problem):
    path = tmp_path / "hostile.log"
    _make_log(path)
    path.write_text(path.read_text().replace(old, new, 1))

    with pytest.raises(c.ProofCollectionError, match=problem):
        c.validate_run_log(path, _log_facts())


def test_collection_packages_the_exact_log_bytes_it_validated(
    complete_collection, tmp_path, monkeypatch
):
    source = complete_collection["log"]
    original_payload = source.read_bytes()
    real_validator = c.validate_run_log_payload

    def replace_after_validation(payload, facts):
        receipt = real_validator(payload, facts)
        source.write_bytes(b"I135_ABORT validate-then-reopen-substitution\n")
        return receipt

    monkeypatch.setattr(c, "validate_run_log_payload", replace_after_validation)
    proof = tmp_path / "proof"
    try:
        c.collect_proof(
            run_log=source,
            decision_root=complete_collection["decisions"],
            runs_root=complete_collection["runs"],
            launch_manifest=complete_collection["manifest"],
            proof_dir=proof,
            free_bytes_provider=lambda _path: TEST_FREE_BYTES,
            runtime_evidence_provider=lambda _path, role: complete_collection[
                "runtime_evidence"
            ][role],
        )
    finally:
        source.write_bytes(original_payload)

    assert gzip.decompress((proof / "sentinel-i135.log.gz").read_bytes()) == original_payload
    raw = json.loads((proof / "raw_proof_receipt.json").read_text())
    assert raw["source_receipts"]["launcher_log"]["sha256"] == hashlib.sha256(
        original_payload
    ).hexdigest()


def test_decision_block_rejects_wrong_semantic_identity_and_reset_order(tmp_path):
    source = tmp_path / "bad.jsonl"
    rows = [
        {
            "block_identity": True,
            "arm": "off_baseline",
            "class": "frontal",
            "pair": "0099",
        },
        *({"reset": True, "run": run} for run in reversed(c.RUNS)),
    ]
    source.write_text("".join(json.dumps(row) + "\n" for row in rows))
    with pytest.raises(c.ProofCollectionError, match="class-identity"):
        c._validate_and_copy_decision_block(
            source,
            io.BytesIO(),
            "off_baseline",
            "stationary",
            "0099",
        )


def test_runs_tree_requires_actors_for_every_cell(complete_collection, tmp_path):
    copied = tmp_path / "runs"
    shutil.copytree(complete_collection["runs"], copied, copy_function=os.link)
    missing = copied / "i135-off/stationary-0099/run_0/actors.json"
    missing.unlink()
    with pytest.raises(c.ProofCollectionError, match="tree-not-exact:runs:off_baseline"):
        c.validate_runs_tree(copied)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, stdout=subprocess.PIPE)


def _committed_proof_repo(complete_collection, repo: Path) -> tuple[Path, Path]:
    repo.mkdir()
    manifest = repo / "launch_manifest.json"
    shutil.copy2(complete_collection["manifest"], manifest)
    proof = repo / "proof"
    shutil.copytree(complete_collection["proof_a"], proof)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "sentinel@example.invalid")
    _git(repo, "config", "user.name", "Sentinel Test")
    _git(repo, "add", "launch_manifest.json", "proof")
    _git(repo, "commit", "-q", "-m", "commit raw proof")
    return manifest, proof


def _forge_artifact_receipts_and_commit(repo: Path, proof: Path, role: str, path: Path) -> None:
    raw_path = proof / "raw_proof_receipt.json"
    raw = json.loads(raw_path.read_text())
    raw["artifacts"][role] = c._artifact_receipt(path, path.name)
    raw_path.write_bytes(c._canonical_json(raw))
    checksums = c._parse_checksums(proof / "SHA256SUMS.txt")
    checksums[path.name] = c.sha256_file(path)
    checksums[raw_path.name] = c.sha256_file(raw_path)
    (proof / "SHA256SUMS.txt").write_text(
        "".join(f"{digest}  {name}\n" for name, digest in sorted(checksums.items())),
        encoding="ascii",
    )
    _git(repo, "add", "proof")
    _git(repo, "commit", "-q", "-m", "commit hostile handcrafted proof")


def test_verify_committed_emits_exact_analyzer_contract_and_rejects_dirty_proof(
    complete_collection, tmp_path
):
    repo = tmp_path / "repo"
    manifest, proof = _committed_proof_repo(complete_collection, repo)

    receipt = c.verify_committed_proof(
        launch_manifest=manifest,
        proof_dir=proof,
        repository_root=repo,
    )
    assert set(receipt) == {
        "schema",
        "launch_manifest_sha256",
        "repository_root",
        "proof_commit",
        "inputs",
        "problem_count",
        "problems",
    }
    assert receipt["schema"] == c.COMMITTED_SCHEMA
    assert receipt["repository_root"] == str(repo.resolve())
    assert receipt["problem_count"] == 0
    assert receipt["problems"] == []
    assert set(receipt["inputs"]) == {
        "i135_log",
        "i135_runs",
        "analytic_lock",
        "dataset_runtime_snapshot",
        "docker_runtime_snapshot",
        "validity_receipt",
        "raw_proof_receipt",
        *(f"decision_{arm}" for arm in c.ARMS),
    }
    for rows in receipt["inputs"].values():
        assert len(rows) == 1
        assert set(rows[0]) == {"path", "sha256", "bytes"}
        assert not Path(rows[0]["path"]).is_absolute()

    with (repo / "proof/sentinel-i135.log.gz").open("ab") as handle:
        handle.write(b"hostile")
    with pytest.raises(c.ProofCollectionError, match="repository-not-clean"):
        c.verify_committed_proof(
            launch_manifest=manifest,
            proof_dir=proof,
            repository_root=repo,
        )


def test_verify_committed_replays_semantics_not_handcrafted_completion_claims(
    complete_collection, tmp_path
):
    repo = tmp_path / "repo"
    manifest, proof = _committed_proof_repo(complete_collection, repo)
    arm = "blind_2_0x"
    decision = proof / c.DECISION_FILENAMES[arm]
    rows = gzip.decompress(decision.read_bytes()).splitlines(keepends=True)
    cut = max(
        index
        for index, line in enumerate(rows)
        if json.loads(line).get("reset") is True and json.loads(line).get("run") == 0
    )
    decision.write_bytes(gzip.compress(b"".join(rows[:cut]), compresslevel=9, mtime=0))
    _forge_artifact_receipts_and_commit(repo, proof, f"decision_{arm}", decision)

    with pytest.raises(c.ProofCollectionError, match="decision:packaged-block-count"):
        c.verify_committed_proof(
            launch_manifest=manifest,
            proof_dir=proof,
            repository_root=repo,
        )


def test_verify_committed_tar_replay_rejects_missing_actors_member(
    complete_collection, tmp_path
):
    repo = tmp_path / "repo"
    manifest, proof = _committed_proof_repo(complete_collection, repo)
    runs = proof / "i135-runs.tar.gz"
    replacement = proof / "replacement.tar.gz"
    removed = False
    with tarfile.open(runs, "r:gz") as source, tarfile.open(replacement, "w:gz") as target:
        for member in source.getmembers():
            if not removed and member.name.endswith("/actors.json"):
                removed = True
                continue
            extracted = source.extractfile(member)
            assert extracted is not None
            target.addfile(member, extracted)
    replacement.replace(runs)
    _forge_artifact_receipts_and_commit(repo, proof, "i135_runs", runs)

    with pytest.raises(c.ProofCollectionError, match="runs:packaged-member-order-or-set"):
        c.verify_committed_proof(
            launch_manifest=manifest,
            proof_dir=proof,
            repository_root=repo,
        )
