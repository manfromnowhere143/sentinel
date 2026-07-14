#!/usr/bin/env python3
"""Iteration 128 support-core source-pool and mutation-operator preflight."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ITER126_VERDICT = "SUPPORT_CORE_CANDIDATE_MANIFEST_PREFLIGHT_COMPLETE"
ITER127_VERDICT = "POST_ITER126_MISSION_ALIGNMENT_AUDIT_COMPLETE"
COMPLETE_VERDICT = "SUPPORT_CORE_SOURCE_POOL_MUTATION_PREFLIGHT_COMPLETE"
INFRA_NULL_VERDICT = "SUPPORT_CORE_SOURCE_POOL_MUTATION_PREFLIGHT_INFRA_NULL"
EXPECTED_CANDIDATE_COUNT = 10
EXPECTED_ARCHETYPE_COUNT = 5
EXPECTED_OPERATOR_COUNT = 8
EXPECTED_ROLES = {"branch_stress": 5, "counterfactual_control": 5}
ITER126_REPORT_PATH = Path(
    "experiments/iter126_support_core_candidate_manifest_preflight/proof-manifest/"
    "support_core_candidate_manifest_report.json"
)
ITER126_RESULT_PATH = Path("experiments/iter126_support_core_candidate_manifest_preflight/RESULT.md")
ITER126_NOTE_PATH = Path(
    "docs/research/SUPPORT_CORE_CANDIDATE_GENERATION_MANIFEST_2026-07-14.md"
)
ITER127_RESULT_PATH = Path("experiments/iter127_post_iter126_mission_alignment_audit/RESULT.md")
ITER127_NOTE_PATH = Path(
    "docs/research/SENTINEL_POST_ITER126_MISSION_ALIGNMENT_AUDIT_2026-07-14.md"
)
SOURCE_POOL_NOTE_PATH = Path(
    "docs/research/SUPPORT_CORE_SOURCE_POOL_MUTATION_PREFLIGHT_2026-07-14.md"
)
DEFAULT_PROOF_DIR = Path("experiments/iter128_support_core_source_pool_mutation_preflight/proof-preflight")
DEFAULT_REPORT_PATH = DEFAULT_PROOF_DIR / "support_core_source_pool_mutation_preflight_report.json"
DEFAULT_MARKDOWN_PATH = DEFAULT_PROOF_DIR / "support_core_source_pool_mutation_preflight.md"
DEFAULT_COMMAND_PATH = DEFAULT_PROOF_DIR / "generate_support_core_source_pool_mutation_preflight.command.txt"
BOUNDARY = (
    "source-pool and mutation-operator preflight only; no scenario-generation execution, "
    "generated scenario artifact, execution-slot selection, GPU launch, HUGSIM run, "
    "learning/update step, repair, actor-causality, threshold-value, transfer upgrade, safety, "
    "deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world "
    "behavior, first-responder behavior, acquisition-value, retuning, production, commercial "
    "claim, or frontier-stack equivalence claim"
)
FORBIDDEN_CLAIMS = (
    "scenario-generation execution",
    "generated scenario artifact",
    "execution-slot selection",
    "GPU launch",
    "HUGSIM run",
    "learning/update step",
    "repair",
    "actor-causality",
    "threshold-value",
    "transfer upgrade",
    "safety",
    "deployment",
    "robustness",
    "benchmark",
    "population-rate",
    "HD-Score-invariance",
    "real-world behavior",
    "first-responder behavior",
    "acquisition-value",
    "retuning",
    "production",
    "commercial claim",
    "frontier-stack equivalence claim",
)
BOUNDARY_NEEDLES = (
    "scenario generation",
    "HUGSIM run",
    "GPU",
    "retuning",
    "repair",
    "safety",
    "deployment",
    "production",
    "commercial claim",
)
REQUIRED_CANDIDATE_FIELDS = (
    "candidate_id",
    "archetype_id",
    "candidate_role",
    "mutation_family",
    "source_slot_ids",
    "source_scenarios",
    "timing_gap_class",
    "selected_rank_condition",
    "candidate_generation_knobs",
    "required_gates",
)
ITER126_FALSE_AUTHORIZATION_FIELDS = (
    "execution_authorized",
    "gpu_authorized",
    "hugsim_run_authorized",
    "scenario_generation_authorized",
    "metric_change_authorized",
    "threshold_change_authorized",
    "planner_code_change_authorized",
    "runtime_code_change_authorized",
)
PREFLIGHT_FALSE_AUTHORIZATION_FIELDS = ITER126_FALSE_AUTHORIZATION_FIELDS + (
    "generated_artifact_authorized",
    "execution_slot_selection_authorized",
    "learning_update_authorized",
    "repair_authorized",
    "safety_claim_authorized",
    "deployment_authorized",
    "production_authorized",
    "commercial_claim_authorized",
)
FORBIDDEN_KEYS = (
    "generated_scenario_path",
    "generated_scenario_paths",
    "generated_artifact_path",
    "generated_artifact_paths",
    "launch_command",
    "launcher_command",
    "hugsim_command",
    "raw_log_path",
    "raw_log_paths",
    "gpu_path",
    "output_directory",
    "output_directories",
    "execution_slot_id",
    "execution_slot_selection",
)
ALLOWED_SOURCE_FIELDS = (
    "candidate_id",
    "archetype_id",
    "candidate_role",
    "mutation_family",
    "source_slot_ids",
    "source_scenarios",
    "support_side_branch",
    "selected_side_branch",
    "selected_rank_condition",
    "timing_gap_class",
    "support_gap_range_s",
)


OPERATOR_LIBRARY: dict[str, dict[str, list[str] | str]] = {
    "unsupported_nearest_reference_pressure": {
        "operator_kind": "branch_stress_no_support_reference",
        "allowed_controls": [
            "symbolically preserve no-pre-fire-support reference pressure",
            "symbolically preserve selected-nearest condition",
            "record future checks for selected object outside actor-support band",
        ],
    },
    "introduce_pre_fire_support_reference_control": {
        "operator_kind": "counterfactual_pre_fire_support_reference",
        "allowed_controls": [
            "symbolically define paired pre-fire support reference control",
            "preserve source candidate and scenario identity",
            "record future checks for support continuity before first fire",
        ],
    },
    "post_fire_support_delay_pressure": {
        "operator_kind": "branch_stress_post_fire_delay",
        "allowed_controls": [
            "symbolically preserve post-fire support timing pressure",
            "preserve selected-nearest condition",
            "record future checks for support evidence after first fire",
        ],
    },
    "shift_post_fire_evidence_to_pre_fire_control": {
        "operator_kind": "counterfactual_post_to_pre_fire_shift",
        "allowed_controls": [
            "symbolically define paired pre-fire evidence timing control",
            "preserve active-surface pressure",
            "record future checks for support evidence before first fire",
        ],
    },
    "support_drift_outside_band_sweep": {
        "operator_kind": "branch_stress_support_drift_sweep",
        "allowed_controls": [
            "symbolically preserve support drift outside the actor-support band",
            "preserve selected-not-nearest competition",
            "record future checks for support-band distance margin",
        ],
    },
    "support_band_border_continuity_control": {
        "operator_kind": "counterfactual_support_band_border_control",
        "allowed_controls": [
            "symbolically define paired support-band border continuity control",
            "preserve source slot identity",
            "record future checks for support continuity at the frozen band",
        ],
    },
    "support_loss_gap_sweep": {
        "operator_kind": "branch_stress_support_loss_gap_sweep",
        "allowed_controls": [
            "symbolically preserve measured last-support-to-fire gap pressure",
            "preserve selected rank condition from source candidate",
            "record future checks for last-presence and last-support gaps",
        ],
    },
    "same_object_visibility_continuity_control": {
        "operator_kind": "counterfactual_same_object_visibility_control",
        "allowed_controls": [
            "symbolically define paired same-object visibility continuity control",
            "preserve active-surface pressure",
            "record future checks for same-object support through first fire",
        ],
    },
}


def load_json(path: Path, label: str) -> tuple[dict[str, Any], list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-or-empty:{label}:{path}"]
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"read-json-failed:{label}:{path}:{exc}"]
    if not isinstance(data, dict):
        return {}, [f"json-not-dict:{label}:{path}"]
    return data, []


def load_text(path: Path, label: str) -> tuple[str, list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return "", [f"missing-or-empty:{label}:{path}"]
    try:
        return path.read_text(), []
    except OSError as exc:
        return "", [f"read-text-failed:{label}:{path}:{exc}"]


def normalize(text: str) -> str:
    return " ".join(text.split())


def slug(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return text or "missing"


def require_contains(problems: list[str], label: str, text: str, needle: str) -> None:
    if normalize(needle) not in normalize(text):
        problems.append(f"{label}-missing:{needle}")


def require_boundary(problems: list[str], label: str, text: str) -> None:
    for needle in BOUNDARY_NEEDLES:
        require_contains(problems, label, text, needle)


def validate_candidates(candidates_in: Any, problems: list[str]) -> list[dict[str, Any]]:
    if not isinstance(candidates_in, list):
        problems.append("iter126-candidates-not-list")
        return []
    candidates: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, candidate in enumerate(candidates_in, start=1):
        if not isinstance(candidate, dict):
            problems.append(f"iter126-candidate-not-dict:{index}")
            continue
        candidate_id = candidate.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id:
            problems.append(f"iter126-candidate-id-missing:{index}")
        elif candidate_id in seen_ids:
            problems.append(f"iter126-duplicate-candidate:{candidate_id}")
        else:
            seen_ids.add(candidate_id)
        for field in REQUIRED_CANDIDATE_FIELDS:
            value = candidate.get(field)
            if value in (None, "", [], {}):
                problems.append(f"iter126-candidate-missing-{field}:{candidate_id or index}")
        for field in ("source_slot_ids", "source_scenarios", "candidate_generation_knobs", "required_gates"):
            if not isinstance(candidate.get(field), list):
                problems.append(f"iter126-candidate-{field}-not-list:{candidate_id or index}")
        for field in ITER126_FALSE_AUTHORIZATION_FIELDS:
            if candidate.get(field) is not False:
                problems.append(f"iter126-candidate-auth-not-false:{candidate_id or index}:{field}")
        candidates.append(candidate)
    return sorted(candidates, key=lambda item: str(item.get("candidate_id")))


def false_authorizations() -> dict[str, bool]:
    return {field: False for field in PREFLIGHT_FALSE_AUTHORIZATION_FIELDS}


def source_pool_id(index: int, candidate: dict[str, Any]) -> str:
    return f"scsp_{index:03d}_{slug(str(candidate['candidate_id']))}"


def operator_id(mutation_family: str) -> str:
    return f"scop_{slug(mutation_family)}"


def binding_id(index: int, candidate: dict[str, Any]) -> str:
    return f"scbind_{index:03d}_{slug(str(candidate['candidate_id']))}"


def build_source_pool(index: int, candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_pool_id": source_pool_id(index, candidate),
        "candidate_id": candidate["candidate_id"],
        "archetype_id": candidate["archetype_id"],
        "candidate_role": candidate["candidate_role"],
        "mutation_family": candidate["mutation_family"],
        "source_pool_kind": "committed_iteration_126_manifest_metadata_only",
        "selection_key": "candidate_id+slot_id",
        "duplicate_handling_rule": "preserve_duplicate_scenarios_by_source_slot_id",
        "source_slot_ids": [str(slot) for slot in candidate.get("source_slot_ids", [])],
        "source_scenarios": [str(scenario) for scenario in candidate.get("source_scenarios", [])],
        "allowed_source_fields": list(ALLOWED_SOURCE_FIELDS),
        "source_constraints": [
            "read committed iteration-126 manifest metadata only",
            "preserve source slot identities before any generation step",
            "preserve duplicate scenario groups by slot_id, not scenario name",
            "require a later HYPOTHESIS.md before generated artifacts or execution slots exist",
        ],
        "forbidden_claims": list(FORBIDDEN_CLAIMS),
        **false_authorizations(),
    }


def operator_invariants() -> list[str]:
    return [
        "thresholds remain frozen",
        "HUGSIM metrics remain frozen",
        "planner code remains frozen",
        "runtime monitor code remains frozen",
        "candidate_id and source_slot_id provenance remain primary keys",
        "result remains pre-generation unless a later HYPOTHESIS.md authorizes generation",
    ]


def operator_prohibited_actions() -> list[str]:
    return [
        "scenario generation",
        "generated artifact creation",
        "execution slot selection",
        "GPU launch",
        "HUGSIM run",
        "threshold retuning",
        "metric alteration",
        "planner-code alteration",
        "runtime-code alteration",
        "learning or monitor update",
        "repair/safety/deployment/production/commercial claim",
    ]


def operator_checks() -> list[str]:
    return [
        "fresh HYPOTHESIS.md exists for any future generation successor",
        "source-pool IDs and candidate IDs are frozen before generating artifacts",
        "mutation operators are selected from the iteration-128 operator library",
        "destination naming is defined before any generated artifact can exist",
        "duplicate handling remains keyed by candidate_id and source_slot_id",
        "claim boundary is copied into the future successor result",
    ]


def build_operator(mutation_family: str) -> dict[str, Any]:
    spec = OPERATOR_LIBRARY[mutation_family]
    return {
        "operator_id": operator_id(mutation_family),
        "mutation_family": mutation_family,
        "operator_kind": spec["operator_kind"],
        "allowed_controls": list(spec["allowed_controls"]),
        "invariants": operator_invariants(),
        "prohibited_actions": operator_prohibited_actions(),
        "required_pre_generation_checks": operator_checks(),
        "forbidden_claims": list(FORBIDDEN_CLAIMS),
        **false_authorizations(),
    }


def build_binding(index: int, candidate: dict[str, Any], pool: dict[str, Any]) -> dict[str, Any]:
    mutation_family = str(candidate["mutation_family"])
    return {
        "binding_id": binding_id(index, candidate),
        "candidate_id": candidate["candidate_id"],
        "source_pool_id": pool["source_pool_id"],
        "operator_id": operator_id(mutation_family),
        "mutation_family": mutation_family,
        "binding_kind": "symbolic_pre_generation_binding",
        "binding_constraints": [
            "one source pool per committed candidate",
            "one mutation operator per committed mutation family",
            "one candidate-to-operator binding per committed candidate",
            "no generated artifact or execution slot is created by this binding",
        ],
        **false_authorizations(),
    }


def build_preflight(
    candidates: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    source_pools = [build_source_pool(index, candidate) for index, candidate in enumerate(candidates, start=1)]
    mutation_families = sorted({str(candidate.get("mutation_family")) for candidate in candidates})
    unknown_families = sorted(family for family in mutation_families if family not in OPERATOR_LIBRARY)
    for family in unknown_families:
        problems.append(f"operator-library-missing-family:{family}")
    operators = [build_operator(family) for family in mutation_families if family in OPERATOR_LIBRARY]
    pool_by_candidate = {pool["candidate_id"]: pool for pool in source_pools}
    bindings = [
        build_binding(index, candidate, pool_by_candidate[str(candidate["candidate_id"])])
        for index, candidate in enumerate(candidates, start=1)
        if str(candidate.get("mutation_family")) in OPERATOR_LIBRARY
    ]
    return source_pools, operators, bindings, problems


def check_forbidden_keys(item: Any, path: str = "root") -> list[str]:
    problems: list[str] = []
    if isinstance(item, dict):
        for key, value in item.items():
            if key in FORBIDDEN_KEYS and value not in (None, "", [], {}):
                problems.append(f"forbidden-key-present:{path}.{key}")
            problems.extend(check_forbidden_keys(value, f"{path}.{key}"))
    elif isinstance(item, list):
        for index, value in enumerate(item):
            problems.extend(check_forbidden_keys(value, f"{path}[{index}]"))
    return problems


def preflight_problem_counts(
    source_pools: list[dict[str, Any]],
    operators: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
    problems: list[str],
) -> dict[str, int]:
    true_authorization_count = 0
    missing_content_count = 0
    forbidden_key_count = 0
    for collection_name, collection in (
        ("source_pool", source_pools),
        ("operator", operators),
        ("binding", bindings),
    ):
        for item in collection:
            item_id = (
                item.get("source_pool_id")
                or item.get("operator_id")
                or item.get("binding_id")
                or "unknown"
            )
            for field in PREFLIGHT_FALSE_AUTHORIZATION_FIELDS:
                if item.get(field) is not False:
                    true_authorization_count += 1
                    problems.append(f"{collection_name}-auth-not-false:{item_id}:{field}")
            for key in (
                "source_slot_ids",
                "source_scenarios",
                "allowed_controls",
                "invariants",
                "required_pre_generation_checks",
                "candidate_id",
                "operator_id",
            ):
                if key in item and item.get(key) in (None, "", [], {}):
                    missing_content_count += 1
                    problems.append(f"{collection_name}-missing-{key}:{item_id}")
            forbidden = check_forbidden_keys(item, collection_name)
            forbidden_key_count += len(forbidden)
            problems.extend(forbidden)
    return {
        "true_authorization_count": true_authorization_count,
        "missing_preflight_content_count": missing_content_count,
        "forbidden_key_count": forbidden_key_count,
    }


def summarize(
    candidates: list[dict[str, Any]],
    source_pools: list[dict[str, Any]],
    operators: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
    preflight_counts: dict[str, int],
) -> dict[str, Any]:
    candidate_ids = {str(candidate.get("candidate_id")) for candidate in candidates}
    pool_candidate_ids = {str(pool.get("candidate_id")) for pool in source_pools}
    binding_candidate_ids = {str(binding.get("candidate_id")) for binding in bindings}
    source_slots = sorted({str(slot) for item in candidates for slot in item.get("source_slot_ids", [])})
    pool_slots = sorted({str(slot) for item in source_pools for slot in item.get("source_slot_ids", [])})
    bindings_by_candidate: dict[str, list[str]] = defaultdict(list)
    for binding in bindings:
        bindings_by_candidate[str(binding.get("candidate_id"))].append(str(binding.get("operator_id")))
    return {
        "candidate_count": len(candidates),
        "archetype_count": len({str(candidate.get("archetype_id")) for candidate in candidates}),
        "candidate_role_counts": dict(
            sorted(Counter(candidate.get("candidate_role") for candidate in candidates).items())
        ),
        "source_pool_count": len(source_pools),
        "mutation_operator_count": len(operators),
        "candidate_operator_binding_count": len(bindings),
        "unique_mutation_family_count": len({str(candidate.get("mutation_family")) for candidate in candidates}),
        "candidate_without_source_pool_count": len(candidate_ids - pool_candidate_ids),
        "candidate_without_operator_binding_count": len(candidate_ids - binding_candidate_ids),
        "multi_binding_candidate_count": sum(
            1 for operator_ids in bindings_by_candidate.values() if len(operator_ids) != 1
        ),
        "source_slot_count": len(source_slots),
        "covered_source_slot_count": len(set(source_slots) & set(pool_slots)),
        "missing_source_slot_count": len(set(source_slots) - set(pool_slots)),
        "mutation_family_counts": dict(
            sorted(Counter(candidate.get("mutation_family") for candidate in candidates).items())
        ),
        **preflight_counts,
    }


def choose_verdict(problems: list[str], summary: dict[str, Any]) -> str:
    if problems:
        return INFRA_NULL_VERDICT
    expected_summary = {
        "candidate_count": EXPECTED_CANDIDATE_COUNT,
        "archetype_count": EXPECTED_ARCHETYPE_COUNT,
        "candidate_role_counts": EXPECTED_ROLES,
        "source_pool_count": EXPECTED_CANDIDATE_COUNT,
        "mutation_operator_count": EXPECTED_OPERATOR_COUNT,
        "candidate_operator_binding_count": EXPECTED_CANDIDATE_COUNT,
        "unique_mutation_family_count": EXPECTED_OPERATOR_COUNT,
        "candidate_without_source_pool_count": 0,
        "candidate_without_operator_binding_count": 0,
        "multi_binding_candidate_count": 0,
        "missing_source_slot_count": 0,
        "true_authorization_count": 0,
        "missing_preflight_content_count": 0,
        "forbidden_key_count": 0,
    }
    for key, expected in expected_summary.items():
        if summary.get(key) != expected:
            return INFRA_NULL_VERDICT
    return COMPLETE_VERDICT


def build_report(
    iter126_report_path: Path,
    iter126_result_path: Path,
    iter126_note_path: Path,
    iter127_result_path: Path,
    iter127_note_path: Path,
) -> dict[str, Any]:
    problems: list[str] = []
    iter126_report, report_problems = load_json(iter126_report_path, "iter126-report")
    iter126_result, result126_problems = load_text(iter126_result_path, "iter126-result")
    iter126_note, note126_problems = load_text(iter126_note_path, "iter126-note")
    iter127_result, result127_problems = load_text(iter127_result_path, "iter127-result")
    iter127_note, note127_problems = load_text(iter127_note_path, "iter127-note")
    problems.extend(report_problems)
    problems.extend(result126_problems)
    problems.extend(note126_problems)
    problems.extend(result127_problems)
    problems.extend(note127_problems)

    if iter126_report.get("verdict") != ITER126_VERDICT:
        problems.append(f"iter126-verdict-mismatch:{iter126_report.get('verdict')!r}")
    require_contains(problems, "iter126-result", iter126_result, ITER126_VERDICT)
    require_contains(problems, "iter127-result", iter127_result, ITER127_VERDICT)
    require_boundary(problems, "iter126-note", iter126_note)
    require_boundary(problems, "iter127-note", iter127_note)

    summary_in = iter126_report.get("summary")
    if not isinstance(summary_in, dict):
        problems.append("iter126-summary-not-dict")
        summary_in = {}
    for key, expected in (
        ("candidate_count", EXPECTED_CANDIDATE_COUNT),
        ("archetype_count", EXPECTED_ARCHETYPE_COUNT),
        ("candidate_role_counts", EXPECTED_ROLES),
        ("true_authorization_count", 0),
        ("generated_scenario_path_count", 0),
        ("launch_command_count", 0),
        ("metric_or_threshold_change_instruction_count", 0),
        ("missing_required_content_count", 0),
    ):
        if summary_in.get(key) != expected:
            problems.append(f"iter126-summary-{key}-mismatch:{summary_in.get(key)!r}!={expected!r}")

    candidates = validate_candidates(iter126_report.get("manifest_candidates"), problems)
    if problems:
        source_pools: list[dict[str, Any]] = []
        operators: list[dict[str, Any]] = []
        bindings: list[dict[str, Any]] = []
        preflight_counts = {
            "true_authorization_count": 0,
            "missing_preflight_content_count": 0,
            "forbidden_key_count": 0,
        }
    else:
        source_pools, operators, bindings, preflight_problems = build_preflight(candidates)
        problems.extend(preflight_problems)
        preflight_counts = preflight_problem_counts(source_pools, operators, bindings, problems)
    summary = summarize(candidates, source_pools, operators, bindings, preflight_counts)
    return {
        "iteration": 128,
        "inputs": {
            "iter126_report": str(iter126_report_path),
            "iter126_result": str(iter126_result_path),
            "iter126_note": str(iter126_note_path),
            "iter127_result": str(iter127_result_path),
            "iter127_note": str(iter127_note_path),
        },
        "summary": summary,
        "source_pools": source_pools,
        "mutation_operators": operators,
        "candidate_operator_bindings": bindings,
        "future_generation_preflight_requirements": [
            "freeze generated artifact naming before any scenario file is created",
            "freeze destination directories and duplicate handling before any generation run",
            "carry candidate_id, source_pool_id, source_slot_id, and operator_id into all outputs",
            "separate scenario generation, execution, analysis, and learning/update into distinct hypotheses",
            "preserve no-repair/no-safety/no-deployment claim boundary until later evidence proves otherwise",
        ],
        "problems": problems,
        "verdict": choose_verdict(problems, summary),
        "claim_boundary": BOUNDARY,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 128 - support-core source-pool and mutation-operator preflight",
        "",
        f"Verdict: `{report['verdict']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Source pools", ""])
    for pool in report["source_pools"]:
        lines.extend(
            [
                f"### `{pool['source_pool_id']}`",
                "",
                f"- candidate: `{pool['candidate_id']}`",
                f"- archetype: `{pool['archetype_id']}`",
                f"- role: `{pool['candidate_role']}`",
                f"- mutation family: `{pool['mutation_family']}`",
                f"- source slots: `{pool['source_slot_ids']}`",
                f"- source scenarios: `{pool['source_scenarios']}`",
                f"- scenario generation authorized: `{pool['scenario_generation_authorized']}`",
                f"- HUGSIM run authorized: `{pool['hugsim_run_authorized']}`",
                "",
            ]
        )
    lines.extend(["## Mutation operators", ""])
    for operator in report["mutation_operators"]:
        lines.extend(
            [
                f"### `{operator['operator_id']}`",
                "",
                f"- mutation family: `{operator['mutation_family']}`",
                f"- operator kind: `{operator['operator_kind']}`",
                "- allowed controls:",
            ]
        )
        lines.extend(f"  - {control}" for control in operator["allowed_controls"])
        lines.append("- invariants:")
        lines.extend(f"  - {invariant}" for invariant in operator["invariants"])
        lines.append("")
    if report["problems"]:
        lines.extend(["## Problems", ""])
        lines.extend(f"- `{problem}`" for problem in report["problems"])
        lines.append("")
    lines.extend(["## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def write_note(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# HUGSIM support-core source-pool and mutation-operator preflight",
        "",
        "Status: iteration-128 pre-generation note. This freezes source pools and mutation",
        "operators only; it authorizes no scenario generation, generated artifacts, execution",
        "slot selection, HUGSIM run, GPU launch, learning/update step, retuning, repair, safety,",
        "deployment, production, or commercial claim.",
        "",
        "## Source",
        "",
        "- Iteration 126 candidate manifest:",
        "  [`support_core_candidate_manifest_report.json`](../../experiments/iter126_support_core_candidate_manifest_preflight/proof-manifest/support_core_candidate_manifest_report.json)",
        "- Iteration 127 alignment audit:",
        "  [`SENTINEL_POST_ITER126_MISSION_ALIGNMENT_AUDIT_2026-07-14.md`](SENTINEL_POST_ITER126_MISSION_ALIGNMENT_AUDIT_2026-07-14.md)",
        "- Iteration 128 proof:",
        "  [`support_core_source_pool_mutation_preflight_report.json`](../../experiments/iter128_support_core_source_pool_mutation_preflight/proof-preflight/support_core_source_pool_mutation_preflight_report.json)",
        "",
        "## Freeze Rule",
        "",
        "Each iteration-126 symbolic candidate receives exactly one source pool and exactly one",
        "candidate-to-operator binding. Each unique mutation family receives exactly one frozen",
        "operator. These artifacts remain symbolic until a later pre-registration authorizes",
        "scenario generation.",
        "",
        "## Operator Library",
        "",
    ]
    for operator in report["mutation_operators"]:
        lines.extend(
            [
                f"### `{operator['operator_id']}`",
                "",
                f"- mutation family: `{operator['mutation_family']}`",
                f"- operator kind: `{operator['operator_kind']}`",
                "- allowed controls:",
            ]
        )
        lines.extend(f"  - {control}" for control in operator["allowed_controls"])
        lines.append("")
    lines.extend(["## Source Pools", ""])
    for pool in report["source_pools"]:
        lines.extend(
            [
                f"- `{pool['source_pool_id']}` -> `{pool['candidate_id']}` "
                f"using `{pool['mutation_family']}`; "
                "`scenario_generation=false`, `gpu=false`, `hugsim_run=false`.",
            ]
        )
    lines.extend(["", "## Future Gates", ""])
    for requirement in report["future_generation_preflight_requirements"]:
        lines.append(f"- {requirement}")
    lines.extend(["", "## Claim Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def write_command(path: Path) -> None:
    command = (
        "python3 experiments/iter128_support_core_source_pool_mutation_preflight/"
        "generate_support_core_source_pool_mutation_preflight.py\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(command)


def run_preflight(
    iter126_report: Path,
    iter126_result: Path,
    iter126_note: Path,
    iter127_result: Path,
    iter127_note: Path,
    out: Path,
    markdown_out: Path,
    note_out: Path,
    command_out: Path,
) -> dict[str, Any]:
    report = build_report(iter126_report, iter126_result, iter126_note, iter127_result, iter127_note)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    write_note(report, note_out)
    write_command(command_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iter126-report", type=Path, default=ITER126_REPORT_PATH)
    parser.add_argument("--iter126-result", type=Path, default=ITER126_RESULT_PATH)
    parser.add_argument("--iter126-note", type=Path, default=ITER126_NOTE_PATH)
    parser.add_argument("--iter127-result", type=Path, default=ITER127_RESULT_PATH)
    parser.add_argument("--iter127-note", type=Path, default=ITER127_NOTE_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_PATH)
    parser.add_argument("--note-out", type=Path, default=SOURCE_POOL_NOTE_PATH)
    parser.add_argument("--command-out", type=Path, default=DEFAULT_COMMAND_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_preflight(
        args.iter126_report,
        args.iter126_result,
        args.iter126_note,
        args.iter127_result,
        args.iter127_note,
        args.out,
        args.markdown_out,
        args.note_out,
        args.command_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
