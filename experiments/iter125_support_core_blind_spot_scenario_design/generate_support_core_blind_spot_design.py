#!/usr/bin/env python3
"""Iteration 125 support-core blind-spot scenario design generator."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ITER121_VERDICT = "HUGSIM_SUPPORT_CORE_TWO_TRACK_SYNTHESIS_COMPLETE"
ITER122_VERDICT = "SUPPORT_CORE_TAXONOMY_DOCUMENTATION_COMPLETE"
ITER123_VERDICT = "MISSION_EVIDENCE_ALIGNMENT_AUDIT_COMPLETE"
ITER124_VERDICT = "MANUSCRIPT_REPORT_FRESHNESS_COMPLETE"
COMPLETE_VERDICT = "SUPPORT_CORE_BLIND_SPOT_SCENARIO_DESIGN_COMPLETE"
INFRA_NULL_VERDICT = "SUPPORT_CORE_BLIND_SPOT_SCENARIO_DESIGN_INFRA_NULL"
EXPECTED_ROW_COUNT = 8
EXPECTED_ARCHETYPE_COUNT = 5
ITER121_REPORT_PATH = Path(
    "experiments/iter121_hugsim_support_core_two_track_synthesis/proof-synthesis/"
    "support_core_two_track_synthesis_report.json"
)
ITER122_RESULT_PATH = Path("experiments/iter122_support_core_taxonomy_documentation/RESULT.md")
ITER123_RESULT_PATH = Path("experiments/iter123_mission_evidence_alignment_audit/RESULT.md")
ITER124_RESULT_PATH = Path("experiments/iter124_manuscript_report_freshness/RESULT.md")
SUPPORT_CORE_NOTE_PATH = Path("docs/research/SUPPORT_CORE_TWO_TRACK_TAXONOMY_2026-07-14.md")
DESIGN_NOTE_PATH = Path("docs/research/SUPPORT_CORE_BLIND_SPOT_SCENARIO_DESIGN_2026-07-14.md")
BOUNDARY = (
    "design surface only; no scenario-generation execution, GPU launch, HUGSIM run, repair, "
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


def require_contains(problems: list[str], label: str, text: str, needle: str) -> None:
    if needle not in text:
        problems.append(f"{label}-missing:{needle}")


def selected_rank_condition(rows: list[dict[str, Any]]) -> str:
    values = {row.get("selected_is_fire_nearest") for row in rows}
    if values == {True}:
        return "selected_nearest"
    if values == {False}:
        return "selected_not_nearest"
    return "selected_rank_mixed"


def timing_gap_class(rows: list[dict[str, Any]]) -> str:
    support_labels = {str(row.get("support_lifecycle_label")) for row in rows}
    if all(label.startswith("post_fire_support_only") for label in support_labels):
        return "post_fire_support"
    if support_labels == {"never_supported_reference"}:
        return "no_pre_fire_support"
    if any(row.get("fire_minus_last_support_s") is not None for row in rows):
        return "measured_support_gap"
    return "timing_gap_unknown"


def support_branch(rows: list[dict[str, Any]]) -> str:
    labels = sorted({str(row.get("support_lifecycle_label")) for row in rows})
    if labels == ["pre_fire_object_absent_at_fire"]:
        return "pre_fire_support_lost_absent_at_fire"
    if labels == ["pre_fire_object_drifted_outside_support_at_fire"]:
        return "pre_fire_support_drifted_outside_support"
    if labels == ["never_supported_reference"]:
        return "never_supported_reference"
    if all(label.startswith("post_fire_support_only") for label in labels):
        return "post_fire_support_only"
    return "support_branch_mixed:" + ",".join(labels)


def branch_knobs(synthesis_label: str, rank_condition: str, timing_class: str) -> list[str]:
    knobs = [
        "selected-object actor-support distance: keep selected first-fire object outside the frozen support band",
        "first-fire surface pressure: preserve the active CPA/TTC surface while varying provenance support",
        "slot-id keyed duplication: preserve repeated-scenario variants as distinct candidates",
    ]
    if "lost_absent" in synthesis_label:
        knobs.extend(
            [
                "support-object disappearance timing: sweep last-presence-to-fire and last-support-to-fire gaps",
                "same-object continuity control: paired variant where the early support object remains visible",
            ]
        )
    if "drifted" in synthesis_label:
        knobs.extend(
            [
                "support-object drift vector: sweep lateral/longitudinal drift outside the frozen support band",
                "support-band border control: paired variant at the support threshold without changing thresholds",
            ]
        )
    if "post_fire" in synthesis_label:
        knobs.extend(
            [
                "post-fire provenance delay: shift support evidence from after fire toward pre-fire",
                "different-object versus far-support split: preserve both observed post-fire support subtypes",
            ]
        )
    if "never_supported" in synthesis_label:
        knobs.extend(
            [
                "no-support reference control: require zero pre-fire support evidence for the reference branch",
                "nearest-decoy pressure: make the selected first-fire object nearest while still unsupported",
            ]
        )
    if rank_condition == "selected_not_nearest":
        knobs.append("rank competition: keep the selected object non-nearest while another object is closer")
    if rank_condition == "selected_nearest":
        knobs.append("nearest unsupported decoy: make the selected object nearest but still unsupported")
    if timing_class == "measured_support_gap":
        knobs.append("measured support-gap band: preserve the observed last-support-to-fire gap range")
    return knobs


def validation_gates() -> list[str]:
    return [
        "frozen-input gate: use committed support-core rows or a separately pre-registered candidate pool",
        "provenance gate: candidate must expose collision_provenance before actor-support classification",
        "two-track gate: selected first-fire object remains never-supported before collision",
        "branch-reproduction gate: candidate reproduces exactly one registered support-side branch",
        "duplicate-safety gate: destination paths and collection checks key by slot_id, not scenario",
        "no-retuning gate: thresholds, monitor code, HUGSIM metrics, and planner/action code remain unchanged",
        "claim-boundary gate: result remains design/preflight unless a later HYPOTHESIS authorizes execution",
    ]


def classify_archetype(synthesis_label: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    rank_condition = selected_rank_condition(rows)
    timing_class = timing_gap_class(rows)
    gap_values = [
        row.get("fire_minus_last_support_s")
        for row in rows
        if isinstance(row.get("fire_minus_last_support_s"), int | float)
    ]
    return {
        "archetype_id": synthesis_label.replace("two_track_", "blindspot_"),
        "synthesis_label": synthesis_label,
        "source_row_count": len(rows),
        "source_slot_ids": sorted(str(row["slot_id"]) for row in rows),
        "source_scenarios": sorted({str(row.get("scenario")) for row in rows}),
        "support_side_branch": support_branch(rows),
        "selected_side_branch": "selected_never_supported_before_collision",
        "selected_rank_condition": rank_condition,
        "timing_gap_class": timing_class,
        "support_gap_range_s": [min(gap_values), max(gap_values)] if gap_values else None,
        "candidate_generation_knobs": branch_knobs(synthesis_label, rank_condition, timing_class),
        "future_validation_gates": validation_gates(),
        "forbidden_claims": list(FORBIDDEN_CLAIMS),
    }


def choose_verdict(problems: list[str], archetypes: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    if problems:
        return INFRA_NULL_VERDICT
    if summary.get("row_count") != EXPECTED_ROW_COUNT:
        return INFRA_NULL_VERDICT
    if summary.get("covered_row_count") != EXPECTED_ROW_COUNT:
        return INFRA_NULL_VERDICT
    if summary.get("archetype_count") != EXPECTED_ARCHETYPE_COUNT:
        return INFRA_NULL_VERDICT
    if summary.get("duplicate_covered_slot_count") != 0:
        return INFRA_NULL_VERDICT
    if summary.get("missing_covered_slot_count") != 0:
        return INFRA_NULL_VERDICT
    for archetype in archetypes:
        if not archetype.get("candidate_generation_knobs") or not archetype.get("future_validation_gates"):
            return INFRA_NULL_VERDICT
        if len(archetype.get("forbidden_claims", [])) != len(FORBIDDEN_CLAIMS):
            return INFRA_NULL_VERDICT
    return COMPLETE_VERDICT


def build_report(
    iter121_report_path: Path,
    iter122_result_path: Path,
    iter123_result_path: Path,
    iter124_result_path: Path,
    support_core_note_path: Path,
) -> dict[str, Any]:
    problems: list[str] = []
    iter121_report, iter121_problems = load_json(iter121_report_path, "iter121-report")
    iter122_text, iter122_problems = load_text(iter122_result_path, "iter122-result")
    iter123_text, iter123_problems = load_text(iter123_result_path, "iter123-result")
    iter124_text, iter124_problems = load_text(iter124_result_path, "iter124-result")
    note_text, note_problems = load_text(support_core_note_path, "support-core-note")
    problems.extend(iter121_problems)
    problems.extend(iter122_problems)
    problems.extend(iter123_problems)
    problems.extend(iter124_problems)
    problems.extend(note_problems)
    require_contains(problems, "iter122-result", iter122_text, ITER122_VERDICT)
    require_contains(problems, "iter123-result", iter123_text, ITER123_VERDICT)
    require_contains(problems, "iter124-result", iter124_text, ITER124_VERDICT)
    require_contains(problems, "support-core-note", note_text, "support-core two-track taxonomy")

    rows: list[dict[str, Any]] = []
    if not problems:
        if iter121_report.get("verdict") != ITER121_VERDICT:
            problems.append(f"iter121-verdict-mismatch:{iter121_report.get('verdict')!r}")
        summary_in = iter121_report.get("summary")
        if not isinstance(summary_in, dict):
            problems.append("iter121-summary-not-dict")
            summary_in = {}
        if summary_in.get("row_count") != EXPECTED_ROW_COUNT:
            problems.append(f"iter121-row-count-mismatch:{summary_in.get('row_count')!r}")
        if summary_in.get("two_track_split_count") != EXPECTED_ROW_COUNT:
            problems.append(f"iter121-two-track-count-mismatch:{summary_in.get('two_track_split_count')!r}")
        selected_counts = summary_in.get("selected_lifecycle_counts")
        if not isinstance(selected_counts, dict) or selected_counts.get("selected_never_supported_before_collision") != 8:
            problems.append(f"iter121-selected-count-mismatch:{selected_counts!r}")
        rows_in = iter121_report.get("synthesis_rows")
        if not isinstance(rows_in, list):
            problems.append("iter121-synthesis-rows-not-list")
        else:
            for row in rows_in:
                if not isinstance(row, dict):
                    problems.append("iter121-synthesis-row-not-dict")
                    continue
                if row.get("two_track_split") is not True:
                    problems.append(f"row-not-two-track:{row.get('slot_id')!r}")
                if row.get("selected_lifecycle_label") != "selected_never_supported_before_collision":
                    problems.append(f"row-selected-label-mismatch:{row.get('slot_id')!r}")
                rows.append(row)

    by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        label = row.get("synthesis_label")
        if not isinstance(label, str):
            problems.append(f"row-synthesis-label-missing:{row.get('slot_id')!r}")
            continue
        by_label[label].append(row)
    archetypes = [classify_archetype(label, by_label[label]) for label in sorted(by_label)]
    covered_slots = [slot for archetype in archetypes for slot in archetype["source_slot_ids"]]
    source_slots = [str(row.get("slot_id")) for row in rows]
    duplicate_count = sum(count - 1 for count in Counter(covered_slots).values() if count > 1)
    missing_count = len(set(source_slots) - set(covered_slots))
    summary = {
        "row_count": len(rows),
        "covered_row_count": len(covered_slots),
        "archetype_count": len(archetypes),
        "synthesis_label_counts": dict(sorted(Counter(row.get("synthesis_label") for row in rows).items())),
        "selected_rank_condition_counts": dict(
            sorted(Counter(archetype["selected_rank_condition"] for archetype in archetypes).items())
        ),
        "timing_gap_class_counts": dict(
            sorted(Counter(archetype["timing_gap_class"] for archetype in archetypes).items())
        ),
        "duplicate_covered_slot_count": duplicate_count,
        "missing_covered_slot_count": missing_count,
    }
    return {
        "iteration": 125,
        "inputs": {
            "iter121_report": str(iter121_report_path),
            "iter122_result": str(iter122_result_path),
            "iter123_result": str(iter123_result_path),
            "iter124_result": str(iter124_result_path),
            "support_core_note": str(support_core_note_path),
        },
        "summary": summary,
        "archetypes": archetypes,
        "future_pre_registration_requirements": [
            "freeze candidate source pool before any scenario generation",
            "define mutation operators without changing Sentinel thresholds",
            "define support/provenance gates before selecting GPU slots",
            "separate design/preflight, generation, execution, and analysis into distinct hypotheses",
            "preserve no-repair/no-safety/no-deployment claim boundary until later evidence proves otherwise",
        ],
        "problems": problems,
        "verdict": choose_verdict(problems, archetypes, summary),
        "claim_boundary": BOUNDARY,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 125 - support-core blind-spot scenario design",
        "",
        f"Verdict: `{report['verdict']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Archetypes", ""])
    for archetype in report["archetypes"]:
        lines.extend(
            [
                f"### `{archetype['archetype_id']}`",
                "",
                f"- synthesis label: `{archetype['synthesis_label']}`",
                f"- source rows: `{archetype['source_row_count']}`",
                f"- support side: `{archetype['support_side_branch']}`",
                f"- selected side: `{archetype['selected_side_branch']}`",
                f"- selected rank: `{archetype['selected_rank_condition']}`",
                f"- timing class: `{archetype['timing_gap_class']}`",
                f"- source slots: `{archetype['source_slot_ids']}`",
                "- candidate-generation knobs:",
            ]
        )
        lines.extend(f"  - {knob}" for knob in archetype["candidate_generation_knobs"])
        lines.append("- future validation gates:")
        lines.extend(f"  - {gate}" for gate in archetype["future_validation_gates"])
        lines.append("")
    if report["problems"]:
        lines.extend(["## Problems", ""])
        lines.extend(f"- `{problem}`" for problem in report["problems"])
        lines.append("")
    lines.extend(["## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def write_design_note(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# HUGSIM support-core blind-spot scenario design",
        "",
        "Status: iteration-125 design note. This is a future candidate-generation design surface",
        "only; it authorizes no scenario generation, HUGSIM run, GPU launch, retuning, repair,",
        "safety, deployment, benchmark, population-rate, production, or commercial claim.",
        "",
        "## Source",
        "",
        "- Source taxonomy: [`SUPPORT_CORE_TWO_TRACK_TAXONOMY_2026-07-14.md`](SUPPORT_CORE_TWO_TRACK_TAXONOMY_2026-07-14.md)",
        "- Iteration 121 synthesis:",
        "  [`RESULT.md`](../../experiments/iter121_hugsim_support_core_two_track_synthesis/RESULT.md)",
        "- Iteration 125 proof:",
        "  [`support_core_blind_spot_scenario_design_report.json`](../../experiments/iter125_support_core_blind_spot_scenario_design/proof-design/support_core_blind_spot_scenario_design_report.json)",
        "",
        "## Design Principle",
        "",
        "The design target is the observed two-track split: support evidence appears on one object",
        "or branch, while first fire selects another object that was never supported before",
        "collision. Future candidate generation should vary this object/timing separation before",
        "any execution batch is proposed.",
        "",
        "## Archetypes",
        "",
    ]
    for archetype in report["archetypes"]:
        lines.extend(
            [
                f"### `{archetype['archetype_id']}`",
                "",
                f"- observed rows: `{archetype['source_row_count']}`",
                f"- source scenarios: `{archetype['source_scenarios']}`",
                f"- support branch: `{archetype['support_side_branch']}`",
                f"- selected branch: `{archetype['selected_side_branch']}`",
                f"- selected rank condition: `{archetype['selected_rank_condition']}`",
                f"- timing-gap class: `{archetype['timing_gap_class']}`",
                "- knobs:",
            ]
        )
        lines.extend(f"  - {knob}" for knob in archetype["candidate_generation_knobs"])
        lines.append("")
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


def run_design(
    iter121_report: Path,
    iter122_result: Path,
    iter123_result: Path,
    iter124_result: Path,
    support_core_note: Path,
    out: Path,
    markdown_out: Path,
    design_note_out: Path,
) -> dict[str, Any]:
    report = build_report(iter121_report, iter122_result, iter123_result, iter124_result, support_core_note)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    write_design_note(report, design_note_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iter121-report", type=Path, default=ITER121_REPORT_PATH)
    parser.add_argument("--iter122-result", type=Path, default=ITER122_RESULT_PATH)
    parser.add_argument("--iter123-result", type=Path, default=ITER123_RESULT_PATH)
    parser.add_argument("--iter124-result", type=Path, default=ITER124_RESULT_PATH)
    parser.add_argument("--support-core-note", type=Path, default=SUPPORT_CORE_NOTE_PATH)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter125_support_core_blind_spot_scenario_design/proof-design/"
            "support_core_blind_spot_scenario_design_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter125_support_core_blind_spot_scenario_design/proof-design/"
            "support_core_blind_spot_scenario_design.md"
        ),
    )
    parser.add_argument("--design-note-out", type=Path, default=DESIGN_NOTE_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_design(
        args.iter121_report,
        args.iter122_result,
        args.iter123_result,
        args.iter124_result,
        args.support_core_note,
        args.out,
        args.markdown_out,
        args.design_note_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
