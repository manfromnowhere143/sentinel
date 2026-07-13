#!/usr/bin/env python3
"""Iteration 56 HUGSIM provenance instrumentation patch verifier.

Static source gate only: verify the frozen HUGSIM checkout, apply the proposed patch to a
temporary clone, and reject non-additive metric/control changes by diff inspection.
"""

from __future__ import annotations

import argparse
import json
import py_compile
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EXPECTED_HUGSIM_SHA = "62c690d39fd90020e68a196bd8bcc1c4d4191f2e"
NULL_VERDICT = "INSTRUMENTATION_PATCH_DESIGN_NULL"
COMPLETE_VERDICT = "INSTRUMENTATION_PATCH_DESIGN_COMPLETE"

ALLOWED_CHANGED_FILES = {
    "sim/utils/score_calculator.py",
    "closed_loop.py",
}
REQUIRED_ADDITIONS = (
    "collision_provenance",
    "_calculate_no_collision_provenance",
    "'source': 'nc'",
    "contact_distance",
    "final_score_dict['collision_provenance']",
)
FORBIDDEN_CHANGED_SUBSTRINGS = (
    "score_weight =",
    "boundaries =",
    "new_score_weight",
    "score_nc =",
    "score_dac =",
    "score_ttc =",
    "score_c =",
    "score_pdms =",
    "mean_score =",
    "route_completion =",
    "driving_score =",
    "traj2control",
    "env.step",
    "action =",
)


@dataclass(frozen=True)
class PatchLine:
    file: str
    text: str


@dataclass(frozen=True)
class PatchSummary:
    changed_files: list[str]
    additions: list[PatchLine]
    removals: list[PatchLine]


def run(cmd: list[str], cwd: Path | None = None) -> str:
    proc = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
    return proc.stdout.strip()


def repository_head(source_root: Path) -> str:
    return run(["git", "-C", str(source_root), "rev-parse", "HEAD"])


def parse_patch(patch_text: str) -> PatchSummary:
    changed_files: list[str] = []
    additions: list[PatchLine] = []
    removals: list[PatchLine] = []
    current_file = ""
    for line in patch_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            current_file = parts[3][2:] if len(parts) >= 4 and parts[3].startswith("b/") else ""
            if current_file:
                changed_files.append(current_file)
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            additions.append(PatchLine(current_file, line[1:]))
        elif line.startswith("-"):
            removals.append(PatchLine(current_file, line[1:]))
    return PatchSummary(sorted(set(changed_files)), additions, removals)


def guard_patch(summary: PatchSummary) -> dict[str, Any]:
    problems: list[str] = []
    disallowed = sorted(set(summary.changed_files) - ALLOWED_CHANGED_FILES)
    if disallowed:
        problems.append(f"disallowed_changed_files:{','.join(disallowed)}")

    added_text = "\n".join(line.text for line in summary.additions)
    missing_required = [needle for needle in REQUIRED_ADDITIONS if needle not in added_text]
    if missing_required:
        problems.append(f"missing_required_additions:{','.join(missing_required)}")

    addition_lines = {(line.file, line.text.strip()) for line in summary.additions}
    for line in [*summary.additions, *summary.removals]:
        stripped = line.text.strip()
        if (line.file, stripped) in addition_lines and line in summary.removals:
            continue
        for needle in FORBIDDEN_CHANGED_SUBSTRINGS:
            if needle in stripped:
                problems.append(f"forbidden_metric_or_control_change:{line.file}:{needle}:{stripped}")

    for line in summary.additions:
        if "score_list[" in line.text and "collision_provenance" in line.text:
            problems.append("provenance_added_inside_scalar_score_list")

    return {
        "changed_files_allowed": not disallowed,
        "required_provenance_fields_present": not missing_required,
        "metric_control_guard_passed": not problems,
        "problems": problems,
    }


def prepare_worktree(source_root: Path, expected_sha: str, work_root: Path) -> None:
    if work_root.exists():
        shutil.rmtree(work_root)
    run(["git", "clone", "--no-hardlinks", str(source_root), str(work_root)])
    run(["git", "-C", str(work_root), "checkout", "--detach", expected_sha])


def apply_patch(work_root: Path, patch_path: Path) -> None:
    run(["git", "-C", str(work_root), "apply", "--check", str(patch_path)])
    run(["git", "-C", str(work_root), "apply", str(patch_path)])


