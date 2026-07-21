from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import textwrap
import types

import pytest


REPO = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO
    / "experiments/iter135_neuroncap_blind_braking_dose_response/authorize_launch135.py"
)
SPEC = importlib.util.spec_from_file_location("iter135_launch_authorization", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
auth = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(auth)

PACKET_NAMES = (
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
    "tooling_verification_receipt.json",
    "prepare_host135.py",
)
EXECUTABLE_NAMES = {
    "capture_environment135.py",
    "run_smoke135.sh",
    "validate_smoke135.py",
    "prepare_host135.py",
}
PAYLOAD_NAMES = tuple(
    name
    for name in PACKET_NAMES
    if name not in {"MISSION_STATE.json", "tooling_verification_receipt.json"}
)


def _git(repo: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ("/usr/bin/git", *arguments),
        cwd=repo,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout


def _write(repo: Path, relative: str, payload: bytes | str | dict) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, dict):
        path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    elif isinstance(payload, bytes):
        path.write_bytes(payload)
    else:
        path.write_text(payload)


def _commit(repo: Path, message: str, *paths: str) -> str:
    _git(repo, "add", *paths)
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD").decode().strip()


def _load_module(path: Path, name: str) -> types.ModuleType:
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def _binding(relative: str, payload: bytes) -> dict[str, object]:
    return {
        "source_path": relative,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
    }


def _authority_artifact(
    relative: str,
    payload: bytes,
    *,
    git_mode: str = "100644",
) -> dict[str, object]:
    return {
        "path": relative,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "git_blob_oid": auth._git_blob_oid(payload),
        "git_mode": git_mode,
    }


@pytest.mark.parametrize("hostile_count", [False, 0.0])
def test_green_receipt_requires_exact_integer_zero(hostile_count: object) -> None:
    receipt = {
        "schema": auth.ENV_SCHEMA,
        "verdict": auth.ENV_VERDICT,
        "problem_count": hostile_count,
        "problems": [],
    }

    assert auth._green_receipt(
        receipt,
        auth.ENV_SCHEMA,
        auth.ENV_VERDICT,
        "environment",
    ) == ["environment:problem-metadata"]


@pytest.mark.parametrize("hostile_count", [True, 1.0])
def test_pre_smoke_manifest_requires_exact_integer_problem_count(
    hostile_count: object,
) -> None:
    manifest = {
        "schema": auth.MANIFEST_SCHEMA,
        "verdict": auth.PRE_SMOKE_VERDICT,
        "launch_authorized": False,
        "mission_phase": auth.TOOLING_PHASE,
        "missing_artifacts": ["smoke-evidence/smoke_receipt.json"],
        "problem_count": hostile_count,
        "problems": ["smoke:receipt-missing"],
    }

    assert auth._validate_pre_smoke_manifest(manifest) == [
        "pre-smoke:problem-contract"
    ]


@pytest.mark.parametrize(
    "mutation",
    [
        "problem-count-bool",
        "mission-state-bytes-float",
        "host-packet-bytes-float",
        "host-receipt-bytes-float",
        "environment-bytes-float",
        "smoke-bytes-float",
    ],
)
def test_final_manifest_rejects_numeric_json_aliases(mutation: str) -> None:
    state_payload = b'{"state":true}\n'
    payloads = {
        "host_packet_manifest.json": b'{"host_packet":true}\n',
        "host_preparation_receipt.json": b'{"host":true}\n',
        "env_receipts.json": b'{"environment":true}\n',
        "smoke-evidence/smoke_receipt.json": b'{"smoke":true}\n',
    }
    bound = {
        relative: _binding(relative, payload)
        for relative, payload in payloads.items()
    }
    manifest = {
        "schema": auth.MANIFEST_SCHEMA,
        "verdict": auth.FINAL_MANIFEST_VERDICT,
        "launch_authorized": True,
        "mission_phase": auth.LAUNCH_PHASE,
        "problem_count": 0,
        "problems": [],
        "gates": {"all": True},
        "mission_state": _binding(auth.MISSION_REL, state_payload),
        "hash_bound_files": bound,
        "host_preparation_receipt": copy.deepcopy(
            bound["host_preparation_receipt.json"]
        ),
        "host_packet_manifest": copy.deepcopy(bound["host_packet_manifest.json"]),
    }
    if mutation == "problem-count-bool":
        manifest["problem_count"] = False
    elif mutation == "mission-state-bytes-float":
        manifest["mission_state"]["bytes"] = float(
            manifest["mission_state"]["bytes"]
        )
    else:
        relative = {
            "host-packet-bytes-float": "host_packet_manifest.json",
            "host-receipt-bytes-float": "host_preparation_receipt.json",
            "environment-bytes-float": "env_receipts.json",
            "smoke-bytes-float": "smoke-evidence/smoke_receipt.json",
        }[mutation]
        manifest["hash_bound_files"][relative]["bytes"] = float(
            manifest["hash_bound_files"][relative]["bytes"]
        )

    problems = auth._validate_final_manifest(
        manifest,
        state_payload=state_payload,
        host_packet_payload=payloads["host_packet_manifest.json"],
        host_payload=payloads["host_preparation_receipt.json"],
        env_payload=payloads["env_receipts.json"],
        smoke_payload=payloads["smoke-evidence/smoke_receipt.json"],
    )

    assert problems


def _publication_authority(commit: str, artifacts: list[dict] | None = None) -> dict:
    return {
        "schema": auth.PUBLICATION_AUTHORITY_SCHEMA,
        "repository": auth.PUBLICATION_REPOSITORY,
        "branch": auth.PUBLICATION_BRANCH,
        "source_commit": commit,
        "branch_head_sha": commit,
        "required_checks": list(auth.PUBLICATION_CHECKS),
        "checks": [
            {
                "name": name,
                "id": 510 + index,
                "status": "completed",
                "conclusion": "success",
                "head_sha": commit,
                "app_slug": "github-actions",
            }
            for index, name in enumerate(auth.PUBLICATION_CHECKS)
        ],
        "artifacts": artifacts or [],
        "verified": True,
    }


def _complete_tooling_receipt(receipt: dict) -> dict:
    receipt.update(
        {
            "inventory": {
                "contract": "frozen fixture inventory",
                "tests": [],
                "python_tools": [],
                "python_files": [],
                "shell_files": [],
                "data_files": [],
                "control_files": [],
                "tested_files": [],
            },
            "inventory_sha256": "1" * 64,
            "toolchain": {},
            "environment_contract": {},
            "files": {},
            "file_content_set_sha256": "2" * 64,
            "command_contract": [],
            "commands": [],
            "timing": {
                "started_at_utc": "2026-07-16T00:00:00Z",
                "finished_at_utc": "2026-07-16T00:00:01Z",
                "wall_duration_ns": 1_000_000_000,
                "monotonic_duration_ns": 1_000_000_000,
            },
        }
    )
    receipt["receipt_payload_sha256"] = hashlib.sha256(
        auth._canonical_json(receipt)
    ).hexdigest()
    return receipt


def _docker_runtime() -> dict:
    return {
        "schema": "iter135.docker_runtime_receipt.v1",
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
                "arch": "x86_64",
                "build_time": "2025-01-22T13:41:17.000000000+00:00",
                "experimental": False,
            },
        },
    }


