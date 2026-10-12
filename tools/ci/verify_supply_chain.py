#!/usr/bin/env python3
"""Replay the exact repository-local inputs of Sentinel's Gen17 CI candidate.

This verifier is deliberately narrower than a hermetic-build or provenance system. It binds the
exact workflow, requirement input, resolved hash locks, verifier, and hostile test bytes; enforces
the frozen critical workflow shape; strict-decodes a canonical manifest; and refuses drift.

An honestly executed green result establishes only that these repository-local inputs and
structural rules match the committed manifest. It does not authenticate upstream actions or
packages, freeze the hosted runner, Python patch release, pip implementation, package index, or
network, reproduce a lock solve, retain an offline wheel mirror, produce an SBOM, or establish
SLSA/hermeticity/readiness.

Usage:
    python3 -I -B -S tools/ci/verify_supply_chain.py
    python3 -I -B -S tools/ci/verify_supply_chain.py --write
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
AGENTS_REL = "AGENTS.md"
WORKFLOW_REL = ".github/workflows/ci.yml"
MANIFEST_REL = "tools/ci/supply-chain-manifest.json"
MANIFEST = ROOT / MANIFEST_REL
REQUIREMENTS_INPUT_REL = "tools/ci/requirements-ci.in"
VERIFIER_REL = "tools/ci/verify_supply_chain.py"
KNOWN_BADS_REL = "tests/test_iter135_gen17_ci_hardening.py"
PYTEST_LAUNCHER_REL = "tools/ci/run_pytest_isolated.py"
INSTALL_VERIFIER_REL = "tools/ci/verify_ci_install.py"
INSTALL_KNOWN_BADS_REL = "tests/test_iter135_ci_install_verifier.py"
LAUNCHER_KNOWN_BADS_REL = "tests/test_iter135_launcher.py"
PYPROJECT_REL = "pyproject.toml"
LOCKS = {
    "3.10": "tools/ci/requirements-ci-py310.lock",
    "3.11": "tools/ci/requirements-ci-py311.lock",
}
# Frozen execution/editorial source copies are evidence, not maintained modules.
# Exact paths are excluded from Ruff and individually byte-bound here before lint.
ARCHIVED_SOURCE_FILES = (
    "docs/editorial/2026-10-11/render_diagrams.py",
    "docs/editorial/2026-10-11/validate_review.py",
    "experiments/iter136_hugsim_recoverability_canary/proof/diagnose_simulator_import.py",
    "experiments/iter136_hugsim_recoverability_canary/proof/inspect_runtime_1.py",
    "experiments/iter136_hugsim_recoverability_canary/proof/inspect_runtime_2.py",
    "experiments/iter136_hugsim_recoverability_canary/proof/inspect_runtime_3.py",
    "experiments/iter137_controller_execution_contract/proof/benchmark_launch.py",
    "experiments/iter137_controller_execution_contract/proof/benchmark_progress_1.py",
    "experiments/iter137_controller_execution_contract/proof/host_postflight.py",
    "experiments/iter137_controller_execution_contract/proof/host_preflight_ready.py",
    "experiments/iter137_controller_execution_contract/proof/host_preflight_v2.py",
    "experiments/iter145_constrained_execution/proof/gpu_raw/e2e145.py",
    "experiments/iter145_constrained_execution/proof/resume_loader_source/caching__df_cache.py",
    "experiments/iter145_constrained_execution/proof/resume_loader_source/data_structures__scene.py",
    "experiments/iter145_constrained_execution/proof/resume_loader_source/dataset.py",
    "experiments/iter145_constrained_execution/proof/resume_loader_source/dataset_specific__nusc__nusc_dataset.py",
    "experiments/iter145_constrained_execution/proof/resume_loader_source/maps__map_api.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_deploy_inventory.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_diagnose_replay.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_hostops.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_init.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_packet.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_packet_v2.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_packet_v3.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_packet_v4.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_pause.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_preflight.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_preflight_retry1.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_price.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_run.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_start.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_stop.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_verify_pause.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_watchdog.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_analyze.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_close_docs.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_collect.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_deploy.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_launch.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_mount_preflight.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_ops.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_packet.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_patch_preflight.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_preflight.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_progress.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_start.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_verify_close.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_watchdog.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145r_deploy_inventory.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145r_inspect.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145r_inspect_ready.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145r_inspect_selected.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145r_maps_deploy.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145r_ops.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145r_preflight.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145r_preflight_retry.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145r_start.py",
    "experiments/iter145_constrained_execution/proof/session_tools/i145r_watchdog.py",
    "experiments/iter145_constrained_execution/proof/session_tools/sentinel_i145_commit.py",
    "experiments/iter146_route_outcome_contract/proof/gpu_raw/brake_t0/e2e146.py",
    "experiments/iter146_route_outcome_contract/proof/gpu_raw/brake_t2_5/e2e146.py",
    "experiments/iter146_route_outcome_contract/proof/gpu_raw/monitor/e2e146.py",
    "experiments/iter146_route_outcome_contract/proof/gpu_raw/nominal/e2e146.py",
    "experiments/iter146_route_outcome_contract/proof/session_tools/commit.py",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146_final_audit.py",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146_legacy_gpu_replay.py",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146_update_docs.py",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146_write_close.py",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_aggregate.py",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_analyze_pair.py",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_collect.py",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_deploy.py",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_launch_pair.py",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_ops.py",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_packet.py",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_preflight.py",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_progress.py",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_start.py",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_watchdog.py",
    "experiments/iter146_route_outcome_contract/proof/session_tools/price.py",
    "experiments/iter146_route_outcome_contract/proof/session_tools/run.py",
    "experiments/iter147_full_horizon_execution/proof/gpu_raw/pair_000/e2e147.py",
    "experiments/iter147_full_horizon_execution/proof/gpu_raw/pair_001/e2e147.py",
    "experiments/iter147_full_horizon_execution/proof/gpu_raw/pair_002/e2e147.py",
    "experiments/iter147_full_horizon_execution/proof/gpu_raw/pair_003/e2e147.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/commit.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/cpu_analysis.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147_close.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147_final_audit.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147_metrics.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147_prepare.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147_price.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147_update_docs.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147_write_results.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_aggregate.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_analyze_pair.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_budget.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_collect.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_deploy.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_launch_pair.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_ops.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_packet.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_preflight.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_progress.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_start.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_supervise.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_watchdog.py",
    "experiments/iter147_full_horizon_execution/proof/session_tools/run.py",
    "experiments/iter148_recovery_study/proof/session_tools/commit.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148_docs.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148_final_audit.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148_finish_local.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148_packet_check.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148_prefix_replay.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148_prepare.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148_prepare_forensic.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148_price.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148_update_docs.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_active_docs.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_aggregate.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_analyze_pair.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_budget.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_close.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_collect.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_complete_deployment.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_completion_known_bads.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_deploy.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_final_audit.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_final_docs.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_launch_pair.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_ops.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_packet.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_preflight.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_price.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_progress.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_start.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_supervise.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_watchdog.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148f_budget.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148f_collect.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148f_ops.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148f_preflight.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148f_start.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148f_watchdog.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_analyze_pair.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_budget.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_collect.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_deploy.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_launch_pair.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_ops.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_packet.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_preflight.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_progress.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_start.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_supervise.py",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_watchdog.py",
    "experiments/iter148_recovery_study/proof/session_tools/run.py",
    "experiments/iter148_recovery_study/proof/study_raw/pair_000/e2e147.py",
    "experiments/iter148_recovery_study/proof/study_raw/pair_001/e2e147.py",
    "experiments/iter148_recovery_study/proof/study_raw/pair_002/e2e147.py",
    "experiments/iter151_recovery_canary/proof/study_raw/pair_000/e2e147.py",
    "experiments/iter152_recovery_continuation/proof/study_raw/pair_000/e2e147.py",
    "experiments/iter152_recovery_continuation/proof/study_raw/pair_001/e2e147.py",
    "experiments/iter152_recovery_continuation/proof/study_raw/pair_002/e2e147.py",
    "experiments/iter152_recovery_continuation/proof/study_raw/pair_003/e2e147.py",
    "experiments/iter152_recovery_continuation/proof/study_raw/pair_004/e2e147.py",
    "experiments/iter152_recovery_continuation/proof/study_raw/pair_005/e2e147.py",
    "experiments/iter152_recovery_continuation/proof/study_raw/pair_006/e2e147.py",
)
BOUND_FILES = (
    *ARCHIVED_SOURCE_FILES,
    AGENTS_REL,
    WORKFLOW_REL,
    REQUIREMENTS_INPUT_REL,
    LOCKS["3.10"],
    LOCKS["3.11"],
    VERIFIER_REL,
    KNOWN_BADS_REL,
    PYTEST_LAUNCHER_REL,
    INSTALL_VERIFIER_REL,
    INSTALL_KNOWN_BADS_REL,
    LAUNCHER_KNOWN_BADS_REL,
    PYPROJECT_REL,
)

SCHEMA = "sentinel.ci_input_manifest.v2"
CLAIM = (
    "exact identities of enumerated repository-local Gen17 controls and frozen critical "
    "workflow shape replay"
)
LIMITATIONS = (
    "no upstream action or package authenticity claim",
    "GitHub-hosted runner image, Python patch, pip, index, and network are not content-addressed",
    "hash-locked install is not an offline wheel mirror or rebuild proof",
    "lock solving is not claimed deterministic or reproducible from requirements-ci.in",
    "co-edited inputs and manifest require an independently accepted commit/receipt identity",
    "no hermeticity, SBOM, SLSA, product-readiness, launch-authority, or scientific claim",
    "enumerated controls are not whole-tree identity; that requires the accepted source commit",
)

EXPECTED_ACTIONS = (
    ("actions/checkout", "11d5960a326750d5838078e36cf38b85af677262"),
    ("actions/setup-python", "a26af69be951a213d495a4c3e4e4022e16d87065"),
)
EXPECTED_RUNNER = "ubuntu-latest"
EXPECTED_MATRIX = (
    ("3.10", LOCKS["3.10"]),
    ("3.11", LOCKS["3.11"]),
)
EXPECTED_RUN_COMMANDS = (
    "python3 -I -B -S tools/ci/verify_supply_chain.py",
    'test -n "${RUNNER_TEMP:-}" && test -d "${RUNNER_TEMP}" && test ! -L '
    '"${RUNNER_TEMP}" && test ! -e "${RUNNER_TEMP}/sentinel-ci-'
    '${{ matrix.python-version }}" && python -I -B -m venv '
    '"${RUNNER_TEMP}/sentinel-ci-${{ matrix.python-version }}"',
    'test ! -e "${RUNNER_TEMP}/sentinel-ci-install-${{ matrix.python-version }}.json" && '
    '"${RUNNER_TEMP}/sentinel-ci-${{ matrix.python-version }}/bin/python" -I -B -m pip '
    "--isolated --disable-pip-version-check install --no-input --force-reinstall "
    "--require-hashes --only-binary=':all:' --no-deps --report "
    '"${RUNNER_TEMP}/sentinel-ci-install-${{ matrix.python-version }}.json" '
    "-r ${{ matrix.lock }}",
    'command "${RUNNER_TEMP}/sentinel-ci-${{ matrix.python-version }}/bin/python" -I -B '
    "-m pip --isolated --disable-pip-version-check check",
    'command "${RUNNER_TEMP}/sentinel-ci-${{ matrix.python-version }}/bin/python" -I -B '
    "-S tools/ci/verify_ci_install.py --python-minor "
    '"${{ matrix.python-version }}" --lock "${{ matrix.lock }}" --report '
    '"${RUNNER_TEMP}/sentinel-ci-install-${{ matrix.python-version }}.json"',
    'command "${RUNNER_TEMP}/sentinel-ci-${{ matrix.python-version }}/bin/ruff" check .',
    "env -u PYTHONHOME -u PYTHONOPTIMIZE -u PYTEST_ADDOPTS -u PYTEST_PLUGINS "
    "PYTHONPATH= PYTHONHASHSEED=0 PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "
    '"${RUNNER_TEMP}/sentinel-ci-${{ matrix.python-version }}/bin/python" -B -S '
    "tools/ci/run_pytest_isolated.py -q "
    "-c pyproject.toml --noconftest --strict-config --strict-markers "
    "tests/test_iter135_gen17_ci_hardening.py tests/test_iter135_ci_install_verifier.py",
    "env -u PYTHONHOME -u PYTHONOPTIMIZE -u PYTEST_ADDOPTS -u PYTEST_PLUGINS "
    "PYTHONPATH= PYTHONHASHSEED=0 PYTHONNOUSERSITE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "
    '"${RUNNER_TEMP}/sentinel-ci-${{ matrix.python-version }}/bin/python" -B -S '
    "tools/ci/run_pytest_isolated.py -q "
    "-c pyproject.toml --noconftest --strict-config --strict-markers",
    'command "${RUNNER_TEMP}/sentinel-ci-${{ matrix.python-version }}/bin/python" -I -B -S '
    "-c 'import runpy,sys;"
    "sys.path.append(\"scripts\");"
    "runpy.run_path(\"scripts/validate_docs.py\",run_name=\"__main__\")'",
)
EXPECTED_STEP_SEQUENCE = (
    (
        "uses",
        "actions/checkout@11d5960a326750d5838078e36cf38b85af677262",
    ),
    ("run", EXPECTED_RUN_COMMANDS[0]),
    (
        "uses",
        "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
    ),
    *(("run", command) for command in EXPECTED_RUN_COMMANDS[1:]),
)
EXPECTED_STATIC_SHA256 = {
    "docs/editorial/2026-10-11/render_diagrams.py": "404a1221f1856fa6788f4e0c1ca5daf4872eab14b7af95e873cf202b333c05f4",
    "docs/editorial/2026-10-11/validate_review.py": "d7a86ce62f4864d75e9ecc7354ee6832745dd5d75a606b383cc4a7d26903fb3c",
    "experiments/iter136_hugsim_recoverability_canary/proof/diagnose_simulator_import.py": "e93ec05919adabc56864906eba91c11871abd7041df16e76734ce09262dc2e78",
    "experiments/iter136_hugsim_recoverability_canary/proof/inspect_runtime_1.py": "5e3ac97994ac4d0f76936e556b3ba97ed86971e507f1a48b60271b01f0b6f34a",
    "experiments/iter136_hugsim_recoverability_canary/proof/inspect_runtime_2.py": "066dc8c6c97ffe70cbfde92a51b09be537f1ea046460717398e7a9d4c54006d4",
    "experiments/iter136_hugsim_recoverability_canary/proof/inspect_runtime_3.py": "e933137b39d5f81aa88eb1c257f5e472119b988726a2eb33da1ed95f1cdd3533",
    "experiments/iter137_controller_execution_contract/proof/benchmark_launch.py": "7d59961e116aabf60bcb2eb7311d19fa0dadd04573781f59d365d0a5e51785a6",
    "experiments/iter137_controller_execution_contract/proof/benchmark_progress_1.py": "a561ee4a14f720cc037e2fb50a171b2abbf89a7071dca8379e7d837ce152b323",
    "experiments/iter137_controller_execution_contract/proof/host_postflight.py": "47f1fcb3142b7ec56250fc5fee942023c7cb298318a8e8b26120d66fc748f0a5",
    "experiments/iter137_controller_execution_contract/proof/host_preflight_ready.py": "23e2d253d7b9c38de39f3940fdfe0426f630075db5d193fca0e938e5039e183c",
    "experiments/iter137_controller_execution_contract/proof/host_preflight_v2.py": "23e2d253d7b9c38de39f3940fdfe0426f630075db5d193fca0e938e5039e183c",
    "experiments/iter145_constrained_execution/proof/gpu_raw/e2e145.py": "320d9079d1f506c76c5c60e29d43a03f8d65157ebc3bcf5e6022a8b3d935b0b7",
    "experiments/iter145_constrained_execution/proof/resume_loader_source/caching__df_cache.py": "cb25b9b73452a13751072ae90f551ad72bec93b857fccf7cec366ee94f6f6c8e",
    "experiments/iter145_constrained_execution/proof/resume_loader_source/data_structures__scene.py": "f831acd959e7836643192a46addec57775d24dd5e12f5d2ea9b4f5ef496f7401",
    "experiments/iter145_constrained_execution/proof/resume_loader_source/dataset.py": "7def8bfe55adc9f73f6646d82e7685bd2a9c12fb3985003d1055a7c1788c4b55",
    "experiments/iter145_constrained_execution/proof/resume_loader_source/dataset_specific__nusc__nusc_dataset.py": "9c462c192e996b4ba16bdf7391a59986c4e7d92bd7ccce454e4c3eb394154af3",
    "experiments/iter145_constrained_execution/proof/resume_loader_source/maps__map_api.py": "a0a502b0f7b8c0b54ba4b4fb0cc1e9b15db518298fb2c68e76a2060dfc4506b7",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_deploy_inventory.py": "211ee1896a2d0013a34bba963fd07fe98ffcfe3b8d2cadd3526591829dc117c5",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_diagnose_replay.py": "ba684e988b6d3ee328ba708e2543e2a4c8768a7542b818e146e2222ef6b20a54",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_hostops.py": "d546728857b64a159b55f03edf8c13524205cba80d7faff0f48bb60efde4f9de",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_init.py": "9b2b2cf53e57849b97a7e294d7f526f65eafc0ef1482435b422d1993193b0551",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_packet.py": "5e5230fa8afc86b26f890c945cc7af670be7b6b4ad9e75db0ae332b2170ad0ee",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_packet_v2.py": "17dc72c6638fda5bd4be3c9d2c98f80db5021a2a7d28ac3b8a4968ee8ac47d36",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_packet_v3.py": "2f486bd8041c120c2fd1fed8618bc874993bbb1c3de5710c17c3e0a82799992b",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_packet_v4.py": "6c7676bb3da682778a9784c409ddbadc3b623ba103a7e5144dcafdedb78110fa",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_pause.py": "281a98df89d1bbb0e40a2c0b59c3db41d2cd1de30a7e1f6887ea19f15ebf4ee5",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_preflight.py": "d5a66fa2269b59179cc89bde71a1681347125086717851960826cf20d518d4ba",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_preflight_retry1.py": "9d3f6daf0e8392366e6eda3996bc4827500a8aad276fe0de0edba7920430235c",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_price.py": "4d52c690dc2106a868f95736d195986b5a3a80a11e5b79ee02209ba356855757",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_run.py": "82313db56df90ff75b8d5d5065542558811516a7417b3f87520bce9512f1e2ba",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_start.py": "de038aa129a2b5dda608711fe082edb40336336139c4d082c683b9aa0e001da2",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_stop.py": "760846637db06cd6b8aee929a847410b2085de9b9f147aaed6271e7e1c94e7cb",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_verify_pause.py": "b4f658df0f204f6444b2ae1d776c52785e7c5a4e79117ab2106ada7131991d33",
    "experiments/iter145_constrained_execution/proof/session_tools/i145_watchdog.py": "d33e8a9112dce826cef97c636f8ff267b3d49b453ae3e7a6a0985fc4fd924e52",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_analyze.py": "8d7171fbc9a8f2ec73438ecfc05f98fac660296b21df9f742a94fdac02a85e98",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_close_docs.py": "40195b2e0c3620eb956be650feec28c31740f2ca89ab130346b3225dc6b747b3",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_collect.py": "20834ee01ee0b1b301980098eacc10cc2dfb256cc46d41693c6828d5734cdeee",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_deploy.py": "6fe1aa1610d74a878e529f22f8e3cc1add496d1a308eb3a3cafd7814cc8a755d",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_launch.py": "65d9af138451a4c080de12a7a4f5ec87976443c5facaaa63026ce376be89414d",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_mount_preflight.py": "35f9b2a98ac36a40ac0a6785b1aee4d4e1ebb29b9614999c22b0bcc67f103a01",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_ops.py": "4cd3c126dd01d7ebbb5e8197b93acbc482eba6af25cf682e173b6d950ae51162",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_packet.py": "afaf63359d60b5824e792cd45dc0c44713678745cbe8ab7095de089999e07f3d",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_patch_preflight.py": "ed7ee218b27b1dd55223249bd37c3f9acd7bdaa9fdad1af9de88fa1cb11f2471",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_preflight.py": "cade0c54b5bd16960e32783512aaef27a93dbb1140b6b6cc9c3032583869e793",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_progress.py": "7016d03aeda76fd2b1d35de4fec96df3a96e6720c0da21dd33e12c624dab2465",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_start.py": "7f4fb74261fd6545146410bc964bada3fc0fa4c803eb7d7acda6ad8d8f9eaff9",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_verify_close.py": "eb39978a4679501c191939109d8a56af1dfa719e1a9fbab2100fbec24c7a4447",
    "experiments/iter145_constrained_execution/proof/session_tools/i145g_watchdog.py": "3c6839e55ba6aa8553bd17ca4262f36bcd3458f17c4df8f1deae51718e00ad37",
    "experiments/iter145_constrained_execution/proof/session_tools/i145r_deploy_inventory.py": "e5965f50adca54627d0e7b4f856e0d4d6c6bb41ef6db93fa1aef0bcc0ed958ec",
    "experiments/iter145_constrained_execution/proof/session_tools/i145r_inspect.py": "47fd928de77210dafaeaf9f74924e441c7996425700cafd9513f54d7fa7faa97",
    "experiments/iter145_constrained_execution/proof/session_tools/i145r_inspect_ready.py": "e53abcc0bd4ea00f830dbbde98bf29aa7dcbc369b9db94b8d21a6fcdb5363fe4",
    "experiments/iter145_constrained_execution/proof/session_tools/i145r_inspect_selected.py": "908721b82591455140785a512c7b085e575bd24ddf5e59ae13ceebf6bef34b0c",
    "experiments/iter145_constrained_execution/proof/session_tools/i145r_maps_deploy.py": "315040a2dbbd4f5813d60ba7f5d438705a95eb441ced6b55634660b0e26e923d",
    "experiments/iter145_constrained_execution/proof/session_tools/i145r_ops.py": "a0d7b9eb8e5385a7df5b0a8cd50258089ee7698575af76dfe3792ed3656144f9",
    "experiments/iter145_constrained_execution/proof/session_tools/i145r_preflight.py": "2abf7602ed516d7d23c5e2aa2101afa1596fb39b93823120f4e138e0b96183aa",
    "experiments/iter145_constrained_execution/proof/session_tools/i145r_preflight_retry.py": "eaa1e45ea86d9ad24395e9c73dd560cdda420a186e8bb2c5f0f160d16e1ff3a8",
    "experiments/iter145_constrained_execution/proof/session_tools/i145r_start.py": "9582deb4dc721979649cf5f04d71dd9af79cc3e47a2f662f65983d7fb4a290e5",
    "experiments/iter145_constrained_execution/proof/session_tools/i145r_watchdog.py": "38e6df34ffb30e4b90a7ff98ad798682dae2ec14d67eca55747ae1ac6a39d86f",
    "experiments/iter145_constrained_execution/proof/session_tools/sentinel_i145_commit.py": "b5aead1677c828ba5774e8ae550ea9965cfe5482a54933ffd09c757af47683b3",
    "experiments/iter146_route_outcome_contract/proof/gpu_raw/brake_t0/e2e146.py": "dbb343436a1e2b6fcd8e132992504c38a8d0b07b74bff59f0a06d13ba3adb813",
    "experiments/iter146_route_outcome_contract/proof/gpu_raw/brake_t2_5/e2e146.py": "dbb343436a1e2b6fcd8e132992504c38a8d0b07b74bff59f0a06d13ba3adb813",
    "experiments/iter146_route_outcome_contract/proof/gpu_raw/monitor/e2e146.py": "dbb343436a1e2b6fcd8e132992504c38a8d0b07b74bff59f0a06d13ba3adb813",
    "experiments/iter146_route_outcome_contract/proof/gpu_raw/nominal/e2e146.py": "dbb343436a1e2b6fcd8e132992504c38a8d0b07b74bff59f0a06d13ba3adb813",
    "experiments/iter146_route_outcome_contract/proof/session_tools/commit.py": "355d52994003e14aefeb79134e76b32912105ff297678f62a90fadfa42691109",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146_final_audit.py": "b1b384b2ec4ee0cb15da539555f231e24bbfe867e0402820b602b12e29d3513d",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146_legacy_gpu_replay.py": "434fd699f9a0a7e00dd743ade6b5d451f25872391c48464566d2236f281bf221",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146_update_docs.py": "72f8d8ebc898e0981f04266ad54a7ae256890a5c488b0f7d6191ce26eef85be6",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146_write_close.py": "96e2c8b59597827e4a28f6f471076fc6d638d3103d90c7ea4a394aaa0289b31a",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_aggregate.py": "b13d45c6589545f1d427165e78c4ed75afd595c9f613ad0102c923fef2424a5c",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_analyze_pair.py": "0c1881de87d1d7c450706dd2c6fd0db921914597321255bfd9fb259221e47e76",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_collect.py": "8f605ab0afef8208b912905e33646cd581d71b7a68a8ad45e4de04b6af6c62b6",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_deploy.py": "8ffa9c00ddad3a0bdcba7743dcd256e135c3c8b6a1a73f8459b22eec3f991e5e",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_launch_pair.py": "14fd549bb73850577007c3d30c8a9dca13d20f8cd26ed5911988cb39b9a760a0",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_ops.py": "7883548ad2524148d0467e0639f3e2a4355154bfd16744e9d166e0cab0d4f90d",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_packet.py": "c0ed4b27159a7e7fc76320bb9dc8774ffbb51cbd33076300fe92d547c1a56721",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_preflight.py": "68fcda81b6a86580250aabd7ed4fb79ce59adf3f98379aee90e3eed41d0707c1",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_progress.py": "00870005aca2f6bb44f9f319810c4799e89400207ed0c00aafd954eea7092da2",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_start.py": "c39f55fe43911b6306436a2057a31355f659793d12bc5af81128eae16a440e47",
    "experiments/iter146_route_outcome_contract/proof/session_tools/i146g_watchdog.py": "46bb2f16dd807ebf43f380d8bf3ebf29719ee0a114e90be8d33b598b0f8259ce",
    "experiments/iter146_route_outcome_contract/proof/session_tools/price.py": "9a032673a834ed99ec92c22cb498bf2ad467833b22a0a2a2bbfa7157fd15893c",
    "experiments/iter146_route_outcome_contract/proof/session_tools/run.py": "d2849d521bf2471d39732b4836f57af2579fe178a376f4593a480102b66f1188",
    "experiments/iter147_full_horizon_execution/proof/gpu_raw/pair_000/e2e147.py": "fe2dfca899a5446bfa6fd7d762524cfe57a304ca08330a45dc9e267d50b3159d",
    "experiments/iter147_full_horizon_execution/proof/gpu_raw/pair_001/e2e147.py": "fe2dfca899a5446bfa6fd7d762524cfe57a304ca08330a45dc9e267d50b3159d",
    "experiments/iter147_full_horizon_execution/proof/gpu_raw/pair_002/e2e147.py": "fe2dfca899a5446bfa6fd7d762524cfe57a304ca08330a45dc9e267d50b3159d",
    "experiments/iter147_full_horizon_execution/proof/gpu_raw/pair_003/e2e147.py": "fe2dfca899a5446bfa6fd7d762524cfe57a304ca08330a45dc9e267d50b3159d",
    "experiments/iter147_full_horizon_execution/proof/session_tools/commit.py": "6f1c4f25014a7708a0ae61560e7667559848bf3788ad0a4ec0612f7eec320a79",
    "experiments/iter147_full_horizon_execution/proof/session_tools/cpu_analysis.py": "cf803807c6c88c5b00bfb68666619216a94366c9cb2cb8ad2ea997ab7960160f",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147_close.py": "0dce31139e77c2ff3fea4a4f78fe5c56e99599cb1c9d836f5c9815ca1399dff1",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147_final_audit.py": "869beb742b3015aa8e7d4abb556e587940d738998296982ed4fea89c2c0dd2d8",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147_metrics.py": "fadcd86af380db9fffb41b9dd91fc1307e1c3f65d5692b39b7d8eef9229acd2b",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147_prepare.py": "f8aeeaa5027dcbc09932d4db28614895d74157f772c0bccc33f94bc0021b215f",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147_price.py": "cbdcaf47f7164d46ff69ff48726846a42e6e04046b38d0bebfdcfe6cd987dbf5",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147_update_docs.py": "21099a5baa321407a44a0634b388e29c051604d3ce058a196cf144878811b01e",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147_write_results.py": "5945e55cf786ed0759f627f273ef4c8ccc8c2859dd78e1c7d190c98a26efc04b",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_aggregate.py": "7ac54dfb71948f529481dc89881e7c5a36aec954c268288af11028b8372be240",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_analyze_pair.py": "251d16e893d934d959e9d1df16247c6c1beb6cf998196ba832c5d966697b03a7",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_budget.py": "84394a0a96f8ef2a502501343771f58219cbd00be44fbf84ee71bffe246da470",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_collect.py": "22705ccbe6375d82ae5b357bbd4b0cadb28ba86af77ca16d5ae63a9b5c4c5cdf",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_deploy.py": "15960398d38584d9754d1eaa66f5352bd5bcd9dd17ee489af97c843fb353f9e3",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_launch_pair.py": "1ad05750a42674930e68124b9e3c47f041b571e2ae159ea726f191d1a16c8adb",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_ops.py": "08db203b69bd5811f561e8c57ed39040dac5a9e6c2f8eda85c8317d049a3acd6",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_packet.py": "fea3def33ff98ba49852e467daea7164ad8117bf3ed81f85574e4ecac0c87d86",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_preflight.py": "8c453c40e57508bba4c4fc819f09414879ee7af42778dc36cfcb846d50481ebd",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_progress.py": "f4cd5bd2ac6e5a134a30bf41b18cd10686125a6405b78f49439015d94afebc9e",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_start.py": "c287e40e9193f4ee689261a2f46d4473cb1bf8c75f0ba88c7ad15f9623223bbf",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_supervise.py": "b0d0dc36c09d749c7fba963d16bff9cb8f59ce84d96a377e4f40556fd39dc015",
    "experiments/iter147_full_horizon_execution/proof/session_tools/i147g_watchdog.py": "2004a8a41f724d648f2124af85f8982165d8a2e8662072c5309fede4d71f11bc",
    "experiments/iter147_full_horizon_execution/proof/session_tools/run.py": "ba71225fb8718bc1370fb2a5a4be7bab0a4b0f4623e2fdcfe5dfe64053754f67",
    "experiments/iter148_recovery_study/proof/session_tools/commit.py": "1d24c04d5e955bc74fb84bd8f6823d6c5c792129859ab03a18fae37338512820",
    "experiments/iter148_recovery_study/proof/session_tools/i148_docs.py": "6ef01309e99b0bd32a130f6ea09d81be6b46defe02021919e81d2fec93969f39",
    "experiments/iter148_recovery_study/proof/session_tools/i148_final_audit.py": "6e3a54c8d6a385486dc3096bc8115f52220d4bc762e0dcd81b907fe170d30ea1",
    "experiments/iter148_recovery_study/proof/session_tools/i148_finish_local.py": "c99a00fa1dfa7eb3cce5f7469cb65f88d3470c91e6dd3b0693dded702891264a",
    "experiments/iter148_recovery_study/proof/session_tools/i148_packet_check.py": "708147f49fb8ffb7799a82a0cd0b9f309504e0daa0f4618f3ed135887353441e",
    "experiments/iter148_recovery_study/proof/session_tools/i148_prefix_replay.py": "4da6e55123ad585cf43fd9aa327af9f5b2c01149db00631c616c247ca35801ef",
    "experiments/iter148_recovery_study/proof/session_tools/i148_prepare.py": "4485788e215a002790418670610ec1276c234c011978c61d217dc82f8fb63165",
    "experiments/iter148_recovery_study/proof/session_tools/i148_prepare_forensic.py": "39a7843c9929fb58a261be495b68e4cd0b7a26bb4db5edbc1d0ed42d1f6331d6",
    "experiments/iter148_recovery_study/proof/session_tools/i148_price.py": "494829181c2bb529da1f2a924b3ba738d9f9f875658530dfba464ca0bb769a25",
    "experiments/iter148_recovery_study/proof/session_tools/i148_update_docs.py": "4ef29e3f20fca7fe9816361a0e8afc51ebe12f3637458d1d0a7e68386b4bd59c",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_active_docs.py": "267bb7ed729a11f47f918f3a78a2e2c660a29a3505426be04732d6deb9655408",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_aggregate.py": "7a97acd1cc42f113773dbd20e9f9a8159e463bd32602a16344f5975fd3df851f",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_analyze_pair.py": "223919203faaab2c8f90a02db43ae68a8552f7f85a1965f57f09758f77b50c20",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_budget.py": "ec2e4fe5feeb1b62b3fc7f09d88dd47f60cdf7363703ad1e0c136f69f04147eb",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_close.py": "52b78f4677a2a246ffa90713a574a7e3a8a3048322e21ba8473cddf7319f1830",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_collect.py": "20a86d8ee8a141271ebfc90adc5b5e0641986253b9e7312da6da9a588452e389",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_complete_deployment.py": "c84eecf7d7cfcae03fc332d97b990128429d54e34ebeb24fbbd9a9c8e55e6663",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_completion_known_bads.py": "a05d0e5ddff8afee08230543522ad1af8e6f867515a3db267cebe7669be47945",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_deploy.py": "c01bd7707e7b75c90ebcc0207d37638089144b5bed716626147ae72630ce484c",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_final_audit.py": "40e80f9e7180fd8caea1d9841eebabce826807307541deec88ff39039cc483ff",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_final_docs.py": "ae88da9943840b1224b739b98c82b13c856710c4bbcbdecaebfc7f1496ce6822",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_launch_pair.py": "1e71004edea00c2b9bc382b074856251d6f03f08bddea9925618a20f266c6e0b",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_ops.py": "93c69e3f1c11f2ee2988160d825127931c3ec850e827b4bc9229a76d3c08c406",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_packet.py": "f1e621326ec6aebd30e51d99661e56625dbfc2de630652e24f8dd7a09634b181",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_preflight.py": "6472832d5e263ece881aac0592cd5cfa3bd63f36e8e021b6b1001aa526049b24",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_price.py": "d7efccaa1128af0e2614535d0c7c9b60aaee98b6a846d2cf2ddf3c4c15d1e553",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_progress.py": "ec2a9d294bdd357c2ee6c8caae533c6d506fa4ea55cd97990dd53ce222c59b80",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_start.py": "142b7377e6e1cb512c0ab4059adbad61260e41924e3889b0a4131ec07a819bf7",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_supervise.py": "6f87957e5e0e2d36382473e2aa6efacd0c3e6f954a59f86b95e9eb95b5c89f8a",
    "experiments/iter148_recovery_study/proof/session_tools/i148a_watchdog.py": "9580190879b267ce31c06a3c92a4ea94f00741f7e7f10dac8d58f4809c162e47",
    "experiments/iter148_recovery_study/proof/session_tools/i148f_budget.py": "78789a1d334e558d2dad531367db9aeaad8750a9acb6e73c8aa9c36dd3194815",
    "experiments/iter148_recovery_study/proof/session_tools/i148f_collect.py": "59e816aeb626cf5eda64643de62a5a72be96a482ab432331886b513802483730",
    "experiments/iter148_recovery_study/proof/session_tools/i148f_ops.py": "b49893475eb5648b042372ca69b105b83db0564926d273b3e3d378909b74edc6",
    "experiments/iter148_recovery_study/proof/session_tools/i148f_preflight.py": "ee765e0a23a5a954bc8ef0b6569086db1868bec1af1914da5f3abf48b63c1653",
    "experiments/iter148_recovery_study/proof/session_tools/i148f_start.py": "2b2d1d29eb5e3036671d040208e956c63b11b993f9cf62e96dc16dc46446570e",
    "experiments/iter148_recovery_study/proof/session_tools/i148f_watchdog.py": "908bef387cafef8211f42180fb06b4f4e10b8bea922229d73d5fd329212649cf",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_analyze_pair.py": "aaa3135da6c625d4bef1db0bdb2ac88752e8d656506a64d81d0e46fbfee43c8b",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_budget.py": "138a64e9bfe7b851eb6c91e49fcd045e0368368e171d8950c11d784c852b73bc",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_collect.py": "3c77bd6f1b26cd13dc37b3ea8eb2c4ed8809536a1987d020d86d507df3c94608",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_deploy.py": "2091e1f1f1946cbb29a265bda5bcfb818df72d2f7dcc059ad0575663639c90d4",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_launch_pair.py": "4ba5153f741a1bc7a74fba1af0cc8673607f329515bb854515dfa3ac7ee3c129",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_ops.py": "0a810afbaf027edeae0dfd5df2b4037891ec215f2d655ae2ce56165d7ebb6af3",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_packet.py": "62cbd24c1a1a98814421f957ac3074473753f67018e170ce2dcf932e70c84916",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_preflight.py": "891e9e3d8c519dba8c208e2df59929fdd668d89a90cf15b0690a972b7fe1bbf6",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_progress.py": "d0f3847f3c62b74fc4c8dbc5d6f00e5a5e8bd1b2f1725bda70eede65d71fb8b7",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_start.py": "cedfdc91e43cfab6a96a78302e4821d6fc0da385eca107aad4b61081fc494210",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_supervise.py": "0b690cec0a6284579d916f3afc57d8a01246972a6f2296c1fc0adf02eec2f856",
    "experiments/iter148_recovery_study/proof/session_tools/i148g_watchdog.py": "042e82075d148b0db9d8092c4b96e1bbc69ed8e0238195707c5036fd7000cb3c",
    "experiments/iter148_recovery_study/proof/session_tools/run.py": "9f7de79d7949c80330353fdde6841498a48c7249917d465f97d0c3e2427b017b",
    "experiments/iter148_recovery_study/proof/study_raw/pair_000/e2e147.py": "fe2dfca899a5446bfa6fd7d762524cfe57a304ca08330a45dc9e267d50b3159d",
    "experiments/iter148_recovery_study/proof/study_raw/pair_001/e2e147.py": "fe2dfca899a5446bfa6fd7d762524cfe57a304ca08330a45dc9e267d50b3159d",
    "experiments/iter148_recovery_study/proof/study_raw/pair_002/e2e147.py": "fe2dfca899a5446bfa6fd7d762524cfe57a304ca08330a45dc9e267d50b3159d",
    "experiments/iter151_recovery_canary/proof/study_raw/pair_000/e2e147.py": "fe2dfca899a5446bfa6fd7d762524cfe57a304ca08330a45dc9e267d50b3159d",
    "experiments/iter152_recovery_continuation/proof/study_raw/pair_000/e2e147.py": "fe2dfca899a5446bfa6fd7d762524cfe57a304ca08330a45dc9e267d50b3159d",
    "experiments/iter152_recovery_continuation/proof/study_raw/pair_001/e2e147.py": "fe2dfca899a5446bfa6fd7d762524cfe57a304ca08330a45dc9e267d50b3159d",
    "experiments/iter152_recovery_continuation/proof/study_raw/pair_002/e2e147.py": "fe2dfca899a5446bfa6fd7d762524cfe57a304ca08330a45dc9e267d50b3159d",
    "experiments/iter152_recovery_continuation/proof/study_raw/pair_003/e2e147.py": "fe2dfca899a5446bfa6fd7d762524cfe57a304ca08330a45dc9e267d50b3159d",
    "experiments/iter152_recovery_continuation/proof/study_raw/pair_004/e2e147.py": "fe2dfca899a5446bfa6fd7d762524cfe57a304ca08330a45dc9e267d50b3159d",
    "experiments/iter152_recovery_continuation/proof/study_raw/pair_005/e2e147.py": "fe2dfca899a5446bfa6fd7d762524cfe57a304ca08330a45dc9e267d50b3159d",
    "experiments/iter152_recovery_continuation/proof/study_raw/pair_006/e2e147.py": "fe2dfca899a5446bfa6fd7d762524cfe57a304ca08330a45dc9e267d50b3159d",

    AGENTS_REL: "9dd96d223327384d77760671396b8075a5a57bc1396abdcff5a12095055add69",
    WORKFLOW_REL: "09c7fb25eff2429aa9474ca9b4a4d0fdeb88efc3ff3d0cdb92c760bbdcd535d8",
    REQUIREMENTS_INPUT_REL: "127ffdf390bc2edf16056b8cfbfad341d9a97c03d659a5f61ab8b63f17d7f35e",
    LOCKS["3.10"]: "81a5eb85355f335b6384e3a98f650486a8782c62d17f70cef124f712e1ed079d",
    LOCKS["3.11"]: "2d00841c6d0fb64fc89054a055819f66fbb53cb8870fa421a3a62165984c2e00",
    PYPROJECT_REL: "ca3c6f5a3427b419e86139ebf49bbdfe57c8ab84ee30913f59057bffe069dbcf",
}
EXPECTED_REQUIREMENTS_INPUT = (
    "ruff==0.15.20",
    "pytest==9.1.1",
    'numpy==2.2.6 ; python_version == "3.10"',
    'numpy==2.4.6 ; python_version == "3.11"',
    'scikit-learn==1.7.2 ; python_version == "3.10"',
    'scikit-learn==1.9.0 ; python_version == "3.11"',
    "torch==2.10.0+cpu",
    "shapely==2.1.2",
    "PyYAML==6.0.3",
)
EXPECTED_DIRECT_PACKAGES = {
    "3.10": {
        "numpy": "2.2.6",
        "pytest": "9.1.1",
        "ruff": "0.15.20",
        "scikit-learn": "1.7.2",
        "torch": "2.10.0+cpu",
        "shapely": "2.1.2",
        "pyyaml": "6.0.3",
    },
    "3.11": {
        "numpy": "2.4.6",
        "pytest": "9.1.1",
        "ruff": "0.15.20",
        "scikit-learn": "1.9.0",
        "torch": "2.10.0+cpu",
        "shapely": "2.1.2",
        "pyyaml": "6.0.3",
    },
}

MAX_BOUND_FILE_BYTES = 4 * 1024 * 1024
MAX_MANIFEST_BYTES = 512 * 1024
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_USES_LINE = re.compile(
    r"^\s*-\s+uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([^\s#]+)(?:\s+#.*)?$"
)
_RUN_LINE = re.compile(r"^\s*-\s+run:\s*(.*?)\s*$")
_RUNNER_LINE = re.compile(r"^\s*runs-on:\s*([^\s#]+)\s*$")
_MATRIX_PYTHON_LINE = re.compile(r'^\s*-\s+python-version:\s*"([^"]+)"\s*$')
_MATRIX_LOCK_LINE = re.compile(r"^\s+lock:\s*([^\s#]+)\s*$")
_PLAIN_WORKFLOW_MAPPING_LINE = re.compile(
    r"^ *(?:- )?[A-Za-z][A-Za-z0-9_-]*:(?: .*)?$"
)
_FORBIDDEN_WORKFLOW_CONTROL_LINE = re.compile(
    r'''^\s*(?:-\s*)?["']?(?:if|continue-on-error|concurrency|container|defaults|needs|services)'''
    r'''["']?\s*:'''
)
_REQUIREMENT_START = re.compile(
    r"^([A-Za-z0-9][A-Za-z0-9_.-]*)==([^\s;\\]+)\s+\\$"
)
_HASH_TOKEN = re.compile(
    r"^    --hash=sha256:([0-9a-f]{64})(?:\s+\\)?$", re.MULTILINE
)


class SupplyChainError(ValueError):
    """A CI input or manifest is absent, unsafe, malformed, or outside the frozen contract."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(document: object) -> bytes:
    return (
        json.dumps(document, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"
    ).encode("ascii")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SupplyChainError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise SupplyChainError(f"non-finite JSON number: {value}")


def _exact_json_value(observed: object, expected: object) -> bool:
    if type(observed) is not type(expected):
        return False
    if type(expected) is dict:
        observed_dict = observed
        expected_dict = expected
        return set(observed_dict) == set(expected_dict) and all(
            _exact_json_value(observed_dict[key], expected_dict[key]) for key in expected_dict
        )
    if type(expected) is list:
        observed_list = observed
        expected_list = expected
        return len(observed_list) == len(expected_list) and all(
            _exact_json_value(left, right)
            for left, right in zip(observed_list, expected_list, strict=True)
        )
    return observed == expected


def _read_regular_file(root: Path, relative: str, maximum: int) -> bytes:
    path = root / relative
    try:
        before = path.lstat()
    except OSError as exc:
        raise SupplyChainError(f"file cannot be stated: {relative}:{type(exc).__name__}") from exc
    if not stat.S_ISREG(before.st_mode):
        raise SupplyChainError(f"file is not a physical regular file: {relative}")
    if before.st_size < 0 or before.st_size > maximum:
        raise SupplyChainError(f"file exceeds byte bound: {relative}")
    try:
        payload = path.read_bytes()
        after = path.lstat()
    except OSError as exc:
        raise SupplyChainError(f"file cannot be read: {relative}:{type(exc).__name__}") from exc
    identity_before = (before.st_dev, before.st_ino, before.st_mode, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns)
    if identity_before != identity_after or len(payload) != after.st_size:
        raise SupplyChainError(f"file changed while read: {relative}")
    return payload


def _decode_utf8(payload: bytes, relative: str) -> str:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SupplyChainError(f"file is not UTF-8: {relative}") from exc
    if not text.endswith("\n") or "\r" in text or "\x00" in text:
        raise SupplyChainError(f"file text framing is noncanonical: {relative}")
    return text


def _parse_workflow(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    if sum(line == "on: [push, pull_request]" for line in lines) != 1:
        raise SupplyChainError("workflow trigger is not exact push/pull_request")

    actions: list[tuple[str, str]] = []
    commands: list[str] = []
    runners: list[str] = []
    matrix: list[tuple[str, str]] = []
    steps: list[tuple[str, str]] = []
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        if _FORBIDDEN_WORKFLOW_CONTROL_LINE.match(line):
            raise SupplyChainError("workflow contains a forbidden control key")
        if _PLAIN_WORKFLOW_MAPPING_LINE.fullmatch(line) is None:
            raise SupplyChainError("workflow contains noncanonical mapping-key syntax")
        if "uses:" in line:
            match = _USES_LINE.fullmatch(line)
            if match is None:
                raise SupplyChainError("workflow contains an unparseable action use")
            actions.append((match.group(1), match.group(2)))
            steps.append(("uses", f"{match.group(1)}@{match.group(2)}"))
        if "run:" in line:
            match = _RUN_LINE.fullmatch(line)
            if match is None or not match.group(1):
                raise SupplyChainError("workflow contains an unparseable run step")
            commands.append(match.group(1))
            steps.append(("run", match.group(1)))
        if "runs-on:" in line:
            match = _RUNNER_LINE.fullmatch(line)
            if match is None:
                raise SupplyChainError("workflow contains an unparseable runner")
            runners.append(match.group(1))
        python_match = _MATRIX_PYTHON_LINE.fullmatch(line)
        if python_match is not None:
            if index + 1 >= len(lines):
                raise SupplyChainError("workflow matrix row lacks a lock")
            lock_match = _MATRIX_LOCK_LINE.fullmatch(lines[index + 1])
            if lock_match is None:
                raise SupplyChainError("workflow matrix lock row is malformed")
            matrix.append((python_match.group(1), lock_match.group(1)))

    if tuple(actions) != EXPECTED_ACTIONS:
        raise SupplyChainError("workflow action inventory/order/ref differs from frozen contract")
    if any(not _SHA40.fullmatch(ref) for _owner, ref in actions):
        raise SupplyChainError("workflow action ref is not lowercase 40-hex")
    if runners != [EXPECTED_RUNNER]:
        raise SupplyChainError("workflow runner differs from frozen contract")
    if tuple(matrix) != EXPECTED_MATRIX:
        raise SupplyChainError("workflow Python/lock matrix differs from frozen contract")
    if tuple(commands) != EXPECTED_RUN_COMMANDS:
        raise SupplyChainError("workflow run-step inventory/order differs from frozen contract")
    if tuple(steps) != EXPECTED_STEP_SEQUENCE:
        raise SupplyChainError("workflow action/run interleaving differs from frozen contract")
    if text.count("python-version: ${{ matrix.python-version }}") != 1:
        raise SupplyChainError("setup-python matrix binding differs from frozen contract")
    return {
        "triggers": ["push", "pull_request"],
        "runner": EXPECTED_RUNNER,
        "actions": [
            {"owner_repo": owner_repo, "ref": ref} for owner_repo, ref in actions
        ],
        "python_lock_matrix": [
            {"python": version, "lock": lock} for version, lock in matrix
        ],
        "run_commands": commands,
        "steps": [{"kind": kind, "value": value} for kind, value in steps],
    }


def _parse_requirements_input(text: str) -> list[str]:
    rows = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]
    if tuple(rows) != EXPECTED_REQUIREMENTS_INPUT:
        raise SupplyChainError("requirements input differs from frozen exact direct constraints")
    return rows


def _normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _parse_lock(text: str, version: str) -> list[dict[str, Any]]:
    # One exact upstream CPU wheel listing, only at the start. All package
    # versions and wheel SHA-256 allowlists remain mandatory. Other options fail.
    cpu_source = "--find-links https://download.pytorch.org/whl/cpu/torch/\n"
    if cpu_source in text and not text.startswith(cpu_source):
        raise SupplyChainError("lock contains an unrecognized preamble")
    if text.startswith(cpu_source):
        text = text[len(cpu_source):]
    lines = text.splitlines()
    starts: list[tuple[int, re.Match[str]]] = []
    for index, line in enumerate(lines):
        if not line or line.startswith(("#", " ", "\t")):
            continue
        match = _REQUIREMENT_START.fullmatch(line)
        if match is None:
            raise SupplyChainError(f"lock {version} contains an unpinned or malformed row")
        starts.append((index, match))
    if not starts:
        raise SupplyChainError(f"lock {version} contains no requirements")
    for preamble_line in lines[: starts[0][0]]:
        if preamble_line and not preamble_line.startswith("#"):
            raise SupplyChainError(f"lock {version} contains an unrecognized preamble")

    packages: dict[str, dict[str, Any]] = {}
    for ordinal, (start, match) in enumerate(starts):
        end = starts[ordinal + 1][0] if ordinal + 1 < len(starts) else len(lines)
        block = "\n".join(lines[start:end])
        for continuation in lines[start + 1 : end]:
            if (
                not continuation
                or continuation.startswith("    #")
                or _HASH_TOKEN.fullmatch(continuation) is not None
            ):
                continue
            raise SupplyChainError(f"lock {version} contains an unrecognized continuation")
        hashes = _HASH_TOKEN.findall(block)
        if not hashes or block.count("--hash=") != len(hashes):
            raise SupplyChainError(f"lock {version} requirement lacks exact SHA-256 hashes")
        if len(hashes) != len(set(hashes)) or any(not _SHA256.fullmatch(item) for item in hashes):
            raise SupplyChainError(f"lock {version} contains duplicate or malformed hashes")
        name = _normalize_name(match.group(1))
        if name in packages:
            raise SupplyChainError(f"lock {version} contains duplicate package: {name}")
        packages[name] = {
            "version": match.group(2),
            "hash_count": len(hashes),
        }

    direct = EXPECTED_DIRECT_PACKAGES[version]
    if any(
        name not in packages or packages[name]["version"] != expected
        for name, expected in direct.items()
    ):
        raise SupplyChainError(f"lock {version} direct package versions differ")
    return [{"name": name, **packages[name]} for name in sorted(packages)]


def derive(root: Path) -> dict[str, Any]:
    """Derive the complete frozen Gen17 CI-input projection from repository bytes."""

    root = root.resolve(strict=True)
    payloads = {
        relative: _read_regular_file(root, relative, MAX_BOUND_FILE_BYTES)
        for relative in BOUND_FILES
    }
    for relative, expected_sha256 in EXPECTED_STATIC_SHA256.items():
        if _sha256_bytes(payloads[relative]) != expected_sha256:
            raise SupplyChainError(f"frozen static input digest differs: {relative}")
    workflow = _parse_workflow(_decode_utf8(payloads[WORKFLOW_REL], WORKFLOW_REL))
    requirements_input = _parse_requirements_input(
        _decode_utf8(payloads[REQUIREMENTS_INPUT_REL], REQUIREMENTS_INPUT_REL)
    )
    locks: dict[str, Any] = {}
    for version, relative in LOCKS.items():
        locks[version] = {
            "path": relative,
            "sha256": _sha256_bytes(payloads[relative]),
            "packages": _parse_lock(_decode_utf8(payloads[relative], relative), version),
        }
    return {
        "schema": SCHEMA,
        "claim": CLAIM,
        "limitations": list(LIMITATIONS),
        "files": {
            relative: {
                "bytes": len(payloads[relative]),
                "sha256": _sha256_bytes(payloads[relative]),
            }
            for relative in sorted(payloads)
        },
        "requirements_input": requirements_input,
        "workflow": workflow,
        "locks": locks,
    }


def _load_manifest(root: Path) -> dict[str, Any]:
    raw = _read_regular_file(root, MANIFEST_REL, MAX_MANIFEST_BYTES)
    try:
        document = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeDecodeError, ValueError, SupplyChainError) as exc:
        raise SupplyChainError(f"manifest strict decode failed: {exc}") from exc
    if type(document) is not dict:
        raise SupplyChainError("manifest root is not an exact object")
    if raw != _canonical(document):
        raise SupplyChainError("manifest bytes are not canonical JSON")
    return document


