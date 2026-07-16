"""Hostile tests for the frozen Iteration-135 raw-proof analyzer."""

import copy
import gzip
import hashlib
import json
import math
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from experiments.iter135_neuroncap_blind_braking_dose_response import analyze_dose135 as a

analyzer = a

DATASET_SNAPSHOT_ID = "66308:13501"
DOCKER_SNAPSHOT_ID = "66308:13502"
ANALYTIC_LOCK_ID = "66308:13503"
PYTHON_WRAPPER_SHA256 = "d" * 64
PYTHON_BINARY_SHA256 = "e" * 64
PYTHON_BINARY_IDENTITY = "66305:13504"


def _github_launch_authority(manifest_sha256: str) -> dict:
    activation_commit = "f" * 40
    authority = {
        "schema": "iter135.github_launch_authority.v1",
        "repository": "manfromnowhere143/sentinel",
        "branch": "master",
        "activation_commit": activation_commit,
        "final_manifest_commit": "a" * 40,
        "activation_receipt_sha256": "b" * 64,
        "manifest_sha256": manifest_sha256,
        "checks": [
            {
                "name": name,
                "id": check_id,
                "head_sha": activation_commit,
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


def _dataset_receipt() -> dict:
    identity = {
        "dataset_root": a.EXPECTED_DATASET_ROOT,
        "dataset_realpath": a.EXPECTED_DATASET_ROOT,
        "dataset_is_symlink": False,
        "dataset_version": a.EXPECTED_DATASET_VERSION,
        "archive_root": a.EXPECTED_DATASET_ARCHIVE_ROOT,
        "archive_realpath": a.EXPECTED_DATASET_ARCHIVE_ROOT,
        "archive_is_symlink": False,
        "metadata_root": a.EXPECTED_DATASET_METADATA_ROOT,
        "metadata_realpath": a.EXPECTED_DATASET_METADATA_ROOT,
        "metadata_is_symlink": False,
        "map_root": a.EXPECTED_DATASET_MAP_ROOT,
        "map_realpath": a.EXPECTED_DATASET_MAP_ROOT,
        "map_is_symlink": False,
        **a.EXPECTED_DATASET_MOUNT,
        "dataset_st_dev": 66_308,
        "mount_st_dev": 66_308,
        "root_st_dev": 66_305,
    }
    receipt = {
        "schema": a.DATASET_SCHEMA,
        "contract_sha256": a.EXPECTED_DATASET_CONTRACT_SHA256,
        "proof_basis": a.EXPECTED_DATASET_PROOF_BASIS,
        "identity": identity,
        "archives": {
            name: {
                "path": f"{a.EXPECTED_DATASET_ARCHIVE_ROOT}/{name}",
                "sha256": digest,
                "bytes": byte_count,
            }
            for name, (digest, byte_count) in a.EXPECTED_DATASET_ARCHIVES.items()
        },
        "metadata_json": {
            name: {
                "path": f"{a.EXPECTED_DATASET_METADATA_ROOT}/{name}",
                "sha256": hashlib.sha256(f"metadata:{name}".encode()).hexdigest(),
                "bytes": index + 1,
            }
            for index, name in enumerate(a.EXPECTED_DATASET_METADATA_FILES)
        },
        "map_anchors": {
            name: {
                "path": f"{a.EXPECTED_DATASET_MAP_ROOT}/{name}",
                "sha256": hashlib.sha256(f"map:{name}".encode()).hexdigest(),
                "bytes": index + 101,
            }
            for index, name in enumerate(a.EXPECTED_DATASET_MAP_ANCHORS)
        },
    }
    receipt["receipt_payload_sha256"] = a._canonical_json_sha256(receipt)
    return receipt


def _manifest(*, hash_bound_files: dict | None = None) -> dict:
    dataset = _dataset_receipt()
    return {
        "schema": a.LAUNCH_MANIFEST_SCHEMA,
        "verdict": "I135_TOOLING_MANIFEST_OK",
        "launch_authorized": True,
        "gates": {
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
        },
        "dataset_receipt": dataset,
        "environment_receipts": {
            "schema": a.ENVIRONMENT_SCHEMA,
            "dataset": dataset,
        },
        "hash_bound_files": {
            "env_receipts.json": {
                "source_path": "env_receipts.json",
                "sha256": "e" * 64,
                "bytes": 135,
            },
            **(hash_bound_files or {}),
        },
    }


def _runtime_evidence(manifest_sha: str, manifest: dict) -> dict[str, bytes]:
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
        "schema": a.DATASET_RUNTIME_SCHEMA,
        "manifest_sha256": manifest_sha,
        "dataset_receipt_payload_sha256": dataset["receipt_payload_sha256"],
        "dataset_root": {
            "path": a.EXPECTED_DATASET_ROOT,
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
        "schema": a.DOCKER_RUNTIME_SCHEMA,
        "manifest_sha256": manifest_sha,
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
    dataset_payload = a._canonical_runtime_snapshot(dataset_snapshot)
    docker_payload = a._canonical_runtime_snapshot(docker_snapshot)
    lock = {
        "schema": a.ANALYTIC_LOCK_SCHEMA,
        "manifest_sha256": manifest_sha,
        "dataset_runtime_snapshot_sha256": hashlib.sha256(dataset_payload).hexdigest(),
        "docker_runtime_snapshot_sha256": hashlib.sha256(docker_payload).hexdigest(),
        "python_wrapper_sha256": PYTHON_WRAPPER_SHA256,
        "python_binary_sha256": PYTHON_BINARY_SHA256,
        "python_binary_identity": PYTHON_BINARY_IDENTITY,
        "github_launch_authority": _github_launch_authority(manifest_sha),
        "pid": 135,
        "created_at_utc": "2026-07-16T00:00:00Z",
    }
    return {
        "dataset_runtime_snapshot": dataset_payload,
        "docker_runtime_snapshot": docker_payload,
        "analytic_lock": (json.dumps(lock, sort_keys=True) + "\n").encode(),
    }


def _runtime_log(manifest_sha: str, evidence: dict[str, bytes]) -> bytes:
    dataset_sha = hashlib.sha256(evidence["dataset_runtime_snapshot"]).hexdigest()
    docker_sha = hashlib.sha256(evidence["docker_runtime_snapshot"]).hexdigest()
    runtime_root = f"/var/lib/sentinel/i135-runtime-{manifest_sha}"
    lines = [
        f"I135_INVOCATION_START at=2026-07-16T00:00:00Z pid=135 manifest_sha256={manifest_sha}\n",
        f"I135_RUNTIME_SNAPSHOT_OK manifest_sha256={manifest_sha} path={runtime_root}\n",
        f"I135_DATASET_SNAPSHOT_OK sha256={dataset_sha} id={DATASET_SNAPSHOT_ID} files=28\n",
        f"I135_DOCKER_SNAPSHOT_OK sha256={docker_sha} id={DOCKER_SNAPSHOT_ID}\n",
        "I135_ANALYTIC_ARMED lock=/var/lib/sentinel/i135-analytic.lock "
        f"lock_id={ANALYTIC_LOCK_ID} "
        "output_root=/datasets/nuscenes-full/sentinel-i135-outoutput "
        f"python_wrapper_sha256={PYTHON_WRAPPER_SHA256} "
        f"python_binary_sha256={PYTHON_BINARY_SHA256} "
        f"python_binary_identity={PYTHON_BINARY_IDENTITY}\n",
        "I135_DATASET_RUNTIME_OK phase=analytic-arm files=28\n",
        "I135_DOCKER_RUNTIME_OK phase=analytic-arm daemon_id=sentinel-daemon-135\n",
    ]
    for _ in range(120):
        lines.extend(
            [
                "I135_DATASET_RUNTIME_OK phase=before files=28\n",
                "I135_DOCKER_RUNTIME_OK phase=before daemon_id=sentinel-daemon-135\n",
                "I135_DATASET_RUNTIME_OK phase=after files=28\n",
                "I135_DOCKER_RUNTIME_OK phase=after daemon_id=sentinel-daemon-135\n",
            ]
        )
    lines.extend(
        [
            "I135_DATASET_RUNTIME_OK phase=before-done files=28\n",
            "I135_DOCKER_RUNTIME_OK phase=before-done daemon_id=sentinel-daemon-135\n",
            "I135_DONE_METADATA at=2026-07-16T01:00:00Z "
            f"manifest_sha256={manifest_sha} runtime_snapshot={runtime_root} "
            f"dataset_runtime_snapshot_sha256={dataset_sha} "
            f"dataset_runtime_snapshot_id={DATASET_SNAPSHOT_ID} "
            f"docker_runtime_snapshot_sha256={docker_sha} "
            f"docker_runtime_snapshot_id={DOCKER_SNAPSHOT_ID} "
            f"python_wrapper_sha256={PYTHON_WRAPPER_SHA256} "
            f"python_binary_sha256={PYTHON_BINARY_SHA256} "
            f"python_binary_identity={PYTHON_BINARY_IDENTITY} "
            "launch_lock_retained=/var/lib/sentinel/i135-analytic.lock "
            f"launch_lock_id={ANALYTIC_LOCK_ID} elapsed_seconds=360 "
            "prior_smoke_gpu_seconds=7 blocks=120 episodes=2400 "
            "output_root=/datasets/nuscenes-full/sentinel-i135-outoutput "
            "output_device=/dev/nvme0n2 "
            "output_uuid=9a98277e-b21f-4ffc-8f14-3f2235b43103 "
            "start_free_bytes=128849018880 end_free_bytes=118111600640 "
            "output_bytes=10737418240\n",
            "I135_DOSE_DONE\n",
        ]
    )
    return "".join(lines).encode()


def _write_runtime_proof(proof: Path, manifest_path: Path, manifest: dict) -> dict:
    proof.mkdir(parents=True, exist_ok=True)
    manifest_sha = a.sha256_file(manifest_path)
    evidence = _runtime_evidence(manifest_sha, manifest)
    (proof / "sentinel-i135.log.gz").write_bytes(
        gzip.compress(_runtime_log(manifest_sha, evidence), mtime=0)
    )
    for role, filename in a.RUNTIME_EVIDENCE_FILENAMES.items():
        (proof / filename).write_bytes(evidence[role])
    log_facts = a.runtime_log_facts(_runtime_log(manifest_sha, evidence))
    runtime_facts, problems = a.validate_runtime_evidence_payloads(
        evidence,
        manifest=manifest,
        manifest_sha=manifest_sha,
        log_facts=log_facts,
    )
    assert problems == []
    return runtime_facts


def _validity_receipt(manifest_path: Path, manifest: dict, runtime_facts: dict) -> dict:
    manifest_sha = a.sha256_file(manifest_path)
    dataset_facts, problems = a.validate_manifest_dataset(manifest)
    assert problems == []
    dataset_runtime = runtime_facts["dataset_runtime_snapshot"]
    docker_runtime = runtime_facts["docker_runtime_snapshot"]
    lock = runtime_facts["analytic_lock"]
    runtime_root = f"/var/lib/sentinel/i135-runtime-{manifest_sha}"
    return {
        "schema": a.VALIDITY_RECEIPT_SCHEMA,
        "launch_manifest_sha256": manifest_sha,
        "gates": {
            gate: True for gate in ("G0", "G1", "G2", "G3", "G4", "G5", "G8", "G9")
        },
        "dataset_provenance": {
            **dataset_facts,
            "manifest_gate": "g7_dataset_provenance",
            "passed": True,
            "runtime_snapshot_contract": {
                "schema": a.DATASET_RUNTIME_SCHEMA,
                "path": f"{runtime_root}/dataset_runtime_snapshot.json",
                "manifest_sha256": manifest_sha,
                "dataset_receipt_payload_sha256": dataset_facts[
                    "dataset_receipt_payload_sha256"
                ],
                "file_count": dataset_facts["dataset_file_count"],
                "sha256": dataset_runtime["sha256"],
                "bytes": dataset_runtime["bytes"],
                "source_id": dataset_runtime["source_id"],
            },
        },
        "docker_runtime_provenance": {
            "schema": a.DOCKER_RUNTIME_SCHEMA,
            "path": docker_runtime["source_path"],
            "manifest_sha256": docker_runtime["manifest_sha256"],
            "sha256": docker_runtime["sha256"],
            "bytes": docker_runtime["bytes"],
            "source_id": docker_runtime["source_id"],
            "client_path": docker_runtime["client_path"],
            "client_sha256": docker_runtime["client_sha256"],
            "context": docker_runtime["context"],
            "endpoint": docker_runtime["endpoint"],
            "daemon_id": docker_runtime["daemon_id"],
            "server_version": docker_runtime["server_version"],
        },
        "analytic_lock_provenance": {
            "schema": a.ANALYTIC_LOCK_SCHEMA,
            "path": lock["source_path"],
            "source_id": lock["source_id"],
            "sha256": lock["sha256"],
            "bytes": lock["bytes"],
            "manifest_sha256": lock["manifest_sha256"],
            "dataset_runtime_snapshot_sha256": lock[
                "dataset_runtime_snapshot_sha256"
            ],
            "docker_runtime_snapshot_sha256": lock["docker_runtime_snapshot_sha256"],
            "python_wrapper_sha256": lock["python_wrapper_sha256"],
            "python_binary_sha256": lock["python_binary_sha256"],
            "python_binary_identity": lock["python_binary_identity"],
            "github_launch_authority": lock["github_launch_authority"],
            "pid": lock["pid"],
            "created_at_utc": lock["created_at_utc"],
        },
        "falsifiers_clear": True,
        "done_marker": "I135_DOSE_DONE",
        "analytic_gpu_hours": 90,
        "remote_free_gib_at_launch": 100,
        "remote_projected_reserve_gib": 25,
        "local_free_gib_at_collection": 15,
        "retry_policy_violations": 0,
        "unexpected_falsifiers": [],
    }


def transform(x, y):
    return [[1.0, 0.0, 0.0, x], [0.0, 1.0, 0.0, y], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def frozen_pair_tables(delta_n=0.3, delta_q=0.0):
    tables = {arm: {} for arm in a.ARMS}
    for pair in a.canonical_pairs():
        for arm in a.ARMS:
            tables[arm][pair] = {
                "ncap": 2.0,
                "q16": 0.7,
                "impact_speed": 1.0,
                "raw_path_length": 10.0,
                "legacy_safe_progress": 1.4,
                "collision_rate": 0.5,
            }
        tables["released_union_semantic_reference"][pair]["ncap"] += delta_n
        tables["released_union_semantic_reference"][pair]["q16"] += delta_q
    return tables


def frontier(*, competitive=False, dominates=False):
    return {
        "doses": {
            arm: {"competitive": competitive, "pareto_dominates": dominates}
            for arm in a.BLIND_ARMS
        }
    }


def primary(*, confirm=False, competitive=False, reverse=False):
    return {
        "confirmatory_gate": confirm,
        "blind_primary_competitive": competitive,
        "blind_primary_reverse_dominance": reverse,
    }


def test_q16_uses_only_first_16_sorted_poses_and_absorbs_early_terminal():
    poses = {str(index): transform(float(index), 0.0) for index in reversed(range(20))}
    assert a.q16_distance(poses) == 15.0
    early = {str(index): transform(float(index), 0.0) for index in reversed(range(4))}
    assert a.q16_distance(early) == 3.0


def test_raw_metrics_collision_is_authoritative_not_impact_speed():
    cells = sorted(a.expected_cells())
    collided_with_zero_impact = cells[0]
    noncollision_with_positive_impact = cells[1]
    scores = {
        collided_with_zero_impact: a.ScoreRow(ncap=4.0, impact_speed=0.0),
        noncollision_with_positive_impact: a.ScoreRow(ncap=3.0, impact_speed=9.0),
    }
    artifacts = {
        collided_with_zero_impact: a.RunArtifact(
            ego_poses={"0": transform(0.0, 0.0), "1": transform(1.0, 0.0)},
            metrics={"ncap_score": 4.0, "any_collide@0.0s": True},
        ),
        noncollision_with_positive_impact: a.RunArtifact(
            ego_poses={"0": transform(0.0, 0.0), "1": transform(1.0, 0.0)},
            metrics={"ncap_score": 3.0, "any_collide@0.0s": False},
        ),
    }

    episodes, _problems = a.assemble_episodes(scores, artifacts)

    assert episodes[collided_with_zero_impact].collision is True
    assert episodes[noncollision_with_positive_impact].collision is False


def test_missing_or_nonboolean_raw_collision_field_rejects_episode():
    cell = next(iter(a.expected_cells()))
    scores = {cell: a.ScoreRow(ncap=1.0, impact_speed=0.0)}
    artifacts = {
        cell: a.RunArtifact(
            ego_poses={"0": transform(0.0, 0.0)},
            metrics={"ncap_score": 1.0, "any_collide@0.0s": 1},
        )
    }

    episodes, problems = a.assemble_episodes(scores, artifacts)

    assert cell not in episodes
    assert any("metrics-collision-missing-or-nonboolean" in row for row in problems)


def test_run_artifact_loader_requires_actors_json_at_raw_boundary(tmp_path):
    cell = ("off_baseline", "stationary", "0099", 0)
    run = tmp_path / "i135-off/stationary-0099/run_0"
    run.mkdir(parents=True)
    (run / "ego_poses.json").write_text("{}\n")
    (run / "metrics.json").write_text("{}\n")

    artifacts, problems = a.load_run_artifacts(
        tmp_path,
        a.ARM_DIRS,
        {cell},
    )

    assert artifacts == {}
    assert f"runs:missing:{a.cell_id(cell)}:actors" in problems


def test_frozen_quantile_indices_are_exact_order_statistics():
    draws = list(reversed(range(a.BOOT_DRAWS)))
    bounds = a.frozen_bounds(draws)
    assert bounds.lcb95 == 4_999
    assert bounds.ucb95 == 94_999
    assert bounds.ci95 == (2_499, 97_499)


def test_frozen_quantiles_reject_any_other_draw_count():
    with pytest.raises(a.AnalysisInputError, match="requires 100000 draws"):
        a.frozen_bounds([0.0] * 99_999)


def test_paired_class_bootstrap_carries_every_contrast_on_same_draw():
    tables = frozen_pair_tables(delta_n=0.3, delta_q=-0.02)
    draws = a.class_stratified_draws(tables, draws=25, seed=a.BOOT_SEED)
    assert set(draws) == {
        f"{arm}:{metric}" for arm in a.BLIND_ARMS for metric in ("ncap", "q16")
    }
    for arm in a.BLIND_ARMS:
        assert draws[f"{arm}:ncap"] == pytest.approx([0.3] * 25)
        assert draws[f"{arm}:q16"] == pytest.approx([-0.02] * 25)


def test_max_t_zero_se_contrasts_get_exact_intervals_and_leave_empty_maximum():
    points = {"a": 0.25, "b": -0.05}
    draws = {
        "a": [0.25] * a.BOOT_DRAWS,
        "b": [-0.05] * a.BOOT_DRAWS,
    }
    critical, intervals = a.simultaneous_max_t(points, draws)
    assert critical == 0.0
    assert intervals["a"]["zero_se"] is True
    assert intervals["a"]["simultaneous_ci95"] == [0.25, 0.25]
    assert intervals["b"]["simultaneous_ci95"] == [-0.05, -0.05]


def test_max_t_fails_closed_on_missing_or_extra_contrast():
    with pytest.raises(a.AnalysisInputError, match="contrast family mismatch"):
        a.simultaneous_max_t({"a": 0.0, "b": 0.0}, {"a": [0.0] * a.BOOT_DRAWS})


def test_missing_analytic_cell_is_hostile_not_silently_filtered():
    exact = a.expected_cells()
    missing = next(iter(exact))
    problems = a.validate_exact_cells(exact - {missing}, exact)
    assert problems
    assert any("missing-cells:1" in problem for problem in problems)


def test_merged_log_rejects_missing_cell_score_and_noncanonical_execution(tmp_path):
    log = tmp_path / "i135.log"
    log.write_text(
        "##### I135BLOCK off_baseline stationary 0099 #####\n"
        "I135_DOSE_DONE\n"
    )
    scores, problems, _ = a.parse_i135_log(log)
    assert scores == {}
    assert any("block-score-count" in problem for problem in problems)
    assert any("missing-cells" in problem for problem in problems)
    assert any("execution-order" in problem for problem in problems)


def test_amended_execution_order_is_exactly_120_contiguous_twenty_run_blocks():
    blocks = a.expected_execution_blocks()
    flattened = a.expected_execution_order()
    assert len(blocks) == 120
    assert len(flattened) == 2_400
    assert len(set(flattened)) == 2_400
    for block_index, block in enumerate(blocks):
        chunk = flattened[block_index * 20 : (block_index + 1) * 20]
        assert chunk == [(*block, run) for run in range(20)]
    for pair_index in range(20):
        pair_blocks = blocks[pair_index * 6 : (pair_index + 1) * 6]
        cls, seq = a.canonical_pairs()[pair_index]
        rotation = pair_index % 6
        assert [arm for arm, _, _ in pair_blocks] == list(a.ARMS[rotation:] + a.ARMS[:rotation])
        assert {(block_cls, block_seq) for _, block_cls, block_seq in pair_blocks} == {(cls, seq)}


def test_block_log_parser_binds_each_next_twenty_scores_to_runs_zero_through_nineteen(tmp_path):
    lines = []
    for arm, cls, seq in a.expected_execution_blocks():
        lines.append(f"##### I135BLOCK {arm} {cls} {seq} #####\n")
        lines.extend(
            f"ncap_score: {run / 10:.1f},  impact_speed: 0.0, reference_speed: 1.0\n"
            for run in range(20)
        )
    lines.append("I135_DOSE_DONE\n")
    log = tmp_path / "complete-i135.log"
    log.write_text("".join(lines))
    scores, problems, flattened = a.parse_i135_log(log)
    assert problems == []
    assert len(scores) == 2_400
    assert flattened == a.expected_execution_order()
    first_block = a.expected_execution_blocks()[0]
    assert [scores[(*first_block, run)].ncap for run in range(20)] == pytest.approx(
        [run / 10 for run in range(20)]
    )


def test_block_log_parser_rejects_short_long_and_out_of_order_blocks(tmp_path):
    first, second = a.expected_execution_blocks()[:2]
    lines = [f"##### I135BLOCK {first[0]} {first[1]} {first[2]} #####\n"]
    lines.extend("ncap_score: 1.0,  impact_speed: 0.0\n" for _ in range(19))
    # Deliberately swap identity, then emit 21 scores.
    lines.append(f"##### I135BLOCK {second[0]} {second[1]} 9999 #####\n")
    lines.extend("ncap_score: 1.0,  impact_speed: 0.0\n" for _ in range(21))
    lines.append("I135_DOSE_DONE\n")
    log = tmp_path / "hostile-i135.log"
    log.write_text("".join(lines))
    _, problems, _ = a.parse_i135_log(log)
    assert any(":19/20:" in problem for problem in problems)
    assert any("too-many-scores" in problem for problem in problems)
    assert any("unexpected-block" in problem for problem in problems)
    assert any("block-order" in problem for problem in problems)


def test_current_frozen_schedule_passes_analyzer_integrity_adapter():
    path = (
        a.pathlib.Path(__file__).resolve().parents[1]
        / "experiments"
        / "iter135_neuroncap_blind_braking_dose_response"
        / "dose_schedules.json"
    )
    schedules, problems, raw = a.load_schedule(path)
    assert raw["schema"] == "iter135.nested_dose_schedules.v1"
    assert len(schedules) == 1_600
    assert problems == []


def test_primary_verdict_order_generic_dominance_precedes_semantic_confirmation():
    verdict, qualifier = a.decide_verdict(
        True,
        primary(confirm=True, competitive=True, reverse=True),
        frontier(competitive=True, dominates=False),
    )
    assert verdict == "GENERIC_BRAKING_DOMINATES"
    assert qualifier == "BLIND_FRONTIER_COMPETITIVE"


@pytest.mark.parametrize(
    ("p", "f", "expected_verdict", "expected_qualifier"),
    [
        (
            primary(confirm=True),
            frontier(),
            "SEMANTIC_MATCHED_BUDGET_CONFIRMED",
            "NO_BLIND_FRONTIER_COMPETITIVENESS_ESTABLISHED",
        ),
        (
            primary(competitive=True),
            frontier(competitive=True),
            "BLIND_MATCHED_BUDGET_COMPETITIVE",
            "BLIND_FRONTIER_COMPETITIVE",
        ),
        (
            primary(),
            frontier(),
            "MATCHED_BUDGET_INCONCLUSIVE",
            "NO_BLIND_FRONTIER_COMPETITIVENESS_ESTABLISHED",
        ),
        (
            primary(confirm=True),
            frontier(competitive=True, dominates=True),
            "GENERIC_BRAKING_DOMINATES",
            "BLIND_FRONTIER_DOMINATES",
        ),
    ],
)
def test_noninfrastructure_verdict_and_mandatory_qualifier(p, f, expected_verdict, expected_qualifier):
    assert a.decide_verdict(True, p, f) == (expected_verdict, expected_qualifier)


def test_any_failed_validity_gate_forces_infra_null_without_frontier_qualifier():
    verdict, qualifier = a.decide_verdict(False, primary(confirm=True), frontier(dominates=True))
    assert verdict == "PLACEBO_DOSE_INFRA_NULL"
    assert qualifier is None


def test_receipt_is_manifest_bound_and_all_resource_falsifiers_fail_closed(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest_value = _manifest()
    manifest.write_text(json.dumps(manifest_value, sort_keys=True) + "\n")
    runtime_facts = _write_runtime_proof(tmp_path, manifest, manifest_value)
    receipt = _validity_receipt(manifest, manifest_value, runtime_facts)
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(receipt))
    gates, problems, _ = a.validate_receipt(receipt_path, manifest)
    assert all(gates.values())
    assert problems == []
    assert "G7" not in gates

    hostile = copy.deepcopy(receipt)
    hostile["remote_projected_reserve_gib"] = 24.999
    hostile["unexpected_falsifiers"] = ["selected-dose inference"]
    receipt_path.write_text(json.dumps(hostile))
    _, problems, _ = a.validate_receipt(receipt_path, manifest)
    assert any("remote_projected_reserve_gib" in problem for problem in problems)
    assert any("unexpected-falsifiers" in problem for problem in problems)

    conflated = copy.deepcopy(receipt)
    conflated["gates"]["G7"] = True
    receipt_path.write_text(json.dumps(conflated))
    _, problems, _ = a.validate_receipt(receipt_path, manifest)
    assert any("receipt:gate-set" in problem and "G7" in problem for problem in problems)


def test_manifest_dataset_missing_environment_mismatch_and_archive_drift_fail_closed():
    legacy = _manifest()
    legacy["environment_receipts"]["schema"] = "iter135.environment_receipts.v2"
    _facts, problems = a.validate_manifest_dataset(legacy)
    assert "manifest:environment-receipts-v3" in problems

    missing = _manifest()
    missing.pop("dataset_receipt")
    _facts, problems = a.validate_manifest_dataset(missing)
    assert "manifest:dataset:missing" in problems
    assert "manifest:dataset-environment-mismatch" in problems

    mismatch = _manifest()
    mismatch["environment_receipts"]["dataset"] = copy.deepcopy(
        mismatch["dataset_receipt"]
    )
    mismatch["environment_receipts"]["dataset"]["identity"][
        "dataset_realpath"
    ] = "/datasets/substituted"
    _facts, problems = a.validate_manifest_dataset(mismatch)
    assert "manifest:dataset-environment-mismatch" in problems

    drifted = _manifest()
    dataset = drifted["dataset_receipt"]
    first_archive = next(iter(a.EXPECTED_DATASET_ARCHIVES))
    dataset["archives"][first_archive]["sha256"] = "0" * 64
    digest_payload = dict(dataset)
    digest_payload.pop("receipt_payload_sha256")
    dataset["receipt_payload_sha256"] = a._canonical_json_sha256(digest_payload)
    drifted["environment_receipts"]["dataset"] = dataset
    _facts, problems = a.validate_manifest_dataset(drifted)
    assert any(
        problem == f"manifest:dataset:archive:{first_archive}:expected-sha256"
        for problem in problems
    )


def test_receipt_rejects_packaged_dataset_snapshot_drift_and_missing_phase(tmp_path):
    drift_root = tmp_path / "drift"
    drift_root.mkdir()
    manifest_value = _manifest()
    manifest_path = drift_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_value, sort_keys=True) + "\n")
    runtime_facts = _write_runtime_proof(drift_root, manifest_path, manifest_value)
    receipt = _validity_receipt(manifest_path, manifest_value, runtime_facts)
    receipt_path = drift_root / "receipt.json"
    receipt_path.write_text(json.dumps(receipt))
    dataset_path = drift_root / "dataset_runtime_snapshot.json"
    dataset_snapshot = json.loads(dataset_path.read_bytes())
    first_file = next(iter(dataset_snapshot["files"]))
    dataset_snapshot["files"][first_file]["path"] = "/datasets/substituted"
    dataset_path.write_bytes(a._canonical_runtime_snapshot(dataset_snapshot))

    _, problems, _ = a.validate_receipt(receipt_path, manifest_path)
    assert any("runtime-evidence:dataset_runtime_snapshot" in problem for problem in problems)
    assert "receipt:dataset-provenance-drift" in problems

    phase_root = tmp_path / "phase"
    phase_root.mkdir()
    phase_manifest = _manifest()
    phase_manifest_path = phase_root / "manifest.json"
    phase_manifest_path.write_text(json.dumps(phase_manifest, sort_keys=True) + "\n")
    phase_facts = _write_runtime_proof(phase_root, phase_manifest_path, phase_manifest)
    phase_receipt = _validity_receipt(phase_manifest_path, phase_manifest, phase_facts)
    phase_receipt_path = phase_root / "receipt.json"
    phase_receipt_path.write_text(json.dumps(phase_receipt))
    log_path = phase_root / "sentinel-i135.log.gz"
    log_payload = gzip.decompress(log_path.read_bytes()).replace(
        b"I135_DATASET_RUNTIME_OK phase=before files=28\n",
        b"",
        1,
    )
    log_path.write_bytes(gzip.compress(log_payload, mtime=0))

    _, problems, _ = a.validate_receipt(phase_receipt_path, phase_manifest_path)
    assert any("runtime-log" in problem and "dataset-check-counts" in problem for problem in problems)


def test_manifest_binds_exact_schedule_and_executing_analyzer_bytes(tmp_path):
    schedule = tmp_path / "dose_schedules.json"
    analyzer_path = tmp_path / "analyze_dose135.py"
    schedule.write_bytes(b"frozen schedule\n")
    analyzer_path.write_bytes(b"frozen analyzer\n")
    manifest = _manifest(
        hash_bound_files={
            "dose_schedules.json": {
                "sha256": a.sha256_file(schedule),
                "bytes": schedule.stat().st_size,
            },
            "analyze_dose135.py": {
                "sha256": a.sha256_file(analyzer_path),
                "bytes": analyzer_path.stat().st_size,
            },
        }
    )
    manifest_path = tmp_path / "launch_manifest.json"
    manifest_path.write_text(json.dumps(manifest))

    _, problems = a.validate_manifest_bindings(
        manifest_path, schedule, analyzer_path=analyzer_path
    )
    assert problems == []

    old_schema = copy.deepcopy(manifest)
    old_schema["schema"] = "iter135.launch_manifest.v1"
    manifest_path.write_text(json.dumps(old_schema))
    _, problems = a.validate_manifest_bindings(
        manifest_path, schedule, analyzer_path=analyzer_path
    )
    assert any("manifest:schema:iter135.launch_manifest.v1" in row for row in problems)
    manifest_path.write_text(json.dumps(manifest))

    schedule.write_bytes(b"post-launch schedule substitution\n")
    analyzer_path.write_bytes(b"post-launch analyzer substitution\n")
    _, problems = a.validate_manifest_bindings(
        manifest_path, schedule, analyzer_path=analyzer_path
    )
    assert any("bound-sha256-mismatch:dose_schedules.json" in row for row in problems)
    assert any("bound-sha256-mismatch:analyze_dose135.py" in row for row in problems)


def _run_git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _committed_proof_fixture(tmp_path: Path):
    repository = tmp_path / "repo"
    repository.mkdir()
    _run_git(repository, "init", "-q")
    _run_git(repository, "config", "user.email", "sentinel@example.invalid")
    _run_git(repository, "config", "user.name", "Sentinel hostile test")
    proof = (
        repository
        / "experiments"
        / "iter135_neuroncap_blind_braking_dose_response"
        / "proof"
    )
    proof.mkdir(parents=True)
    collector = repository / "collect_proof135.py"
    collector.write_bytes(b"frozen collector\n")
    manifest = repository / "launch_manifest.json"
    manifest_value = _manifest(
        hash_bound_files={
            "collect_proof135.py": {
                "sha256": a.sha256_file(collector),
                "bytes": collector.stat().st_size,
            }
        }
    )
    manifest.write_text(json.dumps(manifest_value, sort_keys=True) + "\n")
    runtime_facts = _write_runtime_proof(proof, manifest, manifest_value)
    paths = {
        "i135_log": [proof / "sentinel-i135.log.gz"],
        "i135_runs": [proof / "i135-runs.tar.gz"],
        "validity_receipt": [proof / "launch_validity_receipt.json"],
        **{
            role: [proof / filename]
            for role, filename in a.RUNTIME_EVIDENCE_FILENAMES.items()
        },
    }
    for arm in a.ARMS:
        paths[f"decision_{arm}"] = [proof / f"{arm}.jsonl.gz"]
    for role, members in paths.items():
        for member in members:
            if not member.exists():
                member.write_bytes(f"committed proof for {role}\n".encode())
    raw_receipt = {
        "schema": a.RAW_PROOF_RECEIPT_SCHEMA,
        "verdict": "I135_RAW_PROOF_COMPLETE",
        "launch_manifest_sha256": a.sha256_file(manifest),
        "collector_sha256": a.sha256_file(collector),
        "collection_gate": {
            "minimum_local_free_bytes": a.MINIMUM_LOCAL_COLLECTION_BYTES,
            "observed_local_free_bytes": a.MINIMUM_LOCAL_COLLECTION_BYTES,
            "passed": True,
        },
        "completion": {
            "done_marker": a.DONE_MARKER,
            "done_marker_count": 1,
            "successful_blocks": 120,
            "analytic_cells": 2400,
            "decision_blocks": 120,
            "decision_resets": 2400,
            "run_archive_cells": 2400,
            "run_archive_members": 7200,
        },
        "source_receipts": {
            "launcher_log": {},
            "runtime_evidence": runtime_facts,
            "decision_blocks": {},
            "run_tree": {},
        },
        "artifacts": {
            role: {
                "path": members[0].name,
                "sha256": a.sha256_file(members[0]),
                "bytes": members[0].stat().st_size,
            }
            for role, members in sorted(paths.items())
        },
        "problem_count": 0,
        "problems": [],
    }
    raw_path = proof / "raw_proof_receipt.json"
    raw_path.write_text(json.dumps(raw_receipt, sort_keys=True) + "\n")
    paths["raw_proof_receipt"] = [raw_path]
    checksum_rows = sorted(
        (
            member.name,
            a.sha256_file(member),
        )
        for members in paths.values()
        for member in members
    )
    (proof / "SHA256SUMS.txt").write_text(
        "".join(f"{digest}  {name}\n" for name, digest in checksum_rows)
    )
    _run_git(repository, "add", ".")
    _run_git(repository, "commit", "-qm", "commit raw proof")
    proof_commit = _run_git(repository, "rev-parse", "HEAD")
    inputs = {
        role: [
            {
                "path": member.relative_to(repository).as_posix(),
                "sha256": a.sha256_file(member),
                "bytes": member.stat().st_size,
            }
            for member in members
        ]
        for role, members in paths.items()
    }
    receipt = {
        "schema": a.COMMITTED_PROOF_RECEIPT_SCHEMA,
        "launch_manifest_sha256": a.sha256_file(manifest),
        "repository_root": str(repository),
        "proof_commit": proof_commit,
        "inputs": inputs,
        "problem_count": 0,
        "problems": [],
    }
    receipt_path = repository / "proof_commit_receipt.json"
    receipt_path.write_text(json.dumps(receipt))
    args = SimpleNamespace(
        i135_log=str(paths["i135_log"][0]),
        i135_runs=str(paths["i135_runs"][0]),
        validity_receipt=str(paths["validity_receipt"][0]),
    )
    decision_paths = {
        arm: [str(paths[f"decision_{arm}"][0])] for arm in a.ARMS
    }
    return repository, manifest, receipt_path, receipt, paths, args, decision_paths


def test_proof_receipt_is_mechanically_verified_against_commit_blobs(tmp_path):
    repository, manifest, receipt_path, _receipt, _paths, args, decision_paths = (
        _committed_proof_fixture(tmp_path)
    )

    _, problems = a.validate_committed_proof_receipt(
        receipt_path,
        manifest,
        args,
        decision_paths,
        expected_repository_root=repository,
    )
    assert problems == []


def test_proof_receipt_cannot_bless_uncommitted_bytes_or_unknown_roles(tmp_path):
    repository, manifest, receipt_path, receipt, paths, args, decision_paths = (
        _committed_proof_fixture(tmp_path)
    )
    target = paths["i135_log"][0]
    target.write_bytes(b"fabricated post-commit proof\n")
    receipt["inputs"]["i135_log"][0].update(
        sha256=a.sha256_file(target), bytes=target.stat().st_size
    )
    receipt["inputs"]["arbitrary_unreviewed_input"] = receipt["inputs"]["i135_runs"]
    receipt_path.write_text(json.dumps(receipt))

    _, problems = a.validate_committed_proof_receipt(
        receipt_path,
        manifest,
        args,
        decision_paths,
        expected_repository_root=repository,
    )
    assert any("unknown=['arbitrary_unreviewed_input']" in row for row in problems)
    assert any(
        "commit-blob-mismatch:" in row and row.endswith("proof/sentinel-i135.log.gz")
        for row in problems
    )
    assert any("current-state-differs-from-proof-commit" in row for row in problems)


def test_proof_replay_consumes_and_rejects_substituted_runtime_snapshot(tmp_path):
    repository, manifest, receipt_path, receipt, paths, args, decision_paths = (
        _committed_proof_fixture(tmp_path)
    )
    target = paths["dataset_runtime_snapshot"][0]
    snapshot = json.loads(target.read_bytes())
    first_file = next(iter(snapshot["files"]))
    snapshot["files"][first_file]["path"] = "/datasets/substituted"
    target.write_bytes(a._canonical_runtime_snapshot(snapshot))
    receipt["inputs"]["dataset_runtime_snapshot"][0].update(
        sha256=a.sha256_file(target), bytes=target.stat().st_size
    )
    receipt_path.write_text(json.dumps(receipt))

    _, problems = a.validate_committed_proof_receipt(
        receipt_path,
        manifest,
        args,
        decision_paths,
        expected_repository_root=repository,
    )

    assert any("commit-blob-mismatch" in row for row in problems)
    assert any("runtime" in row and "dataset" in row for row in problems)


def test_proof_verifier_independently_rejects_committed_raw_receipt_disagreement(tmp_path):
    repository, manifest, receipt_path, receipt, paths, args, decision_paths = (
        _committed_proof_fixture(tmp_path)
    )
    raw_path = paths["raw_proof_receipt"][0]
    raw = json.loads(raw_path.read_text())
    raw["artifacts"]["i135_log"]["sha256"] = "0" * 64
    raw_path.write_text(json.dumps(raw, sort_keys=True) + "\n")
    checksum_path = raw_path.parent / "SHA256SUMS.txt"
    checksum_rows = {
        line.split("  ", 1)[1]: line.split("  ", 1)[0]
        for line in checksum_path.read_text().splitlines()
    }
    checksum_rows[raw_path.name] = a.sha256_file(raw_path)
    checksum_path.write_text(
        "".join(f"{digest}  {name}\n" for name, digest in sorted(checksum_rows.items()))
    )
    _run_git(repository, "add", str(raw_path), str(checksum_path))
    _run_git(repository, "commit", "-qm", "commit internally inconsistent raw receipt")
    receipt["proof_commit"] = _run_git(repository, "rev-parse", "HEAD")
    receipt["inputs"]["raw_proof_receipt"][0].update(
        sha256=a.sha256_file(raw_path), bytes=raw_path.stat().st_size
    )
    receipt_path.write_text(json.dumps(receipt))

    _, problems = a.validate_committed_proof_receipt(
        receipt_path,
        manifest,
        args,
        decision_paths,
        expected_repository_root=repository,
    )

    assert any("raw-proof-chain:artifact-mismatch:i135_log" in row for row in problems)


def test_blind_decision_parser_rejects_reachable_scheduled_frame_that_did_not_fire(tmp_path):
    arm = "blind_0_5x"
    cell = (arm, "stationary", "0099", 0)
    rows = [
        {"reset": True, "run": 0, "pair": "stationary/0099", "dose": arm},
        {
            "frame": True,
            "scheduled": True,
            "run": 0,
            "pair": "stationary/0099",
            "dose": arm,
            "frame_index": 0,
        },
    ]
    log = tmp_path / "blind.jsonl"
    log.write_text("".join(json.dumps(row) + "\n" for row in rows))
    parsed = a.parse_blind_decisions(arm, [log], {cell: {"brake_frames": [0]}})
    assert any("missed-reachable-schedule" in problem for problem in parsed.problems)
    assert any("missing-cells" in problem for problem in parsed.problems)


def test_semantic_decisions_bind_cells_from_content_not_cli_path_order(tmp_path):
    frontal = tmp_path / "second.jsonl"
    stationary = tmp_path / "first.jsonl"
    frontal.write_text(
        json.dumps(
            {
                "block_identity": True,
                "arm": "off_baseline",
                "class": "frontal",
                "pair": "0103",
            }
        )
        + "\n"
        + json.dumps({"reset": True, "run": 0})
        + "\n"
        + json.dumps({"ts": 1, "traj": [[0.0, 0.0]]})
        + "\n"
    )
    stationary.write_text(
        json.dumps(
            {
                "block_identity": True,
                "arm": "off_baseline",
                "class": "stationary",
                "pair": "0099",
            }
        )
        + "\n"
        + json.dumps({"reset": True, "run": 0})
        + "\n"
        + json.dumps({"ts": 2, "traj": [[0.0, 0.0]]})
        + "\n"
    )

    parsed = a.parse_semantic_decisions("off_baseline", [frontal, stationary])

    assert ("off_baseline", "frontal", "0103", 0) in parsed.cells
    assert ("off_baseline", "stationary", "0099", 0) in parsed.cells
    assert not any("block-identity" in problem for problem in parsed.problems)


def test_semantic_decisions_reject_reset_without_block_identity(tmp_path):
    log = tmp_path / "unbound.jsonl"
    log.write_text(json.dumps({"reset": True, "run": 0}) + "\n")

    parsed = a.parse_semantic_decisions("released_union_semantic_reference", [log])

    assert parsed.cells == {}
    assert any("reset-without-block-identity" in problem for problem in parsed.problems)


def test_frozen_oracle_substitution_is_rejected_before_outcome_parsing(tmp_path):
    oracle_log = tmp_path / "oracle.log.gz"
    oracle_runs = tmp_path / "oracle-runs.tar.gz"
    part_a = tmp_path / "part-aa"
    part_b = tmp_path / "part-ab"
    for path in (oracle_log, oracle_runs, part_a, part_b):
        path.write_bytes(b"substituted")
    args = SimpleNamespace(
        oracle_log=str(oracle_log),
        oracle_runs=str(oracle_runs),
        oracle_union_log=[str(part_a), str(part_b)],
    )

    with pytest.raises(a.AnalysisInputError, match="frozen-oracle-provenance"):
        a.verify_frozen_oracle_inputs(args)


def _raw_cli_arguments(output: Path) -> list[str]:
    return [
        "--i135-log",
        "missing-i135-log",
        "--i135-runs",
        "missing-i135-runs",
        "--schedule",
        "missing-schedule",
        "--launch-manifest",
        "missing-manifest",
        "--validity-receipt",
        "missing-validity-receipt",
        "--proof-commit-receipt",
        "missing-proof-commit-receipt",
        "--oracle-log",
        "missing-oracle-log",
        "--oracle-runs",
        "missing-oracle-runs",
        "--oracle-union-log",
        "missing-oracle-part",
        "--out",
        str(output),
    ]


def test_incomplete_raw_proof_accumulates_diagnostics_before_any_inference(tmp_path, monkeypatch):
    def forbidden_inference(_episodes):
        raise AssertionError("inference/indexing must not run for incomplete proof")

    monkeypatch.setattr(a, "make_metric_tables", forbidden_inference)
    args = a.parser().parse_args(_raw_cli_arguments(tmp_path / "unused.json"))

    report = a.build_report(args)

    assert report["verdict"] == "PLACEBO_DOSE_INFRA_NULL"
    assert report["analysis_status"] == "INFERENCE_NOT_RUN"
    assert report["primary"] is None
    assert report["problem_count"] == len(report["problems"])
    assert report["problem_count"] > 5
    assert any(row.startswith("manifest:unreadable:") for row in report["problems"])
    assert any(row.startswith("schedule:unreadable:") for row in report["problems"])
    assert any(row.startswith("proof-receipt:unreadable:") for row in report["problems"])
    assert any(row.startswith("runs:unreadable:") for row in report["problems"])


def test_main_writes_infra_null_and_returns_nonzero(tmp_path, monkeypatch):
    report = a.infra_null_report(problems=["hostile:incomplete-proof"])
    monkeypatch.setattr(a, "build_report", lambda _args: report)
    output = tmp_path / "report.json"

    return_code = a.main(_raw_cli_arguments(output))

    assert return_code == 2
    assert json.loads(output.read_text())["problems"] == ["hostile:incomplete-proof"]


def test_main_revalidates_all_mutable_inputs_before_atomic_publish(tmp_path, monkeypatch):
    mutable_input = tmp_path / "proof-input"
    mutable_input.write_bytes(b"verified bytes\n")
    for filename in a.RUNTIME_EVIDENCE_FILENAMES.values():
        (tmp_path / filename).write_bytes(b"verified runtime evidence\n")
    output = tmp_path / "report.json"
    arguments = _raw_cli_arguments(output)
    arguments = [
        str(mutable_input) if value.startswith("missing-") else value
        for value in arguments
    ]
    for arm in a.ARMS:
        arguments.extend(["--decision-log", f"{arm}={mutable_input}"])
    captured_roles = set(a.capture_analysis_input_state(a.parser().parse_args(arguments)))
    assert {
        "i135_log",
        "i135_runs",
        "schedule",
        "launch_manifest",
        "analytic_lock",
        "dataset_runtime_snapshot",
        "docker_runtime_snapshot",
        *(f"decision_{index}" for index in range(len(a.ARMS))),
    } <= captured_roles
    would_be_valid = {
        "schema": "iter135.neuroncap_blind_braking_dose_response_report.v1",
        "headline": "HOSTILE_VALID_RESULT",
        "verdict": "SEMANTIC_MATCHED_BUDGET_CONFIRMED",
        "infrastructure_valid": True,
        "problem_count": 0,
        "problems": [],
        "validity_gates": {
            f"G{index}": {"pass": True} for index in range(10)
        },
    }

    def mutate_after_verification(_args):
        mutable_input.write_bytes(b"post-verification substituted bytes\n")
        (tmp_path / "dataset_runtime_snapshot.json").write_bytes(
            b"post-verification substituted runtime snapshot\n"
        )
        return would_be_valid

    monkeypatch.setattr(a, "build_report", mutate_after_verification)

    return_code = a.main(arguments)
    published = json.loads(output.read_text())

    assert return_code == 2
    assert published["verdict"] == "PLACEBO_DOSE_INFRA_NULL"
    assert published["analysis_status"] == "INFERENCE_NOT_RUN"
    assert any(
        "input-toctou:post-verification-mutation" in row
        and "dataset_runtime_snapshot" in row
        for row in published["problems"]
    )
    assert not list(tmp_path.glob(".report.json.*"))


def test_main_prints_structured_report_if_output_write_fails(tmp_path, monkeypatch, capsys):
    report = a.infra_null_report(problems=["hostile:write-target"])
    monkeypatch.setattr(a, "build_report", lambda _args: report)

    return_code = a.main(_raw_cli_arguments(tmp_path))

    assert return_code == 3
    fallback = json.loads(capsys.readouterr().err)
    assert fallback["schema"] == "iter135.analyzer_output_failure.v1"
    assert fallback["stage"] == "write-report"
    assert fallback["report"]["problems"] == ["hostile:write-target"]


# The normalized collector boundary is tested independently from the raw parser above. The
# analyzer must reconstruct Q16 and every aggregate from these raw episode rows; no precomputed
# outcome is allowed across this boundary.


def _matrix(x: float, y: float = 0.0) -> list[list[float]]:
    return [
        [1.0, 0.0, 0.0, x],
        [0.0, 1.0, 0.0, y],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def _poses(step: float = 1.0, samples: int = 18) -> dict[str, list[list[float]]]:
    return {f"{index:03d}": _matrix(index * step) for index in range(samples)}


def _allocation(budget: int, schedules: int) -> list[int]:
    base, remainder = divmod(budget, schedules)
    return [base + (index < remainder) for index in range(schedules)]


def _complete_evidence() -> dict:
    gates = {
        gate_id: {"passed": True, "detail": "hash-bound receipt verified"}
        for gate_id in analyzer.GATE_IDS
    }
    episodes = []
    union_global_index = 0
    for scenario_class in analyzer.CLASSES:
        schedules = len(analyzer.PAIRS_BY_CLASS[scenario_class]) * len(analyzer.RUNS)
        blind_counts = {
            arm: _allocation(analyzer.SCHEDULED_BUDGETS[arm][scenario_class], schedules)
            for arm in analyzer.BLIND_ARMS
        }
        local_index = 0
        for pair in analyzer.PAIRS_BY_CLASS[scenario_class]:
            for run in analyzer.RUNS:
                for arm in analyzer.ARMS:
                    scheduled: list[int] = []
                    realized: list[int] = []
                    releases: list[int] = []
                    if arm in analyzer.BLIND_ARMS:
                        scheduled = list(range(blind_counts[arm][local_index]))
                        realized = scheduled.copy()
                    elif arm == analyzer.UNION_ARM:
                        realized = list(range(blind_counts["blind_1_0x"][local_index]))
                        releases = [20] if union_global_index < 156 else []
                    episodes.append(
                        {
                            "arm": arm,
                            "scenario_class": scenario_class,
                            "pair": pair,
                            "run": run,
                            "ncap_score": 4.0 if arm == analyzer.UNION_ARM else 3.5,
                            "impact_speed": 0.0,
                            "ego_poses": _poses(),
                            "collision": False,
                            "terminal_reason": "benchmark_complete",
                            "episode_frame_count": 100,
                            "scheduled_brake_frames": scheduled,
                            "realized_brake_frames": realized,
                            "realized_release_frames": releases,
                        }
                    )
                local_index += 1
                union_global_index += 1
    return {
        "schema": analyzer.EVIDENCE_SCHEMA,
        "episodes": episodes,
        "validity_gates": gates,
        "falsifiers": [],
    }


def _primary_stats(
    *,
    delta_ncap: float = 0.0,
    lcb_ncap: float = -0.2,
    ucb_ncap: float = 0.5,
    delta_q16: float = 0.0,
    lcb_q16: float = -0.1,
    ucb_q16: float = 0.2,
) -> analyzer.PrimaryInference:
    return analyzer.PrimaryInference(
        delta_ncap=delta_ncap,
        lcb_ncap=lcb_ncap,
        ucb_ncap=ucb_ncap,
        ci_ncap=(lcb_ncap, ucb_ncap),
        delta_q16=delta_q16,
        lcb_q16=lcb_q16,
        ucb_q16=ucb_q16,
        ci_q16=(lcb_q16, ucb_q16),
    )


def _frontier_stats(
    arm: str,
    *,
    delta_ncap: float = 0.5,
    ncap_interval: tuple[float, float] = (-0.5, 0.5),
    delta_q16: float = 0.2,
    q16_interval: tuple[float, float] = (-0.2, 0.2),
) -> analyzer.FrontierInference:
    return analyzer.FrontierInference(
        arm=arm,
        delta_ncap=delta_ncap,
        interval_ncap=ncap_interval,
        delta_q16=delta_q16,
        interval_q16=q16_interval,
    )


def _neutral_frontier() -> list[analyzer.FrontierInference]:
    return [_frontier_stats(arm) for arm in analyzer.BLIND_ARMS]


def test_normalized_q16_sorts_limits_and_absorbs_short_episodes():
    scrambled = {f"{index:03d}": _matrix(float(index)) for index in reversed(range(20))}
    points = analyzer.pose_points(scrambled)
    assert analyzer.q16_distance(points) == 15.0
    assert analyzer.path_distance(points) == 19.0
    assert analyzer.q16_distance(points[:3]) == 2.0


def test_normalized_q16_is_euclidean_not_axis_or_pose_count():
    assert analyzer.q16_distance(((0.0, 0.0), (3.0, 4.0), (6.0, 8.0))) == 10.0


def test_normalized_parser_rejects_unknown_precomputed_outcome_and_missing_raw_field():
    row = _complete_evidence()["episodes"][0]
    document = _complete_evidence()
    document["episodes"] = [dict(row, q16=0.99)]
    with pytest.raises(analyzer.EvidenceError, match=r"unknown=\['q16'\]"):
        analyzer.parse_evidence(document)
    missing_poses = dict(row)
    missing_poses.pop("ego_poses")
    document["episodes"] = [missing_poses]
    with pytest.raises(analyzer.EvidenceError, match="ego_poses"):
        analyzer.parse_evidence(document)


def test_normalized_parser_rejects_nonfinite_and_bad_frame_lists():
    document = _complete_evidence()
    document["episodes"][0]["ncap_score"] = math.nan
    with pytest.raises(analyzer.EvidenceError, match="finite"):
        analyzer.parse_evidence(document)
    document = _complete_evidence()
    document["episodes"][0]["scheduled_brake_frames"] = [2, 1, 1]
    with pytest.raises(analyzer.EvidenceError, match="sorted and unique"):
        analyzer.parse_evidence(document)


def test_normalized_parser_requires_exact_gate_set_and_boolean_receipts():
    document = _complete_evidence()
    document["validity_gates"].pop("G9")
    with pytest.raises(analyzer.EvidenceError, match="exactly G0..G9"):
        analyzer.parse_evidence(document)
    document = _complete_evidence()
    document["validity_gates"]["G4"]["passed"] = 1
    with pytest.raises(analyzer.EvidenceError, match="must be boolean"):
        analyzer.parse_evidence(document)


def test_normalized_missing_cell_is_infra_null_without_inference():
    document = _complete_evidence()
    document["episodes"].pop()
    report = analyzer.analyze_evidence(document)
    assert report["verdict"] == "PLACEBO_DOSE_INFRA_NULL"
    assert report["qualifier"] is None
    assert report["primary"] is None
    assert "G7:missing-analytic-cells:1" in report["problems"]


def test_normalized_duplicate_cell_is_infra_null():
    document = _complete_evidence()
    document["episodes"][-1] = copy.deepcopy(document["episodes"][0])
    report = analyzer.analyze_evidence(document)
    assert report["verdict"] == "PLACEBO_DOSE_INFRA_NULL"
    assert any(problem.startswith("G7:duplicate-analytic-cells:") for problem in report["problems"])


def test_normalized_complete_grid_passes_mechanical_integrity():
    evidence = analyzer.parse_evidence(_complete_evidence())
    assert len(evidence.episodes) == 2400
    assert analyzer.evidence_integrity_problems(evidence) == []


def test_normalized_class_bootstrap_equal_weights_and_pairing():
    pair_values = {}
    class_differences = {"stationary": 3.0, "frontal": 6.0, "side": 9.0}
    for scenario_class in analyzer.CLASSES:
        for pair_index, pair in enumerate(analyzer.PAIRS_BY_CLASS[scenario_class]):
            shared_noise = pair_index * 100.0
            for arm in analyzer.ARMS:
                pair_values[(arm, scenario_class, pair)] = {"ncap": shared_noise, "q16": shared_noise}
            for arm in analyzer.BLIND_ARMS:
                pair_values[(arm, scenario_class, pair)]["ncap"] -= class_differences[scenario_class]
                pair_values[(arm, scenario_class, pair)]["q16"] -= class_differences[scenario_class]
    points, draws = analyzer.class_stratified_contrast_draws(pair_values, draw_count=25, seed=135)
    for key in analyzer.contrast_keys():
        assert points[key] == pytest.approx(6.0)
        assert draws[key] == pytest.approx([6.0] * 25)


def test_normalized_exact_order_statistic_indices():
    interval = analyzer.canonical_interval(list(reversed(range(analyzer.BOOTSTRAP_DRAWS))))
    assert interval == {
        "one_sided_lcb": 4_999,
        "one_sided_ucb": 94_999,
        "two_sided_95": [2_499, 97_499],
    }


def test_normalized_order_statistics_reject_noncanonical_count():
    with pytest.raises(ValueError, match="exactly 100000"):
        analyzer.canonical_interval([0.0] * 99_999)


def test_normalized_max_t_all_zero_se_is_exact_and_omitted():
    points = {key: float(index) for index, key in enumerate(analyzer.contrast_keys())}
    draws = {key: [points[key]] * analyzer.BOOTSTRAP_DRAWS for key in analyzer.contrast_keys()}
    critical, intervals = analyzer.simultaneous_max_t_intervals(points, draws)
    assert critical == 0.0
    for key, point in points.items():
        assert intervals[key] == {"se": 0.0, "lower": point, "upper": point}


def test_normalized_max_t_mixed_zero_se_keeps_zero_exact():
    keys = analyzer.contrast_keys()
    points = {key: 0.0 for key in keys}
    draws = {key: [0.0] * analyzer.BOOTSTRAP_DRAWS for key in keys}
    draws[keys[0]] = [-1.0, 1.0] * (analyzer.BOOTSTRAP_DRAWS // 2)
    critical, intervals = analyzer.simultaneous_max_t_intervals(points, draws)
    assert critical > 0.0
    assert intervals[keys[1]] == {"se": 0.0, "lower": 0.0, "upper": 0.0}


def test_normalized_infrastructure_null_has_absolute_precedence():
    semantic = _primary_stats(delta_ncap=0.25, lcb_ncap=0.01, lcb_q16=-0.049)
    assert analyzer.select_verdict(False, semantic, _neutral_frontier()) == (
        "PLACEBO_DOSE_INFRA_NULL",
        None,
    )


def test_normalized_semantic_boundaries_are_inclusive_point_strict_bounds():
    semantic = _primary_stats(delta_ncap=0.25, lcb_ncap=1e-12, lcb_q16=-0.05 + 1e-12)
    assert analyzer.select_verdict(True, semantic, _neutral_frontier())[0] == (
        "SEMANTIC_MATCHED_BUDGET_CONFIRMED"
    )
    assert analyzer.select_verdict(
        True, _primary_stats(delta_ncap=0.25, lcb_ncap=0.0, lcb_q16=0.0), _neutral_frontier()
    )[0] == "MATCHED_BUDGET_INCONCLUSIVE"
    assert analyzer.select_verdict(
        True, _primary_stats(delta_ncap=0.25, lcb_ncap=0.1, lcb_q16=-0.05), _neutral_frontier()
    )[0] == "MATCHED_BUDGET_INCONCLUSIVE"


def test_normalized_reverse_dominance_boundaries():
    dominance = _primary_stats(delta_ncap=-0.25, ucb_ncap=-1e-12, ucb_q16=0.0)
    assert analyzer.select_verdict(True, dominance, _neutral_frontier())[0] == "GENERIC_BRAKING_DOMINATES"
    zero_upper = _primary_stats(delta_ncap=-0.25, ucb_ncap=0.0, ucb_q16=0.0)
    assert analyzer.select_verdict(True, zero_upper, _neutral_frontier())[0] == (
        "BLIND_MATCHED_BUDGET_COMPETITIVE"
    )


def test_normalized_secondary_dominance_precedes_semantic():
    semantic = _primary_stats(delta_ncap=0.4, lcb_ncap=0.1, lcb_q16=0.0)
    rows = _neutral_frontier()
    rows[0] = _frontier_stats(
        analyzer.BLIND_ARMS[0],
        delta_ncap=-0.25,
        ncap_interval=(-0.5, -0.01),
        delta_q16=0.0,
        q16_interval=(-0.1, 0.01),
    )
    assert analyzer.select_verdict(True, semantic, rows) == (
        "GENERIC_BRAKING_DOMINATES",
        "BLIND_FRONTIER_DOMINATES",
    )


def test_normalized_primary_competitiveness_bounds_are_strict():
    below = _primary_stats(ucb_ncap=0.25 - 1e-12, ucb_q16=0.05 - 1e-12)
    assert analyzer.select_verdict(True, below, _neutral_frontier())[0] == (
        "BLIND_MATCHED_BUDGET_COMPETITIVE"
    )
    assert analyzer.select_verdict(
        True, _primary_stats(ucb_ncap=0.25, ucb_q16=0.0), _neutral_frontier()
    )[0] == "MATCHED_BUDGET_INCONCLUSIVE"
    assert analyzer.select_verdict(
        True, _primary_stats(ucb_ncap=0.0, ucb_q16=0.05), _neutral_frontier()
    )[0] == "MATCHED_BUDGET_INCONCLUSIVE"


def test_normalized_qualifier_order():
    rows = _neutral_frontier()
    rows[1] = _frontier_stats(
        analyzer.BLIND_ARMS[1],
        delta_ncap=0.1,
        ncap_interval=(-0.1, 0.249),
        delta_q16=0.0,
        q16_interval=(-0.1, 0.049),
    )
    assert analyzer.select_verdict(True, _primary_stats(), rows)[1] == "BLIND_FRONTIER_COMPETITIVE"
    rows[2] = _frontier_stats(
        analyzer.BLIND_ARMS[2],
        delta_q16=-0.05,
        ncap_interval=(-0.1, 0.1),
        q16_interval=(-0.2, -0.001),
    )
    assert analyzer.select_verdict(True, _primary_stats(), rows)[1] == "BLIND_FRONTIER_DOMINATES"


def test_normalized_full_report_reconstructs_endpoints_and_headline(monkeypatch):
    monkeypatch.setattr(analyzer, "BOOTSTRAP_DRAWS", 20)
    monkeypatch.setattr(analyzer, "ONE_SIDED_LOWER_INDEX", 0)
    monkeypatch.setattr(analyzer, "ONE_SIDED_UPPER_INDEX", 18)
    monkeypatch.setattr(analyzer, "TWO_SIDED_LOWER_INDEX", 0)
    monkeypatch.setattr(analyzer, "TWO_SIDED_UPPER_INDEX", 19)
    monkeypatch.setattr(analyzer, "MAX_T_CRITICAL_INDEX", 18)
    report = analyzer.analyze_evidence(_complete_evidence())
    assert report["verdict"] == "SEMANTIC_MATCHED_BUDGET_CONFIRMED"
    assert report["qualifier"] == "NO_BLIND_FRONTIER_COMPETITIVENESS_ESTABLISHED"
    assert report["verdict"] in report["headline"] and report["qualifier"] in report["headline"]
    assert report["primary"]["delta_ncap"] == pytest.approx(0.5)
    assert report["primary"]["delta_q16"] == pytest.approx(0.0)
    assert report["arms"][analyzer.UNION_ARM]["aggregate"]["q16_raw"] == pytest.approx(15.0)
    assert report["arms"][analyzer.UNION_ARM]["aggregate"]["raw_path"] == pytest.approx(17.0)
    assert len(report["episode_disclosures"]) == 2400