def _make_validator_source() -> str:
    source = r'''
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
REQUIRED_PAYLOAD_NAMES = __PAYLOAD_NAMES__
HOST_PACKET_FILE_NAMES = __PACKET_NAMES__
HYPOTHESIS_REL = "experiments/iter135_neuroncap_blind_braking_dose_response/HYPOTHESIS.md"

def receipt(path, source_path):
    payload = Path(path).read_bytes()
    return {
        "source_path": source_path,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
    }

def validate_host_preparation_evidence(packet, host, *, packet_binding, expected_file_bindings):
    problems = []
    # The frozen validator reads git_blob_oid and git_mode from the bindings, so the
    # controller must pass the FULL binding rows, never the three-field packet projection.
    if not all(
        isinstance(row, dict) and "git_blob_oid" in row and "git_mode" in row
        for row in expected_file_bindings.values()
    ):
        problems.append("binding-fields")
    projected = {
        name: {"sha256": row.get("sha256"), "bytes": row.get("bytes"), "mode": row.get("mode")}
        for name, row in expected_file_bindings.items()
    }
    if packet.get("files") != projected:
        problems.append("packet-files")
    if not isinstance(host.get("repositories"), dict) or not isinstance(host.get("storage"), dict):
        problems.append("deep-host")
    if host.get("packet_manifest_sha256") != packet_binding.get("sha256"):
        problems.append("packet-binding")
    if host.get("publication_authority", {}).get("verified") is not True:
        problems.append("publication-authority")
    return problems

def validate_environment_receipt(
    receipt_value,
    bound_hashes,
    *,
    expected_host_preparation=None,
    expected_host_authority_artifacts=None,
):
    # The frozen validator reads the patcher binding and the two host-authority artifact
    # rows; the controller must supply both or a true receipt can never validate.
    if "patch_compose_dose_env.py" not in bound_hashes:
        return ["patcher-binding-missing"]
    if not isinstance(expected_host_authority_artifacts, list) or len(
        expected_host_authority_artifacts
    ) != 2 or not all(
        isinstance(row, dict) and "git_blob_oid" in row and "git_mode" in row
        for row in expected_host_authority_artifacts
    ):
        return ["host-authority-artifacts-missing"]
    if (
        receipt_value.get("deep_probe") != "remote-probes-replayed"
        or receipt_value.get("host_preparation", {}).get("evidence") != expected_host_preparation
        or receipt_value.get("host_publication_authority", {}).get("verified") is not True
        or receipt_value.get("docker_runtime", {}).get("schema")
        != "iter135.docker_runtime_receipt.v1"
    ):
        return ["deep-environment"]
    return []

def build_manifest(*, repo_root, experiment_dir, mission_state_path, git_provenance, **_kwargs):
    experiment_dir = Path(experiment_dir)
    state_path = Path(mission_state_path)
    state = json.loads(state_path.read_text())
    phase = state["next_program"]["phase"]
    smoke_path = experiment_dir / "smoke-evidence/smoke_receipt.json"
    smoke_exists = smoke_path.is_file()
    host_packet = receipt(
        experiment_dir / "host_packet_manifest.json", "host_packet_manifest.json"
    )
    host = receipt(
        experiment_dir / "host_preparation_receipt.json", "host_preparation_receipt.json"
    )
    environment = receipt(experiment_dir / "env_receipts.json", "env_receipts.json")
    bound = {
        "host_packet_manifest.json": host_packet,
        "host_preparation_receipt.json": host,
        "env_receipts.json": environment,
    }
    if smoke_exists:
        bound["smoke-evidence/smoke_receipt.json"] = receipt(
            smoke_path, "smoke-evidence/smoke_receipt.json"
        )
    authorized = smoke_exists and phase == "LAUNCH_AUTHORIZED"
    missing = [] if smoke_exists else ["smoke-evidence/smoke_receipt.json"]
    problems = [] if smoke_exists else ["smoke:receipt-missing"]
    return {
        "schema": "iter135.launch_manifest.v2",
        "verdict": (
            "I135_TOOLING_MANIFEST_OK"
            if authorized
            else "I135_TOOLING_MANIFEST_INCOMPLETE"
        ),
        "launch_authorized": authorized,
        "mission_phase": phase,
        "mission_state": receipt(state_path, "MISSION_STATE.json"),
        "git_provenance": dict(git_provenance),
        "hash_bound_files": bound,
        "host_packet_manifest": host_packet,
        "host_preparation_receipt": host,
        "gates": {"deep_replay": authorized},
        "missing_artifacts": missing,
        "problem_count": len(problems),
        "problems": problems,
    }
'''
    return textwrap.dedent(source).replace("__PAYLOAD_NAMES__", repr(PAYLOAD_NAMES)).replace(
        "__PACKET_NAMES__", repr(PACKET_NAMES)
    )


def _smoke_validator_source() -> str:
    return textwrap.dedent(
        r'''
        import hashlib
        import json
        from pathlib import Path

        EXPECTED = {
            "execution.jsonl",
            "pre_smoke_manifest.json",
            "pre_smoke_mission_state.json",
            "environment_receipt.json",
            *{
                f"{dose}.{suffix}"
                for dose in ("blind_0_5x", "blind_1_0x", "blind_1_5x", "blind_2_0x")
                for suffix in ("decisions.jsonl", "model-env.bin", "compose.log")
            },
        }

        def recompute_smoke_receipt(experiment_dir):
            raw = Path(experiment_dir) / "smoke-evidence/raw"
            names = {path.name for path in raw.iterdir()} if raw.is_dir() else set()
            state = json.loads((raw / "pre_smoke_mission_state.json").read_text())
            manifest = json.loads((raw / "pre_smoke_manifest.json").read_text())
            environment = json.loads((raw / "environment_receipt.json").read_text())
            problems = []
            if names != EXPECTED:
                problems.append("raw:file-set")
            if (raw / "execution.jsonl").read_bytes() != b"deep-smoke-ok\n":
                problems.append("raw:execution")
            if state.get("next_program", {}).get("phase") != "TOOLING_FROZEN_PREFLIGHT_REQUIRED":
                problems.append("raw:state")
            if manifest.get("mission_phase") != "TOOLING_FROZEN_PREFLIGHT_REQUIRED":
                problems.append("raw:manifest")
            if environment.get("deep_probe") != "remote-probes-replayed":
                problems.append("raw:environment")
            artifacts = {
                name: hashlib.sha256((raw / name).read_bytes()).hexdigest()
                for name in sorted(names)
            }
            return {
                "schema": "iter135.smoke_receipt.v1",
                "verdict": (
                    "I135_LIVE_SMOKE_OK" if not problems else "I135_LIVE_SMOKE_INFRA_NULL"
                ),
                "problem_count": len(problems),
                "problems": problems,
                "nonanalytic": True,
                "analytic_episode_count": 0,
                "artifacts": artifacts,
            }

        def canonical_smoke_receipt_bytes(receipt):
            return (json.dumps(receipt, indent=1, sort_keys=True) + "\n").encode()

        def render_smoke_summary(receipt, receipt_bytes=None):
            payload = receipt_bytes or canonical_smoke_receipt_bytes(receipt)
            return b"# generated smoke\n" + hashlib.sha256(payload).hexdigest().encode() + b"\n"
        '''
    )


def _host_repository_row(
    label: str,
    *,
    dirty: list[str],
    untracked: list[str],
) -> dict[str, object]:
    return {
        "path": auth.HOST_REPOSITORY_PATHS[label],
        "head": auth.HOST_REPOSITORY_HEADS[label],
        "staged_paths": [],
        "dirty_tracked_paths": dirty,
        "untracked_paths": untracked,
    }


