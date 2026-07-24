#!/usr/bin/env python3
"""Produce and independently validate the frozen Iteration-135 tooling receipt.

This verifier is intentionally local-only.  It discovers the complete Iteration-135 focused test
surface, binds every relevant source byte, executes the frozen validation commands without a
shell, and rejects file- or test-set drift at every command boundary.  Command output is never
embedded in the receipt: only byte counts and SHA-256 digests are retained.

Usage:
    python3 verify_tooling135.py [OUTPUT.json]
    python3 verify_tooling135.py --verify-receipt RECEIPT.json
    python3 -I -B -S verify_tooling135.py --bind-next-source COMMIT --accepted-baton-commit B16
        --accepted-tooling-receipt-sha256 SHA256 --next-source-output OUTPUT.json
    python3 -I -B -S verify_tooling135.py --verify-next-source-binding RECEIPT.json
        --accepted-baton-commit B16 --accepted-tooling-receipt-sha256 SHA256
        --expected-candidate-commit COMMIT --expected-binding-sha256 SHA256

The default output is ``tooling_verification_receipt.json`` beside this file.  A successful run
exits zero.  Any failed command, provenance failure, or temporal drift emits a red receipt and
exits two.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import select
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Sequence


SCHEMA = "iter135.tooling_verification.v2"
OK_VERDICT = "I135_TOOLING_VERIFICATION_OK"
FAIL_VERDICT = "I135_TOOLING_VERIFICATION_FAILED"
RECEIPT_FIELDS = frozenset(
    {
        "schema",
        "publication",
        "verdict",
        "problem_count",
        "problems",
        "repository",
        "inventory",
        "inventory_sha256",
        "toolchain",
        "environment_contract",
        "files",
        "file_content_set_sha256",
        "command_contract",
        "commands",
        "timing",
        "receipt_payload_sha256",
    }
)
RECEIPT_PAYLOAD_FIELDS = RECEIPT_FIELDS - {"receipt_payload_sha256"}
REPOSITORY_FIELDS = frozenset(
    {
        "root",
        "git_start",
        "git_end",
        "git_head_stable",
        "git_state_stable",
        "repository_clean_state_stable",
    }
)
GIT_STATE_FIELDS = frozenset(
    {
        "head",
        "dirty_entries",
        "porcelain_v1_z_sha256",
        "branch",
        "upstream",
        "upstream_head",
        "parents",
        "commit_paths",
    }
)
TOOLCHAIN_ROW_FIELDS = frozenset(
    {
        "path",
        "sha256",
        "bytes",
        "device",
        "inode",
        "mode",
        "mtime_ns",
        "ctime_ns",
        "version",
    }
)
FILE_ROW_FIELDS = frozenset({"sha256", "bytes", "execution_identity"})
EXECUTION_IDENTITY_FIELDS = frozenset(
    {"device", "inode", "mode", "mtime_ns", "ctime_ns"}
)
COMMAND_ROW_FIELDS = frozenset(
    {
        "argv",
        "return_code",
        "stdout_bytes",
        "stdout_sha256",
        "stderr_bytes",
        "stderr_sha256",
    }
)
TIMING_FIELDS = frozenset(
    {
        "started_at_utc",
        "finished_at_utc",
        "wall_duration_ns",
        "monotonic_duration_ns",
    }
)
# ``datetime`` serializes the wall-clock endpoints at microsecond resolution.  Each endpoint can
# therefore differ from the corresponding nanosecond clock sample by less than one microsecond.
WALL_TIMESTAMP_ROUNDING_BUDGET_NS = 2_000

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
CANONICAL_REPOSITORY = "/Users/danielwahnich/workspace/sentinel"
DEFAULT_RECEIPT = HERE / "tooling_verification_receipt.json"
EXPERIMENT_REL = "experiments/iter135_neuroncap_blind_braking_dose_response"
RECEIPT_REL = f"{EXPERIMENT_REL}/tooling_verification_receipt.json"
BINDER_REL = f"{EXPERIMENT_REL}/verify_tooling135.py"
NEXT_SOURCE_SCHEMA = "sentinel.next_source_binding.v1"
NEXT_SOURCE_OK_VERDICT = "I135_NEXT_SOURCE_BINDING_OK"
NEXT_SOURCE_COMMITTED_POSTCONDITION_VERDICT = (
    "I135_NEXT_SOURCE_BINDING_COMMITTED_POSTCONDITION_FAILED"
)
NEXT_SOURCE_COMMIT_STATE_INDETERMINATE_VERDICT = (
    "I135_NEXT_SOURCE_BINDING_COMMIT_STATE_INDETERMINATE"
)
NEXT_SOURCE_CLAIM = "NEXT_SOURCE_CONTENT_BINDING_ONLY"
NEXT_SOURCE_FIELDS = frozenset(
    {
        "schema",
        "verdict",
        "claim",
        "authority",
        "limitations",
        "policy",
        "trust_root",
        "candidate",
        "problems",
        "problem_count",
        "receipt_payload_sha256",
    }
)
NEXT_SOURCE_FILE_FIELDS = frozenset(
    {"path", "mode", "bytes", "git_blob_oid", "sha256"}
)
NEXT_SOURCE_TRUST_ROOT_FIELDS = frozenset(
    {
        "baton_commit",
        "baton_tree",
        "source_commit",
        "receipt_commit",
        "tooling_receipt",
        "binder",
        "python",
        "git",
    }
)
NEXT_SOURCE_ARTIFACT_FIELDS = frozenset({"path", "bytes", "sha256"})
NEXT_SOURCE_BINDER_FIELDS = frozenset(
    {"path", "mode", "bytes", "git_blob_oid", "sha256"}
)
NEXT_SOURCE_TOOL_FIELDS = frozenset({"path", "bytes", "sha256", "version"})
NEXT_SOURCE_CANDIDATE_FIELDS = frozenset(
    {
        "commit",
        "commit_bytes",
        "commit_sha256",
        "parent",
        "tree",
        "tree_object_count",
        "tree_object_bytes",
        "file_count",
        "total_file_bytes",
        "unique_blob_count",
        "unique_blob_bytes",
        "manifest_sha256",
        "files",
    }
)
NEXT_SOURCE_MAX_COMMIT_BYTES = 1_048_576
NEXT_SOURCE_MAX_TREE_DEPTH = 64
NEXT_SOURCE_MAX_TREE_OBJECTS = 10_000
NEXT_SOURCE_MAX_TREE_BYTES = 67_108_864
NEXT_SOURCE_MAX_FILES = 10_000
NEXT_SOURCE_MAX_PATH_BYTES = 1_024
NEXT_SOURCE_MAX_COMPONENT_BYTES = 255
NEXT_SOURCE_MAX_BLOB_BYTES = 134_217_728
NEXT_SOURCE_MAX_TOTAL_FILE_BYTES = 8_589_934_592
NEXT_SOURCE_MAX_RECEIPT_BYTES = 16_777_216
NEXT_SOURCE_MAX_GIT_HEADER_BYTES = 256
NEXT_SOURCE_OBJECT_DEADLINE_SECONDS = 900
NEXT_SOURCE_MAX_GIT_STDERR_BYTES = 1_048_576
NEXT_SOURCE_MAX_JSON_DEPTH = 32
NEXT_SOURCE_MAX_JSON_NODES = 200_000
NEXT_SOURCE_ALLOWED_BLOB_MODES = ("100644", "100755")
NEXT_SOURCE_LIMITATIONS = [
    "The operator-supplied accepted B16 commit and canonical R16 tooling-receipt SHA-256 are external trust axioms.",
    "The operator's pre-execution selection and measurement of the exact R16 Python and B16 verifier are external bootstrap trust axioms; executing code cannot authenticate itself before execution.",
    "The R16-bound Python executable does not bind its standard-library installation, which remains an external trust axiom.",
    "The output writer validates parent ownership and group/world write mode bits but does not bind filesystem ACLs, mount policy, or permission enforcement, which remain external host axioms.",
    "The output writer assumes no adversarial same-UID process mutates the output-parent route, the staging or final names, or their inodes, content, or metadata throughout publication or after its last observation before independent replay; portable POSIX interfaces neither isolate processes sharing a UID nor make name-based link or unlink inode-conditional.",
    "This receipt binds one direct-child candidate commit, tree, and complete regular-file content manifest only.",
    "The operator must separately accept this binding before any candidate checkout, import, execution, or publication.",
    "This receipt establishes no repository publication, hosted-CI, scientific, host, lifecycle, launch, or safety authority.",
]
NEXT_SOURCE_POLICY = {
    "object_format": "sha1",
    "allowed_blob_modes": list(NEXT_SOURCE_ALLOWED_BLOB_MODES),
    "max_commit_bytes": NEXT_SOURCE_MAX_COMMIT_BYTES,
    "max_tree_depth": NEXT_SOURCE_MAX_TREE_DEPTH,
    "max_tree_objects": NEXT_SOURCE_MAX_TREE_OBJECTS,
    "max_tree_bytes": NEXT_SOURCE_MAX_TREE_BYTES,
    "max_files": NEXT_SOURCE_MAX_FILES,
    "max_path_bytes": NEXT_SOURCE_MAX_PATH_BYTES,
    "max_component_bytes": NEXT_SOURCE_MAX_COMPONENT_BYTES,
    "max_blob_bytes": NEXT_SOURCE_MAX_BLOB_BYTES,
    "max_total_file_bytes": NEXT_SOURCE_MAX_TOTAL_FILE_BYTES,
    "max_receipt_bytes": NEXT_SOURCE_MAX_RECEIPT_BYTES,
    "object_deadline_seconds": NEXT_SOURCE_OBJECT_DEADLINE_SECONDS,
    "max_git_stderr_bytes": NEXT_SOURCE_MAX_GIT_STDERR_BYTES,
    "max_json_depth": NEXT_SOURCE_MAX_JSON_DEPTH,
    "max_json_nodes": NEXT_SOURCE_MAX_JSON_NODES,
}
GENERATION_ONE_SOURCE_PARENT = "3fcb607fea8e1a251c2c82da385dd096dd650909"
GENERATION_ONE_SOURCE_COMMIT = "2d94cf45acb337ff3ba923da1d1de6e6dda6dab7"
GENERATION_ONE_RECEIPT_COMMIT = "0b5b2d9a4956606fe0619f53288a64d2da58284a"
GENERATION_TWO_SOURCE_PARENT = "c868040f542f9277fc99a451a108138848e80b33"
GENERATION_TWO_SOURCE_COMMIT = "90773c3686e0e01562a62f3d0f21ddaf594de7d4"
GENERATION_TWO_RECEIPT_COMMIT = "b0eca127ff1d522aefa6164271de7bce3bcaf1a7"
GENERATION_TWO_STATE_COMMIT = "71a137faa268c63d73ae5d1ec0f8409306f446e5"
GENERATION_TWO_BATON_COMMIT = "ee0c0c953ace80b53f3cce97ddd7eb262fb22a2d"
GENERATION_THREE_SOURCE_PARENT = GENERATION_TWO_BATON_COMMIT
GENERATION_THREE_SOURCE_COMMIT = "1820fcfd65483fa9c7429dd54fe65dbf91dc6b35"
GENERATION_THREE_RECEIPT_COMMIT = "755489f36ae2b8cefad183341edefd7c30c047e7"
GENERATION_THREE_STATE_COMMIT = "d9e261075d27d5d717debebe5c881fa4d6e882c5"
GENERATION_THREE_BATON_COMMIT = "30b6390b3e165fc517ec6a7d1d7a26502ea45e2a"
GENERATION_THREE_REASON = (
    "PRE_SMOKE_CONTROL_GAPS_INTERPRETER_SUMMARY_AND_LAUNCH_AUTHORIZATION"
)
GENERATION_FOUR_SOURCE_PARENT = GENERATION_THREE_BATON_COMMIT
GENERATION_FOUR_REASON = "B3_CI_STRUCTURAL_GIT_READER_TOOLCHAIN_ROOT_FAILURE"
GENERATION_FOUR_SOURCE_COMMIT = "052404fb13aee8395f538a92cc3c898c13f06adc"
GENERATION_FOUR_RECEIPT_COMMIT = "c3e891b9e41f2291b47edc9cec7abffd5259f674"
GENERATION_FOUR_STATE_COMMIT = "0137eeb97442f7af92eaefeb57befcd53c8c2319"
GENERATION_FOUR_BATON_COMMIT = "27c7f02b5474dd156c4a7686de774a6f408df42e"
GENERATION_FIVE_SOURCE_PARENT = GENERATION_FOUR_BATON_COMMIT
GENERATION_FIVE_REASON = "B4_H_CONTRACT_UNIAD_LOAD_BEARING_UNTRACKED_SYMLINK"
GENERATION_FIVE_SOURCE_COMMIT = "27c19216387bc211810e7ae8379040f3eee13bd7"
GENERATION_FIVE_RECEIPT_COMMIT = "1f70e367cd1ffcc2c3dab1c801d0e195a1341ef2"
# Generation five published its source and receipt and then failed its own structural probe at the
# local state-acceptance step: this validator's receipt-history check was still hardcoded to the
# four-entry generation-four shape. No generation-five state or baton commit exists, so the
# generation-six recovery parent is the generation-five receipt, the exact published master tip
# at the moment the defect was found.
GENERATION_SIX_SOURCE_PARENT = GENERATION_FIVE_RECEIPT_COMMIT
GENERATION_SIX_REASON = "T5_FROZEN_STRUCTURAL_VALIDATOR_STALE_RECEIPT_HISTORY"
GENERATION_SIX_SOURCE_COMMIT = "b4e0f82fd2ba2a4d3b2604115e9f47f59895e533"
GENERATION_SIX_RECEIPT_COMMIT = "4fb4d819d56f6a6c6331abfa4e8039bf8bedf7be"
GENERATION_SIX_STATE_COMMIT = "b2d4980dcf786427cee518f2998f8e9ec8225dc0"
GENERATION_SIX_BATON_COMMIT = "a37d1fc0fc9b96604e68e37006c0a8b3515984bb"
# Generation seven exists because the first host-preparation attempt failed closed on
# `publication-authority:check-run-envelope`: the frozen proof required exactly two check runs on
# the source commit, but every SHA published under the disclosed branch-validation amendment
# carries the probe run plus the master run per check name. The amended envelope binds authority
# to the newest run per required name.
GENERATION_SEVEN_SOURCE_PARENT = GENERATION_SIX_BATON_COMMIT
GENERATION_SEVEN_REASON = "H1_CHECK_RUN_ENVELOPE_INCOMPATIBLE_WITH_BRANCH_VALIDATION"
GENERATION_SEVEN_SOURCE_COMMIT = "7cb0c442a5649542168db44e1abfd715f4a404e0"
GENERATION_SEVEN_RECEIPT_COMMIT = "470ec333b29f3da8e8b2ee696982f2503ea66161"
GENERATION_SEVEN_STATE_COMMIT = "c44639d8f475d79f35cf0e9a0dc6967f3b06fe78"
GENERATION_SEVEN_BATON_COMMIT = "04801441ce17e104ed2e78a4dd02370d4ffdde17"
# Generation eight exists because the first descendant validation (the stage-zero host-evidence
# commit) proved the frozen ten-second Git probe timeout cannot materialize the multi-gibibyte
# committed evidence tree during the deep replay's isolated checkout: ~14-18 seconds measured on
# the canonical operator host, and the identical TimeoutExpired on both hosted CI lanes. The
# amended controller gives the replay checkout its own hard six-hundred-second fail-closed bound;
# every other Git probe keeps the ten-second bound.
GENERATION_EIGHT_SOURCE_PARENT = GENERATION_SEVEN_BATON_COMMIT
GENERATION_EIGHT_REASON = "B7_STAGE_ZERO_DEEP_REPLAY_CHECKOUT_TIMEOUT_UNSATISFIABLE"
GENERATION_EIGHT_SOURCE_COMMIT = "ba615b59c44954dc91562a5ed37ecaee8ac8d378"
GENERATION_EIGHT_RECEIPT_COMMIT = "faf8a2d0a35be2ad053dae1946893cf69f024f5c"
GENERATION_EIGHT_STATE_COMMIT = "346465c894f9378074f8de4997a4a78fda5f7930"
GENERATION_EIGHT_BATON_COMMIT = "833a00cd930b44e3fac63edb09c6590efd128933"
# Generation nine exists because the stage-zero validation that generation eight unblocked then
# executed the remaining never-run host checks and found the same fossil in every frozen mirror
# of the host contract: the launch controller's receipt deep-check, the environment capture, and
# both launchers still required the UniAD untracked set to be empty, while generation five had
# already accepted the load-bearing `checkpoints` symlink as the real, required state; the deep
# replay also passed a three-field binding projection where the frozen evidence validator reads
# five fields. Generation nine reconciles every mirror at once against an exhaustive audit of the
# frozen tools and adds the explicit symlink contract (type and exact target, `ckpts`).
GENERATION_NINE_SOURCE_PARENT = GENERATION_EIGHT_BATON_COMMIT
GENERATION_NINE_REASON = "B8_STAGE_ZERO_HOST_STATE_MIRRORS_STALE_ACROSS_FROZEN_TOOLS"
GENERATION_NINE_SOURCE_COMMIT = "9dabc72e4d88590dc35b195017ffb0be3538b0cf"
GENERATION_NINE_RECEIPT_COMMIT = "133c7c924a3f47a8e1ff9bf9f975e4e99902fea2"
GENERATION_NINE_STATE_COMMIT = "a0b0947ef2ea86bcb9f5bbabc517bc63d3fb2365"
GENERATION_NINE_BATON_COMMIT = "150e04dd9f996b545393061250fd8448bac795c5"
# Generation ten exists because the generation-seven check-run envelope fix was applied only to
# the host-preparation controller: the environment capture and both launchers still required the
# exact pre-amendment run count, and every amendment-published SHA permanently carries the probe
# run plus the master run per required name. The stage-zero commit published green and the fossil
# was found by a pre-fire sweep before the environment capture ever ran, so no attempt burned.
# Generation ten ports the newest-run-per-name envelope to all remaining live GitHub fetchers.
# Its source parent is the published generation-nine stage-zero commit, the exact master tip at
# discovery (generation-six precedent: the source parent is the published tip, not a baton).
GENERATION_NINE_STAGE_ZERO_COMMIT = "023d7ca638de5f3bde29ef9c6068bc64ecf711f2"
GENERATION_TEN_SOURCE_PARENT = GENERATION_NINE_STAGE_ZERO_COMMIT
GENERATION_TEN_REASON = "E_PREFLIGHT_CHECK_RUN_ENVELOPE_FOSSILS_IN_CAPTURE_AND_LAUNCHERS"
GENERATION_TEN_SOURCE_COMMIT = "214758fd4783cc8e50c72585b0cd56b24e6d2c87"
GENERATION_TEN_RECEIPT_COMMIT = "146d52e5b662bf6af0fd26925367c6218822fa39"
GENERATION_TEN_STATE_COMMIT = "165aa47ba5c40ffa9d7e3d2a735209f2fff4dd8b"
GENERATION_TEN_BATON_COMMIT = "1693d928da4ec2089bb3c60e777e2d1b1e72b3cc"
# Generation eleven exists because the first live environment capture failed closed with
# twenty-three problems that reduced to four contract-versus-reality families: the dataset
# contract omitted the iteration-47 map-expansion archive and its extracted map directories,
# the daemon-version projection required fields Docker 29 relocated, the artifact replay
# demanded a JSON-inline payload the Contents API cannot return above one mebibyte, and the
# image and idle probes cascaded from the daemon failure. The capture is repeatable, no
# one-shot burned, and the repository also gains its Apache-2.0 LICENSE in this scope.
GENERATION_TEN_STAGE_ZERO_COMMIT = "50511a9261e904f4367b390bcc5fa85572e09c26"
GENERATION_ELEVEN_SOURCE_PARENT = GENERATION_TEN_STAGE_ZERO_COMMIT
GENERATION_ELEVEN_REASON = "E1_ENVIRONMENT_CONTRACTS_STALE_DATASET_DOCKER_ARTIFACT_REPLAY"
GENERATION_ELEVEN_SOURCE_COMMIT = "b71fc34a2fc6d093c5665ac63a7d269bfc3e8de9"
GENERATION_ELEVEN_RECEIPT_COMMIT = "97dc88eaa44831eb329d86579f49a4a10a3347e4"
GENERATION_ELEVEN_STATE_COMMIT = "78bb76478615c23bac85f5fe4b0089b65e67726c"
GENERATION_ELEVEN_BATON_COMMIT = "19428eb4d51a22552d803ab4ce4c34177373938f"
# Generation twelve exists because the first live E-commit validation exposed two wiring
# defects in the frozen launch controller's call into the environment validator: the compose
# patcher's binding was absent from the bound hashes, and the two host-authority artifact rows
# were never supplied, so a true green environment receipt could not validate. The capture
# itself returned green; the fix threads both expectations through the call with hostile
# coverage in the launch-authorization suite's stub validator.
GENERATION_ELEVEN_STAGE_ZERO_COMMIT = "a698cbbe3cf6c9e1320c74ab2748f576e68b114e"
GENERATION_TWELVE_SOURCE_PARENT = GENERATION_ELEVEN_STAGE_ZERO_COMMIT
GENERATION_TWELVE_REASON = "E2_COMMIT_VALIDATOR_WIRING_PATCHER_AND_AUTHORITY_ARTIFACTS"
GENERATION_TWELVE_SOURCE_COMMIT = "00f427f139f728a13d21e2d66a3abc6b35f6b31b"
GENERATION_TWELVE_RECEIPT_COMMIT = "fa073e6903be65ff449fc7566df751395d585929"
GENERATION_TWELVE_STATE_COMMIT = "09c200606fbd57497f7be9e93e0ef78d857ae4fd"
GENERATION_TWELVE_BATON_COMMIT = "265fe62e84f685f1308b7974e49c34c8ab9db56d"
# Generation thirteen exists because the pre-smoke (and, by the same structure, the final)
# deep-replay rebuild ran the manifest builder's tooling-receipt gate inside an isolated clone
# whose origin/master had advanced past the stage parent, injecting a spurious
# `origin/master is not an ancestor of current HEAD` problem that no committed P/F could match.
# Generation thirteen pins the isolated checkout's origin/master back to the exact stage parent
# before each rebuild, replaying the manifest under the ref state it was generated in.
GENERATION_TWELVE_ENV_COMMIT = "2c70393f95dcad0871bee24647dd93a151d7b954"
GENERATION_THIRTEEN_SOURCE_PARENT = GENERATION_TWELVE_ENV_COMMIT
GENERATION_THIRTEEN_REASON = "E3_PRESMOKE_REBUILD_ORIGIN_MASTER_AHEAD_OF_STAGE_PARENT"
GENERATION_THIRTEEN_SOURCE_COMMIT = "b0de93a781e4c8929212e278701a3ca7cba27b2d"
GENERATION_THIRTEEN_RECEIPT_COMMIT = "688182ad3b7afbb0d58141accbcf554981e6fb20"
GENERATION_THIRTEEN_STATE_COMMIT = "70fda528d0223d099e387f48dbf5b8feae8b793f"
GENERATION_THIRTEEN_BATON_COMMIT = "2cde00658562b981cd4ab38051b8e08e621b3d83"
# Generation fourteen exists because Docker Engine 29 moved the daemon `Experimental` flag out of
# the top-level Server object into the Engine component's Details map as the string "true"/"false".
# Generation eleven repaired that projection in the environment capture only; the identical frozen
# assertion survived in both live launchers, so the nonanalytic smoke aborted at preflight with
# `docker-v3-runtime-binding` and the analytic launcher would have aborted the same way. Generation
# fourteen reads the top level first and falls back to the Engine component in both launchers, so
# each daemon generation projects to the same bool and every other recorded byte is unchanged.
GENERATION_THIRTEEN_MANIFEST_COMMIT = "1ba42bbb869c652fd6d3d951a3c92ec404f61e72"
GENERATION_FOURTEEN_SOURCE_PARENT = GENERATION_THIRTEEN_MANIFEST_COMMIT
GENERATION_FOURTEEN_REASON = "S1_SMOKE_AND_DOSE_DOCKER29_DAEMON_EXPERIMENTAL_SCHEMA_FOSSIL"
GENERATION_FOURTEEN_SOURCE_COMMIT = "4a62cc4127e9dc2fcea2dcbdd0acd3c6d790259b"
GENERATION_FOURTEEN_RECEIPT_COMMIT = "b260ca5b0910c4d499c13e42add97affd726b77c"
GENERATION_FOURTEEN_STATE_COMMIT = "a084198d89ece710a490363bdbf53f548cbd0456"
GENERATION_FOURTEEN_BATON_COMMIT = "69bd2e2face00ccabb426382347eb04e8a0dbe83"
GENERATION_FIFTEEN_SOURCE_PARENT = GENERATION_FOURTEEN_BATON_COMMIT
GENERATION_FIFTEEN_REASON = (
    "B14_H_DESCENDANT_CONTROLLER_OMISSION_GITHUB_RUN_AUTHORITY_"
    "AND_CI_FIXTURE_OBJECT_CONNECTIVITY_AND_RECEIPT_SCHEMA_EXACTNESS_"
    "AND_FALSE_IDLE_LEGACY_HANDOFF_REMOTE_PROBE_"
    "AND_RECEIPT_FAILURE_BOUNDARY_STOP"
)
GENERATION_FIFTEEN_SOURCE_COMMIT = "3bc8913fb8e7b09650fbf2b7370ac17a57f7e2d0"
GENERATION_FIFTEEN_RECEIPT_COMMIT = "80f4b37d7c7c1f2a917e68bdcb015f188299f1fe"
GENERATION_FIFTEEN_STATE_COMMIT = "5366d8f714d8d1c49e99f238ba4e88733d7904ab"
GENERATION_FIFTEEN_BATON_COMMIT = "21509ef2cdb634c02fac9310b57b7608b9878530"
GENERATION_SIXTEEN_SOURCE_PARENT = GENERATION_FIFTEEN_BATON_COMMIT
GENERATION_SIXTEEN_REASON = (
    "B15_SOURCE_BOUND_LIFECYCLE_CONTROL_AND_LIFECYCLE_EVIDENCE_SEPARATION_"
    "AND_NEXT_SOURCE_CONTENT_BINDING_BOOTSTRAP"
)
# Compatibility aliases used by the receipt generator and focused hostile tests. They always name
# the active generation-sixteen source publication, never a historical recovery.
# The generation-sixteen lifecycle-control source published as F16. Its hash became citable the
# moment it landed on canonical master, exactly like every earlier generation's commits.
GENERATION_SIXTEEN_SOURCE_COMMIT = "51370ccac79fd141f774ca462a4fdd8b8f3f5b55"
# The CI toolchain pin exists because the published CI lane installed an unpinned ruff and a
# newer release failed the generation-sixteen receipt lane after local verification was green.
# It amends the active generation-sixteen source with EXACTLY ONE additional commit: a single
# direct child of F16 whose committed path set pins ruff in CI and teaches the three publication
# validators (and their tests) this amended source resolution. The receipt is regenerated at the
# pin commit; F16's own published shape stays enforced below. The full content-addressed
# toolchain lock remains the CI_HARDENING (generation-seventeen) mission.
CI_TOOLCHAIN_PIN_SOURCE_PARENT = GENERATION_SIXTEEN_SOURCE_COMMIT
RECOVERY_SOURCE_PARENT = CI_TOOLCHAIN_PIN_SOURCE_PARENT
RECOVERY_REASON = GENERATION_SIXTEEN_REASON
POST_FREEZE_EXACT_PATHS = {
    "CONTINUITY.md",
    "HANDOFF.md",
    "MISSION_STATE.json",
    f"{EXPERIMENT_REL}/env_receipts.json",
    f"{EXPERIMENT_REL}/host_packet_manifest.json",
    f"{EXPERIMENT_REL}/host_preparation_receipt.json",
    f"{EXPERIMENT_REL}/launch_manifest.json",
    f"{EXPERIMENT_REL}/launch_activation_receipt.json",
}
SMOKE_DOSES = ("blind_0_5x", "blind_1_0x", "blind_1_5x", "blind_2_0x")
SMOKE_EVIDENCE_PATHS = tuple(
    sorted(
        {
            f"{EXPERIMENT_REL}/smoke-evidence/SMOKE.md",
            f"{EXPERIMENT_REL}/smoke-evidence/smoke_receipt.json",
            f"{EXPERIMENT_REL}/smoke-evidence/raw/execution.jsonl",
            f"{EXPERIMENT_REL}/smoke-evidence/raw/pre_smoke_manifest.json",
            f"{EXPERIMENT_REL}/smoke-evidence/raw/environment_receipt.json",
            f"{EXPERIMENT_REL}/smoke-evidence/raw/pre_smoke_mission_state.json",
            *{
                f"{EXPERIMENT_REL}/smoke-evidence/raw/{dose}.{suffix}"
                for dose in SMOKE_DOSES
                for suffix in ("decisions.jsonl", "model-env.bin", "compose.log")
            },
        }
    )
)
HOST_PACKET_MANIFEST_REL = f"{EXPERIMENT_REL}/host_packet_manifest.json"
HOST_PREPARATION_RECEIPT_REL = f"{EXPERIMENT_REL}/host_preparation_receipt.json"
ENVIRONMENT_RECEIPT_REL = f"{EXPERIMENT_REL}/env_receipts.json"
LAUNCH_MANIFEST_REL = f"{EXPERIMENT_REL}/launch_manifest.json"
LAUNCH_ACTIVATION_RECEIPT_REL = f"{EXPERIMENT_REL}/launch_activation_receipt.json"

# These are mandatory members of the frozen surface.  Discovery is deliberately open to
# additional test/Python files so a newly added Iter135 source cannot silently escape the receipt.
REQUIRED_TEST_FILES = (
    "tests/test_handoff_generator.py",
    "tests/test_iter131_post_iter130_mission_alignment_audit.py",
    "tests/test_iter135_analyzer.py",
    "tests/test_iter135_environment_capture.py",
    "tests/test_iter135_harness_patches.py",
    "tests/test_iter135_host_preparation.py",
    "tests/test_iter135_launch_authorization.py",
    "tests/test_iter135_launch_manifest.py",
    "tests/test_iter135_launcher.py",
    "tests/test_iter135_lifecycle_control.py",
    "tests/test_iter135_proof_collector.py",
    "tests/test_iter135_runtime_patches.py",
    "tests/test_iter135_schedule_tools.py",
    "tests/test_iter135_smoke_pipeline.py",
    "tests/test_iter135_tooling_verifier.py",
)
REQUIRED_PYTHON_TOOL_FILES = (
    f"{EXPERIMENT_REL}/analyze_dose135.py",
    f"{EXPERIMENT_REL}/authorize_launch135.py",
    f"{EXPERIMENT_REL}/capture_environment135.py",
    f"{EXPERIMENT_REL}/collect_proof135.py",
    f"{EXPERIMENT_REL}/extract_union_windows.py",
    f"{EXPERIMENT_REL}/generate_nested_dose_schedules.py",
    f"{EXPERIMENT_REL}/make_launch_manifest.py",
    f"{EXPERIMENT_REL}/patch_compose_dose_env.py",
    f"{EXPERIMENT_REL}/prepare_host135.py",
    f"{EXPERIMENT_REL}/server_patch_blind_dose.py",
    f"{EXPERIMENT_REL}/server_patch_union_release.py",
    f"{EXPERIMENT_REL}/validate_smoke135.py",
    f"{EXPERIMENT_REL}/validate_lifecycle135.py",
    f"{EXPERIMENT_REL}/verify_tooling135.py",
)
REQUIRED_SHELL_FILES = (
    f"{EXPERIMENT_REL}/run_dose135.sh",
    f"{EXPERIMENT_REL}/run_smoke135.sh",
)
REQUIRED_DATA_FILES = (f"{EXPERIMENT_REL}/dose_schedules.json",)
REQUIRED_CONTROL_FILES = (
    ".github/workflows/ci.yml",
    "CONTINUITY.md",
    "HANDOFF.md",
    "MISSION_STATE.json",
    "README.md",
    "docs/NEXT_PHASE.md",
    "docs/REPORT.md",
    "docs/paper/STATUS.md",
    "docs/research/BENCH2DRIVE_ROBUST_PREFLIGHT_2026-07-16.md",
    "docs/research/FRONTIER_ALIGNMENT_MEMORY_2026-07-13.md",
    "docs/research/ITER135_SOURCE_BOUND_LIFECYCLE_CONTROL_PREREGISTRATION_2026-07-21.md",
    "pyproject.toml",
    "scripts/make_handoff.py",
    "scripts/mission_state.py",
    "scripts/validate_docs.py",
    "tests/test_mission_state.py",
    f"{EXPERIMENT_REL}/HYPOTHESIS.md",
)
GENERATION_ONE_SOURCE_COMMIT_PATHS = (
    "CONTINUITY.md",
    "MISSION_STATE.json",
    "README.md",
    "docs/research/BENCH2DRIVE_ROBUST_PREFLIGHT_2026-07-16.md",
    "docs/research/FRONTIER_ALIGNMENT_MEMORY_2026-07-13.md",
    f"{EXPERIMENT_REL}/analyze_dose135.py",
    f"{EXPERIMENT_REL}/capture_environment135.py",
    f"{EXPERIMENT_REL}/collect_proof135.py",
    f"{EXPERIMENT_REL}/dose_schedules.json",
    f"{EXPERIMENT_REL}/extract_union_windows.py",
    f"{EXPERIMENT_REL}/generate_nested_dose_schedules.py",
    f"{EXPERIMENT_REL}/make_launch_manifest.py",
    f"{EXPERIMENT_REL}/patch_compose_dose_env.py",
    f"{EXPERIMENT_REL}/run_dose135.sh",
    f"{EXPERIMENT_REL}/run_smoke135.sh",
    f"{EXPERIMENT_REL}/server_patch_blind_dose.py",
    f"{EXPERIMENT_REL}/server_patch_union_release.py",
    f"{EXPERIMENT_REL}/validate_smoke135.py",
    f"{EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/mission_state.py",
    "tests/test_iter135_analyzer.py",
    "tests/test_iter135_environment_capture.py",
    "tests/test_iter135_harness_patches.py",
    "tests/test_iter135_launch_manifest.py",
    "tests/test_iter135_launcher.py",
    "tests/test_iter135_proof_collector.py",
    "tests/test_iter135_runtime_patches.py",
    "tests/test_iter135_schedule_tools.py",
    "tests/test_iter135_smoke_pipeline.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
GENERATION_TWO_SOURCE_COMMIT_PATHS = (
    ".github/workflows/ci.yml",
    "CONTINUITY.md",
    "HANDOFF.md",
    "MISSION_STATE.json",
    f"{EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/mission_state.py",
    "tests/test_iter135_smoke_pipeline.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
GENERATION_THREE_SOURCE_COMMIT_PATHS = (
    ".github/workflows/ci.yml",
    "CONTINUITY.md",
    "HANDOFF.md",
    "MISSION_STATE.json",
    f"{EXPERIMENT_REL}/analyze_dose135.py",
    f"{EXPERIMENT_REL}/authorize_launch135.py",
    f"{EXPERIMENT_REL}/capture_environment135.py",
    f"{EXPERIMENT_REL}/collect_proof135.py",
    f"{EXPERIMENT_REL}/make_launch_manifest.py",
    f"{EXPERIMENT_REL}/prepare_host135.py",
    f"{EXPERIMENT_REL}/run_dose135.sh",
    f"{EXPERIMENT_REL}/run_smoke135.sh",
    f"{EXPERIMENT_REL}/validate_smoke135.py",
    f"{EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/mission_state.py",
    "tests/test_iter135_analyzer.py",
    "tests/test_iter135_environment_capture.py",
    "tests/test_iter135_host_preparation.py",
    "tests/test_iter135_launch_authorization.py",
    "tests/test_iter135_launch_manifest.py",
    "tests/test_iter135_launcher.py",
    "tests/test_iter135_proof_collector.py",
    "tests/test_iter135_smoke_pipeline.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
GENERATION_FOUR_SOURCE_COMMIT_PATHS = (
    "CONTINUITY.md",
    "HANDOFF.md",
    "MISSION_STATE.json",
    f"{EXPERIMENT_REL}/authorize_launch135.py",
    f"{EXPERIMENT_REL}/run_dose135.sh",
    f"{EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/mission_state.py",
    "tests/test_iter135_launch_authorization.py",
    "tests/test_iter135_launcher.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
GENERATION_FIVE_SOURCE_COMMIT_PATHS = (
    "CONTINUITY.md",
    "HANDOFF.md",
    "MISSION_STATE.json",
    f"{EXPERIMENT_REL}/authorize_launch135.py",
    f"{EXPERIMENT_REL}/prepare_host135.py",
    f"{EXPERIMENT_REL}/run_dose135.sh",
    f"{EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/mission_state.py",
    "tests/test_iter135_host_preparation.py",
    "tests/test_iter135_launch_authorization.py",
    "tests/test_iter135_launcher.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
GENERATION_SIX_SOURCE_COMMIT_PATHS = (
    "CONTINUITY.md",
    "HANDOFF.md",
    f"{EXPERIMENT_REL}/authorize_launch135.py",
    f"{EXPERIMENT_REL}/run_dose135.sh",
    f"{EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/mission_state.py",
    "tests/test_iter135_launch_authorization.py",
    "tests/test_iter135_launcher.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
GENERATION_SEVEN_SOURCE_COMMIT_PATHS = (
    "CONTINUITY.md",
    "HANDOFF.md",
    "MISSION_STATE.json",
    f"{EXPERIMENT_REL}/authorize_launch135.py",
    f"{EXPERIMENT_REL}/prepare_host135.py",
    f"{EXPERIMENT_REL}/run_dose135.sh",
    f"{EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/mission_state.py",
    "tests/test_iter135_host_preparation.py",
    "tests/test_iter135_launch_authorization.py",
    "tests/test_iter135_launcher.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
GENERATION_EIGHT_SOURCE_COMMIT_PATHS = (
    "CONTINUITY.md",
    "HANDOFF.md",
    "MISSION_STATE.json",
    f"{EXPERIMENT_REL}/authorize_launch135.py",
    f"{EXPERIMENT_REL}/run_dose135.sh",
    f"{EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/mission_state.py",
    "tests/test_iter135_launch_authorization.py",
    "tests/test_iter135_launcher.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
GENERATION_NINE_SOURCE_COMMIT_PATHS = (
    "CONTINUITY.md",
    "HANDOFF.md",
    "MISSION_STATE.json",
    f"{EXPERIMENT_REL}/authorize_launch135.py",
    f"{EXPERIMENT_REL}/capture_environment135.py",
    f"{EXPERIMENT_REL}/run_dose135.sh",
    f"{EXPERIMENT_REL}/run_smoke135.sh",
    f"{EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/mission_state.py",
    "tests/test_iter135_environment_capture.py",
    "tests/test_iter135_launch_authorization.py",
    "tests/test_iter135_launcher.py",
    "tests/test_iter135_smoke_pipeline.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
GENERATION_TEN_SOURCE_COMMIT_PATHS = (
    "CONTINUITY.md",
    "HANDOFF.md",
    "MISSION_STATE.json",
    f"{EXPERIMENT_REL}/authorize_launch135.py",
    f"{EXPERIMENT_REL}/capture_environment135.py",
    f"{EXPERIMENT_REL}/run_dose135.sh",
    f"{EXPERIMENT_REL}/run_smoke135.sh",
    f"{EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/mission_state.py",
    "tests/test_iter135_environment_capture.py",
    "tests/test_iter135_launch_authorization.py",
    "tests/test_iter135_launcher.py",
    "tests/test_iter135_smoke_pipeline.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
GENERATION_ELEVEN_SOURCE_COMMIT_PATHS = (
    "CONTINUITY.md",
    "HANDOFF.md",
    "LICENSE",
    "MISSION_STATE.json",
    f"{EXPERIMENT_REL}/analyze_dose135.py",
    f"{EXPERIMENT_REL}/authorize_launch135.py",
    f"{EXPERIMENT_REL}/capture_environment135.py",
    f"{EXPERIMENT_REL}/collect_proof135.py",
    f"{EXPERIMENT_REL}/make_launch_manifest.py",
    f"{EXPERIMENT_REL}/run_dose135.sh",
    f"{EXPERIMENT_REL}/run_smoke135.sh",
    f"{EXPERIMENT_REL}/validate_smoke135.py",
    f"{EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/mission_state.py",
    "tests/test_iter135_environment_capture.py",
    "tests/test_iter135_launch_authorization.py",
    "tests/test_iter135_launch_manifest.py",
    "tests/test_iter135_launcher.py",
    "tests/test_iter135_proof_collector.py",
    "tests/test_iter135_smoke_pipeline.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
GENERATION_TWELVE_SOURCE_COMMIT_PATHS = (
    "CONTINUITY.md",
    "HANDOFF.md",
    "MISSION_STATE.json",
    f"{EXPERIMENT_REL}/authorize_launch135.py",
    f"{EXPERIMENT_REL}/run_dose135.sh",
    f"{EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/mission_state.py",
    "tests/test_iter135_launch_authorization.py",
    "tests/test_iter135_launcher.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
GENERATION_THIRTEEN_SOURCE_COMMIT_PATHS = GENERATION_TWELVE_SOURCE_COMMIT_PATHS
# Generation fourteen repairs the Docker Engine 29 daemon-schema fossil inside the nonanalytic
# smoke launcher as well, so its scope is the generation-thirteen set plus run_smoke135.sh.
GENERATION_FOURTEEN_SOURCE_COMMIT_PATHS = tuple(
    sorted({*GENERATION_THIRTEEN_SOURCE_COMMIT_PATHS, f"{EXPERIMENT_REL}/run_smoke135.sh"})
)
GENERATION_FIFTEEN_SOURCE_COMMIT_PATHS = (
    "CONTINUITY.md",
    "HANDOFF.md",
    "MISSION_STATE.json",
    f"{EXPERIMENT_REL}/authorize_launch135.py",
    f"{EXPERIMENT_REL}/capture_environment135.py",
    f"{EXPERIMENT_REL}/prepare_host135.py",
    f"{EXPERIMENT_REL}/run_dose135.sh",
    f"{EXPERIMENT_REL}/run_smoke135.sh",
    f"{EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/make_handoff.py",
    "scripts/mission_state.py",
    "tests/test_handoff_generator.py",
    "tests/test_iter135_environment_capture.py",
    "tests/test_iter135_host_preparation.py",
    "tests/test_iter135_launch_authorization.py",
    "tests/test_iter135_launcher.py",
    "tests/test_iter135_smoke_pipeline.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
GENERATION_SIXTEEN_SOURCE_COMMIT_PATHS = (
    "CONTINUITY.md",
    "HANDOFF.md",
    "README.md",
    "docs/NEXT_PHASE.md",
    "docs/REPORT.md",
    "docs/research/ITER135_SOURCE_BOUND_LIFECYCLE_CONTROL_PREREGISTRATION_2026-07-21.md",
    f"{EXPERIMENT_REL}/authorize_launch135.py",
    f"{EXPERIMENT_REL}/validate_lifecycle135.py",
    f"{EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/make_handoff.py",
    "scripts/mission_state.py",
    "tests/test_handoff_generator.py",
    "tests/test_iter131_post_iter130_mission_alignment_audit.py",
    "tests/test_iter135_launch_authorization.py",
    "tests/test_iter135_lifecycle_control.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
# The exact committed path set of the CI toolchain pin commit — the active generation-sixteen
# source amendment. It contains the machinery files themselves because the pin commit is
# self-admitting in the established F16 bootstrap idiom.
CI_TOOLCHAIN_PIN_COMMIT_PATHS = (
    ".github/workflows/ci.yml",
    f"{EXPERIMENT_REL}/authorize_launch135.py",
    f"{EXPERIMENT_REL}/verify_tooling135.py",
    "scripts/mission_state.py",
    "tests/test_iter135_launch_authorization.py",
    "tests/test_iter135_tooling_verifier.py",
    "tests/test_mission_state.py",
)
# One reviewed documentation-correction tranche is pre-registered as the only lawful commit
# after the generation-sixteen baton: a single direct child of B16 with exactly this path set,
# leaving MISSION_STATE.json byte-identical to T16's. It is not a general docs allowance.
DOCUMENTATION_CORRECTION_TRANCHE_COMMIT_PATHS = (
    "REVIEWER.md",
    "docs/CAMPAIGN.md",
    "docs/paper/MANUSCRIPT.md",
    "docs/paper/STATUS.md",
    "scripts/mission_state.py",
    "tests/test_mission_state.py",
)
RECOVERY_SOURCE_COMMIT_PATHS = CI_TOOLCHAIN_PIN_COMMIT_PATHS
EXPECTED_RECOVERY_PUBLICATION = {
    "generation": 16,
    "supersedes_receipt_commit": GENERATION_FIFTEEN_RECEIPT_COMMIT,
    "recovery_parent": GENERATION_SIXTEEN_SOURCE_PARENT,
    "reason_code": GENERATION_SIXTEEN_REASON,
}
CI_HARDENING_AUTHORIZED_ACTIONS = (
    "implement and validate only offline, content-addressed CI inputs, exact dependency locks, "
    "supply-chain manifests, independent evidence replay, and known-bad controls",
    "retain the accepted lifecycle-control source without running a host observer or changing "
    "external governance settings",
)
CI_HARDENING_FORBIDDEN_ACTIONS = (
    "access, inventory, prepare, mutate, or execute on any iteration-135 remote host, provider, "
    "filesystem, packet, runtime, lock, container, GPU, credential, or evidence path",
    "create, execute, publish, or advance any H, E, P, or S descendant; lifecycle observation; "
    "launch activation; live smoke; or analytic episode",
    "infer IDLE, termination, completion, readiness, approval, authority, hermeticity, "
    "authenticity, reproducibility, or SLSA conformance from a green workflow or incomplete proof",
    "run analyzers or publish iteration-135 data, results, claims, figures, paper text, or "
    "scientific conclusions",
    "change branch protection, rulesets, Actions policy, repository visibility, credentials, "
    "secrets, access control, or other external governance settings without explicit operator "
    "authorization",
    "rerun iteration 134 or adapt iteration-135 schedules, estimands, verdicts, or policies after "
    "evidence",
)

# Compatibility names describe only the immutable first freeze.  Recovery publication checks use
# the separate paired parent/scope contract above; never substitute the nine recovery paths for
# the full generation-one frozen surface.
EXPECTED_PREREGISTRATION_HEAD = GENERATION_ONE_SOURCE_PARENT
EXPECTED_SOURCE_COMMIT_PATHS = GENERATION_ONE_SOURCE_COMMIT_PATHS

DISCOVERY_CONTRACT = (
    "required frozen members plus every top-level experiment *.py and every top-level "
    "tests/test_iter135_*.py; exact offline-handoff test, exact two shell launchers, "
    "dose_schedules.json, and frozen CI/test/mission control inputs; receipt JSON excluded"
)


class VerificationError(RuntimeError):
    """A fail-closed discovery, snapshot, or receipt error."""


class NextSourceBindingCommittedError(VerificationError):
    """The immutable final binding exists, but a post-link condition failed."""


class NextSourceBindingIndeterminateError(VerificationError):
    """The link outcome cannot be classified without independent inspection."""


@dataclass(frozen=True)
class Inventory:
    tests: tuple[str, ...]
    python_tools: tuple[str, ...]
    shell_files: tuple[str, ...]
    data_files: tuple[str, ...]
    control_files: tuple[str, ...]

    @property
    def python_files(self) -> tuple[str, ...]:
        return tuple(sorted((*self.python_tools, *self.tests)))

    @property
    def tested_files(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                (
                    *self.tests,
                    *self.python_tools,
                    *self.shell_files,
                    *self.data_files,
                    *self.control_files,
                )
            )
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "contract": DISCOVERY_CONTRACT,
            "tests": list(self.tests),
            "python_tools": list(self.python_tools),
            "python_files": list(self.python_files),
            "shell_files": list(self.shell_files),
            "data_files": list(self.data_files),
            "control_files": list(self.control_files),
            "tested_files": list(self.tested_files),
        }


@dataclass(frozen=True)
class FileFingerprint:
    sha256: str
    bytes: int
    device: int
    inode: int
    mode: int
    mtime_ns: int
    ctime_ns: int

    def public(self) -> dict[str, Any]:
        return {
            "sha256": self.sha256,
            "bytes": self.bytes,
            "execution_identity": {
                "device": self.device,
                "inode": self.inode,
                "mode": self.mode,
                "mtime_ns": self.mtime_ns,
                "ctime_ns": self.ctime_ns,
            },
        }


@dataclass(frozen=True)
class RawCommandResult:
    returncode: int
    stdout: bytes = b""
    stderr: bytes = b""


@dataclass(frozen=True)
class GitState:
    head: str
    dirty_entries: tuple[str, ...]
    porcelain_sha256: str
    branch: str = ""
    upstream: str = ""
    upstream_head: str = ""
    parents: tuple[str, ...] = ()
    commit_paths: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "head": self.head,
            "dirty_entries": list(self.dirty_entries),
            "porcelain_v1_z_sha256": self.porcelain_sha256,
            "branch": self.branch,
            "upstream": self.upstream,
            "upstream_head": self.upstream_head,
            "parents": list(self.parents),
            "commit_paths": list(self.commit_paths),
        }


Runner = Callable[[tuple[str, ...], Path], Any]
GitProbe = Callable[[Path, tuple[str, ...]], GitState]
AncestryProbe = Callable[[Path, str, str], bool]
ToolchainResolver = Callable[[], dict[str, dict[str, Any]]]
Clock = Callable[[], int]

TOOL_NAMES = ("pytest", "bash", "shellcheck", "ruff", "python3", "git")
ALLOWED_TOOL_ROOTS = (
    Path("/bin"),
    Path("/usr/bin"),
    Path("/usr/local"),
    Path("/opt/homebrew"),
    Path("/Library/Frameworks"),
    Path("/System/Cryptexes"),
)
TOOL_VERSION_ARGS = {
    "pytest": ("--version",),
    "bash": ("--version",),
    "shellcheck": ("--version",),
    "ruff": ("--version",),
    "python3": ("--version",),
    "git": ("--version",),
}


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _exact_json_value(observed: object, expected: object) -> bool:
    """Compare JSON values without bool/int or int/float equivalence."""

    if type(observed) is not type(expected):
        return False
    if type(expected) is dict:
        observed_dict = observed
        expected_dict = expected
        return set(observed_dict) == set(expected_dict) and all(
            _exact_json_value(observed_dict[key], expected_dict[key])
            for key in expected_dict
        )
    if type(expected) is list:
        observed_list = observed
        expected_list = expected
        return len(observed_list) == len(expected_list) and all(
            _exact_json_value(observed_item, expected_item)
            for observed_item, expected_item in zip(
                observed_list,
                expected_list,
                strict=True,
            )
        )
    return observed == expected


def _strict_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise VerificationError(f"duplicate receipt JSON key: {key}")
        value[key] = item
    return value


def _reject_nonfinite_json(value: str) -> None:
    raise VerificationError(f"non-finite receipt JSON number: {value}")


def _parse_receipt_json(payload: str | bytes) -> dict[str, Any]:
    value = json.loads(
        payload,
        object_pairs_hook=_strict_json_object,
        parse_constant=_reject_nonfinite_json,
    )
    if not isinstance(value, dict):
        raise VerificationError("receipt JSON root is not an object")
    return value


def _expected_ci_hardening_state(repo_root: Path) -> dict[str, Any]:
    """Derive T16 from the exact hash-bound B15 state without trusting working-tree code."""

    state = _parse_receipt_json(
        _git_file_bytes(
            repo_root,
            GENERATION_FIFTEEN_BATON_COMMIT,
            "MISSION_STATE.json",
        )
    )
    state["run_state"] = "UNKNOWN"
    state["next_program"] = {
        "iteration": 135,
        "name": "semantics-free placebo dose-response causal closure",
        "phase": "CI_HARDENING_REQUIRED",
        "authorized_actions": list(CI_HARDENING_AUTHORIZED_ACTIONS),
        "forbidden_actions": list(CI_HARDENING_FORBIDDEN_ACTIONS),
    }
    return state


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _is_exact_nonnegative_int(value: object) -> bool:
    return type(value) is int and value >= 0


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _canonical_utc_ns(value: object) -> int | None:
    if not isinstance(value, str) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError:
        return None
    if parsed.tzinfo != timezone.utc:
        return None
    if parsed.isoformat().replace("+00:00", "Z") != value:
        return None
    delta = parsed - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return (
        (delta.days * 86_400 + delta.seconds) * 1_000_000_000
        + delta.microseconds * 1_000
    )


def _nested_receipt_shape_errors(receipt: Mapping[str, Any]) -> list[str]:
    """Validate exact JSON shapes that do not depend on the current checkout."""

    errors: list[str] = []
    problem_count = receipt.get("problem_count")
    if type(problem_count) is not int or problem_count != 0:
        errors.append("problem_count is not exact integer zero")

    publication = receipt.get("publication")
    if type(publication) is not dict:
        errors.append("publication block malformed")
    else:
        if set(publication) != set(EXPECTED_RECOVERY_PUBLICATION):
            errors.append("publication field set mismatch")
        if type(publication.get("generation")) is not int:
            errors.append("publication generation is not an exact integer")
        for field in (
            "supersedes_receipt_commit",
            "recovery_parent",
            "reason_code",
        ):
            if type(publication.get(field)) is not str:
                errors.append(f"publication {field} malformed")

    repository = receipt.get("repository")
    if not isinstance(repository, Mapping):
        errors.append("repository block malformed")
    else:
        if set(repository) != REPOSITORY_FIELDS:
            errors.append("repository field set mismatch")
        if not isinstance(repository.get("root"), str):
            errors.append("repository root malformed")
        for flag in (
            "git_head_stable",
            "git_state_stable",
            "repository_clean_state_stable",
        ):
            if type(repository.get(flag)) is not bool:
                errors.append(f"repository {flag} is not a JSON boolean")
        for label in ("git_start", "git_end"):
            state = repository.get(label)
            if not isinstance(state, Mapping):
                errors.append(f"repository {label} block malformed")
                continue
            if set(state) != GIT_STATE_FIELDS:
                errors.append(f"repository {label} field set mismatch")
            for commit_field in ("head", "upstream_head"):
                if not _valid_commit(state.get(commit_field)):
                    errors.append(f"repository {label} {commit_field} malformed")
            if not _is_sha256(state.get("porcelain_v1_z_sha256")):
                errors.append(f"repository {label} status digest malformed")
            for text_field in ("branch", "upstream"):
                if not isinstance(state.get(text_field), str):
                    errors.append(f"repository {label} {text_field} malformed")
            dirty_entries = state.get("dirty_entries")
            if not isinstance(dirty_entries, list) or not all(
                isinstance(value, str) for value in dirty_entries
            ):
                errors.append(f"repository {label} dirty_entries malformed")
            parents = state.get("parents")
            if not isinstance(parents, list) or not all(_valid_commit(value) for value in parents):
                errors.append(f"repository {label} parents malformed")
            commit_paths = state.get("commit_paths")
            if not isinstance(commit_paths, list) or not all(
                isinstance(value, str) for value in commit_paths
            ):
                errors.append(f"repository {label} commit_paths malformed")

    toolchain = receipt.get("toolchain")
    if not isinstance(toolchain, Mapping):
        errors.append("toolchain block malformed")
    else:
        if set(toolchain) != set(TOOL_NAMES):
            errors.append("toolchain field set mismatch")
        for name in TOOL_NAMES:
            row = toolchain.get(name)
            if not isinstance(row, Mapping):
                errors.append(f"toolchain row malformed: {name}")
                continue
            if set(row) != TOOLCHAIN_ROW_FIELDS:
                errors.append(f"toolchain row field set mismatch: {name}")
            if not isinstance(row.get("path"), str) or not isinstance(row.get("version"), str):
                errors.append(f"toolchain text metadata malformed: {name}")
            if not _is_sha256(row.get("sha256")):
                errors.append(f"toolchain digest malformed: {name}")
            for field in ("bytes", "device", "inode"):
                if not _is_exact_nonnegative_int(row.get(field)):
                    errors.append(f"toolchain {field} malformed: {name}")
            mode = row.get("mode")
            if not _is_exact_nonnegative_int(mode) or mode > 0o7777:
                errors.append(f"toolchain mode malformed: {name}")
            for field in ("mtime_ns", "ctime_ns"):
                if type(row.get(field)) is not int:
                    errors.append(f"toolchain {field} malformed: {name}")

    files = receipt.get("files")
    if not isinstance(files, Mapping):
        errors.append("file binding map malformed")
    else:
        for relative_path, row in files.items():
            if not isinstance(relative_path, str) or not isinstance(row, Mapping):
                errors.append(f"file binding row malformed: {relative_path}")
                continue
            if set(row) != FILE_ROW_FIELDS:
                errors.append(f"file binding row field set mismatch: {relative_path}")
            if not _is_sha256(row.get("sha256")):
                errors.append(f"file binding digest malformed: {relative_path}")
            if not _is_exact_nonnegative_int(row.get("bytes")):
                errors.append(f"file binding byte count malformed: {relative_path}")
            identity = row.get("execution_identity")
            if not isinstance(identity, Mapping):
                errors.append(f"file execution_identity malformed: {relative_path}")
                continue
            if set(identity) != EXECUTION_IDENTITY_FIELDS:
                errors.append(
                    f"file execution_identity field set mismatch: {relative_path}"
                )
            for field in ("device", "inode"):
                if not _is_exact_nonnegative_int(identity.get(field)):
                    errors.append(
                        f"file execution_identity {field} malformed: {relative_path}"
                    )
            mode = identity.get("mode")
            if type(mode) is not int or not stat.S_ISREG(mode):
                errors.append(f"file execution_identity mode malformed: {relative_path}")
            for field in ("mtime_ns", "ctime_ns"):
                if type(identity.get(field)) is not int:
                    errors.append(
                        f"file execution_identity {field} malformed: {relative_path}"
                    )

    command_contract = receipt.get("command_contract")
    if not isinstance(command_contract, list) or not all(
        isinstance(command, list)
        and bool(command)
        and all(isinstance(argument, str) for argument in command)
        for command in command_contract
    ):
        errors.append("command contract shape malformed")

    commands = receipt.get("commands")
    if not isinstance(commands, list):
        errors.append("command result set malformed")
    else:
        for index, row in enumerate(commands):
            if not isinstance(row, Mapping):
                errors.append(f"command_{index} record malformed")
                continue
            if set(row) != COMMAND_ROW_FIELDS:
                errors.append(f"command_{index} field set mismatch")
            argv = row.get("argv")
            if not isinstance(argv, list) or not argv or not all(
                isinstance(argument, str) for argument in argv
            ):
                errors.append(f"command_{index} argv malformed")
            return_code = row.get("return_code")
            if type(return_code) is not int or return_code != 0:
                errors.append(f"command_{index} return_code is not exact integer zero")
            for stream in ("stdout", "stderr"):
                byte_count = row.get(f"{stream}_bytes")
                digest = row.get(f"{stream}_sha256")
                if not _is_exact_nonnegative_int(byte_count):
                    errors.append(f"command_{index} {stream} byte count malformed")
                if not _is_sha256(digest):
                    errors.append(f"command_{index} {stream} digest malformed")
                if (
                    _is_exact_nonnegative_int(byte_count)
                    and _is_sha256(digest)
                    and ((byte_count == 0) != (digest == _sha256_bytes(b"")))
                ):
                    errors.append(
                        f"command_{index} {stream} byte count and digest are inconsistent"
                    )

    timing = receipt.get("timing")
    if not isinstance(timing, Mapping):
        errors.append("timing block malformed")
    else:
        if set(timing) != TIMING_FIELDS:
            errors.append("timing field set mismatch")
        started_ns = _canonical_utc_ns(timing.get("started_at_utc"))
        finished_ns = _canonical_utc_ns(timing.get("finished_at_utc"))
        if started_ns is None:
            errors.append("timing started_at_utc is not canonical UTC")
        if finished_ns is None:
            errors.append("timing finished_at_utc is not canonical UTC")
        for field in ("wall_duration_ns", "monotonic_duration_ns"):
            if not _is_exact_nonnegative_int(timing.get(field)):
                errors.append(f"{field} malformed")
        wall_duration = timing.get("wall_duration_ns")
        if started_ns is not None and finished_ns is not None:
            if finished_ns < started_ns:
                errors.append("timing UTC timestamps are out of order")
            elif _is_exact_nonnegative_int(wall_duration) and abs(
                finished_ns - started_ns - wall_duration
            ) > WALL_TIMESTAMP_ROUNDING_BUDGET_NS:
                errors.append("timing wall duration is inconsistent with UTC timestamps")
    return errors


def _allowed_tool_path(path: Path) -> bool:
    return any(path == root or path.is_relative_to(root) for root in ALLOWED_TOOL_ROOTS)


def _stable_external_file(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path:
        raise VerificationError(f"tool executable is not a physical regular file: {path}")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    digest = hashlib.sha256()
    byte_count = 0
    try:
        before = os.fstat(descriptor)
        while chunk := os.read(descriptor, 1024 * 1024):
            digest.update(chunk)
            byte_count += len(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    path_after = path.stat(follow_symlinks=False)
    before_row = (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    after_row = (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    path_row = (
        path_after.st_dev,
        path_after.st_ino,
        path_after.st_mode,
        path_after.st_size,
        path_after.st_mtime_ns,
        path_after.st_ctime_ns,
    )
    if before_row != after_row or before_row != path_row or byte_count != before.st_size:
        raise VerificationError(f"tool executable changed while hashing: {path}")
    return {
        "path": str(path),
        "sha256": digest.hexdigest(),
        "bytes": byte_count,
        "device": before.st_dev,
        "inode": before.st_ino,
        "mode": stat.S_IMODE(before.st_mode),
        "mtime_ns": before.st_mtime_ns,
        "ctime_ns": before.st_ctime_ns,
    }


def _sanitized_environment_for_paths(paths: Sequence[str]) -> dict[str, str]:
    directories = []
    for executable in paths:
        path = str(Path(executable).parent)
        if path not in directories:
            directories.append(path)
    for path in ("/usr/bin", "/bin", "/usr/sbin", "/sbin"):
        if path not in directories:
            directories.append(path)
    return {
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.pathsep.join(directories),
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
        "TZ": "UTC",
    }


def _sanitized_environment(toolchain: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
    return _sanitized_environment_for_paths(
        [str(toolchain[name]["path"]) for name in TOOL_NAMES]
    )


def _sanitized_git_environment(git: Mapping[str, Any]) -> dict[str, str]:
    """Build a Git-only environment without consulting the verification toolchain."""

    return _sanitized_environment_for_paths([str(git["path"])])


def _hardened_git_environment(git: Mapping[str, Any]) -> dict[str, str]:
    """Return the offline object-reader environment used by the next-source binder."""

    environment = _sanitized_git_environment(git)
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": "/dev/null",
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return environment


def _hardened_git_argv(
    git: Mapping[str, Any], repo_root: Path, *argv: str
) -> tuple[str, ...]:
    return (
        str(git["path"]),
        "--no-replace-objects",
        "-C",
        str(repo_root),
        f"--work-tree={repo_root.resolve(strict=False)}",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.untrackedCache=false",
        "-c",
        "core.hooksPath=/dev/null",
        *argv,
    )


@lru_cache(maxsize=8)
def _resolve_toolchain_cached(
    candidates: tuple[tuple[str, str, int, int, int, int, int], ...],
) -> dict[str, dict[str, Any]]:
    receipts: dict[str, dict[str, Any]] = {}
    for name, path_text, *_identity in candidates:
        physical = Path(path_text)
        receipts[name] = _stable_external_file(physical)
    environment = _sanitized_environment(receipts)
    for name in TOOL_NAMES:
        completed = subprocess.run(  # noqa: S603 - exact physical binary resolved above
            (receipts[name]["path"], *TOOL_VERSION_ARGS[name]),
            cwd=REPO_ROOT,
            env=environment,
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=10,
        )
        if completed.returncode != 0:
            raise VerificationError(f"verification executable version probe failed: {name}")
        first_line = completed.stdout.decode("utf-8", errors="replace").splitlines()
        receipts[name]["version"] = first_line[0] if first_line else ""
    return receipts


def resolve_toolchain() -> dict[str, dict[str, Any]]:
    candidates = []
    for name in TOOL_NAMES:
        located = shutil.which(name)
        if not located:
            raise VerificationError(f"required verification executable is missing: {name}")
        physical = Path(located).resolve(strict=True)
        if not _allowed_tool_path(physical):
            raise VerificationError(f"verification executable is outside trusted roots: {name}")
        observed = physical.stat(follow_symlinks=False)
        candidates.append(
            (
                name,
                str(physical),
                observed.st_dev,
                observed.st_ino,
                observed.st_size,
                observed.st_mtime_ns,
                observed.st_ctime_ns,
            )
        )
    return _resolve_toolchain_cached(tuple(candidates))


@lru_cache(maxsize=8)
def _resolve_git_cached(
    candidate: tuple[str, int, int, int, int, int],
) -> dict[str, Any]:
    """Bind and version only the trusted Git executable needed for history reads."""

    path_text, *_identity = candidate
    receipt = _stable_external_file(Path(path_text))
    completed = subprocess.run(  # noqa: S603 - exact physical Git binary resolved above
        (receipt["path"], *TOOL_VERSION_ARGS["git"]),
        cwd=REPO_ROOT,
        env=_sanitized_git_environment(receipt),
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=10,
    )
    if completed.returncode != 0:
        raise VerificationError("Git executable version probe failed")
    first_line = completed.stdout.decode("utf-8", errors="replace").splitlines()
    receipt["version"] = first_line[0] if first_line else ""
    return receipt


def resolve_git() -> dict[str, Any]:
    """Resolve one physical trusted Git binary without resolving pytest, Ruff, or peers."""

    located = shutil.which("git")
    if not located:
        raise VerificationError("required Git executable is missing")
    physical = Path(located).resolve(strict=True)
    if not _allowed_tool_path(physical):
        raise VerificationError("Git executable is outside trusted roots")
    observed = physical.stat(follow_symlinks=False)
    return _resolve_git_cached(
        (
            str(physical),
            observed.st_dev,
            observed.st_ino,
            observed.st_size,
            observed.st_mtime_ns,
            observed.st_ctime_ns,
        )
    )


def _utc_from_ns(value: int) -> str:
    return datetime.fromtimestamp(value / 1_000_000_000, tz=timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )


def _relative_regular_files(root: Path, pattern: str) -> tuple[str, ...]:
    paths: list[str] = []
    for path in root.glob(pattern):
        if path.is_symlink():
            raise VerificationError(f"symlink is forbidden in tested source inventory: {path}")
        if not path.is_file():
            continue
        paths.append(path.relative_to(root).as_posix())
    return tuple(sorted(paths))


def discover_inventory(repo_root: Path) -> Inventory:
    """Discover the exact focused surface, with frozen members as a mandatory floor."""

    root = repo_root.resolve(strict=True)
    tests = tuple(
        sorted(
                {
                    *_relative_regular_files(root, "tests/test_iter135_*.py"),
                    *_relative_regular_files(root, "tests/test_handoff_generator.py"),
                    *_relative_regular_files(
                        root,
                        "tests/test_iter131_post_iter130_mission_alignment_audit.py",
                    ),
                }
        )
    )
    python_tools = _relative_regular_files(root, f"{EXPERIMENT_REL}/*.py")
    shell_discovered = _relative_regular_files(root, f"{EXPERIMENT_REL}/*.sh")
    forbidden_configs = [
        relative
        for relative in (
            "pytest.ini",
            "tox.ini",
            "setup.cfg",
            "ruff.toml",
            ".ruff.toml",
            ".shellcheckrc",
            "conftest.py",
        )
        if (root / relative).exists() or (root / relative).is_symlink()
    ]
    for test_root in (root / "tests", root / "engine", root / "method"):
        if test_root.is_dir() and not test_root.is_symlink():
            forbidden_configs.extend(
                path.relative_to(root).as_posix()
                for path in test_root.rglob("conftest.py")
                if path.exists() or path.is_symlink()
            )

    missing_tests = sorted(set(REQUIRED_TEST_FILES) - set(tests))
    missing_tools = sorted(set(REQUIRED_PYTHON_TOOL_FILES) - set(python_tools))
    missing_shell = sorted(set(REQUIRED_SHELL_FILES) - set(shell_discovered))
    unexpected_shell = sorted(set(shell_discovered) - set(REQUIRED_SHELL_FILES))
    missing_data = sorted(
        rel for rel in REQUIRED_DATA_FILES if not (root / rel).is_file() or (root / rel).is_symlink()
    )
    missing_controls = sorted(
        rel
        for rel in REQUIRED_CONTROL_FILES
        if not (root / rel).is_file() or (root / rel).is_symlink()
    )
    if missing_tests:
        raise VerificationError(f"required focused tests missing: {missing_tests}")
    if missing_tools:
        raise VerificationError(f"required Python tooling missing: {missing_tools}")
    if missing_shell:
        raise VerificationError(f"required shell tooling missing: {missing_shell}")
    if unexpected_shell:
        raise VerificationError(f"unreviewed Iter135 shell tooling present: {unexpected_shell}")
    if missing_data:
        raise VerificationError(f"required tooling data missing: {missing_data}")
    if missing_controls:
        raise VerificationError(f"required control files missing: {missing_controls}")
    if forbidden_configs:
        raise VerificationError(
            f"unbound command-influencing configuration present: {sorted(forbidden_configs)}"
        )

    inventory = Inventory(
        tests=tests,
        python_tools=python_tools,
        shell_files=tuple(sorted(REQUIRED_SHELL_FILES)),
        data_files=tuple(sorted(REQUIRED_DATA_FILES)),
        control_files=tuple(sorted(REQUIRED_CONTROL_FILES)),
    )
    if RECEIPT_REL in inventory.tested_files:
        raise VerificationError("receipt output entered tested-source inventory")
    if len(inventory.tested_files) != len(set(inventory.tested_files)):
        raise VerificationError("duplicate tested-source inventory member")
    return inventory


def _fingerprint_file(repo_root: Path, relative_path: str) -> FileFingerprint:
    root = repo_root.resolve(strict=True)
    path = root / relative_path
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise VerificationError(f"tested source unavailable: {relative_path}") from exc
    if resolved != path.absolute():
        raise VerificationError(f"tested source traverses a symlink: {relative_path}")
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise VerificationError(f"tested source escapes repository: {relative_path}") from exc

    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise VerificationError(f"cannot open tested source: {relative_path}") from exc
    digest = hashlib.sha256()
    byte_count = 0
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise VerificationError(f"tested source is not regular: {relative_path}")
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            byte_count += len(chunk)
        after = os.fstat(fd)
    finally:
        os.close(fd)
    final_path = path.lstat()
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    identity_path = (
        final_path.st_dev,
        final_path.st_ino,
        final_path.st_mode,
        final_path.st_size,
        final_path.st_mtime_ns,
        final_path.st_ctime_ns,
    )
    if identity_before != identity_after or identity_after != identity_path:
        raise VerificationError(f"tested source changed while hashing: {relative_path}")
    if byte_count != after.st_size:
        raise VerificationError(f"tested source byte count raced: {relative_path}")
    return FileFingerprint(
        sha256=digest.hexdigest(),
        bytes=byte_count,
        device=after.st_dev,
        inode=after.st_ino,
        mode=after.st_mode,
        mtime_ns=after.st_mtime_ns,
        ctime_ns=after.st_ctime_ns,
    )


def snapshot_files(repo_root: Path, relative_paths: Sequence[str]) -> dict[str, FileFingerprint]:
    return {rel: _fingerprint_file(repo_root, rel) for rel in sorted(relative_paths)}


def _snapshot_public(snapshot: Mapping[str, FileFingerprint]) -> dict[str, Any]:
    return {rel: value.public() for rel, value in sorted(snapshot.items())}


def _content_projection(snapshot: Mapping[str, FileFingerprint]) -> dict[str, Any]:
    return {
        rel: {"sha256": value.sha256, "bytes": value.bytes}
        for rel, value in sorted(snapshot.items())
    }


def build_commands(
    inventory: Inventory,
    toolchain: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[tuple[str, ...], ...]:
    """Return the canonical, shell-free command contract in execution order."""

    tools = toolchain or resolve_toolchain()
    return (
        (str(tools["pytest"]["path"]), "-q", *inventory.tests),
        (str(tools["bash"]["path"]), "-n", "--", inventory.shell_files[0]),
        (str(tools["bash"]["path"]), "-n", "--", inventory.shell_files[1]),
        (
            str(tools["shellcheck"]["path"]),
            "--rcfile",
            "/dev/null",
            "--",
            *inventory.shell_files,
        ),
        (str(tools["ruff"]["path"]), "check", "."),
        (str(tools["pytest"]["path"]), "-q"),
        (str(tools["python3"]["path"]), "scripts/validate_docs.py"),
        (str(tools["python3"]["path"]), "scripts/mission_state.py"),
    )


def default_runner(command: tuple[str, ...], cwd: Path) -> RawCommandResult:
    toolchain = resolve_toolchain()
    try:
        completed = subprocess.run(  # noqa: S603 - command is a frozen argv tuple, never a shell
            command,
            cwd=cwd,
            env=_sanitized_environment(toolchain),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3_600,
        )
    except subprocess.TimeoutExpired as exc:
        return RawCommandResult(
            returncode=124,
            stdout=exc.stdout or b"",
            stderr=exc.stderr or b"",
        )
    return RawCommandResult(completed.returncode, completed.stdout, completed.stderr)


def _git_bytes(repo_root: Path, argv: Sequence[str]) -> bytes:
    git = resolve_git()
    completed = subprocess.run(  # noqa: S603 - fixed git command and validated source paths
        _hardened_git_argv(git, repo_root, *argv),
        env=_hardened_git_environment(git),
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    if completed.returncode != 0:
        raise VerificationError(
            f"Git provenance command failed with return code {completed.returncode}"
        )
    return completed.stdout


def default_git_probe(repo_root: Path, relative_paths: tuple[str, ...]) -> GitState:
    head_raw = _git_bytes(repo_root, ("rev-parse", "--verify", "HEAD"))
    head = head_raw.decode("ascii", errors="strict").strip()
    if len(head) != 40 or any(char not in "0123456789abcdef" for char in head):
        raise VerificationError("Git HEAD is not a lowercase 40-hex commit")
    branch = _git_bytes(repo_root, ("symbolic-ref", "--quiet", "--short", "HEAD")).decode(
        "utf-8", errors="strict"
    ).strip()
    upstream = _git_bytes(
        repo_root, ("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    ).decode("utf-8", errors="strict").strip()
    upstream_head = _git_bytes(repo_root, ("rev-parse", "--verify", "@{u}")).decode(
        "ascii", errors="strict"
    ).strip()
    if len(upstream_head) != 40 or any(
        character not in "0123456789abcdef" for character in upstream_head
    ):
        raise VerificationError("Git upstream HEAD is not a lowercase 40-hex commit")
    parent_fields = _git_bytes(repo_root, ("rev-list", "--parents", "-n", "1", "HEAD")).decode(
        "ascii", errors="strict"
    ).strip().split()
    if not parent_fields or parent_fields[0] != head:
        raise VerificationError("Git parent receipt does not start with HEAD")
    parents = tuple(parent_fields[1:])
    commit_paths = tuple(
        sorted(
            field.decode("utf-8", errors="surrogateescape")
            for field in _git_bytes(
                repo_root,
                (
                    "diff-tree",
                    "--root",
                    "--no-commit-id",
                    "--name-only",
                    "-r",
                    "-z",
                    "HEAD",
                ),
            ).split(b"\0")
            if field
        )
    )
    del relative_paths
    status = _git_bytes(
        repo_root,
        (
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        ),
    )
    entries = tuple(
        field.decode("utf-8", errors="surrogateescape")
        for field in status.split(b"\0")
        if field
    )
    return GitState(
        head=head,
        dirty_entries=entries,
        porcelain_sha256=_sha256_bytes(status),
        branch=branch,
        upstream=upstream,
        upstream_head=upstream_head,
        parents=parents,
        commit_paths=commit_paths,
    )


def default_structural_git_probe(
    repo_root: Path, relative_paths: tuple[str, ...]
) -> GitState:
    """Inspect published history without requiring a checked-out branch or configured upstream."""

    head = _git_bytes(repo_root, ("rev-parse", "--verify", "HEAD^{commit}"))
    head_text = head.decode("ascii", errors="strict").strip()
    if not _valid_commit(head_text):
        raise VerificationError("structural Git HEAD is not a lowercase 40-hex commit")
    origin_head = _git_bytes(
        repo_root,
        ("rev-parse", "--verify", "refs/remotes/origin/master^{commit}"),
    ).decode("ascii", errors="strict").strip()
    if not _valid_commit(origin_head):
        raise VerificationError("origin/master is not a lowercase 40-hex commit")
    parents, commit_paths = _git_commit_row(repo_root, head_text)
    del relative_paths
    status = _git_bytes(
        repo_root,
        (
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
        ),
    )
    entries = tuple(
        field.decode("utf-8", errors="surrogateescape")
        for field in status.split(b"\0")
        if field
    )
    return GitState(
        head=head_text,
        dirty_entries=entries,
        porcelain_sha256=_sha256_bytes(status),
        upstream_head=origin_head,
        parents=parents,
        commit_paths=commit_paths,
    )


def default_ancestry_probe(repo_root: Path, ancestor: str, descendant: str) -> bool:
    """Return whether ANCESTOR is reachable from DESCENDANT, failing closed on Git errors."""

    git = resolve_git()
    completed = subprocess.run(  # noqa: S603 - commits are validated lowercase 40-hex IDs
        _hardened_git_argv(
            git,
            repo_root,
            "merge-base",
            "--is-ancestor",
            ancestor,
            descendant,
        ),
        env=_hardened_git_environment(git),
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    if completed.returncode == 0:
        return True
    if completed.returncode == 1:
        return False
    raise VerificationError(
        f"Git ancestry command failed with return code {completed.returncode}"
    )


def _to_bytes(value: Any) -> bytes:
    if value is None:
        return b""
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return value.encode("utf-8", errors="surrogateescape")
    raise TypeError(f"command stream has unsupported type {type(value).__name__}")


def _command_record(command: tuple[str, ...], runner: Runner, cwd: Path) -> dict[str, Any]:
    error_type: str | None = None
    try:
        result = runner(command, cwd)
        if type(result.returncode) is not int:
            raise TypeError("runner-returncode-not-exact-integer")
        returncode = result.returncode
        stdout = _to_bytes(result.stdout)
        stderr = _to_bytes(result.stderr)
    except Exception as exc:  # fail closed while retaining no exception/log plaintext
        error_type = type(exc).__name__
        returncode = 125
        stdout = b""
        stderr = str(exc).encode("utf-8", errors="replace")
    record = {
        "argv": list(command),
        "return_code": returncode,
        "stdout_bytes": len(stdout),
        "stdout_sha256": _sha256_bytes(stdout),
        "stderr_bytes": len(stderr),
        "stderr_sha256": _sha256_bytes(stderr),
    }
    if error_type is not None:
        record["runner_error_type"] = error_type
    return record


def _problem(code: str, detail: str) -> dict[str, str]:
    return {"code": code, "detail": detail}


def _inventory_digest(inventory: Inventory) -> str:
    return _sha256_bytes(_canonical_json(inventory.as_dict()))


def _snapshot_digest(snapshot: Mapping[str, FileFingerprint]) -> str:
    return _sha256_bytes(_canonical_json(_content_projection(snapshot)))


def _changed_paths(
    initial: Mapping[str, FileFingerprint], current: Mapping[str, FileFingerprint]
) -> list[str]:
    return sorted(
        rel
        for rel in set(initial) | set(current)
        if initial.get(rel) != current.get(rel)
    )


def run_verification(
    repo_root: Path = REPO_ROOT,
    *,
    runner: Runner = default_runner,
    git_probe: GitProbe = default_git_probe,
    toolchain_resolver: ToolchainResolver = resolve_toolchain,
    wall_clock_ns: Clock = time.time_ns,
    monotonic_clock_ns: Clock = time.monotonic_ns,
) -> dict[str, Any]:
    """Run the generation-sixteen lifecycle-control pipeline and return its in-memory receipt."""

    root = repo_root.resolve(strict=True)
    wall_start = wall_clock_ns()
    monotonic_start = monotonic_clock_ns()
    problems: list[dict[str, str]] = []
    commands: list[dict[str, Any]] = []

    try:
        toolchain = toolchain_resolver()
        inventory = discover_inventory(root)
        initial = snapshot_files(root, inventory.tested_files)
        # Close discovery-to-snapshot races before any validation command executes.
        if discover_inventory(root) != inventory:
            raise VerificationError("focused inventory changed during initial snapshot")
        if snapshot_files(root, inventory.tested_files) != initial:
            raise VerificationError("tested sources changed during initial snapshot")
        git_start = git_probe(root, inventory.tested_files)
    except Exception as exc:
        problems.append(_problem("INITIALIZATION_FAILED", f"{type(exc).__name__}: {exc}"))
        inventory = Inventory((), (), (), (), ())
        initial = {}
        toolchain = {}
        git_start = GitState("", (), _sha256_bytes(b""))

    command_contract = (
        build_commands(inventory, toolchain) if inventory.tested_files and toolchain else ()
    )

    if git_start.dirty_entries or git_start.porcelain_sha256 != _sha256_bytes(b""):
        problems.append(
            _problem(
                "GIT_REPOSITORY_DIRTY_START",
                "repository was not globally clean before verification",
            )
        )
    if git_start.branch != "master":
        problems.append(_problem("GIT_BRANCH", f"expected master, observed {git_start.branch!r}"))
    if git_start.upstream != "origin/master":
        problems.append(
            _problem("GIT_UPSTREAM", f"expected origin/master, observed {git_start.upstream!r}")
        )
    if git_start.upstream_head != git_start.head:
        problems.append(
            _problem("SOURCE_NOT_PUSHED", "source HEAD does not equal the frozen upstream HEAD")
        )
    if git_start.parents != (RECOVERY_SOURCE_PARENT,):
        problems.append(
            _problem(
                "SOURCE_PARENT",
                "generation-sixteen source HEAD is not the direct child of the accepted B15 baton",
            )
        )
    if git_start.commit_paths != tuple(sorted(RECOVERY_SOURCE_COMMIT_PATHS)):
        problems.append(
            _problem(
                "SOURCE_COMMIT_SCOPE",
                "generation-sixteen source HEAD path set is not the exact preregistered lifecycle-control set",
            )
        )

    def checkpoint(label: str) -> bool:
        try:
            observed_inventory = discover_inventory(root)
            if observed_inventory != inventory:
                expected = set(inventory.tested_files)
                observed = set(observed_inventory.tested_files)
                problems.append(
                    _problem(
                        "INVENTORY_DRIFT",
                        f"{label}: added={sorted(observed - expected)} removed={sorted(expected - observed)}",
                    )
                )
                return False
            if toolchain_resolver() != toolchain:
                problems.append(_problem("TOOLCHAIN_DRIFT", f"{label}: executable receipt changed"))
                return False
            observed_git = git_probe(root, inventory.tested_files)
            if observed_git != git_start:
                problems.append(_problem("GIT_STATE_DRIFT", f"{label}: Git state changed"))
                return False
            observed = snapshot_files(root, inventory.tested_files)
            changed = _changed_paths(initial, observed)
            if changed:
                problems.append(_problem("TESTED_FILE_DRIFT", f"{label}: {changed}"))
                return False
            return True
        except Exception as exc:
            problems.append(
                _problem("CHECKPOINT_FAILED", f"{label}: {type(exc).__name__}: {exc}")
            )
            return False

    if not problems:
        for index, command in enumerate(command_contract):
            if not checkpoint(f"before_command_{index}"):
                break
            record = _command_record(command, runner, root)
            commands.append(record)
            if record["return_code"] != 0:
                problems.append(
                    _problem(
                        "COMMAND_FAILED",
                        f"command_{index} returned {record['return_code']}",
                    )
                )
            if not checkpoint(f"after_command_{index}"):
                break

    # The final probes run even after a command failure; a drifted surface can never be green.
    checkpoint("final") if inventory.tested_files else None
    try:
        final = snapshot_files(root, inventory.tested_files) if inventory.tested_files else {}
    except Exception as exc:
        problems.append(_problem("FINAL_SNAPSHOT_FAILED", f"{type(exc).__name__}: {exc}"))
        final = {}
    try:
        git_end = git_probe(root, inventory.tested_files) if inventory.tested_files else git_start
    except Exception as exc:
        problems.append(_problem("FINAL_GIT_PROBE_FAILED", f"{type(exc).__name__}: {exc}"))
        git_end = GitState("", (), _sha256_bytes(b""))

    if git_start.head != git_end.head:
        problems.append(_problem("GIT_HEAD_DRIFT", "Git HEAD changed during verification"))
    if git_start != git_end:
        problems.append(_problem("GIT_STATE_DRIFT", "Git publication state changed during verification"))
    if git_end.dirty_entries or git_end.porcelain_sha256 != _sha256_bytes(b""):
        problems.append(
            _problem(
                "GIT_REPOSITORY_DIRTY_END",
                "repository was not globally clean at verification end",
            )
        )
    if git_start.dirty_entries != git_end.dirty_entries:
        problems.append(
            _problem("GIT_DIRTY_STATE_DRIFT", "repository dirty state changed during verification")
        )
    if initial != final:
        changed = _changed_paths(initial, final)
        marker = _problem("FINAL_TESTED_FILE_DRIFT", f"changed={changed}")
        if marker not in problems:
            problems.append(marker)
    if len(commands) != len(command_contract):
        problems.append(
            _problem(
                "COMMAND_SET_INCOMPLETE",
                f"executed={len(commands)} expected={len(command_contract)}",
            )
        )

    monotonic_end = monotonic_clock_ns()
    wall_end = wall_clock_ns()
    if monotonic_end < monotonic_start:
        problems.append(_problem("MONOTONIC_CLOCK_REGRESSED", "monotonic duration is negative"))
    if wall_end < wall_start:
        problems.append(_problem("WALL_CLOCK_REGRESSED", "wall duration is negative"))

    receipt: dict[str, Any] = {
        "schema": SCHEMA,
        "publication": dict(EXPECTED_RECOVERY_PUBLICATION),
        "verdict": OK_VERDICT if not problems else FAIL_VERDICT,
        "problem_count": len(problems),
        "problems": problems,
        "repository": {
            "root": str(root),
            "git_start": git_start.as_dict(),
            "git_end": git_end.as_dict(),
            "git_head_stable": git_start.head == git_end.head,
            "git_state_stable": git_start == git_end,
            "repository_clean_state_stable": (
                not git_start.dirty_entries
                and git_start.porcelain_sha256 == _sha256_bytes(b"")
                and git_start == git_end
            ),
        },
        "inventory": inventory.as_dict(),
        "inventory_sha256": _inventory_digest(inventory),
        "toolchain": toolchain,
        "environment_contract": _sanitized_environment(toolchain) if toolchain else {},
        "files": _snapshot_public(initial),
        "file_content_set_sha256": _snapshot_digest(initial),
        "command_contract": [list(command) for command in command_contract],
        "commands": commands,
        "timing": {
            "started_at_utc": _utc_from_ns(wall_start),
            "finished_at_utc": _utc_from_ns(wall_end),
            "wall_duration_ns": max(0, wall_end - wall_start),
            "monotonic_duration_ns": max(0, monotonic_end - monotonic_start),
        },
    }
    if set(receipt) != RECEIPT_PAYLOAD_FIELDS:
        raise VerificationError("generated receipt payload field set drift")
    receipt["receipt_payload_sha256"] = _sha256_bytes(_canonical_json(receipt))
    if set(receipt) != RECEIPT_FIELDS:
        raise VerificationError("generated receipt field set drift")
    return receipt


def _valid_commit(value: object) -> bool:
    return isinstance(value, str) and len(value) == 40 and all(
        character in "0123456789abcdef" for character in value
    )


def _git_commit_row(repo_root: Path, commit: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if not _valid_commit(commit):
        raise VerificationError("publication commit is not lowercase 40-hex")
    parent_fields = _git_bytes(
        repo_root, ("rev-list", "--parents", "-n", "1", commit)
    ).decode("ascii", errors="strict").strip().split()
    if not parent_fields or parent_fields[0] != commit:
        raise VerificationError("publication parent row does not start with requested commit")
    parents = tuple(parent_fields[1:])
    paths = tuple(
        sorted(
            field.decode("utf-8", errors="surrogateescape")
            for field in _git_bytes(
                repo_root,
                (
                    "diff-tree",
                    "--root",
                    "--no-commit-id",
                    "--name-only",
                    "-r",
                    "-z",
                    commit,
                ),
            ).split(b"\0")
            if field
        )
    )
    return parents, paths


def _git_file_bytes(repo_root: Path, commit: str, relative_path: str) -> bytes:
    if not _valid_commit(commit):
        raise VerificationError("publication file commit is malformed")
    pure = PurePosixPath(relative_path)
    if pure.is_absolute() or ".." in pure.parts or pure.as_posix() != relative_path:
        raise VerificationError(f"publication file path is unsafe: {relative_path!r}")
    return _git_bytes(
        repo_root,
        ("show", "--no-ext-diff", "--no-textconv", f"{commit}:{relative_path}"),
    )


def _source_inventory_from_tree(repo_root: Path, source_commit: str) -> Inventory:
    tree_paths = {
        field.decode("utf-8", errors="surrogateescape")
        for field in _git_bytes(
            repo_root,
            ("ls-tree", "-r", "-z", "--name-only", source_commit),
        ).split(b"\0")
        if field
    }
    tests = tuple(
        sorted(
            path
            for path in tree_paths
            if PurePosixPath(path).parent.as_posix() == "tests"
            and (
                PurePosixPath(path).match("test_iter135_*.py")
                or path == "tests/test_handoff_generator.py"
                or path
                == "tests/test_iter131_post_iter130_mission_alignment_audit.py"
            )
        )
    )
    python_tools = tuple(
        sorted(
            path
            for path in tree_paths
            if PurePosixPath(path).parent.as_posix() == EXPERIMENT_REL
            and PurePosixPath(path).suffix == ".py"
        )
    )
    shell_files = tuple(
        sorted(
            path
            for path in tree_paths
            if PurePosixPath(path).parent.as_posix() == EXPERIMENT_REL
            and PurePosixPath(path).suffix == ".sh"
        )
    )
    missing = sorted(
        (
            set(REQUIRED_TEST_FILES)
            | set(REQUIRED_PYTHON_TOOL_FILES)
            | set(REQUIRED_SHELL_FILES)
            | set(REQUIRED_DATA_FILES)
            | set(REQUIRED_CONTROL_FILES)
        )
        - tree_paths
    )
    if missing:
        raise VerificationError(f"published source tree is missing frozen files: {missing}")
    if shell_files != tuple(sorted(REQUIRED_SHELL_FILES)):
        raise VerificationError("published source tree has an unreviewed shell-file set")
    forbidden = {
        path
        for path in tree_paths
        if path
        in {
            "pytest.ini",
            "tox.ini",
            "setup.cfg",
            "ruff.toml",
            ".ruff.toml",
            ".shellcheckrc",
            "conftest.py",
        }
        or (
            path.endswith("/conftest.py")
            and path.split("/", 1)[0] in {"tests", "engine", "method"}
        )
    }
    if forbidden:
        raise VerificationError(
            f"published source tree has unbound command configuration: {sorted(forbidden)}"
        )
    return Inventory(
        tests=tests,
        python_tools=python_tools,
        shell_files=shell_files,
        data_files=tuple(sorted(REQUIRED_DATA_FILES)),
        control_files=tuple(sorted(REQUIRED_CONTROL_FILES)),
    )


def _read_stable_regular_file(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path.absolute():
        raise VerificationError(f"publication receipt is not a physical regular file: {path}")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    final = path.stat(follow_symlinks=False)
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    identity_path = (
        final.st_dev,
        final.st_ino,
        final.st_mode,
        final.st_size,
        final.st_mtime_ns,
        final.st_ctime_ns,
    )
    payload = b"".join(chunks)
    if identity_before != identity_after or identity_after != identity_path:
        raise VerificationError("publication receipt changed while reading")
    if not stat.S_ISREG(after.st_mode) or len(payload) != after.st_size:
        raise VerificationError("publication receipt byte count or type is invalid")
    return payload


def _physical_stat_identity(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_uid,
        value.st_gid,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _open_physical_directory_chain(
    directory: Path,
) -> tuple[int, tuple[tuple[str, tuple[int, ...]], ...]]:
    """Open every absolute path component with no-follow directory descriptors."""

    absolute = Path(os.path.abspath(os.fspath(directory)))
    if not absolute.is_absolute():
        raise VerificationError("physical directory walk requires an absolute path")
    components = absolute.parts
    flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        descriptor = os.open(components[0], flags)
    except OSError as error:
        raise VerificationError("physical directory root cannot be opened") from error
    current = Path(components[0])
    rows: list[tuple[str, tuple[int, ...]]] = []
    try:
        root_state = os.fstat(descriptor)
        if not stat.S_ISDIR(root_state.st_mode):
            raise VerificationError("physical directory root is not a directory")
        rows.append((str(current), _physical_stat_identity(root_state)[:5]))
        for component in components[1:]:
            if component in {"", ".", ".."}:
                raise VerificationError("physical directory component is malformed")
            try:
                next_descriptor = os.open(component, flags, dir_fd=descriptor)
            except OSError as error:
                raise VerificationError(
                    f"physical directory component cannot be opened: {component}"
                ) from error
            try:
                observed = os.fstat(next_descriptor)
                if not stat.S_ISDIR(observed.st_mode):
                    raise VerificationError(
                        f"physical path component is not a directory: {component}"
                    )
            except Exception:
                os.close(next_descriptor)
                raise
            os.close(descriptor)
            descriptor = next_descriptor
            current /= component
            rows.append((str(current), _physical_stat_identity(observed)[:5]))
        return descriptor, tuple(rows)
    except Exception:
        os.close(descriptor)
        raise


def _physical_route_contains_directory_identity(
    route: Sequence[tuple[str, tuple[int, ...]]], identity: tuple[int, int]
) -> bool:
    """Compare physical directory ancestry by device/inode, never by path spelling."""

    return any(row_identity[:2] == identity for _path, row_identity in route)


def _read_physical_regular_file_snapshot(
    path: Path, maximum: int, *, required: bool
) -> tuple[bytes | None, tuple[Any, ...]]:
    """Read or witness absence through two no-follow descriptor-relative path walks."""

    if maximum < 0:
        raise VerificationError("bounded regular-file maximum is negative")
    absolute = Path(os.path.abspath(os.fspath(path)))
    if absolute.name in {"", ".", ".."}:
        raise VerificationError("bounded regular-file basename is malformed")
    parent_descriptor: int | None = None
    file_descriptor: int | None = None
    final_parent_descriptor: int | None = None
    final_file_descriptor: int | None = None
    file_flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        parent_descriptor, parent_before = _open_physical_directory_chain(absolute.parent)
        try:
            file_descriptor = os.open(
                absolute.name, file_flags, dir_fd=parent_descriptor
            )
        except FileNotFoundError:
            if required:
                raise VerificationError(
                    f"required bounded regular file is absent: {absolute}"
                ) from None
            final_parent_descriptor, parent_after = _open_physical_directory_chain(
                absolute.parent
            )
            if parent_before != parent_after:
                raise VerificationError("bounded absent-file parent path changed")
            try:
                appeared = os.open(
                    absolute.name, file_flags, dir_fd=final_parent_descriptor
                )
            except FileNotFoundError:
                return None, ("absent", parent_before)
            else:
                os.close(appeared)
                raise VerificationError("bounded absent file appeared during snapshot")
        except OSError as error:
            raise VerificationError(
                "bounded regular file has a symlink or physical-path redirection: "
                f"{absolute}"
            ) from error

        before = os.fstat(file_descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_size < 0
            or before.st_size > maximum
        ):
            raise VerificationError("bounded regular-file size or type is outside the contract")
        remaining = before.st_size
        chunks: list[bytes] = []
        while remaining:
            chunk = os.read(file_descriptor, min(1024 * 1024, remaining))
            if not chunk:
                raise VerificationError("bounded regular file ended before its declared size")
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(file_descriptor, 1):
            raise VerificationError("bounded regular file grew while reading")
        after = os.fstat(file_descriptor)
        final_parent_descriptor, parent_after = _open_physical_directory_chain(
            absolute.parent
        )
        try:
            final_file_descriptor = os.open(
                absolute.name, file_flags, dir_fd=final_parent_descriptor
            )
        except OSError as error:
            raise VerificationError("bounded regular file vanished or redirected") from error
        final = os.fstat(final_file_descriptor)
        identity = _physical_stat_identity(before)
        if (
            parent_before != parent_after
            or identity != _physical_stat_identity(after)
            or identity != _physical_stat_identity(final)
        ):
            raise VerificationError("bounded regular file or physical parent changed")
        payload = b"".join(chunks)
        return payload, ("file", identity, _sha256_bytes(payload), parent_before)
    finally:
        for descriptor in (
            final_file_descriptor,
            final_parent_descriptor,
            file_descriptor,
            parent_descriptor,
        ):
            if descriptor is not None:
                os.close(descriptor)


def _read_stable_regular_file_bounded(path: Path, maximum: int) -> bytes:
    """Read a bounded regular file through a stable no-follow physical path walk."""

    payload, _snapshot = _read_physical_regular_file_snapshot(
        path, maximum, required=True
    )
    assert payload is not None
    return payload


def _linear_publication_chain(
    repo_root: Path, ancestor: str, descendant: str
) -> list[tuple[str, tuple[str, ...]]]:
    reverse_chain: list[tuple[str, tuple[str, ...]]] = []
    cursor = descendant
    for _ in range(1_000):
        if cursor == ancestor:
            return list(reversed(reverse_chain))
        parents, paths = _git_commit_row(repo_root, cursor)
        if len(parents) != 1:
            raise VerificationError("publication chain is not linear")
        reverse_chain.append((cursor, paths))
        cursor = parents[0]
    raise VerificationError("publication chain exceeded the bounded history walk")


def _validate_post_baton_chain(
    chain: Sequence[tuple[str, tuple[str, ...]]],
) -> None:
    """Require the only publication order that can end in analytic authority.

    Partial prefixes through smoke are valid preflight states.  Exact A and A/F prefixes are also
    valid only while constructing the deterministic final manifest and activation baton; they are
    never launch authority.  This function proves path topology.  The mission-state controller
    requires complete A/F/B and separately proves artifact bytes, phases, hashes, and publication.
    """

    expected_prefixes = (
        (HOST_PACKET_MANIFEST_REL, HOST_PREPARATION_RECEIPT_REL),
        (ENVIRONMENT_RECEIPT_REL,),
        (LAUNCH_MANIFEST_REL,),
    )
    cursor = 0
    for expected in expected_prefixes:
        if cursor >= len(chain):
            return
        commit, paths = chain[cursor]
        if paths != expected:
            raise VerificationError(
                f"post-freeze commit {commit} violates evidence order: {list(paths)}!={list(expected)}"
            )
        cursor += 1

    if cursor >= len(chain):
        return
    smoke_commit, smoke_paths = chain[cursor]
    if smoke_paths != SMOKE_EVIDENCE_PATHS:
        raise VerificationError(
            f"post-freeze commit {smoke_commit} is not the exact smoke-evidence freeze"
        )
    cursor += 1
    if cursor >= len(chain):
        return

    launch_tail = chain[cursor:]
    expected_launch_paths = (
        ("MISSION_STATE.json",),
        (LAUNCH_MANIFEST_REL,),
        ("CONTINUITY.md", "HANDOFF.md", LAUNCH_ACTIVATION_RECEIPT_REL),
    )
    if len(launch_tail) > len(expected_launch_paths):
        raise VerificationError(
            "launch transition has commits beyond the exact state, final-manifest, and "
            "activation-baton sequence"
        )
    for (commit, paths), expected in zip(launch_tail, expected_launch_paths):
        if paths != expected:
            raise VerificationError(
                f"launch-transition commit {commit} has wrong scope: {list(paths)}!={list(expected)}"
            )


@dataclass(frozen=True)
class _BindingGitLayout:
    worktree: Path
    git_dir: Path
    common_dir: Path
    objects_dir: Path
    linked_worktree: bool
    directory_snapshots: tuple[tuple[str, tuple[Any, ...]], ...]
    control_snapshots: tuple[tuple[str, tuple[Any, ...]], ...]


@dataclass(frozen=True)
class _AnchoredBootstrap:
    tooling_receipt: Mapping[str, Any]
    tooling_receipt_bytes: bytes
    tooling_receipt_sha256: str
    source_commit: str
    git: Mapping[str, Any]
    python: Mapping[str, Any]
    binder: Mapping[str, Any]


def _binding_stat_identity(value: os.stat_result) -> tuple[int, ...]:
    return _physical_stat_identity(value)


def _binding_directory_snapshot(path: Path) -> tuple[Any, ...]:
    if path.is_symlink():
        raise VerificationError(f"bootstrap Git directory is a symlink: {path}")
    try:
        observed = path.stat(follow_symlinks=False)
    except OSError as error:
        raise VerificationError(f"bootstrap Git directory cannot be stated: {path}") from error
    if not stat.S_ISDIR(observed.st_mode):
        raise VerificationError(f"bootstrap Git directory is not physical: {path}")
    return (str(path), *_binding_stat_identity(observed))


def _binding_optional_directory_snapshot(path: Path) -> tuple[Any, ...]:
    if path.is_symlink():
        raise VerificationError(f"bootstrap optional Git directory is a symlink: {path}")
    try:
        observed = path.stat(follow_symlinks=False)
    except FileNotFoundError:
        return (str(path), "absent")
    except OSError as error:
        raise VerificationError(
            f"bootstrap optional Git directory cannot be stated: {path}"
        ) from error
    if not stat.S_ISDIR(observed.st_mode):
        raise VerificationError(f"bootstrap optional Git directory is not physical: {path}")
    return (str(path), "directory", *_binding_stat_identity(observed))


def _binding_control_snapshot(
    path: Path, maximum: int, *, required: bool
) -> tuple[tuple[Any, ...], bytes | None]:
    """Bounded no-follow snapshot for one Git control file, including absence."""

    payload, snapshot = _read_physical_regular_file_snapshot(
        path, maximum, required=required
    )
    return ((str(path), *snapshot), payload)


def _next_source_exact_tool_row(
    claimed: Mapping[str, Any],
    *,
    expected_path: Path | None,
    version_args: tuple[str, ...],
    cwd: Path,
) -> dict[str, Any]:
    if set(claimed) != TOOLCHAIN_ROW_FIELDS:
        raise VerificationError("bootstrap tool row field set mismatch")
    claimed_path = claimed.get("path")
    if not isinstance(claimed_path, str):
        raise VerificationError("bootstrap tool path is malformed")
    physical = Path(claimed_path).resolve(strict=True)
    if expected_path is not None and physical != expected_path.resolve(strict=True):
        raise VerificationError("bootstrap interpreter differs from anchored R16 tool")
    if not _allowed_tool_path(physical):
        raise VerificationError("bootstrap tool is outside accepted roots")
    observed = _stable_external_file(physical)
    environment = _sanitized_environment_for_paths([str(physical)])
    completed = subprocess.run(  # noqa: S603 - exact R16-bound executable path
        (str(physical), *version_args),
        cwd=cwd,
        env=environment,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=10,
    )
    if completed.returncode != 0 or len(completed.stdout) > 65_536:
        raise VerificationError("bootstrap tool version probe failed")
    lines = completed.stdout.decode("utf-8", errors="replace").splitlines()
    observed["version"] = lines[0] if lines else ""
    if not _exact_json_value(observed, claimed):
        raise VerificationError("bootstrap tool identity differs from anchored R16 receipt")
    return observed


def _require_isolated_binding_interpreter() -> None:
    flags = sys.flags
    if (
        flags.isolated != 1
        or flags.ignore_environment != 1
        or flags.no_user_site != 1
        or flags.no_site != 1
        or flags.dont_write_bytecode != 1
        or getattr(flags, "safe_path", 0) != 1
    ):
        raise VerificationError("next-source binding requires Python -I -B -S")


def _anchor_next_source_tools(
    repo_root: Path, accepted_tooling_receipt_sha256: str
) -> _AnchoredBootstrap:
    """Authenticate R16, the executing binder, Python, and Git before any Git read."""

    if not _is_sha256(accepted_tooling_receipt_sha256):
        raise VerificationError("accepted tooling-receipt SHA-256 is malformed")
    receipt_path = repo_root / RECEIPT_REL
    raw_receipt = _read_stable_regular_file_bounded(receipt_path, 8 * 1024 * 1024)
    observed_receipt_sha256 = _sha256_bytes(raw_receipt)
    if observed_receipt_sha256 != accepted_tooling_receipt_sha256:
        raise VerificationError("working R16 receipt differs from detached accepted SHA-256")
    _require_isolated_binding_interpreter()
    receipt = _parse_receipt_json(raw_receipt)
    if set(receipt) != RECEIPT_FIELDS or receipt.get("schema") != SCHEMA:
        raise VerificationError("anchored tooling receipt schema is malformed")
    if not _exact_json_value(receipt.get("publication"), EXPECTED_RECOVERY_PUBLICATION):
        raise VerificationError("anchored tooling receipt publication block is wrong")
    if (
        receipt.get("verdict") != OK_VERDICT
        or type(receipt.get("problem_count")) is not int
        or receipt.get("problem_count") != 0
        or receipt.get("problems") != []
    ):
        raise VerificationError("anchored tooling receipt is not exactly green")
    nested_errors = _nested_receipt_shape_errors(receipt)
    if nested_errors:
        raise VerificationError("anchored tooling receipt nested schema is malformed")
    payload = dict(receipt)
    claimed_payload_sha256 = payload.pop("receipt_payload_sha256", None)
    if claimed_payload_sha256 != _sha256_bytes(_canonical_json(payload)):
        raise VerificationError("anchored tooling receipt payload checksum is wrong")

    repository = receipt.get("repository")
    if not isinstance(repository, Mapping):
        raise VerificationError("anchored tooling repository block is malformed")
    git_start = repository.get("git_start")
    git_end = repository.get("git_end")
    if not isinstance(git_start, Mapping) or not _exact_json_value(git_start, git_end):
        raise VerificationError("anchored tooling Git state was not stable")
    source_commit = git_start.get("head")
    if not _valid_commit(source_commit):
        raise VerificationError("anchored F16 source commit is malformed")
    if (
        git_start.get("parents") != [GENERATION_SIXTEEN_SOURCE_PARENT]
        or git_start.get("commit_paths")
        != list(sorted(GENERATION_SIXTEEN_SOURCE_COMMIT_PATHS))
    ):
        raise VerificationError("anchored F16 source topology claim is malformed")

    claimed_files = receipt.get("files")
    if not isinstance(claimed_files, Mapping):
        raise VerificationError("anchored tooling file map is malformed")
    claimed_binder = claimed_files.get(BINDER_REL)
    if not isinstance(claimed_binder, Mapping) or set(claimed_binder) != FILE_ROW_FIELDS:
        raise VerificationError("anchored binder file row is missing or malformed")
    binder_bytes = _read_stable_regular_file_bounded(
        repo_root / BINDER_REL, NEXT_SOURCE_MAX_BLOB_BYTES
    )
    binder_projection = {
        "path": BINDER_REL,
        "bytes": len(binder_bytes),
        "sha256": _sha256_bytes(binder_bytes),
    }
    if {
        "bytes": claimed_binder.get("bytes"),
        "sha256": claimed_binder.get("sha256"),
    } != {
        "bytes": binder_projection["bytes"],
        "sha256": binder_projection["sha256"],
    }:
        raise VerificationError("executing binder bytes differ from anchored R16 receipt")

    toolchain = receipt.get("toolchain")
    if not isinstance(toolchain, Mapping):
        raise VerificationError("anchored tooling toolchain is malformed")
    python_row = toolchain.get("python3")
    git_row = toolchain.get("git")
    if not isinstance(python_row, Mapping) or not isinstance(git_row, Mapping):
        raise VerificationError("anchored Python or Git row is missing")
    python = _next_source_exact_tool_row(
        python_row,
        expected_path=Path(sys.executable),
        version_args=TOOL_VERSION_ARGS["python3"],
        cwd=repo_root,
    )
    git = _next_source_exact_tool_row(
        git_row,
        expected_path=None,
        version_args=TOOL_VERSION_ARGS["git"],
        cwd=repo_root,
    )
    return _AnchoredBootstrap(
        tooling_receipt=receipt,
        tooling_receipt_bytes=raw_receipt,
        tooling_receipt_sha256=observed_receipt_sha256,
        source_commit=source_commit,
        git=git,
        python=python,
        binder=binder_projection,
    )


def _read_small_physical_file(path: Path, maximum: int) -> bytes:
    return _read_stable_regular_file_bounded(path, maximum)


def _discover_binding_git_layout(repo_root: Path) -> _BindingGitLayout:
    worktree = repo_root.resolve(strict=True)
    dot_git = worktree / ".git"
    linked_worktree = False
    if dot_git.is_symlink():
        raise VerificationError("bootstrap .git path must not be a symlink")
    if dot_git.is_dir():
        git_dir = dot_git.resolve(strict=True)
    elif dot_git.is_file():
        if not stat.S_ISREG(dot_git.stat(follow_symlinks=False).st_mode):
            raise VerificationError("bootstrap .git file is not regular")
        linked_worktree = True
        gitfile = _read_small_physical_file(dot_git, 4_096)
        if not gitfile.startswith(b"gitdir: ") or not gitfile.endswith(b"\n"):
            raise VerificationError("bootstrap linked-worktree gitfile is malformed")
        target_raw = gitfile[8:-1]
        if not target_raw or b"\0" in target_raw or b"\n" in target_raw:
            raise VerificationError("bootstrap linked-worktree gitdir is malformed")
        target_text = target_raw.decode("utf-8", errors="strict")
        target = Path(target_text)
        if not target.is_absolute():
            target = worktree / target
        if target.is_symlink() or not target.is_dir():
            raise VerificationError("bootstrap linked-worktree gitdir is not physical")
        git_dir = target.resolve(strict=True)
        if not git_dir.is_dir():
            raise VerificationError("bootstrap linked-worktree gitdir is not physical")
    else:
        raise VerificationError("bootstrap worktree has no physical .git metadata")

    commondir_path = git_dir / "commondir"
    has_commondir = commondir_path.exists() or commondir_path.is_symlink()
    if has_commondir != linked_worktree:
        raise VerificationError("bootstrap commondir/link-worktree state is noncanonical")
    if has_commondir:
        if commondir_path.is_symlink():
            raise VerificationError("bootstrap commondir must not be a symlink")
        common_raw = _read_small_physical_file(commondir_path, 4_096)
        if not common_raw.endswith(b"\n") or b"\0" in common_raw:
            raise VerificationError("bootstrap commondir file is malformed")
        common_text = common_raw[:-1].decode("utf-8", errors="strict")
        common_target = git_dir / common_text
        if common_target.is_symlink() or not common_target.is_dir():
            raise VerificationError("bootstrap common Git directory is not physical")
        common_dir = common_target.resolve(strict=True)
    else:
        common_dir = git_dir
    if not common_dir.is_dir():
        raise VerificationError("bootstrap common Git directory is not physical")
    if linked_worktree:
        worktrees_root = common_dir / "worktrees"
        if worktrees_root.is_symlink() or not worktrees_root.is_dir():
            raise VerificationError("bootstrap linked-worktree registry is not physical")
        if git_dir.parent != worktrees_root.resolve(strict=True):
            raise VerificationError(
                "bootstrap linked-worktree gitdir is outside canonical .git/worktrees"
            )
    objects_path = common_dir / "objects"
    if objects_path.is_symlink() or not objects_path.is_dir():
        raise VerificationError("bootstrap object directory is not physical")
    objects_dir = objects_path.resolve(strict=True)
    if not objects_dir.is_dir():
        raise VerificationError("bootstrap object directory is not physical")

    forbidden_files = (
        git_dir / "shallow",
        common_dir / "shallow",
        git_dir / "info/grafts",
        common_dir / "info/grafts",
        objects_dir / "info/alternates",
    )
    if any(path.exists() or path.is_symlink() for path in forbidden_files):
        raise VerificationError("bootstrap repository uses shallow, graft, or alternate state")
    replace_refs = common_dir / "refs/replace"
    pack_dir = objects_dir / "pack"
    info_dir = objects_dir / "info"
    if pack_dir.is_symlink() or info_dir.is_symlink():
        raise VerificationError("bootstrap object metadata directory is a symlink")
    if replace_refs.exists() or replace_refs.is_symlink() or any(
        (objects_dir / "pack").glob("*.promisor")
    ):
        raise VerificationError("bootstrap repository uses replacement or promisor state")

    gitfile_snapshot: tuple[Any, ...]
    if linked_worktree:
        gitfile_snapshot, _gitfile_bytes = _binding_control_snapshot(
            dot_git, 4_096, required=True
        )
        if _gitfile_bytes != gitfile:
            raise VerificationError("bootstrap linked-worktree gitfile changed during discovery")
    else:
        gitfile_snapshot = ("directory", *_binding_directory_snapshot(dot_git))
    commondir_snapshot, _commondir_bytes = _binding_control_snapshot(
        commondir_path, 4_096, required=linked_worktree
    )
    if linked_worktree and _commondir_bytes != common_raw:
        raise VerificationError("bootstrap commondir changed during discovery")
    backlink_snapshot, backlink_bytes = _binding_control_snapshot(
        git_dir / "gitdir", 4_096, required=linked_worktree
    )
    if linked_worktree and backlink_bytes != str(dot_git).encode("utf-8") + b"\n":
        raise VerificationError("bootstrap linked-worktree backlink is redirected")
    head_snapshot, _head_bytes = _binding_control_snapshot(
        git_dir / "HEAD", 256, required=True
    )
    index_snapshot, _index_bytes = _binding_control_snapshot(
        git_dir / "index", 64 * 1024 * 1024, required=True
    )
    config_snapshot, config_bytes = _binding_control_snapshot(
        common_dir / "config", 8 * 1024 * 1024, required=True
    )
    worktree_config_snapshot, worktree_config_bytes = _binding_control_snapshot(
        git_dir / "config.worktree", 8 * 1024 * 1024, required=False
    )
    packed_refs_snapshot, packed_refs_bytes = _binding_control_snapshot(
        common_dir / "packed-refs", 64 * 1024 * 1024, required=False
    )
    if packed_refs_bytes is not None and b"refs/replace/" in packed_refs_bytes:
        raise VerificationError("bootstrap repository has packed replacement refs")
    for payload in (config_bytes, worktree_config_bytes):
        if payload is None:
            continue
        lowered = payload.lower()
        if b"[include" in lowered or b"include.path" in lowered:
            raise VerificationError("bootstrap Git config includes external configuration")
        if b"promisor" in lowered or b"partialclone" in lowered:
            raise VerificationError("bootstrap Git config enables partial or promisor state")

    directory_rows = [
        ("worktree", _binding_directory_snapshot(worktree)),
        ("git_dir", _binding_directory_snapshot(git_dir)),
        ("common_dir", _binding_directory_snapshot(common_dir)),
        ("objects_dir", _binding_directory_snapshot(objects_dir)),
        ("git_info", _binding_optional_directory_snapshot(git_dir / "info")),
        ("common_info", _binding_optional_directory_snapshot(common_dir / "info")),
        ("common_refs", _binding_optional_directory_snapshot(common_dir / "refs")),
        ("objects_info", _binding_optional_directory_snapshot(objects_dir / "info")),
        ("objects_pack", _binding_optional_directory_snapshot(objects_dir / "pack")),
    ]
    if linked_worktree:
        directory_rows.append(
            ("worktrees_dir", _binding_directory_snapshot(common_dir / "worktrees"))
        )
    control_rows = (
        ("gitfile", gitfile_snapshot),
        ("commondir", commondir_snapshot),
        ("gitdir", backlink_snapshot),
        ("HEAD", head_snapshot),
        ("index", index_snapshot),
        ("config", config_snapshot),
        ("config.worktree", worktree_config_snapshot),
        ("packed-refs", packed_refs_snapshot),
    )
    return _BindingGitLayout(
        worktree=worktree,
        git_dir=git_dir,
        common_dir=common_dir,
        objects_dir=objects_dir,
        linked_worktree=linked_worktree,
        directory_snapshots=tuple(directory_rows),
        control_snapshots=control_rows,
    )


def _binding_git_argv(
    git: Mapping[str, Any],
    layout: _BindingGitLayout,
    *argv: str,
    worktree: bool = False,
) -> tuple[str, ...]:
    command = [
        str(git["path"]),
        "--no-replace-objects",
        f"--git-dir={layout.git_dir}",
    ]
    if worktree:
        command.append(f"--work-tree={layout.worktree}")
    command.extend(
        (
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.untrackedCache=false",
            "-c",
            "core.hooksPath=/dev/null",
            *argv,
        )
    )
    return tuple(command)


def _binding_git_bytes(
    git: Mapping[str, Any],
    layout: _BindingGitLayout,
    *argv: str,
    worktree: bool = False,
    maximum: int = 8 * 1024 * 1024,
) -> bytes:
    completed = subprocess.run(  # noqa: S603 - exact anchored Git executable and fixed argv
        _binding_git_argv(git, layout, *argv, worktree=worktree),
        cwd=layout.worktree,
        env=_hardened_git_environment(git),
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
    )
    if completed.returncode != 0:
        raise VerificationError(
            f"bootstrap Git command failed with return code {completed.returncode}"
        )
    if completed.stderr or len(completed.stdout) > maximum:
        raise VerificationError("bootstrap Git command emitted stderr or oversized output")
    return completed.stdout


def _validate_binding_index_rows(raw: bytes) -> None:
    """Reject hidden index state; every tracked entry must have the normal ``H`` tag."""

    if not raw or not raw.endswith(b"\0"):
        raise VerificationError("bootstrap Git index inventory is empty or malformed")
    for row in raw[:-1].split(b"\0"):
        if len(row) < 3 or row[:2] != b"H ":
            raise VerificationError(
                "bootstrap Git index contains assume-unchanged or skip-worktree state"
            )


class _GitBatchObjectReader:
    """Stream raw local Git objects through one anchored, no-replacement process."""

    def __init__(
        self, git: Mapping[str, Any], layout: _BindingGitLayout
    ) -> None:
        self._deadline = time.monotonic() + NEXT_SOURCE_OBJECT_DEADLINE_SECONDS
        self._stderr = tempfile.TemporaryFile()
        self._buffer = bytearray()
        self._object_cache: dict[str, tuple[str, int, str, bytes | None]] = {}
        self._process = subprocess.Popen(  # noqa: S603 - exact anchored Git executable
            _binding_git_argv(git, layout, "cat-file", "--batch"),
            cwd=layout.worktree,
            env=_hardened_git_environment(git),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self._stderr,
            bufsize=0,
        )
        if self._process.stdin is None or self._process.stdout is None:
            raise VerificationError("bootstrap Git object reader has no pipes")

    def _remaining_seconds(self) -> float:
        remaining = self._deadline - time.monotonic()
        if remaining <= 0:
            self.abort()
            raise VerificationError("bootstrap Git object-reader deadline expired")
        return remaining

    def _fill(self) -> None:
        stdout = self._process.stdout
        assert stdout is not None
        ready, _writable, _exceptional = select.select(
            [stdout.fileno()], [], [], self._remaining_seconds()
        )
        if not ready:
            self.abort()
            raise VerificationError("bootstrap Git object-reader deadline expired")
        chunk = os.read(stdout.fileno(), 1024 * 1024)
        if not chunk:
            raise VerificationError("bootstrap Git object reader ended unexpectedly")
        self._buffer.extend(chunk)

    def _readline(self, maximum: int) -> bytes:
        while b"\n" not in self._buffer:
            if len(self._buffer) > maximum:
                raise VerificationError("bootstrap Git object header is oversized")
            self._fill()
        index = self._buffer.index(0x0A) + 1
        if index > maximum:
            raise VerificationError("bootstrap Git object header is oversized")
        result = bytes(self._buffer[:index])
        del self._buffer[:index]
        return result

    def _read_exact(self, size: int) -> bytes:
        while len(self._buffer) < size:
            self._fill()
        result = bytes(self._buffer[:size])
        del self._buffer[:size]
        return result

    def _stderr_bytes(self) -> bytes:
        self._stderr.flush()
        self._stderr.seek(0)
        payload = self._stderr.read(NEXT_SOURCE_MAX_GIT_STDERR_BYTES + 1)
        if len(payload) > NEXT_SOURCE_MAX_GIT_STDERR_BYTES:
            raise VerificationError("bootstrap Git object-reader stderr is oversized")
        return payload

    def close(self) -> None:
        if self._process.stdin is not None and not self._process.stdin.closed:
            self._process.stdin.close()
        try:
            return_code = self._process.wait(timeout=min(10, self._remaining_seconds()))
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait(timeout=10)
            raise VerificationError("bootstrap Git object reader did not terminate") from None
        if return_code != 0 or self._buffer or self._stderr_bytes():
            raise VerificationError("bootstrap Git object reader failed")
        self._stderr.close()

    def abort(self) -> None:
        if self._process.poll() is None:
            self._process.kill()
        self._process.wait(timeout=10)
        if not self._stderr.closed:
            self._stderr.close()

    def read(
        self, oid: str, *, expected_type: str, maximum: int, retain: bool
    ) -> tuple[int, str, bytes | None]:
        if not _valid_commit(oid):
            raise VerificationError("bootstrap object ID is not lowercase 40-hex")
        cached = self._object_cache.get(oid)
        if cached is not None:
            object_type, size, sha256, payload = cached
            if object_type != expected_type:
                raise VerificationError("bootstrap cached Git object type mismatch")
            if size > maximum:
                raise VerificationError("bootstrap cached Git object exceeds byte bound")
            if retain and payload is None:
                raise VerificationError(
                    "bootstrap cached Git object was not retained on its first read"
                )
            return size, sha256, payload if retain else None
        stdin = self._process.stdin
        stdout = self._process.stdout
        assert stdin is not None and stdout is not None
        stdin.write(oid.encode("ascii") + b"\n")
        stdin.flush()
        header = self._readline(NEXT_SOURCE_MAX_GIT_HEADER_BYTES)
        if not header.endswith(b"\n") or len(header) > NEXT_SOURCE_MAX_GIT_HEADER_BYTES:
            raise VerificationError("bootstrap Git object header is malformed")
        fields = header[:-1].split(b" ")
        if len(fields) != 3:
            raise VerificationError("bootstrap Git object is missing or malformed")
        observed_oid, observed_type, size_raw = fields
        if observed_oid != oid.encode("ascii") or observed_type != expected_type.encode("ascii"):
            raise VerificationError("bootstrap Git object identity or type mismatch")
        if not size_raw.isdigit() or (len(size_raw) > 1 and size_raw.startswith(b"0")):
            raise VerificationError("bootstrap Git object size is malformed")
        size = int(size_raw)
        if size > maximum:
            raise VerificationError("bootstrap Git object exceeds byte bound")
        sha1 = hashlib.sha1(usedforsecurity=False)
        sha1.update(f"{expected_type} {size}".encode("ascii") + b"\0")
        sha256 = hashlib.sha256()
        remaining = size
        chunks: list[bytes] = []
        while remaining:
            chunk = self._read_exact(min(1024 * 1024, remaining))
            if not chunk:
                raise VerificationError("bootstrap Git object stream is truncated")
            remaining -= len(chunk)
            sha1.update(chunk)
            sha256.update(chunk)
            if retain:
                chunks.append(chunk)
        if self._read_exact(1) != b"\n":
            raise VerificationError("bootstrap Git object framing is malformed")
        if sha1.hexdigest() != oid:
            raise VerificationError("bootstrap Git object SHA-1 mismatch")
        digest = sha256.hexdigest()
        payload = b"".join(chunks) if retain else None
        self._object_cache[oid] = (expected_type, size, digest, payload)
        return size, digest, payload


def _parse_raw_commit_links(payload: bytes) -> tuple[str, tuple[str, ...]]:
    headers, separator, _message = payload.partition(b"\n\n")
    if not separator or b"\0" in headers:
        raise VerificationError("bootstrap commit object is malformed")
    lines = headers.split(b"\n")
    if not lines or not lines[0].startswith(b"tree "):
        raise VerificationError("bootstrap commit tree header is missing or misplaced")
    continuation_allowed = False
    for line in lines:
        if line.startswith(b" "):
            if not continuation_allowed:
                raise VerificationError("bootstrap commit continuation is malformed")
            continue
        key, separator_raw, value = line.partition(b" ")
        if (
            not separator_raw
            or not key
            or not value
            or any(
                byte
                not in b"-0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz"
                for byte in key
            )
        ):
            raise VerificationError("bootstrap commit header is malformed")
        continuation_allowed = key in {b"gpgsig", b"gpgsig-sha256", b"mergetag"}
    trees = [line[5:] for line in lines if line.startswith(b"tree ")]
    parents = [line[7:] for line in lines if line.startswith(b"parent ")]
    if len(trees) != 1:
        raise VerificationError("bootstrap commit must contain exactly one tree")
    try:
        tree = trees[0].decode("ascii", errors="strict")
        parent_oids = tuple(
            parent.decode("ascii", errors="strict") for parent in parents
        )
    except UnicodeDecodeError as error:
        raise VerificationError("bootstrap commit binding is not ASCII") from error
    if not _valid_commit(tree) or any(not _valid_commit(parent) for parent in parent_oids):
        raise VerificationError("bootstrap commit tree or parent is malformed")
    return tree, parent_oids


def _parse_next_source_commit(payload: bytes, accepted_baton_commit: str) -> str:
    tree, parents = _parse_raw_commit_links(payload)
    if parents != (accepted_baton_commit,):
        raise VerificationError("candidate tree is malformed or parent is not accepted B16")
    return tree


def _parse_raw_git_tree(payload: bytes) -> list[tuple[str, bytes, str]]:
    entries: list[tuple[str, bytes, str]] = []
    component_names: set[bytes] = set()
    cursor = 0
    previous_key: bytes | None = None
    while cursor < len(payload):
        space = payload.find(b" ", cursor)
        nul = payload.find(b"\0", space + 1 if space >= 0 else cursor)
        if space <= cursor or nul <= space + 1 or nul + 21 > len(payload):
            raise VerificationError("candidate tree entry is malformed")
        mode_raw = payload[cursor:space]
        name = payload[space + 1 : nul]
        oid_raw = payload[nul + 1 : nul + 21]
        cursor = nul + 21
        try:
            mode = mode_raw.decode("ascii", errors="strict")
        except UnicodeDecodeError as error:
            raise VerificationError("candidate tree mode is malformed") from error
        if mode not in {"40000", "100644", "100755", "120000", "160000"}:
            raise VerificationError("bootstrap tree contains a noncanonical mode")
        if (
            not name
            or name in {b".", b".."}
            or b"/" in name
        ):
            raise VerificationError("bootstrap tree path component is malformed")
        if name in component_names:
            raise VerificationError("bootstrap tree contains a duplicate component name")
        component_names.add(name)
        ordering_key = name + (b"/" if mode == "40000" else b"\0")
        if previous_key is not None and ordering_key <= previous_key:
            raise VerificationError("bootstrap tree entries are not canonical and unique")
        previous_key = ordering_key
        entries.append((mode, name, oid_raw.hex()))
    return entries


def _parse_next_source_tree(payload: bytes) -> list[tuple[str, bytes, str]]:
    if not payload:
        raise VerificationError("candidate tree must not be empty")
    entries = _parse_raw_git_tree(payload)
    for mode, name, _oid in entries:
        if mode not in {"40000", *NEXT_SOURCE_ALLOWED_BLOB_MODES}:
            raise VerificationError("candidate tree contains a forbidden mode")
        if (
            len(name) > NEXT_SOURCE_MAX_COMPONENT_BYTES
            or name.lower() == b".git"
            or any(
                byte not in b"-.0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz"
                for byte in name
            )
        ):
            raise VerificationError("candidate tree path component is outside the contract")
    return entries


class _RawTopologyView:
    """SHA-verifying raw commit/tree view used for the accepted bootstrap chain."""

    def __init__(self, reader: _GitBatchObjectReader) -> None:
        self._reader = reader
        self._commits: dict[str, tuple[str, tuple[str, ...]]] = {}
        self._trees: dict[str, dict[bytes, tuple[str, str]]] = {}
        self._tree_object_bytes = 0

    def commit(self, oid: str) -> tuple[str, tuple[str, ...]]:
        if oid not in self._commits:
            _size, _sha256, payload = self._reader.read(
                oid,
                expected_type="commit",
                maximum=NEXT_SOURCE_MAX_COMMIT_BYTES,
                retain=True,
            )
            assert payload is not None
            self._commits[oid] = _parse_raw_commit_links(payload)
        return self._commits[oid]

    def tree(self, oid: str) -> dict[bytes, tuple[str, str]]:
        if oid in self._trees:
            return self._trees[oid]
        if len(self._trees) >= NEXT_SOURCE_MAX_TREE_OBJECTS:
            raise VerificationError("bootstrap trust tree exceeds object-count bound")
        remaining = NEXT_SOURCE_MAX_TREE_BYTES - self._tree_object_bytes
        if remaining < 0:
            raise VerificationError("bootstrap trust tree exceeds aggregate byte bound")
        size, _sha256, payload = self._reader.read(
            oid, expected_type="tree", maximum=remaining, retain=True
        )
        assert payload is not None
        self._tree_object_bytes += size
        entries = _parse_raw_git_tree(payload)
        rows = {name: (mode, child_oid) for mode, name, child_oid in entries}
        self._trees[oid] = rows
        return rows

    def _enumerate_leaves(
        self,
        identity: tuple[str, str],
        path: bytes,
        *,
        active: frozenset[str],
        depth: int,
    ) -> list[bytes]:
        mode, oid = identity
        if len(path) > NEXT_SOURCE_MAX_PATH_BYTES:
            raise VerificationError("bootstrap trust path exceeds byte bound")
        if mode != "40000":
            return [path]
        if depth > NEXT_SOURCE_MAX_TREE_DEPTH:
            raise VerificationError("bootstrap trust tree exceeds depth bound")
        if oid in active:
            raise VerificationError("bootstrap trust tree contains a recursive reference")
        rows = self.tree(oid)
        if not rows:
            raise VerificationError("bootstrap trust tree contains an empty subtree")
        result: list[bytes] = []
        for name in sorted(rows):
            result.extend(
                self._enumerate_leaves(
                    rows[name],
                    path + b"/" + name,
                    active=active | {oid},
                    depth=depth + 1,
                )
            )
            if len(result) > NEXT_SOURCE_MAX_FILES:
                raise VerificationError("bootstrap trust tree exceeds file-count bound")
        return result

    def _diff_trees(
        self,
        current_oid: str,
        parent_oid: str,
        prefix: bytes,
        *,
        active: frozenset[tuple[str, str]],
        depth: int,
    ) -> list[bytes]:
        if current_oid == parent_oid:
            return []
        if depth > NEXT_SOURCE_MAX_TREE_DEPTH:
            raise VerificationError("bootstrap trust tree diff exceeds depth bound")
        pair = (current_oid, parent_oid)
        if pair in active:
            raise VerificationError("bootstrap trust tree diff is recursive")
        current = self.tree(current_oid)
        parent = self.tree(parent_oid)
        result: list[bytes] = []
        for name in sorted(current.keys() | parent.keys()):
            current_identity = current.get(name)
            parent_identity = parent.get(name)
            path = prefix + name
            if len(path) > NEXT_SOURCE_MAX_PATH_BYTES:
                raise VerificationError("bootstrap trust path exceeds byte bound")
            if current_identity is None:
                assert parent_identity is not None
                result.extend(
                    self._enumerate_leaves(
                        parent_identity,
                        path,
                        active=frozenset(),
                        depth=depth,
                    )
                )
            elif parent_identity is None:
                result.extend(
                    self._enumerate_leaves(
                        current_identity,
                        path,
                        active=frozenset(),
                        depth=depth,
                    )
                )
            elif current_identity == parent_identity:
                continue
            elif current_identity[0] == "40000" and parent_identity[0] == "40000":
                result.extend(
                    self._diff_trees(
                        current_identity[1],
                        parent_identity[1],
                        path + b"/",
                        active=active | {pair},
                        depth=depth + 1,
                    )
                )
            elif "40000" in {current_identity[0], parent_identity[0]}:
                raise VerificationError("bootstrap trust tree has a blob/tree transition")
            else:
                result.append(path)
            if len(result) > NEXT_SOURCE_MAX_FILES:
                raise VerificationError("bootstrap trust tree diff exceeds file-count bound")
        return result

    def lookup(self, tree_oid: str, path: bytes) -> tuple[str, str] | None:
        components = path.split(b"/")
        if not components or any(not component for component in components):
            raise VerificationError("bootstrap raw tree lookup path is malformed")
        cursor = tree_oid
        for index, component in enumerate(components):
            identity = self.tree(cursor).get(component)
            if identity is None:
                return None
            if index == len(components) - 1:
                return identity
            if identity[0] != "40000":
                raise VerificationError("bootstrap raw tree lookup crosses a non-tree")
            cursor = identity[1]
        raise AssertionError("nonempty raw tree lookup did not return")

    def changed_paths(self, commit_oid: str, parent_oid: str) -> tuple[bytes, ...]:
        commit_tree, _parents = self.commit(commit_oid)
        parent_tree, _parent_parents = self.commit(parent_oid)
        return tuple(
            sorted(
                self._diff_trees(
                    commit_tree,
                    parent_tree,
                    b"",
                    active=frozenset(),
                    depth=0,
                )
            )
        )


def _candidate_manifest_from_objects(
    reader: _GitBatchObjectReader,
    *,
    accepted_baton_commit: str,
    candidate_commit: str,
) -> dict[str, Any]:
    commit_bytes, commit_sha256, commit_payload = reader.read(
        candidate_commit,
        expected_type="commit",
        maximum=NEXT_SOURCE_MAX_COMMIT_BYTES,
        retain=True,
    )
    assert commit_payload is not None
    root_tree = _parse_next_source_commit(commit_payload, accepted_baton_commit)
    files: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    blob_cache: dict[str, tuple[int, str]] = {}
    tree_cache: dict[str, tuple[int, list[tuple[str, bytes, str]]]] = {}
    active_trees: set[str] = set()
    tree_reference_count = 0
    tree_object_bytes = 0
    total_file_bytes = 0
    unique_blob_bytes = 0

    def visit_tree(tree_oid: str, prefix: bytes, depth: int) -> None:
        nonlocal tree_reference_count, tree_object_bytes
        nonlocal total_file_bytes, unique_blob_bytes
        if depth > NEXT_SOURCE_MAX_TREE_DEPTH:
            raise VerificationError("candidate tree exceeds depth bound")
        tree_reference_count += 1
        if tree_reference_count > NEXT_SOURCE_MAX_TREE_OBJECTS:
            raise VerificationError("candidate tree exceeds object-reference bound")
        if tree_oid in active_trees:
            raise VerificationError("candidate tree contains a recursive reference")
        if tree_oid not in tree_cache:
            remaining_tree_budget = NEXT_SOURCE_MAX_TREE_BYTES - tree_object_bytes
            if remaining_tree_budget < 0:
                raise VerificationError("candidate tree exceeds aggregate byte bound")
            size, _sha256, raw = reader.read(
                tree_oid,
                expected_type="tree",
                maximum=remaining_tree_budget,
                retain=True,
            )
            assert raw is not None
            tree_object_bytes += size
            tree_cache[tree_oid] = (size, _parse_next_source_tree(raw))
        active_trees.add(tree_oid)
        try:
            for mode, name, oid in tree_cache[tree_oid][1]:
                path_raw = prefix + name
                if len(path_raw) > NEXT_SOURCE_MAX_PATH_BYTES:
                    raise VerificationError("candidate path exceeds byte bound")
                if mode == "40000":
                    visit_tree(oid, path_raw + b"/", depth + 1)
                    continue
                path = path_raw.decode("ascii", errors="strict")
                if path in seen_paths:
                    raise VerificationError("candidate manifest contains a duplicate path")
                if len(files) >= NEXT_SOURCE_MAX_FILES:
                    raise VerificationError("candidate manifest exceeds file-count bound")
                if oid not in blob_cache:
                    size, sha256, _raw = reader.read(
                        oid,
                        expected_type="blob",
                        maximum=NEXT_SOURCE_MAX_BLOB_BYTES,
                        retain=False,
                    )
                    unique_blob_bytes += size
                    if unique_blob_bytes > NEXT_SOURCE_MAX_TOTAL_FILE_BYTES:
                        raise VerificationError("candidate unique blobs exceed byte bound")
                    blob_cache[oid] = (size, sha256)
                size, sha256 = blob_cache[oid]
                total_file_bytes += size
                if total_file_bytes > NEXT_SOURCE_MAX_TOTAL_FILE_BYTES:
                    raise VerificationError("candidate files exceed aggregate byte bound")
                seen_paths.add(path)
                files.append(
                    {
                        "path": path,
                        "mode": mode,
                        "bytes": size,
                        "git_blob_oid": oid,
                        "sha256": sha256,
                    }
                )
        finally:
            active_trees.remove(tree_oid)

    visit_tree(root_tree, b"", 0)
    files.sort(key=lambda row: str(row["path"]).encode("ascii"))
    return {
        "commit": candidate_commit,
        "commit_bytes": commit_bytes,
        "commit_sha256": commit_sha256,
        "parent": accepted_baton_commit,
        "tree": root_tree,
        "tree_object_count": len(tree_cache),
        "tree_object_bytes": tree_object_bytes,
        "file_count": len(files),
        "total_file_bytes": total_file_bytes,
        "unique_blob_count": len(blob_cache),
        "unique_blob_bytes": unique_blob_bytes,
        "manifest_sha256": _sha256_bytes(_canonical_json(files)),
        "files": files,
    }


def _validate_next_source_trust_topology(
    anchored: _AnchoredBootstrap,
    layout: _BindingGitLayout,
    accepted_baton_commit: str,
    reader: _GitBatchObjectReader,
) -> dict[str, Any]:
    """Validate object topology only; never execute receipt commands or candidate code."""

    if not _valid_commit(accepted_baton_commit):
        raise VerificationError("accepted B16 commit is not lowercase 40-hex")
    head_raw = _read_small_physical_file(layout.git_dir / "HEAD", 256)
    if head_raw != accepted_baton_commit.encode("ascii") + b"\n":
        raise VerificationError("bootstrap worktree is not detached at accepted B16")
    status = _binding_git_bytes(
        anchored.git,
        layout,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignored=matching",
        worktree=True,
    )
    if status:
        raise VerificationError("bootstrap B16 worktree contains tracked or residual files")
    _validate_binding_index_rows(
        _binding_git_bytes(
            anchored.git,
            layout,
            "ls-files",
            "-v",
            "-z",
            worktree=True,
            maximum=64 * 1024 * 1024,
        )
    )
    if _binding_git_bytes(
        anchored.git, layout, "rev-parse", "--show-object-format"
    ) != b"sha1\n":
        raise VerificationError("bootstrap repository object format is not SHA-1")

    topology = _RawTopologyView(reader)
    baton_tree, baton_parents = topology.commit(accepted_baton_commit)
    if len(baton_parents) != 1:
        raise VerificationError("accepted B16 object topology is malformed")
    state_commit = baton_parents[0]
    _state_tree, state_parents = topology.commit(state_commit)
    if len(state_parents) != 1:
        raise VerificationError("T16 object topology is malformed")
    receipt_commit = state_parents[0]
    receipt_tree, receipt_parents = topology.commit(receipt_commit)
    if len(receipt_parents) != 1:
        raise VerificationError("R16 object topology is malformed")
    source_commit = receipt_parents[0]
    source_tree, source_parents = topology.commit(source_commit)
    if (
        source_commit != anchored.source_commit
        or source_parents != (GENERATION_SIXTEEN_SOURCE_PARENT,)
    ):
        raise VerificationError("F16 object topology differs from anchored R16 receipt")
    expected_changes = (
        (
            accepted_baton_commit,
            state_commit,
            tuple(sorted(path.encode("ascii") for path in ("CONTINUITY.md", "HANDOFF.md"))),
        ),
        (state_commit, receipt_commit, (b"MISSION_STATE.json",)),
        (receipt_commit, source_commit, (RECEIPT_REL.encode("ascii"),)),
        (
            source_commit,
            GENERATION_SIXTEEN_SOURCE_PARENT,
            tuple(
                sorted(
                    path.encode("ascii")
                    for path in GENERATION_SIXTEEN_SOURCE_COMMIT_PATHS
                )
            ),
        ),
    )
    for commit_oid, parent_oid, expected_paths in expected_changes:
        if topology.changed_paths(commit_oid, parent_oid) != expected_paths:
            raise VerificationError(
                f"bootstrap raw tree diff is malformed at {commit_oid}"
            )

    receipt_identity = topology.lookup(receipt_tree, RECEIPT_REL.encode("ascii"))
    if receipt_identity is None or receipt_identity[0] != "100644":
        raise VerificationError("R16 receipt raw tree row is missing or malformed")
    receipt_size, receipt_sha256, committed_receipt = reader.read(
        receipt_identity[1],
        expected_type="blob",
        maximum=8 * 1024 * 1024,
        retain=True,
    )
    if (
        committed_receipt != anchored.tooling_receipt_bytes
        or receipt_size != len(anchored.tooling_receipt_bytes)
        or receipt_sha256 != anchored.tooling_receipt_sha256
    ):
        raise VerificationError("B16 working receipt differs from exact R16 commit bytes")
    binder_identity = topology.lookup(source_tree, BINDER_REL.encode("ascii"))
    if binder_identity is None or binder_identity[0] != "100644":
        raise VerificationError("F16 binder raw tree row is missing or malformed")
    binder_oid = binder_identity[1]
    binder_size, binder_sha256, binder_object = reader.read(
        binder_oid,
        expected_type="blob",
        maximum=max(int(anchored.binder["bytes"]), 1),
        retain=True,
    )
    if (
        binder_object is None
        or binder_size != anchored.binder["bytes"]
        or binder_sha256 != anchored.binder["sha256"]
    ):
        raise VerificationError("F16 binder Git blob differs from anchored working bytes")
    return {
        "baton_commit": accepted_baton_commit,
        "baton_tree": baton_tree,
        "source_commit": source_commit,
        "receipt_commit": receipt_commit,
        "tooling_receipt": {
            "path": RECEIPT_REL,
            "bytes": len(anchored.tooling_receipt_bytes),
            "sha256": anchored.tooling_receipt_sha256,
        },
        "binder": {
            **anchored.binder,
            "mode": "100644",
            "git_blob_oid": binder_oid,
        },
        "python": {
            key: anchored.python[key]
            for key in ("path", "bytes", "sha256", "version")
        },
        "git": {
            key: anchored.git[key]
            for key in ("path", "bytes", "sha256", "version")
        },
    }


def build_next_source_binding(
    repo_root: Path = REPO_ROOT,
    *,
    accepted_baton_commit: str,
    accepted_tooling_receipt_sha256: str,
    candidate_commit: str,
) -> dict[str, Any]:
    """Bind a direct-child source using only externally anchored B16 bytes."""

    _require_isolated_binding_interpreter()
    root = repo_root.resolve(strict=True)
    if not _valid_commit(candidate_commit) or candidate_commit == accepted_baton_commit:
        raise VerificationError("candidate commit binding is malformed")
    anchored = _anchor_next_source_tools(root, accepted_tooling_receipt_sha256)
    layout = _discover_binding_git_layout(root)
    reader = _GitBatchObjectReader(anchored.git, layout)
    try:
        trust_root = _validate_next_source_trust_topology(
            anchored, layout, accepted_baton_commit, reader
        )
        candidate = _candidate_manifest_from_objects(
            reader,
            accepted_baton_commit=accepted_baton_commit,
            candidate_commit=candidate_commit,
        )
        reader.close()
    except Exception:
        reader.abort()
        raise
    ending_anchor = _anchor_next_source_tools(root, accepted_tooling_receipt_sha256)
    ending_layout = _discover_binding_git_layout(root)
    ending_reader = _GitBatchObjectReader(ending_anchor.git, ending_layout)
    try:
        ending_trust_root = _validate_next_source_trust_topology(
            ending_anchor, ending_layout, accepted_baton_commit, ending_reader
        )
        ending_reader.close()
    except Exception:
        ending_reader.abort()
        raise
    final_layout = _discover_binding_git_layout(root)
    if ending_anchor != anchored:
        raise VerificationError("anchored bootstrap bytes changed during source binding")
    if ending_layout != layout or final_layout != ending_layout:
        raise VerificationError("bootstrap Git layout changed during source binding")
    if not _exact_json_value(ending_trust_root, trust_root):
        raise VerificationError("bootstrap trust topology changed during source binding")
    receipt: dict[str, Any] = {
        "schema": NEXT_SOURCE_SCHEMA,
        "verdict": NEXT_SOURCE_OK_VERDICT,
        "claim": NEXT_SOURCE_CLAIM,
        "authority": {
            "launch_authorized": False,
            "publication_authorized": False,
        },
        "limitations": list(NEXT_SOURCE_LIMITATIONS),
        "policy": dict(NEXT_SOURCE_POLICY),
        "trust_root": trust_root,
        "candidate": candidate,
        "problems": [],
        "problem_count": 0,
    }
    receipt["receipt_payload_sha256"] = _sha256_bytes(_canonical_json(receipt))
    if set(receipt) != NEXT_SOURCE_FIELDS:
        raise VerificationError("generated next-source receipt field set drift")
    encoded = _canonical_json(receipt) + b"\n"
    if len(encoded) > NEXT_SOURCE_MAX_RECEIPT_BYTES:
        raise VerificationError("generated next-source receipt exceeds byte bound")
    return receipt


def _preflight_next_source_json_bounds(raw_receipt: bytes) -> None:
    """Bound nesting and broad node growth before the recursive stdlib decoder runs."""

    depth = 0
    structural_budget = 0
    in_string = False
    escaped = False
    for byte in raw_receipt:
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
            continue
        if byte == 0x22:
            in_string = True
        elif byte in (0x7B, 0x5B):
            depth += 1
            structural_budget += 1
            if depth > NEXT_SOURCE_MAX_JSON_DEPTH:
                raise VerificationError("next-source JSON depth exceeds bound")
        elif byte in (0x7D, 0x5D):
            depth -= 1
        elif byte == 0x2C:
            structural_budget += 1
        if structural_budget > NEXT_SOURCE_MAX_JSON_NODES:
            raise VerificationError("next-source JSON node count exceeds bound")


def _parse_next_source_json(raw_receipt: bytes) -> dict[str, Any]:
    _preflight_next_source_json_bounds(raw_receipt)

    def parse_integer(value: str) -> int:
        if len(value.lstrip("-")) > 19:
            raise VerificationError("next-source JSON integer is oversized")
        parsed = int(value)
        if abs(parsed) > 9_223_372_036_854_775_807:
            raise VerificationError("next-source JSON integer is oversized")
        return parsed

    def reject_float(_value: str) -> float:
        raise VerificationError("next-source JSON floats are forbidden")

    value = json.loads(
        raw_receipt,
        object_pairs_hook=_strict_json_object,
        parse_int=parse_integer,
        parse_float=reject_float,
        parse_constant=_reject_nonfinite_json,
    )
    if not isinstance(value, dict):
        raise VerificationError("next-source JSON root is not an object")
    stack: list[tuple[object, int]] = [(value, 1)]
    nodes = 0
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > NEXT_SOURCE_MAX_JSON_NODES:
            raise VerificationError("next-source JSON node count exceeds bound")
        if depth > NEXT_SOURCE_MAX_JSON_DEPTH:
            raise VerificationError("next-source JSON depth exceeds bound")
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str) or len(key.encode("utf-8")) > 256:
                    raise VerificationError("next-source JSON key is oversized")
                stack.append((child, depth + 1))
        elif isinstance(item, list):
            stack.extend((child, depth + 1) for child in item)
        elif isinstance(item, str) and len(item.encode("utf-8")) > 4_096:
            raise VerificationError("next-source JSON string exceeds bound")
        elif not isinstance(item, (str, int, bool, type(None))):
            raise VerificationError("next-source JSON scalar type is forbidden")
    return value


def _strict_next_source_receipt(raw_receipt: bytes) -> dict[str, Any]:
    if not raw_receipt or len(raw_receipt) > NEXT_SOURCE_MAX_RECEIPT_BYTES:
        raise VerificationError("next-source receipt byte count is outside the contract")
    receipt = _parse_next_source_json(raw_receipt)
    if raw_receipt != _canonical_json(receipt) + b"\n":
        raise VerificationError("next-source receipt encoding is not canonical")
    if set(receipt) != NEXT_SOURCE_FIELDS:
        raise VerificationError("next-source receipt field set mismatch")
    if (
        receipt.get("schema") != NEXT_SOURCE_SCHEMA
        or receipt.get("verdict") != NEXT_SOURCE_OK_VERDICT
        or receipt.get("claim") != NEXT_SOURCE_CLAIM
        or not _exact_json_value(receipt.get("limitations"), NEXT_SOURCE_LIMITATIONS)
        or not _exact_json_value(receipt.get("policy"), NEXT_SOURCE_POLICY)
        or not _exact_json_value(
            receipt.get("authority"),
            {"launch_authorized": False, "publication_authorized": False},
        )
        or receipt.get("problems") != []
        or type(receipt.get("problem_count")) is not int
        or receipt.get("problem_count") != 0
    ):
        raise VerificationError("next-source receipt fixed contract mismatch")
    payload = dict(receipt)
    claimed_payload = payload.pop("receipt_payload_sha256", None)
    if claimed_payload != _sha256_bytes(_canonical_json(payload)):
        raise VerificationError("next-source receipt payload checksum mismatch")
    trust_root = receipt.get("trust_root")
    if not isinstance(trust_root, Mapping) or set(trust_root) != NEXT_SOURCE_TRUST_ROOT_FIELDS:
        raise VerificationError("next-source trust-root field set is malformed")
    for key in ("baton_commit", "baton_tree", "source_commit", "receipt_commit"):
        if not _valid_commit(trust_root.get(key)):
            raise VerificationError(f"next-source trust-root {key} is malformed")
    tooling_receipt = trust_root.get("tooling_receipt")
    if (
        not isinstance(tooling_receipt, Mapping)
        or set(tooling_receipt) != NEXT_SOURCE_ARTIFACT_FIELDS
        or tooling_receipt.get("path") != RECEIPT_REL
        or type(tooling_receipt.get("bytes")) is not int
        or tooling_receipt.get("bytes") < 1
        or tooling_receipt.get("bytes") > 8 * 1024 * 1024
        or not _is_sha256(tooling_receipt.get("sha256"))
    ):
        raise VerificationError("next-source tooling-receipt binding is malformed")
    binder = trust_root.get("binder")
    if (
        not isinstance(binder, Mapping)
        or set(binder) != NEXT_SOURCE_BINDER_FIELDS
        or binder.get("path") != BINDER_REL
        or binder.get("mode") != "100644"
        or type(binder.get("bytes")) is not int
        or binder.get("bytes") < 1
        or binder.get("bytes") > NEXT_SOURCE_MAX_BLOB_BYTES
        or not _valid_commit(binder.get("git_blob_oid"))
        or not _is_sha256(binder.get("sha256"))
    ):
        raise VerificationError("next-source binder binding is malformed")
    for tool_name in ("python", "git"):
        tool = trust_root.get(tool_name)
        if (
            not isinstance(tool, Mapping)
            or set(tool) != NEXT_SOURCE_TOOL_FIELDS
            or not isinstance(tool.get("path"), str)
            or not Path(tool["path"]).is_absolute()
            or type(tool.get("bytes")) is not int
            or tool.get("bytes") < 1
            or not _is_sha256(tool.get("sha256"))
            or not isinstance(tool.get("version"), str)
            or not tool.get("version")
        ):
            raise VerificationError(f"next-source {tool_name} binding is malformed")
    candidate = receipt.get("candidate")
    if not isinstance(candidate, Mapping) or set(candidate) != NEXT_SOURCE_CANDIDATE_FIELDS:
        raise VerificationError("next-source candidate field set is malformed")
    for key in ("commit", "parent", "tree"):
        if not _valid_commit(candidate.get(key)):
            raise VerificationError(f"next-source candidate {key} is malformed")
    if candidate.get("parent") != trust_root.get("baton_commit"):
        raise VerificationError("next-source candidate parent differs from trust root")
    if (
        type(candidate.get("commit_bytes")) is not int
        or candidate.get("commit_bytes") < 1
        or candidate.get("commit_bytes") > NEXT_SOURCE_MAX_COMMIT_BYTES
        or not _is_sha256(candidate.get("commit_sha256"))
    ):
        raise VerificationError("next-source commit-object binding is malformed")
    for key, minimum, maximum in (
        ("tree_object_count", 1, NEXT_SOURCE_MAX_TREE_OBJECTS),
        ("tree_object_bytes", 1, NEXT_SOURCE_MAX_TREE_BYTES),
        ("file_count", 1, NEXT_SOURCE_MAX_FILES),
        ("total_file_bytes", 0, NEXT_SOURCE_MAX_TOTAL_FILE_BYTES),
        ("unique_blob_count", 1, NEXT_SOURCE_MAX_FILES),
        ("unique_blob_bytes", 0, NEXT_SOURCE_MAX_TOTAL_FILE_BYTES),
    ):
        value = candidate.get(key)
        if type(value) is not int or value < minimum or value > maximum:
            raise VerificationError(f"next-source candidate {key} is outside bounds")
    if not _is_sha256(candidate.get("manifest_sha256")):
        raise VerificationError("next-source manifest aggregate digest is malformed")
    files = candidate.get("files")
    if not isinstance(files, list) or len(files) > NEXT_SOURCE_MAX_FILES:
        raise VerificationError("next-source manifest is malformed or oversized")
    previous_path: bytes | None = None
    total_bytes = 0
    for row in files:
        if not isinstance(row, Mapping) or set(row) != NEXT_SOURCE_FILE_FIELDS:
            raise VerificationError("next-source manifest row is malformed")
        path = row.get("path")
        if not isinstance(path, str):
            raise VerificationError("next-source manifest path is malformed")
        try:
            path_bytes = path.encode("ascii", errors="strict")
        except UnicodeEncodeError as error:
            raise VerificationError("next-source manifest path is not ASCII") from error
        if previous_path is not None and path_bytes <= previous_path:
            raise VerificationError("next-source manifest paths are not strictly ordered")
        previous_path = path_bytes
        if row.get("mode") not in NEXT_SOURCE_ALLOWED_BLOB_MODES:
            raise VerificationError("next-source manifest mode is invalid")
        size = row.get("bytes")
        if type(size) is not int or size < 0 or size > NEXT_SOURCE_MAX_BLOB_BYTES:
            raise VerificationError("next-source manifest byte count is invalid")
        total_bytes += size
        if total_bytes > NEXT_SOURCE_MAX_TOTAL_FILE_BYTES:
            raise VerificationError("next-source manifest total exceeds byte bound")
        if not _valid_commit(row.get("git_blob_oid")) or not _is_sha256(
            row.get("sha256")
        ):
            raise VerificationError("next-source manifest digest is malformed")
    if (
        type(candidate.get("file_count")) is not int
        or candidate.get("file_count") != len(files)
        or type(candidate.get("total_file_bytes")) is not int
        or candidate.get("total_file_bytes") != total_bytes
        or candidate.get("manifest_sha256") != _sha256_bytes(_canonical_json(files))
    ):
        raise VerificationError("next-source manifest aggregate mismatch")
    unique_blobs: dict[str, tuple[int, str]] = {}
    for row in files:
        oid = str(row["git_blob_oid"])
        size = int(row["bytes"])
        sha256 = str(row["sha256"])
        identity = (size, sha256)
        if oid in unique_blobs and unique_blobs[oid] != identity:
            raise VerificationError("next-source duplicate blob OID has identity drift")
        unique_blobs[oid] = identity
    if (
        candidate.get("unique_blob_count") != len(unique_blobs)
        or candidate.get("unique_blob_count") > candidate.get("file_count")
        or candidate.get("unique_blob_bytes")
        != sum(size for size, _sha256 in unique_blobs.values())
        or candidate.get("unique_blob_bytes") > candidate.get("total_file_bytes")
    ):
        raise VerificationError("next-source unique-blob aggregate mismatch")
    return receipt


def validate_next_source_binding(
    raw_receipt: bytes,
    repo_root: Path = REPO_ROOT,
    *,
    expected_baton_commit: str,
    expected_tooling_receipt_sha256: str,
    expected_candidate_commit: str,
    expected_receipt_sha256: str,
) -> list[str]:
    """Replay one receipt with detached identities; never trust receipt-derived expectations."""

    try:
        _require_isolated_binding_interpreter()
        if not _is_sha256(expected_receipt_sha256):
            raise VerificationError("detached next-source receipt SHA-256 is malformed")
        if _sha256_bytes(raw_receipt) != expected_receipt_sha256:
            raise VerificationError("next-source receipt differs from detached SHA-256")
        observed = _strict_next_source_receipt(raw_receipt)
        if observed.get("candidate", {}).get("commit") != expected_candidate_commit:
            raise VerificationError("next-source candidate differs from detached commit")
        if observed.get("trust_root", {}).get("baton_commit") != expected_baton_commit:
            raise VerificationError("next-source baton differs from detached accepted B16")
        if (
            observed.get("trust_root", {}).get("tooling_receipt", {}).get("sha256")
            != expected_tooling_receipt_sha256
        ):
            raise VerificationError("next-source R16 digest differs from detached accepted digest")
        replayed = build_next_source_binding(
            repo_root,
            accepted_baton_commit=expected_baton_commit,
            accepted_tooling_receipt_sha256=expected_tooling_receipt_sha256,
            candidate_commit=expected_candidate_commit,
        )
        if not _exact_json_value(observed, replayed):
            raise VerificationError("next-source receipt differs from independent object replay")
    except Exception as exc:
        return [f"next-source binding invalid: {type(exc).__name__}: {exc}"]
    return []


def _write_next_source_no_clobber(
    output: Path,
    payload: bytes,
    *,
    forbidden_roots: Sequence[Path] = (REPO_ROOT,),
) -> None:
    output = output.absolute()
    if len(payload) > NEXT_SOURCE_MAX_RECEIPT_BYTES:
        raise VerificationError("next-source output exceeds byte bound")
    if (
        output.name in {"", ".", ".."}
        or len(output.name.encode("utf-8")) > 255
        or any(
            byte
            not in b"-.0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz"
            for byte in output.name.encode("utf-8")
        )
    ):
        raise VerificationError("next-source output basename is unsafe")
    folded_output_name = output.name.casefold()
    if folded_output_name.startswith(
        ".next-source."
    ) and folded_output_name.endswith(".tmp"):
        raise VerificationError(
            "next-source output basename uses the reserved staging namespace"
        )
    parent = output.parent
    if (
        not parent.is_dir()
        or parent.is_symlink()
        or parent.resolve(strict=True) != parent.absolute()
    ):
        raise VerificationError("next-source output parent is not a physical directory")
    parent_before = parent.stat(follow_symlinks=False)
    directory_fd, parent_route = _open_physical_directory_chain(parent)
    temporary_name = f".next-source.{os.getpid():x}.{time.monotonic_ns():x}.tmp"
    publication_state = "PRECOMMIT"
    temporary_owned = False
    temporary_identity: tuple[int, int] | None = None
    temporary_descriptor: int | None = None

    def owner_mode_identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
        return (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_uid,
            value.st_gid,
        )

    def revalidate_open_parent(*, initial: bool) -> os.stat_result:
        if parent.is_symlink() or parent.resolve(strict=True) != parent.absolute():
            raise VerificationError("next-source output parent became redirected")
        path_state = parent.stat(follow_symlinks=False)
        descriptor_state = os.fstat(directory_fd)
        if not stat.S_ISDIR(descriptor_state.st_mode):
            raise VerificationError("next-source output parent descriptor is not a directory")
        if initial:
            if owner_mode_identity(path_state) != owner_mode_identity(
                parent_before
            ) or owner_mode_identity(descriptor_state) != owner_mode_identity(
                parent_before
            ):
                raise VerificationError("next-source output parent changed while opening")
        elif (
            owner_mode_identity(path_state) != owner_mode_identity(descriptor_state)
            or owner_mode_identity(descriptor_state)
            != owner_mode_identity(parent_before)
        ):
            raise VerificationError("next-source output parent changed before publication")
        if (
            descriptor_state.st_uid != os.geteuid()
            or stat.S_IMODE(descriptor_state.st_mode) & 0o022
        ):
            raise VerificationError("next-source output parent ownership or mode changed")
        return descriptor_state

    def inspect_final_link_state() -> tuple[bool, bool]:
        if temporary_identity is None:
            return False, False
        try:
            named = os.stat(output.name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            return False, False
        except OSError as error:
            raise VerificationError("next-source final link state is unreadable") from error
        if (
            not stat.S_ISREG(named.st_mode)
            or (named.st_dev, named.st_ino) != temporary_identity
        ):
            return False, False
        if (
            stat.S_IMODE(named.st_mode) != 0o600
            or named.st_size != len(payload)
            or named.st_nlink != 2
        ):
            return True, False
        try:
            descriptor = os.open(
                output.name,
                os.O_RDONLY
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_NONBLOCK", 0)
                | getattr(os, "O_CLOEXEC", 0),
                dir_fd=directory_fd,
            )
            try:
                before = os.fstat(descriptor)
                remaining = len(payload)
                chunks: list[bytes] = []
                while remaining:
                    chunk = os.read(descriptor, min(1024 * 1024, remaining))
                    if not chunk:
                        return True, False
                    chunks.append(chunk)
                    remaining -= len(chunk)
                if os.read(descriptor, 1):
                    return True, False
                after = os.fstat(descriptor)
            finally:
                os.close(descriptor)
        except BaseException:
            return True, False
        return True, (
            b"".join(chunks) == payload
            and _physical_stat_identity(before) == _physical_stat_identity(after)
            and (after.st_dev, after.st_ino) == temporary_identity
            and after.st_nlink == 2
        )

    def owned_temporary_state() -> os.stat_result:
        nonlocal temporary_owned
        if not temporary_owned or temporary_identity is None:
            raise VerificationError("next-source temporary output is not owned")
        try:
            observed = os.stat(
                temporary_name, dir_fd=directory_fd, follow_symlinks=False
            )
        except FileNotFoundError as error:
            temporary_owned = False
            raise VerificationError("next-source temporary output disappeared") from error
        except OSError as error:
            temporary_owned = False
            raise VerificationError("next-source temporary output is unreadable") from error
        if (
            not stat.S_ISREG(observed.st_mode)
            or (observed.st_dev, observed.st_ino) != temporary_identity
        ):
            temporary_owned = False
            raise VerificationError("next-source temporary output identity changed")
        return observed

    def unlink_owned_temporary(*, require_current: bool) -> None:
        nonlocal temporary_owned
        if not temporary_owned or temporary_identity is None:
            return
        try:
            observed = os.stat(
                temporary_name, dir_fd=directory_fd, follow_symlinks=False
            )
        except FileNotFoundError as error:
            temporary_owned = False
            if require_current:
                raise VerificationError(
                    "next-source temporary output disappeared before unlink"
                ) from error
            return
        except OSError as error:
            if require_current:
                raise VerificationError(
                    "next-source temporary output is unreadable before unlink"
                ) from error
            return
        if (
            not stat.S_ISREG(observed.st_mode)
            or (observed.st_dev, observed.st_ino) != temporary_identity
        ):
            temporary_owned = False
            if require_current:
                raise VerificationError(
                    "next-source temporary output identity changed before unlink"
                )
            return
        try:
            os.unlink(temporary_name, dir_fd=directory_fd)
        except FileNotFoundError as error:
            temporary_owned = False
            if require_current:
                raise VerificationError(
                    "next-source temporary output disappeared during unlink"
                ) from error
            return
        temporary_owned = False

    try:
        if (
            not stat.S_ISDIR(parent_before.st_mode)
            or parent_before.st_uid != os.geteuid()
            or stat.S_IMODE(parent_before.st_mode) & 0o022
        ):
            raise VerificationError(
                "next-source output parent ownership or mode is unsafe"
            )
        for forbidden_root in forbidden_roots:
            forbidden_descriptor, _forbidden_route = _open_physical_directory_chain(
                forbidden_root.resolve(strict=True)
            )
            try:
                forbidden_state = os.fstat(forbidden_descriptor)
            finally:
                os.close(forbidden_descriptor)
            if _physical_route_contains_directory_identity(
                parent_route, (forbidden_state.st_dev, forbidden_state.st_ino)
            ):
                raise VerificationError(
                    "next-source output is inside a forbidden trusted root"
                )
        revalidate_open_parent(initial=True)
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0)
        )
        temporary_descriptor = os.open(
            temporary_name, flags, 0o600, dir_fd=directory_fd
        )
        temporary_owned = True
        created = os.fstat(temporary_descriptor)
        if (
            not stat.S_ISREG(created.st_mode)
            or stat.S_IMODE(created.st_mode) != 0o600
            or created.st_size != 0
            or created.st_nlink != 1
        ):
            raise VerificationError(
                "next-source created temporary output identity is invalid"
            )
        temporary_identity = (created.st_dev, created.st_ino)
        view = memoryview(payload)
        while view:
            written = os.write(temporary_descriptor, view)
            if written <= 0:
                raise VerificationError("next-source output write made no progress")
            view = view[written:]
        os.fsync(temporary_descriptor)
        observed = os.fstat(temporary_descriptor)
        if (
            not stat.S_ISREG(observed.st_mode)
            or stat.S_IMODE(observed.st_mode) != 0o600
            or observed.st_size != len(payload)
            or observed.st_nlink != 1
            or temporary_identity != (observed.st_dev, observed.st_ino)
        ):
            raise VerificationError("next-source temporary output identity is invalid")
        revalidate_open_parent(initial=False)
        staged = owned_temporary_state()
        if (
            stat.S_IMODE(staged.st_mode) != 0o600
            or staged.st_size != len(payload)
            or staged.st_nlink != 1
        ):
            raise VerificationError(
                "next-source temporary output changed before publication"
            )
        try:
            os.link(
                temporary_name,
                output.name,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
                follow_symlinks=False,
            )
        except BaseException as error:
            try:
                landed, exact = inspect_final_link_state()
            except BaseException as reconciliation_error:
                publication_state = "INDETERMINATE"
                raise NextSourceBindingIndeterminateError(
                    "next-source hard-link outcome is indeterminate after "
                    "reconciliation failure"
                ) from reconciliation_error
            if landed:
                publication_state = "COMMITTED"
                raise NextSourceBindingCommittedError(
                    "next-source binding hard link landed before link-call failure"
                    if exact
                    else "next-source binding landed with an unverifiable postcondition"
                ) from error
            if isinstance(error, FileExistsError):
                raise VerificationError("next-source output already exists") from error
            raise
        publication_state = "COMMITTED"
        try:
            os.fsync(directory_fd)
            unlink_owned_temporary(require_current=True)
            os.fsync(directory_fd)
            final = _read_stable_regular_file_bounded(
                output, NEXT_SOURCE_MAX_RECEIPT_BYTES
            )
            final_stat = os.stat(output.name, dir_fd=directory_fd, follow_symlinks=False)
            if (
                final != payload
                or not stat.S_ISREG(final_stat.st_mode)
                or stat.S_IMODE(final_stat.st_mode) != 0o600
                or final_stat.st_nlink != 1
                or temporary_identity != (final_stat.st_dev, final_stat.st_ino)
            ):
                raise VerificationError(
                    "published next-source output failed final validation"
                )
            revalidate_open_parent(initial=False)
        except BaseException as error:
            raise NextSourceBindingCommittedError(
                "next-source binding committed but a post-link condition failed"
            ) from error
    finally:
        try:
            if publication_state == "PRECOMMIT":
                unlink_owned_temporary(require_current=False)
        finally:
            try:
                try:
                    os.close(directory_fd)
                except BaseException as error:
                    if publication_state == "COMMITTED":
                        raise NextSourceBindingCommittedError(
                            "next-source binding committed but directory close failed"
                        ) from error
                    if publication_state == "INDETERMINATE":
                        raise NextSourceBindingIndeterminateError(
                            "next-source hard-link outcome remains indeterminate after "
                            "directory close failure"
                        ) from error
                    raise VerificationError(
                        "next-source output directory close failed"
                    ) from error
            finally:
                if temporary_descriptor is not None:
                    try:
                        os.close(temporary_descriptor)
                    except BaseException as error:
                        if publication_state == "COMMITTED":
                            raise NextSourceBindingCommittedError(
                                "next-source binding committed but temporary descriptor "
                                "close failed"
                            ) from error
                        if publication_state == "INDETERMINATE":
                            raise NextSourceBindingIndeterminateError(
                                "next-source hard-link outcome remains indeterminate after "
                                "temporary descriptor close failure"
                            ) from error
                        raise VerificationError(
                            "next-source temporary descriptor close failed"
                        ) from error


def publish_next_source_binding(
    output: Path,
    repo_root: Path = REPO_ROOT,
    *,
    accepted_baton_commit: str,
    accepted_tooling_receipt_sha256: str,
    candidate_commit: str,
) -> tuple[str, int, dict[str, Any]]:
    receipt = build_next_source_binding(
        repo_root,
        accepted_baton_commit=accepted_baton_commit,
        accepted_tooling_receipt_sha256=accepted_tooling_receipt_sha256,
        candidate_commit=candidate_commit,
    )
    encoded = _canonical_json(receipt) + b"\n"
    digest = _sha256_bytes(encoded)
    byte_count = len(encoded)
    layout = _discover_binding_git_layout(repo_root.resolve(strict=True))
    _write_next_source_no_clobber(
        output,
        encoded,
        forbidden_roots=(layout.worktree, layout.common_dir),
    )
    return digest, byte_count, receipt


def validate_published_receipt_structure(
    receipt: Mapping[str, Any],
    repo_root: Path = REPO_ROOT,
    *,
    git_probe: GitProbe = default_structural_git_probe,
    ancestry_probe: AncestryProbe = default_ancestry_probe,
) -> list[str]:
    """Validate the explicit generation-sixteen lifecycle-control publication.

    Independent command replay is deliberately performed at the exact replacement receipt commit by
    :func:`validate_receipt`.  This post-transition validator instead proves that the committed
    receipt still binds the exact published source tree and that every later commit follows the
    narrow state/baton/preflight-artifact topology without changing frozen tooling.
    """

    errors: list[str] = []
    if not isinstance(receipt, Mapping):
        return ["receipt root is not an object"]
    if set(receipt) != RECEIPT_FIELDS:
        errors.append("receipt root field set mismatch")
    if receipt.get("schema") != SCHEMA:
        errors.append("schema mismatch")
    if not _exact_json_value(
        receipt.get("publication"),
        EXPECTED_RECOVERY_PUBLICATION,
    ):
        errors.append("generation-sixteen publication block mismatch")
    if receipt.get("verdict") != OK_VERDICT:
        errors.append("receipt verdict is not green")
    if (
        type(receipt.get("problem_count")) is not int
        or receipt.get("problem_count") != 0
        or receipt.get("problems") != []
    ):
        errors.append("receipt problem metadata is not exactly green")
    errors.extend(_nested_receipt_shape_errors(receipt))
    payload = dict(receipt)
    claimed_payload_hash = payload.pop("receipt_payload_sha256", None)
    if claimed_payload_hash != _sha256_bytes(_canonical_json(payload)):
        errors.append("receipt payload digest mismatch")

    try:
        root = repo_root.resolve(strict=True)
        repository = receipt.get("repository")
        if (
            not isinstance(repository, Mapping)
            or repository.get("root") != CANONICAL_REPOSITORY
        ):
            raise VerificationError("receipt canonical repository identity is malformed")
        claimed_start = repository.get("git_start")
        claimed_end = repository.get("git_end")
        if not isinstance(claimed_start, Mapping) or claimed_start != claimed_end:
            raise VerificationError("receipt source Git state was not stable")
        source_commit = claimed_start.get("head")
        if not _valid_commit(source_commit):
            raise VerificationError("receipt source commit is malformed")
        empty_status = _sha256_bytes(b"")
        expected_source_paths = tuple(sorted(RECOVERY_SOURCE_COMMIT_PATHS))
        if (
            claimed_start.get("dirty_entries") != []
            or claimed_start.get("porcelain_v1_z_sha256") != empty_status
            or claimed_start.get("branch") != "master"
            or claimed_start.get("upstream") != "origin/master"
            or claimed_start.get("upstream_head") != source_commit
            or claimed_start.get("parents") != [RECOVERY_SOURCE_PARENT]
            or claimed_start.get("commit_paths") != list(expected_source_paths)
        ):
            raise VerificationError("receipt source publication claim is malformed")
        if (
            repository.get("git_head_stable") is not True
            or repository.get("git_state_stable") is not True
            or repository.get("repository_clean_state_stable") is not True
        ):
            raise VerificationError("receipt repository stability flags are not green")

        source_parents, source_paths = _git_commit_row(root, source_commit)
        if source_parents != (RECOVERY_SOURCE_PARENT,) or source_paths != expected_source_paths:
            raise VerificationError(
                "actual generation-sixteen source topology or path scope is wrong"
            )
        lifecycle_source_parents, lifecycle_source_paths = _git_commit_row(
            root, GENERATION_SIXTEEN_SOURCE_COMMIT
        )
        if lifecycle_source_parents != (GENERATION_SIXTEEN_SOURCE_PARENT,) or (
            lifecycle_source_paths != tuple(sorted(GENERATION_SIXTEEN_SOURCE_COMMIT_PATHS))
        ):
            raise VerificationError(
                "published F16 lifecycle-control source topology or path scope changed"
            )

        inventory = _source_inventory_from_tree(root, source_commit)
        if receipt.get("inventory") != inventory.as_dict():
            raise VerificationError("receipt inventory does not match the published source tree")
        if receipt.get("inventory_sha256") != _inventory_digest(inventory):
            raise VerificationError("receipt inventory digest is wrong")
        claimed_files = receipt.get("files")
        if not isinstance(claimed_files, Mapping) or set(claimed_files) != set(
            inventory.tested_files
        ):
            raise VerificationError("receipt file binding set is malformed")
        source_projection: dict[str, dict[str, Any]] = {}
        for relative_path in inventory.tested_files:
            source_bytes = _git_file_bytes(root, source_commit, relative_path)
            projection = {"sha256": _sha256_bytes(source_bytes), "bytes": len(source_bytes)}
            source_projection[relative_path] = projection
            row = claimed_files.get(relative_path)
            if not isinstance(row, Mapping) or {
                "sha256": row.get("sha256"),
                "bytes": row.get("bytes"),
            } != projection:
                raise VerificationError(
                    f"receipt file binding differs from source commit: {relative_path}"
                )
        if receipt.get("file_content_set_sha256") != _sha256_bytes(
            _canonical_json(source_projection)
        ):
            raise VerificationError("receipt source content-set digest is wrong")

        toolchain = receipt.get("toolchain")
        if not isinstance(toolchain, Mapping) or set(toolchain) != set(TOOL_NAMES):
            raise VerificationError("receipt toolchain set is malformed")
        for name in TOOL_NAMES:
            row = toolchain.get(name)
            if not isinstance(row, Mapping):
                raise VerificationError(f"receipt toolchain row is malformed: {name}")
            path = Path(str(row.get("path", "")))
            digest = row.get("sha256")
            if (
                not path.is_absolute()
                or not _allowed_tool_path(path)
                or not isinstance(digest, str)
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
                or not isinstance(row.get("bytes"), int)
                or not isinstance(row.get("version"), str)
            ):
                raise VerificationError(f"receipt toolchain row is invalid: {name}")
        if receipt.get("environment_contract") != _sanitized_environment(toolchain):
            raise VerificationError("receipt environment contract is malformed")
        expected_commands = build_commands(inventory, toolchain)
        if receipt.get("command_contract") != [list(command) for command in expected_commands]:
            raise VerificationError("receipt command contract is malformed")
        command_rows = receipt.get("commands")
        if not isinstance(command_rows, list) or len(command_rows) != len(expected_commands):
            raise VerificationError("receipt command result set is incomplete")
        for index, (row, command) in enumerate(zip(command_rows, expected_commands)):
            if (
                not isinstance(row, Mapping)
                or row.get("argv") != list(command)
                or type(row.get("return_code")) is not int
                or row.get("return_code") != 0
            ):
                raise VerificationError(f"receipt command result is not green: {index}")

        history_raw = _git_bytes(root, ("log", "--format=%H", "--", RECEIPT_REL))
        receipt_history = tuple(
            line for line in history_raw.decode("ascii", errors="strict").splitlines() if line
        )
        if (
            len(receipt_history) != 16
            or not _valid_commit(receipt_history[0])
            or receipt_history[1:] != (
                GENERATION_FIFTEEN_RECEIPT_COMMIT,
                GENERATION_FOURTEEN_RECEIPT_COMMIT,
                GENERATION_THIRTEEN_RECEIPT_COMMIT,
                GENERATION_TWELVE_RECEIPT_COMMIT,
                GENERATION_ELEVEN_RECEIPT_COMMIT,
                GENERATION_TEN_RECEIPT_COMMIT,
                GENERATION_NINE_RECEIPT_COMMIT,
                GENERATION_EIGHT_RECEIPT_COMMIT,
                GENERATION_SEVEN_RECEIPT_COMMIT,
                GENERATION_SIX_RECEIPT_COMMIT,
                GENERATION_FIVE_RECEIPT_COMMIT,
                GENERATION_FOUR_RECEIPT_COMMIT,
                GENERATION_THREE_RECEIPT_COMMIT,
                GENERATION_TWO_RECEIPT_COMMIT,
                GENERATION_ONE_RECEIPT_COMMIT,
            )
        ):
            raise VerificationError(
                "canonical receipt history is not exact generation-sixteen, "
                "generation-fifteen, generation-fourteen, generation-thirteen, generation-twelve, "
                "generation-eleven, generation-ten, generation-nine, generation-eight, "
                "generation-seven, generation-six, generation-five, generation-four, "
                "generation-three, generation-two, then generation-one"
            )
        receipt_commit = receipt_history[0]

        old_source_parents, old_source_paths = _git_commit_row(
            root, GENERATION_ONE_SOURCE_COMMIT
        )
        if old_source_parents != (GENERATION_ONE_SOURCE_PARENT,) or old_source_paths != tuple(
            sorted(GENERATION_ONE_SOURCE_COMMIT_PATHS)
        ):
            raise VerificationError("generation-one source topology or path scope changed")
        old_receipt_parents, old_receipt_paths = _git_commit_row(
            root, GENERATION_ONE_RECEIPT_COMMIT
        )
        if old_receipt_parents != (GENERATION_ONE_SOURCE_COMMIT,) or old_receipt_paths != (
            RECEIPT_REL,
        ):
            raise VerificationError("generation-one receipt topology or path scope changed")

        generation_two_source_parents, generation_two_source_paths = _git_commit_row(
            root, GENERATION_TWO_SOURCE_COMMIT
        )
        if generation_two_source_parents != (GENERATION_TWO_SOURCE_PARENT,) or (
            generation_two_source_paths != tuple(sorted(GENERATION_TWO_SOURCE_COMMIT_PATHS))
        ):
            raise VerificationError("generation-two source topology or path scope changed")
        generation_two_receipt_parents, generation_two_receipt_paths = _git_commit_row(
            root, GENERATION_TWO_RECEIPT_COMMIT
        )
        if generation_two_receipt_parents != (GENERATION_TWO_SOURCE_COMMIT,) or (
            generation_two_receipt_paths != (RECEIPT_REL,)
        ):
            raise VerificationError("generation-two receipt topology or path scope changed")
        generation_two_state_parents, generation_two_state_paths = _git_commit_row(
            root, GENERATION_TWO_STATE_COMMIT
        )
        if generation_two_state_parents != (GENERATION_TWO_RECEIPT_COMMIT,) or (
            generation_two_state_paths != ("MISSION_STATE.json",)
        ):
            raise VerificationError("generation-two state topology or path scope changed")
        generation_two_baton_parents, generation_two_baton_paths = _git_commit_row(
            root, GENERATION_TWO_BATON_COMMIT
        )
        if generation_two_baton_parents != (GENERATION_TWO_STATE_COMMIT,) or (
            generation_two_baton_paths != ("CONTINUITY.md", "HANDOFF.md")
        ):
            raise VerificationError("generation-two baton topology or path scope changed")

        generation_three_source_parents, generation_three_source_paths = _git_commit_row(
            root, GENERATION_THREE_SOURCE_COMMIT
        )
        if generation_three_source_parents != (GENERATION_THREE_SOURCE_PARENT,) or (
            generation_three_source_paths
            != tuple(sorted(GENERATION_THREE_SOURCE_COMMIT_PATHS))
        ):
            raise VerificationError("generation-three source topology or path scope changed")
        generation_three_receipt_parents, generation_three_receipt_paths = _git_commit_row(
            root, GENERATION_THREE_RECEIPT_COMMIT
        )
        if generation_three_receipt_parents != (GENERATION_THREE_SOURCE_COMMIT,) or (
            generation_three_receipt_paths != (RECEIPT_REL,)
        ):
            raise VerificationError("generation-three receipt topology or path scope changed")
        generation_three_state_parents, generation_three_state_paths = _git_commit_row(
            root, GENERATION_THREE_STATE_COMMIT
        )
        if generation_three_state_parents != (GENERATION_THREE_RECEIPT_COMMIT,) or (
            generation_three_state_paths != ("MISSION_STATE.json",)
        ):
            raise VerificationError("generation-three state topology or path scope changed")
        generation_three_baton_parents, generation_three_baton_paths = _git_commit_row(
            root, GENERATION_THREE_BATON_COMMIT
        )
        if generation_three_baton_parents != (GENERATION_THREE_STATE_COMMIT,) or (
            generation_three_baton_paths != ("CONTINUITY.md", "HANDOFF.md")
        ):
            raise VerificationError("generation-three baton topology or path scope changed")
        generation_four_source_parents, generation_four_source_paths = _git_commit_row(
            root, GENERATION_FOUR_SOURCE_COMMIT
        )
        if generation_four_source_parents != (GENERATION_FOUR_SOURCE_PARENT,) or (
            generation_four_source_paths != tuple(sorted(GENERATION_FOUR_SOURCE_COMMIT_PATHS))
        ):
            raise VerificationError("generation-four source topology or path scope changed")
        generation_four_receipt_parents, generation_four_receipt_paths = _git_commit_row(
            root, GENERATION_FOUR_RECEIPT_COMMIT
        )
        if generation_four_receipt_parents != (GENERATION_FOUR_SOURCE_COMMIT,) or (
            generation_four_receipt_paths != (RECEIPT_REL,)
        ):
            raise VerificationError("generation-four receipt topology or path scope changed")
        generation_four_state_parents, generation_four_state_paths = _git_commit_row(
            root, GENERATION_FOUR_STATE_COMMIT
        )
        if generation_four_state_parents != (GENERATION_FOUR_RECEIPT_COMMIT,) or (
            generation_four_state_paths != ("MISSION_STATE.json",)
        ):
            raise VerificationError("generation-four state topology or path scope changed")
        generation_four_baton_parents, generation_four_baton_paths = _git_commit_row(
            root, GENERATION_FOUR_BATON_COMMIT
        )
        if generation_four_baton_parents != (GENERATION_FOUR_STATE_COMMIT,) or (
            generation_four_baton_paths != ("CONTINUITY.md", "HANDOFF.md")
        ):
            raise VerificationError("generation-four baton topology or path scope changed")
        # Generation five published only its source and receipt before its structural probe fired;
        # no generation-five state or baton commit exists, and none is required here.
        generation_five_source_parents, generation_five_source_paths = _git_commit_row(
            root, GENERATION_FIVE_SOURCE_COMMIT
        )
        if generation_five_source_parents != (GENERATION_FIVE_SOURCE_PARENT,) or (
            generation_five_source_paths != tuple(sorted(GENERATION_FIVE_SOURCE_COMMIT_PATHS))
        ):
            raise VerificationError("generation-five source topology or path scope changed")
        generation_five_receipt_parents, generation_five_receipt_paths = _git_commit_row(
            root, GENERATION_FIVE_RECEIPT_COMMIT
        )
        if generation_five_receipt_parents != (GENERATION_FIVE_SOURCE_COMMIT,) or (
            generation_five_receipt_paths != (RECEIPT_REL,)
        ):
            raise VerificationError("generation-five receipt topology or path scope changed")
        generation_six_source_parents, generation_six_source_paths = _git_commit_row(
            root, GENERATION_SIX_SOURCE_COMMIT
        )
        if generation_six_source_parents != (GENERATION_SIX_SOURCE_PARENT,) or (
            generation_six_source_paths != tuple(sorted(GENERATION_SIX_SOURCE_COMMIT_PATHS))
        ):
            raise VerificationError("generation-six source topology or path scope changed")
        generation_six_receipt_parents, generation_six_receipt_paths = _git_commit_row(
            root, GENERATION_SIX_RECEIPT_COMMIT
        )
        if generation_six_receipt_parents != (GENERATION_SIX_SOURCE_COMMIT,) or (
            generation_six_receipt_paths != (RECEIPT_REL,)
        ):
            raise VerificationError("generation-six receipt topology or path scope changed")
        generation_six_state_parents, generation_six_state_paths = _git_commit_row(
            root, GENERATION_SIX_STATE_COMMIT
        )
        if generation_six_state_parents != (GENERATION_SIX_RECEIPT_COMMIT,) or (
            generation_six_state_paths != ("MISSION_STATE.json",)
        ):
            raise VerificationError("generation-six state topology or path scope changed")
        generation_six_baton_parents, generation_six_baton_paths = _git_commit_row(
            root, GENERATION_SIX_BATON_COMMIT
        )
        if generation_six_baton_parents != (GENERATION_SIX_STATE_COMMIT,) or (
            generation_six_baton_paths != ("CONTINUITY.md", "HANDOFF.md")
        ):
            raise VerificationError("generation-six baton topology or path scope changed")
        generation_seven_source_parents, generation_seven_source_paths = _git_commit_row(
            root, GENERATION_SEVEN_SOURCE_COMMIT
        )
        if generation_seven_source_parents != (GENERATION_SEVEN_SOURCE_PARENT,) or (
            generation_seven_source_paths
            != tuple(sorted(GENERATION_SEVEN_SOURCE_COMMIT_PATHS))
        ):
            raise VerificationError("generation-seven source topology or path scope changed")
        generation_seven_receipt_parents, generation_seven_receipt_paths = _git_commit_row(
            root, GENERATION_SEVEN_RECEIPT_COMMIT
        )
        if generation_seven_receipt_parents != (GENERATION_SEVEN_SOURCE_COMMIT,) or (
            generation_seven_receipt_paths != (RECEIPT_REL,)
        ):
            raise VerificationError("generation-seven receipt topology or path scope changed")
        generation_seven_state_parents, generation_seven_state_paths = _git_commit_row(
            root, GENERATION_SEVEN_STATE_COMMIT
        )
        if generation_seven_state_parents != (GENERATION_SEVEN_RECEIPT_COMMIT,) or (
            generation_seven_state_paths != ("MISSION_STATE.json",)
        ):
            raise VerificationError("generation-seven state topology or path scope changed")
        generation_seven_baton_parents, generation_seven_baton_paths = _git_commit_row(
            root, GENERATION_SEVEN_BATON_COMMIT
        )
        if generation_seven_baton_parents != (GENERATION_SEVEN_STATE_COMMIT,) or (
            generation_seven_baton_paths != ("CONTINUITY.md", "HANDOFF.md")
        ):
            raise VerificationError("generation-seven baton topology or path scope changed")
        generation_eight_source_parents, generation_eight_source_paths = _git_commit_row(
            root, GENERATION_EIGHT_SOURCE_COMMIT
        )
        if generation_eight_source_parents != (GENERATION_EIGHT_SOURCE_PARENT,) or (
            generation_eight_source_paths
            != tuple(sorted(GENERATION_EIGHT_SOURCE_COMMIT_PATHS))
        ):
            raise VerificationError("generation-eight source topology or path scope changed")
        generation_eight_receipt_parents, generation_eight_receipt_paths = _git_commit_row(
            root, GENERATION_EIGHT_RECEIPT_COMMIT
        )
        if generation_eight_receipt_parents != (GENERATION_EIGHT_SOURCE_COMMIT,) or (
            generation_eight_receipt_paths != (RECEIPT_REL,)
        ):
            raise VerificationError("generation-eight receipt topology or path scope changed")
        generation_eight_state_parents, generation_eight_state_paths = _git_commit_row(
            root, GENERATION_EIGHT_STATE_COMMIT
        )
        if generation_eight_state_parents != (GENERATION_EIGHT_RECEIPT_COMMIT,) or (
            generation_eight_state_paths != ("MISSION_STATE.json",)
        ):
            raise VerificationError("generation-eight state topology or path scope changed")
        generation_eight_baton_parents, generation_eight_baton_paths = _git_commit_row(
            root, GENERATION_EIGHT_BATON_COMMIT
        )
        if generation_eight_baton_parents != (GENERATION_EIGHT_STATE_COMMIT,) or (
            generation_eight_baton_paths != ("CONTINUITY.md", "HANDOFF.md")
        ):
            raise VerificationError("generation-eight baton topology or path scope changed")
        generation_nine_source_parents, generation_nine_source_paths = _git_commit_row(
            root, GENERATION_NINE_SOURCE_COMMIT
        )
        if generation_nine_source_parents != (GENERATION_NINE_SOURCE_PARENT,) or (
            generation_nine_source_paths != tuple(sorted(GENERATION_NINE_SOURCE_COMMIT_PATHS))
        ):
            raise VerificationError("generation-nine source topology or path scope changed")
        generation_nine_receipt_parents, generation_nine_receipt_paths = _git_commit_row(
            root, GENERATION_NINE_RECEIPT_COMMIT
        )
        if generation_nine_receipt_parents != (GENERATION_NINE_SOURCE_COMMIT,) or (
            generation_nine_receipt_paths != (RECEIPT_REL,)
        ):
            raise VerificationError("generation-nine receipt topology or path scope changed")
        generation_nine_state_parents, generation_nine_state_paths = _git_commit_row(
            root, GENERATION_NINE_STATE_COMMIT
        )
        if generation_nine_state_parents != (GENERATION_NINE_RECEIPT_COMMIT,) or (
            generation_nine_state_paths != ("MISSION_STATE.json",)
        ):
            raise VerificationError("generation-nine state topology or path scope changed")
        generation_nine_baton_parents, generation_nine_baton_paths = _git_commit_row(
            root, GENERATION_NINE_BATON_COMMIT
        )
        if generation_nine_baton_parents != (GENERATION_NINE_STATE_COMMIT,) or (
            generation_nine_baton_paths != ("CONTINUITY.md", "HANDOFF.md")
        ):
            raise VerificationError("generation-nine baton topology or path scope changed")
        generation_ten_source_parents, generation_ten_source_paths = _git_commit_row(
            root, GENERATION_TEN_SOURCE_COMMIT
        )
        if generation_ten_source_parents != (GENERATION_TEN_SOURCE_PARENT,) or (
            generation_ten_source_paths != tuple(sorted(GENERATION_TEN_SOURCE_COMMIT_PATHS))
        ):
            raise VerificationError("generation-ten source topology or path scope changed")
        generation_ten_receipt_parents, generation_ten_receipt_paths = _git_commit_row(
            root, GENERATION_TEN_RECEIPT_COMMIT
        )
        if generation_ten_receipt_parents != (GENERATION_TEN_SOURCE_COMMIT,) or (
            generation_ten_receipt_paths != (RECEIPT_REL,)
        ):
            raise VerificationError("generation-ten receipt topology or path scope changed")
        generation_ten_state_parents, generation_ten_state_paths = _git_commit_row(
            root, GENERATION_TEN_STATE_COMMIT
        )
        if generation_ten_state_parents != (GENERATION_TEN_RECEIPT_COMMIT,) or (
            generation_ten_state_paths != ("MISSION_STATE.json",)
        ):
            raise VerificationError("generation-ten state topology or path scope changed")
        generation_ten_baton_parents, generation_ten_baton_paths = _git_commit_row(
            root, GENERATION_TEN_BATON_COMMIT
        )
        if generation_ten_baton_parents != (GENERATION_TEN_STATE_COMMIT,) or (
            generation_ten_baton_paths != ("CONTINUITY.md", "HANDOFF.md")
        ):
            raise VerificationError("generation-ten baton topology or path scope changed")
        generation_eleven_source_parents, generation_eleven_source_paths = _git_commit_row(
            root, GENERATION_ELEVEN_SOURCE_COMMIT
        )
        if generation_eleven_source_parents != (GENERATION_ELEVEN_SOURCE_PARENT,) or (
            generation_eleven_source_paths
            != tuple(sorted(GENERATION_ELEVEN_SOURCE_COMMIT_PATHS))
        ):
            raise VerificationError("generation-eleven source topology or path scope changed")
        generation_eleven_receipt_parents, generation_eleven_receipt_paths = _git_commit_row(
            root, GENERATION_ELEVEN_RECEIPT_COMMIT
        )
        if generation_eleven_receipt_parents != (GENERATION_ELEVEN_SOURCE_COMMIT,) or (
            generation_eleven_receipt_paths != (RECEIPT_REL,)
        ):
            raise VerificationError("generation-eleven receipt topology or path scope changed")
        generation_eleven_state_parents, generation_eleven_state_paths = _git_commit_row(
            root, GENERATION_ELEVEN_STATE_COMMIT
        )
        if generation_eleven_state_parents != (GENERATION_ELEVEN_RECEIPT_COMMIT,) or (
            generation_eleven_state_paths != ("MISSION_STATE.json",)
        ):
            raise VerificationError("generation-eleven state topology or path scope changed")
        generation_eleven_baton_parents, generation_eleven_baton_paths = _git_commit_row(
            root, GENERATION_ELEVEN_BATON_COMMIT
        )
        if generation_eleven_baton_parents != (GENERATION_ELEVEN_STATE_COMMIT,) or (
            generation_eleven_baton_paths != ("CONTINUITY.md", "HANDOFF.md")
        ):
            raise VerificationError("generation-eleven baton topology or path scope changed")
        generation_twelve_source_parents, generation_twelve_source_paths = _git_commit_row(
            root, GENERATION_TWELVE_SOURCE_COMMIT
        )
        if generation_twelve_source_parents != (GENERATION_TWELVE_SOURCE_PARENT,) or (
            generation_twelve_source_paths
            != tuple(sorted(GENERATION_TWELVE_SOURCE_COMMIT_PATHS))
        ):
            raise VerificationError("generation-twelve source topology or path scope changed")
        generation_twelve_receipt_parents, generation_twelve_receipt_paths = _git_commit_row(
            root, GENERATION_TWELVE_RECEIPT_COMMIT
        )
        if generation_twelve_receipt_parents != (GENERATION_TWELVE_SOURCE_COMMIT,) or (
            generation_twelve_receipt_paths != (RECEIPT_REL,)
        ):
            raise VerificationError("generation-twelve receipt topology or path scope changed")
        generation_twelve_state_parents, generation_twelve_state_paths = _git_commit_row(
            root, GENERATION_TWELVE_STATE_COMMIT
        )
        if generation_twelve_state_parents != (GENERATION_TWELVE_RECEIPT_COMMIT,) or (
            generation_twelve_state_paths != ("MISSION_STATE.json",)
        ):
            raise VerificationError("generation-twelve state topology or path scope changed")
        generation_twelve_baton_parents, generation_twelve_baton_paths = _git_commit_row(
            root, GENERATION_TWELVE_BATON_COMMIT
        )
        if generation_twelve_baton_parents != (GENERATION_TWELVE_STATE_COMMIT,) or (
            generation_twelve_baton_paths != ("CONTINUITY.md", "HANDOFF.md")
        ):
            raise VerificationError("generation-twelve baton topology or path scope changed")

        generation_thirteen_source_parents, generation_thirteen_source_paths = _git_commit_row(
            root, GENERATION_THIRTEEN_SOURCE_COMMIT
        )
        if generation_thirteen_source_parents != (GENERATION_THIRTEEN_SOURCE_PARENT,) or (
            generation_thirteen_source_paths
            != tuple(sorted(GENERATION_THIRTEEN_SOURCE_COMMIT_PATHS))
        ):
            raise VerificationError("generation-thirteen source topology or path scope changed")
        generation_thirteen_receipt_parents, generation_thirteen_receipt_paths = _git_commit_row(
            root, GENERATION_THIRTEEN_RECEIPT_COMMIT
        )
        if generation_thirteen_receipt_parents != (GENERATION_THIRTEEN_SOURCE_COMMIT,) or (
            generation_thirteen_receipt_paths != (RECEIPT_REL,)
        ):
            raise VerificationError("generation-thirteen receipt topology or path scope changed")
        generation_thirteen_state_parents, generation_thirteen_state_paths = _git_commit_row(
            root, GENERATION_THIRTEEN_STATE_COMMIT
        )
        if generation_thirteen_state_parents != (GENERATION_THIRTEEN_RECEIPT_COMMIT,) or (
            generation_thirteen_state_paths != ("MISSION_STATE.json",)
        ):
            raise VerificationError("generation-thirteen state topology or path scope changed")
        generation_thirteen_baton_parents, generation_thirteen_baton_paths = _git_commit_row(
            root, GENERATION_THIRTEEN_BATON_COMMIT
        )
        if generation_thirteen_baton_parents != (GENERATION_THIRTEEN_STATE_COMMIT,) or (
            generation_thirteen_baton_paths != ("CONTINUITY.md", "HANDOFF.md")
        ):
            raise VerificationError("generation-thirteen baton topology or path scope changed")

        generation_fourteen_source_parents, generation_fourteen_source_paths = _git_commit_row(
            root, GENERATION_FOURTEEN_SOURCE_COMMIT
        )
        if generation_fourteen_source_parents != (GENERATION_FOURTEEN_SOURCE_PARENT,) or (
            generation_fourteen_source_paths
            != tuple(sorted(GENERATION_FOURTEEN_SOURCE_COMMIT_PATHS))
        ):
            raise VerificationError("generation-fourteen source topology or path scope changed")
        generation_fourteen_receipt_parents, generation_fourteen_receipt_paths = _git_commit_row(
            root, GENERATION_FOURTEEN_RECEIPT_COMMIT
        )
        if generation_fourteen_receipt_parents != (GENERATION_FOURTEEN_SOURCE_COMMIT,) or (
            generation_fourteen_receipt_paths != (RECEIPT_REL,)
        ):
            raise VerificationError("generation-fourteen receipt topology or path scope changed")
        generation_fourteen_state_parents, generation_fourteen_state_paths = _git_commit_row(
            root, GENERATION_FOURTEEN_STATE_COMMIT
        )
        if generation_fourteen_state_parents != (GENERATION_FOURTEEN_RECEIPT_COMMIT,) or (
            generation_fourteen_state_paths != ("MISSION_STATE.json",)
        ):
            raise VerificationError("generation-fourteen state topology or path scope changed")
        generation_fourteen_baton_parents, generation_fourteen_baton_paths = _git_commit_row(
            root, GENERATION_FOURTEEN_BATON_COMMIT
        )
        if generation_fourteen_baton_parents != (GENERATION_FOURTEEN_STATE_COMMIT,) or (
            generation_fourteen_baton_paths != ("CONTINUITY.md", "HANDOFF.md")
        ):
            raise VerificationError("generation-fourteen baton topology or path scope changed")

        generation_fifteen_source_parents, generation_fifteen_source_paths = _git_commit_row(
            root, GENERATION_FIFTEEN_SOURCE_COMMIT
        )
        if generation_fifteen_source_parents != (GENERATION_FIFTEEN_SOURCE_PARENT,) or (
            generation_fifteen_source_paths
            != tuple(sorted(GENERATION_FIFTEEN_SOURCE_COMMIT_PATHS))
        ):
            raise VerificationError("generation-fifteen source topology or path scope changed")
        generation_fifteen_receipt_parents, generation_fifteen_receipt_paths = _git_commit_row(
            root, GENERATION_FIFTEEN_RECEIPT_COMMIT
        )
        if generation_fifteen_receipt_parents != (GENERATION_FIFTEEN_SOURCE_COMMIT,) or (
            generation_fifteen_receipt_paths != (RECEIPT_REL,)
        ):
            raise VerificationError("generation-fifteen receipt topology or path scope changed")
        generation_fifteen_state_parents, generation_fifteen_state_paths = _git_commit_row(
            root, GENERATION_FIFTEEN_STATE_COMMIT
        )
        if generation_fifteen_state_parents != (GENERATION_FIFTEEN_RECEIPT_COMMIT,) or (
            generation_fifteen_state_paths != ("MISSION_STATE.json",)
        ):
            raise VerificationError("generation-fifteen state topology or path scope changed")
        generation_fifteen_baton_parents, generation_fifteen_baton_paths = _git_commit_row(
            root, GENERATION_FIFTEEN_BATON_COMMIT
        )
        if generation_fifteen_baton_parents != (GENERATION_FIFTEEN_STATE_COMMIT,) or (
            generation_fifteen_baton_paths != ("CONTINUITY.md", "HANDOFF.md")
        ):
            raise VerificationError("generation-fifteen baton topology or path scope changed")

        receipt_parents, receipt_paths = _git_commit_row(root, receipt_commit)
        if receipt_parents != (source_commit,) or receipt_paths != (RECEIPT_REL,):
            raise VerificationError(
                "generation-sixteen receipt is not the exact receipt-only child"
            )

        receipt_path = root / RECEIPT_REL
        current_receipt_bytes = _read_stable_regular_file(receipt_path)
        if _git_file_bytes(root, receipt_commit, RECEIPT_REL) != current_receipt_bytes:
            raise VerificationError(
                "canonical receipt bytes differ from generation-sixteen receipt commit bytes"
            )
        committed_receipt = _parse_receipt_json(current_receipt_bytes)
        if committed_receipt != dict(receipt):
            raise VerificationError("supplied receipt differs from the committed canonical receipt")
        if _git_file_bytes(root, source_commit, "MISSION_STATE.json") != _git_file_bytes(
            root,
            GENERATION_FIFTEEN_BATON_COMMIT,
            "MISSION_STATE.json",
        ):
            raise VerificationError("generation-sixteen source changed the accepted B15 state")
        if _git_file_bytes(
            root,
            GENERATION_SIXTEEN_SOURCE_COMMIT,
            "MISSION_STATE.json",
        ) != _git_file_bytes(
            root,
            GENERATION_FIFTEEN_BATON_COMMIT,
            "MISSION_STATE.json",
        ):
            raise VerificationError("F16 lifecycle-control source changed the accepted B15 state")

        current_git = git_probe(root, inventory.tested_files)
        if current_git.dirty_entries or current_git.porcelain_sha256 != empty_status:
            raise VerificationError("current repository is dirty")
        if not _valid_commit(current_git.upstream_head):
            raise VerificationError("origin/master commit is malformed or missing")
        if not ancestry_probe(root, receipt_commit, current_git.head):
            raise VerificationError("generation-sixteen receipt is not an ancestor of current HEAD")

        chain = _linear_publication_chain(root, receipt_commit, current_git.head)
        if len(chain) > 3:
            raise VerificationError(
                "generation-sixteen has commits beyond exact T16, B16, "
                "and the single documentation tranche"
            )
        if chain:
            state_commit, state_paths = chain[0]
            if state_paths != ("MISSION_STATE.json",):
                raise VerificationError("T16 is not the exact state-only commit")
            state = _parse_receipt_json(
                _git_file_bytes(root, state_commit, "MISSION_STATE.json")
            )
            if not _exact_json_value(state, _expected_ci_hardening_state(root)):
                raise VerificationError("T16 is not the exact CI_HARDENING_REQUIRED/UNKNOWN state")
        if len(chain) >= 2 and chain[1][1] != ("CONTINUITY.md", "HANDOFF.md"):
            raise VerificationError("B16 is not the exact documentation-only baton")
        if len(chain) == 3:
            # Exactly one pre-registered reviewed documentation tranche may follow B16.
            tranche_commit, tranche_paths = chain[2]
            if tranche_paths != tuple(
                sorted(DOCUMENTATION_CORRECTION_TRANCHE_COMMIT_PATHS)
            ):
                raise VerificationError(
                    "post-B16 commit is not the exact reviewed documentation tranche"
                )
            if _git_file_bytes(
                root, tranche_commit, "MISSION_STATE.json"
            ) != _git_file_bytes(root, chain[0][0], "MISSION_STATE.json"):
                raise VerificationError("documentation tranche changed the accepted T16 state")

        allowed_upstream = {receipt_commit}
        if not chain:
            allowed_upstream.add(source_commit)
        elif len(chain) == 2:
            allowed_upstream.add(chain[1][0])
        elif len(chain) == 3:
            allowed_upstream = {chain[1][0], chain[2][0]}
        if current_git.upstream_head not in allowed_upstream:
            raise VerificationError(
                "origin/master is not the exact published commit for this stage"
            )
        if current_git.upstream_head != source_commit and not ancestry_probe(
            root,
            receipt_commit,
            current_git.upstream_head,
        ):
            raise VerificationError("generation-sixteen receipt is not published on origin/master")
        if current_git.upstream_head != current_git.head and not ancestry_probe(
            root, current_git.upstream_head, current_git.head
        ):
            raise VerificationError("origin/master is not an ancestor of current HEAD")
    except Exception as exc:
        errors.append(f"published receipt structure invalid: {type(exc).__name__}: {exc}")
    return errors


def validate_receipt(
    receipt: Mapping[str, Any],
    repo_root: Path = REPO_ROOT,
    *,
    runner: Runner = default_runner,
    git_probe: GitProbe = default_git_probe,
    ancestry_probe: AncestryProbe = default_ancestry_probe,
    toolchain_resolver: ToolchainResolver = resolve_toolchain,
) -> list[str]:
    """Replay every generation-sixteen command and claim against current source bytes."""

    errors: list[str] = []
    if not isinstance(receipt, Mapping):
        return ["receipt root is not an object"]
    if set(receipt) != RECEIPT_FIELDS:
        errors.append("receipt root field set mismatch")
    if receipt.get("schema") != SCHEMA:
        errors.append("schema mismatch")
    if not _exact_json_value(
        receipt.get("publication"),
        EXPECTED_RECOVERY_PUBLICATION,
    ):
        errors.append("generation-sixteen publication block mismatch")
    if receipt.get("verdict") != OK_VERDICT:
        errors.append("receipt verdict is not green")
    problems = receipt.get("problems")
    if not isinstance(problems, list) or problems:
        errors.append("receipt contains problems or malformed problem list")
    if type(receipt.get("problem_count")) is not int or receipt.get("problem_count") != 0:
        errors.append("problem_count is not zero")
    errors.extend(_nested_receipt_shape_errors(receipt))

    payload = dict(receipt)
    claimed_payload_hash = payload.pop("receipt_payload_sha256", None)
    if claimed_payload_hash != _sha256_bytes(_canonical_json(payload)):
        errors.append("receipt payload digest mismatch")

    try:
        root = repo_root.resolve(strict=True)
        current_toolchain = toolchain_resolver()
        inventory = discover_inventory(root)
        if receipt.get("repository", {}).get("root") != str(root):
            errors.append("repository root mismatch")
        if receipt.get("inventory") != inventory.as_dict():
            errors.append("focused inventory mismatch")
        if receipt.get("inventory_sha256") != _inventory_digest(inventory):
            errors.append("inventory digest mismatch")
        if receipt.get("toolchain") != current_toolchain:
            errors.append("toolchain receipt mismatch")
        if receipt.get("environment_contract") != _sanitized_environment(current_toolchain):
            errors.append("sanitized environment contract mismatch")

        current = snapshot_files(root, inventory.tested_files)
        claimed_files = receipt.get("files")
        if not isinstance(claimed_files, Mapping):
            errors.append("file binding map malformed")
        else:
            claimed_content = {
                rel: {
                    "sha256": value.get("sha256") if isinstance(value, Mapping) else None,
                    "bytes": value.get("bytes") if isinstance(value, Mapping) else None,
                }
                for rel, value in claimed_files.items()
            }
            if claimed_content != _content_projection(current):
                errors.append("tested source content is stale or forged")
        if receipt.get("file_content_set_sha256") != _snapshot_digest(current):
            errors.append("file content-set digest mismatch")

        empty_status_sha256 = _sha256_bytes(b"")
        replay_git_start = git_probe(root, inventory.tested_files)
        replay_allowed = not replay_git_start.dirty_entries and (
            replay_git_start.porcelain_sha256 == empty_status_sha256
        )
        if not replay_allowed:
            errors.append("current repository is dirty before command replay")

        expected_commands = build_commands(inventory, current_toolchain)
        if receipt.get("command_contract") != [list(command) for command in expected_commands]:
            errors.append("command contract mismatch")
        command_records = receipt.get("commands")
        if not isinstance(command_records, list) or len(command_records) != len(expected_commands):
            errors.append("executed command set incomplete")
        else:
            for index, (record, expected) in enumerate(zip(command_records, expected_commands)):
                if not isinstance(record, Mapping):
                    errors.append(f"command_{index} record malformed")
                    continue
                if record.get("argv") != list(expected):
                    errors.append(f"command_{index} argv mismatch")
                if (
                    type(record.get("return_code")) is not int
                    or record.get("return_code") != 0
                ):
                    errors.append(f"command_{index} did not succeed")
                for stream in ("stdout", "stderr"):
                    digest = record.get(f"{stream}_sha256")
                    byte_count = record.get(f"{stream}_bytes")
                    if not isinstance(digest, str) or len(digest) != 64:
                        errors.append(f"command_{index} {stream} digest malformed")
                    elif any(char not in "0123456789abcdef" for char in digest):
                        errors.append(f"command_{index} {stream} digest malformed")
                    if not isinstance(byte_count, int) or isinstance(byte_count, bool) or byte_count < 0:
                        errors.append(f"command_{index} {stream} byte count malformed")

        # A receipt payload hash is an integrity check, not an authenticity primitive. Never trust
        # its recorded return codes as proof that the commands succeeded: independently execute the
        # exact frozen argv against the exact bound bytes. Stream hashes remain historical metadata
        # because pytest elapsed-time text and tool warnings are not deterministic across replays.
        for index, expected in enumerate(expected_commands if replay_allowed else ()):
            if discover_inventory(root) != inventory or snapshot_files(
                root, inventory.tested_files
            ) != current:
                errors.append(f"command_{index} pre-replay source drift")
                break
            if toolchain_resolver() != current_toolchain:
                errors.append(f"command_{index} pre-replay toolchain drift")
                break
            if git_probe(root, inventory.tested_files) != replay_git_start:
                errors.append(f"command_{index} pre-replay Git drift")
                break
            replay = _command_record(expected, runner, root)
            if replay["return_code"] != 0:
                errors.append(f"command_{index} independent replay failed")
            if discover_inventory(root) != inventory or snapshot_files(
                root, inventory.tested_files
            ) != current:
                errors.append(f"command_{index} post-replay source drift")
                break
            if git_probe(root, inventory.tested_files) != replay_git_start:
                errors.append(f"command_{index} post-replay Git drift")
                break
            if toolchain_resolver() != current_toolchain:
                errors.append(f"command_{index} post-replay toolchain drift")
                break

        repository = receipt.get("repository", {})
        git_start = repository.get("git_start")
        git_end = repository.get("git_end")
        if not isinstance(git_start, Mapping) or not isinstance(git_end, Mapping):
            errors.append("claimed Git provenance is malformed")
            claimed_head = ""
        else:
            claimed_head = git_end.get("head")
            if git_start != git_end:
                errors.append("claimed tested Git states differ")
            if git_start.get("head") != claimed_head:
                errors.append("claimed repository Git HEAD was not stable")
            for label, state in (("start", git_start), ("end", git_end)):
                if state.get("dirty_entries") != []:
                    errors.append(f"claimed repository was dirty at {label}")
                if state.get("porcelain_v1_z_sha256") != empty_status_sha256:
                    errors.append(f"claimed repository status digest was not empty at {label}")
                if state.get("branch") != "master":
                    errors.append(f"claimed source branch was not master at {label}")
                if state.get("upstream") != "origin/master":
                    errors.append(f"claimed source upstream was not origin/master at {label}")
                if state.get("upstream_head") != state.get("head"):
                    errors.append(f"claimed source commit was not pushed at {label}")
                if state.get("parents") != [RECOVERY_SOURCE_PARENT]:
                    errors.append(f"claimed source parent mismatch at {label}")
                if state.get("commit_paths") != sorted(RECOVERY_SOURCE_COMMIT_PATHS):
                    errors.append(f"claimed source commit scope mismatch at {label}")
            if not isinstance(claimed_head, str) or len(claimed_head) != 40 or any(
                char not in "0123456789abcdef" for char in claimed_head
            ):
                errors.append("claimed tested Git HEAD is malformed")
                claimed_head = ""

        current_git = git_probe(root, inventory.tested_files)
        if current_git != replay_git_start:
            errors.append("repository Git state changed during command replay")
        if current_git.dirty_entries or current_git.porcelain_sha256 != empty_status_sha256:
            errors.append("current repository is dirty")
        current_head_valid = len(current_git.head) == 40 and all(
            char in "0123456789abcdef" for char in current_git.head
        )
        if not current_head_valid:
            errors.append("current Git HEAD is malformed")
        elif (
            claimed_head
            and claimed_head != current_git.head
            and not ancestry_probe(root, claimed_head, current_git.head)
        ):
            errors.append("claimed tested Git HEAD is not an ancestor of current HEAD")
        if current_git.branch != "master":
            errors.append("current branch is not master")
        if current_git.upstream != "origin/master":
            errors.append("current upstream is not origin/master")
        if current_git.upstream_head not in {claimed_head, current_git.head}:
            errors.append("current receipt commit is neither exact pre-push nor pushed topology")
        if claimed_head and claimed_head != current_git.head:
            if current_git.parents != (claimed_head,):
                errors.append("receipt commit is not the direct child of the source commit")
            if current_git.commit_paths != (RECEIPT_REL,):
                errors.append("receipt commit changed paths beyond the canonical receipt")
        if repository.get("git_head_stable") is not True:
            errors.append("Git HEAD was not stable")
        if repository.get("git_state_stable") is not True:
            errors.append("Git publication state was not stable")
        if repository.get("repository_clean_state_stable") is not True:
            errors.append("repository clean state was not stable")
    except Exception as exc:
        errors.append(f"validation probe failed: {type(exc).__name__}: {exc}")

    timing = receipt.get("timing")
    if not isinstance(timing, Mapping):
        errors.append("timing block malformed")
    else:
        for key in ("wall_duration_ns", "monotonic_duration_ns"):
            value = timing.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                errors.append(f"{key} malformed")
    return errors


def write_json_atomic(output: Path, payload: Mapping[str, Any]) -> None:
    """Durably replace OUTPUT with canonical JSON, never following an output symlink."""

    output = output.absolute()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.is_symlink():
        raise VerificationError(f"refusing symlink receipt output: {output}")
    encoded = json.dumps(
        payload,
        sort_keys=True,
        indent=2,
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8") + b"\n"
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
        directory_fd = os.open(output.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists():
            temporary.unlink()


def run_and_write_verification(
    output: Path = DEFAULT_RECEIPT,
    repo_root: Path = REPO_ROOT,
    **kwargs: Any,
) -> dict[str, Any]:
    output_abs = output.absolute()
    try:
        output_rel = output_abs.relative_to(repo_root.resolve(strict=True)).as_posix()
    except ValueError:
        output_rel = None
    if output_rel is not None and output_rel != RECEIPT_REL:
        raise VerificationError("in-repository receipt output must use the canonical receipt path")
    receipt = run_verification(repo_root, **kwargs)
    write_json_atomic(output_abs, receipt)
    return receipt


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--verify-receipt",
        type=Path,
        help="validate an existing green receipt against current files instead of running tools",
    )
    modes.add_argument(
        "--bind-next-source",
        metavar="COMMIT",
        help="bind one direct-child candidate from an externally accepted B16 worktree",
    )
    modes.add_argument(
        "--verify-next-source-binding",
        type=Path,
        metavar="RECEIPT",
        help="independently replay a retained next-source binding receipt",
    )
    parser.add_argument("--accepted-baton-commit")
    parser.add_argument("--accepted-tooling-receipt-sha256")
    parser.add_argument("--next-source-output", type=Path)
    parser.add_argument("--expected-candidate-commit")
    parser.add_argument("--expected-binding-sha256")
    return parser.parse_args(argv)


def _best_effort_cli_stderr(line: str) -> None:
    """Emit one flushed machine verdict without allowing stderr failure to change its exit code."""

    try:
        print(line, file=sys.stderr, flush=True)
    except BaseException:
        pass


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    detached_values = (
        args.accepted_baton_commit,
        args.accepted_tooling_receipt_sha256,
        args.next_source_output,
        args.expected_candidate_commit,
        args.expected_binding_sha256,
    )
    if args.bind_next_source is not None:
        wrong_envelope = (
            args.output is not None
            or args.expected_candidate_commit is not None
            or args.expected_binding_sha256 is not None
        )
    elif args.verify_next_source_binding is not None:
        wrong_envelope = args.output is not None or args.next_source_output is not None
    elif args.verify_receipt is not None:
        wrong_envelope = args.output is not None or any(
            value is not None for value in detached_values
        )
    else:
        wrong_envelope = any(value is not None for value in detached_values)
    if wrong_envelope:
        _best_effort_cli_stderr(f"{FAIL_VERDICT}: ArgumentEnvelopeError")
        return 2

    if args.bind_next_source is not None:
        required = (
            args.accepted_baton_commit,
            args.accepted_tooling_receipt_sha256,
            args.next_source_output,
        )
        if any(value is None for value in required):
            _best_effort_cli_stderr(f"{FAIL_VERDICT}: NextSourceArgumentError")
            return 2
        try:
            digest, byte_count, receipt = publish_next_source_binding(
                args.next_source_output,
                accepted_baton_commit=args.accepted_baton_commit,
                accepted_tooling_receipt_sha256=args.accepted_tooling_receipt_sha256,
                candidate_commit=args.bind_next_source,
            )
        except NextSourceBindingCommittedError:
            _best_effort_cli_stderr(NEXT_SOURCE_COMMITTED_POSTCONDITION_VERDICT)
            return 3
        except NextSourceBindingIndeterminateError:
            _best_effort_cli_stderr(NEXT_SOURCE_COMMIT_STATE_INDETERMINATE_VERDICT)
            return 4
        except Exception as exc:
            _best_effort_cli_stderr(f"{FAIL_VERDICT}: {type(exc).__name__}")
            return 2
        except BaseException:
            _best_effort_cli_stderr(NEXT_SOURCE_COMMIT_STATE_INDETERMINATE_VERDICT)
            return 4
        try:
            print(f"receipt_sha256={digest}")
            print(f"receipt_bytes={byte_count}")
            print(f"candidate_commit={receipt['candidate']['commit']}")
            print(f"candidate_tree={receipt['candidate']['tree']}")
            print(NEXT_SOURCE_OK_VERDICT, flush=True)
        except BaseException:
            _best_effort_cli_stderr(NEXT_SOURCE_COMMITTED_POSTCONDITION_VERDICT)
            return 3
        return 0

    if args.verify_next_source_binding is not None:
        required = (
            args.accepted_baton_commit,
            args.accepted_tooling_receipt_sha256,
            args.expected_candidate_commit,
            args.expected_binding_sha256,
        )
        if any(value is None for value in required):
            print(f"{FAIL_VERDICT}: NextSourceArgumentError", file=sys.stderr)
            return 2
        try:
            _require_isolated_binding_interpreter()
            raw_receipt = _read_stable_regular_file_bounded(
                args.verify_next_source_binding, NEXT_SOURCE_MAX_RECEIPT_BYTES
            )
            errors = validate_next_source_binding(
                raw_receipt,
                expected_baton_commit=args.accepted_baton_commit,
                expected_tooling_receipt_sha256=args.accepted_tooling_receipt_sha256,
                expected_candidate_commit=args.expected_candidate_commit,
                expected_receipt_sha256=args.expected_binding_sha256,
            )
        except Exception as exc:
            errors = [f"next-source receipt read failed: {type(exc).__name__}"]
        print(NEXT_SOURCE_OK_VERDICT if not errors else FAIL_VERDICT)
        if errors:
            print(f"problem_count={len(errors)}")
        return 0 if not errors else 2

    if args.verify_receipt is not None:
        try:
            receipt = _parse_receipt_json(args.verify_receipt.read_bytes())
            errors = validate_receipt(receipt)
        except Exception as exc:
            errors = [f"receipt read failed: {type(exc).__name__}"]
        print(OK_VERDICT if not errors else FAIL_VERDICT)
        if errors:
            print(f"problem_count={len(errors)}")
        return 0 if not errors else 2

    output = args.output if args.output is not None else DEFAULT_RECEIPT
    try:
        receipt = run_and_write_verification(output)
    except Exception as exc:
        print(f"{FAIL_VERDICT}: {type(exc).__name__}", file=sys.stderr)
        return 2
    print(receipt["verdict"])
    print(f"problem_count={receipt['problem_count']}")
    print(f"receipt={output.absolute()}")
    return 0 if receipt["verdict"] == OK_VERDICT else 2


if __name__ == "__main__":
    raise SystemExit(main())
