"""Narrow post-evidence repair of two synthetic source references; no query logic."""

import ast
import os
import re
import subprocess

from .support import BASE, bounded, git, require, sha
from .support import committed_raw as original_committed_raw
from experiments.iter155_background_witness.storage import read_json

REMOVED = ["_classes.py", "_ops.py"]
CORRECTION_FILES = [
    str(BASE / name)
    for name in [
        "ADMISSION_CORRECTION.json",
        "ADMISSION_CORRECTION.md",
        "admission_repair.py",
        "corrected_check.py",
    ]
] + ["tests/test_iter157_admission_repair.py"]


def algorithm(source):
    tree = ast.parse(source)
    imports = []
    body = []
    for node in tree.body:
        if (
            isinstance(node, ast.ImportFrom)
            and node.level == 1
            and node.module in {"support", "admission_repair"}
        ):
            for name in node.names:
                imports.append((name.name, name.asname))
        else:
            body.append(ast.dump(node, include_attributes=False))
    return sorted(imports), body


def repair_plan(root, plan, correction):
    require(correction["removed_non_repository_paths"] == REMOVED, "correction_removal_set")
    require(
        correction["original_plan_sha256"] == sha(bounded(root, BASE / "PLAN.json")),
        "correction_plan_hash",
    )
    require(all(p in plan["source_files"] for p in REMOVED), "correction_original_entries")
    expected = [p for p in plan["source_files"] if p not in REMOVED]
    require(
        correction["remaining_source_files"] == expected and len(expected) == 38,
        "correction_inventory",
    )
    original = correction["original_source"]
    tracked = set(git(root, "ls-tree", "-r", "--name-only", original).decode().splitlines())
    require(
        all(p not in tracked and not (root / p).exists() for p in REMOVED),
        "synthetic_path_became_real",
    )
    require(all(p in tracked and (root / p).is_file() for p in expected), "real_source_missing")
    require(
        algorithm(bounded(root, BASE / "check.py").decode())
        == algorithm(bounded(root, BASE / "corrected_check.py").decode()),
        "checker_algorithm_changed",
    )
    return {**plan, "source_files": expected}


def committed_raw(root, raw, commit, plan, data):
    source = os.environ.get("SENTINEL157_CORRECTION_SOURCE", "")
    require(bool(re.fullmatch(r"[a-f0-9]{40}", source)), "correction_source_required")
    require(git(root, "rev-parse", "HEAD").decode().strip() == source, "correction_head")
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, source], cwd=root, capture_output=True
        ).returncode
        == 0,
        "correction_after_raw",
    )
    for path in CORRECTION_FILES:
        require(
            git(root, "show", f"{source}:{path}") == bounded(root, path), "correction_source_drift"
        )
    correction = read_json(root / BASE / "ADMISSION_CORRECTION.json")
    require(
        correction["raw_commit"] == commit
        and correction["original_source"] == data["source_commit"],
        "correction_binding",
    )
    effective = repair_plan(root, plan, correction)
    return original_committed_raw(root, raw, commit, effective, data)