def _host_receipt(
    packet_payload: bytes,
    packet: dict,
    expected_files: dict[str, dict[str, object]],
    publication_artifacts: list[dict[str, object]],
) -> dict:
    observed = {
        name: {"path": f"/opt/sentinel-stack/.iter135-packet/{name}", **row}
        for name, row in expected_files.items()
    }
    compose_path = "/opt/sentinel-stack/NeuroNCAP/scripts/_docker_compose_release.sh"
    host = {
        "schema": auth.HOST_SCHEMA,
        "verdict": auth.HOST_VERDICT,
        "started_at_utc": "2026-07-16T09:58:00Z",
        "finished_at_utc": "2026-07-16T09:59:00Z",
        "host": "sentinel-gpu",
        "problem_count": 0,
        "problems": [],
        "packet_manifest_sha256": hashlib.sha256(packet_payload).hexdigest(),
        "publication_authority": _publication_authority(
            packet["source_commit"],
            sorted(publication_artifacts, key=lambda row: str(row["path"])),
        ),
        "packet": {
            "schema": auth.HOST_PACKET_SCHEMA,
            "source_commit": packet["source_commit"],
            "manifest": {
                "path": "/opt/sentinel-stack/.iter135-packet/host_packet_manifest.json",
                "sha256": hashlib.sha256(packet_payload).hexdigest(),
                "bytes": len(packet_payload),
                "mode": 0o644,
            },
            "independently_supplied_manifest_sha256": hashlib.sha256(
                packet_payload
            ).hexdigest(),
            "files": observed,
        },
        "controller": observed["prepare_host135.py"],
        "repositories": {
            "before": {
                "uniad": _host_repository_row(
                    "uniad",
                    dirty=[
                        "inference/server.py",
                        "projects/mmdet3d_plugin/uniad/detectors/uniad_track.py",
                    ],
                    untracked=["checkpoints"],
                ),
                "neuroncap": _host_repository_row(
                    "neuroncap",
                    dirty=["docker/Dockerfile", "scripts/_docker_compose_release.sh"],
                    untracked=["outoutput"],
                ),
                "neurad": _host_repository_row(
                    "neurad", dirty=["Dockerfile"], untracked=["Dockerfile.bak"]
                ),
            },
            "after": {
                "uniad": _host_repository_row(
                    "uniad",
                    dirty=["projects/mmdet3d_plugin/uniad/detectors/uniad_track.py"],
                    untracked=["checkpoints"],
                ),
                "neuroncap": _host_repository_row(
                    "neuroncap",
                    dirty=["docker/Dockerfile", "scripts/_docker_compose_release.sh"],
                    untracked=["outoutput"],
                ),
                "neurad": _host_repository_row(
                    "neurad", dirty=["Dockerfile"], untracked=["Dockerfile.bak"]
                ),
            },
        },
        "compose": {
            "patcher": observed["patch_compose_dose_env.py"],
            "before": {
                "path": compose_path,
                "sha256": "9f8804b523faa8ec3b6770a69b4b4bc9595c2b36e4b98422a588b9a3e1fe8e5d",
                "bytes": 3_380,
                "mode": 0o755,
            },
            "after": {
                "path": compose_path,
                "sha256": "a5ed766b8a4c7efd7b33cdb6a9bdf9a5878f63604695758ff5f2268b770cfada",
                "bytes": 3_613,
                "mode": 0o755,
            },
        },
        "storage": {
            "mount_target": "/datasets/nuscenes-full",
            "mount_source": "/dev/nvme0n2",
            "mount_fstype": "ext4",
            "mount_uuid": "9a98277e-b21f-4ffc-8f14-3f2235b43103",
            "dataset_st_dev": 66308,
            "root_st_dev": 66305,
            "free_bytes_before": 121 * 1024**3,
            "free_bytes_after": 121 * 1024**3,
            "minimum_remote_free_bytes": 100 * 1024**3,
            "projected_output_bytes": 72_380_432_384,
            "minimum_reserve_bytes": 25 * 1024**3,
            "analytic_root": "/datasets/nuscenes-full/sentinel-i135-outoutput",
            "analytic_root_realpath": "/datasets/nuscenes-full/sentinel-i135-outoutput",
            "analytic_root_is_symlink": False,
            "analytic_root_empty": True,
            "analytic_root_st_dev": 66308,
        },
        "forbidden_paths": {
            path: False for path in sorted(auth.EXPECTED_HOST_FORBIDDEN_PATHS)
        },
        "actions": [
            {
                "action": "normalize_uniad_server_from_verified_head_blob",
                "performed": False,
                "before": {
                    "path": "/opt/sentinel-stack/UniAD/inference/server.py",
                    "sha256": (
                        "066a3fc31a2c78960255cedf659018bab4190ac5dee7e7c5ec14d1031043c424"
                    ),
                    "bytes": 4_519,
                    "mode": 0o644,
                },
                "after": {
                    "path": "/opt/sentinel-stack/UniAD/inference/server.py",
                    "sha256": (
                        "066a3fc31a2c78960255cedf659018bab4190ac5dee7e7c5ec14d1031043c424"
                    ),
                    "bytes": 4_519,
                    "mode": 0o644,
                },
            },
            {
                "action": "atomically_patch_compose_from_exact_preimage",
                "performed": True,
                "before_sha256": (
                    "9f8804b523faa8ec3b6770a69b4b4bc9595c2b36e4b98422a588b9a3e1fe8e5d"
                ),
                "after_sha256": (
                    "a5ed766b8a4c7efd7b33cdb6a9bdf9a5878f63604695758ff5f2268b770cfada"
                ),
            },
            {
                "action": "create_absent_empty_analytic_root",
                "performed": True,
                "path": "/datasets/nuscenes-full/sentinel-i135-outoutput",
            },
            {
                "action": "atomically_install_verified_packet",
                "performed": True,
                "from": "/opt/sentinel-stack/.iter135-packet",
                "to": "/opt/sentinel-stack/iter135",
            },
        ],
        "invocation": {
            "environment": dict(auth.HOST_SAFE_ENVIRONMENT),
            "environment_matches": True,
            "isolated": True,
            "python_implementation": "CPython",
            "python_version": "3.10.14",
        },
        "receipt_payload_sha256": None,
    }
    payload = dict(host)
    payload.pop("receipt_payload_sha256")
    host["receipt_payload_sha256"] = hashlib.sha256(auth._canonical_json(payload)).hexdigest()
    return host


def _preflight_state() -> dict:
    return {
        "schema": "sentinel.mission_state.v1",
        "next_program": {"phase": auth.TOOLING_PHASE},
        "run_state": "IDLE",
    }


