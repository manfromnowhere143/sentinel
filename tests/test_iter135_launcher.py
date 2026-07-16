from __future__ import annotations

import base64
import contextlib
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = (
    ROOT
    / "experiments"
    / "iter135_neuroncap_blind_braking_dose_response"
    / "run_dose135.sh"
)
SMOKE_LAUNCHER = LAUNCHER.with_name("run_smoke135.sh")


def bootstrap_program(source: Path, expected_cwd: Path) -> str:
    prefix = source.read_text().split("export PATH=$CANONICAL_PATH", 1)[0]
    return prefix.replace("/opt/sentinel-stack/iter135", str(expected_cwd)) + "exit 0\n"


def embedded_docker_wrapper() -> str:
    text = LAUNCHER.read_text()
    marker = "payload = r'''"
    return text.split(marker, 1)[1].split("\n'''", 1)[0]


def executing_runner_binding_program() -> str:
    text = LAUNCHER.read_text()
    marker = 'EXECUTING_RUNNER_RECEIPT=$(python3 - "$RUNNER_SOURCE" "${BASH_SOURCE[0]}" <<\'PY\'\n'
    return text.split(marker, 1)[1].split("\nPY\n) ||", 1)[0]


def shell_function(name: str, next_name: str) -> str:
    text = LAUNCHER.read_text()
    start = text.index(f"{name}() {{")
    end = text.index(f"\n\n{next_name}() {{", start)
    return text[start:end]


def container_receipt_rows_program() -> str:
    text = LAUNCHER.read_text()
    marker = (
        'container_receipt_rows() {\n'
        '  python3 - "$CURRENT_BLOCK_CID_DIR" "$CURRENT_BLOCK_ORDINAL" <<\'PY\'\n'
    )
    return text.split(marker, 1)[1].split("\nPY\n}", 1)[0]


def stable_dataset_file_program() -> str:
    text = LAUNCHER.read_text()
    start = text.index("def stable_dataset_file(")
    end = text.index("\n\n\ndataset_root = Path", start)
    return (
        "import hashlib\n"
        "import os\n"
        "import stat\n"
        "from pathlib import Path\n\n"
        + text[start:end]
    )


def current_mission_state_program() -> str:
    text = LAUNCHER.read_text()
    start = text.index("verify_current_mission_state() {")
    block = text[start : text.index("\n\ncleanup_containers() {", start)]
    return block.split("<<'PY'\n", 1)[1].split("\nPY\n}", 1)[0]


def launch_activation_program() -> str:
    text = LAUNCHER.read_text()
    start = text.index("verify_launch_activation() {")
    block = text[start : text.index("\n\ncleanup_containers() {", start)]
    return block.split("<<'PY'\n", 1)[1].split("\nPY\n}", 1)[0]


def tooling_publication_contract_namespace() -> dict[str, object]:
    text = LAUNCHER.read_text()
    program = text.split("# BEGIN I135_TOOLING_PUBLICATION_CONTRACT_PYTHON\n", 1)[
        1
    ].split("# END I135_TOOLING_PUBLICATION_CONTRACT_PYTHON", 1)[0]
    namespace: dict[str, object] = {"oid": re.compile(r"^[0-9a-f]{40}$")}
    exec(compile(program, str(LAUNCHER), "exec"), namespace)
    return namespace


def analytic_lock_publisher_program() -> str:
    text = LAUNCHER.read_text()
    start = text.index("publish_analytic_lock() {")
    block = text[start : text.index("\n\nFINAL_ARM_CONTAINER_IDS=", start)]
    return block.split("<<'PY'\n", 1)[1].split("\nPY\n}", 1)[0]


def github_launch_authority_namespace() -> dict[str, object]:
    text = LAUNCHER.read_text()
    program = text.split("# BEGIN I135_GITHUB_LAUNCH_AUTHORITY_PYTHON\n", 1)[1].split(
        "# END I135_GITHUB_LAUNCH_AUTHORITY_PYTHON", 1
    )[0]
    namespace: dict[str, object] = {"__name__": "iter135_github_launch_authority_test"}
    exec(compile(program, str(LAUNCHER), "exec"), namespace)
    return namespace


def docker_runtime_program() -> str:
    text = LAUNCHER.read_text()
    return text.split("# BEGIN I135_DOCKER_RUNTIME_PYTHON\n", 1)[1].split(
        "# END I135_DOCKER_RUNTIME_PYTHON", 1
    )[0]


def launch_authorized_state() -> dict:
    return {
        "schema": "sentinel.mission_state.v1",
        "canonical_repository": "/Users/danielwahnich/workspace/sentinel",
        "workspace_boundary": {
            "isolated_from": "/Users/danielwahnich/workspace/aweb",
            "recovery_sources": ["MISSION_STATE.json", "CONTINUITY.md", "HANDOFF.md"],
            "cross_workspace_access_requires_explicit_operator_request": True,
        },
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
        "next_program": {
            "iteration": 135,
            "name": "semantics-free placebo dose-response causal closure",
            "phase": "LAUNCH_AUTHORIZED",
            "authorized_actions": [
                "launch the exact hash-bound iteration-135 analytic manifest once on sentinel-gpu",
                (
                    "collect and commit raw proof after the single launch terminates, whether "
                    "done or aborted"
                ),
                (
                    "publish partial evidence and PLACEBO_DOSE_INFRA_NULL after any aborted "
                    "analytic launch"
                ),
            ],
            "forbidden_actions": [
                (
                    "relaunch or retry any iteration-135 analytic block after the first analytic "
                    "block starts"
                ),
                (
                    "run with any manifest, payload, environment, smoke, repository, image, GPU, "
                    "storage, or idle-state drift"
                ),
                "run the analyzer before raw proof is committed",
            ],
        },
        "claim_state": {
            "neuroncap_union_gain": "ESTABLISHED_ON_NEURONCAP",
            "semantic_attribution": "UNRESOLVED",
            "hugsim_transfer": "TRANSFER_NULL",
            "production_readiness": "NOT_ESTABLISHED",
        },
        "deprecated_pending_hypotheses": [
            "experiments/iter38_track_query_opposite_direction/HYPOTHESIS.md"
        ],
        "paper_state": {
            "status": "ARCHIVED_NOT_SUBMISSION_READY",
            "next_route": "peer-reviewed venue after a full evidence rewrite",
            "blocking_omissions": [
                "HUGSIM transfer null",
                "iteration-134 placebo result",
                "resolved wording for the decoder universal-negative overclaim",
            ],
        },
        "storage_gate": {
            "minimum_local_free_gib_before_new_proof_collection": 15,
            "remote_execution_filesystem_path": "/datasets/nuscenes-full",
            "analytic_output_root": "/datasets/nuscenes-full/sentinel-i135-outoutput",
            "minimum_remote_execution_filesystem_free_gib_before_gpu_launch": 100,
            "minimum_remote_execution_filesystem_reserve_gib_after_projected_output": 25,
            "policy": (
                "preserve committed proof and hashes; delete only hash-verified duplicates, "
                "reproducible renders, and caches"
            ),
        },
    }


def write_state_authority(tmp_path: Path, state: dict) -> tuple[Path, Path, str]:
    state_path = tmp_path / "MISSION_STATE.json"
    state_payload = (json.dumps(state, sort_keys=True) + "\n").encode()
    state_path.write_bytes(state_payload)
    manifest = {
        "schema": "iter135.launch_manifest.v2",
        "verdict": "I135_TOOLING_MANIFEST_OK",
        "launch_authorized": True,
        "mission_phase": "LAUNCH_AUTHORIZED",
        "mission_state": {
            "source_path": "MISSION_STATE.json",
            "sha256": hashlib.sha256(state_payload).hexdigest(),
            "bytes": len(state_payload),
        },
    }
    manifest_path = tmp_path / "launch_manifest.json"
    manifest_payload = (json.dumps(manifest, sort_keys=True) + "\n").encode()
    manifest_path.write_bytes(manifest_payload)
    return state_path, manifest_path, hashlib.sha256(manifest_payload).hexdigest()


def run_state_authority_check(
    state_path: Path,
    manifest_path: Path,
    manifest_sha: str,
    pinned_descriptor: int,
    *,
    expected_identity: str = "",
    expected_sha: str = "",
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-",
            str(state_path),
            str(manifest_path),
            manifest_sha,
            f"/dev/fd/{pinned_descriptor}",
            expected_identity,
            expected_sha,
        ],
        input=current_mission_state_program(),
        text=True,
        check=False,
        capture_output=True,
        pass_fds=(pinned_descriptor,),
    )


def test_launcher_is_shell_syntax_valid() -> None:
    subprocess.run(["bash", "-n", str(LAUNCHER)], check=True)


def test_launcher_binds_and_rechecks_current_mission_authority_before_execution() -> None:
    text = LAUNCHER.read_text()
    final_state_check = (
        'verify_current_mission_state >/dev/null \\\n'
        '  || abort "mission-state-revoked-at-final-analytic-arm"'
    )
    block_state_check = (
        'verify_current_mission_state >/dev/null \\\n'
        '    || abort "mission-state-revoked-before-block:$ORDINAL"'
    )
    loop = text[text.index("while IFS=$'\\t' read -r ORDINAL") :]

    assert "MISSION_STATE_SOURCE=$I135/MISSION_STATE.json" in text
    assert 'exec 6< "$MISSION_STATE_SOURCE"' in text
    assert '"/proc/$$/fd/6"' in text
    assert 'exec 6>&- || true' in text
    assert "deployed mission state is not the launch manifest's bound current state" in text
    assert 'state.get("workspace_boundary") != expected_workspace_boundary' in text
    assert 'state.get("run_state") != "IDLE"' in text
    assert '"phase": "LAUNCH_AUTHORIZED"' in text
    assert text.index(final_state_check) < text.index(
        "ANALYTIC_LOCK_ID=$(publish_analytic_lock)"
    )
    assert loop.index('abort "containers-present-before-block:$ORDINAL"') < loop.index(
        block_state_check
    )
    assert loop.index(block_state_check) < loop.index('ANALYTIC_STARTED=1')
    assert loop.index(block_state_check) < loop.index(
        'if run_block "$ORDINAL" "$ARM_ID" "$SCENARIO" "$SEQ"'
    )
    assert 'tooling_evidence.get("schema") != "iter135.tooling_verification.v2"' in text
    assert "iter135.tooling_verification.v1" not in text


