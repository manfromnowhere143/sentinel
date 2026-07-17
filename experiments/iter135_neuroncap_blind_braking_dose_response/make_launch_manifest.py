#!/usr/bin/env python3
"""Build the fail-closed Iteration-135 launch manifest.

The manifest is a deterministic projection of committed local artifacts and explicit evidence
receipts.  It never probes or guesses remote state.  Missing tooling, environment evidence, smoke
evidence, Git provenance, or launch authorization remains visible as an incomplete preflight.

The amended execution contract is pair-major: twenty canonical pairs, six cyclically rotated arm
blocks per pair, and twenty run indices inside each block.  The manifest materializes both the 120
compose blocks and the 2,400 analytic cells.

Usage:
    make_launch_manifest.py [OUTPUT.json]

Without OUTPUT the JSON is written to stdout.  The command exits zero only when launch is actually
authorized; an incomplete but well-formed preflight exits two.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import types
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "iter135.launch_manifest.v2"
READY_VERDICT = "I135_TOOLING_MANIFEST_OK"
INCOMPLETE_VERDICT = "I135_TOOLING_MANIFEST_INCOMPLETE"

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
MISSION_STATE_PATH = REPO_ROOT / "MISSION_STATE.json"

HYPOTHESIS_REL = "experiments/iter135_neuroncap_blind_braking_dose_response/HYPOTHESIS.md"
EXPERIMENT_REL = "experiments/iter135_neuroncap_blind_braking_dose_response"
ACTIVE_HYPOTHESIS = HYPOTHESIS_REL
EXPECTED_CANONICAL_REPOSITORY = "/Users/danielwahnich/workspace/sentinel"
EXPECTED_MISSION_SCHEMA = "sentinel.mission_state.v1"
EXPECTED_WORKSPACE_BOUNDARY = {
    "isolated_from": "/Users/danielwahnich/workspace/aweb",
    "recovery_sources": ["MISSION_STATE.json", "CONTINUITY.md", "HANDOFF.md"],
    "cross_workspace_access_requires_explicit_operator_request": True,
}
EXPECTED_MISSION_STATE_FIELDS = {
    "schema",
    "canonical_repository",
    "workspace_boundary",
    "trunk",
    "current_completed_iteration",
    "current_result",
    "current_verdict",
    "run_state",
    "active_hypothesis",
    "next_program",
    "claim_state",
    "deprecated_pending_hypotheses",
    "paper_state",
    "storage_gate",
}
EXPECTED_MISSION_CLAIM_STATE = {
    "neuroncap_union_gain": "ESTABLISHED_ON_NEURONCAP",
    "semantic_attribution": "UNRESOLVED",
    "hugsim_transfer": "TRANSFER_NULL",
    "production_readiness": "NOT_ESTABLISHED",
}
EXPECTED_DEPRECATED_HYPOTHESES = [
    "experiments/iter38_track_query_opposite_direction/HYPOTHESIS.md"
]
EXPECTED_PAPER_STATE = {
    "status": "ARCHIVED_NOT_SUBMISSION_READY",
    "next_route": "peer-reviewed venue after a full evidence rewrite",
    "blocking_omissions": [
        "HUGSIM transfer null",
        "iteration-134 placebo result",
        "resolved wording for the decoder universal-negative overclaim",
    ],
}
EXPECTED_MISSION_PHASE = "LAUNCH_AUTHORIZED"
PREFLIGHT_MISSION_PHASE = "TOOLING_FROZEN_PREFLIGHT_REQUIRED"
ALLOWED_MISSION_PHASES = {PREFLIGHT_MISSION_PHASE, EXPECTED_MISSION_PHASE}
EXPECTED_PROGRAM_NAME = "semantics-free placebo dose-response causal closure"
PREFLIGHT_AUTHORIZED_ACTIONS = (
    "prepare the exact hash-bound sentinel-gpu host contract and atomically commit "
    "host_packet_manifest.json and host_preparation_receipt.json",
    "capture and commit the read-only iteration-135 environment receipt on sentinel-gpu",
    "generate and commit only the hash-addressed incomplete pre-smoke manifest; no analytic "
    "episodes",
    "run exactly the hash-bound four-run nonanalytic G5 smoke after the incomplete pre-smoke "
    "manifest is committed",
    "validate, collect, and commit the exact nonanalytic smoke raw evidence, recomputed receipt, "
    "and mechanically generated SMOKE.md",
)
PREFLIGHT_FORBIDDEN_ACTIONS = (
    "run any iteration-135 analytic episode before smoke evidence and the final launch manifest "
    "are committed green",
    "remove or bypass the permanent analytic launch lock",
    "rerun iteration 134 or adapt iteration-135 schedules, estimands, verdicts, or policies after "
    "evidence",
    "place any iteration-135 analytic output on the remote root filesystem",
)
LAUNCH_AUTHORIZED_ACTIONS = (
    "launch the exact hash-bound iteration-135 analytic manifest once on sentinel-gpu",
    "collect and commit raw proof after the single launch terminates, whether done or aborted",
    "publish partial evidence and PLACEBO_DOSE_INFRA_NULL after any aborted analytic launch",
)
LAUNCH_FORBIDDEN_ACTIONS = (
    "relaunch or retry any iteration-135 analytic block after the first analytic block starts",
    "run with any manifest, payload, environment, smoke, repository, image, GPU, storage, or "
    "idle-state drift",
    "run the analyzer before raw proof is committed",
)
EXPECTED_PHASE_ACTIONS = {
    PREFLIGHT_MISSION_PHASE: (PREFLIGHT_AUTHORIZED_ACTIONS, PREFLIGHT_FORBIDDEN_ACTIONS),
    EXPECTED_MISSION_PHASE: (LAUNCH_AUTHORIZED_ACTIONS, LAUNCH_FORBIDDEN_ACTIONS),
}
EXPECTED_OUTPUT_ROOT = "/datasets/nuscenes-full/sentinel-i135-outoutput"
EXPECTED_HOST = "sentinel-gpu"
EXPECTED_GPU_IDENTITY = {
    "model": "NVIDIA L4",
    "count": 1,
    "uuid": "GPU-9604ae8a-e823-3a38-5a57-0420cd29bc07",
    "driver_version": "580.159.03",
    "memory_total_mib": 23_034,
}
MINIMUM_REMOTE_FREE_BYTES = 100 * 1024**3
MINIMUM_RESERVE_BYTES = 25 * 1024**3
MINIMUM_LOCAL_FREE_BYTES = 15 * 1024**3
PROJECTED_OUTPUT_BYTES = 72_380_432_384

CLASSES = ("stationary", "frontal", "side")
CLASS_PAIRS = {
    "stationary": ("0099", "0101", "0103", "0106", "0108", "0278", "0331", "0783", "0796", "0966"),
    "frontal": ("0103", "0106", "0110", "0346", "0923"),
    "side": ("0103", "0108", "0110", "0278", "0921"),
}
ARMS = (
    "off_baseline",
    "released_union_semantic_reference",
    "blind_0_5x",
    "blind_1_0x",
    "blind_1_5x",
    "blind_2_0x",
)
BLIND_ARMS = ARMS[2:]
RUN_INDICES = tuple(range(20))
PLANNED_BLOCKS = 120
PLANNED_EPISODES = 2_400

ARM_CONFIG = {
    "off_baseline": {
        "patch": "server_patch_union_release.py",
        "sentinel_enabled": "0",
        "dose_id": None,
    },
    "released_union_semantic_reference": {
        "patch": "server_patch_union_release.py",
        "sentinel_enabled": "1",
        "dose_id": None,
    },
    "blind_0_5x": {
        "patch": "server_patch_blind_dose.py",
        "sentinel_enabled": "1",
        "dose_id": "blind_0_5x",
    },
    "blind_1_0x": {
        "patch": "server_patch_blind_dose.py",
        "sentinel_enabled": "1",
        "dose_id": "blind_1_0x",
    },
    "blind_1_5x": {
        "patch": "server_patch_blind_dose.py",
        "sentinel_enabled": "1",
        "dose_id": "blind_1_5x",
    },
    "blind_2_0x": {
        "patch": "server_patch_blind_dose.py",
        "sentinel_enabled": "1",
        "dose_id": "blind_2_0x",
    },
}

FROZEN_UNION_PARAMETERS = {
    "SENTINEL_MIN_SCORE": "0.3",
    "SENTINEL_MAXGAP": "30",
    "SENTINEL_CPA_MARGIN": "1.5",
    "SENTINEL_TTC": "2.5",
    "SENTINEL_MIN_CLOSING": "3",
    "SENTINEL_RELEASE_K": "4",
}

EXPECTED_UNION_SHA256 = "d0338d5cee088d2271ee886b86ccac6f03775bf94991b4128013015159b91189"
EXPECTED_CHECKPOINT_SHA256 = "0ad0c2f5dc9788a41c313305779ea49346aeb742d1f6bb5ad25c46f9beffc990"
EXPECTED_CHECKPOINT_BYTES = 996_345_538
EXPECTED_SHIM_SHA256 = "905dcbc652eb526b0cd7fd2a51534cfcdefdd293ca8417b37091c825e61aa3b8"
EXPECTED_COMPOSE_INPUT_SHA256 = "9f8804b523faa8ec3b6770a69b4b4bc9595c2b36e4b98422a588b9a3e1fe8e5d"
EXPECTED_COMPOSE_OUTPUT_SHA256 = "a5ed766b8a4c7efd7b33cdb6a9bdf9a5878f63604695758ff5f2268b770cfada"
EXPECTED_IMAGE_IDS = {
    "ncap:latest": "sha256:c7ffab2e73d3896b1a6cdfbcd2db0910c250a9cbf078cc61a4b43baa6f6d92ce",
    "neurad:latest": "sha256:4b36caf2054d37b4febeddeae08b310f906ec632fec4095b5dc4497323433e5c",
    "uniad:latest": "sha256:f73ef38840631211983ea0dde0cf1ecdfa6dbc84ef6cd0bfb900427da6d601cb",
}

EXPECTED_REPOSITORIES = {
    "uniad": {
        "path": "/opt/sentinel-stack/UniAD",
        "head": "4827b8be0823e90862caa75d9d146b2ae800b72f",
        "staged_paths": [],
        "dirty_tracked_paths": [
            "projects/mmdet3d_plugin/uniad/detectors/uniad_track.py",
        ],
        "required_untracked_paths": [],
    },
    "neuroncap": {
        "path": "/opt/sentinel-stack/NeuroNCAP",
        "head": "ecdcf284e2b7b83c537f3292a06c0adddff55811",
        "staged_paths": [],
        "dirty_tracked_paths": [
            "docker/Dockerfile",
            "scripts/_docker_compose_release.sh",
        ],
        "required_untracked_paths": [],
    },
    "neurad": {
        "path": "/opt/sentinel-stack/neurad-studio",
        "head": "b25f717b23d85c865d469bf52a0bd03b244014be",
        "staged_paths": [],
        "dirty_tracked_paths": ["Dockerfile"],
        "required_untracked_paths": ["Dockerfile.bak"],
    },
}

EXPECTED_STORAGE_IDENTITY = {
    "filesystem_path": EXPECTED_OUTPUT_ROOT,
    "filesystem_realpath": EXPECTED_OUTPUT_ROOT,
    "filesystem_is_symlink": False,
    "filesystem_empty": True,
    "mount_target": "/datasets/nuscenes-full",
    "mount_source": "/dev/nvme0n2",
    "mount_fstype": "ext4",
    "mount_uuid": "9a98277e-b21f-4ffc-8f14-3f2235b43103",
}

EXPECTED_DATASET_SCHEMA = "iter135.nuscenes_dataset_receipt.v1"
EXPECTED_DATASET_ROOT = "/datasets/nuscenes-full"
EXPECTED_DATASET_VERSION = "v1.0-trainval"
EXPECTED_DATASET_ARCHIVE_ROOT = f"{EXPECTED_DATASET_ROOT}/archives"
EXPECTED_DATASET_METADATA_ROOT = f"{EXPECTED_DATASET_ROOT}/{EXPECTED_DATASET_VERSION}"
EXPECTED_DATASET_MAP_ROOT = f"{EXPECTED_DATASET_ROOT}/maps"
EXPECTED_DATASET_MOUNT = {
    "mount_target": EXPECTED_DATASET_ROOT,
    "mount_source": "/dev/nvme0n2",
    "mount_fstype": "ext4",
    "mount_uuid": "9a98277e-b21f-4ffc-8f14-3f2235b43103",
}

# These are the 11 official archive byte proofs committed by Iteration 28.  They are deliberately
# duplicated here, rather than loaded from an environment receipt, so the launch-manifest
# generator cannot bless a self-declared archive set, digest, path, or byte length.
EXPECTED_DATASET_ARCHIVES: dict[str, tuple[str, int]] = {
    "v1.0-trainval_meta.tgz": (
        "db48746b10e3544d5ef619eaa3d687e3960626fe1b4422ed856711da5aa7325b",
        461_678_030,
    ),
    "v1.0-trainval01_blobs.tgz": (
        "fee4316c55f0780532819ea1b01f347b2ad964303c93477cc815f8191b126171",
        31_579_122_687,
    ),
    "v1.0-trainval02_blobs.tgz": (
        "292301394af9d4a8eb62cee41b3b3031c6cad78e2b39bf63a91bd6d3b7592373",
        30_134_721_083,
    ),
    "v1.0-trainval03_blobs.tgz": (
        "9e6e7c949fbea971321112757dfcff757add646078393c191981a0a49d5f483c",
        29_872_679_856,
    ),
    "v1.0-trainval04_blobs.tgz": (
        "6927f765f8555ce6f901ed2763569bd860b33ad5e076709bbc6c4cc8a51ffc76",
        32_075_538_096,
    ),
    "v1.0-trainval05_blobs.tgz": (
        "ea8d886bc79be30d02e9552d229aaa0843ecffccaaff6606644540b4183f605f",
        28_191_611_840,
    ),
    "v1.0-trainval06_blobs.tgz": (
        "26e3dfff85d8ef6354d4b9dc0a9d8b3f0ebd8719b6d84eac5841fa31b97b8deb",
        27_516_468_993,
    ),
    "v1.0-trainval07_blobs.tgz": (
        "70287e2d65386bce2d67001ef56f5c0abdd3dd95d1ec404c3e00a39208fa60b7",
        29_534_216_608,
    ),
    "v1.0-trainval08_blobs.tgz": (
        "744080381fcfbca3e3ee8d20c5340dce4b5b7fae8020a7e90338ec98b20802c1",
        30_275_496_199,
    ),
    "v1.0-trainval09_blobs.tgz": (
        "ca3aba09dc63cd22fdc455959f3aea99e0f6ed4de822c8c3f5f96f0efa372ec5",
        33_517_622_306,
    ),
    "v1.0-trainval10_blobs.tgz": (
        "046aa7c5ff2cab63a25eaa6210e00bd8197f835e5324457d305a2a16a262f57a",
        41_727_447_974,
    ),
    # Staged by iteration 47 from the public Motional bucket (see
    # experiments/iter47_map_staging_and_off_completion); its extraction is the maps
    # basemap/expansion/prediction content pinned below.
    "nuScenes-map-expansion-v1.3.zip": (
        "9dbc80a095b6b28d9b79fc9a43471a750dc92ca78c6d0db288fd92b34be5a144",
        398_535_531,
    ),
}
EXPECTED_DATASET_ARCHIVE_TOTAL_BYTES = 315_285_139_203
EXPECTED_DATASET_METADATA_FILES = (
    "attribute.json",
    "calibrated_sensor.json",
    "category.json",
    "ego_pose.json",
    "instance.json",
    "log.json",
    "map.json",
    "sample.json",
    "sample_annotation.json",
    "sample_data.json",
    "scene.json",
    "sensor.json",
    "visibility.json",
)
EXPECTED_DATASET_MAP_ANCHORS = (
    "36092f0b03a857c6a3403e25b4b7aab3.png",
    "37819e65e09e5547b8a3ceaefba56bb2.png",
    "53992ee3023e5494b90c316c183be829.png",
    "93406b464a165eaba6d9de76ca09f5da.png",
    "LICENSE",
)
# The nuScenes map-expansion v1.3 pack extracted by iteration 47. Iteration 135 never reads
# these payloads; the contract pins the directory shape so the shared evidence volume's true
# state validates exactly instead of being reported as unexpected.
EXPECTED_DATASET_MAP_DIRECTORIES = {
    "basemap": (
        "boston-seaport.png",
        "singapore-hollandvillage.png",
        "singapore-onenorth.png",
        "singapore-queenstown.png",
    ),
    "expansion": (
        "boston-seaport.json",
        "singapore-hollandvillage.json",
        "singapore-onenorth.json",
        "singapore-queenstown.json",
    ),
    "prediction": ("prediction_scenes.json",),
}
EXPECTED_DATASET_PROOF_BASIS = {
    "iteration": 28,
    "result_path": "experiments/iter28_nuscenes_trainval_staging/RESULT.md",
    "receipt_directory": ("experiments/iter28_nuscenes_trainval_staging/proof-staging/uploads"),
    "archive_count": 12,
    "archive_total_bytes": EXPECTED_DATASET_ARCHIVE_TOTAL_BYTES,
    "map_expansion_result_path": (
        "experiments/iter47_map_staging_and_off_completion/RESULT.md"
    ),
}
ITER28_DATASET_PROOF_DIRECTORY_REL = Path(EXPECTED_DATASET_PROOF_BASIS["receipt_directory"])
# The map-expansion archive was staged by iteration 47, not iteration 28; its byte proof is the
# committed iteration-47 staging receipt and is replayed separately below.
MAP_EXPANSION_ARCHIVE_NAME = "nuScenes-map-expansion-v1.3.zip"
ITER47_MAP_EXPANSION_PROOF_REL = Path(
    "experiments/iter47_map_staging_and_off_completion/proof-staging/staging_receipts.json"
)


def canonical_dataset_contract_payload() -> dict[str, Any]:
    """Return the immutable, environment-independent nuScenes contract."""

    return {
        "schema": EXPECTED_DATASET_SCHEMA,
        "dataset_root": EXPECTED_DATASET_ROOT,
        "dataset_version": EXPECTED_DATASET_VERSION,
        "archive_root": EXPECTED_DATASET_ARCHIVE_ROOT,
        "metadata_root": EXPECTED_DATASET_METADATA_ROOT,
        "map_root": EXPECTED_DATASET_MAP_ROOT,
        "mount": EXPECTED_DATASET_MOUNT,
        "proof_basis": EXPECTED_DATASET_PROOF_BASIS,
        "archives": {
            name: {"sha256": digest, "bytes": byte_count}
            for name, (digest, byte_count) in sorted(EXPECTED_DATASET_ARCHIVES.items())
        },
        "metadata_json_names": list(EXPECTED_DATASET_METADATA_FILES),
        "map_anchor_names": list(EXPECTED_DATASET_MAP_ANCHORS),
        "map_directory_names": {
            name: list(files)
            for name, files in sorted(EXPECTED_DATASET_MAP_DIRECTORIES.items())
        },
    }


def _canonical_json_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


# Independent constant: changing any path, filename, archive digest, byte count, device identity,
# or proof locator makes manifest generation fail closed until the change is explicitly audited.
EXPECTED_DATASET_CONTRACT_SHA256 = (
    "f61363c91fa6e0f3db24a6df2e32afc16ad02ebc44e3c4af66132fcc317760c2"
)

# Role -> (absolute execution-host path, SHA256, byte length).  Every file below is read by the
# frozen launch path or controls its repository's load-bearing dirty state.  The environment
# receipt must contain exactly this role set: no basename inference, wildcard trust, or receipt
# self-declaration can substitute for byte identity.
EXPECTED_REMOTE_FILES: dict[str, tuple[str, str, int]] = {
    "compose_script": (
        "/opt/sentinel-stack/NeuroNCAP/scripts/_docker_compose_release.sh",
        EXPECTED_COMPOSE_OUTPUT_SHA256,
        3_613,
    ),
    "uniad_server_baseline": (
        "/opt/sentinel-stack/UniAD/inference/server.py",
        "066a3fc31a2c78960255cedf659018bab4190ac5dee7e7c5ec14d1031043c424",
        4_519,
    ),
    "uniad_runner": (
        "/opt/sentinel-stack/UniAD/inference/runner.py",
        "9fd3d3dcc3472495005bad57a79c52d3123c30cd6043c96e8c4bcad64bbace35",
        18_732,
    ),
    "uniad_inference_config": (
        "/opt/sentinel-stack/UniAD/projects/configs/stage2_e2e/inference_e2e.py",
        "6be66465a80eafd69d3c9865199cdd6eb2bd6dea663e0689cd60687b438d90c9",
        436,
    ),
    "uniad_base_config": (
        "/opt/sentinel-stack/UniAD/projects/configs/stage2_e2e/base_e2e.py",
        "ebd657c9d6ebcde64210f56917e04855d2d058a1c7f3d12bb546d2d7a17e7404",
        23_659,
    ),
    "uniad_dataset_config": (
        "/opt/sentinel-stack/UniAD/projects/configs/_base_/datasets/nus-3d.py",
        "89f7e6d1fa1707826b6d409d522cddea06ab6489ab030222e25cd83af7e77445",
        4_915,
    ),
    "uniad_runtime_config": (
        "/opt/sentinel-stack/UniAD/projects/configs/_base_/default_runtime.py",
        "778df7b551bf0348f09490f0e8df0252d2bd8c006ba916153a6b0f74e4b5c988",
        485,
    ),
    "checkpoint": (
        "/opt/sentinel-stack/UniAD/ckpts/uniad_base_e2e.pth",
        EXPECTED_CHECKPOINT_SHA256,
        EXPECTED_CHECKPOINT_BYTES,
    ),
    "shim": (
        "/opt/sentinel-stack/UniAD/projects/mmdet3d_plugin/uniad/detectors/uniad_track.py",
        EXPECTED_SHIM_SHA256,
        33_601,
    ),
    "neuroncap_dockerfile": (
        "/opt/sentinel-stack/NeuroNCAP/docker/Dockerfile",
        "972dab1854bebb14bccfe78d620d1d53773b2c7f5893046201903fde8bdd3b06",
        1_157,
    ),
    "neuroncap_main": (
        "/opt/sentinel-stack/NeuroNCAP/main.py",
        "0807d9cf304d578d49045aa26305f341b64f9f3a620b897ee4923bbc51cb6842",
        2_307,
    ),
    "neuroncap_engine": (
        "/opt/sentinel-stack/NeuroNCAP/neuro_ncap/engine.py",
        "0524060181ab255b027d793292ce35107eb8f1e61a80d9346c1f5488ae640deb",
        15_232,
    ),
    "neuroncap_evaluator": (
        "/opt/sentinel-stack/NeuroNCAP/neuro_ncap/components/evaluator.py",
        "679d0a08a58e079ba8fa41508963a450e75f98211e66d4532ec5a99e4becfddc",
        7_495,
    ),
    "neuroncap_scenario": (
        "/opt/sentinel-stack/NeuroNCAP/neuro_ncap/components/scenario.py",
        "8bccf527d47206b90b3d83df1c15c71f7f57b33d175a30b4ff6253aac09a30c8",
        7_529,
    ),
    "neuroncap_config": (
        "/opt/sentinel-stack/NeuroNCAP/neuro_ncap/utils/config.py",
        "75f81a5d58f59a8356e6508ee34f8703892adb48d92cd09daf78dc6c306bc675",
        966,
    ),
    "neuroncap_collision": (
        "/opt/sentinel-stack/NeuroNCAP/neuro_ncap/evaluation/collision.py",
        "a052b62f1854d689e48ef9fec2c34d76953ec527bc3120d139b8815dcc478c2b",
        6_852,
    ),
    "neuroncap_target_recall": (
        "/opt/sentinel-stack/NeuroNCAP/neuro_ncap/evaluation/target_recall.py",
        "8f6ec56add89a3672b9e06af90534fb5252ea9fca4b6cecaeeb87091e958dbac",
        15_831,
    ),
    "neurad_dockerfile": (
        "/opt/sentinel-stack/neurad-studio/Dockerfile",
        "147c4505d116322bf4ee7f147588e8afd7f2cc3812afe40808bfc88bc566d799",
        4_851,
    ),
    "neurad_dockerfile_backup": (
        "/opt/sentinel-stack/neurad-studio/Dockerfile.bak",
        "39d436db5de8aa5c45630b7e838d77fa96ee44cda0d8ce512e9c6278a578faec",
        5_478,
    ),
    "neurad_main": (
        "/opt/sentinel-stack/neurad-studio/nerfstudio/scripts/closed_loop/main.py",
        "c7927ca1affdf9d726dc6559ab0fd4e88dfcb0c7253b661fb6bf0d198bc4e17d",
        3_774,
    ),
}

EXPECTED_SCENARIO_FILES = {
    "stationary/0099": ("30b366a008a03aa4515cddb89152747e8c3fdd24bf49e09166443d753e25597a", 819),
    "stationary/0101": ("a02960dfbed3356ee23a625c051a9c9e14e0703de70c917633d2055ff063edf3", 633),
    "stationary/0103": ("f5fb357117194345fbece4ab0fdaac467f7b1ed5c546ad4eb96a019a4e59a461", 671),
    "stationary/0106": ("6059240a5ae3b6c9c472bd47f88403cd1463f36b22d8265d20a074ec0795cca2", 659),
    "stationary/0108": ("41971edd3aa33870ad000f9eab02eaa344459f19420a8605a378a29366462902", 679),
    "stationary/0278": ("8921aebc2626662fa68d2c2bf9e4129f7e5f5ade2bd7a236853a777654b98253", 515),
    "stationary/0331": ("633a81f30bee926b250a9d69ca448b9c3687644124d097be15f0c03831d61c4b", 628),
    "stationary/0783": ("56629a32862e402c3328cb0344f002a228e280df665c0709a589ed90bb2401aa", 509),
    "stationary/0796": ("b2c6bca31f9c1d29596ada9a2e0f38fcdbf20ac517762668b1c4a2fdb1ace818", 648),
    "stationary/0966": ("f5baacc86e11fab7148afc6c97727418e35bafecc8cf41ed8cf1267919d42fc1", 578),
    "frontal/0103": ("26e4a95cfde049a473f5fd31fa4853dc4cc37647469e10bd5b18fcfdf2a28621", 638),
    "frontal/0106": ("b75c7653c5118938706cc05cf70dd408851c93fc34e22333c4d330a5336d27ba", 685),
    "frontal/0110": ("86af35807d9e09511aeb3dd75b898db74ab3b404eda10036c587fcb13db91cc6", 721),
    "frontal/0346": ("64fcc53c55279db1d7c02799db9c34e9465cac5574690c614760a5a8ab678705", 540),
    "frontal/0923": ("dbbd9e1b6c881901c27548e645f41fe81fc2dad52fa4127410b13cf573635785", 856),
    "side/0103": ("b2316d0493fa2db50ca7729c77485432dffb99b599aa072e4becc3a86cc91ab9", 633),
    "side/0108": ("c20e364a32729aae2c4494e39dbcb6ab043dc790928ca8e47eeef3e85f8bdf66", 995),
    "side/0110": ("6acb11491fefe7e7d4a265fab7eb3c2ef411104ecd16cc44fdecf492f8e56b70", 726),
    "side/0278": ("39ac5ea672d498abedca2a1e4fa676353e1a907ed77cb3e5fb25786a51e4ad9b", 646),
    "side/0921": ("ef0cff20f06f9bde22cda577854af63d6f94c72f73694605fa429e832ea4268f", 628),
}

for _scenario_id, (_digest, _bytes) in EXPECTED_SCENARIO_FILES.items():
    EXPECTED_REMOTE_FILES[f"scenario:{_scenario_id}"] = (
        f"/opt/sentinel-stack/NeuroNCAP/scenarios/{_scenario_id}.yaml",
        _digest,
        _bytes,
    )

EXPECTED_RENDERER_FILES = {
    "0099": (
        ("30293d95c925d8343047f31a60609baf97f536e7037e48c5f9876717eeb5f5c7", 21_892),
        ("2b794fe81a8bebbb058a332b0aacb8fbfc78e67fcf8ec0342bfcd323738a026d", 528),
        ("0759369aad4f0fd757b26ad1e8d15c4124395a603a4970667a4f0a70beec49e1", 1_039_780_312),
    ),
    "0101": (
        ("8fd80809b192e190e253b485eca0caebc29de6e05b660ee3fddb0ca799a92830", 21_892),
        ("b59d31f6ce0306f2e1282b99fc110dd9b5c51ffb6f4c17ccb478256f3ff1e94c", 509),
        ("a7df093a95ac994b7864ab57f379309b58d965bf2305f6800d382bef933847d2", 1_040_564_312),
    ),
    "0103": (
        ("1c5a5b048314b892ff5ceaca6012455874fd139f0e7aadd4eeff2dd67aa459c0", 21_892),
        ("d147721166c31064714e18bf067e1125ef8e21bd759156209d49cecd954c5eba", 508),
        ("20b1d37f06eb050cb2b599a26185b8eb12e74ec1302c2ccffc5c5165de68b4e3", 1_040_783_384),
    ),
    "0106": (
        ("ed16bbc22ccc657133de889001b41d28c3deac3f44b8efbee0d7808d7ea85a5d", 21_892),
        ("04a8259c41145df6825b5f15f2cc83fa99f000b34b594bf1a0fb2733fe0c5f77", 533),
        ("b7dbba4f71ab4ea49dd517c839f254d35179c6a56f130eef215997c1b9980a5f", 1_040_036_952),
    ),
    "0108": (
        ("a0eb42f4a452758ee0b212957d95cf1abb4df71d2894516672c333b586996185", 21_892),
        ("7e5f8cf91bc0fd670a78ebe4768047116a6552a1002bf326395d0d64bba6b24d", 532),
        ("a149f79eb9755b631b381709f3fa9bcb574fea64b6e0a445e962c388a19c8b54", 1_039_274_712),
    ),
    "0110": (
        ("62d7e4b75d50180b4adb21c5087e0659b20e8458c0eea3202660637aad36d87e", 21_892),
        ("8a21cfb48b3dda83c09d2f6798b31b44dee0449eee5f58ed0531651d98aceb88", 547),
        ("a8a075e568d1a74a7e1ab43861c7dde22be292e06b21134c157d01de02a4d25c", 1_039_394_200),
    ),
    "0278": (
        ("50527fd67f825201eec5eb9ec899419915403038db77ea2d07b952795c431545", 21_892),
        ("e0b63a6337b0392ff2b5ead39f5bb45bd006b9f119b8dfe3ceee3650b784de33", 529),
        ("ed69f23d14a081ba40d467ac695f2548f26204d7c8616e4d6950559eb13d0f93", 1_039_453_208),
    ),
    "0331": (
        ("d8dcde849d91b6ae635d24e80b9981318b270467ced277a0faf1023ec71fd07b", 21_892),
        ("c31b0509636c7c450004a66d67533275bc59d53e2fa2862a257c9d833050eb39", 508),
        ("f753ffecd4103038ebe9babba4d0e50262c8963e1206beaabb99a9124977a72a", 1_038_906_200),
    ),
    "0346": (
        ("a4e943d80bd876a459b7e13be9c0b541b1f6a9b0e6b00b98087c4921fa0846f4", 21_892),
        ("718281afd629c3cb91c3c850d7e998de6d1185d01fee936ae2e4931ddf7f3707", 525),
        ("9ec852b2ef5cc95666be0759a7dcb5b3d876ced3739fd2da788b1a706b40aa72", 1_038_807_896),
    ),
    "0783": (
        ("34e0451a0eb6a50d8562614f68e9a3159338c8419e2027a39c21cabb8363b457", 21_892),
        ("e84f1f7a7516ebaa119e87e8a1df642a0563b7229ae650cea63692be8114de7a", 529),
        ("75bb4599d3b7ae85dc6dbc23c15f04d3e4f422d2c7c8ef79e6268e39647b4ad6", 1_040_172_184),
    ),
    "0796": (
        ("8f2c73462518853cb11312aa47c72d4c8ab6906003e549c3d1c11e5ee3c85825", 21_892),
        ("609292580dfa0659932a100a247b0bb0c17bb337c0583f5689903590ae88c0cb", 510),
        ("ba21bee72203f8818fe14c35570dd6a2a8ed9e89d5ac827f693fde84d0413fd8", 1_040_211_800),
    ),
    "0921": (
        ("85761c6d8a12a5b5c215610475cb882ff7e4a982d7542ad8cc408d7c4b25f41d", 21_892),
        ("66b479221a77a03ad8184558be1dcdda032ec2a214e8d8abe32c0e63b910a9f6", 541),
        ("4bef4f7eb58be05339596486f2c5f51ab261516e8afb9b6ee793576e0358a95a", 1_038_714_904),
    ),
    "0923": (
        ("c4b926fc6313b0953767a6e324947b62fd6c99aad539dfdb023ef38f6b7ad81f", 21_892),
        ("a6b6ae20260111080b5a4e736f2200ef9d81e226348afc80b256125c244ad02b", 509),
        ("da7722849de977829c6dfe7061580e30326da9698f9d5f429e6a966fb7c1177c", 1_038_969_368),
    ),
    "0966": (
        ("9e2b4696645ca838248c9a447b5dc45a1c9b4d256ddf601ea503725e5b7c8fc6", 21_892),
        ("9cc3f04192775ef7e94fd449c9ba6a74a66882529c220cc06ec34cad60a9cb52", 512),
        ("352a1458be429f4e77e49e79990607f818832d8be8d352f734f365d3487d5b7d", 1_039_731_352),
    ),
}

for _sequence, _receipts in EXPECTED_RENDERER_FILES.items():
    for _kind, _filename, (_digest, _bytes) in zip(
        ("config", "transforms", "checkpoint"),
        ("config.yml", "dataparser_transforms.json", "step-000150000.ckpt"),
        _receipts,
        strict=True,
    ):
        EXPECTED_REMOTE_FILES[f"renderer:{_sequence}:{_kind}"] = (
            f"/opt/sentinel-stack/neurad-studio/checkpoints/{_sequence}/{_filename}",
            _digest,
            _bytes,
        )

EXPECTED_REMOTE_PATHS = {
    role: path for role, (path, _digest, _bytes) in EXPECTED_REMOTE_FILES.items()
}
EXPECTED_REQUIRED_UNTRACKED_BINDINGS = {
    ("neurad", "Dockerfile.bak"): "neurad_dockerfile_backup",
}

SOURCE_ARTIFACTS = {
    "iter134_oracle_log": (
        "experiments/iter134_neuroncap_placebo_semantics_execution/proof/sentinel-i134.log.gz",
        "55c5a77e898f1a1834a984dd02c576f128c0ac445c71f9721256beaac2b04b14",
    ),
    "iter134_oracle_runs": (
        "experiments/iter134_neuroncap_placebo_semantics_execution/proof/i134-runs.tar.gz",
        "b6e7522c7f709d550c51df5de6ed7b67339335ee3e74f0b1e068f377b2ce8315",
    ),
    "iter134_union_part_aa": (
        "experiments/iter134_neuroncap_placebo_semantics_execution/proof/"
        "sentinel_i134_union.jsonl.gz.part-aa",
        "4a4b90a383613ebd228a24b510d59f2214695a3a020858d082187f1e507ffb85",
    ),
    "iter134_union_part_ab": (
        "experiments/iter134_neuroncap_placebo_semantics_execution/proof/"
        "sentinel_i134_union.jsonl.gz.part-ab",
        "93a39b950789c1416055e32ea2056e3a9f8202f14f885b4f789458f4d8b4ca97",
    ),
    "iter15_released_union": (
        "experiments/iter15_latch_release/server_patch_union_release.py",
        EXPECTED_UNION_SHA256,
    ),
    "iter134_released_union": (
        "experiments/iter134_neuroncap_placebo_semantics_execution/server_patch_union_release.py",
        EXPECTED_UNION_SHA256,
    ),
}

REQUIRED_PAYLOAD_NAMES = (
    "HYPOTHESIS.md",
    "authorize_launch135.py",
    "extract_union_windows.py",
    "generate_nested_dose_schedules.py",
    "dose_schedules.json",
    "server_patch_union_release.py",
    "server_patch_blind_dose.py",
    "analyze_dose135.py",
    "collect_proof135.py",
    "run_dose135.sh",
    "run_smoke135.sh",
    "validate_smoke135.py",
    "capture_environment135.py",
    "prepare_host135.py",
    "verify_tooling135.py",
    "patch_compose_dose_env.py",
    "make_launch_manifest.py",
)

EXPECTED_ENV_SCHEMA = "iter135.environment_receipts.v3"
EXPECTED_ENV_VERDICT = "I135_ENVIRONMENT_PREFLIGHT_OK"
EXPECTED_HOST_PACKET_SCHEMA = "iter135.host_packet_manifest.v1"
EXPECTED_HOST_PREPARATION_SCHEMA = "iter135.host_preparation_receipt.v1"
EXPECTED_HOST_PREPARATION_VERDICT = "I135_HOST_PREPARATION_OK"
EXPECTED_PUBLICATION_AUTHORITY_SCHEMA = "iter135.github_publication_authority.v1"
EXPECTED_PUBLICATION_REPOSITORY = "manfromnowhere143/sentinel"
EXPECTED_PUBLICATION_BRANCH = "master"
EXPECTED_PUBLICATION_CHECKS = ("check (3.10)", "check (3.11)")
EXPECTED_DOCKER_RUNTIME_SCHEMA = "iter135.docker_runtime_receipt.v1"
EXPECTED_SMOKE_SCHEMA = "iter135.smoke_receipt.v1"
EXPECTED_SMOKE_VERDICT = "I135_LIVE_SMOKE_OK"
EXPECTED_TOOLING_SCHEMA = "iter135.tooling_verification.v2"
EXPECTED_TOOLING_VERDICT = "I135_TOOLING_VERIFICATION_OK"
ENV_RECEIPT_REL = "env_receipts.json"
HOST_PACKET_MANIFEST_REL = "host_packet_manifest.json"
HOST_PREPARATION_RECEIPT_REL = "host_preparation_receipt.json"
SMOKE_RECEIPT_REL = "smoke-evidence/smoke_receipt.json"
SMOKE_SUMMARY_REL = "smoke-evidence/SMOKE.md"
TOOLING_RECEIPT_REL = "tooling_verification_receipt.json"
HOST_PACKET_FILE_NAMES = (
    "MISSION_STATE.json",
    "HYPOTHESIS.md",
    "extract_union_windows.py",
    "generate_nested_dose_schedules.py",
    "dose_schedules.json",
    "server_patch_union_release.py",
    "server_patch_blind_dose.py",
    "analyze_dose135.py",
    "collect_proof135.py",
    "run_dose135.sh",
    "run_smoke135.sh",
    "validate_smoke135.py",
    "capture_environment135.py",
    "verify_tooling135.py",
    "patch_compose_dose_env.py",
    "make_launch_manifest.py",
    "authorize_launch135.py",
    TOOLING_RECEIPT_REL,
    "prepare_host135.py",
)
HOST_PACKET_EXECUTABLE_FILES = {
    "capture_environment135.py",
    "run_smoke135.sh",
    "validate_smoke135.py",
    "prepare_host135.py",
}
EXPECTED_CAPTURE_ENVIRONMENT = {
    "DOCKER_CONFIG": "/nonexistent",
    "DOCKER_HOST": "unix:///var/run/docker.sock",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_TERMINAL_PROMPT": "0",
    "HOME": "/nonexistent",
    "LANG": "C",
    "LC_ALL": "C",
    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "SENTINEL_I135_CAPTURE_SANITIZED": "1",
    "TZ": "UTC",
}

RISK_TOKENS = (
    "aux_outputs",
    "objects_in_bev",
    "object_scores",
    "future_trajs",
    "object_ids",
    "ego2world",
    "timestamp",
    "SENTINEL_TTC",
    "SENTINEL_CPA_MARGIN",
    "SENTINEL_MIN_CLOSING",
    "SENTINEL_MAXGAP",
    "SENTINEL_MIN_SCORE",
    "SENTINEL_RELEASE_K",
)
REQUIRED_MODEL_ENV = (
    "SENTINEL_ENABLED",
    "SENTINEL_DOSE_PAIR",
    "SENTINEL_DOSE_ID",
    "SENTINEL_DOSE_SCHEDULE",
    "SENTINEL_LOG",
    "SENTINEL_RELEASE_K",
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GPU_UUID_RE = re.compile(r"^GPU-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$")
_IMAGE_ID_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_GIT_OBJECT_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")


def _parse_canonical_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    canonical = parsed.isoformat().replace("+00:00", "Z")
    if parsed.tzinfo != timezone.utc or canonical != value:
        return None
    return parsed


def canonical_pairs() -> tuple[tuple[str, str], ...]:
    return tuple((cls, seq) for cls in CLASSES for seq in CLASS_PAIRS[cls])


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_receipt(path: Path, source_path: str) -> dict[str, Any]:
    return {
        "source_path": source_path,
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def _git_blob_oid(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload, usedforsecurity=False).hexdigest()


def authority_artifact_receipt(
    path: Path, source_path: str, *, git_mode: str
) -> dict[str, Any] | None:
    if git_mode not in {"100644", "100755"}:
        return None
    try:
        payload = path.read_bytes()
    except OSError:
        return None
    return {
        "path": source_path,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "git_blob_oid": _git_blob_oid(payload),
        "git_mode": git_mode,
    }


def git_blob_receipt(
    repo_root: Path, commit: str, relative_path: str
) -> dict[str, Any] | None:
    """Read one committed blob without consulting mutable worktree bytes."""

    if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        return None
    completed = subprocess.run(  # noqa: S603 - fixed Git binary and validated revision/path
        ("/usr/bin/git", "-C", str(Path(repo_root)), "show", f"{commit}:{relative_path}"),
        env={
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "HOME": "/nonexistent",
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        },
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        timeout=10,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return {
        "source_path": relative_path,
        "sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "bytes": len(completed.stdout),
        "git_blob_oid": _git_blob_oid(completed.stdout),
        "git_mode": "100644",
    }


def execution_plan() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Materialize the amended 120-block pair-major execution plan."""

    blocks: list[dict[str, Any]] = []
    cells: list[dict[str, Any]] = []
    for pair_index, (cls, seq) in enumerate(canonical_pairs()):
        rotation = pair_index % len(ARMS)
        arm_order = ARMS[rotation:] + ARMS[:rotation]
        for block_position, arm_id in enumerate(arm_order):
            block_ordinal = len(blocks)
            block = {
                "ordinal": block_ordinal,
                "pair_index": pair_index,
                "scenario_class": cls,
                "sequence": seq,
                "temporal_position": block_position,
                "arm_id": arm_id,
                "run_indices": list(RUN_INDICES),
            }
            blocks.append(block)
            for run_index in RUN_INDICES:
                cells.append(
                    {
                        "ordinal": len(cells),
                        "block_ordinal": block_ordinal,
                        "pair_index": pair_index,
                        "scenario_class": cls,
                        "sequence": seq,
                        "temporal_position": block_position,
                        "arm_id": arm_id,
                        "run_index": run_index,
                    }
                )
    return blocks, cells