def _publication(
    tmp_path: Path,
    *,
    tamper_raw_manifest: bool = False,
    tamper_raw_decision_after_receipt: bool = False,
    tamper_final_state_binding: bool = False,
    tamper_activation: bool = False,
    tamper_host_packet_binding: bool = False,
    tamper_host_packet_source: bool = False,
    tamper_host_actions: bool = False,
    host_exactness_mutation: str | None = None,
    tamper_host_authority_artifacts: bool = False,
    tamper_environment_deep: bool = False,
    environment_host_evidence_numeric_alias: str | None = None,
    activation_numeric_alias: str | None = None,
    tooling_receipt_root_mutation: str | None = None,
    tooling_receipt_nested_mutation: bool = False,
    tooling_publication_overrides: dict[str, object] | None = None,
    publish_activation: bool = True,
) -> tuple[Path, dict[str, str]]:
    repo = tmp_path
    _git(repo, "init", "-b", "master")
    _git(repo, "config", "user.name", "Sentinel Test")
    _git(repo, "config", "user.email", "sentinel-test@example.invalid")
    experiment = repo / auth.EXPERIMENT_REL
    experiment.mkdir(parents=True)

    prepare_source = (
        f"REQUIRED_PACKET_FILES = {PACKET_NAMES!r}\n"
        f"EXPECTED_PACKET_MODES = "
        f"{{name: (0o755 if name in {EXECUTABLE_NAMES!r} else 0o644) "
        f"for name in REQUIRED_PACKET_FILES}}\n"
    )
    capture_source = f"EXPECTED_PREPARATION_PACKET_FILES = {set(PACKET_NAMES)!r}\n"
    sources = {
        "prepare_host135.py": prepare_source,
        "capture_environment135.py": capture_source,
        "make_launch_manifest.py": _make_validator_source(),
        "validate_smoke135.py": _smoke_validator_source(),
        "verify_tooling135.py": (
            "def validate_published_receipt_structure(receipt, *a, **k):\n"
            "    return ['nested receipt invalid'] if receipt.get('commands') else []\n"
        ),
        "authorize_launch135.py": MODULE_PATH.read_text(),
    }
    for name in PAYLOAD_NAMES:
        _write(repo, f"{auth.EXPERIMENT_REL}/{name}", sources.get(name, f"payload:{name}\n"))
        mode = 0o755 if name in EXECUTABLE_NAMES else 0o644
        (experiment / name).chmod(mode)
    baseline_state = _preflight_state()
    baseline_state["next_program"]["phase"] = "PREREGISTERED_TOOLING_REQUIRED"
    _write(repo, auth.MISSION_REL, baseline_state)
    _write(repo, "CONTINUITY.md", "baseline\n")
    _write(repo, "HANDOFF.md", "baseline\n")
    baseline_paths = [
        auth.MISSION_REL,
        "CONTINUITY.md",
        "HANDOFF.md",
        *(f"{auth.EXPERIMENT_REL}/{name}" for name in PAYLOAD_NAMES if name != "HYPOTHESIS.md"),
    ]
    _commit(repo, "baseline packet sources", *baseline_paths)
    _write(repo, f"{auth.EXPERIMENT_REL}/HYPOTHESIS.md", "hypothesis v1\n")
    _commit(repo, "hypothesis registration", f"{auth.EXPERIMENT_REL}/HYPOTHESIS.md")
    _write(repo, f"{auth.EXPERIMENT_REL}/HYPOTHESIS.md", "hypothesis v2 frozen\n")
    _commit(repo, "hypothesis amendment", f"{auth.EXPERIMENT_REL}/HYPOTHESIS.md")
    _write(repo, "source-freeze-marker.txt", "generation four\n")
    source_commit = _commit(repo, "generation four source freeze", "source-freeze-marker.txt")

    source_parents = _git(repo, "show", "-s", "--format=%P", source_commit).decode().split()
    source_paths = sorted(
        item.decode()
        for item in _git(
            repo,
            "diff-tree",
            "--root",
            "--no-commit-id",
            "--name-only",
            "-r",
            "-z",
            source_commit,
        ).split(b"\0")
        if item
    )
    git_state = {
        "head": source_commit,
        "dirty_entries": [],
        "porcelain_v1_z_sha256": hashlib.sha256(b"").hexdigest(),
        "branch": "master",
        "upstream": "origin/master",
        "upstream_head": source_commit,
        "parents": source_parents,
        "commit_paths": source_paths,
    }

    publication = dict(auth.EXPECTED_TOOLING_PUBLICATION)
    if tooling_publication_overrides:
        publication.update(tooling_publication_overrides)
    receipt = {
        "schema": "iter135.tooling_verification.v2",
        "verdict": "I135_TOOLING_VERIFICATION_OK",
        "problem_count": 0,
        "problems": [],
        "publication": publication,
        "repository": {
            "root": "/Users/danielwahnich/workspace/sentinel",
            "git_start": git_state,
            "git_end": git_state,
            "git_head_stable": True,
            "git_state_stable": True,
            "repository_clean_state_stable": True,
        },
    }
    _complete_tooling_receipt(receipt)
    if tooling_receipt_nested_mutation:
        receipt["commands"] = [{"forged": True}]
    if tooling_receipt_root_mutation == "extra":
        receipt["unexpected_root"] = True
    elif tooling_receipt_root_mutation == "missing":
        receipt.pop("timing")
    elif tooling_receipt_root_mutation is not None:
        raise AssertionError(
            f"unsupported tooling receipt mutation: {tooling_receipt_root_mutation}"
        )
    if tooling_receipt_root_mutation is not None or tooling_receipt_nested_mutation:
        receipt["receipt_payload_sha256"] = hashlib.sha256(
            auth._canonical_json(
                {key: value for key, value in receipt.items() if key != "receipt_payload_sha256"}
            )
        ).hexdigest()
    _write(repo, auth.TOOLING_RECEIPT_REL, receipt)
    tooling_receipt = _commit(
        repo, "generation four receipt", auth.TOOLING_RECEIPT_REL
    )
    _write(repo, auth.MISSION_REL, _preflight_state())
    # Force a state-only commit without altering the semantic state bytes consumed by smoke.
    (repo / auth.MISSION_REL).write_text(
        json.dumps(_preflight_state(), indent=1, sort_keys=True) + "\n"
    )
    tooling_state = _commit(repo, "generation four state", auth.MISSION_REL)
    _write(repo, "CONTINUITY.md", "tooling baton\n")
    _write(repo, "HANDOFF.md", "GPU_RUN_STATE=NOT_PROBED_OFFLINE_GENERATION\n")
    tooling_baton = _commit(repo, "generation four baton", "CONTINUITY.md", "HANDOFF.md")

    packet_files: dict[str, dict[str, object]] = {}
    packet_authority_artifacts: list[dict[str, object]] = []
    for name in PACKET_NAMES:
        relative = auth.MISSION_REL if name == "MISSION_STATE.json" else f"{auth.EXPERIMENT_REL}/{name}"
        payload = _git(repo, "show", f"{tooling_baton}:{relative}")
        mode = 0o755 if name in EXECUTABLE_NAMES else 0o644
        packet_files[name] = {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "mode": mode,
        }
        packet_authority_artifacts.append(
            _authority_artifact(
                relative,
                payload,
                git_mode="100755" if mode == 0o755 else "100644",
            )
        )
    packet = {
        "schema": auth.HOST_PACKET_SCHEMA,
        "source_commit": "a" * 40 if tamper_host_packet_source else tooling_baton,
        "files": packet_files,
    }
    _write(repo, auth.HOST_PACKET_REL, packet)
    packet_payload = (repo / auth.HOST_PACKET_REL).read_bytes()
    host = _host_receipt(
        packet_payload,
        packet,
        packet_files,
        packet_authority_artifacts,
    )
    if tamper_host_packet_binding:
        host["packet_manifest_sha256"] = "0" * 64
    if tamper_host_actions:
        host["actions"][2]["performed"] = False
    if host_exactness_mutation == "compose-patcher-bytes-float":
        host["compose"]["patcher"] = copy.deepcopy(host["compose"]["patcher"])
        host["compose"]["patcher"]["bytes"] = float(host["compose"]["patcher"]["bytes"])
    elif host_exactness_mutation == "compose-patcher-bytes-bool":
        host["compose"]["patcher"] = copy.deepcopy(host["compose"]["patcher"])
        host["compose"]["patcher"]["bytes"] = True
    elif host_exactness_mutation == "storage-extra":
        host["storage"]["unregistered_claim"] = 0
    elif host_exactness_mutation == "storage-missing":
        host["storage"].pop("mount_uuid")
    elif host_exactness_mutation == "storage-device-float":
        host["storage"]["dataset_st_dev"] = float(host["storage"]["dataset_st_dev"])
    elif host_exactness_mutation == "storage-device-negative":
        host["storage"]["dataset_st_dev"] = -2
        host["storage"]["analytic_root_st_dev"] = -2
        host["storage"]["root_st_dev"] = -1
    elif host_exactness_mutation == "action-extra":
        host["actions"][1]["unregistered_claim"] = 0
    elif host_exactness_mutation == "action-omission":
        host["actions"][2].pop("path")
    elif host_exactness_mutation == "invocation-extra":
        host["invocation"]["unregistered_claim"] = 0
    elif host_exactness_mutation == "invocation-omission":
        host["invocation"].pop("environment_matches")
    elif host_exactness_mutation == "invocation-environment-alias":
        host["invocation"]["environment"]["PYTHONHASHSEED"] = 0
    elif host_exactness_mutation is not None:
        raise AssertionError(
            f"unsupported host exactness mutation: {host_exactness_mutation}"
        )
    if tamper_host_authority_artifacts:
        host["publication_authority"]["artifacts"] = host["publication_authority"][
            "artifacts"
        ][:-1]
    payload = dict(host)
    payload.pop("receipt_payload_sha256")
    host["receipt_payload_sha256"] = hashlib.sha256(auth._canonical_json(payload)).hexdigest()
    _write(repo, auth.HOST_REL, host)
    host_commit = _commit(repo, "host preparation", auth.HOST_PACKET_REL, auth.HOST_REL)
    host_payload = (repo / auth.HOST_REL).read_bytes()

    environment_host_evidence = copy.deepcopy(host)
    if environment_host_evidence_numeric_alias == "problem-count-bool":
        environment_host_evidence["problem_count"] = False
    elif environment_host_evidence_numeric_alias == "storage-device-float":
        environment_host_evidence["storage"]["dataset_st_dev"] = float(
            environment_host_evidence["storage"]["dataset_st_dev"]
        )
    elif environment_host_evidence_numeric_alias is not None:
        raise AssertionError(
            "unsupported environment host-evidence numeric alias: "
            f"{environment_host_evidence_numeric_alias}"
        )
    environment = {
        "schema": auth.ENV_SCHEMA,
        "verdict": auth.ENV_VERDICT,
        "problem_count": 0,
        "problems": [],
        "deep_probe": "handcrafted-green" if tamper_environment_deep else "remote-probes-replayed",
        "host_preparation": {
            "receipt_file": {
                "path": "/opt/sentinel-stack/iter135/host_preparation_receipt.json",
                "sha256": hashlib.sha256(host_payload).hexdigest(),
                "bytes": len(host_payload),
            },
            "evidence": environment_host_evidence,
        },
        "host_publication_authority": _publication_authority(
            host_commit,
            [
                {
                    **_authority_artifact(auth.HOST_PACKET_REL, packet_payload),
                },
                {
                    **_authority_artifact(auth.HOST_REL, host_payload),
                },
            ],
        ),
        "docker_runtime": _docker_runtime(),
    }
    _write(repo, auth.ENV_REL, environment)
    environment_commit = _commit(repo, "environment receipt", auth.ENV_REL)
    environment_payload = (repo / auth.ENV_REL).read_bytes()

    manifest_module = _load_module(experiment / "make_launch_manifest.py", "fixture_manifest_p")
    pre_manifest = manifest_module.build_manifest(
        repo_root=repo,
        experiment_dir=experiment,
        mission_state_path=repo / auth.MISSION_REL,
        git_provenance=auth._observed_git_provenance(
            repo, manifest_module, include_smoke=False
        ),
    )
    _write(repo, auth.MANIFEST_REL, pre_manifest)
    pre_smoke_commit = _commit(repo, "pre-smoke manifest", auth.MANIFEST_REL)
    pre_manifest_payload = (repo / auth.MANIFEST_REL).read_bytes()

    tampered_pre_manifest = dict(pre_manifest)
    tampered_pre_manifest["handcrafted"] = True
    raw_payloads = {
        "execution.jsonl": b"deep-smoke-ok\n",
        "pre_smoke_manifest.json": (
            (json.dumps(tampered_pre_manifest, indent=1, sort_keys=True) + "\n").encode()
            if tamper_raw_manifest
            else pre_manifest_payload
        ),
        "pre_smoke_mission_state.json": _git(
            repo, "show", f"{tooling_baton}:{auth.MISSION_REL}"
        ),
        "environment_receipt.json": environment_payload,
    }
    for dose in auth.BLIND_DOSES:
        raw_payloads[f"{dose}.decisions.jsonl"] = f"decision:{dose}\n".encode()
        raw_payloads[f"{dose}.model-env.bin"] = f"env:{dose}\0".encode()
        raw_payloads[f"{dose}.compose.log"] = f"compose:{dose}\n".encode()
    for name, payload_value in raw_payloads.items():
        _write(repo, f"{auth.SMOKE_ROOT_REL}/raw/{name}", payload_value)
    smoke_module = _load_module(experiment / "validate_smoke135.py", "fixture_smoke")
    smoke = smoke_module.recompute_smoke_receipt(experiment)
    smoke_bytes = smoke_module.canonical_smoke_receipt_bytes(smoke)
    _write(repo, auth.SMOKE_RECEIPT_REL, smoke_bytes)
    _write(
        repo,
        f"{auth.SMOKE_ROOT_REL}/SMOKE.md",
        smoke_module.render_smoke_summary(smoke, smoke_bytes),
    )
    if tamper_raw_decision_after_receipt:
        _write(
            repo,
            f"{auth.SMOKE_ROOT_REL}/raw/blind_1_0x.decisions.jsonl",
            b"handcrafted replacement\n",
        )
    smoke_commit = _commit(repo, "smoke evidence", *auth.SMOKE_EVIDENCE_PATHS)

    launch_state = {
        "schema": "sentinel.mission_state.v1",
        "next_program": {"phase": auth.LAUNCH_PHASE},
        "run_state": "IDLE",
    }
    _write(repo, auth.MISSION_REL, launch_state)
    state_commit = _commit(repo, "launch state", auth.MISSION_REL)

    manifest_module = _load_module(experiment / "make_launch_manifest.py", "fixture_manifest_f")
    final_manifest = manifest_module.build_manifest(
        repo_root=repo,
        experiment_dir=experiment,
        mission_state_path=repo / auth.MISSION_REL,
        git_provenance=auth._observed_git_provenance(
            repo, manifest_module, include_smoke=True
        ),
    )
    if tamper_final_state_binding:
        final_manifest["mission_state"] = _binding(auth.MISSION_REL, b"wrong-state\n")
    _write(repo, auth.MANIFEST_REL, final_manifest)
    final_manifest_commit = _commit(repo, "final manifest", auth.MANIFEST_REL)

    activation = auth.build_activation_receipt(
        repo,
        tooling_receipt_commit=tooling_receipt,
        host_commit=host_commit,
        environment_commit=environment_commit,
        pre_smoke_manifest_commit=pre_smoke_commit,
        smoke_commit=smoke_commit,
        state_commit=state_commit,
        final_manifest_commit=final_manifest_commit,
    )
    if tamper_activation:
        activation["phase"] = auth.TOOLING_PHASE
        payload = dict(activation)
        payload.pop("receipt_payload_sha256")
        activation["receipt_payload_sha256"] = hashlib.sha256(
            auth._canonical_json(payload)
        ).hexdigest()
    if activation_numeric_alias == "problem-count-bool":
        activation["problem_count"] = False
    elif activation_numeric_alias == "artifact-bytes-float":
        activation["artifacts"]["mission_state"]["bytes"] = float(
            activation["artifacts"]["mission_state"]["bytes"]
        )
    elif activation_numeric_alias is not None:
        raise AssertionError(
            f"unsupported activation numeric alias: {activation_numeric_alias}"
        )
    _write(repo, auth.ACTIVATION_REL, activation)
    _write(repo, "CONTINUITY.md", "launch activation\n")
    _write(repo, "HANDOFF.md", "LAUNCH_ACTIVATION=COMMITTED\n")
    activation_commit = _commit(
        repo,
        "launch activation baton",
        auth.ACTIVATION_REL,
        "CONTINUITY.md",
        "HANDOFF.md",
    )
    _git(repo, "remote", "add", "origin", ".")
    _git(
        repo,
        "update-ref",
        "refs/remotes/origin/master",
        activation_commit if publish_activation else smoke_commit,
    )
    return repo, {
        "source": source_commit,
        "tooling_receipt": tooling_receipt,
        "tooling_state": tooling_state,
        "tooling_baton": tooling_baton,
        "host": host_commit,
        "environment": environment_commit,
        "pre_smoke": pre_smoke_commit,
        "smoke": smoke_commit,
        "state": state_commit,
        "final_manifest": final_manifest_commit,
        "activation": activation_commit,
    }