def test_current_mission_authority_accepts_exact_bound_physical_state(
    tmp_path: Path,
) -> None:
    state_path, manifest_path, manifest_sha = write_state_authority(
        tmp_path, launch_authorized_state()
    )
    descriptor = os.open(state_path, os.O_RDONLY)
    try:
        result = run_state_authority_check(
            state_path, manifest_path, manifest_sha, descriptor
        )
    finally:
        os.close(descriptor)

    assert result.returncode == 0, result.stderr
    state_sha, identity, byte_count = result.stdout.split()
    assert state_sha == hashlib.sha256(state_path.read_bytes()).hexdigest()
    assert len(identity.split(":")) == 6
    assert int(byte_count) == state_path.stat().st_size


@pytest.mark.parametrize(
    "mutation",
    [
        "phase",
        "run_state",
        "authorized_actions",
        "workspace_boundary",
    ],
)
def test_current_mission_authority_rejects_semantically_revoked_state_even_if_receipted(
    tmp_path: Path, mutation: str
) -> None:
    state = launch_authorized_state()
    if mutation == "phase":
        state["next_program"]["phase"] = "TOOLING_FROZEN_PREFLIGHT_REQUIRED"
    elif mutation == "run_state":
        state["run_state"] = "RUNNING"
    elif mutation == "authorized_actions":
        state["next_program"]["authorized_actions"] = []
    else:
        state["workspace_boundary"]["isolated_from"] = (
            "/Users/danielwahnich/workspace/sentinel"
        )
    case = tmp_path / mutation
    case.mkdir()
    state_path, manifest_path, manifest_sha = write_state_authority(case, state)
    descriptor = os.open(state_path, os.O_RDONLY)
    try:
        result = run_state_authority_check(
            state_path, manifest_path, manifest_sha, descriptor
        )
    finally:
        os.close(descriptor)

    assert result.returncode != 0
    assert "does not authorize this analytic launch" in result.stderr


def test_current_mission_authority_rejects_in_place_revocation_after_binding(
    tmp_path: Path,
) -> None:
    state = launch_authorized_state()
    state_path, manifest_path, manifest_sha = write_state_authority(tmp_path, state)
    descriptor = os.open(state_path, os.O_RDONLY)
    try:
        accepted = run_state_authority_check(
            state_path, manifest_path, manifest_sha, descriptor
        )
        assert accepted.returncode == 0, accepted.stderr
        expected_sha, expected_identity, _ = accepted.stdout.split()
        state["run_state"] = "RUNNING"
        state_path.write_text(json.dumps(state, sort_keys=True) + "\n")
        rejected = run_state_authority_check(
            state_path,
            manifest_path,
            manifest_sha,
            descriptor,
            expected_identity=expected_identity,
            expected_sha=expected_sha,
        )
    finally:
        os.close(descriptor)

    assert rejected.returncode != 0
    assert (
        "identity drift" in rejected.stderr
        or "hash drift" in rejected.stderr
        or "bound current state" in rejected.stderr
    )


def test_current_mission_authority_rejects_atomic_replacement_after_binding(
    tmp_path: Path,
) -> None:
    state_path, manifest_path, manifest_sha = write_state_authority(
        tmp_path, launch_authorized_state()
    )
    descriptor = os.open(state_path, os.O_RDONLY)
    try:
        accepted = run_state_authority_check(
            state_path, manifest_path, manifest_sha, descriptor
        )
        assert accepted.returncode == 0, accepted.stderr
        expected_sha, expected_identity, _ = accepted.stdout.split()
        replacement = tmp_path / "replacement.json"
        replacement.write_bytes(state_path.read_bytes())
        os.replace(replacement, state_path)
        rejected = run_state_authority_check(
            state_path,
            manifest_path,
            manifest_sha,
            descriptor,
            expected_identity=expected_identity,
            expected_sha=expected_sha,
        )
    finally:
        os.close(descriptor)

    assert rejected.returncode != 0
    assert "no longer matches pinned launch authority" in rejected.stderr


def test_launcher_binds_the_executing_inode_to_manifest_source(tmp_path: Path) -> None:
    program = executing_runner_binding_program()
    canonical = subprocess.run(
        [sys.executable, "-", str(LAUNCHER), str(LAUNCHER)],
        input=program,
        text=True,
        check=True,
        capture_output=True,
    )
    assert len(canonical.stdout.split()[0]) == 64
    copied = tmp_path / "run_dose135.sh"
    copied.write_bytes(LAUNCHER.read_bytes())

    rejected = subprocess.run(
        [sys.executable, "-", str(LAUNCHER), str(copied)],
        input=program,
        text=True,
        check=False,
        capture_output=True,
    )

    assert rejected.returncode != 0
    assert "executing launcher is not the canonical physical source" in rejected.stderr
    assert "executing-runner-manifest-binding" in LAUNCHER.read_text()


def test_launcher_implements_only_the_amended_block_execution() -> None:
    text = LAUNCHER.read_text()

    assert 'echo "##### I135BLOCK $ARM_ID $SCENARIO $SEQ #####"' in text
    assert '--scenario-category="$SCENARIO" --runs 20' in text
    assert "--runs 1" not in text
    assert "--run-index" not in text
    assert "SENTINEL_DOSE_RUN" not in text
    assert "I135_CELL_INFRA_RETRY" not in text
    assert 'manifest.get("planned_blocks") != 120' in text
    assert 'manifest.get("planned_episodes") != 2400' in text
    assert 'manifest.get("execution_blocks") != expected_blocks' in text
    assert 'manifest.get("execution_cells") != expected_cells' in text


def test_launcher_is_inert_without_all_fail_closed_gates() -> None:
    text = LAUNCHER.read_text()

    assert 'manifest.get("launch_authorized") is not True' in text
    assert 'passed is not True' in text
    assert "payload-outside-root" in text
    assert "remote-artifacts:missing" in text
    assert "docker_image_ids" in text
    assert '"--query-gpu=name,uuid,driver_version,memory.total"' in text
    assert "gpu-live-drift" in text
    assert "environment-file:embedded-receipt-drift" in text
    assert "environment-receipts:field-set" in text
    assert '"capture_started_at_utc"' in text
    assert '"storage_devices"' in text
    assert '"capture_environment135.py"' in text
    assert "parse_canonical_utc" in text
    assert "environment-host-contract" in text
    assert "gpu-receipt:frozen-identity" in text
    assert "environment-box:contract-drift" in text
    assert "storage-live-device-drift" in text
    assert "containers-present-before-launch" in text
    assert "containers-present-before-block" in text
    assert "containers-present-after-completion" in text
    assert "live-gpu-topology" in text
    assert "live-gpu-process-present" in text
    assert "evaluator-process-present" in text
    assert "for REQUIRED_COMMAND in awk chmod cp date docker find findmnt flock git grep mkdir mktemp" in text
    assert "nvidia-smi ps python3 readlink rm rmdir sha256sum sleep stat timeout tr wc" in text
    assert 'echo "I135_ABORT $REQUIRED_COMMAND-missing" >&2' in text
    assert "EXPECTED_MANIFEST_SHA=${SENTINEL_LAUNCH_MANIFEST_SHA256:-}" in text
    assert "independent-manifest-sha256" in text
    assert "minimum_remote_free_bytes" in text
    assert "projected-reserve-bytes" in text
    assert "G8-reserve-after-block" in text
    assert "storage-path-not-dedicated-filesystem" in text
    assert "storage-output-root-not-empty" in text
    assert "OUTPUT_ROOT=/datasets/nuscenes-full/sentinel-i135-outoutput" in text
    assert "TOTAL_CEILING_SECONDS=$((110 * 60 * 60))" in text
    assert "prior_smoke_gpu_seconds" in text
    assert "remaining_analytic_seconds" in text
    assert 'manifest.get("schema") != "iter135.launch_manifest.v2"' in text
    assert 'environment.get("schema") != "iter135.environment_receipts.v3"' in text
    assert '"g7_dataset_provenance"' in text
    assert '"dataset_receipt"' in text
    assert "iter135.dataset_runtime_snapshot.v1" in text
    assert "I135_DATASET_RUNTIME_OK" in text
    assert "iter135.docker_runtime_snapshot.v1" in text
    assert "I135_DOCKER_RUNTIME_OK" in text
    assert 'docker_context != "default"' in text
    assert 'docker_endpoint != "unix:///var/run/docker.sock"' in text
    assert '"docker_runtime_snapshot_sha256"' in text
    assert "NUSCENES_PATH=/datasets/nuscenes-full" in text
    assert "NUSCENES_PATH=/datasets/nuscenes\n" not in text


def test_launcher_requires_independent_activation_baton_and_rechecks_it_at_boundaries() -> None:
    text = LAUNCHER.read_text()
    local_activation = text[
        text.index("verify_launch_activation() {") : text.index("\n\ncleanup_containers() {")
    ]
    final_activation = "FINAL_LOCAL_ACTIVATION_BINDING=$(verify_launch_activation)"
    block_activation = (
        "verify_launch_activation >/dev/null \\\n"
        '    || abort "launch-activation-revoked-before-block:$ORDINAL"'
    )
    loop = text[text.index("while IFS=$'\\t' read -r ORDINAL") :]

    assert "ACTIVATION_SOURCE=$I135/launch_activation_receipt.json" in text
    assert "EXPECTED_ACTIVATION_COMMIT=${SENTINEL_LAUNCH_ACTIVATION_COMMIT:-}" in text
    assert "EXPECTED_ACTIVATION_SHA=${SENTINEL_LAUNCH_ACTIVATION_SHA256:-}" in text
    assert 'exec 5< "$ACTIVATION_SOURCE"' in text
    assert '"/proc/$$/fd/5"' in text
    assert "iter135.launch_activation.v1" in text
    assert "MISSION_STATE alone" not in text  # authority is code, not a documentary assertion
    assert "activation receipt no longer matches its pinned authority" in text
    assert "independently supplied activation authority is malformed" in text
    assert "GITHUB_ACTIVATION_COMMIT" not in local_activation
    assert "GITHUB_FINAL_MANIFEST_COMMIT" not in local_activation
    assert "https://api.github.com/repos/manfromnowhere143/sentinel" in text
    assert 'EXPECTED_CHECKS = {"check (3.10)", "check (3.11)"}' in text
    assert "ProxyHandler({})" in text
    assert "ssl.create_default_context()" in text
    assert "activation B parent does not equal receipt-bound F" in text
    assert text.index(final_activation) < text.index(
        "ANALYTIC_LOCK_ID=$(publish_analytic_lock)"
    )
    assert loop.index(block_activation) < loop.index("ANALYTIC_STARTED=1")
    assert 'abort "launch-activation-revoked-before-done"' in text
    assert 'manifest.get("host_packet_manifest") != bound.get(' in text
    assert '"smoke-evidence/SMOKE.md"' in text
    assert '"authorize_launch135.py"' in text
    assert '"prepare_host135.py"' in text