def validate_execution_plan(
    blocks: Sequence[Mapping[str, Any]], cells: Sequence[Mapping[str, Any]]
) -> list[str]:
    problems: list[str] = []
    if len(blocks) != PLANNED_BLOCKS:
        problems.append(f"execution:block-count:{len(blocks)}!={PLANNED_BLOCKS}")
    if len(cells) != PLANNED_EPISODES:
        problems.append(f"execution:cell-count:{len(cells)}!={PLANNED_EPISODES}")

    expected_cells = {
        (arm, cls, seq, run)
        for arm in ARMS
        for cls, seq in canonical_pairs()
        for run in RUN_INDICES
    }
    actual_cells = [
        (
            cell.get("arm_id"),
            cell.get("scenario_class"),
            cell.get("sequence"),
            cell.get("run_index"),
        )
        for cell in cells
    ]
    if len(actual_cells) != len(set(actual_cells)):
        problems.append("execution:duplicate-cell")
    if set(actual_cells) != expected_cells:
        problems.append("execution:cell-population")

    position_counts: Counter[tuple[str, int]] = Counter()
    for expected_ordinal, block in enumerate(blocks):
        if block.get("ordinal") != expected_ordinal:
            problems.append(f"execution:block-ordinal:{expected_ordinal}")
            continue
        pair_index = block.get("pair_index")
        position = block.get("temporal_position")
        if not isinstance(pair_index, int) or pair_index not in range(20):
            problems.append(f"execution:block-pair-index:{expected_ordinal}")
            continue
        if not isinstance(position, int) or position not in range(6):
            problems.append(f"execution:block-position:{expected_ordinal}")
            continue
        expected_arm = ARMS[(pair_index % 6 + position) % 6]
        if block.get("arm_id") != expected_arm:
            problems.append(f"execution:block-arm-order:{expected_ordinal}")
        expected_pair = canonical_pairs()[pair_index]
        if (block.get("scenario_class"), block.get("sequence")) != expected_pair:
            problems.append(f"execution:block-pair:{expected_ordinal}")
        if block.get("run_indices") != list(RUN_INDICES):
            problems.append(f"execution:block-runs:{expected_ordinal}")
        position_counts[(expected_arm, position)] += 1

        start = expected_ordinal * 20
        block_cells = cells[start : start + 20]
        expected_runs = list(RUN_INDICES)
        if [cell.get("run_index") for cell in block_cells] != expected_runs:
            problems.append(f"execution:block-cell-runs:{expected_ordinal}")
        if any(cell.get("block_ordinal") != expected_ordinal for cell in block_cells):
            problems.append(f"execution:block-cell-link:{expected_ordinal}")

    if any(count not in {3, 4} for count in position_counts.values()):
        problems.append("execution:arm-position-balance")
    if set(position_counts) != {(arm, position) for arm in ARMS for position in range(6)}:
        problems.append("execution:arm-position-coverage")
    return problems


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite_json(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _load_json(path: Path, label: str, problems: list[str]) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_nonfinite_json,
        )
    except (OSError, UnicodeDecodeError, ValueError) as error:
        problems.append(f"invalid-json:{label}:{type(error).__name__}")
        return None
    if not isinstance(value, dict):
        problems.append(f"invalid-json-object:{label}")
        return None
    return value


