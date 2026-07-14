#!/usr/bin/env python3
"""Iteration 129 support-core generated-artifact naming preflight."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ITER128_VERDICT = "SUPPORT_CORE_SOURCE_POOL_MUTATION_PREFLIGHT_COMPLETE"
ITER126_VERDICT = "SUPPORT_CORE_CANDIDATE_MANIFEST_PREFLIGHT_COMPLETE"
COMPLETE_VERDICT = "SUPPORT_CORE_ARTIFACT_NAMING_PREFLIGHT_COMPLETE"
INFRA_NULL_VERDICT = "SUPPORT_CORE_ARTIFACT_NAMING_PREFLIGHT_INFRA_NULL"
EXPECTED_SOURCE_POOL_COUNT = 10
EXPECTED_OPERATOR_COUNT = 8
EXPECTED_BINDING_COUNT = 10
EXPECTED_RESERVATION_COUNT = 10
EXPECTED_RESERVED_PATHS_PER_RESERVATION = 3
EXPECTED_RESERVED_PATH_COUNT = 30
RESERVED_ROOT = "future_artifacts/support_core_blindspot_generation"
ITER128_REPORT_PATH = Path(
    "experiments/iter128_support_core_source_pool_mutation_preflight/proof-preflight/"
    "support_core_source_pool_mutation_preflight_report.json"
)
ITER128_RESULT_PATH = Path("experiments/iter128_support_core_source_pool_mutation_preflight/RESULT.md")
ITER128_NOTE_PATH = Path(
    "docs/research/SUPPORT_CORE_SOURCE_POOL_MUTATION_PREFLIGHT_2026-07-14.md"
)
ITER126_REPORT_PATH = Path(
    "experiments/iter126_support_core_candidate_manifest_preflight/proof-manifest/"
    "support_core_candidate_manifest_report.json"
)
ARTIFACT_NAMING_NOTE_PATH = Path(
    "docs/research/SUPPORT_CORE_ARTIFACT_NAMING_PREFLIGHT_2026-07-14.md"
)
DEFAULT_PROOF_DIR = Path("experiments/iter129_support_core_artifact_naming_preflight/proof-naming")
DEFAULT_REPORT_PATH = DEFAULT_PROOF_DIR / "support_core_artifact_naming_preflight_report.json"
DEFAULT_MARKDOWN_PATH = DEFAULT_PROOF_DIR / "support_core_artifact_naming_preflight.md"
DEFAULT_COMMAND_PATH = DEFAULT_PROOF_DIR / "generate_support_core_artifact_naming_preflight.command.txt"
BOUNDARY = (
    "generated-artifact naming and destination preflight only; no generated scenario artifact, "
    "scenario generation, execution-slot selection, GPU launch, HUGSIM run, learning/update "
    "step, repair, actor-causality, threshold-value, transfer upgrade, safety, deployment, "
    "robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, "
    "first-responder behavior, acquisition-value, retuning, production, commercial claim, or "
    "frontier-stack equivalence claim"
)
BOUNDARY_NEEDLES = (
    "no scenario generation",
    "generated artifact",
    "HUGSIM run",
    "GPU launch",
    "learning/update",
    "retuning",
    "repair",
    "safety",
    "deployment",
    "production",
    "commercial claim",
)
FALSE_AUTHORIZATION_FIELDS = (
    "reserved_path_creation_authorized",
    "generated_artifact_authorized",
    "scenario_generation_authorized",
    "execution_slot_selection_authorized",
    "execution_authorized",
    "gpu_authorized",
    "hugsim_run_authorized",
    "learning_update_authorized",
    "metric_change_authorized",
    "threshold_change_authorized",
    "planner_code_change_authorized",
    "runtime_code_change_authorized",
    "repair_authorized",
    "safety_claim_authorized",
    "deployment_authorized",
    "production_authorized",
    "commercial_claim_authorized",
)
FORBIDDEN_KEYS = (
    "launch_command",
    "launcher_command",
    "hugsim_command",
    "gpu_path",
    "raw_log_path",
    "raw_log_paths",
    "execution_slot_id",
    "execution_slot_selection",
    "generated_artifact_path",
    "generated_scenario_path",
)
FORBIDDEN_TEXT_NEEDLES = (
    "change thresholds",
    "change metrics",
    "alter thresholds",
    "alter metrics",
    "launch HUGSIM",
    "run HUGSIM",
    "use GPU",
    "select execution slot",
    "write generated artifact",
    "create generated artifact",
)


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
    normalized = normalize(text)
    for needle in BOUNDARY_NEEDLES:
        if normalize(needle) not in normalized:
            problems.append(f"{label}-missing-boundary:{needle}")


def false_authorizations() -> dict[str, bool]:
    return {field: False for field in FALSE_AUTHORIZATION_FIELDS}


def validate_iter128_report(report: dict[str, Any], problems: list[str]) -> None:
    if report.get("verdict") != ITER128_VERDICT:
        problems.append(f"iter128-verdict-mismatch:{report.get('verdict')!r}")
    summary = report.get("summary")
    if not isinstance(summary, dict):
        problems.append("iter128-summary-not-dict")
        return
    expected = {
        "source_pool_count": EXPECTED_SOURCE_POOL_COUNT,
        "mutation_operator_count": EXPECTED_OPERATOR_COUNT,
        "candidate_operator_binding_count": EXPECTED_BINDING_COUNT,
        "true_authorization_count": 0,
        "missing_preflight_content_count": 0,
        "forbidden_key_count": 0,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            problems.append(f"iter128-summary-{key}-mismatch:{summary.get(key)!r}!={value!r}")


def require_list(report: dict[str, Any], key: str, expected_count: int, problems: list[str]) -> list[dict[str, Any]]:
    value = report.get(key)
    if not isinstance(value, list):
        problems.append(f"iter128-{key}-not-list")
        return []
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            problems.append(f"iter128-{key}-item-not-dict:{index}")
            continue
        rows.append(item)
    if len(rows) != expected_count:
        problems.append(f"iter128-{key}-count-mismatch:{len(rows)}!={expected_count}")
    return rows


def validate_source_pools(source_pools: list[dict[str, Any]], problems: list[str]) -> None:
    seen: set[str] = set()
    for pool in source_pools:
        pool_id = pool.get("source_pool_id")
        if not isinstance(pool_id, str) or not pool_id:
            problems.append(f"source-pool-id-missing:{pool_id!r}")
        elif pool_id in seen:
            problems.append(f"source-pool-duplicate:{pool_id}")
        else:
            seen.add(pool_id)
        for field in (
            "candidate_id",
            "source_slot_ids",
            "source_scenarios",
            "mutation_family",
            "duplicate_handling_rule",
        ):
            if pool.get(field) in (None, "", [], {}):
                problems.append(f"source-pool-missing-{field}:{pool_id}")
        for field in FALSE_AUTHORIZATION_FIELDS:
            if field in pool and pool.get(field) is not False:
                problems.append(f"source-pool-auth-not-false:{pool_id}:{field}")


def validate_operators(operators: list[dict[str, Any]], problems: list[str]) -> None:
    seen: set[str] = set()
    for operator in operators:
        operator_id = operator.get("operator_id")
        if not isinstance(operator_id, str) or not operator_id:
            problems.append(f"operator-id-missing:{operator_id!r}")
        elif operator_id in seen:
            problems.append(f"operator-duplicate:{operator_id}")
        else:
            seen.add(operator_id)
        for field in ("mutation_family", "operator_kind", "allowed_controls", "invariants"):
            if operator.get(field) in (None, "", [], {}):
                problems.append(f"operator-missing-{field}:{operator_id}")


def validate_bindings(
    bindings: list[dict[str, Any]],
    source_pools: list[dict[str, Any]],
    operators: list[dict[str, Any]],
    problems: list[str],
) -> None:
    seen: set[str] = set()
    pool_ids = {str(pool.get("source_pool_id")) for pool in source_pools}
    operator_ids = {str(operator.get("operator_id")) for operator in operators}
    for binding in bindings:
        binding_id = binding.get("binding_id")
        if not isinstance(binding_id, str) or not binding_id:
            problems.append(f"binding-id-missing:{binding_id!r}")
        elif binding_id in seen:
            problems.append(f"binding-duplicate:{binding_id}")
        else:
            seen.add(binding_id)
        source_pool_id = str(binding.get("source_pool_id"))
        operator_id = str(binding.get("operator_id"))
        if source_pool_id not in pool_ids:
            problems.append(f"binding-missing-source-pool:{binding_id}:{source_pool_id}")
        if operator_id not in operator_ids:
            problems.append(f"binding-missing-operator:{binding_id}:{operator_id}")
        for field in FALSE_AUTHORIZATION_FIELDS:
            if field in binding and binding.get(field) is not False:
                problems.append(f"binding-auth-not-false:{binding_id}:{field}")


def reservation_id(index: int, candidate_id: str) -> str:
    return f"scar_{index:03d}_{slug(candidate_id)}"


def artifact_stem(index: int, candidate_id: str) -> str:
    return f"scartifact_{index:03d}_{slug(candidate_id)}"


def reserved_paths(candidate_id: str, stem: str) -> dict[str, str]:
    candidate_slug = slug(candidate_id)
    root = f"{RESERVED_ROOT}/{candidate_slug}"
    return {
        "scenario_spec": f"{root}/scenario_spec/{stem}.scenario_spec.json",
        "provenance_receipt": f"{root}/provenance_receipt/{stem}.provenance_receipt.json",
        "validation_manifest": f"{root}/validation_manifest/{stem}.validation_manifest.json",
    }


def build_reservations(
    source_pools: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    binding_by_candidate = {str(binding["candidate_id"]): binding for binding in bindings}
    reservations: list[dict[str, Any]] = []
    for index, pool in enumerate(sorted(source_pools, key=lambda item: str(item.get("source_pool_id"))), start=1):
        candidate_id = str(pool["candidate_id"])
        binding = binding_by_candidate[candidate_id]
        stem = artifact_stem(index, candidate_id)
        reservations.append(
            {
                "reservation_id": reservation_id(index, candidate_id),
                "candidate_id": candidate_id,
                "source_pool_id": pool["source_pool_id"],
                "operator_id": binding["operator_id"],
                "binding_id": binding["binding_id"],
                "mutation_family": pool["mutation_family"],
                "artifact_stem": stem,
                "reserved_destination_root": RESERVED_ROOT,
                "reserved_relative_paths": reserved_paths(candidate_id, stem),
                "path_collision_key": f"{candidate_id}|{pool['source_pool_id']}|{binding['operator_id']}",
                "duplicate_handling_rule": (
                    "preserve candidate_id, source_pool_id, and source_slot_id; repeated scenarios "
                    "remain distinct by source_slot_id"
                ),
                "required_future_creation_checks": [
                    "fresh HYPOTHESIS.md authorizes artifact creation",
                    "reserved path does not already exist immediately before creation",
                    "candidate_id/source_pool_id/operator_id are copied into artifact metadata",
                    "duplicate source scenarios remain keyed by source_slot_id",
                    "no HUGSIM execution or GPU launch is implied by artifact creation",
                    "claim boundary is copied into any future generation result",
                ],
                "source_slot_ids": [str(slot) for slot in pool.get("source_slot_ids", [])],
                "source_scenarios": [str(scenario) for scenario in pool.get("source_scenarios", [])],
                **false_authorizations(),
            }
        )
    return reservations


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


def check_forbidden_text(item: Any, path: str = "root") -> list[str]:
    problems: list[str] = []
    if isinstance(item, str):
        normalized = normalize(item).lower()
        for needle in FORBIDDEN_TEXT_NEEDLES:
            if needle in normalized:
                problems.append(f"forbidden-text:{path}:{needle}")
    elif isinstance(item, dict):
        for key, value in item.items():
            problems.extend(check_forbidden_text(value, f"{path}.{key}"))
    elif isinstance(item, list):
        for index, value in enumerate(item):
            problems.extend(check_forbidden_text(value, f"{path}[{index}]"))
    return problems


def reservation_problem_counts(
    repo_root: Path,
    reservations: list[dict[str, Any]],
    problems: list[str],
) -> dict[str, int]:
    true_authorization_count = 0
    missing_content_count = 0
    bad_reserved_path_count = 0
    existing_reserved_path_count = 0
    forbidden_key_count = 0
    forbidden_text_count = 0
    all_paths: list[str] = []
    for reservation in reservations:
        reservation_id_value = reservation.get("reservation_id")
        for field in FALSE_AUTHORIZATION_FIELDS:
            if reservation.get(field) is not False:
                true_authorization_count += 1
                problems.append(f"reservation-auth-not-false:{reservation_id_value}:{field}")
        for field in (
            "candidate_id",
            "source_pool_id",
            "operator_id",
            "binding_id",
            "artifact_stem",
            "reserved_destination_root",
            "reserved_relative_paths",
            "path_collision_key",
            "duplicate_handling_rule",
            "required_future_creation_checks",
        ):
            if reservation.get(field) in (None, "", [], {}):
                missing_content_count += 1
                problems.append(f"reservation-missing-{field}:{reservation_id_value}")
        relpaths = reservation.get("reserved_relative_paths")
        if not isinstance(relpaths, dict):
            missing_content_count += 1
            problems.append(f"reservation-paths-not-dict:{reservation_id_value}")
            continue
        if set(relpaths) != {"scenario_spec", "provenance_receipt", "validation_manifest"}:
            bad_reserved_path_count += 1
            problems.append(f"reservation-path-types-mismatch:{reservation_id_value}:{sorted(relpaths)}")
        for relpath in relpaths.values():
            all_paths.append(str(relpath))
            if not str(relpath).startswith(f"{RESERVED_ROOT}/"):
                bad_reserved_path_count += 1
                problems.append(f"reservation-path-outside-root:{reservation_id_value}:{relpath}")
            if (repo_root / str(relpath)).exists():
                existing_reserved_path_count += 1
                problems.append(f"reservation-path-exists:{reservation_id_value}:{relpath}")
        forbidden_keys = check_forbidden_keys(reservation, "reservation")
        forbidden_text = check_forbidden_text(reservation, "reservation")
        forbidden_key_count += len(forbidden_keys)
        forbidden_text_count += len(forbidden_text)
        problems.extend(forbidden_keys)
        problems.extend(forbidden_text)
    duplicate_path_count = sum(count - 1 for count in Counter(all_paths).values() if count > 1)
    if duplicate_path_count:
        problems.append(f"reserved-path-duplicate-count:{duplicate_path_count}")
    return {
        "true_authorization_count": true_authorization_count,
        "missing_reservation_content_count": missing_content_count,
        "bad_reserved_path_count": bad_reserved_path_count,
        "existing_reserved_path_count": existing_reserved_path_count,
        "duplicate_reserved_path_count": duplicate_path_count,
        "forbidden_key_count": forbidden_key_count,
        "forbidden_text_count": forbidden_text_count,
        "reserved_relative_path_count": len(all_paths),
    }


def summarize(reservations: list[dict[str, Any]], counts: dict[str, int]) -> dict[str, Any]:
    return {
        "artifact_reservation_count": len(reservations),
        "reserved_destination_root": RESERVED_ROOT,
        "reservation_type_counts": {
            key: sum(1 for item in reservations if key in item.get("reserved_relative_paths", {}))
            for key in ("scenario_spec", "provenance_receipt", "validation_manifest")
        },
        "candidate_count": len({str(item.get("candidate_id")) for item in reservations}),
        "source_pool_count": len({str(item.get("source_pool_id")) for item in reservations}),
        "operator_count": len({str(item.get("operator_id")) for item in reservations}),
        "binding_count": len({str(item.get("binding_id")) for item in reservations}),
        **counts,
    }


def choose_verdict(problems: list[str], summary: dict[str, Any]) -> str:
    if problems:
        return INFRA_NULL_VERDICT
    expected = {
        "artifact_reservation_count": EXPECTED_RESERVATION_COUNT,
        "candidate_count": EXPECTED_RESERVATION_COUNT,
        "source_pool_count": EXPECTED_SOURCE_POOL_COUNT,
        "operator_count": EXPECTED_OPERATOR_COUNT,
        "binding_count": EXPECTED_BINDING_COUNT,
        "reserved_relative_path_count": EXPECTED_RESERVED_PATH_COUNT,
        "true_authorization_count": 0,
        "missing_reservation_content_count": 0,
        "bad_reserved_path_count": 0,
        "existing_reserved_path_count": 0,
        "duplicate_reserved_path_count": 0,
        "forbidden_key_count": 0,
        "forbidden_text_count": 0,
    }
    for key, value in expected.items():
        if summary.get(key) != value:
            return INFRA_NULL_VERDICT
    if summary.get("reservation_type_counts") != {
        "scenario_spec": EXPECTED_RESERVATION_COUNT,
        "provenance_receipt": EXPECTED_RESERVATION_COUNT,
        "validation_manifest": EXPECTED_RESERVATION_COUNT,
    }:
        return INFRA_NULL_VERDICT
    return COMPLETE_VERDICT


def build_report(
    repo_root: Path,
    iter128_report_path: Path,
    iter128_result_path: Path,
    iter128_note_path: Path,
    iter126_report_path: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    problems: list[str] = []
    iter128_report, report128_problems = load_json(iter128_report_path, "iter128-report")
    iter128_result, result128_problems = load_text(iter128_result_path, "iter128-result")
    iter128_note, note128_problems = load_text(iter128_note_path, "iter128-note")
    iter126_report, report126_problems = load_json(iter126_report_path, "iter126-report")
    problems.extend(report128_problems)
    problems.extend(result128_problems)
    problems.extend(note128_problems)
    problems.extend(report126_problems)

    validate_iter128_report(iter128_report, problems)
    require_contains(problems, "iter128-result", iter128_result, ITER128_VERDICT)
    require_boundary(problems, "iter128-note", iter128_note)
    if iter126_report.get("verdict") != ITER126_VERDICT:
        problems.append(f"iter126-verdict-mismatch:{iter126_report.get('verdict')!r}")

    source_pools = require_list(iter128_report, "source_pools", EXPECTED_SOURCE_POOL_COUNT, problems)
    operators = require_list(iter128_report, "mutation_operators", EXPECTED_OPERATOR_COUNT, problems)
    bindings = require_list(
        iter128_report,
        "candidate_operator_bindings",
        EXPECTED_BINDING_COUNT,
        problems,
    )
    validate_source_pools(source_pools, problems)
    validate_operators(operators, problems)
    validate_bindings(bindings, source_pools, operators, problems)

    if problems:
        reservations: list[dict[str, Any]] = []
        counts = {
            "true_authorization_count": 0,
            "missing_reservation_content_count": 0,
            "bad_reserved_path_count": 0,
            "existing_reserved_path_count": 0,
            "duplicate_reserved_path_count": 0,
            "forbidden_key_count": 0,
            "forbidden_text_count": 0,
            "reserved_relative_path_count": 0,
        }
    else:
        reservations = build_reservations(source_pools, bindings)
        counts = reservation_problem_counts(repo_root, reservations, problems)
    summary = summarize(reservations, counts)
    return {
        "iteration": 129,
        "inputs": {
            "iter128_report": str(iter128_report_path),
            "iter128_result": str(iter128_result_path),
            "iter128_note": str(iter128_note_path),
            "iter126_report": str(iter126_report_path),
        },
        "summary": summary,
        "artifact_reservations": reservations,
        "future_generation_requirements": [
            "fresh HYPOTHESIS.md authorizes creation of reserved paths",
            "reserved paths are rechecked for nonexistence immediately before creation",
            "generated artifact metadata carries candidate_id, source_pool_id, operator_id, and binding_id",
            "scenario generation remains separate from execution-slot selection",
            "HUGSIM/GPU execution remains a later separately registered step",
            "learning/update and repair claims remain forbidden unless later evidence proves them",
        ],
        "problems": problems,
        "verdict": choose_verdict(problems, summary),
        "claim_boundary": BOUNDARY,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 129 - support-core generated-artifact naming preflight",
        "",
        f"Verdict: `{report['verdict']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Reservations", ""])
    for reservation in report["artifact_reservations"]:
        lines.extend(
            [
                f"### `{reservation['reservation_id']}`",
                "",
                f"- candidate: `{reservation['candidate_id']}`",
                f"- source pool: `{reservation['source_pool_id']}`",
                f"- operator: `{reservation['operator_id']}`",
                f"- binding: `{reservation['binding_id']}`",
                f"- artifact stem: `{reservation['artifact_stem']}`",
                f"- destination root: `{reservation['reserved_destination_root']}`",
                f"- path creation authorized: `{reservation['reserved_path_creation_authorized']}`",
                "- reserved relative paths:",
            ]
        )
        for label, relpath in reservation["reserved_relative_paths"].items():
            lines.append(f"  - `{label}`: `{relpath}`")
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
        "# HUGSIM support-core generated-artifact naming preflight",
        "",
        "Status: iteration-129 naming/destination preflight note. This reserves future artifact",
        "names and destination templates only; it authorizes no reserved path creation, generated",
        "scenario artifact, scenario generation, execution-slot selection, HUGSIM run, GPU launch,",
        "learning/update step, retuning, repair, safety, deployment, production, or commercial claim.",
        "",
        "## Source",
        "",
        "- Iteration 128 source-pool/mutation preflight:",
        "  [`support_core_source_pool_mutation_preflight_report.json`](../../experiments/iter128_support_core_source_pool_mutation_preflight/proof-preflight/support_core_source_pool_mutation_preflight_report.json)",
        "- Iteration 129 proof:",
        "  [`support_core_artifact_naming_preflight_report.json`](../../experiments/iter129_support_core_artifact_naming_preflight/proof-naming/support_core_artifact_naming_preflight_report.json)",
        "",
        "## Reservation Rule",
        "",
        f"Every reservation stays under `{RESERVED_ROOT}/`. Each candidate has one reservation with",
        "three planned future paths: `scenario_spec`, `provenance_receipt`, and",
        "`validation_manifest`. These paths are checked for uniqueness and nonexistence, but no",
        "reserved path is created by this iteration.",
        "",
        "## Reservations",
        "",
    ]
    for reservation in report["artifact_reservations"]:
        lines.extend(
            [
                f"### `{reservation['reservation_id']}`",
                "",
                f"- candidate: `{reservation['candidate_id']}`",
                f"- source pool: `{reservation['source_pool_id']}`",
                f"- operator: `{reservation['operator_id']}`",
                f"- path creation: `{reservation['reserved_path_creation_authorized']}`",
                "- reserved paths:",
            ]
        )
        for label, relpath in reservation["reserved_relative_paths"].items():
            lines.append(f"  - `{label}`: `{relpath}`")
        lines.append("")
    lines.extend(["## Future Gates", ""])
    for requirement in report["future_generation_requirements"]:
        lines.append(f"- {requirement}")
    lines.extend(["", "## Claim Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def write_command(path: Path) -> None:
    command = (
        "python3 experiments/iter129_support_core_artifact_naming_preflight/"
        "generate_support_core_artifact_naming_preflight.py\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(command)


def run_preflight(
    repo_root: Path,
    iter128_report: Path,
    iter128_result: Path,
    iter128_note: Path,
    iter126_report: Path,
    out: Path,
    markdown_out: Path,
    note_out: Path,
    command_out: Path,
) -> dict[str, Any]:
    report = build_report(repo_root, iter128_report, iter128_result, iter128_note, iter126_report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    write_note(report, note_out)
    write_command(command_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--iter128-report", type=Path, default=ITER128_REPORT_PATH)
    parser.add_argument("--iter128-result", type=Path, default=ITER128_RESULT_PATH)
    parser.add_argument("--iter128-note", type=Path, default=ITER128_NOTE_PATH)
    parser.add_argument("--iter126-report", type=Path, default=ITER126_REPORT_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_PATH)
    parser.add_argument("--note-out", type=Path, default=ARTIFACT_NAMING_NOTE_PATH)
    parser.add_argument("--command-out", type=Path, default=DEFAULT_COMMAND_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_preflight(
        args.repo_root,
        args.iter128_report,
        args.iter128_result,
        args.iter128_note,
        args.iter126_report,
        args.out,
        args.markdown_out,
        args.note_out,
        args.command_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