@pytest.mark.parametrize("mutation", ["malformed-receipt", "malformed-commit"])
def test_activation_validator_rejects_hostile_authority_inputs(
    tmp_path: Path, mutation: str
) -> None:
    experiment = tmp_path / "iter135"
    experiment.mkdir()
    activation = experiment / "launch_activation_receipt.json"
    activation.write_text("{}\n")
    state = experiment / "MISSION_STATE.json"
    state.write_text("{}\n")
    manifest = experiment / "launch_manifest.json"
    manifest.write_text("{}\n")
    activation_payload = activation.read_bytes()
    activation_sha = hashlib.sha256(activation_payload).hexdigest()
    expected_commit = "a" * 40
    supplied_commit = "not-a-commit" if mutation == "malformed-commit" else expected_commit
    descriptor = os.open(activation, os.O_RDONLY)
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-",
                str(activation),
                str(state),
                str(manifest),
                str(experiment),
                supplied_commit,
                activation_sha,
                f"/dev/fd/{descriptor}",
                "",
                "",
                hashlib.sha256(manifest.read_bytes()).hexdigest(),
            ],
            input=launch_activation_program(),
            text=True,
            check=False,
            capture_output=True,
            pass_fds=(descriptor,),
        )
    finally:
        os.close(descriptor)

    assert completed.returncode != 0
    if mutation == "malformed-commit":
        assert "independently supplied activation authority is malformed" in completed.stderr
    else:
        assert "activation receipt field set drift" in completed.stderr