def _descendants(commits: dict[str, str]) -> list[str]:
    return [
        commits["host"],
        commits["environment"],
        commits["pre_smoke"],
        commits["smoke"],
        commits["state"],
        commits["final_manifest"],
        commits["activation"],
    ]


def _control_publication(
    repo: Path,
    commits: dict[str, str],
    *,
    receipt_commit: str | None = None,
    baton_extra_path: bool = False,
    state: dict | None = None,
) -> tuple[str, str]:
    active_receipt = receipt_commit or commits["tooling_receipt"]
    _git(repo, "checkout", "--detach", active_receipt)
    control_state = (
        auth._control_hardening_expected_state()
        if state is None
        else copy.deepcopy(state)
    )
    _write(repo, auth.MISSION_REL, control_state)
    state_commit = _commit(repo, "generation fifteen control state", auth.MISSION_REL)
    _write(repo, "CONTINUITY.md", "control hardening transition\n")
    _write(repo, "HANDOFF.md", "GPU_RUN_STATE=UNKNOWN\n")
    baton_paths = ["CONTINUITY.md", "HANDOFF.md"]
    if baton_extra_path:
        _write(repo, "unexpected-control-baton.txt", "hostile scope\n")
        baton_paths.append("unexpected-control-baton.txt")
    baton_commit = _commit(repo, "generation fifteen control baton", *baton_paths)
    return state_commit, baton_commit


def _lifecycle_control_publication(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    extra_source_path: bool = False,
) -> tuple[str, str, str, str, str]:
    """Build a compact exact B15 -> F16 -> R16 -> T16 -> B16 topology."""

    _git(repo, "init", "-b", "master")
    _git(repo, "config", "user.name", "Sentinel Test")
    _git(repo, "config", "user.email", "sentinel-test@example.invalid")
    _write(repo, auth.MISSION_REL, auth._control_hardening_expected_state())
    _write(repo, "CONTINUITY.md", "accepted generation fifteen control baton\n")
    _write(repo, "HANDOFF.md", "Lifecycle state: UNKNOWN\n")
    b15 = _commit(
        repo,
        "accepted generation fifteen control baton",
        auth.MISSION_REL,
        "CONTINUITY.md",
        "HANDOFF.md",
    )
    monkeypatch.setattr(auth, "GENERATION_FIFTEEN_BATON_COMMIT", b15)
    monkeypatch.setattr(auth, "_frozen_generation_fifteen_problems", lambda _repo: [])

    source_paths = list(auth.GENERATION_SIXTEEN_SOURCE_COMMIT_PATHS)
    for relative in source_paths:
        _write(repo, relative, f"generation sixteen source: {relative}\n")
    if extra_source_path:
        source_paths.append("unexpected-generation-sixteen-source.txt")
        _write(repo, source_paths[-1], "hostile source-scope expansion\n")
    f16 = _commit(repo, "generation sixteen lifecycle-control source", *source_paths)

    _write(repo, auth.TOOLING_RECEIPT_REL, {"generation": 16})
    r16 = _commit(
        repo,
        "generation sixteen tooling receipt",
        auth.TOOLING_RECEIPT_REL,
    )
    _write(repo, auth.MISSION_REL, auth._ci_hardening_expected_state())
    t16 = _commit(repo, "generation sixteen CI hardening state", auth.MISSION_REL)
    _write(repo, "CONTINUITY.md", "generation sixteen lifecycle-control baton\n")
    _write(repo, "HANDOFF.md", "Lifecycle state: UNKNOWN\n")
    b16 = _commit(
        repo,
        "generation sixteen lifecycle-control baton",
        "CONTINUITY.md",
        "HANDOFF.md",
    )
    return b15, f16, r16, t16, b16


def test_control_hardening_state_mirror_matches_canonical_state_contract() -> None:
    canonical = json.loads((REPO / auth.MISSION_REL).read_text())
    canonical["run_state"] = "UNKNOWN"
    canonical["next_program"] = {
        "iteration": 135,
        "name": "semantics-free placebo dose-response causal closure",
        "phase": auth.CONTROL_HARDENING_PHASE,
        "authorized_actions": list(auth.CONTROL_HARDENING_AUTHORIZED_ACTIONS),
        "forbidden_actions": list(auth.CONTROL_HARDENING_FORBIDDEN_ACTIONS),
    }

    assert auth._exact_json_value(
        auth._control_hardening_expected_state(),
        canonical,
    )


def test_generation_sixteen_declares_the_exact_seventeen_path_f16_scope() -> None:
    assert auth.GENERATION_SIXTEEN_SOURCE_COMMIT_PATHS == (
        "CONTINUITY.md",
        "HANDOFF.md",
        "README.md",
        "docs/NEXT_PHASE.md",
        "docs/REPORT.md",
        "docs/research/ITER135_SOURCE_BOUND_LIFECYCLE_CONTROL_PREREGISTRATION_2026-07-21.md",
        f"{auth.EXPERIMENT_REL}/authorize_launch135.py",
        f"{auth.EXPERIMENT_REL}/validate_lifecycle135.py",
        f"{auth.EXPERIMENT_REL}/verify_tooling135.py",
        "scripts/make_handoff.py",
        "scripts/mission_state.py",
        "tests/test_handoff_generator.py",
        "tests/test_iter131_post_iter130_mission_alignment_audit.py",
        "tests/test_iter135_launch_authorization.py",
        "tests/test_iter135_lifecycle_control.py",
        "tests/test_iter135_tooling_verifier.py",
        "tests/test_mission_state.py",
    )


