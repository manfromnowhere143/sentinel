#!/usr/bin/env python3
"""Iteration 55 HUGSIM collision instrumentation source audit.

Source-only audit over a frozen HUGSIM checkout. The analyzer verifies checkout identity,
scans source text for metric/collision/provenance terms, and emits a conservative source map
for a future instrumentation design. It does not run HUGSIM and does not edit the source tree.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

EXPECTED_HUGSIM_SHA = "62c690d39fd90020e68a196bd8bcc1c4d4191f2e"
NULL_VERDICT = "COLLISION_INSTRUMENTATION_SOURCE_NULL"
COMPLETE_VERDICT = "COLLISION_INSTRUMENTATION_SOURCE_MAP_COMPLETE"

SOURCE_SUFFIXES = {
    ".cfg",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
SKIP_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
}

METRIC_TERMS = ("eval.json", "hdscore", "pdms", "nc", "dac", "ttc", "comfort", "rc")
GEOMETRY_TERMS = (
    "collision",
    "collide",
    "contact",
    "overlap",
    "intersect",
    "distance",
    "bbox",
    "box",
)
IDENTITY_TERMS = ("actor", "agent", "vehicle", "object", "track", "token", "instance", "id", "name")
WRITE_TERMS = ("json.dump", ".dump", ".write", "open(", "eval.json")


def _term_pattern(term: str) -> re.Pattern[str]:
    if re.fullmatch(r"[a-z0-9_]+", term):
        return re.compile(rf"(?<![A-Za-z0-9]){re.escape(term)}(?![A-Za-z0-9])", re.I)
    return re.compile(re.escape(term), re.I)


TERM_PATTERNS = {
    "metric": {term: _term_pattern(term) for term in METRIC_TERMS},
    "geometry": {term: _term_pattern(term) for term in GEOMETRY_TERMS},
    "identity": {term: _term_pattern(term) for term in IDENTITY_TERMS},
    "write": {term: _term_pattern(term) for term in WRITE_TERMS},
}


@dataclass(frozen=True)
class LineHit:
    line: int
    categories: tuple[str, ...]
    terms: tuple[str, ...]
    text: str
    before: str
    after: str


@dataclass(frozen=True)
class FileScan:
    path: str
    line_count: int
    term_counts: dict[str, dict[str, int]]
    category_counts: dict[str, int]
    snippets: list[LineHit]
    score: int
    metric_source: bool
    collision_geometry_source: bool
    actor_identity_available: bool
    instrumentation_candidate: bool


def run_git(source_root: Path, args: list[str]) -> str:
    proc = subprocess.run(
        ["git", "-C", str(source_root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def redact_remote_url(url: str) -> str:
    """Return a remote URL without credentials, preserving only host/path identity."""
    url = url.strip()
    if not url:
        return url
    if "://" in url:
        parsed = urlsplit(url)
        host = parsed.netloc.split("@")[-1]
        return urlunsplit((parsed.scheme, host, parsed.path, "", ""))
    if "@" in url and ":" in url:
        host_path = url.split("@", 1)[1]
        host, path = host_path.split(":", 1)
        return f"{host}/{path}"
    return re.sub(r"//[^/@]+@", "//", url)


def repository_identity(source_root: Path, expected_sha: str) -> dict[str, Any]:
    head = run_git(source_root, ["rev-parse", "HEAD"])
    remote_stdout = run_git(source_root, ["remote", "-v"])
    remotes = []
    for row in remote_stdout.splitlines():
        parts = row.split()
        if len(parts) >= 2:
            remotes.append({"name": parts[0], "url": redact_remote_url(parts[1])})
    return {
        "head": head,
        "expected_sha": expected_sha,
        "sha_matches_expected": head == expected_sha,
        "remotes": remotes,
    }


def iter_source_files(source_root: Path) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(source_root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        base = Path(dirpath)
        for filename in sorted(filenames):
            path = base / filename
            if path.suffix.lower() in SOURCE_SUFFIXES:
                files.append(path)
    return files


def _safe_line(line: str, limit: int = 180) -> str:
    compact = line.strip().replace("\t", " ")
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _hits_for_line(line: str) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {}
    for category, patterns in TERM_PATTERNS.items():
        found = [term for term, pattern in patterns.items() if pattern.search(line)]
        if found:
            hits[category] = found
    return hits


def _has_near(lines_a: list[int], lines_b: list[int], window: int) -> bool:
    return any(abs(a - b) <= window for a in lines_a for b in lines_b)


def scan_file(path: Path, source_root: Path, max_snippets: int = 4) -> FileScan | None:
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        return None

    rel = path.relative_to(source_root).as_posix()
    category_lines: dict[str, list[int]] = {"metric": [], "geometry": [], "identity": [], "write": []}
    term_counts: dict[str, Counter[str]] = {
        "metric": Counter(),
        "geometry": Counter(),
        "identity": Counter(),
        "write": Counter(),
    }
    snippets: list[LineHit] = []

    for idx, line in enumerate(lines, start=1):
        hits = _hits_for_line(line)
        if not hits:
            continue
        for category, terms in hits.items():
            category_lines[category].append(idx)
            term_counts[category].update(terms)
        if len(snippets) < max_snippets:
            before = _safe_line(lines[idx - 2]) if idx > 1 else ""
            after = _safe_line(lines[idx]) if idx < len(lines) else ""
            snippets.append(
                LineHit(
                    line=idx,
                    categories=tuple(sorted(hits)),
                    terms=tuple(sorted({term for terms in hits.values() for term in terms})),
                    text=_safe_line(line),
                    before=before,
                    after=after,
                )
            )

    category_counts = {key: len(value) for key, value in category_lines.items()}
    if not any(category_counts.values()):
        return None

    metric_terms = term_counts["metric"]
    metric_source = bool(
        metric_terms.get("eval.json")
        or (
            metric_terms.get("hdscore")
            and sum(metric_terms.get(term, 0) for term in ("nc", "pdms", "dac", "ttc")) >= 1
        )
        or (
            metric_terms.get("nc")
            and category_counts["write"]
            and _has_near(category_lines["metric"], category_lines["write"], 20)
        )
    )
    collision_geometry_source = bool(
        category_counts["geometry"]
        and (
            _has_near(category_lines["metric"], category_lines["geometry"], 80)
            or "collision" in rel.lower()
            or "metric" in rel.lower()
            or "eval" in rel.lower()
        )
    )
    actor_identity_available = bool(
        category_counts["identity"]
        and category_counts["geometry"]
        and _has_near(category_lines["identity"], category_lines["geometry"], 80)
    )
    instrumentation_candidate = bool(metric_source and collision_geometry_source)

    score = (
        10 * category_counts["metric"]
        + 7 * category_counts["geometry"]
        + 5 * category_counts["identity"]
        + 4 * category_counts["write"]
    )
    if metric_source:
        score += 40
    if collision_geometry_source:
        score += 30
    if actor_identity_available:
        score += 20
    if instrumentation_candidate:
        score += 30

    return FileScan(
        path=rel,
        line_count=len(lines),
        term_counts={category: dict(counts) for category, counts in term_counts.items()},
        category_counts=category_counts,
        snippets=snippets,
        score=score,
        metric_source=metric_source,
        collision_geometry_source=collision_geometry_source,
        actor_identity_available=actor_identity_available,
        instrumentation_candidate=instrumentation_candidate,
    )


def scan_source(source_root: Path, max_files: int = 30, max_snippets: int = 4) -> dict[str, Any]:
    scans: list[FileScan] = []
    files = iter_source_files(source_root)
    for path in files:
        scan = scan_file(path, source_root, max_snippets=max_snippets)
        if scan is not None:
            scans.append(scan)
    scans.sort(key=lambda item: (-item.score, item.path))
    selected = scans[:max_files]
    return {
        "source_file_count": len(files),
        "candidate_file_count": len(scans),
        "candidate_files": [file_scan_to_json(scan) for scan in selected],
        "omitted_candidate_file_count": max(0, len(scans) - len(selected)),
    }


def file_scan_to_json(scan: FileScan) -> dict[str, Any]:
    return {
        "path": scan.path,
        "line_count": scan.line_count,
        "score": scan.score,
        "category_counts": scan.category_counts,
        "term_counts": scan.term_counts,
        "labels": {
            "metric_source": scan.metric_source,
            "collision_geometry_source": scan.collision_geometry_source,
            "actor_identity_available": scan.actor_identity_available,
            "instrumentation_candidate": scan.instrumentation_candidate,
        },
        "snippets": [
            {
                "line": hit.line,
                "categories": list(hit.categories),
                "terms": list(hit.terms),
                "before": hit.before,
                "text": hit.text,
                "after": hit.after,
            }
            for hit in scan.snippets
        ],
    }


def summarize_labels(identity: dict[str, Any], source_map: dict[str, Any], problems: list[str]) -> dict[str, bool]:
    candidates = source_map["candidate_files"]
    metric_source_identified = any(row["labels"]["metric_source"] for row in candidates)
    collision_geometry_source_identified = any(
        row["labels"]["collision_geometry_source"] for row in candidates
    )
    actor_identity_available = any(row["labels"]["actor_identity_available"] for row in candidates)
    instrumentation_point_supported = any(
        row["labels"]["instrumentation_candidate"] for row in candidates
    )
    source_map_insufficient = bool(
        problems
        or not identity.get("sha_matches_expected")
        or not metric_source_identified
        or not collision_geometry_source_identified
        or not instrumentation_point_supported
    )
    return {
        "metric_source_identified": metric_source_identified,
        "collision_geometry_source_identified": collision_geometry_source_identified,
        "actor_identity_available_in_source": actor_identity_available,
        "instrumentation_point_supported": instrumentation_point_supported,
        "source_map_insufficient": source_map_insufficient,
    }


def choose_verdict(labels: dict[str, bool]) -> str:
    if labels["source_map_insufficient"]:
        return NULL_VERDICT
    return COMPLETE_VERDICT


def build_report(source_root: Path, expected_sha: str, max_files: int, max_snippets: int) -> dict[str, Any]:
    problems: list[str] = []
    try:
        identity = repository_identity(source_root, expected_sha)
    except (subprocess.CalledProcessError, OSError) as exc:
        identity = {
            "head": None,
            "expected_sha": expected_sha,
            "sha_matches_expected": False,
            "remotes": [],
        }
        problems.append(f"repository_identity_failed:{type(exc).__name__}")

    if not identity.get("sha_matches_expected"):
        problems.append(
            f"sha_mismatch:expected={expected_sha}:actual={identity.get('head')}"
        )

    source_map = scan_source(source_root, max_files=max_files, max_snippets=max_snippets)
    labels = summarize_labels(identity, source_map, problems)
    verdict = choose_verdict(labels)
    instrumentation_points = [
        {
            "path": row["path"],
            "score": row["score"],
            "reason": "metric and collision/proximity source terms co-located",
            "actor_identity_available": row["labels"]["actor_identity_available"],
        }
        for row in source_map["candidate_files"]
        if row["labels"]["instrumentation_candidate"]
    ]
    return {
        "iteration": 55,
        "audit": "hugsim_collision_instrumentation_source_audit",
        "source_root": str(source_root),
        "repository_identity": identity,
        "problems": problems,
        "labels": labels,
        "verdict": verdict,
        "source_map": source_map,
        "instrumentation_points": instrumentation_points,
        "claim_boundary": (
            "source-map only; no HUGSIM run, actor match, safety, transfer, benchmark, "
            "or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    labels = report["labels"]
    identity = report["repository_identity"]
    lines = [
        "# Iteration 55 - HUGSIM collision instrumentation source map",
        "",
        f"Verdict: `{report['verdict']}`",
        "",
        "## Checkout",
        "",
        f"- HEAD: `{identity.get('head')}`",
        f"- Expected: `{identity.get('expected_sha')}`",
        f"- SHA match: `{identity.get('sha_matches_expected')}`",
        "",
        "## Labels",
        "",
    ]
    for key in (
        "metric_source_identified",
        "collision_geometry_source_identified",
        "actor_identity_available_in_source",
        "instrumentation_point_supported",
        "source_map_insufficient",
    ):
        lines.append(f"- `{key}`: `{labels[key]}`")

    if report["problems"]:
        lines.extend(["", "## Problems", ""])
        lines.extend(f"- `{problem}`" for problem in report["problems"])

    lines.extend(["", "## Candidate Instrumentation Points", ""])
    if report["instrumentation_points"]:
        for point in report["instrumentation_points"][:10]:
            actor = point["actor_identity_available"]
            lines.append(f"- `{point['path']}` score `{point['score']}` actor_identity `{actor}`")
    else:
        lines.append("- None identified by the frozen source-text audit.")

    lines.extend(["", "## Ranked Source Files", ""])
    for row in report["source_map"]["candidate_files"][:12]:
        row_labels = row["labels"]
        lines.append(
            f"### `{row['path']}`"
        )
        lines.append("")
        lines.append(
            "- "
            f"score `{row['score']}`, metric `{row_labels['metric_source']}`, "
            f"geometry `{row_labels['collision_geometry_source']}`, "
            f"identity `{row_labels['actor_identity_available']}`"
        )
        for snippet in row["snippets"][:3]:
            terms = ", ".join(snippet["terms"])
            lines.append(f"- line `{snippet['line']}` terms `{terms}`: `{snippet['text']}`")
        lines.append("")

    lines.extend([
        "## Boundary",
        "",
        report["claim_boundary"],
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    source_root: Path,
    out: Path,
    markdown_out: Path,
    expected_sha: str = EXPECTED_HUGSIM_SHA,
    max_files: int = 30,
    max_snippets: int = 4,
) -> dict[str, Any]:
    report = build_report(source_root, expected_sha, max_files=max_files, max_snippets=max_snippets)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter55_hugsim_collision_instrumentation_source_audit/"
            "proof-source/source_map_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter55_hugsim_collision_instrumentation_source_audit/"
            "proof-source/source_map.md"
        ),
    )
    parser.add_argument("--expected-sha", default=EXPECTED_HUGSIM_SHA)
    parser.add_argument("--max-files", type=int, default=30)
    parser.add_argument("--max-snippets", type=int, default=4)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.source_root.resolve(),
        args.out,
        args.markdown_out,
        expected_sha=args.expected_sha,
        max_files=args.max_files,
        max_snippets=args.max_snippets,
    )
    print(json.dumps({"verdict": report["verdict"], "labels": report["labels"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