def compile_changed_python(work_root: Path, changed_files: list[str]) -> dict[str, Any]:
    compiled: list[str] = []
    failures: list[str] = []
    for rel in changed_files:
        if not rel.endswith(".py"):
            continue
        try:
            py_compile.compile(str(work_root / rel), doraise=True)
            compiled.append(rel)
        except py_compile.PyCompileError as exc:
            failures.append(f"{rel}:{exc.msg}")
    return {
        "compiled_python_files": compiled,
        "compile_failures": failures,
        "python_compile_passed": not failures,
    }


def choose_verdict(labels: dict[str, bool], problems: list[str]) -> str:
    if problems or not all(labels.values()):
        return NULL_VERDICT
    return COMPLETE_VERDICT


def build_report(
    source_root: Path,
    patch_path: Path,
    expected_sha: str,
    work_root: Path | None = None,
) -> dict[str, Any]:
    problems: list[str] = []
    head = repository_head(source_root)
    source_sha_match = head == expected_sha
    if not source_sha_match:
        problems.append(f"sha_mismatch:expected={expected_sha}:actual={head}")

    patch_text = patch_path.read_text()
    summary = parse_patch(patch_text)
    guard = guard_patch(summary)
    problems.extend(guard["problems"])

    patch_applies_cleanly = False
    compile_result = {
        "compiled_python_files": [],
        "compile_failures": [],
        "python_compile_passed": False,
    }
    temp_ctx = None
    try:
        if work_root is None:
            temp_ctx = tempfile.TemporaryDirectory(prefix="sentinel_iter56_patch_")
            work_root = Path(temp_ctx.name) / "HUGSIM"
        prepare_worktree(source_root, expected_sha, work_root)
        apply_patch(work_root, patch_path)
        patch_applies_cleanly = True
        compile_result = compile_changed_python(work_root, summary.changed_files)
        problems.extend(compile_result["compile_failures"])
    except (subprocess.CalledProcessError, OSError) as exc:
        problems.append(f"patch_apply_or_compile_failed:{type(exc).__name__}:{exc}")
    finally:
        if temp_ctx is not None:
            temp_ctx.cleanup()

    labels = {
        "source_sha_match": source_sha_match,
        "patch_applies_cleanly": patch_applies_cleanly,
        "changed_files_allowed": guard["changed_files_allowed"],
        "required_provenance_fields_present": guard["required_provenance_fields_present"],
        "metric_control_guard_passed": guard["metric_control_guard_passed"],
        "python_compile_passed": compile_result["python_compile_passed"],
    }
    labels["static_patch_supported"] = all(labels.values()) and not problems
    verdict = choose_verdict(labels, problems)
    return {
        "iteration": 56,
        "audit": "hugsim_provenance_instrumentation_patch",
        "source_root": str(source_root),
        "patch_path": str(patch_path),
        "repository_identity": {
            "head": head,
            "expected_sha": expected_sha,
            "sha_matches_expected": source_sha_match,
        },
        "changed_files": summary.changed_files,
        "addition_count": len(summary.additions),
        "removal_count": len(summary.removals),
        "labels": labels,
        "compile": compile_result,
        "problems": problems,
        "verdict": verdict,
        "claim_boundary": (
            "static patch-design gate only; no HUGSIM run, metric execution, actor-match, "
            "safety, transfer, deployment, benchmark, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 56 - HUGSIM provenance instrumentation patch verification",
        "",
        f"Verdict: `{report['verdict']}`",
        "",
        "## Labels",
        "",
    ]
    for key, value in report["labels"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend([
        "",
        "## Changed Files",
        "",
    ])
    for changed_file in report["changed_files"]:
        lines.append(f"- `{changed_file}`")
    lines.extend([
        "",
        "## Compile",
        "",
        f"- compiled Python files: `{report['compile']['compiled_python_files']}`",
        f"- compile failures: `{report['compile']['compile_failures']}`",
        "",
        "## Problems",
        "",
    ])
    if report["problems"]:
        lines.extend(f"- `{problem}`" for problem in report["problems"])
    else:
        lines.append("- None.")
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_verification(
    source_root: Path,
    patch_path: Path,
    out: Path,
    markdown_out: Path,
    expected_sha: str = EXPECTED_HUGSIM_SHA,
) -> dict[str, Any]:
    report = build_report(source_root, patch_path, expected_sha)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter56_hugsim_provenance_instrumentation_patch/"
            "proof-patch/patch_verification_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter56_hugsim_provenance_instrumentation_patch/"
            "proof-patch/patch_verification.md"
        ),
    )
    parser.add_argument("--expected-sha", default=EXPECTED_HUGSIM_SHA)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_verification(
        args.source_root.resolve(),
        args.patch.resolve(),
        args.out,
        args.markdown_out,
        expected_sha=args.expected_sha,
    )
    print(json.dumps({"verdict": report["verdict"], "labels": report["labels"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
