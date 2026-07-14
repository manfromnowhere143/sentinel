#!/usr/bin/env python3
"""Iteration 126 support-core candidate-generation manifest preflight."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ITER125_VERDICT = "SUPPORT_CORE_BLIND_SPOT_SCENARIO_DESIGN_COMPLETE"
COMPLETE_VERDICT = "SUPPORT_CORE_CANDIDATE_MANIFEST_PREFLIGHT_COMPLETE"
INFRA_NULL_VERDICT = "SUPPORT_CORE_CANDIDATE_MANIFEST_PREFLIGHT_INFRA_NULL"
EXPECTED_ARCHETYPE_COUNT = 5
EXPECTED_CANDIDATE_COUNT = 10
EXPECTED_ROLES = ("branch_stress", "counterfactual_control")
ITER125_REPORT_PATH = Path(
    "experiments/iter125_support_core_blind_spot_scenario_design/proof-design/"
    "support_core_blind_spot_scenario_design_report.json"
)
ITER125_RESULT_PATH = Path("experiments/iter125_support_core_blind_spot_scenario_design/RESULT.md")
ITER125_DESIGN_NOTE_PATH = Path(
    "docs/research/SUPPORT_CORE_BLIND_SPOT_SCENARIO_DESIGN_2026-07-14.md"
)
MANIFEST_NOTE_PATH = Path(
    "docs/research/SUPPORT_CORE_CANDIDATE_GENERATION_MANIFEST_2026-07-14.md"
)
DEFAULT_PROOF_DIR = Path("experiments/iter126_support_core_candidate_manifest_preflight/proof-manifest")
DEFAULT_REPORT_PATH = DEFAULT_PROOF_DIR / "support_core_candidate_manifest_report.json"
DEFAULT_MARKDOWN_PATH = DEFAULT_PROOF_DIR / "support_core_candidate_manifest.md"
DEFAULT_COMMAND_PATH = DEFAULT_PROOF_DIR / "generate_support_core_candidate_manifest.command.txt"
BOUNDARY = (
    "manifest preflight only; no scenario-generation execution, GPU launch, HUGSIM run, repair, "
    "actor-causality, threshold-value, transfer upgrade, safety, deployment, robustness, "
    "benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder "
    "behavior, acquisition-value, retuning, production, commercial claim, or frontier-stack "
    "equivalence claim"
)
FORBIDDEN_CLAIMS = (
    "scenario-generation execution",
    "GPU launch",
    "HUGSIM run",
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
    "authorizes no scenario generation",
    "HUGSIM run",
    "GPU launch",
    "retuning",
    "repair",
    "safety",
    "deployment",
    "benchmark",
    "population-rate",
    "production",
    "commercial claim",
)
REQUIRED_ARCHETYPE_FIELDS = (
    "archetype_id",
    "synthesis_label",
    "source_slot_ids",
    "source_scenarios",
    "support_side_branch",
    "selected_side_branch",
    "selected_rank_condition",
    "timing_gap_class",
    "candidate_generation_knobs",
    "future_validation_gates",
)
FALSE_AUTHORIZATION_FIELDS = (
    "execution_authorized",
    "gpu_authorized",
    "hugsim_run_authorized",
    "scenario_generation_authorized",
    "metric_change_authorized",
    "threshold_change_authorized",
    "planner_code_change_authorized",
    "runtime_code_change_authorized",
)
FORBIDDEN_CANDIDATE_KEYS = (
    "generated_scenario_path",
    "generated_scenario_paths",
    "launch_command",
    "launcher_command",
    "hugsim_command",
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


def slug(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return text or "missing"


def require_contains(problems: list[str], label: str, text: str, needle: str) -> None:
    if needle not in text:
        problems.append(f"{label}-missing:{needle}")


def validate_archetypes(archetypes: Any, problems: list[str]) -> list[dict[str, Any]]:
    if not isinstance(archetypes, list):
        problems.append("iter125-archetypes-not-list")
        return []
    validated: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, archetype in enumerate(archetypes, start=1):
        if not isinstance(archetype, dict):
            problems.append(f"iter125-archetype-not-dict:{index}")
            continue
        for field in REQUIRED_ARCHETYPE_FIELDS:
            value = archetype.get(field)
            if value in (None, "", [], {}):
                problems.append(f"iter125-archetype-missing-{field}:{index}")
        archetype_id = archetype.get("archetype_id")
        if isinstance(archetype_id, str):
            if archetype_id in seen_ids:
                problems.append(f"iter125-duplicate-archetype:{archetype_id}")
            seen_ids.add(archetype_id)
        else:
            problems.append(f"iter125-archetype-id-not-str:{index}:{archetype_id!r}")
        if not isinstance(archetype.get("source_slot_ids"), list):
            problems.append(f"iter125-source-slots-not-list:{index}")
        if not isinstance(archetype.get("source_scenarios"), list):
            problems.append(f"iter125-source-scenarios-not-list:{index}")
        if not isinstance(archetype.get("candidate_generation_knobs"), list):
            problems.append(f"iter125-knobs-not-list:{index}")
        if not isinstance(archetype.get("future_validation_gates"), list):
            problems.append(f"iter125-gates-not-list:{index}")
        validated.append(archetype)
    return sorted(validated, key=lambda item: str(item.get("archetype_id")))


def mutation_family(archetype: dict[str, Any], role: str) -> str:
    archetype_id = str(archetype.get("archetype_id"))
    support_branch = str(archetype.get("support_side_branch"))
    timing_class = str(archetype.get("timing_gap_class"))
    if role == "counterfactual_control":
        if timing_class == "no_pre_fire_support":
            return "introduce_pre_fire_support_reference_control"
        if timing_class == "post_fire_support":
            return "shift_post_fire_evidence_to_pre_fire_control"
        if "drifted" in support_branch or "drifted" in archetype_id:
            return "support_band_border_continuity_control"
        if "lost_absent" in support_branch or "lost_absent" in archetype_id:
            return "same_object_visibility_continuity_control"
        return "support_continuity_control"
    if timing_class == "no_pre_fire_support":
        return "unsupported_nearest_reference_pressure"
    if timing_class == "post_fire_support":
        return "post_fire_support_delay_pressure"
    if "drifted" in support_branch or "drifted" in archetype_id:
        return "support_drift_outside_band_sweep"
    if "lost_absent" in support_branch or "lost_absent" in archetype_id:
        return "support_loss_gap_sweep"
    return "measured_support_gap_pressure"


def role_objective(archetype: dict[str, Any], role: str) -> str:
    timing_class = archetype.get("timing_gap_class")
    rank = archetype.get("selected_rank_condition")
    if role == "branch_stress":
        return (
            "Preserve the observed two-track pressure: selected first-fire object remains "
            f"{rank}, timing class remains {timing_class}, and support-side branch pressure is "
            "varied without changing thresholds."
        )
    return (
        "Define a paired future control that preserves source provenance and active-surface "
        "pressure while attempting to restore support-side continuity before first fire; it "
        "keeps thresholds, metrics, planner code, and runtime code frozen."
    )


def required_gates(archetype: dict[str, Any]) -> list[str]:
    inherited = [str(gate) for gate in archetype.get("future_validation_gates", [])]
    return inherited + [
        "candidate-manifest gate: this row is a symbolic future candidate spec only",
        "fresh-hypothesis gate: scenario generation and execution require a later HYPOTHESIS.md",
        "authorization gate: execution_authorized, gpu_authorized, and hugsim_run_authorized stay false",
        "no-generated-path gate: candidate records no generated scenario path",
        "no-launch-command gate: candidate records no launch command",
        "no-threshold-change gate: thresholds and metrics remain frozen",
        "paired-role gate: each archetype has one branch_stress and one counterfactual_control spec",
    ]


def candidate_knobs(archetype: dict[str, Any], role: str) -> list[str]:
    knobs = [str(knob) for knob in archetype.get("candidate_generation_knobs", [])]
    if role == "branch_stress":
        knobs.append("role branch_stress: preserve observed branch pressure before any future run")
    else:
        knobs.append("role counterfactual_control: define paired continuity control before any future run")
    return knobs


def build_candidate(index: int, archetype: dict[str, Any], role: str) -> dict[str, Any]:
    archetype_id = str(archetype["archetype_id"])
    candidate = {
        "candidate_id": f"scbs_{index:03d}_{role}_{slug(archetype_id)}",
        "archetype_id": archetype_id,
        "candidate_role": role,
        "role_objective": role_objective(archetype, role),
        "source_synthesis_label": archetype.get("synthesis_label"),
        "source_slot_ids": [str(slot) for slot in archetype.get("source_slot_ids", [])],
        "source_scenarios": [str(scenario) for scenario in archetype.get("source_scenarios", [])],
        "source_row_count": archetype.get("source_row_count"),
        "support_side_branch": archetype.get("support_side_branch"),
        "selected_side_branch": archetype.get("selected_side_branch"),
        "selected_rank_condition": archetype.get("selected_rank_condition"),
        "timing_gap_class": archetype.get("timing_gap_class"),
        "support_gap_range_s": archetype.get("support_gap_range_s"),
        "mutation_family": mutation_family(archetype, role),
        "candidate_generation_knobs": candidate_knobs(archetype, role),
        "required_gates": required_gates(archetype),
        "future_hypothesis_required": True,
        "execution_authorized": False,
        "gpu_authorized": False,
        "hugsim_run_authorized": False,
        "scenario_generation_authorized": False,
        "metric_change_authorized": False,
        "threshold_change_authorized": False,
        "planner_code_change_authorized": False,
        "runtime_code_change_authorized": False,
        "forbidden_claims": list(FORBIDDEN_CLAIMS),
    }
    return candidate


def build_candidates(archetypes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for archetype in archetypes:
        for role in EXPECTED_ROLES:
            candidates.append(build_candidate(len(candidates) + 1, archetype, role))
    return candidates


def candidate_problem_counts(candidates: list[dict[str, Any]], problems: list[str]) -> dict[str, int]:
    true_authorization_count = 0
    generated_path_count = 0
    launch_command_count = 0
    metric_or_threshold_change_count = 0
    missing_required_content_count = 0
    for candidate in candidates:
        candidate_id = candidate.get("candidate_id")
        for field in FALSE_AUTHORIZATION_FIELDS:
            if candidate.get(field) is not False:
                true_authorization_count += 1
                problems.append(f"candidate-authorization-not-false:{candidate_id}:{field}")
        for key in FORBIDDEN_CANDIDATE_KEYS:
            if key in candidate and candidate.get(key) not in (None, "", [], {}):
                if "command" in key:
                    launch_command_count += 1
                else:
                    generated_path_count += 1
                problems.append(f"candidate-forbidden-key-present:{candidate_id}:{key}")
        for key in ("mutation_family", "candidate_generation_knobs", "required_gates"):
            if candidate.get(key) in (None, "", [], {}):
                missing_required_content_count += 1
                problems.append(f"candidate-missing-{key}:{candidate_id}")
        text = json.dumps(candidate, sort_keys=True)
        if "change thresholds" in text or "change metrics" in text:
            metric_or_threshold_change_count += 1
            problems.append(f"candidate-metric-threshold-change-language:{candidate_id}")
    return {
        "true_authorization_count": true_authorization_count,
        "generated_scenario_path_count": generated_path_count,
        "launch_command_count": launch_command_count,
        "metric_or_threshold_change_instruction_count": metric_or_threshold_change_count,
        "missing_required_content_count": missing_required_content_count,
    }


def summarize(
    archetypes: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    candidate_counts: dict[str, int],
) -> dict[str, Any]:
    source_slots = sorted({str(slot) for item in archetypes for slot in item.get("source_slot_ids", [])})
    covered_slots = sorted(
        {str(slot) for item in candidates for slot in item.get("source_slot_ids", [])}
    )
    by_archetype: dict[str, list[str]] = defaultdict(list)
    for candidate in candidates:
        by_archetype[str(candidate.get("archetype_id"))].append(str(candidate.get("candidate_role")))
    role_pair_complete_count = sum(1 for roles in by_archetype.values() if sorted(roles) == sorted(EXPECTED_ROLES))
    return {
        "archetype_count": len(archetypes),
        "candidate_count": len(candidates),
        "candidates_per_archetype": {
            archetype_id: len(roles) for archetype_id, roles in sorted(by_archetype.items())
        },
        "candidate_role_counts": dict(
            sorted(Counter(candidate.get("candidate_role") for candidate in candidates).items())
        ),
        "role_pair_complete_count": role_pair_complete_count,
        "source_slot_count": len(source_slots),
        "covered_source_slot_count": len(set(source_slots) & set(covered_slots)),
        "missing_source_slot_count": len(set(source_slots) - set(covered_slots)),
        "mutation_family_counts": dict(
            sorted(Counter(candidate.get("mutation_family") for candidate in candidates).items())
        ),
        **candidate_counts,
    }


def choose_verdict(
    problems: list[str],
    archetypes: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    summary: dict[str, Any],
) -> str:
    if problems:
        return INFRA_NULL_VERDICT
    if len(archetypes) != EXPECTED_ARCHETYPE_COUNT:
        return INFRA_NULL_VERDICT
    if len(candidates) != EXPECTED_CANDIDATE_COUNT:
        return INFRA_NULL_VERDICT
    if summary.get("role_pair_complete_count") != EXPECTED_ARCHETYPE_COUNT:
        return INFRA_NULL_VERDICT
    if summary.get("candidate_role_counts") != {"branch_stress": 5, "counterfactual_control": 5}:
        return INFRA_NULL_VERDICT
    if summary.get("missing_source_slot_count") != 0:
        return INFRA_NULL_VERDICT
    for key in (
        "true_authorization_count",
        "generated_scenario_path_count",
        "launch_command_count",
        "metric_or_threshold_change_instruction_count",
        "missing_required_content_count",
    ):
        if summary.get(key) != 0:
            return INFRA_NULL_VERDICT
    return COMPLETE_VERDICT


def build_report(
    iter125_report_path: Path,
    iter125_result_path: Path,
    iter125_design_note_path: Path,
) -> dict[str, Any]:
    problems: list[str] = []
    iter125_report, report_problems = load_json(iter125_report_path, "iter125-report")
    iter125_result, result_problems = load_text(iter125_result_path, "iter125-result")
    iter125_note, note_problems = load_text(iter125_design_note_path, "iter125-design-note")
    problems.extend(report_problems)
    problems.extend(result_problems)
    problems.extend(note_problems)
    if iter125_report.get("verdict") != ITER125_VERDICT:
        problems.append(f"iter125-verdict-mismatch:{iter125_report.get('verdict')!r}")
    require_contains(problems, "iter125-result", iter125_result, ITER125_VERDICT)
    for needle in BOUNDARY_NEEDLES:
        require_contains(problems, "iter125-design-note", iter125_note, needle)

    archetypes = validate_archetypes(iter125_report.get("archetypes"), problems)
    candidates = build_candidates(archetypes) if not problems else []
    candidate_counts = candidate_problem_counts(candidates, problems)
    summary = summarize(archetypes, candidates, candidate_counts)
    report = {
        "iteration": 126,
        "inputs": {
            "iter125_report": str(iter125_report_path),
            "iter125_result": str(iter125_result_path),
            "iter125_design_note": str(iter125_design_note_path),
        },
        "summary": summary,
        "manifest_candidates": candidates,
        "future_pre_registration_requirements": [
            "freeze candidate source pool and mutation operators before scenario generation",
            "preserve branch_stress and counterfactual_control pairing by archetype",
            "define destination paths and duplicate handling by candidate_id and slot_id",
            "keep thresholds, HUGSIM metrics, planner code, and runtime code unchanged unless "
            "a later hypothesis explicitly authorizes a separate intervention",
            "separate manifest preflight, generation, execution, and analysis into distinct "
            "pre-registered iterations",
        ],
        "problems": problems,
        "verdict": choose_verdict(problems, archetypes, candidates, summary),
        "claim_boundary": BOUNDARY,
    }
    return report


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 126 - support-core candidate-generation manifest preflight",
        "",
        f"Verdict: `{report['verdict']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Candidate specs", ""])
    for candidate in report["manifest_candidates"]:
        lines.extend(
            [
                f"### `{candidate['candidate_id']}`",
                "",
                f"- archetype: `{candidate['archetype_id']}`",
                f"- role: `{candidate['candidate_role']}`",
                f"- mutation family: `{candidate['mutation_family']}`",
                f"- source slots: `{candidate['source_slot_ids']}`",
                f"- source scenarios: `{candidate['source_scenarios']}`",
                f"- execution authorized: `{candidate['execution_authorized']}`",
                f"- GPU authorized: `{candidate['gpu_authorized']}`",
                f"- HUGSIM run authorized: `{candidate['hugsim_run_authorized']}`",
                "- required gates:",
            ]
        )
        lines.extend(f"  - {gate}" for gate in candidate["required_gates"])
        lines.append("")
    if report["problems"]:
        lines.extend(["## Problems", ""])
        lines.extend(f"- `{problem}`" for problem in report["problems"])
        lines.append("")
    lines.extend(["## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def write_manifest_note(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# HUGSIM support-core candidate-generation manifest",
        "",
        "Status: iteration-126 manifest preflight note. This is a symbolic future-candidate",
        "manifest only; it authorizes no scenario generation, HUGSIM run, GPU launch, retuning,",
        "repair, safety, deployment, benchmark, population-rate, production, or commercial claim.",
        "",
        "## Source",
        "",
        "- Iteration 125 design proof:",
        "  [`support_core_blind_spot_scenario_design_report.json`](../../experiments/iter125_support_core_blind_spot_scenario_design/proof-design/support_core_blind_spot_scenario_design_report.json)",
        "- Iteration 125 design note:",
        "  [`SUPPORT_CORE_BLIND_SPOT_SCENARIO_DESIGN_2026-07-14.md`](SUPPORT_CORE_BLIND_SPOT_SCENARIO_DESIGN_2026-07-14.md)",
        "- Iteration 126 proof:",
        "  [`support_core_candidate_manifest_report.json`](../../experiments/iter126_support_core_candidate_manifest_preflight/proof-manifest/support_core_candidate_manifest_report.json)",
        "",
        "## Manifest Rule",
        "",
        "Each registered iteration-125 archetype receives exactly two future symbolic candidates:",
        "`branch_stress` and `counterfactual_control`. The first preserves observed branch",
        "pressure; the second freezes the paired future control idea. Both remain inert until a",
        "later pre-registration authorizes generation or execution.",
        "",
        "## Candidate Families",
        "",
    ]
    for candidate in report["manifest_candidates"]:
        lines.extend(
            [
                f"### `{candidate['candidate_id']}`",
                "",
                f"- archetype: `{candidate['archetype_id']}`",
                f"- role: `{candidate['candidate_role']}`",
                f"- mutation family: `{candidate['mutation_family']}`",
                f"- timing class: `{candidate['timing_gap_class']}`",
                f"- selected rank condition: `{candidate['selected_rank_condition']}`",
                f"- source slots: `{candidate['source_slot_ids']}`",
                "- authorization: `execution=false`, `gpu=false`, `hugsim_run=false`",
                "",
            ]
        )
    lines.extend(
        [
            "## Future Gates",
            "",
        ]
    )
    for requirement in report["future_pre_registration_requirements"]:
        lines.append(f"- {requirement}")
    lines.extend(["", "## Claim Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def write_command(path: Path) -> None:
    command = (
        "python3 experiments/iter126_support_core_candidate_manifest_preflight/"
        "generate_support_core_candidate_manifest.py\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(command)


def run_manifest(
    iter125_report: Path,
    iter125_result: Path,
    iter125_design_note: Path,
    out: Path,
    markdown_out: Path,
    manifest_note_out: Path,
    command_out: Path,
) -> dict[str, Any]:
    report = build_report(iter125_report, iter125_result, iter125_design_note)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    write_manifest_note(report, manifest_note_out)
    write_command(command_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iter125-report", type=Path, default=ITER125_REPORT_PATH)
    parser.add_argument("--iter125-result", type=Path, default=ITER125_RESULT_PATH)
    parser.add_argument("--iter125-design-note", type=Path, default=ITER125_DESIGN_NOTE_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_PATH)
    parser.add_argument("--manifest-note-out", type=Path, default=MANIFEST_NOTE_PATH)
    parser.add_argument("--command-out", type=Path, default=DEFAULT_COMMAND_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_manifest(
        args.iter125_report,
        args.iter125_result,
        args.iter125_design_note,
        args.out,
        args.markdown_out,
        args.manifest_note_out,
        args.command_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