def verify(root: Path) -> list[str]:
    """Return stable problems; an empty list means exact repository-local replay."""

    try:
        derived = derive(root)
    except (OSError, SupplyChainError) as exc:
        return [f"supply_chain:derive:{exc}"]
    try:
        committed = _load_manifest(root.resolve(strict=True))
    except (OSError, SupplyChainError) as exc:
        return [f"supply_chain:manifest:{exc}"]
    if not _exact_json_value(committed, derived):
        return ["supply_chain:manifest_drift"]
    return []


def _write_manifest(document: dict[str, Any]) -> None:
    payload = _canonical(document)
    staging = MANIFEST.with_name(f".{MANIFEST.name}.tmp-{os.getpid()}")
    descriptor: int | None = None
    try:
        descriptor = os.open(staging, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = None
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(staging, MANIFEST)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            staging.unlink()
        except FileNotFoundError:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the canonical derived manifest")
    args = parser.parse_args(argv)

    if args.write:
        try:
            document = derive(ROOT)
            _write_manifest(document)
        except (OSError, SupplyChainError) as exc:
            print(f"SUPPLY_CHAIN_MANIFEST_WRITE_FAILED: {exc}", file=sys.stderr)
            return 1
        print(f"wrote {MANIFEST_REL}")
        return 0

    problems = verify(ROOT)
    if problems:
        print("SUPPLY_CHAIN_VERIFICATION_FAILED", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    print("SUPPLY_CHAIN_VERIFICATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