def validate_mission_state(state: Mapping[str, Any] | None) -> list[str]:
    if state is None:
        return ["mission-state:missing"]
    problems: list[str] = []
    if set(state) != EXPECTED_MISSION_STATE_FIELDS:
        problems.append("mission-state:field-set")
    if state.get("schema") != EXPECTED_MISSION_SCHEMA:
        problems.append("mission-state:schema")
    if state.get("canonical_repository") != EXPECTED_CANONICAL_REPOSITORY:
        problems.append("mission-state:canonical-repository")
    if state.get("workspace_boundary") != EXPECTED_WORKSPACE_BOUNDARY:
        problems.append("mission-state:workspace-boundary")
    if state.get("trunk") != "master":
        problems.append("mission-state:trunk")
    if state.get("current_completed_iteration") != 134:
        problems.append("mission-state:completed-iteration")
    if state.get("current_result") != (
        "experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md"
    ):
        problems.append("mission-state:current-result")
    if state.get("current_verdict") != "PLACEBO_HARM_OR_NULL":
        problems.append("mission-state:current-verdict")
    if state.get("active_hypothesis") != ACTIVE_HYPOTHESIS:
        problems.append("mission-state:active-hypothesis")
    if state.get("claim_state") != EXPECTED_MISSION_CLAIM_STATE:
        problems.append("mission-state:claim-state")
    if state.get("deprecated_pending_hypotheses") != EXPECTED_DEPRECATED_HYPOTHESES:
        problems.append("mission-state:deprecated-hypotheses")
    if state.get("paper_state") != EXPECTED_PAPER_STATE:
        problems.append("mission-state:paper-state")
    next_program = state.get("next_program")
    expected_program_fields = {
        "iteration",
        "name",
        "phase",
        "authorized_actions",
        "forbidden_actions",
    }
    if not isinstance(next_program, dict) or set(next_program) != expected_program_fields:
        problems.append("mission-state:next-program-field-set")
    if not isinstance(next_program, dict) or next_program.get("iteration") != 135:
        problems.append("mission-state:next-iteration")
    if not isinstance(next_program, dict) or next_program.get("name") != EXPECTED_PROGRAM_NAME:
        problems.append("mission-state:next-program-name")
    phase = next_program.get("phase") if isinstance(next_program, dict) else None
    if phase not in ALLOWED_MISSION_PHASES:
        problems.append(f"mission-state:phase:{phase!r}:not-in-{sorted(ALLOWED_MISSION_PHASES)!r}")
    elif isinstance(next_program, dict):
        authorized, forbidden = EXPECTED_PHASE_ACTIONS[phase]
        if next_program.get("authorized_actions") != list(authorized):
            problems.append("mission-state:authorized-actions")
        if next_program.get("forbidden_actions") != list(forbidden):
            problems.append("mission-state:forbidden-actions")
    if state.get("run_state") != "IDLE":
        problems.append(f"mission-state:run-state:{state.get('run_state')!r}")
    storage = state.get("storage_gate")
    if not isinstance(storage, dict):
        problems.append("mission-state:storage-gate")
    else:
        expected_storage_fields = {
            "minimum_local_free_gib_before_new_proof_collection",
            "remote_execution_filesystem_path",
            "analytic_output_root",
            "minimum_remote_execution_filesystem_free_gib_before_gpu_launch",
            "minimum_remote_execution_filesystem_reserve_gib_after_projected_output",
            "policy",
        }
        if set(storage) != expected_storage_fields:
            problems.append("mission-state:storage-field-set")
        if storage.get("minimum_local_free_gib_before_new_proof_collection") != 15:
            problems.append("mission-state:local-storage-threshold")
        if storage.get("remote_execution_filesystem_path") != "/datasets/nuscenes-full":
            problems.append("mission-state:execution-filesystem")
        if storage.get("analytic_output_root") != EXPECTED_OUTPUT_ROOT:
            problems.append("mission-state:analytic-output-root")
        if storage.get("minimum_remote_execution_filesystem_free_gib_before_gpu_launch") != 100:
            problems.append("mission-state:remote-storage-threshold")
        if (
            storage.get("minimum_remote_execution_filesystem_reserve_gib_after_projected_output")
            != 25
        ):
            problems.append("mission-state:remote-storage-reserve")
        if storage.get("policy") != (
            "preserve committed proof and hashes; delete only hash-verified duplicates, "
            "reproducible renders, and caches"
        ):
            problems.append("mission-state:storage-policy")
    return problems


