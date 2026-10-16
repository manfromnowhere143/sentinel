"""Strict content and Git bindings; no scientific implementation."""

from pathlib import Path

from experiments.iter150_cloud_observation.native import parse
from experiments.iter158_constraint_aware_search.common import (
    inputs,
    encode,
    git,
    read,
    require,
    rss,
    sha,
    write,
)

BASE = Path("experiments/iter184_discarded_progress")
OLD = Path("experiments/iter153_action_feasibility/PLAN.json")


def document(root, name):
    raw = read(root, name)
    value = parse(raw)
    require(encode(value) == raw, "canonical_document")
    return value


def source_check(root, plan, source):
    require(len(source) == 40 and all(c in "0123456789abcdef" for c in source), "source_encoding")
    for name in [str(BASE / "PLAN.json"), *plan["source_files"]]:
        require(
            git(root, "show", source + ":" + name) == read(root, name), "source_changed:" + name
        )


__all__ = [
    "BASE",
    "OLD",
    "encode",
    "git",
    "read",
    "require",
    "rss",
    "sha",
    "write",
    "source_check",
    "inputs",
    "document",
]