def test_local_activation_then_github_projection_feeds_exact_lock_payload(
    tmp_path: Path,
) -> None:
    experiment = tmp_path / "iter135"
    (experiment / "smoke-evidence/raw").mkdir(parents=True)
    state_payload = b"{}\n"
    (experiment / "MISSION_STATE.json").write_bytes(state_payload)
    host_packet = {"schema": "iter135.host_packet_manifest.v1", "source_commit": "a" * 40}
    host_packet_payload = (json.dumps(host_packet, sort_keys=True) + "\n").encode()
    (experiment / "host_packet_manifest.json").write_bytes(host_packet_payload)
    host_preparation = {
        "schema": "iter135.host_preparation_receipt.v1",
        "verdict": "I135_HOST_PREPARATION_OK",
        "packet_manifest_sha256": hashlib.sha256(host_packet_payload).hexdigest(),
    }
    host_preparation_payload = (
        json.dumps(host_preparation, sort_keys=True) + "\n"
    ).encode()
    (experiment / "host_preparation_receipt.json").write_bytes(host_preparation_payload)
    environment_payload = (
        json.dumps(
            {
                "schema": "iter135.environment_receipts.v3",
                "verdict": "I135_ENVIRONMENT_PREFLIGHT_OK",
            },
            sort_keys=True,
        )
        + "\n"
    ).encode()
    (experiment / "env_receipts.json").write_bytes(environment_payload)
    pre_smoke_payload = b'{"pre_smoke":true}\n'
    (experiment / "smoke-evidence/raw/pre_smoke_manifest.json").write_bytes(
        pre_smoke_payload
    )
    smoke_payload = (
        json.dumps(
            {
                "schema": "iter135.smoke_receipt.v1",
                "verdict": "I135_LIVE_SMOKE_OK",
                "nonanalytic": True,
                "analytic_episode_count": 0,
            },
            sort_keys=True,
        )
        + "\n"
    ).encode()
    (experiment / "smoke-evidence/smoke_receipt.json").write_bytes(smoke_payload)
    tooling_payload = (
        json.dumps(
            {
                "schema": "iter135.tooling_verification.v2",
                "verdict": "I135_TOOLING_VERIFICATION_OK",
                "publication": {
                    "generation": 5,
                    "supersedes_receipt_commit": (
                        "c3e891b9e41f2291b47edc9cec7abffd5259f674"
                    ),
                    "recovery_parent": "27c7f02b5474dd156c4a7686de774a6f408df42e",
                    "reason_code": "B4_H_CONTRACT_UNIAD_LOAD_BEARING_UNTRACKED_SYMLINK",
                },
                "repository": {"git_start": {"head": "9" * 40}},
            },
            sort_keys=True,
        )
        + "\n"
    ).encode()
    (experiment / "tooling_verification_receipt.json").write_bytes(tooling_payload)
    commits = {
        "tooling_receipt": "1" * 40,
        "host_preparation": "2" * 40,
        "environment": "3" * 40,
        "pre_smoke_manifest": "4" * 40,
        "smoke": "5" * 40,
        "state": "6" * 40,
        "final_manifest": "7" * 40,
        "baton_parent": "7" * 40,
    }

    def bound(path: str, payload: bytes) -> dict[str, object]:
        return {
            "source_path": path,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
        }

    def activation_bound(path: str, payload: bytes) -> dict[str, object]:
        return {
            "path": path,
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
        }

    relative_root = "experiments/iter135_neuroncap_blind_braking_dose_response"
    manifest = {
        "git_provenance": {"head": commits["state"]},
        "mission_state": bound("MISSION_STATE.json", state_payload),
        "hash_bound_files": {
            "host_packet_manifest.json": bound(
                f"{relative_root}/host_packet_manifest.json", host_packet_payload
            ),
            "host_preparation_receipt.json": bound(
                f"{relative_root}/host_preparation_receipt.json",
                host_preparation_payload,
            ),
            "env_receipts.json": bound(
                f"{relative_root}/env_receipts.json", environment_payload
            ),
            "smoke-evidence/smoke_receipt.json": bound(
                f"{relative_root}/smoke-evidence/smoke_receipt.json", smoke_payload
            ),
        },
    }
    manifest["host_packet_manifest"] = manifest["hash_bound_files"][
        "host_packet_manifest.json"
    ]
    manifest["host_preparation_receipt"] = manifest["hash_bound_files"][
        "host_preparation_receipt.json"
    ]
    manifest["smoke_receipt"] = manifest["hash_bound_files"][
        "smoke-evidence/smoke_receipt.json"
    ]
    manifest_payload = (json.dumps(manifest, sort_keys=True) + "\n").encode()
    manifest_path = experiment / "launch_manifest.json"
    manifest_path.write_bytes(manifest_payload)
    artifacts = {
        "mission_state": activation_bound("MISSION_STATE.json", state_payload),
        "host_preparation": activation_bound(
            f"{relative_root}/host_preparation_receipt.json", host_preparation_payload
        ),
        "host_packet_manifest": activation_bound(
            f"{relative_root}/host_packet_manifest.json", host_packet_payload
        ),
        "environment": activation_bound(
            f"{relative_root}/env_receipts.json", environment_payload
        ),
        "pre_smoke_manifest": activation_bound(
            f"{relative_root}/launch_manifest.json", pre_smoke_payload
        ),
        "smoke_receipt": activation_bound(
            f"{relative_root}/smoke-evidence/smoke_receipt.json", smoke_payload
        ),
        "final_manifest": activation_bound(
            f"{relative_root}/launch_manifest.json", manifest_payload
        ),
    }
    activation = {
        "schema": "iter135.launch_activation.v1",
        "verdict": "I135_LAUNCH_ACTIVATION_OK",
        "problem_count": 0,
        "problems": [],
        "phase": "LAUNCH_AUTHORIZED",
        "commits": commits,
        "artifacts": artifacts,
    }
    activation["receipt_payload_sha256"] = hashlib.sha256(
        json.dumps(activation, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    activation_payload = (json.dumps(activation, sort_keys=True) + "\n").encode()
    activation_path = experiment / "launch_activation_receipt.json"
    activation_path.write_bytes(activation_payload)
    activation_sha = hashlib.sha256(activation_payload).hexdigest()
    activation_commit = "8" * 40
    descriptor = os.open(activation_path, os.O_RDONLY)
    try:
        local = subprocess.run(
            [
                sys.executable,
                "-",
                str(activation_path),
                str(experiment / "MISSION_STATE.json"),
                str(manifest_path),
                str(experiment),
                activation_commit,
                activation_sha,
                f"/dev/fd/{descriptor}",
                "",
                "",
                hashlib.sha256(manifest_payload).hexdigest(),
            ],
            input=launch_activation_program(),
            text=True,
            check=False,
            capture_output=True,
            pass_fds=(descriptor,),
        )
    finally:
        os.close(descriptor)
    assert local.returncode == 0, local.stderr
    local_fields = local.stdout.split()
    assert local_fields[3] == commits["final_manifest"]

    namespace = github_launch_authority_namespace()
    blob_oid = hashlib.sha1(
        f"blob {len(activation_payload)}\0".encode() + activation_payload
    ).hexdigest()
    ref = {
        "ref": "refs/heads/master",
        "object": {"type": "commit", "sha": activation_commit},
    }
    responses = [
        ref,
        _green_check_runs(activation_commit),
        {
            "sha": activation_commit,
            "parents": [{"sha": commits["final_manifest"]}],
            "files": [
                {"filename": path, "status": "modified"}
                for path in sorted(
                    {
                        "CONTINUITY.md",
                        "HANDOFF.md",
                        namespace["ACTIVATION_REPOSITORY_PATH"],
                    }
                )
            ],
        },
        {
            "type": "file",
            "path": namespace["ACTIVATION_REPOSITORY_PATH"],
            "sha": blob_oid,
            "encoding": "base64",
            "size": len(activation_payload),
            "content": base64.b64encode(activation_payload).decode(),
        },
        ref,
    ]
    namespace["github_json"] = lambda _relative: responses.pop(0)
    original_argv = namespace["sys"].argv
    namespace["sys"].argv = [
        "authority",
        activation_commit,
        activation_sha,
        str(activation_path),
    ]
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            namespace["main"]()
    finally:
        namespace["sys"].argv = original_argv
    remote_fields = output.getvalue().split()
    assert remote_fields[:2] == [activation_commit, commits["final_manifest"]]
    assert remote_fields[1] == local_fields[3]

    lock = tmp_path / "analytic.lock"
    published = subprocess.run(
        [
            sys.executable,
            "-",
            str(lock),
            hashlib.sha256(manifest_payload).hexdigest(),
            "a" * 64,
            "b" * 64,
            activation_sha,
            remote_fields[0],
            remote_fields[1],
            remote_fields[2],
            remote_fields[3],
            "c" * 64,
            "d" * 64,
            "66305:13504",
            "135",
        ],
        input=analytic_lock_publisher_program(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert published.returncode == 0, published.stderr
    lock_payload = json.loads(lock.read_text())
    authority = lock_payload["github_launch_authority"]
    assert authority["activation_commit"] == activation_commit
    assert authority["final_manifest_commit"] == local_fields[3]
    assert [row["id"] for row in authority["checks"]] == [
        int(remote_fields[2]),
        int(remote_fields[3]),
    ]


@pytest.mark.parametrize(
    ("field", "hostile"),
    [
        ("generation", 3),
        ("supersedes_receipt_commit", "0" * 40),
        ("recovery_parent", "1" * 40),
        ("reason_code", "UNREGISTERED_GENERATION_FIVE_REASON"),
    ],
)
def test_analytic_tooling_publication_contract_rejects_each_hostile_field(
    field: str, hostile: object
) -> None:
    namespace = tooling_publication_contract_namespace()
    validate = namespace["tooling_receipt_is_exact"]
    publication = dict(namespace["EXPECTED_TOOLING_PUBLICATION"])
    tooling = {
        "schema": "iter135.tooling_verification.v2",
        "verdict": "I135_TOOLING_VERIFICATION_OK",
        "publication": publication,
        "repository": {"git_start": {"head": "9" * 40}},
    }
    assert validate(tooling) is True

    publication[field] = hostile

    assert validate(tooling) is False


@pytest.mark.parametrize("mutation", ["missing", "extra"])
def test_analytic_tooling_publication_contract_requires_exact_field_set(
    mutation: str,
) -> None:
    namespace = tooling_publication_contract_namespace()
    validate = namespace["tooling_receipt_is_exact"]
    publication = dict(namespace["EXPECTED_TOOLING_PUBLICATION"])
    if mutation == "missing":
        publication.pop("reason_code")
    else:
        publication["unregistered"] = True
    tooling = {
        "schema": "iter135.tooling_verification.v2",
        "verdict": "I135_TOOLING_VERIFICATION_OK",
        "publication": publication,
        "repository": {"git_start": {"head": "9" * 40}},
    }

    assert validate(tooling) is False


@pytest.mark.parametrize("mutation", ["schema", "verdict", "source"])
def test_analytic_tooling_receipt_retains_schema_verdict_and_source_oid_gates(
    mutation: str,
) -> None:
    namespace = tooling_publication_contract_namespace()
    validate = namespace["tooling_receipt_is_exact"]
    tooling = {
        "schema": "iter135.tooling_verification.v2",
        "verdict": "I135_TOOLING_VERIFICATION_OK",
        "publication": dict(namespace["EXPECTED_TOOLING_PUBLICATION"]),
        "repository": {"git_start": {"head": "9" * 40}},
    }
    if mutation == "schema":
        tooling["schema"] = "iter135.tooling_verification.hostile"
    elif mutation == "verdict":
        tooling["verdict"] = "I135_TOOLING_VERIFICATION_FAILED"
    else:
        tooling["repository"]["git_start"]["head"] = "not-an-oid"

    assert validate(tooling) is False


def test_launcher_pins_exact_v3_interpreter_and_rechecks_each_block() -> None:
    text = LAUNCHER.read_text()
    loop = text[text.index("while IFS=$'\\t' read -r ORDINAL") :]

    assert 'PYTHON_BIN=$(readlink -f "$PYTHON_COMMAND")' in text
    assert 'exec 10< "$PYTHON_BIN"' in text
    assert 'PYTHON_FD_PATH=/proc/$$/fd/10' in text
    assert '"$PYTHON_FD_PATH" -I "$@"' in text
    assert '"$(stat -Lc \'%d:%i\' "$PYTHON_FD_PATH")" = "$PYTHON_BIN_ID"' in text
    assert '"$(stat -Lc \'%d:%i\' "$PYTHON_BIN")" = "$PYTHON_BIN_ID"' in text
    assert 'environment.get("schema") != "iter135.environment_receipts.v3"' in text
    assert 'invocation.get("isolated") is not True' in text
    assert '"physical_path"' in text
    assert '"sha256"' in text
    assert '"version"' in text
    assert loop.index("verify_python_interpreter_binding") < loop.index(
        "ANALYTIC_STARTED=1"
    )
    assert 'SENTINEL_DOCKER_EXECUTABLE="$DOCKER_FD_PATH"' in text
    assert 'exec "$SENTINEL_DOCKER_EXECUTABLE" run' in text


def _green_check_runs(commit: str) -> dict[str, object]:
    return {
        "total_count": 2,
        "check_runs": [
            {
                "id": index,
                "name": f"check ({version})",
                "head_sha": commit,
                "status": "completed",
                "conclusion": "success",
                "app": {"slug": "github-actions"},
            }
            for index, version in enumerate(("3.10", "3.11"), start=10)
        ]
    }


@pytest.mark.parametrize(
    "payload",
    [
        b'{"outer":{"x":1,"x":2}}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":-Infinity}',
    ],
)
def test_github_launch_authority_strict_json_rejects_hostile_payloads(
    payload: bytes,
) -> None:
    namespace = github_launch_authority_namespace()

    with pytest.raises(ValueError, match="duplicate JSON key|non-finite JSON number"):
        namespace["strict_json_loads"](payload)


@pytest.mark.parametrize("mutation", ["duplicate-key", "non-finite"])
def test_github_launch_authority_rejects_hostile_committed_activation_artifact(
    mutation: str,
) -> None:
    namespace = github_launch_authority_namespace()
    final_manifest = "b" * 40
    commits = json.dumps(
        {"final_manifest": final_manifest, "baton_parent": final_manifest},
        sort_keys=True,
        separators=(",", ":"),
    )
    if mutation == "duplicate-key":
        deployed = f'{{"commits":{commits},"commits":{commits}}}'.encode()
    else:
        deployed = f'{{"commits":{commits},"hostile":NaN}}'.encode()
    blob_oid = hashlib.sha1(
        f"blob {len(deployed)}\0".encode() + deployed
    ).hexdigest()
    blob = {
        "type": "file",
        "path": namespace["ACTIVATION_REPOSITORY_PATH"],
        "sha": blob_oid,
        "encoding": "base64",
        "size": len(deployed),
        "content": base64.b64encode(deployed).decode(),
    }

    with pytest.raises(ValueError, match="duplicate JSON key|non-finite JSON number"):
        namespace["validate_activation_blob"](
            blob,
            deployed,
            hashlib.sha256(deployed).hexdigest(),
            final_manifest,
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("pending", "not green"),
        ("failure", "not green"),
        ("wrong-head", "identity drift"),
        ("wrong-app", "identity drift"),
        ("missing", "incomplete"),
        ("page-incomplete", "incomplete"),
        ("duplicate", "missing"),
    ],
)
def test_github_launch_gate_rejects_hostile_ci_json(
    mutation: str, message: str
) -> None:
    namespace = github_launch_authority_namespace()
    validate_ci = namespace["validate_ci"]
    commit = "a" * 40
    payload = _green_check_runs(commit)
    if mutation == "pending":
        payload["check_runs"][0]["status"] = "in_progress"
        payload["check_runs"][0]["conclusion"] = None
    elif mutation == "failure":
        payload["check_runs"][0]["conclusion"] = "failure"
    elif mutation == "wrong-head":
        payload["check_runs"][0]["head_sha"] = "b" * 40
    elif mutation == "wrong-app":
        payload["check_runs"][0]["app"] = {"slug": "untrusted"}
    elif mutation == "missing":
        payload["check_runs"] = payload["check_runs"][:1]
        payload["total_count"] = 1
    elif mutation == "page-incomplete":
        payload["total_count"] = 3
    else:
        payload["check_runs"][1]["name"] = "check (3.10)"

    with pytest.raises(ValueError, match=message):
        validate_ci(payload, commit)


def test_github_launch_gate_rejects_master_parent_and_activation_blob_drift() -> None:
    namespace = github_launch_authority_namespace()
    validate_ref = namespace["validate_ref"]
    validate_commit = namespace["validate_commit"]
    validate_activation_blob = namespace["validate_activation_blob"]
    commit = "a" * 40
    final_manifest = "b" * 40

    with pytest.raises(ValueError, match="current canonical GitHub master"):
        validate_ref(
            {
                "ref": "refs/heads/master",
                "object": {"type": "commit", "sha": "c" * 40},
            },
            commit,
        )
    with pytest.raises(ValueError, match="exactly one"):
        validate_commit({"sha": commit, "parents": []}, commit)
    exact_commit = {
        "sha": commit,
        "parents": [{"sha": final_manifest}],
        "files": [
            {"filename": "CONTINUITY.md", "status": "modified"},
            {"filename": "HANDOFF.md", "status": "modified"},
            {
                "filename": namespace["ACTIVATION_REPOSITORY_PATH"],
                "status": "added",
            },
        ],
    }
    assert validate_commit(exact_commit, commit) == final_manifest
    extra_commit = json.loads(json.dumps(exact_commit))
    extra_commit["files"].append({"filename": "unexpected.txt", "status": "added"})
    with pytest.raises(ValueError, match="changed-path scope"):
        validate_commit(extra_commit, commit)
    renamed_commit = json.loads(json.dumps(exact_commit))
    renamed_commit["files"][2]["status"] = "renamed"
    renamed_commit["files"][2]["previous_filename"] = "old.json"
    with pytest.raises(ValueError, match="changed-path scope"):
        validate_commit(renamed_commit, commit)

    activation = {
        "commits": {
            "final_manifest": final_manifest,
            "baton_parent": final_manifest,
        }
    }
    deployed = (json.dumps(activation, sort_keys=True) + "\n").encode()
    blob_oid = hashlib.sha1(f"blob {len(deployed)}\0".encode() + deployed).hexdigest()
    payload = {
        "type": "file",
        "path": namespace["ACTIVATION_REPOSITORY_PATH"],
        "encoding": "base64",
        "size": len(deployed),
        "sha": blob_oid,
        "content": base64.b64encode(deployed).decode(),
    }
    validate_activation_blob(
        payload, deployed, hashlib.sha256(deployed).hexdigest(), final_manifest
    )
    with pytest.raises(ValueError, match="does not equal the GitHub B blob"):
        validate_activation_blob(
            payload,
            deployed + b" ",
            hashlib.sha256(deployed + b" ").hexdigest(),
            final_manifest,
        )
    with pytest.raises(ValueError, match="parent does not equal"):
        validate_activation_blob(
            payload, deployed, hashlib.sha256(deployed).hexdigest(), "d" * 40
        )


def test_github_launch_gate_rechecks_master_after_ci_scope_and_blob(
    tmp_path: Path,
) -> None:
    namespace = github_launch_authority_namespace()
    commit = "a" * 40
    final_manifest = "b" * 40
    activation = {
        "commits": {
            "final_manifest": final_manifest,
            "baton_parent": final_manifest,
        }
    }
    activation_path = tmp_path / "launch_activation_receipt.json"
    activation_path.write_text(json.dumps(activation, sort_keys=True) + "\n")
    deployed = activation_path.read_bytes()
    blob_oid = hashlib.sha1(f"blob {len(deployed)}\0".encode() + deployed).hexdigest()
    green_ref = {
        "ref": "refs/heads/master",
        "object": {"type": "commit", "sha": commit},
    }
    red_ref = {
        "ref": "refs/heads/master",
        "object": {"type": "commit", "sha": "c" * 40},
    }
    responses = [
        green_ref,
        _green_check_runs(commit),
        {
            "sha": commit,
            "parents": [{"sha": final_manifest}],
            "files": [
                {"filename": "CONTINUITY.md", "status": "modified"},
                {"filename": "HANDOFF.md", "status": "modified"},
                {
                    "filename": namespace["ACTIVATION_REPOSITORY_PATH"],
                    "status": "added",
                },
            ],
        },
        {
            "type": "file",
            "path": namespace["ACTIVATION_REPOSITORY_PATH"],
            "encoding": "base64",
            "size": len(deployed),
            "sha": blob_oid,
            "content": base64.b64encode(deployed).decode(),
        },
        red_ref,
    ]
    requests: list[str] = []

    def fake_github_json(relative: str) -> object:
        requests.append(relative)
        return responses.pop(0)

    namespace["github_json"] = fake_github_json
    original_argv = namespace["sys"].argv
    namespace["sys"].argv = [
        "authority",
        commit,
        hashlib.sha256(deployed).hexdigest(),
        str(activation_path),
    ]
    try:
        with pytest.raises(ValueError, match="current canonical GitHub master"):
            namespace["main"]()
    finally:
        namespace["sys"].argv = original_argv
    assert requests[-1] == "/git/ref/heads/master"
    assert not responses


def test_launcher_rejects_shell_bootstrap_spoofing_and_path_replacement(
    tmp_path: Path,
) -> None:
    text = LAUNCHER.read_text()
    assert text.startswith("#!/bin/bash -p\n")
    assert "done < <(compgen -e)" in text
    assert "SENTINEL_LAUNCH_ACTIVATION_SHA256)" in text
    assert 'BOOTSTRAP_ENV_COUNT" != "6"' in text
    assert '"${PWD-}" != "/opt/sentinel-stack/iter135"' in text
    assert '"${SHLVL-}" != "1"' in text
    assert "/usr/bin/env)" not in text
    assert 'if [ "${PATH-}" != "$CANONICAL_PATH" ]' in text
    assert "CANONICAL_PATH=/usr/bin:/bin:/usr/sbin:/sbin" in text

    original = tmp_path / "python3"
    replacement = tmp_path / "replacement"
    original.write_bytes(b"captured interpreter")
    replacement.write_bytes(b"hostile replacement")
    descriptor = os.open(original, os.O_RDONLY)
    try:
        pinned = os.fstat(descriptor)
        os.replace(replacement, original)
        live = original.stat()
        assert (live.st_dev, live.st_ino) != (pinned.st_dev, pinned.st_ino)
    finally:
        os.close(descriptor)
    assert 'python-interpreter-revoked-before-block:$ORDINAL' in text
    assert '"$(sha256sum "$PYTHON_FD_PATH"' in text


@pytest.mark.parametrize(
    ("source", "authority"),
    [
        (
            LAUNCHER,
            {
                "SENTINEL_LAUNCH_MANIFEST_SHA256": "1" * 64,
                "SENTINEL_LAUNCH_ACTIVATION_COMMIT": "2" * 40,
                "SENTINEL_LAUNCH_ACTIVATION_SHA256": "3" * 64,
            },
        ),
        (
            SMOKE_LAUNCHER,
            {
                "SENTINEL_SMOKE_INPUT_MANIFEST_COMMIT": "2" * 40,
                "SENTINEL_SMOKE_INPUT_MANIFEST_SHA256": "1" * 64,
            },
        ),
    ],
)
def test_launcher_startup_exact_environment_fails_before_host_access(
    tmp_path: Path, source: Path, authority: dict[str, str]
) -> None:
    canonical_path = "/usr/bin:/bin:/usr/sbin:/sbin"
    exact = {"PATH": canonical_path, **authority}
    accepted = subprocess.run(
        ["/bin/bash", "-p", str(source)],
        cwd=tmp_path,
        env=exact,
        capture_output=True,
        text=True,
        check=False,
    )
    assert accepted.returncode == 1
    assert "hostile-bootstrap-working-directory" in accepted.stderr

    for name in ("GIT_DIR", "GIT_CONFIG_GLOBAL", "DOCKER_CONTEXT", "PYTHONPATH"):
        hostile = subprocess.run(
            ["/bin/bash", "-p", str(source)],
            cwd=tmp_path,
            env={**exact, name: "/tmp/hostile"},
            capture_output=True,
            text=True,
            check=False,
        )
        assert hostile.returncode == 1
        assert f"hostile-bootstrap-environment:{name}" in hostile.stderr

    wrong_path = subprocess.run(
        ["/bin/bash", "-p", str(source)],
        cwd=tmp_path,
        env={**exact, "PATH": "/tmp"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert wrong_path.returncode == 1
    assert "hostile-bootstrap-path" in wrong_path.stderr

    wrong_level = subprocess.run(
        ["/bin/bash", "-p", "-c", bootstrap_program(source, tmp_path)],
        cwd=tmp_path,
        env={**exact, "SHLVL": "9"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert wrong_level.returncode == 1
    assert "hostile-bootstrap-shell-level" in wrong_level.stderr


def test_public_authority_network_calls_stay_outside_irreversible_loops() -> None:
    analytic = LAUNCHER.read_text()
    smoke = SMOKE_LAUNCHER.read_text()
    assert analytic.count("verify_github_launch_authority") == 2  # definition + final arm
    run_block = analytic[
        analytic.index("run_block() {") : analytic.index("publish_analytic_lock() {")
    ]
    assert "verify_github_launch_authority" not in run_block
    final_call = "GITHUB_LAUNCH_BINDING=$(verify_github_launch_authority)"
    assert analytic.count(final_call) == 1
    final_activation = "FINAL_LOCAL_ACTIVATION_BINDING=$(verify_launch_activation)"
    assert analytic.index(final_activation) < analytic.index(final_call)
    assert analytic.index(final_call) < analytic.index(
        "ANALYTIC_LOCK_ID=$(publish_analytic_lock)"
    )
    terminal_tail = analytic[
        analytic.index(final_call) : analytic.index("ANALYTIC_LOCK_ID=$(publish_analytic_lock)")
    ]
    assert "verify_launch_activation" not in terminal_tail

    assert smoke.count("verify_github_pre_smoke_authority") == 3  # definition + 2 calls
    initial = "GITHUB_PRE_SMOKE_BINDING=$(verify_github_pre_smoke_authority)"
    terminal = "TERMINAL_GITHUB_PRE_SMOKE_BINDING=$(verify_github_pre_smoke_authority)"
    lock = "SMOKE_LOCK_ID=$(python3"
    assert smoke.count("\n" + initial) == 1
    assert smoke.count("\n" + terminal) == 1
    assert smoke.index(initial) < smoke.index(terminal) < smoke.index(lock)
    assert "verify_github_pre_smoke_authority" not in smoke[smoke.index(lock) :]


def test_launcher_binds_canonical_source_paths_and_complete_smoke_raw_set() -> None:
    text = LAUNCHER.read_text()
    assert (
        'source_path\n            != f"experiments/'
        'iter135_neuroncap_blind_braking_dose_response/{name}"'
    ) in text
    assert '"smoke-evidence/raw/pre_smoke_mission_state.json"' in text


def _fake_docker_runtime_receipt(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    return {
        "schema": "iter135.docker_runtime_receipt.v1",
        "client": {
            "invocation_path": str(path),
            "physical_path": str(path),
            "realpath": str(path),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "version": {
                "version": "27.5.1",
                "api_version": "1.47",
                "git_commit": "4c9b3b0",
                "go_version": "go1.22.11",
                "os": "linux",
                "arch": "amd64",
                "build_time": "2025-01-22T13:41:17Z",
                "context": "default",
            },
        },
        "context": {"name": "default", "endpoint": "unix:///var/run/docker.sock"},
        "daemon": {
            "info": {
                "id": "ENGINE",
                "name": "sentinel-gpu",
                "server_version": "27.5.1",
                "docker_root_dir": "/var/lib/docker",
                "driver": "overlay2",
                "operating_system": "Ubuntu",
                "os_type": "linux",
                "architecture": "x86_64",
                "ncpu": 8,
                "mem_total": 32_000_000_000,
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
                "build_time": "2025-01-22T13:41:17Z",
                "experimental": False,
            },
        },
    }


def _write_fake_docker(path: Path) -> None:
    path.write_text(
        f"#!{sys.executable}\n"
        "import json\n"
        "import sys\n"
        "client = {'Version':'27.5.1','ApiVersion':'1.47','GitCommit':'4c9b3b0',"
        "'GoVersion':'go1.22.11','Os':'linux','Arch':'amd64',"
        "'BuildTime':'2025-01-22T13:41:17Z','Context':'default'}\n"
        "server = {'Platform':{'Name':'Docker Engine - Community'},'Version':'27.5.1',"
        "'ApiVersion':'1.47','MinAPIVersion':'1.24','GitCommit':'4c9b3b0',"
        "'GoVersion':'go1.22.11','Os':'linux','Arch':'amd64',"
        "'BuildTime':'2025-01-22T13:41:17Z','Experimental':False}\n"
        "info = {'ID':'ENGINE','Name':'sentinel-gpu','ServerVersion':'27.5.1',"
        "'DockerRootDir':'/var/lib/docker','Driver':'overlay2',"
        "'OperatingSystem':'Ubuntu','OSType':'linux','Architecture':'x86_64',"
        "'NCPU':8,'MemTotal':32000000000,'KernelVersion':'6.8.0',"
        "'CgroupDriver':'systemd','CgroupVersion':'2'}\n"
        "args = sys.argv[1:]\n"
        "if args[:1] == ['version']: print(json.dumps({'Client':client,'Server':server}))\n"
        "elif args[:1] == ['info']: print(json.dumps(info))\n"
        "elif args == ['context','show']: print('default')\n"
        "elif args[:2] == ['context','inspect']: print(json.dumps('unix:///var/run/docker.sock'))\n"
        "else: raise SystemExit(64)\n"
    )
    path.chmod(0o700)


def _run_docker_runtime_program(
    docker: Path, receipt: dict[str, object], descriptor: int
) -> subprocess.CompletedProcess[str]:
    environment_path = docker.parent / "environment.json"
    environment_path.write_text(json.dumps({"docker_runtime": receipt}) + "\n")
    row = os.fstat(descriptor)
    return subprocess.run(
        [
            sys.executable,
            "-",
            str(environment_path),
            str(docker),
            str(docker),
            f"/dev/fd/{descriptor}",
            f"{row.st_dev}:{row.st_ino}",
            hashlib.sha256(os.pread(descriptor, row.st_size, 0)).hexdigest(),
            str(row.st_size),
        ],
        input=docker_runtime_program(),
        text=True,
        check=False,
        capture_output=True,
        pass_fds=(descriptor,),
    )


def test_docker_v3_runtime_gate_binds_fd_daemon_and_architecture_aliases(
    tmp_path: Path,
) -> None:
    if not Path("/proc/self/fd").is_dir():
        pytest.skip("production FD execution is a Linux /proc contract")
    docker = tmp_path / "docker"
    _write_fake_docker(docker)
    receipt = _fake_docker_runtime_receipt(docker)
    descriptor = os.open(docker, os.O_RDONLY)
    try:
        accepted = _run_docker_runtime_program(docker, receipt, descriptor)
    finally:
        os.close(descriptor)
    assert accepted.returncode == 0, accepted.stderr
    assert len(accepted.stdout.strip()) == 64

    drifted = json.loads(json.dumps(receipt))
    drifted["daemon"]["info"]["server_version"] = "99.0.0"
    descriptor = os.open(docker, os.O_RDONLY)
    try:
        rejected = _run_docker_runtime_program(docker, drifted, descriptor)
    finally:
        os.close(descriptor)
    assert rejected.returncode != 0
    assert "live Docker client/context/daemon drift" in rejected.stderr

    text = LAUNCHER.read_text()
    assert '"x86_64": "amd64"' in text
    assert '"aarch64": "arm64"' in text
    assert 'DOCKER_FD_PATH=/proc/$$/fd/11' in text
    assert 'runtime_executable = f"/proc/self/fd/{runtime_descriptor}"' in text
    loop = text[text.index("while IFS=$'\\t' read -r ORDINAL") :]
    assert "verify_docker_v3_runtime" in loop


def test_docker_v3_runtime_gate_rejects_path_replacement_after_fd_pin(
    tmp_path: Path,
) -> None:
    docker = tmp_path / "docker"
    _write_fake_docker(docker)
    receipt = _fake_docker_runtime_receipt(docker)
    descriptor = os.open(docker, os.O_RDONLY)
    try:
        replacement = tmp_path / "replacement"
        _write_fake_docker(replacement)
        os.replace(replacement, docker)
        rejected = _run_docker_runtime_program(docker, receipt, descriptor)
    finally:
        os.close(descriptor)
    assert rejected.returncode != 0
    assert "pinned FD or pathname drift" in rejected.stderr


def test_dataset_snapshot_captures_ctime_and_rejects_cross_device_files(
    tmp_path: Path,
) -> None:
    namespace: dict[str, object] = {}
    exec(stable_dataset_file_program(), namespace)
    stable_dataset_file = namespace["stable_dataset_file"]
    path = tmp_path / "sample.json"
    payload = b'{"sample":"frozen"}\n'
    path.write_bytes(payload)
    expected_sha = hashlib.sha256(payload).hexdigest()
    expected_device = path.stat().st_dev

    first = stable_dataset_file(path, expected_sha, len(payload), expected_device)

    assert first["st_dev"] == expected_device
    assert first["st_ctime_ns"] == path.stat().st_ctime_ns
    with pytest.raises(SystemExit, match="dataset snapshot byte proof drift"):
        stable_dataset_file(path, expected_sha, len(payload), expected_device + 1)

    path.chmod(0o600)
    second = stable_dataset_file(path, expected_sha, len(payload), expected_device)
    assert second["sha256"] == first["sha256"]
    assert second["bytes"] == first["bytes"]
    assert second["st_ctime_ns"] != first["st_ctime_ns"]


def test_dataset_runtime_proof_checks_every_frozen_role_and_preserves_raw_binding() -> None:
    text = LAUNCHER.read_text()

    assert 'files=28' in text
    assert 'if not isinstance(files, dict) or set(files) != expected_snapshot_roles' in text
    assert 'live, live_sha = stable_live_receipt(path, hash_bytes=label != "archive")' in text
    assert 'if label != "archive" and live_sha != receipt.get("sha256")' in text
    assert 'or before.st_dev != root_stat.st_dev' in text
    assert '"st_ctime_ns": before.st_ctime_ns' in text
    assert 'dataset_runtime_snapshot_id=$DATASET_RUNTIME_SNAPSHOT_ID' in text
    assert 'docker_runtime_snapshot_id=$DOCKER_RUNTIME_SNAPSHOT_ID' in text
    assert 'launch_lock_id=$ANALYTIC_LOCK_ID' in text
    canonical_redirect = "exec 1>&9 2>&1"
    logged_snapshot = (
        'echo "I135_DATASET_SNAPSHOT_OK sha256=$DATASET_RUNTIME_SNAPSHOT_SHA '
        'id=$DATASET_RUNTIME_SNAPSHOT_ID files=28"'
    )
    assert text.index(canonical_redirect) < text.rindex(logged_snapshot)


def test_launcher_requires_complete_raw_block_artifacts_and_decisions() -> None:
    text = LAUNCHER.read_text()

    assert 'for name in ("ego_poses.json", "metrics.json", "actors.json")' in text
    assert 'if resets != list(range(20))' in text
    assert '"block_identity": True' in text
    assert "decision-block-identity" in text
    assert 'row.get("schedule_missing") or row.get("intervene_err")' in text
    assert 'row.get("class") != scenario_class or row.get("pair") != sequence' in text
    assert 'row.get("dose") != dose' in text
    assert 'echo "I135_DOSE_DONE"' in text


def test_launcher_cannot_claim_completion_from_a_short_or_failed_plan() -> None:
    text = LAUNCHER.read_text()

    assert 'block_stream > "$BLOCK_PLAN"' in text
    assert 'wc -l < "$BLOCK_PLAN"' in text
    assert 'if [ "$ORDINAL" != "$EXPECTED_ORDINAL" ]' in text
    assert 'verify_block_plan_row "$ORDINAL" "$ARM_ID" "$SCENARIO" "$SEQ"' in text
    assert 'block plan row drift: {observed}!={expected}' in text
    assert 'BLOCK_PLAN_FD_ID=$(stat -Lc' in text
    assert 'done <&7' in text
    assert 'EXECUTED_BLOCKS=$((EXECUTED_BLOCKS + 1))' in text
    assert 'if [ "$EXECUTED_BLOCKS" != "120" ]' in text
    assert 'episodes=$((EXECUTED_BLOCKS * 20))' in text


def test_launcher_preserves_failed_attempt_evidence_and_bounds_hung_blocks() -> None:
    text = LAUNCHER.read_text()

    assert 'if ! exec 9> "$CANONICAL_LOG"' in text
    assert "set -o noclobber" in text
    assert "CANONICAL_LOG_OWNED=1" in text
    assert "CANONICAL_LOG_ID=$(stat -Lc '%d:%i' \"/proc/$$/fd/9\")" in text
    assert 'if [ "$CANONICAL_LOG_PATH_ID" != "$CANONICAL_LOG_ID" ]' in text
    assert "exec 1>&9 2>&1" in text
    assert 'exec > "$CANONICAL_LOG"' not in text
    assert 'timeout --signal=TERM --kill-after=60s "$COMPOSE_TIMEOUT_SECONDS" env' in text
    assert "TERMINATION_RESERVE_SECONDS=300" in text
    assert 'PRE_COMPOSE_ELAPSED=$(monotonic_elapsed)' in text
    assert 'COMPOSE_WALL_REMAINING=$((CEILING_SECONDS - PRE_COMPOSE_ELAPSED))' in text
    assert 'abort "G7-block-failed' in text
    assert "os.link(temporary, lock, follow_symlinks=False)" in text
    assert 'CURRENT_LOCK_ID=$(stat -Lc' in text
    assert 'rm -f "$LOCK" || true' in text
    assert '[ "$ANALYTIC_STARTED" = "0" ]' in text
    assert "ANALYTIC_STARTED=1" in text
    assert "iter135.deadline_watchdog.v1" in text
    assert "signal_tree(signal.SIGTERM)" in text
    assert "signal_tree(signal.SIGKILL)" in text
    assert "verify_deadline_watchdog" in text
    assert 'rm -rf "$LOCK"' not in text
    assert 'rmdir "$LOCK"' not in text
    assert "launch_lock_retained=$LOCK" in text


def test_launcher_has_a_non_destructive_preflight_and_owned_execution_boundary() -> None:
    text = LAUNCHER.read_text()

    preflight_lock = "if ! flock -n 8"
    permanent_lock = "ANALYTIC_LOCK_ID=$(publish_analytic_lock)"
    canonical_log = 'if ! exec 9> "$CANONICAL_LOG"'
    analytic_start = "ANALYTIC_STARTED=1"
    timeout = 'timeout --signal=TERM --kill-after=60s "$COMPOSE_TIMEOUT_SECONDS" env'

    assert preflight_lock in text
    assert "PREFLIGHT_LOCK_OWNED=1" in text
    assert "PREFLIGHT_LOCK_FD_ID=$(stat -Lc" in text
    assert 'if [ -L "$PREFLIGHT_LOCK" ] || [ ! -f "$PREFLIGHT_LOCK" ]' in text
    assert "OWNED_CONTAINER_IDS=()" in text
    assert "OWNED_CONTAINER_ROLES=()" in text
    assert 'docker rm -f "$ID"' in text
    assert 'REMAINING_IDS+=("$ID")' in text
    assert 'OWNED_CONTAINER_IDS=("${REMAINING_IDS[@]}")' in text
    assert 'cleanup_containers || return 73' in text
    assert "docker rm -f renderer model ncap" not in text
    assert "--label sentinel.mission=iter135" in text
    assert '--cidfile "$CID_FILE"' in text
    assert "os.O_WRONLY | os.O_CREAT | os.O_EXCL" in text
    assert text.index(permanent_lock) > text.index('execution-block-stream-count')
    assert text.index(canonical_log) > text.index(permanent_lock)
    assert text.index(permanent_lock) < text.index("ANALYTIC_STAGING_IDS=$(python3")
    run_block = text[text.index("run_block() {") : text.index("BLOCK_PLAN=$(mktemp")]
    main_loop = text[text.index("while IFS=$'\\t' read -r ORDINAL") :]
    assert timeout in run_block
    assert main_loop.index(analytic_start) < main_loop.index('if run_block "$ORDINAL"')
    assert text.index('if run_block "$ORDINAL"') > text.index(canonical_log)
    assert "containers-present-at-analytic-arm" in text
    assert "live-gpu-process-at-analytic-arm" in text
    assert "evaluator-process-at-analytic-arm" in text
    assert 'rm -f "$CANONICAL_LOG"' in text
    cleanup = text[text.index("cleanup() {") : text.index("abort() {")]
    assert cleanup.index('git -C "$STACK/UniAD" checkout HEAD') < cleanup.index("flock -u 8")
    assert cleanup.index('rm -f "$LOCK" || true') < cleanup.index("flock -u 8")
    assert text.count("flock -u 8") == 1


def test_launcher_replays_exact_remote_and_repository_provenance() -> None:
    text = LAUNCHER.read_text()

    assert '"compose_script": "/opt/sentinel-stack/NeuroNCAP/scripts/' in text
    assert 'role = f"scenario:{scenario_class}/{sequence}"' in text
    assert "expected_remote_paths[role]" in text
    assert 'expected_remote_paths[f"renderer:{sequence}:checkpoint"]' in text
    assert 'if set(remote_rows) != set(expected_remote_paths)' in text
    assert 'path.resolve(strict=True) != path' in text
    assert 'actual, byte_count = stable_sha256(path)' in text
    assert 'repositories != expected_repositories' in text
    assert '"diff", "--cached", "--name-only", "--no-renames", "-z"' in text
    assert '"status", "--porcelain=v1", "-z", "--untracked-files=normal"' in text
    assert 'path != "outoutput/" and not path.startswith("outoutput/")' in text


def test_launcher_freezes_zero_retry_and_exact_server_patch_outputs() -> None:
    text = LAUNCHER.read_text()

    assert 'design.get("retry_policy") != "no_automatic_retry_abort_on_first_block_failure"' in text
    assert 'design.get("allowed_retries") != 0' in text
    assert "I135_CELL_INFRA_RETRY" not in text
    assert "8f6ed6a9bbeefc93b0bf7ee2f15b4843921475a0eded3719db59a8ad38538056" in text
    assert "b636930ab2685ea31a417ab10a4eaac055bc8cecc814e38084c706c8ace09bbf" in text
    assert 'git -C "$STACK/UniAD" diff --cached --quiet --' in text
    assert '!= "$EXPECTED_PATCHED_SERVER_SHA"' in text
    run_block = text[text.index("run_block() {") : text.index("BLOCK_PLAN=$(mktemp")]
    baseline_check = '!= "$BASELINE_SERVER_SHA"'
    patch_call = 'python3 "$PATCH"'
    after_replay = (
        'verify_block_runtime_inputs "$SCENARIO" "$SEQ" '
        '"$EXPECTED_PATCHED_SERVER_SHA" after'
    )
    restore = 'git -C "$STACK/UniAD" checkout HEAD -- inference/server.py'
    assert run_block.index(baseline_check) < run_block.index("SERVER_TOUCHED=1")
    assert run_block.index("SERVER_TOUCHED=1") < run_block.index(patch_call)
    assert run_block.index(restore) > run_block.index(after_replay)
    assert restore not in run_block[: run_block.index(patch_call)]


def test_launcher_snapshots_and_rehashes_execution_inputs() -> None:
    text = LAUNCHER.read_text()

    assert "manifest changed while being read" in text
    assert 'snapshot = parent / f"i135-runtime-{expected_manifest_sha}"' in text
    assert "os.O_WRONLY | os.O_CREAT | os.O_EXCL" in text
    assert 'verify_runtime_snapshot || abort "runtime-snapshot-drift-before-block:$ORDINAL"' in text
    assert 'verify_runtime_snapshot || abort "runtime-snapshot-drift-before-done"' in text
    assert "def stable_receipt(path: Path)" in text
    assert 'selected_roles.add(f"scenario:{scenario_class}/{sequence}")' in text
    assert 'f"renderer:{sequence}:checkpoint"' in text
    assert "runtime schedule target drift" in text
    assert "runtime image identity drift" in text
    assert 'verify_block_runtime_inputs "$SCENARIO" "$SEQ" "$EXPECTED_PATCHED_SERVER_SHA" before' in text
    assert 'verify_block_runtime_inputs "$SCENARIO" "$SEQ" "$EXPECTED_PATCHED_SERVER_SHA" after' in text
    assert 'verify_block_runtime_inputs "$SCENARIO" "$SEQ" "$BASELINE_SERVER_SHA" after' in text


def test_launcher_captures_provenance_labeled_container_ids_while_live() -> None:
    text = LAUNCHER.read_text()

    assert 'SENTINEL_CONTAINER_CID_DIR="$CURRENT_BLOCK_CID_DIR"' in text
    assert 'ACTIVE_COMPOSE_PID=$!' in text
    assert 'while compose_process_running "$ACTIVE_COMPOSE_PID"' in text
    assert 'IDENTITY=$(bounded_docker inspect --format' in text
    assert 'OBSERVED_MANIFEST" != "$EXPECTED_MANIFEST_SHA"' in text
    assert 'OBSERVED_BLOCK" != "$CURRENT_BLOCK_ORDINAL"' in text
    assert "I135_CONTAINER_OWNERSHIP_FAIL role-replacement" in text
    assert "I135_CONTAINER_RECEIPT role=$ROLE id=$ID" in text
    assert 'if ! verify_container_receipts' in text
    assert 'verify_container_quiescence "after-block-$ORDINAL"' in text
    assert "container_receipt_rows()" in text
    assert "vanished-without-receipt" in text
    assert 'record_owned_container "$RECEIPT_ID" "$ROLE"' in text
    assert text.count('LIVE_AFTER=$(bounded_docker ps -aq --no-trunc)') >= 2
    assert "CONTAINER_QUIET_SECONDS=5" in text
    assert "CONTAINER_QUIESCENCE_CEILING_SECONDS=20" in text


def test_launcher_binds_storage_and_per_block_output_identities() -> None:
    text = LAUNCHER.read_text()

    assert "verify_output_storage_identity analytic-arm 1" in text
    assert "verify_output_storage_identity before-block 0" in text
    assert "verify_output_storage_identity after-block 0" in text
    assert "verify_output_storage_identity before-done 0" in text
    assert 'OUTPUT_ROOT_ID=$(stat -Lc' in text
    assert "os.O_DIRECTORY | os.O_NOFOLLOW" in text
    assert "os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW" in text
    assert 'f"{decision_identity[0]}:{decision_identity[1]}"' in text
    assert 'f"{output_identity[0]}:{output_identity[1]}"' in text
    assert 'identity(output) != output_identity' in text
    assert 'identity(decision) != decision_identity' in text


def test_launcher_publishes_durable_lock_before_canonical_staging() -> None:
    text = LAUNCHER.read_text()

    final_idle = 'evaluator-process-at-final-analytic-arm'
    storage = 'storage-identity-at-final-analytic-arm'
    lock = "ANALYTIC_LOCK_ID=$(publish_analytic_lock)"
    staging = "ANALYTIC_STAGING_IDS=$(python3"
    log = 'if ! exec 9> "$CANONICAL_LOG"'
    assert text.index(final_idle) < text.index(storage)
    assert text.index(storage) < text.index(lock)
    assert text.index(lock) < text.index(staging)
    assert text.index(staging) < text.index(log)
    assert "os.path.lexists(target)" in text
    assert "os.path.lexists(decision_root)" in text
    assert "SCHEDULE_TARGET_ID=" in text
    assert "DECISION_ROOT_ID=" in text
    assert "iter135.analytic_lock.v2" not in text
    assert text.count("iter135.analytic_lock.v3") >= 2
    assert '"github_launch_authority": authority' in text
    assert '"repository": "manfromnowhere143/sentinel"' in text
    assert '"branch": "master"' in text
    assert '"python_wrapper_sha256": python_wrapper_sha256' in text


@pytest.mark.parametrize("operation", ["ps", "inspect", "rm"])
def test_bounded_docker_times_out_hung_control_operations(
    tmp_path: Path, operation: str
) -> None:
    fake = tmp_path / "docker"
    fake.write_text("#!/bin/bash\nsleep 30\n")
    fake.chmod(0o500)
    program = (
        "set -euo pipefail\n"
        f'DOCKER_BIN="{fake}"\n'
        "DOCKER_CONTROL_TIMEOUT_SECONDS=1\n"
        + shell_function("bounded_docker", "compose_process_running")
        + f"\nbounded_docker {operation}\n"
    )

    started = time.monotonic()
    completed = subprocess.run(
        ["bash"],
        input=program,
        text=True,
        check=False,
        capture_output=True,
        timeout=5,
    )

    assert completed.returncode == 124
    assert time.monotonic() - started < 4


def test_container_receipt_parser_rejects_a_dangling_cid_symlink(
    tmp_path: Path,
) -> None:
    control = tmp_path / "sentinel-i135-control.test"
    block = control / "block-7"
    block.mkdir(parents=True)
    (block / "renderer.cid").symlink_to(block / "missing")
    program = container_receipt_rows_program().replace(
        'expected_root = Path("/tmp")',
        f"expected_root = Path({str(tmp_path)!r})",
    )

    completed = subprocess.run(
        [sys.executable, "-", str(block), "7"],
        input=program,
        text=True,
        check=False,
        capture_output=True,
    )

    assert completed.returncode != 0
    assert "container cid is not physical: renderer" in completed.stderr


def test_container_quiescence_resets_after_delayed_container_appearance(
    tmp_path: Path,
) -> None:
    fake = tmp_path / "docker"
    counter = tmp_path / "counter"
    observed = tmp_path / "observed"
    fake.write_text(
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        ': "${COUNTER:?}"\n'
        'count=$(cat "$COUNTER" 2>/dev/null || printf 0)\n'
        'count=$((count + 1))\n'
        'printf \'%s\' "$count" > "$COUNTER"\n'
        'if [ "$count" = 2 ]; then printf \'%064d\\n\' 1; fi\n'
    )
    fake.chmod(0o500)
    program = (
        "set -euo pipefail\n"
        f'DOCKER_BIN="{fake}"\n'
        "DOCKER_CONTROL_TIMEOUT_SECONDS=1\n"
        "CONTAINER_QUIET_SECONDS=1\n"
        "CONTAINER_QUIESCENCE_CEILING_SECONDS=5\n"
        f'COUNTER="{counter}"\nexport COUNTER\n'
        f'OBSERVED="{observed}"\n'
        "capture_owned_containers() { printf capture >> \"$OBSERVED\"; }\n"
        "cleanup_containers() { printf cleanup >> \"$OBSERVED\"; }\n"
        + shell_function("bounded_docker", "compose_process_running")
        + "\n"
        + shell_function("verify_container_quiescence", "verify_container_receipts")
        + "\nverify_container_quiescence test\n"
    )

    started = time.monotonic()
    completed = subprocess.run(
        ["bash"],
        input=program,
        text=True,
        check=False,
        capture_output=True,
        timeout=8,
    )

    assert completed.returncode == 0, completed.stderr
    assert observed.read_text() == "capturecleanup"
    assert int(counter.read_text()) >= 5
    assert time.monotonic() - started >= 1.1


def test_embedded_docker_wrapper_is_shell_syntax_valid() -> None:
    subprocess.run(
        ["bash", "-n"],
        input=embedded_docker_wrapper(),
        text=True,
        check=True,
    )


def test_embedded_docker_wrapper_injects_exact_renderer_provenance(tmp_path: Path) -> None:
    capture = tmp_path / "argv"
    docker = tmp_path / "docker-real"
    docker.write_text(
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        ': "${CAPTURE:?}"\n'
        'printf \'%s\\n\' "$@" > "$CAPTURE"\n'
    )
    docker.chmod(0o500)
    control = tmp_path / "sentinel-i135-control.test"
    cid_dir = control / "block-7"
    cid_dir.mkdir(parents=True)
    wrapper = control / "docker"
    wrapper.write_text(embedded_docker_wrapper())
    wrapper.chmod(0o500)
    renderer_image = (
        "sha256:4b36caf2054d37b4febeddeae08b310f906ec632fec4095b5dc4497323433e5c"
    )
    manifest_sha = "a" * 64
    environment = {
        **os.environ,
        "CAPTURE": str(capture),
        "SENTINEL_DOCKER_BIN": str(docker),
        "SENTINEL_DOCKER_EXECUTABLE": str(docker),
        "SENTINEL_DOCKER_BIN_ID": f"{docker.stat().st_dev}:{docker.stat().st_ino}",
        "SENTINEL_DOCKER_BIN_SHA256": hashlib.sha256(docker.read_bytes()).hexdigest(),
        "SENTINEL_DOCKER_WRAPPER_SHA256": hashlib.sha256(
            wrapper.read_bytes()
        ).hexdigest(),
        "SENTINEL_MANIFEST_SHA256": manifest_sha,
        "SENTINEL_BLOCK_ORDINAL": "7",
        "SENTINEL_CONTAINER_CONTROL_ROOT": str(control),
        "SENTINEL_CONTAINER_CONTROL_ROOT_ID": (
            f"{control.stat().st_dev}:{control.stat().st_ino}"
        ),
        "SENTINEL_CONTAINER_CID_DIR": str(cid_dir),
    }

    subprocess.run(
        [
            str(wrapper),
            "run",
            "--name",
            "renderer",
            "--rm",
            "--gpus",
            "all",
            renderer_image,
            "python",
            "renderer.py",
        ],
        env=environment,
        check=True,
    )

    argv = capture.read_text().splitlines()
    assert argv == [
        "run",
        "--label",
        "sentinel.mission=iter135",
        "--label",
        f"sentinel.manifest={manifest_sha}",
        "--label",
        "sentinel.mode=analytic",
        "--label",
        "sentinel.block=7",
        "--label",
        "sentinel.role=renderer",
        "--cidfile",
        str(cid_dir / "renderer.cid"),
        "--name",
        "renderer",
        "--rm",
        "--gpus",
        "all",
        renderer_image,
        "python",
        "renderer.py",
    ]


def test_embedded_docker_wrapper_rejects_unrecognized_named_container(
    tmp_path: Path,
) -> None:
    docker = tmp_path / "docker-real"
    docker.write_text("#!/bin/bash\nexit 0\n")
    docker.chmod(0o500)
    control = tmp_path / "sentinel-i135-control.test"
    cid_dir = control / "block-7"
    cid_dir.mkdir(parents=True)
    wrapper = control / "docker"
    wrapper.write_text(embedded_docker_wrapper())
    wrapper.chmod(0o500)
    environment = {
        **os.environ,
        "SENTINEL_DOCKER_BIN": str(docker),
        "SENTINEL_DOCKER_EXECUTABLE": str(docker),
        "SENTINEL_DOCKER_BIN_ID": f"{docker.stat().st_dev}:{docker.stat().st_ino}",
        "SENTINEL_DOCKER_BIN_SHA256": hashlib.sha256(docker.read_bytes()).hexdigest(),
        "SENTINEL_DOCKER_WRAPPER_SHA256": hashlib.sha256(
            wrapper.read_bytes()
        ).hexdigest(),
        "SENTINEL_MANIFEST_SHA256": "a" * 64,
        "SENTINEL_BLOCK_ORDINAL": "7",
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
            "foreign",
            "sha256:" + "f" * 64,
        ],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 125
    assert "I135_DOCKER_WRAPPER_FAIL unexpected-name:foreign" in completed.stderr


def test_analytic_wrapper_runs_owned_kill_tail_and_rejects_other_commands(
    tmp_path: Path,
) -> None:
    control = tmp_path / "sentinel-i135-control.test"
    cid_dir = control / "block-7"
    cid_dir.mkdir(parents=True)
    wrapper = control / "docker"
    wrapper.write_text(embedded_docker_wrapper())
    wrapper.chmod(0o500)
    fake_docker = tmp_path / "docker-real"
    fake_docker.write_text(
        """#!/bin/bash -p
set -euo pipefail
COMMAND=$1
shift
case "$COMMAND" in
  run)
    NAME=
    CID_FILE=
    PREVIOUS=
    for ARG in "$@"; do
      if [ "$PREVIOUS" = "--name" ]; then NAME=$ARG; fi
      if [ "$PREVIOUS" = "--cidfile" ]; then CID_FILE=$ARG; fi
      PREVIOUS=$ARG
    done
    case "$NAME" in
      renderer) CID=$(printf 'a%.0s' {1..64}) ;;
      model) CID=$(printf 'b%.0s' {1..64}) ;;
      *) CID=$(printf 'c%.0s' {1..64}) ;;
    esac
    printf '%s\n' "$CID" > "$CID_FILE"
    printf 'run:%s\n' "${NAME:-ncap}" >> "$FAKE_DOCKER_LOG"
    ;;
  inspect)
    CID=
    for ARG in "$@"; do CID=$ARG; done
    case "$CID" in
      a*) ROLE=renderer ;;
      b*) ROLE=model ;;
      *) exit 44 ;;
    esac
    printf '%s|/%s|iter135|%s|analytic|%s|%s\n' \
      "$CID" "$ROLE" "$SENTINEL_MANIFEST_SHA256" \
      "$SENTINEL_BLOCK_ORDINAL" "$ROLE"
    ;;
  kill) printf 'kill:%s\n' "$1" >> "$FAKE_DOCKER_LOG" ;;
  *) exit 45 ;;
esac
"""
    )
    fake_docker.chmod(0o500)
    tool_bin = tmp_path / "bin"
    tool_bin.mkdir()
    portable_stat = tool_bin / "stat"
    portable_stat.write_text(
        """#!/usr/bin/env python3
import os
import stat
import sys

if sys.argv[1:3] == ["-Lc", "%d:%i"] and len(sys.argv) == 4:
    row = os.stat(sys.argv[3], follow_symlinks=True)
    print(f"{row.st_dev}:{row.st_ino}")
elif sys.argv[1:3] == ["-Lc", "%a"] and len(sys.argv) == 4:
    print(format(stat.S_IMODE(os.stat(sys.argv[3]).st_mode), "o"))
else:
    raise SystemExit(64)
"""
    )
    portable_stat.chmod(0o500)
    log = tmp_path / "docker.log"
    manifest_sha = "1" * 64
    environment = {
        **os.environ,
        "PATH": f"{control}:{tool_bin}:{os.environ['PATH']}",
        "FAKE_DOCKER_LOG": str(log),
        "SENTINEL_DOCKER_BIN": str(fake_docker),
        "SENTINEL_DOCKER_EXECUTABLE": str(fake_docker),
        "SENTINEL_DOCKER_BIN_ID": f"{fake_docker.stat().st_dev}:{fake_docker.stat().st_ino}",
        "SENTINEL_DOCKER_BIN_SHA256": hashlib.sha256(
            fake_docker.read_bytes()
        ).hexdigest(),
        "SENTINEL_DOCKER_WRAPPER_SHA256": hashlib.sha256(
            wrapper.read_bytes()
        ).hexdigest(),
        "SENTINEL_MANIFEST_SHA256": manifest_sha,
        "SENTINEL_BLOCK_ORDINAL": "7",
        "SENTINEL_CONTAINER_CONTROL_ROOT": str(control),
        "SENTINEL_CONTAINER_CONTROL_ROOT_ID": f"{control.stat().st_dev}:{control.stat().st_ino}",
        "SENTINEL_CONTAINER_CID_DIR": str(cid_dir),
    }
    renderer_image = "sha256:4b36caf2054d37b4febeddeae08b310f906ec632fec4095b5dc4497323433e5c"
    model_image = "sha256:f73ef38840631211983ea0dde0cf1ecdfa6dbc84ef6cd0bfb900427da6d601cb"
    harness = tmp_path / "harness.sh"
    harness.write_text(
        "#!/bin/bash -p\nset -euo pipefail\n"
        f"docker run --name renderer {renderer_image}\n"
        f"docker run --name model {model_image}\n"
        "docker kill renderer\n"
        "docker kill model\n"
    )
    harness.chmod(0o500)
    completed = subprocess.run(
        [str(harness)], env=environment, capture_output=True, text=True, check=False
    )
    assert completed.returncode == 0, completed.stderr
    assert log.read_text().splitlines() == [
        "run:renderer",
        "run:model",
        "kill:" + "a" * 64,
        "kill:" + "b" * 64,
    ]
    rejected = subprocess.run(
        [str(wrapper), "rm", "renderer"],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert rejected.returncode == 125
    assert "unexpected-command:rm" in rejected.stderr