def _valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


def _valid_bounded_text(value: Any, *, maximum: int = 256) -> bool:
    return (
        isinstance(value, str)
        and 0 < len(value) <= maximum
        and all(ord(character) >= 32 and ord(character) != 127 for character in value)
    )


def _docker_architecture_family(value: Any) -> Any:
    return {
        "amd64": "amd64",
        "x86_64": "amd64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }.get(value, value)


def validate_publication_authority(
    authority: Any,
    *,
    expected_commit: str | None = None,
    expected_artifacts: Sequence[Mapping[str, Any]] | None = None,
    label: str = "publication-authority",
) -> list[str]:
    """Validate the bounded GitHub branch/check attestation used as launch authority."""

    problems: list[str] = []
    expected_fields = {
        "schema",
        "repository",
        "branch",
        "source_commit",
        "branch_head_sha",
        "required_checks",
        "checks",
        "artifacts",
        "verified",
    }
    if not isinstance(authority, Mapping) or set(authority) != expected_fields:
        return [f"{label}:field-set"]
    if authority.get("schema") != EXPECTED_PUBLICATION_AUTHORITY_SCHEMA:
        problems.append(f"{label}:schema")
    if authority.get("repository") != EXPECTED_PUBLICATION_REPOSITORY:
        problems.append(f"{label}:repository")
    if authority.get("branch") != EXPECTED_PUBLICATION_BRANCH:
        problems.append(f"{label}:branch")
    source_commit = authority.get("source_commit")
    if not isinstance(source_commit, str) or re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        problems.append(f"{label}:source-commit")
    if expected_commit is not None and source_commit != expected_commit:
        problems.append(f"{label}:expected-commit")
    if authority.get("branch_head_sha") != source_commit:
        problems.append(f"{label}:branch-head")
    if authority.get("required_checks") != list(EXPECTED_PUBLICATION_CHECKS):
        problems.append(f"{label}:required-checks")
    if authority.get("verified") is not True:
        problems.append(f"{label}:verified")

    artifacts = authority.get("artifacts")
    if expected_artifacts is not None:
        if artifacts != [dict(row) for row in expected_artifacts]:
            problems.append(f"{label}:artifacts")
    elif not isinstance(artifacts, list) or not all(
        isinstance(row, Mapping)
        and set(row)
        == {"path", "sha256", "bytes", "git_blob_oid", "git_mode"}
        and _valid_bounded_text(row.get("path"), maximum=1024)
        and _valid_sha256(row.get("sha256"))
        and type(row.get("bytes")) is int
        and 0 < row["bytes"] <= 2**40
        and isinstance(row.get("git_blob_oid"), str)
        and re.fullmatch(r"[0-9a-f]{40}", row["git_blob_oid"]) is not None
        and row.get("git_mode") in {"100644", "100755"}
        for row in artifacts
    ):
        problems.append(f"{label}:artifacts")

    checks = authority.get("checks")
    if not isinstance(checks, list) or len(checks) != len(EXPECTED_PUBLICATION_CHECKS):
        problems.append(f"{label}:checks")
    else:
        check_ids: list[int] = []
        for expected_name, row in zip(EXPECTED_PUBLICATION_CHECKS, checks, strict=True):
            if not isinstance(row, Mapping) or set(row) != {
                "name",
                "id",
                "status",
                "conclusion",
                "head_sha",
                "app_slug",
            }:
                problems.append(f"{label}:check:{expected_name}:field-set")
                continue
            check_id = row.get("id")
            if type(check_id) is not int or check_id <= 0:
                problems.append(f"{label}:check:{expected_name}:id")
            else:
                check_ids.append(check_id)
            if row.get("name") != expected_name:
                problems.append(f"{label}:check:{expected_name}:name")
            if row.get("status") != "completed":
                problems.append(f"{label}:check:{expected_name}:status")
            if row.get("conclusion") != "success":
                problems.append(f"{label}:check:{expected_name}:conclusion")
            if row.get("head_sha") != source_commit:
                problems.append(f"{label}:check:{expected_name}:head-sha")
            if row.get("app_slug") != "github-actions":
                problems.append(f"{label}:check:{expected_name}:app")
        if len(check_ids) != len(EXPECTED_PUBLICATION_CHECKS) or len(set(check_ids)) != len(
            check_ids
        ):
            problems.append(f"{label}:check-ids")
    return sorted(set(problems))


def validate_docker_runtime_receipt(receipt: Any) -> list[str]:
    """Validate the bounded Docker client/context/daemon identity captured before smoke."""

    label = "environment:docker-runtime"
    problems: list[str] = []
    if not isinstance(receipt, Mapping) or set(receipt) != {
        "schema",
        "client",
        "context",
        "daemon",
    }:
        return [f"{label}:field-set"]
    if receipt.get("schema") != EXPECTED_DOCKER_RUNTIME_SCHEMA:
        problems.append(f"{label}:schema")

    client = receipt.get("client")
    client_fields = {
        "invocation_path",
        "physical_path",
        "realpath",
        "sha256",
        "bytes",
        "version",
    }
    client_version_fields = {
        "version",
        "api_version",
        "git_commit",
        "go_version",
        "os",
        "arch",
        "build_time",
        "context",
    }
    if not isinstance(client, Mapping) or set(client) != client_fields:
        problems.append(f"{label}:client-field-set")
        client = {}
    for field in ("invocation_path", "physical_path", "realpath"):
        value = client.get(field)
        if not _valid_bounded_text(value, maximum=1024) or not Path(value).is_absolute():
            problems.append(f"{label}:client:{field}")
    if client.get("physical_path") != client.get("realpath"):
        problems.append(f"{label}:client:realpath-drift")
    if not _valid_sha256(client.get("sha256")):
        problems.append(f"{label}:client:sha256")
    if type(client.get("bytes")) is not int or not (0 < client["bytes"] <= 2**40):
        problems.append(f"{label}:client:bytes")
    client_version = client.get("version")
    if not isinstance(client_version, Mapping) or set(client_version) != client_version_fields:
        problems.append(f"{label}:client-version-field-set")
        client_version = {}
    for field in client_version_fields:
        if not _valid_bounded_text(client_version.get(field)):
            problems.append(f"{label}:client-version:{field}")

    context = receipt.get("context")
    if not isinstance(context, Mapping) or set(context) != {"name", "endpoint"}:
        problems.append(f"{label}:context-field-set")
        context = {}
    if context.get("name") != "default":
        problems.append(f"{label}:context:name")
    if context.get("endpoint") != "unix:///var/run/docker.sock":
        problems.append(f"{label}:context:endpoint")
    if client_version.get("context") != context.get("name"):
        problems.append(f"{label}:client-context-drift")

    daemon = receipt.get("daemon")
    if not isinstance(daemon, Mapping) or set(daemon) != {"info", "version"}:
        problems.append(f"{label}:daemon-field-set")
        daemon = {}
    info = daemon.get("info")
    info_fields = {
        "id",
        "name",
        "server_version",
        "docker_root_dir",
        "driver",
        "operating_system",
        "os_type",
        "architecture",
        "ncpu",
        "mem_total",
        "kernel_version",
        "cgroup_driver",
        "cgroup_version",
    }
    if not isinstance(info, Mapping) or set(info) != info_fields:
        problems.append(f"{label}:daemon-info-field-set")
        info = {}
    for field in info_fields - {"ncpu", "mem_total", "docker_root_dir"}:
        if not _valid_bounded_text(info.get(field)):
            problems.append(f"{label}:daemon-info:{field}")
    docker_root = info.get("docker_root_dir")
    if not _valid_bounded_text(docker_root, maximum=1024) or not Path(docker_root).is_absolute():
        problems.append(f"{label}:daemon-info:docker_root_dir")
    if type(info.get("ncpu")) is not int or not (0 < info["ncpu"] <= 1_000_000):
        problems.append(f"{label}:daemon-info:ncpu")
    if type(info.get("mem_total")) is not int or not (0 < info["mem_total"] <= 2**63 - 1):
        problems.append(f"{label}:daemon-info:mem_total")

    daemon_version = daemon.get("version")
    daemon_version_fields = {
        "platform_name",
        "version",
        "api_version",
        "min_api_version",
        "git_commit",
        "go_version",
        "os",
        "arch",
        "build_time",
        "experimental",
    }
    if not isinstance(daemon_version, Mapping) or set(daemon_version) != daemon_version_fields:
        problems.append(f"{label}:daemon-version-field-set")
        daemon_version = {}
    for field in daemon_version_fields - {"experimental"}:
        if not _valid_bounded_text(daemon_version.get(field)):
            problems.append(f"{label}:daemon-version:{field}")
    if type(daemon_version.get("experimental")) is not bool:
        problems.append(f"{label}:daemon-version:experimental")
    if info.get("server_version") != daemon_version.get("version"):
        problems.append(f"{label}:daemon-version-drift")
    if info.get("os_type") != daemon_version.get("os"):
        problems.append(f"{label}:daemon-os-drift")
    if _docker_architecture_family(info.get("architecture")) != (
        _docker_architecture_family(daemon_version.get("arch"))
    ):
        problems.append(f"{label}:daemon-arch-drift")
    return sorted(set(problems))


def validate_host_preparation_evidence(
    packet_manifest: Any,
    preparation_receipt: Any,
    *,
    packet_binding: Mapping[str, Any] | None,
    expected_file_bindings: Mapping[str, Mapping[str, Any] | None],
) -> list[str]:
    """Independently bind the generated packet document to the preparation receipt."""

    problems: list[str] = []
    if not isinstance(packet_manifest, dict) or set(packet_manifest) != {
        "schema",
        "source_commit",
        "files",
    }:
        problems.append("host-packet:field-set")
        packet_manifest = {}
    if packet_manifest.get("schema") != EXPECTED_HOST_PACKET_SCHEMA:
        problems.append("host-packet:schema")
    source_commit = packet_manifest.get("source_commit")
    if not isinstance(source_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        problems.append("host-packet:source-commit")
    files = packet_manifest.get("files")
    if not isinstance(files, dict) or set(files) != set(HOST_PACKET_FILE_NAMES):
        problems.append("host-packet:file-set")
        files = {}
    for name in HOST_PACKET_FILE_NAMES:
        row = files.get(name)
        expected = expected_file_bindings.get(name)
        expected_mode = 0o755 if name in HOST_PACKET_EXECUTABLE_FILES else 0o644
        if not isinstance(row, dict) or set(row) != {"sha256", "bytes", "mode"}:
            problems.append(f"host-packet:file:{name}:field-set")
            continue
        if (
            not _valid_sha256(row.get("sha256"))
            or type(row.get("bytes")) is not int
            or row["bytes"] <= 0
            or row.get("mode") != expected_mode
        ):
            problems.append(f"host-packet:file:{name}:receipt")
        if (
            not isinstance(expected, Mapping)
            or row.get("sha256") != expected.get("sha256")
            or row.get("bytes") != expected.get("bytes")
        ):
            problems.append(f"host-packet:file:{name}:local-binding")

    expected_packet_source_artifacts = sorted(
        (
            {
                "path": (
                    "MISSION_STATE.json"
                    if name == "MISSION_STATE.json"
                    else f"{EXPERIMENT_REL}/{name}"
                ),
                "sha256": (
                    files[name].get("sha256")
                    if isinstance(files.get(name), Mapping)
                    else None
                ),
                "bytes": (
                    files[name].get("bytes")
                    if isinstance(files.get(name), Mapping)
                    else None
                ),
                "git_blob_oid": (
                    expected_file_bindings[name].get("git_blob_oid")
                    if isinstance(expected_file_bindings.get(name), Mapping)
                    else None
                ),
                "git_mode": (
                    expected_file_bindings[name].get("git_mode")
                    if isinstance(expected_file_bindings.get(name), Mapping)
                    else None
                ),
            }
            for name in HOST_PACKET_FILE_NAMES
        ),
        key=lambda row: str(row["path"]),
    )

    packet_digest = packet_binding.get("sha256") if isinstance(packet_binding, Mapping) else None
    packet_bytes = packet_binding.get("bytes") if isinstance(packet_binding, Mapping) else None
    expected_preparation_fields = {
        "schema",
        "verdict",
        "started_at_utc",
        "finished_at_utc",
        "host",
        "problem_count",
        "problems",
        "packet_manifest_sha256",
        "publication_authority",
        "packet",
        "controller",
        "repositories",
        "compose",
        "storage",
        "forbidden_paths",
        "actions",
        "invocation",
        "receipt_payload_sha256",
    }
    if not isinstance(preparation_receipt, dict) or set(preparation_receipt) != (
        expected_preparation_fields
    ):
        problems.append("host-preparation:field-set")
        preparation_receipt = {}
    if preparation_receipt.get("schema") != EXPECTED_HOST_PREPARATION_SCHEMA:
        problems.append("host-preparation:schema")
    if preparation_receipt.get("verdict") != EXPECTED_HOST_PREPARATION_VERDICT:
        problems.append("host-preparation:verdict")
    if (
        preparation_receipt.get("problem_count") != 0
        or preparation_receipt.get("problems") != []
    ):
        problems.append("host-preparation:problem-metadata")
    if preparation_receipt.get("packet_manifest_sha256") != packet_digest:
        problems.append("host-preparation:packet-manifest-sha256")
    problems.extend(
        validate_publication_authority(
            preparation_receipt.get("publication_authority"),
            expected_commit=source_commit if isinstance(source_commit, str) else None,
            expected_artifacts=expected_packet_source_artifacts,
            label="host-preparation:publication-authority",
        )
    )
    receipt_payload = dict(preparation_receipt)
    claimed_payload_sha = receipt_payload.pop("receipt_payload_sha256", None)
    if not _valid_sha256(claimed_payload_sha) or claimed_payload_sha != (
        _canonical_json_sha256(receipt_payload)
    ):
        problems.append("host-preparation:receipt-payload-sha256")

    packet = preparation_receipt.get("packet")
    if not isinstance(packet, dict) or set(packet) != {
        "schema",
        "source_commit",
        "manifest",
        "independently_supplied_manifest_sha256",
        "files",
    }:
        problems.append("host-preparation:packet-field-set")
        packet = {}
    if (
        packet.get("schema") != EXPECTED_HOST_PACKET_SCHEMA
        or packet.get("source_commit") != source_commit
        or packet.get("independently_supplied_manifest_sha256") != packet_digest
    ):
        problems.append("host-preparation:packet-contract")
    manifest_claim = packet.get("manifest")
    if (
        not isinstance(manifest_claim, dict)
        or set(manifest_claim) != {"path", "sha256", "bytes", "mode"}
        or manifest_claim.get("sha256") != packet_digest
        or manifest_claim.get("bytes") != packet_bytes
        or manifest_claim.get("mode") != 0o644
    ):
        problems.append("host-preparation:packet-manifest-binding")
    observed_files = packet.get("files")
    if not isinstance(observed_files, dict) or set(observed_files) != set(HOST_PACKET_FILE_NAMES):
        problems.append("host-preparation:packet-file-set")
        observed_files = {}
    for name in HOST_PACKET_FILE_NAMES:
        observed = observed_files.get(name)
        claimed = files.get(name)
        if (
            not isinstance(observed, dict)
            or set(observed) != {"path", "sha256", "bytes", "mode"}
            or not isinstance(observed.get("path"), str)
            or Path(observed["path"]).name != name
            or not isinstance(claimed, dict)
            or any(observed.get(field) != claimed.get(field) for field in ("sha256", "bytes", "mode"))
        ):
            problems.append(f"host-preparation:packet-file:{name}:binding")
    if preparation_receipt.get("controller") != observed_files.get("prepare_host135.py"):
        problems.append("host-preparation:controller-binding")
    return sorted(set(problems))


def dataset_contract_problems() -> list[str]:
    """Reject drift in the generator's independently frozen dataset contract."""

    problems: list[str] = []
    expected_archive_names = {
        "v1.0-trainval_meta.tgz",
        *(f"v1.0-trainval{index:02d}_blobs.tgz" for index in range(1, 11)),
        "nuScenes-map-expansion-v1.3.zip",
    }
    if set(EXPECTED_DATASET_ARCHIVES) != expected_archive_names:
        problems.append("dataset-contract:archive-set")
    if len(EXPECTED_DATASET_ARCHIVES) != 12:
        problems.append("dataset-contract:archive-count")
    if sum(row[1] for row in EXPECTED_DATASET_ARCHIVES.values()) != (
        EXPECTED_DATASET_ARCHIVE_TOTAL_BYTES
    ):
        problems.append("dataset-contract:archive-total-bytes")
    if any(
        not _valid_sha256(digest) or type(byte_count) is not int or byte_count <= 0
        for digest, byte_count in EXPECTED_DATASET_ARCHIVES.values()
    ):
        problems.append("dataset-contract:archive-values")
    if (
        len(EXPECTED_DATASET_METADATA_FILES) != 13
        or len(set(EXPECTED_DATASET_METADATA_FILES)) != 13
    ):
        problems.append("dataset-contract:metadata-set")
    if len(EXPECTED_DATASET_MAP_ANCHORS) != 5 or len(set(EXPECTED_DATASET_MAP_ANCHORS)) != 5:
        problems.append("dataset-contract:map-set")
    if set(EXPECTED_DATASET_MAP_DIRECTORIES) != {"basemap", "expansion", "prediction"} or {
        name: len(files) for name, files in EXPECTED_DATASET_MAP_DIRECTORIES.items()
    } != {"basemap": 4, "expansion": 4, "prediction": 1}:
        problems.append("dataset-contract:map-directory-set")
    names = (
        *EXPECTED_DATASET_ARCHIVES,
        *EXPECTED_DATASET_METADATA_FILES,
        *EXPECTED_DATASET_MAP_ANCHORS,
        *(
            name
            for files in EXPECTED_DATASET_MAP_DIRECTORIES.values()
            for name in files
        ),
        *EXPECTED_DATASET_MAP_DIRECTORIES,
    )
    if any(Path(name).name != name or name in {"", ".", ".."} for name in names):
        problems.append("dataset-contract:unsafe-name")
    actual_contract_sha256 = _canonical_json_sha256(canonical_dataset_contract_payload())
    if actual_contract_sha256 != EXPECTED_DATASET_CONTRACT_SHA256:
        problems.append("dataset-contract:sha256")
    return problems


def iter28_dataset_proof_problems(repo_root: Path) -> list[str]:
    """Replay the committed Iter28 archive claims behind the hardcoded contract."""

    problems: list[str] = []
    proof_root = Path(repo_root) / ITER28_DATASET_PROOF_DIRECTORY_REL
    if proof_root.is_symlink() or not proof_root.is_dir():
        return ["dataset-proof:directory"]
    expected_names = {
        f"{name}.json"
        for name in EXPECTED_DATASET_ARCHIVES
        if name != MAP_EXPANSION_ARCHIVE_NAME
    }
    try:
        observed_names = {path.name for path in proof_root.iterdir()}
    except OSError as error:
        return [f"dataset-proof:directory:{type(error).__name__}"]
    if observed_names != expected_names:
        problems.append("dataset-proof:file-set")
    for name, (expected_digest, expected_bytes) in EXPECTED_DATASET_ARCHIVES.items():
        if name == MAP_EXPANSION_ARCHIVE_NAME:
            continue
        path = proof_root / f"{name}.json"
        if path.is_symlink() or not path.is_file():
            problems.append(f"dataset-proof:{name}:file")
            continue
        try:
            proof = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            problems.append(f"dataset-proof:{name}:json:{type(error).__name__}")
            continue
        archive = proof.get("archive") if isinstance(proof, dict) else None
        destination = proof.get("destination") if isinstance(proof, dict) else None
        if not isinstance(archive, dict):
            problems.append(f"dataset-proof:{name}:archive")
            continue
        expected_archive = {
            "canonical_name": name,
            "remote_path": f"{EXPECTED_DATASET_ARCHIVE_ROOT}/{name}",
            "remote_sha256": expected_digest,
            "remote_size_bytes": expected_bytes,
        }
        for field, expected in expected_archive.items():
            if archive.get(field) != expected:
                problems.append(f"dataset-proof:{name}:{field}")
        if not isinstance(destination, dict) or destination.get("dest_root") != (
            EXPECTED_DATASET_ROOT
        ):
            problems.append(f"dataset-proof:{name}:destination")
        if not isinstance(proof, dict) or proof.get("experiment") != (
            "iter28_nuscenes_trainval_staging"
        ):
            problems.append(f"dataset-proof:{name}:experiment")
        expected_verify_rows = {
            f"ITER28_REMOTE_SIZE {expected_bytes}",
            f"ITER28_REMOTE_SHA256 {expected_digest}",
        }
        verify_stdout = proof.get("verify_stdout") if isinstance(proof, dict) else None
        if not isinstance(verify_stdout, str) or set(verify_stdout.splitlines()) != (
            expected_verify_rows
        ):
            problems.append(f"dataset-proof:{name}:verify-stdout")

    # The map-expansion archive's byte proof is the committed iteration-47 staging receipt.
    expansion_digest, expansion_bytes = EXPECTED_DATASET_ARCHIVES[MAP_EXPANSION_ARCHIVE_NAME]
    expansion_path = Path(repo_root) / ITER47_MAP_EXPANSION_PROOF_REL
    if expansion_path.is_symlink() or not expansion_path.is_file():
        problems.append(f"dataset-proof:{MAP_EXPANSION_ARCHIVE_NAME}:file")
    else:
        try:
            expansion_proof = json.loads(expansion_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            problems.append(
                f"dataset-proof:{MAP_EXPANSION_ARCHIVE_NAME}:json:{type(error).__name__}"
            )
            expansion_proof = None
        if expansion_proof is not None:
            expansion_archive = (
                expansion_proof.get("archive") if isinstance(expansion_proof, dict) else None
            )
            expected_expansion_archive = {
                "canonical_name": MAP_EXPANSION_ARCHIVE_NAME,
                "remote_path": (
                    f"{EXPECTED_DATASET_ARCHIVE_ROOT}/{MAP_EXPANSION_ARCHIVE_NAME}"
                ),
                "bytes": expansion_bytes,
                "sha256": expansion_digest,
            }
            if expansion_archive != expected_expansion_archive:
                problems.append(f"dataset-proof:{MAP_EXPANSION_ARCHIVE_NAME}:archive")
            if not isinstance(expansion_proof, dict) or expansion_proof.get(
                "experiment"
            ) != "iter47_map_staging_and_off_completion":
                problems.append(f"dataset-proof:{MAP_EXPANSION_ARCHIVE_NAME}:experiment")
    return sorted(set(problems))


def _dataset_receipt_payload_sha256(receipt: Mapping[str, Any]) -> str:
    payload = dict(receipt)
    payload.pop("receipt_payload_sha256", None)
    return _canonical_json_sha256(payload)


def _validate_dataset_file_receipt(
    label: str,
    receipt: Any,
    *,
    expected_path: str,
    expected_sha256: str | None = None,
    expected_bytes: int | None = None,
) -> list[str]:
    problems: list[str] = []
    if not isinstance(receipt, dict):
        return [f"environment:dataset:{label}:missing"]
    if set(receipt) != {"path", "sha256", "bytes"}:
        problems.append(f"environment:dataset:{label}:field-set")
    if receipt.get("path") != expected_path:
        problems.append(f"environment:dataset:{label}:path")
    digest = receipt.get("sha256")
    if not _valid_sha256(digest):
        problems.append(f"environment:dataset:{label}:sha256")
    if expected_sha256 is not None and digest != expected_sha256:
        problems.append(f"environment:dataset:{label}:expected-sha256")
    byte_count = receipt.get("bytes")
    if type(byte_count) is not int or byte_count <= 0:
        problems.append(f"environment:dataset:{label}:bytes")
    if expected_bytes is not None and byte_count != expected_bytes:
        problems.append(f"environment:dataset:{label}:expected-bytes")
    return problems


def validate_dataset_receipt(receipt: Mapping[str, Any] | None) -> list[str]:
    """Validate a dataset receipt against constants, never against receipt-declared topology."""

    if receipt is None:
        return ["environment:dataset:missing"]
    problems = dataset_contract_problems()
    expected_fields = {
        "schema",
        "contract_sha256",
        "proof_basis",
        "identity",
        "archives",
        "metadata_json",
        "map_anchors",
        "receipt_payload_sha256",
    }
    if set(receipt) != expected_fields:
        problems.append("environment:dataset:field-set")
    if receipt.get("schema") != EXPECTED_DATASET_SCHEMA:
        problems.append("environment:dataset:schema")
    if receipt.get("contract_sha256") != EXPECTED_DATASET_CONTRACT_SHA256:
        problems.append("environment:dataset:contract-sha256")
    if receipt.get("proof_basis") != EXPECTED_DATASET_PROOF_BASIS:
        problems.append("environment:dataset:proof-basis")

    identity = receipt.get("identity")
    expected_identity_fields = {
        "dataset_root",
        "dataset_realpath",
        "dataset_is_symlink",
        "dataset_version",
        "archive_root",
        "archive_realpath",
        "archive_is_symlink",
        "metadata_root",
        "metadata_realpath",
        "metadata_is_symlink",
        "map_root",
        "map_realpath",
        "map_is_symlink",
        "mount_target",
        "mount_source",
        "mount_fstype",
        "mount_uuid",
        "dataset_st_dev",
        "mount_st_dev",
        "root_st_dev",
    }
    if not isinstance(identity, dict) or set(identity) != expected_identity_fields:
        problems.append("environment:dataset:identity-field-set")
    else:
        expected_values = {
            "dataset_root": EXPECTED_DATASET_ROOT,
            "dataset_realpath": EXPECTED_DATASET_ROOT,
            "dataset_is_symlink": False,
            "dataset_version": EXPECTED_DATASET_VERSION,
            "archive_root": EXPECTED_DATASET_ARCHIVE_ROOT,
            "archive_realpath": EXPECTED_DATASET_ARCHIVE_ROOT,
            "archive_is_symlink": False,
            "metadata_root": EXPECTED_DATASET_METADATA_ROOT,
            "metadata_realpath": EXPECTED_DATASET_METADATA_ROOT,
            "metadata_is_symlink": False,
            "map_root": EXPECTED_DATASET_MAP_ROOT,
            "map_realpath": EXPECTED_DATASET_MAP_ROOT,
            "map_is_symlink": False,
            **EXPECTED_DATASET_MOUNT,
        }
        for field, expected in expected_values.items():
            actual = identity.get(field)
            if actual != expected or (isinstance(expected, bool) and type(actual) is not bool):
                problems.append(f"environment:dataset:identity:{field}")
        dataset_device = identity.get("dataset_st_dev")
        mount_device = identity.get("mount_st_dev")
        root_device = identity.get("root_st_dev")
        if (
            type(dataset_device) is not int
            or type(mount_device) is not int
            or type(root_device) is not int
            or min(dataset_device, mount_device, root_device) < 0
            or dataset_device != mount_device
            or dataset_device == root_device
        ):
            problems.append("environment:dataset:device-identity")

    archives = receipt.get("archives")
    if not isinstance(archives, dict) or set(archives) != set(EXPECTED_DATASET_ARCHIVES):
        problems.append("environment:dataset:archive-set")
        archives = archives if isinstance(archives, dict) else {}
    for name, (digest, byte_count) in EXPECTED_DATASET_ARCHIVES.items():
        problems.extend(
            _validate_dataset_file_receipt(
                f"archive:{name}",
                archives.get(name),
                expected_path=f"{EXPECTED_DATASET_ARCHIVE_ROOT}/{name}",
                expected_sha256=digest,
                expected_bytes=byte_count,
            )
        )

    metadata = receipt.get("metadata_json")
    if not isinstance(metadata, dict) or set(metadata) != set(EXPECTED_DATASET_METADATA_FILES):
        problems.append("environment:dataset:metadata-set")
        metadata = metadata if isinstance(metadata, dict) else {}
    for name in EXPECTED_DATASET_METADATA_FILES:
        problems.extend(
            _validate_dataset_file_receipt(
                f"metadata:{name}",
                metadata.get(name),
                expected_path=f"{EXPECTED_DATASET_METADATA_ROOT}/{name}",
            )
        )

    maps = receipt.get("map_anchors")
    if not isinstance(maps, dict) or set(maps) != set(EXPECTED_DATASET_MAP_ANCHORS):
        problems.append("environment:dataset:map-set")
        maps = maps if isinstance(maps, dict) else {}
    for name in EXPECTED_DATASET_MAP_ANCHORS:
        problems.extend(
            _validate_dataset_file_receipt(
                f"map:{name}",
                maps.get(name),
                expected_path=f"{EXPECTED_DATASET_MAP_ROOT}/{name}",
            )
        )

    payload_sha256 = receipt.get("receipt_payload_sha256")
    if not _valid_sha256(payload_sha256) or payload_sha256 != (
        _dataset_receipt_payload_sha256(receipt)
    ):
        problems.append("environment:dataset:receipt-payload-sha256")
    return sorted(set(problems))


def _validate_remote_file(
    name: str,
    receipt: Any,
    *,
    expected_path: str | None = None,
    expected_sha256: str | None = None,
    expected_bytes: int | None = None,
) -> list[str]:
    problems: list[str] = []
    if not isinstance(receipt, dict):
        return [f"environment:remote-file:{name}:missing"]
    path = receipt.get("path")
    if not isinstance(path, str) or not path.startswith("/opt/sentinel-stack/"):
        problems.append(f"environment:remote-file:{name}:path")
    if expected_path is not None and path != expected_path:
        problems.append(f"environment:remote-file:{name}:expected-path")
    digest = receipt.get("sha256")
    if not _valid_sha256(digest):
        problems.append(f"environment:remote-file:{name}:sha256")
    if expected_sha256 is not None and digest != expected_sha256:
        problems.append(f"environment:remote-file:{name}:expected-sha256")
    size = receipt.get("bytes")
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        problems.append(f"environment:remote-file:{name}:bytes")
    if expected_bytes is not None and size != expected_bytes:
        problems.append(f"environment:remote-file:{name}:expected-bytes")
    return problems


def validate_environment_receipt(
    receipt: Mapping[str, Any] | None,
    bound_hashes: Mapping[str, Mapping[str, Any]],
    *,
    expected_host_preparation: Mapping[str, Any] | None = None,
    expected_host_authority_artifacts: Sequence[Mapping[str, Any]] | None = None,
) -> list[str]:
    if receipt is None:
        return ["environment:receipt-missing"]
    problems: list[str] = []
    expected_top_level_fields = {
        "schema",
        "verdict",
        "captured_at_utc",
        "capture_started_at_utc",
        "host",
        "problem_count",
        "problems",
        "interpreter",
        "invocation",
        "host_preparation",
        "host_publication_authority",
        "docker_runtime",
        "runtime_snapshots",
        "gpu",
        "box",
        "storage",
        "storage_devices",
        "dataset",
        "repositories",
        "remote_files",
        "container_images",
    }
    if set(receipt) != expected_top_level_fields:
        problems.append("environment:field-set")
    if receipt.get("schema") != EXPECTED_ENV_SCHEMA:
        problems.append("environment:schema")
    if receipt.get("verdict") != EXPECTED_ENV_VERDICT:
        problems.append("environment:verdict")
    if receipt.get("problem_count") != 0 or receipt.get("problems") != []:
        problems.append("environment:problem-metadata")
    captured = _parse_canonical_utc(receipt.get("captured_at_utc"))
    if captured is None:
        problems.append("environment:captured-at")
    capture_started = _parse_canonical_utc(receipt.get("capture_started_at_utc"))
    if capture_started is None or captured is None or capture_started > captured:
        problems.append("environment:capture-started-at")
    if receipt.get("host") != EXPECTED_HOST:
        problems.append("environment:host")

    interpreter = receipt.get("interpreter")
    expected_interpreter_fields = {
        "invocation_path",
        "physical_path",
        "realpath",
        "sha256",
        "bytes",
        "version",
        "implementation",
    }
    if not isinstance(interpreter, dict) or set(interpreter) != expected_interpreter_fields:
        problems.append("environment:interpreter-field-set")
    else:
        for field in ("invocation_path", "physical_path", "realpath"):
            value = interpreter.get(field)
            if not isinstance(value, str) or not Path(value).is_absolute():
                problems.append(f"environment:interpreter:{field}")
        if interpreter.get("physical_path") != interpreter.get("realpath"):
            problems.append("environment:interpreter:realpath-drift")
        if not _valid_sha256(interpreter.get("sha256")):
            problems.append("environment:interpreter:sha256")
        if type(interpreter.get("bytes")) is not int or interpreter["bytes"] <= 0:
            problems.append("environment:interpreter:bytes")
        version = interpreter.get("version")
        try:
            version_tuple = tuple(int(part) for part in version.split("."))
        except (AttributeError, ValueError):
            version_tuple = ()
        if len(version_tuple) != 3 or version_tuple < (3, 10, 0):
            problems.append("environment:interpreter:minimum-version")
        if interpreter.get("implementation") != "CPython":
            problems.append("environment:interpreter:implementation")

    invocation = receipt.get("invocation")
    if not isinstance(invocation, dict) or set(invocation) != {
        "sanitized",
        "isolated",
        "environment",
        "argv",
        "canonical_script",
    }:
        problems.append("environment:invocation-field-set")
    else:
        if invocation.get("sanitized") is not True:
            problems.append("environment:invocation:sanitized")
        if invocation.get("isolated") is not True:
            problems.append("environment:invocation:isolated")
        if invocation.get("environment") != EXPECTED_CAPTURE_ENVIRONMENT:
            problems.append("environment:invocation:environment")
        argv = invocation.get("argv")
        if (
            not isinstance(argv, list)
            or len(argv) < 3
            or not isinstance(interpreter, dict)
            or argv[0] != interpreter.get("physical_path")
            or argv[1] != "-I"
            or argv[2] != "/opt/sentinel-stack/iter135/capture_environment135.py"
        ):
            problems.append("environment:invocation:argv")
        if invocation.get("canonical_script") != (
            "/opt/sentinel-stack/iter135/capture_environment135.py"
        ):
            problems.append("environment:invocation:canonical-script")

    host_preparation = receipt.get("host_preparation")
    if not isinstance(host_preparation, dict) or set(host_preparation) != {
        "receipt_file",
        "evidence",
    }:
        problems.append("environment:host-preparation-field-set")
    else:
        preparation_file = host_preparation.get("receipt_file")
        preparation_evidence = host_preparation.get("evidence")
        expected_preparation = bound_hashes.get(HOST_PREPARATION_RECEIPT_REL, {})
        if (
            not isinstance(preparation_file, dict)
            or set(preparation_file) != {"path", "sha256", "bytes"}
            or preparation_file.get("path")
            != "/opt/sentinel-stack/iter135/host_preparation_receipt.json"
            or preparation_file.get("sha256") != expected_preparation.get("sha256")
            or preparation_file.get("bytes") != expected_preparation.get("bytes")
        ):
            problems.append("environment:host-preparation-binding")
        if not isinstance(preparation_evidence, dict):
            problems.append("environment:host-preparation-evidence")
        else:
            if preparation_evidence != expected_host_preparation:
                problems.append("environment:host-preparation-evidence-drift")
            if preparation_evidence.get("schema") != EXPECTED_HOST_PREPARATION_SCHEMA:
                problems.append("environment:host-preparation-schema")
            if preparation_evidence.get("verdict") != EXPECTED_HOST_PREPARATION_VERDICT:
                problems.append("environment:host-preparation-verdict")
            if (
                preparation_evidence.get("problem_count") != 0
                or preparation_evidence.get("problems") != []
            ):
                problems.append("environment:host-preparation-problems")

    expected_host_artifacts = [
        dict(row) for row in (expected_host_authority_artifacts or [])
    ]
    if len(expected_host_artifacts) != 2:
        problems.append("environment:host-publication-authority:artifact-bindings")
    problems.extend(
        validate_publication_authority(
            receipt.get("host_publication_authority"),
            expected_artifacts=expected_host_artifacts,
            label="environment:host-publication-authority",
        )
    )
    problems.extend(validate_docker_runtime_receipt(receipt.get("docker_runtime")))

    dataset = receipt.get("dataset")
    problems.extend(validate_dataset_receipt(dataset if isinstance(dataset, dict) else None))

    gpu = receipt.get("gpu")
    expected_gpu_fields = {
        "model",
        "count",
        "uuid",
        "driver_version",
        "memory_total_mib",
    }
    if not isinstance(gpu, dict) or set(gpu) != expected_gpu_fields:
        problems.append("environment:gpu-field-set")
    else:
        if gpu.get("model") != EXPECTED_GPU_IDENTITY["model"] or gpu.get("count") != 1:
            problems.append("environment:gpu")
        if (
            not isinstance(gpu.get("uuid"), str)
            or not _GPU_UUID_RE.fullmatch(gpu["uuid"])
            or gpu.get("uuid") != EXPECTED_GPU_IDENTITY["uuid"]
        ):
            problems.append("environment:gpu-uuid")
        if gpu.get("driver_version") != EXPECTED_GPU_IDENTITY["driver_version"]:
            problems.append("environment:gpu-driver")
        if gpu.get("memory_total_mib") != EXPECTED_GPU_IDENTITY["memory_total_mib"]:
            problems.append("environment:gpu-memory")
    box = receipt.get("box")
    expected_box = {
        "idle": True,
        "all_containers": 0,
        "gpu_compute_processes": 0,
        "known_evaluation_processes": 0,
    }
    if not isinstance(box, dict) or box != expected_box:
        problems.append("environment:box-idle")
    runtime_snapshots = receipt.get("runtime_snapshots")
    expected_runtime_snapshots = {
        "before_dataset_hashing": {"gpu": EXPECTED_GPU_IDENTITY, "box": expected_box},
        "after_dataset_hashing": {"gpu": EXPECTED_GPU_IDENTITY, "box": expected_box},
    }
    if runtime_snapshots != expected_runtime_snapshots:
        problems.append("environment:runtime-snapshots")

    storage = receipt.get("storage")
    if not isinstance(storage, dict):
        problems.append("environment:storage")
    else:
        expected_storage_keys = {
            "remote_output_free_bytes",
            "projected_output_bytes",
            "minimum_reserve_bytes",
            "local_free_bytes",
            "remote_output_free_gib",
            "projected_output_gib",
            "minimum_reserve_gib",
            "local_free_gib",
            *EXPECTED_STORAGE_IDENTITY,
        }
        if set(storage) != expected_storage_keys:
            problems.append("environment:storage-field-set")
        remote_free_bytes = storage.get("remote_output_free_bytes")
        projected_bytes = storage.get("projected_output_bytes")
        reserve_bytes = storage.get("minimum_reserve_bytes")
        local_free_bytes = storage.get("local_free_bytes")
        remote_free = storage.get("remote_output_free_gib")
        projected = storage.get("projected_output_gib")
        reserve = storage.get("minimum_reserve_gib")
        local_free = storage.get("local_free_gib")
        for field, expected in EXPECTED_STORAGE_IDENTITY.items():
            actual = storage.get(field)
            if actual != expected or (isinstance(expected, bool) and type(actual) is not bool):
                problems.append(f"environment:storage-identity:{field}")
        numeric = all(
            isinstance(value, (int, float)) and not isinstance(value, bool)
            for value in (remote_free, projected, reserve, local_free)
        )
        if not numeric:
            problems.append("environment:storage-values")
        else:
            byte_values = (remote_free_bytes, projected_bytes, reserve_bytes, local_free_bytes)
            byte_values_valid = all(type(value) is int and value >= 0 for value in byte_values)
            if not byte_values_valid:
                problems.append("environment:storage-byte-values")
            if type(remote_free_bytes) is int and remote_free != remote_free_bytes / 1024**3:
                problems.append("environment:remote-free-unit-drift")
            if type(projected_bytes) is int and projected != projected_bytes / 1024**3:
                problems.append("environment:projected-output-unit-drift")
            if type(reserve_bytes) is int and reserve != reserve_bytes / 1024**3:
                problems.append("environment:reserve-unit-drift")
            if type(local_free_bytes) is int and local_free != local_free_bytes / 1024**3:
                problems.append("environment:local-free-unit-drift")
            if byte_values_valid:
                if remote_free_bytes < MINIMUM_REMOTE_FREE_BYTES:
                    problems.append("environment:remote-free")
                if projected_bytes != PROJECTED_OUTPUT_BYTES:
                    problems.append("environment:projected-output")
                if (
                    reserve_bytes != MINIMUM_RESERVE_BYTES
                    or remote_free_bytes - projected_bytes < reserve_bytes
                ):
                    problems.append("environment:projected-reserve")
                if local_free_bytes < MINIMUM_LOCAL_FREE_BYTES:
                    problems.append("environment:local-free")

    storage_devices = receipt.get("storage_devices")
    expected_device_fields = {"filesystem_st_dev", "mount_st_dev", "root_st_dev"}
    if not isinstance(storage_devices, dict) or set(storage_devices) != expected_device_fields:
        problems.append("environment:storage-device-field-set")
    else:
        filesystem_device = storage_devices.get("filesystem_st_dev")
        mount_device = storage_devices.get("mount_st_dev")
        root_device = storage_devices.get("root_st_dev")
        if (
            type(filesystem_device) is not int
            or type(mount_device) is not int
            or type(root_device) is not int
            or min(filesystem_device, mount_device, root_device) < 0
            or filesystem_device != mount_device
            or filesystem_device == root_device
        ):
            problems.append("environment:storage-device-identity")
        dataset_identity = dataset.get("identity") if isinstance(dataset, dict) else None
        if not isinstance(dataset_identity, dict) or (
            dataset_identity.get("dataset_st_dev") != filesystem_device
            or dataset_identity.get("mount_st_dev") != mount_device
            or dataset_identity.get("root_st_dev") != root_device
        ):
            problems.append("environment:dataset:storage-device-link")

    remote_files = receipt.get("remote_files")
    if not isinstance(remote_files, dict):
        problems.append("environment:remote-files")
        remote_files = {}
    if set(remote_files) != set(EXPECTED_REMOTE_FILES):
        problems.append("environment:remote-file-set")
    for role, (path, digest, byte_count) in EXPECTED_REMOTE_FILES.items():
        problems.extend(
            _validate_remote_file(
                role,
                remote_files.get(role),
                expected_path=path,
                expected_sha256=digest,
                expected_bytes=byte_count,
            )
        )
        row = remote_files.get(role)
        expected_fields = (
            {"path", "sha256", "bytes", "source_sha256", "patcher_sha256"}
            if role == "compose_script"
            else {"path", "sha256", "bytes"}
        )
        if isinstance(row, dict) and set(row) != expected_fields:
            problems.append(f"environment:remote-file:{role}:field-set")

    compose = remote_files.get("compose_script")
    if isinstance(compose, dict):
        if compose.get("source_sha256") != EXPECTED_COMPOSE_INPUT_SHA256:
            problems.append("environment:compose-source-sha256")
        expected_patcher = bound_hashes.get("patch_compose_dose_env.py", {}).get("sha256")
        if compose.get("patcher_sha256") != expected_patcher:
            problems.append("environment:compose-patcher-sha256")
        if compose.get("sha256") == compose.get("source_sha256"):
            problems.append("environment:compose-not-patched")
        if compose.get("sha256") != EXPECTED_COMPOSE_OUTPUT_SHA256:
            problems.append("environment:compose-output-sha256")

    repositories = receipt.get("repositories")
    if not isinstance(repositories, dict):
        problems.append("environment:repositories")
        repositories = {}
    if set(repositories) != set(EXPECTED_REPOSITORIES):
        problems.append("environment:repository-set")
    repository_fields = {
        "path",
        "head",
        "staged_paths",
        "dirty_tracked_paths",
        "required_untracked_paths",
    }
    for repo_id, expected in EXPECTED_REPOSITORIES.items():
        repository = repositories.get(repo_id)
        if not isinstance(repository, dict):
            problems.append(f"environment:repository:{repo_id}:missing")
            continue
        if set(repository) != repository_fields:
            problems.append(f"environment:repository:{repo_id}:field-set")
        for field in repository_fields:
            if repository.get(field) != expected[field]:
                problems.append(f"environment:repository:{repo_id}:{field}")

    observed_untracked = {
        (repo_id, path)
        for repo_id, repository in repositories.items()
        if isinstance(repository, dict)
        for path in repository.get("required_untracked_paths", [])
        if isinstance(path, str)
    }
    if observed_untracked != set(EXPECTED_REQUIRED_UNTRACKED_BINDINGS):
        problems.append("environment:required-untracked-set")
    for identity, role in EXPECTED_REQUIRED_UNTRACKED_BINDINGS.items():
        repo_id, relative_path = identity
        repository = repositories.get(repo_id)
        remote_file = remote_files.get(role)
        if not isinstance(repository, dict) or not isinstance(remote_file, dict):
            problems.append(f"environment:required-untracked-binding:{repo_id}:{relative_path}")
            continue
        expected_path = f"{repository.get('path')}/{relative_path}"
        if remote_file.get("path") != expected_path:
            problems.append(f"environment:required-untracked-binding:{repo_id}:{relative_path}")

    images = receipt.get("container_images")
    if not isinstance(images, dict):
        problems.append("environment:container-images")
    else:
        if set(images) != set(EXPECTED_IMAGE_IDS):
            problems.append("environment:container-image-set")
        for name, expected_id in EXPECTED_IMAGE_IDS.items():
            image = images.get(name)
            if not isinstance(image, dict):
                problems.append(f"environment:image:{name}:missing")
                continue
            if set(image) != {"image_id", "repo_digests"}:
                problems.append(f"environment:image:{name}:field-set")
            image_id = image.get("image_id")
            if not isinstance(image_id, str) or not _IMAGE_ID_RE.fullmatch(image_id):
                problems.append(f"environment:image:{name}:id-format")
            if image_id != expected_id:
                problems.append(f"environment:image:{name}:id-drift")
            repo_digests = image.get("repo_digests")
            if not isinstance(repo_digests, list) or any(
                not isinstance(x, str) for x in repo_digests
            ):
                problems.append(f"environment:image:{name}:repo-digests")
            elif repo_digests != sorted(set(repo_digests)) or any(
                not re.fullmatch(r"[^@\s]+@sha256:[0-9a-f]{64}", digest) for digest in repo_digests
            ):
                problems.append(f"environment:image:{name}:repo-digest-values")
    return problems


def validate_smoke_receipt(
    receipt: Mapping[str, Any] | None,
    *,
    experiment_dir: Path,
    schedule: Mapping[str, Any] | None,
    bound_hashes: Mapping[str, Mapping[str, Any]],
    environment: Mapping[str, Any] | None,
) -> tuple[list[str], list[Path]]:
    if receipt is None:
        return ["smoke:receipt-missing"], []
    problems: list[str] = []
    artifact_paths: list[Path] = []
    if receipt.get("schema") != EXPECTED_SMOKE_SCHEMA:
        problems.append("smoke:schema")
    if receipt.get("verdict") != EXPECTED_SMOKE_VERDICT:
        problems.append("smoke:verdict")
    if receipt.get("problem_count") != 0 or receipt.get("problems") != []:
        problems.append("smoke:problem-metadata")
    if receipt.get("nonanalytic") is not True or receipt.get("analytic_episode_count") != 0:
        problems.append("smoke:nonanalytic-boundary")
    gpu_seconds = receipt.get("gpu_seconds")
    if type(gpu_seconds) is not int or gpu_seconds < 0 or gpu_seconds >= 110 * 60 * 60:
        problems.append("smoke:gpu-seconds")
    if receipt.get("schedule_sha256") != bound_hashes.get("dose_schedules.json", {}).get("sha256"):
        problems.append("smoke:schedule-sha256")
    if receipt.get("blind_patch_sha256") != bound_hashes.get("server_patch_blind_dose.py", {}).get(
        "sha256"
    ):
        problems.append("smoke:blind-patch-sha256")

    remote_files = environment.get("remote_files") if isinstance(environment, dict) else None
    if not isinstance(remote_files, dict):
        problems.append("smoke:environment-link")
        remote_files = {}
    compose = remote_files.get("compose_script")
    if receipt.get("remote_compose_sha256") != (
        compose.get("sha256") if isinstance(compose, dict) else None
    ):
        problems.append("smoke:compose-sha256")
    forwarded = receipt.get("model_environment_forwarded")
    if not isinstance(forwarded, dict) or set(forwarded) != set(REQUIRED_MODEL_ENV):
        problems.append("smoke:model-environment-set")
    elif any(forwarded[name] is not True for name in REQUIRED_MODEL_ENV):
        problems.append("smoke:model-environment-forwarding")
    if receipt.get("pair_present_on_every_frame") is not True:
        problems.append("smoke:pair-counter-fix")

    schedule_rows: dict[str, Any] | None = None
    if isinstance(schedule, dict) and isinstance(schedule.get("schedules"), dict):
        raw_schedules = schedule["schedules"]
        if set(raw_schedules) == set(BLIND_ARMS) and all(
            isinstance(raw_schedules.get(dose), dict) for dose in BLIND_ARMS
        ):
            schedule_rows = {
                f"{dose}/{target}": row
                for dose in BLIND_ARMS
                for target, row in raw_schedules[dose].items()
            }
        else:
            schedule_rows = dict(raw_schedules)
    dose_results = receipt.get("dose_results")
    if not isinstance(dose_results, dict) or set(dose_results) != set(BLIND_ARMS):
        problems.append("smoke:dose-result-set")
        dose_results = {}
    for dose in BLIND_ARMS:
        result = dose_results.get(dose)
        if not isinstance(result, dict):
            problems.append(f"smoke:dose:{dose}:missing")
            continue
        schedule_id = result.get("schedule_id")
        row = schedule_rows.get(schedule_id) if isinstance(schedule_rows, dict) else None
        if not isinstance(schedule_id, str) or not isinstance(row, dict):
            problems.append(f"smoke:dose:{dose}:schedule-id")
            continue
        if row.get("dose_id") != dose:
            problems.append(f"smoke:dose:{dose}:schedule-dose")
        expected_frames = row.get("brake_frames")
        if result.get("expected_brake_frames") != expected_frames:
            problems.append(f"smoke:dose:{dose}:expected-frames")
        if result.get("observed_brake_frames") != expected_frames:
            problems.append(f"smoke:dose:{dose}:observed-frames")
        if result.get("pass_through_exact") is not True:
            problems.append(f"smoke:dose:{dose}:pass-through")
        if result.get("zero_actuator_exact") is not True:
            problems.append(f"smoke:dose:{dose}:actuator")
        if result.get("identity_fields") != ["class", "pair", "run", "frame", "dose"]:
            problems.append(f"smoke:dose:{dose}:identity-fields")
        if result.get("schedule_missing") != 0 or result.get("intervene_errors") != 0:
            problems.append(f"smoke:dose:{dose}:runtime-errors")

    artifacts = receipt.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        problems.append("smoke:artifacts")
    else:
        seen: set[str] = set()
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                problems.append(f"smoke:artifact:{index}:schema")
                continue
            rel = artifact.get("path")
            digest = artifact.get("sha256")
            if (
                not isinstance(rel, str)
                or not rel.startswith("smoke-evidence/")
                or ".." in Path(rel).parts
            ):
                problems.append(f"smoke:artifact:{index}:path")
                continue
            if rel in seen:
                problems.append(f"smoke:artifact:{index}:duplicate")
                continue
            seen.add(rel)
            path = experiment_dir / rel
            artifact_paths.append(path)
            if not path.is_file():
                problems.append(f"smoke:artifact:{index}:missing")
            elif not _valid_sha256(digest) or sha256_file(path) != digest:
                problems.append(f"smoke:artifact:{index}:sha256")
    return problems, artifact_paths


def _load_smoke_validator_api(validator_path: Path):
    module_name = "iter135_smoke_recomputer"
    module = types.ModuleType(module_name)
    module.__file__ = str(validator_path)
    sys.modules[module_name] = module
    try:
        source = validator_path.read_text(encoding="utf-8")
        exec(compile(source, str(validator_path), "exec"), module.__dict__)
        api = (
            module.recompute_smoke_receipt,
            module.canonical_smoke_receipt_bytes,
            module.render_smoke_summary,
            module.validate_smoke_bundle_bytes,
        )
    finally:
        sys.modules.pop(module_name, None)
    return api


def _load_tooling_receipt_validator(verifier_path: Path):
    module_name = "iter135_tooling_receipt_validator"
    module = types.ModuleType(module_name)
    module.__file__ = str(verifier_path)
    sys.modules[module_name] = module
    try:
        source = verifier_path.read_text(encoding="utf-8")
        exec(compile(source, str(verifier_path), "exec"), module.__dict__)
        validator = module.validate_published_receipt_structure
    finally:
        sys.modules.pop(module_name, None)
    return validator


def validate_tooling_receipt(
    receipt: Mapping[str, Any] | None,
    *,
    repo_root: Path,
    verifier_path: Path,
) -> list[str]:
    if receipt is None:
        return ["tooling-verification:receipt-missing"]
    problems: list[str] = []
    if receipt.get("schema") != EXPECTED_TOOLING_SCHEMA:
        problems.append("tooling-verification:schema")
    if receipt.get("verdict") != EXPECTED_TOOLING_VERDICT:
        problems.append("tooling-verification:verdict")
    if receipt.get("problem_count") != 0 or receipt.get("problems") != []:
        problems.append("tooling-verification:problem-metadata")
    if not verifier_path.is_file() or verifier_path.is_symlink():
        problems.append("tooling-verification:verifier-missing")
        return problems
    try:
        validator = _load_tooling_receipt_validator(verifier_path)
        replay_errors = validator(receipt, repo_root=repo_root)
    except Exception as error:  # fail closed on verifier import/probe failure
        problems.append(f"tooling-verification:replay-error:{type(error).__name__}")
    else:
        if not isinstance(replay_errors, list):
            problems.append("tooling-verification:replay-result-schema")
        else:
            problems.extend(
                f"tooling-verification:replay:{index}:{error}"
                for index, error in enumerate(replay_errors)
            )
    return problems


def _load_schedule_validator(generator_path: Path):
    module_name = "iter135_schedule_validator"
    module = types.ModuleType(module_name)
    module.__file__ = str(generator_path)
    sys.modules[module_name] = module
    try:
        source = generator_path.read_text(encoding="utf-8")
        exec(compile(source, str(generator_path), "exec"), module.__dict__)
    finally:
        sys.modules.pop(module_name, None)
    return module.validate_schedule_report


def validate_schedule_artifact(
    schedule: Mapping[str, Any] | None, generator_path: Path
) -> list[str]:
    if schedule is None:
        return ["schedule:missing"]
    problems: list[str] = []
    if not generator_path.is_file():
        return ["schedule:generator-missing"]
    try:
        validator = _load_schedule_validator(generator_path)
        schedule_problems = validator(schedule)
    except Exception as error:  # fail closed across a dynamically loaded preflight tool
        return [f"schedule:validator-error:{type(error).__name__}"]
    if schedule_problems:
        problems.extend(f"schedule:{problem}" for problem in schedule_problems)
    if schedule.get("verdict") != "NESTED_DOSE_SCHEDULES_OK":
        problems.append("schedule:verdict")
    if schedule.get("schedule_count") != 1_600:
        problems.append("schedule:count")
    return problems


def validate_runtime_sources(experiment_dir: Path) -> list[str]:
    problems: list[str] = []
    union = experiment_dir / "server_patch_union_release.py"
    blind = experiment_dir / "server_patch_blind_dose.py"
    if union.is_file() and sha256_file(union) != EXPECTED_UNION_SHA256:
        problems.append("runtime:union-sha256")
    if union.is_file() and blind.is_file():
        union_text = union.read_text(errors="replace")
        blind_text = blind.read_text(errors="replace")
        if not all(token in union_text for token in RISK_TOKENS):
            problems.append("runtime:leak-guard-vacuous")
        leaks = [token for token in RISK_TOKENS if token in blind_text]
        if leaks or "data." in blind_text:
            problems.append(f"runtime:blind-semantic-leak:{','.join(leaks) or 'data.'}")
        actuator = "[[0.0, 0.0] for _ in range(len(base))]"
        if actuator not in union_text or actuator not in blind_text:
            problems.append("runtime:actuator-expression")
    return problems


def validate_consumers(
    experiment_dir: Path, expected_cells: Sequence[Mapping[str, Any]]
) -> list[str]:
    """Require both launch and analysis consumers to encode the amended block order."""

    problems: list[str] = []
    launcher = experiment_dir / "run_dose135.sh"
    if launcher.is_file():
        text = launcher.read_text(errors="replace")
        for marker in ("execution_blocks", "I135BLOCK", "--runs 20"):
            if marker not in text:
                problems.append(f"consumer:launcher-missing:{marker}")
    analyzer_path = experiment_dir / "analyze_dose135.py"
    if analyzer_path.is_file():
        try:
            module_name = "iter135_manifest_analyzer"
            module = types.ModuleType(module_name)
            module.__file__ = str(analyzer_path)
            sys.modules[module_name] = module
            try:
                source = analyzer_path.read_text(encoding="utf-8")
                exec(compile(source, str(analyzer_path), "exec"), module.__dict__)
            finally:
                sys.modules.pop(module_name, None)
            actual = list(module.expected_execution_order())
            expected = [
                (
                    cell["arm_id"],
                    cell["scenario_class"],
                    cell["sequence"],
                    cell["run_index"],
                )
                for cell in expected_cells
            ]
            if actual != expected:
                problems.append("consumer:analyzer-execution-order")
        except Exception as error:  # fail closed on an unusable frozen analyzer
            problems.append(f"consumer:analyzer-import:{type(error).__name__}")
    return problems


def collect_git_provenance(
    repo_root: Path, paths: Sequence[Path], hypothesis_path: Path
) -> dict[str, Any]:
    """Collect committed/clean provenance without converting failures into authorization."""

    problems: list[str] = []

    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=repo_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    rel_paths: list[str] = []
    for path in paths:
        try:
            rel_paths.append(str(path.resolve().relative_to(repo_root.resolve())))
        except ValueError:
            problems.append(f"git:path-outside-repository:{path}")
    rel_paths = sorted(set(rel_paths))
    status = git("status", "--porcelain", "--", *rel_paths) if rel_paths else None
    if status is None or status.returncode != 0:
        problems.append("git:status-failed")
        dirty_lines: list[str] = []
    else:
        dirty_lines = sorted(line for line in status.stdout.splitlines() if line)
        if dirty_lines:
            problems.extend(f"git:dirty:{line}" for line in dirty_lines)

    file_commits: dict[str, str | None] = {}
    for rel in rel_paths:
        tracked = git("ls-files", "--error-unmatch", "--", rel)
        if tracked.returncode != 0:
            problems.append(f"git:untracked:{rel}")
            file_commits[rel] = None
            continue
        latest = git("log", "-1", "--format=%H", "--", rel)
        commit = latest.stdout.strip() if latest.returncode == 0 else ""
        if not commit:
            problems.append(f"git:no-commit:{rel}")
            file_commits[rel] = None
        else:
            file_commits[rel] = commit

    hypothesis_rel = str(hypothesis_path.resolve().relative_to(repo_root.resolve()))
    history = git("log", "--reverse", "--format=%H", "--", hypothesis_rel)
    hypothesis_commits = history.stdout.splitlines() if history.returncode == 0 else []
    if len(hypothesis_commits) < 2:
        problems.append("git:hypothesis-amendment-history")
    for commit in hypothesis_commits:
        names = git("show", "--pretty=format:", "--name-only", commit)
        touched = sorted({line for line in names.stdout.splitlines() if line})
        if names.returncode != 0 or touched != [hypothesis_rel]:
            problems.append(f"git:hypothesis-commit-not-isolated:{commit}")
    latest_hypothesis = hypothesis_commits[-1] if hypothesis_commits else None
    if latest_hypothesis is not None:
        for rel, commit in file_commits.items():
            if rel == hypothesis_rel or commit is None:
                continue
            ancestry = git("merge-base", "--is-ancestor", latest_hypothesis, commit)
            if ancestry.returncode != 0:
                problems.append(f"git:tool-predates-hypothesis:{rel}")

    head = git("rev-parse", "HEAD")
    return {
        "schema": "iter135.git_provenance.v1",
        "verdict": "I135_GIT_PROVENANCE_OK" if not problems else "I135_GIT_PROVENANCE_INCOMPLETE",
        "head": head.stdout.strip() if head.returncode == 0 else None,
        "hypothesis_commits": hypothesis_commits,
        "latest_hypothesis_commit": latest_hypothesis,
        "file_commits": dict(sorted(file_commits.items())),
        "dirty_lines": dirty_lines,
        "problem_count": len(problems),
        "problems": sorted(set(problems)),
    }


def validate_git_provenance(receipt: Mapping[str, Any]) -> list[str]:
    problems = receipt.get("problems")
    if receipt.get("verdict") != "I135_GIT_PROVENANCE_OK":
        return list(problems) if isinstance(problems, list) and problems else ["git:provenance"]
    if receipt.get("problem_count") != 0 or problems != []:
        return ["git:problem-metadata"]
    if not isinstance(receipt.get("head"), str) or not _GIT_OBJECT_RE.fullmatch(receipt["head"]):
        return ["git:head"]
    commits = receipt.get("hypothesis_commits")
    if (
        not isinstance(commits, list)
        or len(commits) < 2
        or not all(isinstance(x, str) and _GIT_OBJECT_RE.fullmatch(x) for x in commits)
    ):
        return ["git:hypothesis-commits"]
    return []


def _source_artifact_receipts(repo_root: Path, problems: list[str]) -> dict[str, dict[str, Any]]:
    receipts: dict[str, dict[str, Any]] = {}
    for name, (rel, expected_sha) in SOURCE_ARTIFACTS.items():
        path = repo_root / rel
        if not path.is_file():
            problems.append(f"missing:source:{name}")
            continue
        receipt = file_receipt(path, rel)
        receipt["expected_sha256"] = expected_sha
        receipt["matches_frozen_sha256"] = receipt["sha256"] == expected_sha
        if not receipt["matches_frozen_sha256"]:
            problems.append(f"source:{name}:sha256")
        receipts[name] = receipt
    return receipts


def build_manifest(
    *,
    repo_root: Path = REPO_ROOT,
    experiment_dir: Path = HERE,
    mission_state_path: Path | None = None,
    host_packet_manifest_path: Path | None = None,
    host_preparation_receipt_path: Path | None = None,
    env_receipt_path: Path | None = None,
    smoke_receipt_path: Path | None = None,
    smoke_summary_path: Path | None = None,
    payload_overrides: Mapping[str, Path] | None = None,
    git_provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a complete or truthfully incomplete manifest from explicit inputs."""

    repo_root = Path(repo_root)
    experiment_dir = Path(experiment_dir)
    mission_state_path = Path(mission_state_path or repo_root / "MISSION_STATE.json")
    host_packet_manifest_path = Path(
        host_packet_manifest_path or experiment_dir / HOST_PACKET_MANIFEST_REL
    )
    host_preparation_receipt_path = Path(
        host_preparation_receipt_path
        or experiment_dir / HOST_PREPARATION_RECEIPT_REL
    )
    env_receipt_path = Path(env_receipt_path or experiment_dir / ENV_RECEIPT_REL)
    smoke_receipt_path = Path(smoke_receipt_path or experiment_dir / SMOKE_RECEIPT_REL)
    smoke_summary_path = Path(smoke_summary_path or experiment_dir / SMOKE_SUMMARY_REL)
    overrides = dict(payload_overrides or {})

    problems: list[str] = []
    missing: list[str] = []
    dataset_generator_problems = [
        *dataset_contract_problems(),
        *iter28_dataset_proof_problems(repo_root),
    ]
    problems.extend(dataset_generator_problems)
    blocks, cells = execution_plan()
    execution_problems = validate_execution_plan(blocks, cells)
    problems.extend(execution_problems)

    mission_state = _load_json(mission_state_path, "MISSION_STATE.json", problems)
    mission_problems = validate_mission_state(mission_state)
    problems.extend(mission_problems)
    mission_phase = (
        mission_state.get("next_program", {}).get("phase")
        if isinstance(mission_state, dict) and isinstance(mission_state.get("next_program"), dict)
        else None
    )
    mission_receipt = (
        file_receipt(mission_state_path, "MISSION_STATE.json")
        if mission_state_path.is_file()
        else None
    )

    bound_files: dict[str, dict[str, Any]] = {}
    bound_paths: list[Path] = []
    for name in REQUIRED_PAYLOAD_NAMES:
        source = Path(overrides.get(name, experiment_dir / name))
        if not source.is_file():
            problems.append(f"missing:payload:{name}")
            missing.append(name)
            continue
        source_rel = f"{EXPERIMENT_REL}/{name}"
        receipt = file_receipt(source, source_rel)
        bound_files[name] = receipt
        bound_paths.append(source)
        if name.endswith(".py"):
            try:
                compile(source.read_text(encoding="utf-8"), str(source), "exec")
            except (OSError, UnicodeDecodeError, SyntaxError) as error:
                problems.append(f"payload:{name}:compile:{type(error).__name__}")

    tooling_receipt_path = experiment_dir / TOOLING_RECEIPT_REL
    tooling_receipt = _load_json(
        tooling_receipt_path,
        TOOLING_RECEIPT_REL,
        problems,
    )
    if tooling_receipt_path.is_file():
        tooling_rel = str(tooling_receipt_path.resolve().relative_to(experiment_dir.resolve()))
        bound_files[tooling_rel] = file_receipt(
            tooling_receipt_path, f"{EXPERIMENT_REL}/{tooling_rel}"
        )
        bound_paths.append(tooling_receipt_path)
    else:
        missing.append(TOOLING_RECEIPT_REL)
    tooling_problems = validate_tooling_receipt(
        tooling_receipt,
        repo_root=repo_root,
        verifier_path=Path(
            overrides.get("verify_tooling135.py", experiment_dir / "verify_tooling135.py")
        ),
    )
    problems.extend(tooling_problems)

    source_problems: list[str] = []
    source_receipts = _source_artifact_receipts(repo_root, source_problems)
    problems.extend(source_problems)

    schedule_path = Path(
        overrides.get("dose_schedules.json", experiment_dir / "dose_schedules.json")
    )
    schedule = _load_json(schedule_path, "dose_schedules.json", problems)
    schedule_problems = validate_schedule_artifact(
        schedule,
        Path(
            overrides.get(
                "generate_nested_dose_schedules.py",
                experiment_dir / "generate_nested_dose_schedules.py",
            )
        ),
    )
    problems.extend(schedule_problems)

    runtime_problems = validate_runtime_sources(experiment_dir)
    consumer_problems = validate_consumers(experiment_dir, cells)
    problems.extend(runtime_problems)
    problems.extend(consumer_problems)

    host_packet_manifest = _load_json(
        host_packet_manifest_path,
        HOST_PACKET_MANIFEST_REL,
        problems,
    )
    if host_packet_manifest_path.is_file():
        packet_rel = str(
            host_packet_manifest_path.resolve().relative_to(experiment_dir.resolve())
        )
        bound_files[packet_rel] = file_receipt(
            host_packet_manifest_path, f"{EXPERIMENT_REL}/{packet_rel}"
        )
        bound_paths.append(host_packet_manifest_path)
    else:
        missing.append(HOST_PACKET_MANIFEST_REL)

    host_preparation_receipt = _load_json(
        host_preparation_receipt_path,
        HOST_PREPARATION_RECEIPT_REL,
        problems,
    )
    if host_preparation_receipt_path.is_file():
        host_rel = str(
            host_preparation_receipt_path.resolve().relative_to(experiment_dir.resolve())
        )
        bound_files[host_rel] = file_receipt(
            host_preparation_receipt_path, f"{EXPERIMENT_REL}/{host_rel}"
        )
        bound_paths.append(host_preparation_receipt_path)
    else:
        missing.append(HOST_PREPARATION_RECEIPT_REL)

    expected_packet_bindings: dict[str, Mapping[str, Any] | None] = {}
    for name in HOST_PACKET_FILE_NAMES:
        binding = bound_files.get(name)
        source_path = Path(overrides.get(name, experiment_dir / name))
        authority_binding = authority_artifact_receipt(
            source_path,
            (
                "MISSION_STATE.json"
                if name == "MISSION_STATE.json"
                else f"{EXPERIMENT_REL}/{name}"
            ),
            git_mode=("100755" if name in HOST_PACKET_EXECUTABLE_FILES else "100644"),
        )
        expected_packet_bindings[name] = (
            {**dict(binding), **dict(authority_binding)}
            if isinstance(binding, Mapping) and isinstance(authority_binding, Mapping)
            else None
        )
    if isinstance(host_packet_manifest, Mapping):
        packet_mission_receipt = git_blob_receipt(
            repo_root,
            host_packet_manifest.get("source_commit"),
            "MISSION_STATE.json",
        )
        if packet_mission_receipt is None:
            problems.append("host-packet:source-mission-state")
        expected_packet_bindings["MISSION_STATE.json"] = packet_mission_receipt
    else:
        expected_packet_bindings["MISSION_STATE.json"] = None
    host_preparation_problems = validate_host_preparation_evidence(
        host_packet_manifest,
        host_preparation_receipt,
        packet_binding=bound_files.get(HOST_PACKET_MANIFEST_REL),
        expected_file_bindings=expected_packet_bindings,
    )
    problems.extend(host_preparation_problems)

    env_receipt = _load_json(env_receipt_path, ENV_RECEIPT_REL, problems)
    if env_receipt_path.is_file():
        env_rel = str(env_receipt_path.resolve().relative_to(experiment_dir.resolve()))
        bound_files[env_rel] = file_receipt(
            env_receipt_path, f"{EXPERIMENT_REL}/{env_rel}"
        )
        bound_paths.append(env_receipt_path)
    else:
        missing.append(ENV_RECEIPT_REL)
    dataset_problems = validate_dataset_receipt(
        env_receipt.get("dataset")
        if isinstance(env_receipt, dict) and isinstance(env_receipt.get("dataset"), dict)
        else None
    )
    expected_host_authority_artifacts = [
        row
        for row in (
            authority_artifact_receipt(
                host_packet_manifest_path,
                f"{EXPERIMENT_REL}/{HOST_PACKET_MANIFEST_REL}",
                git_mode="100644",
            ),
            authority_artifact_receipt(
                host_preparation_receipt_path,
                f"{EXPERIMENT_REL}/{HOST_PREPARATION_RECEIPT_REL}",
                git_mode="100644",
            ),
        )
        if row is not None
    ]
    environment_problems = validate_environment_receipt(
        env_receipt,
        bound_files,
        expected_host_preparation=host_preparation_receipt,
        expected_host_authority_artifacts=expected_host_authority_artifacts,
    )
    problems.extend(environment_problems)

    smoke_receipt = _load_json(smoke_receipt_path, SMOKE_RECEIPT_REL, problems)
    recomputed_smoke_receipt: dict[str, Any] | None = None
    smoke_bundle_problems: list[str] = []
    if smoke_receipt_path.is_file():
        smoke_rel = str(smoke_receipt_path.resolve().relative_to(experiment_dir.resolve()))
        bound_files[smoke_rel] = file_receipt(
            smoke_receipt_path, f"{EXPERIMENT_REL}/{smoke_rel}"
        )
        bound_paths.append(smoke_receipt_path)
        smoke_validator_path = Path(
            overrides.get("validate_smoke135.py", experiment_dir / "validate_smoke135.py")
        )
        if not smoke_validator_path.is_file():
            problems.append("smoke:recomputer-missing")
        else:
            try:
                recomputer, canonicalizer, renderer, bundle_validator = (
                    _load_smoke_validator_api(smoke_validator_path)
                )
                candidate = recomputer(experiment_dir)
            except Exception as error:  # the launch gate must fail closed on validator faults
                problems.append(f"smoke:recompute-error:{type(error).__name__}")
            else:
                if not isinstance(candidate, dict):
                    problems.append("smoke:recompute-not-object")
                else:
                    recomputed_smoke_receipt = candidate
                    if smoke_receipt != recomputed_smoke_receipt:
                        problems.append("smoke:recomputation-mismatch")
                    try:
                        stored_receipt_bytes = smoke_receipt_path.read_bytes()
                        summary_bytes = (
                            smoke_summary_path.read_bytes()
                            if smoke_summary_path.is_file()
                            and not smoke_summary_path.is_symlink()
                            and smoke_summary_path.resolve(strict=True)
                            == smoke_summary_path.absolute()
                            else None
                        )
                        smoke_bundle_problems.extend(
                            bundle_validator(
                                recomputed_smoke_receipt,
                                stored_receipt_bytes,
                                summary_bytes,
                            )
                        )
                        # Exercise both exposed projections independently; a partial or substituted
                        # validator API cannot authorize the manifest.
                        canonical_bytes = canonicalizer(recomputed_smoke_receipt)
                        if canonical_bytes != stored_receipt_bytes:
                            smoke_bundle_problems.append("smoke:receipt-canonical-bytes")
                        if summary_bytes is not None and renderer(
                            recomputed_smoke_receipt, canonical_bytes
                        ) != summary_bytes:
                            smoke_bundle_problems.append("smoke:summary-mismatch")
                    except Exception as error:
                        smoke_bundle_problems.append(
                            f"smoke:bundle-validation-error:{type(error).__name__}"
                        )
        if smoke_summary_path.is_file() and not smoke_summary_path.is_symlink():
            try:
                if smoke_summary_path.resolve(strict=True) != smoke_summary_path.absolute():
                    raise ValueError("summary path is not physical")
                summary_rel = str(
                    smoke_summary_path.resolve().relative_to(experiment_dir.resolve())
                )
                bound_files[summary_rel] = file_receipt(
                    smoke_summary_path, f"{EXPERIMENT_REL}/{summary_rel}"
                )
                bound_paths.append(smoke_summary_path)
            except (OSError, ValueError):
                smoke_bundle_problems.append("smoke:summary-nonregular")
        else:
            missing.append(SMOKE_SUMMARY_REL)
            smoke_bundle_problems.append(
                "smoke:summary-nonregular"
                if smoke_summary_path.exists() or smoke_summary_path.is_symlink()
                else "smoke:summary-missing"
            )
    else:
        missing.append(SMOKE_RECEIPT_REL)
    smoke_problems, smoke_artifacts = validate_smoke_receipt(
        recomputed_smoke_receipt if recomputed_smoke_receipt is not None else smoke_receipt,
        experiment_dir=experiment_dir,
        schedule=schedule,
        bound_hashes=bound_files,
        environment=env_receipt,
    )
    if smoke_receipt_path.is_file() and recomputed_smoke_receipt is None:
        smoke_problems.append("smoke:recomputation-unavailable")
    if smoke_receipt_path.is_file() and smoke_receipt != recomputed_smoke_receipt:
        smoke_problems.append("smoke:recomputation-mismatch")
    smoke_problems.extend(smoke_bundle_problems)
    problems.extend(smoke_problems)
    recomputed_artifact_hashes = {
        row.get("path"): row.get("sha256")
        for row in (
            recomputed_smoke_receipt.get("artifacts", [])
            if isinstance(recomputed_smoke_receipt, dict)
            else []
        )
        if isinstance(row, dict)
    }
    for artifact_path in smoke_artifacts:
        if artifact_path.is_file():
            rel = str(artifact_path.resolve().relative_to(experiment_dir.resolve()))
            artifact_receipt = file_receipt(
                artifact_path, f"{EXPERIMENT_REL}/{rel}"
            )
            if artifact_receipt["sha256"] != recomputed_artifact_hashes.get(rel):
                problems.append(f"smoke:artifact-post-recompute-drift:{rel}")
                smoke_problems.append(f"smoke:artifact-post-recompute-drift:{rel}")
            bound_files[rel] = artifact_receipt
            bound_paths.append(artifact_path)

    if git_provenance is None:
        git_paths = [mission_state_path, *bound_paths]
        git_provenance = collect_git_provenance(
            repo_root,
            git_paths,
            Path(overrides.get("HYPOTHESIS.md", experiment_dir / "HYPOTHESIS.md")),
        )
    git_problems = validate_git_provenance(git_provenance)
    problems.extend(git_problems)

    remote_artifacts: list[dict[str, Any]] = []
    if isinstance(env_receipt, dict) and isinstance(env_receipt.get("remote_files"), dict):
        for role in sorted(EXPECTED_REMOTE_FILES):
            row = env_receipt["remote_files"].get(role)
            if isinstance(row, dict):
                remote_artifacts.append(
                    {
                        "role": role,
                        "path": row.get("path"),
                        "sha256": row.get("sha256"),
                        "bytes": row.get("bytes"),
                    }
                )

    storage_gate: dict[str, Any] = {
        "minimum_remote_free_gib": 100,
        "minimum_reserve_gib": 25,
        "minimum_local_free_gib": 15,
        "minimum_remote_free_bytes": MINIMUM_REMOTE_FREE_BYTES,
        "minimum_reserve_bytes": MINIMUM_RESERVE_BYTES,
        "minimum_local_free_bytes": MINIMUM_LOCAL_FREE_BYTES,
        "filesystem_path": None,
        "projected_output_gib": None,
        "projected_output_bytes": PROJECTED_OUTPUT_BYTES,
        "observed_remote_free_gib": None,
        "observed_remote_free_bytes": None,
        "observed_local_free_gib": None,
        "observed_local_free_bytes": None,
        "filesystem_realpath": None,
        "filesystem_is_symlink": None,
        "filesystem_empty": None,
        "mount_target": None,
        "mount_source": None,
        "mount_fstype": None,
        "mount_uuid": None,
    }
    if isinstance(env_receipt, dict) and isinstance(env_receipt.get("storage"), dict):
        storage = env_receipt["storage"]
        storage_gate.update(
            {
                "projected_output_gib": storage.get("projected_output_gib"),
                "projected_output_bytes": storage.get("projected_output_bytes"),
                "observed_remote_free_gib": storage.get("remote_output_free_gib"),
                "observed_remote_free_bytes": storage.get("remote_output_free_bytes"),
                "observed_local_free_gib": storage.get("local_free_gib"),
                "observed_local_free_bytes": storage.get("local_free_bytes"),
                "filesystem_path": storage.get("filesystem_path"),
                "filesystem_realpath": storage.get("filesystem_realpath"),
                "filesystem_is_symlink": storage.get("filesystem_is_symlink"),
                "filesystem_empty": storage.get("filesystem_empty"),
                "mount_target": storage.get("mount_target"),
                "mount_source": storage.get("mount_source"),
                "mount_fstype": storage.get("mount_fstype"),
                "mount_uuid": storage.get("mount_uuid"),
            }
        )

    gates = {
        "g0_preregistration": not git_problems,
        "g1_provenance": not missing and not source_problems,
        "g2_released_behavior": not [p for p in runtime_problems if "union" in p],
        "g3_schedule_integrity": not schedule_problems,
        "g4_semantic_leak": not runtime_problems,
        "g5_live_smoke": not smoke_problems,
        "g7_dataset_provenance": not dataset_generator_problems and not dataset_problems,
        "g8_storage_environment": not environment_problems,
        "g9_resource_plan": (
            isinstance(smoke_receipt, dict)
            and type(smoke_receipt.get("gpu_seconds")) is int
            and 0 <= smoke_receipt["gpu_seconds"] < 110 * 60 * 60
        ),
        "execution_plan": not execution_problems,
        "execution_consumers": not consumer_problems,
        "tooling_verification": not tooling_problems,
        "mission_state": (not mission_problems and mission_phase == EXPECTED_MISSION_PHASE),
    }
    all_problems = sorted(set(problems))
    launch_authorized = not all_problems and all(gates.values())
    manifest = {
        "schema": SCHEMA,
        "verdict": READY_VERDICT if launch_authorized else INCOMPLETE_VERDICT,
        "launch_authorized": launch_authorized,
        "mission_phase": mission_phase,
        "mission_state": mission_receipt,
        "git_provenance": dict(git_provenance),
        "design": {
            "iteration": 135,
            "execution_unit": "pair-major-20-run-arm-block",
            "pair_count": 20,
            "arms": list(ARMS),
            "arm_config": ARM_CONFIG,
            "run_indices": list(RUN_INDICES),
            "planned_blocks": PLANNED_BLOCKS,
            "planned_episodes": PLANNED_EPISODES,
            "frozen_union_parameters": FROZEN_UNION_PARAMETERS,
            "done_marker": "I135_DOSE_DONE",
            "gpu": "single NVIDIA L4",
            "absolute_gpu_hour_ceiling": 110,
            "retry_policy": "no_automatic_retry_abort_on_first_block_failure",
            "allowed_retries": 0,
        },
        "planned_blocks": PLANNED_BLOCKS,
        "planned_episodes": PLANNED_EPISODES,
        "pair_order": [f"{cls}/{seq}" for cls, seq in canonical_pairs()],
        "execution_blocks": blocks,
        "execution_cells": cells,
        "hash_bound_files": dict(sorted(bound_files.items())),
        "source_artifacts": source_receipts,
        "remote_artifacts": remote_artifacts,
        "dataset_receipt": (env_receipt.get("dataset") if isinstance(env_receipt, dict) else None),
        "environment_receipts": (
            {
                **env_receipt,
                "docker_image_ids": {
                    name: image.get("image_id")
                    for name, image in env_receipt.get("container_images", {}).items()
                    if isinstance(image, dict)
                },
            }
            if isinstance(env_receipt, dict)
            else None
        ),
        "container_images": (
            env_receipt.get("container_images") if isinstance(env_receipt, dict) else None
        ),
        "storage_gate": storage_gate,
        "resource_gate": {
            "total_gpu_ceiling_seconds": 110 * 60 * 60,
            "prior_smoke_gpu_seconds": (
                smoke_receipt.get("gpu_seconds") if isinstance(smoke_receipt, dict) else None
            ),
            "remaining_analytic_seconds": (
                110 * 60 * 60 - smoke_receipt["gpu_seconds"]
                if isinstance(smoke_receipt, dict) and type(smoke_receipt.get("gpu_seconds")) is int
                else None
            ),
        },
        "smoke_receipt": (
            bound_files.get(SMOKE_RECEIPT_REL) if smoke_receipt_path.is_file() else None
        ),
        "host_packet_manifest": (
            bound_files.get(HOST_PACKET_MANIFEST_REL)
            if host_packet_manifest_path.is_file()
            else None
        ),
        "host_preparation_receipt": (
            bound_files.get(HOST_PREPARATION_RECEIPT_REL)
            if host_preparation_receipt_path.is_file()
            else None
        ),
        "tooling_verification_receipt": (
            bound_files.get(TOOLING_RECEIPT_REL) if tooling_receipt_path.is_file() else None
        ),
        "gates": gates,
        "missing_artifacts": sorted(set(missing)),
        "problem_count": len(all_problems),
        "problems": all_problems,
    }
    return manifest


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path)
    args = parser.parse_args(argv)
    manifest = build_manifest()
    if args.output is None:
        print(json.dumps(manifest, indent=1, sort_keys=True))
    else:
        _write_json(args.output, manifest)
    print(
        f"{manifest['verdict']} launch_authorized={manifest['launch_authorized']} "
        f"blocks={manifest['planned_blocks']} cells={manifest['planned_episodes']} "
        f"problems={manifest['problem_count']}",
        file=sys.stderr,
    )
    return 0 if manifest["launch_authorized"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