def test_lifecycle_control_baton_accepts_only_exact_f16_r16_t16_b16_topology(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _b15, _f16, r16, _t16, b16 = _lifecycle_control_publication(
        tmp_path,
        monkeypatch,
    )

    assert auth._ci_hardening_baton_problems(
        tmp_path,
        tooling_receipt_commit=r16,
        tooling_baton_commit=b16,
    ) == []


def test_lifecycle_control_baton_rejects_f16_scope_expansion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _b15, _f16, r16, _t16, b16 = _lifecycle_control_publication(
        tmp_path,
        monkeypatch,
        extra_source_path=True,
    )

    assert "authorization:lifecycle-control-source-scope" in (
        auth._ci_hardening_baton_problems(
            tmp_path,
            tooling_receipt_commit=r16,
            tooling_baton_commit=b16,
        )
    )


@pytest.mark.parametrize(
    ("upstream", "expected_status", "expected_problems"),
    [
        ("r16", auth.LIFECYCLE_CONTROL_PUBLICATION_CANDIDATE_STATUS, []),
        ("b16", auth.LIFECYCLE_CONTROL_PUBLICATION_PUBLISHED_STATUS, []),
        (
            "t16",
            auth.LIFECYCLE_CONTROL_PUBLICATION_INVALID_UPSTREAM_STATUS,
            ["authorization:lifecycle-control-origin-master-not-r16-or-b16"],
        ),
    ],
)
def test_ci_hardening_publication_is_always_non_authoritative(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    upstream: str,
    expected_status: str,
    expected_problems: list[str],
) -> None:
    _b15, _f16, r16, t16, b16 = _lifecycle_control_publication(
        tmp_path,
        monkeypatch,
    )
    monkeypatch.setattr(auth, "_deep_replay_publication", lambda *_args, **_kwargs: [])
    upstream_commit = {"r16": r16, "t16": t16, "b16": b16}[upstream]

    result = auth.validate_publication_descendants(
        tmp_path,
        phase=auth.CI_HARDENING_PHASE,
        tooling_receipt_commit=r16,
        tooling_baton_commit=b16,
        descendants=[],
        upstream_commit=upstream_commit,
    )

    assert result == {
        "problems": expected_problems,
        "references": {},
        "authority": "none",
        "launch_authorized": False,
        "lifecycle_control_publication_status": expected_status,
    }


def _validate(
    repo: Path,
    commits: dict[str, str],
    *,
    phase: str = auth.LAUNCH_PHASE,
    upstream_commit: str | None = None,
) -> dict:
    descendants = _descendants(commits)
    if phase == auth.TOOLING_PHASE:
        descendants = descendants[:4]
    return auth.validate_publication_descendants(
        repo,
        phase=phase,
        tooling_receipt_commit=commits["tooling_receipt"],
        tooling_baton_commit=commits["tooling_baton"],
        descendants=descendants,
        upstream_commit=upstream_commit or commits["activation"],
    )


def test_true_recomputed_h_e_p_s_a_f_b_chain_is_launch_authority(tmp_path: Path) -> None:
    repo, commits = _publication(tmp_path)

    result = _validate(repo, commits)

    assert result["problems"] == []
    assert result["launch_authorized"] is True
    assert result["authority"] == "origin-published"
    assert result["references"][auth.MISSION_REL] == commits["state"]


@pytest.mark.parametrize(
    ("upstream_name", "expected_status"),
    [
        ("r15", auth.CONTROL_PUBLICATION_CANDIDATE_STATUS),
        ("b15", auth.CONTROL_PUBLICATION_PUBLISHED_STATUS),
    ],
)
def test_control_hardening_accepts_exact_non_authoritative_candidate_and_baton(
    tmp_path: Path,
    upstream_name: str,
    expected_status: str,
) -> None:
    repo, commits = _publication(tmp_path)
    _state, baton = _control_publication(repo, commits)
    upstream = commits["tooling_receipt"] if upstream_name == "r15" else baton

    result = auth.validate_publication_descendants(
        repo,
        phase=auth.CONTROL_HARDENING_PHASE,
        tooling_receipt_commit=commits["tooling_receipt"],
        tooling_baton_commit=baton,
        descendants=[],
        upstream_commit=upstream,
    )

    assert result == {
        "problems": [],
        "references": {},
        "authority": "none",
        "launch_authorized": False,
        "control_publication_status": expected_status,
    }


@pytest.mark.parametrize(
    ("descendants", "candidate", "upstream", "problem"),
    [
        (["f" * 40], False, "BATON", "authorization:control-hardening-descendant-count:1"),
        ([], True, "BATON", "authorization:control-hardening-candidate"),
    ],
)
def test_control_hardening_rejects_descendant_and_explicit_candidate_modes(
    tmp_path: Path,
    descendants: list[str],
    candidate: bool,
    upstream: str,
    problem: str,
) -> None:
    repo, commits = _publication(tmp_path)
    _state, baton = _control_publication(repo, commits)

    result = auth.validate_publication_descendants(
        repo,
        phase=auth.CONTROL_HARDENING_PHASE,
        tooling_receipt_commit=commits["tooling_receipt"],
        tooling_baton_commit=baton,
        descendants=descendants,
        upstream_commit=baton if upstream == "BATON" else upstream,
        candidate=candidate,
    )

    assert problem in result["problems"]
    assert result["authority"] == "none"
    assert result["launch_authorized"] is False
    assert (
        result["control_publication_status"]
        == auth.CONTROL_PUBLICATION_PUBLISHED_STATUS
    )
    assert set(result) == {
        "problems",
        "references",
        "authority",
        "launch_authorized",
        "control_publication_status",
    }


@pytest.mark.parametrize(
    "mutation",
    [
        "minimal",
        "extra-field",
        "numeric-current-iteration",
        "numeric-storage",
        "numeric-workspace-boolean",
        "numeric-next-iteration",
    ],
)
def test_control_hardening_rejects_nonexact_t15_state(
    tmp_path: Path,
    mutation: str,
) -> None:
    repo, commits = _publication(tmp_path)
    state = auth._control_hardening_expected_state()
    if mutation == "minimal":
        state = {
            "schema": "sentinel.mission_state.v1",
            "run_state": "UNKNOWN",
            "next_program": state["next_program"],
        }
    elif mutation == "extra-field":
        state["launch_authorized"] = False
    elif mutation == "numeric-current-iteration":
        state["current_completed_iteration"] = 134.0
    elif mutation == "numeric-storage":
        state["storage_gate"]["minimum_local_free_gib_before_new_proof_collection"] = (
            15.0
        )
    elif mutation == "numeric-workspace-boolean":
        state["workspace_boundary"][
            "cross_workspace_access_requires_explicit_operator_request"
        ] = 1
    elif mutation == "numeric-next-iteration":
        state["next_program"]["iteration"] = 135.0
    else:
        raise AssertionError(f"unsupported control-state mutation: {mutation}")
    _state, baton = _control_publication(repo, commits, state=state)

    result = auth.validate_publication_descendants(
        repo,
        phase=auth.CONTROL_HARDENING_PHASE,
        tooling_receipt_commit=commits["tooling_receipt"],
        tooling_baton_commit=baton,
        descendants=[],
        upstream_commit=baton,
    )

    assert "authorization:control-hardening-state-contract" in result["problems"]
    assert result["launch_authorized"] is False


@pytest.mark.parametrize(
    "upstream_name",
    ["t15", "b14", "source", "advanced", "unrelated"],
)
def test_control_hardening_rejects_every_non_r15_non_b15_upstream_exactly(
    tmp_path: Path,
    upstream_name: str,
) -> None:
    repo, commits = _publication(tmp_path)
    state_commit, baton = _control_publication(repo, commits)
    invalid_upstreams = {
        "t15": state_commit,
        "b14": auth.GENERATION_FOURTEEN_BATON_COMMIT,
        "source": commits["source"],
        "unrelated": "f" * 40,
    }
    if upstream_name == "advanced":
        _git(repo, "commit", "--allow-empty", "-m", "unreviewed post-B15 advancement")
        invalid_upstreams["advanced"] = _git(repo, "rev-parse", "HEAD").decode().strip()

    result = auth.validate_publication_descendants(
        repo,
        phase=auth.CONTROL_HARDENING_PHASE,
        tooling_receipt_commit=commits["tooling_receipt"],
        tooling_baton_commit=baton,
        descendants=[],
        upstream_commit=invalid_upstreams[upstream_name],
    )

    assert result == {
        "problems": [
            "authorization:control-hardening-origin-master-not-r15-or-b15"
        ],
        "references": {},
        "authority": "none",
        "launch_authorized": False,
        "control_publication_status": (
            auth.CONTROL_PUBLICATION_INVALID_UPSTREAM_STATUS
        ),
    }


def test_control_hardening_rejects_tampered_r15_receipt_through_frozen_replay(
    tmp_path: Path,
) -> None:
    repo, commits = _publication(
        tmp_path,
        tooling_publication_overrides={"reason_code": "TAMPERED_R15"},
    )
    _state, baton = _control_publication(repo, commits)

    result = auth.validate_publication_descendants(
        repo,
        phase=auth.CONTROL_HARDENING_PHASE,
        tooling_receipt_commit=commits["tooling_receipt"],
        tooling_baton_commit=baton,
        descendants=[],
        upstream_commit=baton,
    )

    assert any(
        problem.startswith("authorization:frozen-source:AuthorizationError:")
        for problem in result["problems"]
    )
    assert result["launch_authorized"] is False


def test_control_hardening_rejects_receipt_reparented_to_tampered_f15_source(
    tmp_path: Path,
) -> None:
    repo, commits = _publication(tmp_path)
    original_receipt = _git(
        repo,
        "show",
        f"{commits['tooling_receipt']}:{auth.TOOLING_RECEIPT_REL}",
    )
    _git(repo, "checkout", "--detach", commits["source"])
    _write(repo, "tampered-source.txt", "unreviewed source descendant\n")
    _commit(repo, "tampered generation fifteen source", "tampered-source.txt")
    _write(repo, auth.TOOLING_RECEIPT_REL, original_receipt)
    tampered_receipt = _commit(
        repo,
        "receipt reparented to tampered source",
        auth.TOOLING_RECEIPT_REL,
    )
    _state, baton = _control_publication(
        repo,
        commits,
        receipt_commit=tampered_receipt,
    )

    result = auth.validate_publication_descendants(
        repo,
        phase=auth.CONTROL_HARDENING_PHASE,
        tooling_receipt_commit=tampered_receipt,
        tooling_baton_commit=baton,
        descendants=[],
        upstream_commit=baton,
    )

    assert any(
        problem.startswith("authorization:frozen-source:AuthorizationError:")
        for problem in result["problems"]
    )
    assert result["launch_authorized"] is False


def test_control_hardening_rejects_malformed_t15_b15_topology(
    tmp_path: Path,
) -> None:
    repo, commits = _publication(tmp_path)
    _state, baton = _control_publication(repo, commits, baton_extra_path=True)

    result = auth.validate_publication_descendants(
        repo,
        phase=auth.CONTROL_HARDENING_PHASE,
        tooling_receipt_commit=commits["tooling_receipt"],
        tooling_baton_commit=baton,
        descendants=[],
        upstream_commit=baton,
    )

    assert "authorization:control-hardening-baton-scope" in result["problems"]
    assert result["launch_authorized"] is False


@pytest.mark.parametrize(
    "payload",
    [b'{"schema":"green","schema":"red"}', b'{"value":NaN}'],
)
def test_authority_json_parser_rejects_ambiguous_or_nonfinite_claims(payload: bytes) -> None:
    with pytest.raises(auth.AuthorizationError):
        auth._strict_json_object(payload, "hostile.json")


@pytest.mark.parametrize("mutation", ["oid", "mode", "extra", "missing"])
def test_publication_authority_rejects_nonexact_artifact_identity(mutation: str) -> None:
    commit = "a" * 40
    expected = [_authority_artifact(auth.HOST_REL, b"host receipt\n")]
    authority = _publication_authority(commit, copy.deepcopy(expected))
    row = authority["artifacts"][0]
    if mutation == "oid":
        row["git_blob_oid"] = "not-a-git-object"
    elif mutation == "mode":
        row["git_mode"] = "100777"
    elif mutation == "extra":
        row["unexpected"] = True
    else:
        row.pop("git_mode")

    problems = auth._validate_publication_authority(
        authority,
        expected_commit=commit,
        expected_artifacts=expected,
        label="hostile-authority",
    )

    assert "hostile-authority:artifacts" in problems


@pytest.mark.parametrize("mutation", ["extra", "missing"])
def test_controller_rejects_nonexact_tooling_receipt_root_before_preflight_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    repo, commits = _publication(
        tmp_path,
        tooling_receipt_root_mutation=mutation,
    )

    def replay_must_not_start(*_args, **_kwargs):
        pytest.fail("preflight replay started after a nonexact tooling receipt root")

    monkeypatch.setattr(auth, "_module_from_checkout", replay_must_not_start)

    with pytest.raises(auth.AuthorizationError, match="root field set is not exact"):
        auth._tooling_source_commit(repo, commits["tooling_receipt"])


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("generation", 14),
        ("generation", 15.0),
        ("supersedes_receipt_commit", "0" * 40),
        ("recovery_parent", "1" * 40),
        ("reason_code", "UNREGISTERED_GENERATION_FIFTEEN_REASON"),
    ),
)
def test_controller_requires_exact_generation_fifteen_tooling_publication(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    repo, commits = _publication(
        tmp_path,
        tooling_publication_overrides={field: value},
    )

    with pytest.raises(
        auth.AuthorizationError,
        match="exact green generation-fifteen source",
    ):
        auth._tooling_source_commit(repo, commits["tooling_receipt"])


def test_controller_propagates_frozen_generation_history_rejection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commits = _publication(tmp_path)

    def hostile_history_validator(_receipt, *, repo_root):
        assert repo_root == repo
        return [
            "canonical receipt history is not exact generation-four, generation-three, "
            "generation-two, then generation-one"
        ]

    monkeypatch.setattr(
        auth,
        "_load_frozen_tooling_receipt_validator",
        lambda _repo, _source: hostile_history_validator,
    )

    with pytest.raises(auth.AuthorizationError, match="receipt history is not exact"):
        auth._tooling_source_commit(repo, commits["tooling_receipt"])


def test_controller_routes_nested_tooling_receipt_to_frozen_validator_before_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, commits = _publication(
        tmp_path,
        tooling_receipt_nested_mutation=True,
    )

    def replay_must_not_start(*_args, **_kwargs):
        pytest.fail("preflight replay started after frozen tooling receipt rejection")

    monkeypatch.setattr(auth, "_module_from_checkout", replay_must_not_start)

    with pytest.raises(auth.AuthorizationError, match="nested receipt invalid"):
        auth._tooling_source_commit(repo, commits["tooling_receipt"])


@pytest.mark.parametrize("count", [0, 1, 2, 3, 4])
def test_tooling_phase_accepts_only_deeply_replayed_preflight_prefix(
    tmp_path: Path, count: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, commits = _publication(tmp_path)
    # The full positive lifecycle above exercises every deep replay stage.  This matrix isolates
    # the prefix-count/topology controller without paying for five redundant local clones.
    monkeypatch.setattr(auth, "_deep_replay_publication", lambda *args, **kwargs: [])
    descendants = _descendants(commits)[:count]
    upstream = commits["tooling_baton"] if not descendants else descendants[-1]
    _git(repo, "checkout", "--detach", upstream)

    result = auth.validate_publication_descendants(
        repo,
        phase=auth.TOOLING_PHASE,
        tooling_receipt_commit=commits["tooling_receipt"],
        tooling_baton_commit=commits["tooling_baton"],
        descendants=descendants,
        upstream_commit=upstream,
    )

    assert result["problems"] == []
    assert result["launch_authorized"] is False


def test_launch_rejects_missing_activation_baton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, commits = _publication(tmp_path)
    monkeypatch.setattr(auth, "_deep_replay_publication", lambda *args, **kwargs: [])
    result = auth.validate_publication_descendants(
        repo,
        phase=auth.LAUNCH_PHASE,
        tooling_receipt_commit=commits["tooling_receipt"],
        tooling_baton_commit=commits["tooling_baton"],
        descendants=_descendants(commits)[:-1],
        upstream_commit=commits["activation"],
    )
    assert "authorization:launch-descendant-count:6" in result["problems"]


def test_launch_rejects_unpublished_activation_baton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, commits = _publication(tmp_path, publish_activation=False)
    monkeypatch.setattr(auth, "_deep_replay_publication", lambda *args, **kwargs: [])

    result = _validate(repo, commits, upstream_commit=commits["smoke"])

    assert "authorization:head-not-on-origin-master" in result["problems"]
    assert result["launch_authorized"] is False


@pytest.mark.parametrize(
    "activation_numeric_alias",
    ["problem-count-bool", "artifact-bytes-float"],
)
def test_launch_rejects_activation_numeric_json_aliases(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    activation_numeric_alias: str,
) -> None:
    repo, commits = _publication(
        tmp_path,
        activation_numeric_alias=activation_numeric_alias,
    )
    monkeypatch.setattr(auth, "_deep_replay_publication", lambda *args, **kwargs: [])

    result = _validate(repo, commits)

    assert "authorization:activation-receipt" in result["problems"]
    assert result["launch_authorized"] is False


def test_launch_rejects_origin_advanced_beyond_exact_activation_tip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, commits = _publication(tmp_path)
    monkeypatch.setattr(auth, "_deep_replay_publication", lambda *args, **kwargs: [])
    _git(repo, "commit", "--allow-empty", "-m", "unreviewed origin advancement")
    advanced = _git(repo, "rev-parse", "HEAD").decode().strip()

    result = _validate(repo, commits, upstream_commit=advanced)

    assert "authorization:head-not-on-origin-master" in result["problems"]
    assert result["launch_authorized"] is False


def test_complete_clean_local_candidate_is_explicitly_non_authoritative(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, commits = _publication(tmp_path, publish_activation=False)
    monkeypatch.setattr(auth, "_deep_replay_publication", lambda *args, **kwargs: [])

    result = auth.validate_local_candidate(
        repo,
        tooling_receipt_commit=commits["tooling_receipt"],
        tooling_baton_commit=commits["tooling_baton"],
        descendants=_descendants(commits),
        upstream_commit=commits["smoke"],
    )

    assert result["candidate_valid"] is True
    assert result["launch_authorized"] is False
    assert result["authority"] == "non-authoritative-local-candidate"
    assert result["problems"] == ["authorization:candidate-non-authoritative"]


def test_local_candidate_rejects_origin_advanced_beyond_exact_smoke_tip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, commits = _publication(tmp_path, publish_activation=False)
    monkeypatch.setattr(auth, "_deep_replay_publication", lambda *args, **kwargs: [])

    result = auth.validate_local_candidate(
        repo,
        tooling_receipt_commit=commits["tooling_receipt"],
        tooling_baton_commit=commits["tooling_baton"],
        descendants=_descendants(commits),
        # B is a descendant of S, so the former ancestor-only rule accepted it.
        upstream_commit=commits["activation"],
    )

    assert result["candidate_valid"] is False
    assert result["launch_authorized"] is False
    assert result["authority"] == "non-authoritative-local-candidate"
    assert "authorization:preflight-not-on-origin-master" in result["problems"]


@pytest.mark.parametrize(
    ("fixture_kwargs", "expected_problem"),
    [
        (
            {"tamper_raw_decision_after_receipt": True},
            "smoke:receipt-recomputation-mismatch",
        ),
        (
            {"tamper_final_state_binding": True},
            "final-manifest:exact-rebuild-mismatch",
        ),
        ({"tamper_host_actions": True}, "host:actions"),
        (
            {"tamper_host_authority_artifacts": True},
            "host:publication-authority:artifacts",
        ),
        (
            {"tamper_environment_deep": True},
            "environment:validator:deep-environment",
        ),
    ],
)
def test_launch_rejects_handcrafted_shallow_green_evidence(
    tmp_path: Path, fixture_kwargs: dict, expected_problem: str
) -> None:
    repo, commits = _publication(tmp_path, **fixture_kwargs)

    result = _validate(repo, commits)

    assert expected_problem in result["problems"]
    assert result["launch_authorized"] is False


@pytest.mark.parametrize(
    "environment_host_evidence_numeric_alias",
    ["problem-count-bool", "storage-device-float"],
)
def test_launch_rejects_environment_host_evidence_numeric_json_aliases(
    tmp_path: Path,
    environment_host_evidence_numeric_alias: str,
) -> None:
    repo, commits = _publication(
        tmp_path,
        environment_host_evidence_numeric_alias=(
            environment_host_evidence_numeric_alias
        ),
    )

    result = _validate(repo, commits)

    assert "environment:host-preparation-deep-link" in result["problems"]
    assert result["launch_authorized"] is False


@pytest.mark.parametrize(
    ("host_exactness_mutation", "expected_problem"),
    [
        ("compose-patcher-bytes-float", "host:compose-patcher"),
        ("compose-patcher-bytes-bool", "host:compose-patcher"),
        ("storage-extra", "host:storage-field-set"),
        ("storage-missing", "host:storage-field-set"),
        ("storage-device-float", "host:storage-device"),
        ("storage-device-negative", "host:storage-device"),
        ("action-extra", "host:actions"),
        ("action-omission", "host:actions"),
        ("invocation-extra", "host:invocation"),
        ("invocation-omission", "host:invocation"),
        ("invocation-environment-alias", "host:invocation"),
    ],
)
def test_launch_rejects_recursive_host_receipt_aliases_and_schema_drift(
    tmp_path: Path,
    host_exactness_mutation: str,
    expected_problem: str,
) -> None:
    repo, commits = _publication(
        tmp_path,
        host_exactness_mutation=host_exactness_mutation,
    )

    result = _validate(repo, commits)

    assert expected_problem in result["problems"]
    assert result["launch_authorized"] is False


@pytest.mark.parametrize(
    ("fixture_kwargs", "expected_problem"),
    [
        ({"tamper_raw_manifest": True}, "smoke:pre-manifest-link"),
        ({"tamper_activation": True}, "authorization:activation-receipt"),
        ({"tamper_host_packet_binding": True}, "host:packet-manifest-binding"),
        ({"tamper_host_packet_source": True}, "host:packet-manifest-binding"),
    ],
)
def test_structural_controller_rejects_bound_artifact_drift_without_replay_cost(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fixture_kwargs: dict,
    expected_problem: str,
) -> None:
    repo, commits = _publication(tmp_path, **fixture_kwargs)
    monkeypatch.setattr(auth, "_deep_replay_publication", lambda *args, **kwargs: [])

    result = _validate(repo, commits)

    assert expected_problem in result["problems"]
    assert result["launch_authorized"] is False


def test_replay_checkout_uses_dedicated_bound_and_probes_stay_at_ten_seconds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The generation-eight amendment: materializing the multi-gibibyte replay tree gets its own
    hard six-hundred-second ceiling, while every other Git probe keeps the ten-second bound."""

    assert auth.REPLAY_CHECKOUT_TIMEOUT_SECONDS == 600

    commit = "a" * 40
    observed: list[tuple[tuple[str, ...], object]] = []

    def recording_run(argv: tuple[str, ...], **kwargs: object) -> types.SimpleNamespace:
        observed.append((tuple(argv), kwargs.get("timeout")))
        return types.SimpleNamespace(returncode=0, stdout=commit.encode() + b"\n")

    monkeypatch.setattr(auth.subprocess, "run", recording_run)
    auth._checkout(tmp_path, tmp_path, commit)

    checkout_calls = [row for row in observed if "checkout" in row[0]]
    probe_calls = [row for row in observed if "rev-parse" in row[0]]
    assert len(checkout_calls) == 1
    assert checkout_calls[0][1] == auth.REPLAY_CHECKOUT_TIMEOUT_SECONDS
    assert len(probe_calls) == 1
    assert probe_calls[0][1] == 10


def test_replay_checkout_timeout_still_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A checkout that exceeds even the dedicated bound must still raise, never hang or pass."""

    def timing_out_run(argv: tuple[str, ...], **kwargs: object) -> types.SimpleNamespace:
        raise subprocess.TimeoutExpired(argv, kwargs.get("timeout"))

    monkeypatch.setattr(auth.subprocess, "run", timing_out_run)
    with pytest.raises(subprocess.TimeoutExpired):
        auth._checkout(tmp_path, tmp_path, "a" * 40)


def test_deep_replay_pins_origin_master_to_stage_parent_before_manifest_rebuilds() -> None:
    """Generation-thirteen regression guard: the pre-smoke (P) and final (F) manifest rebuilds
    in the deep replay must pin the isolated checkout's origin/master back to the stage parent
    BEFORE invoking the frozen manifest builder, so the builder's tooling-receipt gate sees the
    ref state the manifest was generated under instead of the advanced replay tip. The fixtures
    stub the tooling verifier, so this source-level check is the guard that keeps the pin in
    place; without it a true green P/F can never match its rebuild (origin/master would be a
    descendant, not an ancestor, of the stage-parent checkout)."""

    source = MODULE_PATH.read_text(encoding="utf-8")

    # Pre-smoke (P) rebuild: checkout commits[1], then pin origin/master to commits[1].
    p_marker = 'observed_p = _observed_git_provenance('
    p_region = source[: source.index(p_marker)]
    p_checkout = p_region.rindex("_checkout(repo, checkout, commits[1])")
    p_pin = p_region.rindex(
        '_git(checkout, "update-ref", "refs/remotes/origin/master", commits[1])'
    )
    assert p_checkout < p_pin, "P rebuild must pin origin/master after checkout, before builder"

    # Final (F) rebuild: checkout commits[4], then pin origin/master to commits[4].
    f_marker = 'observed_f = _observed_git_provenance('
    f_region = source[: source.index(f_marker)]
    f_checkout = f_region.rindex("_checkout(repo, checkout, commits[4])")
    f_pin = f_region.rindex(
        '_git(checkout, "update-ref", "refs/remotes/origin/master", commits[4])'
    )
    assert f_checkout < f_pin, "F rebuild must pin origin/master after checkout, before builder"
