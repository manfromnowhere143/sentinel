#!/usr/bin/env python3
"""Iteration 47 offline analyzer — full-52 completion gate over carried + new episodes.

Runs ONCE, offline, after `I47_OFF_COMPLETION_DONE` evidence is collected and committed.
It (1) verifies carried-episode integrity — the 38 iteration-46 episodes still on the box
must be byte-identical (eval.json + episode_meta.json SHA256) to the committed iteration-46
artifacts, and the 14 newly collected episodes must match their on-box hashes; then
(2) assembles the full 52-episode stochastic schedule (38 carried from the committed
iteration-46 proof + 14 new from this iteration's collection) and evaluates it with ONE run
of the committed iteration-46 analyzer (same C1/C2 bars, same falsifiers, pairing
re-evaluated over all 26 pairs). No new claim logic beyond the registered bars.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ITER46 = HERE.parent / "iter46_hugsim_off_baseline"
DEFAULT_ITER46_EPISODES = ITER46 / "proof-off" / "episodes"

FAILED_SCENARIOS: list[str] = [
    "scene-0038-medium-01",
    "scene-0051-medium-01",
    "scene-0062-medium-01",
    "scene-0064-medium-01",
    "scene-0071-medium-01",
    "scene-0138-medium-01",
    "scene-0166-medium-01",
]
NEW_EPISODES: list[tuple[str, int]] = [(s, r) for s in FAILED_SCENARIOS for r in (1, 2)]
INTEGRITY_FILES = ("eval.json", "episode_meta.json")


def load_iter46_analyzer():
    spec = importlib.util.spec_from_file_location(
        "iter46_analyzer", ITER46 / "analyze_off_baseline.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def carried_episodes(analyzer46) -> list[tuple[str, int]]:
    sched = analyzer46.scheduled_episodes("stochastic")
    return [(s, r) for s, r in sched if (s, r) not in set(NEW_EPISODES)]


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_box_hashes(path: Path) -> dict[str, str]:
    """Parse `sha256sum`-style lines: `<sha>  <relative path>` -> {normalized path: sha}."""
    out: dict[str, str] = {}
    for line in path.read_text().splitlines():
        parts = line.split(None, 1)
        if len(parts) != 2 or len(parts[0]) != 64:
            continue
        rel = parts[1].strip().lstrip("./")
        out[rel] = parts[0]
    return out


def check_integrity(box_hashes: dict[str, str], iter46_episodes: Path,
                    new_episodes: Path, carried: list[tuple[str, int]]) -> dict:
    """Carried dirs must match the committed iter46 bytes; new dirs must match the box.

    A new episode whose dir is absent locally (e.g. it failed both attempts on the box and
    only a __failed dir exists) is a COMPLETION failure judged by C1, not an integrity
    mismatch; integrity for new episodes applies only to files that were collected.
    """
    mismatches: list[dict] = []
    checked = 0
    for source_root, pairs, label in (
        (iter46_episodes, carried, "carried"),
        (new_episodes, NEW_EPISODES, "new"),
    ):
        for scenario, run in pairs:
            ep_dir = source_root / f"{scenario}__r{run}"
            if label == "new" and not ep_dir.is_dir():
                continue  # completion (C1) judges absent new episodes
            for fname in INTEGRITY_FILES:
                rel = f"{scenario}__r{run}/{fname}"
                local = source_root / rel
                checked += 1
                if not local.is_file():
                    mismatches.append({"file": rel, "kind": label, "reason": "local-missing"})
                    continue
                box = box_hashes.get(rel)
                if box is None:
                    mismatches.append({"file": rel, "kind": label, "reason": "box-hash-missing"})
                elif box != sha256_of(local):
                    mismatches.append({"file": rel, "kind": label, "reason": "sha-mismatch"})
    return {"files_checked": checked, "mismatches": mismatches,
            "pass": not mismatches}


def assemble_and_analyze(analyzer46, iter46_episodes: Path, new_episodes: Path) -> dict:
    carried = carried_episodes(analyzer46)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        shutil.copy2(iter46_episodes / "d0_comparison.json", root / "d0_comparison.json")
        for scenario, run in carried:
            src = iter46_episodes / f"{scenario}__r{run}"
            if src.is_dir():
                shutil.copytree(src, root / src.name)
        for scenario, run in NEW_EPISODES:
            src = new_episodes / f"{scenario}__r{run}"
            if src.is_dir():
                shutil.copytree(src, root / src.name)
            fail_src = new_episodes / f"{scenario}__r{run}__failed"
            if fail_src.is_dir():
                shutil.copytree(fail_src, root / fail_src.name)
        return analyzer46.analyze(root)


def analyze_completion(iter46_episodes: Path, new_episodes: Path,
                       box_hashes_path: Path) -> dict:
    analyzer46 = load_iter46_analyzer()
    carried = carried_episodes(analyzer46)
    report: dict = {
        "schedule": {
            "carried_episodes": len(carried),
            "new_episodes": len(NEW_EPISODES),
            "new_scenarios": FAILED_SCENARIOS,
        },
    }
    report["carried_integrity"] = check_integrity(
        parse_box_hashes(box_hashes_path), iter46_episodes, new_episodes, carried)
    full = assemble_and_analyze(analyzer46, iter46_episodes, new_episodes)
    report["full_52"] = full
    if not report["carried_integrity"]["pass"]:
        report["verdict"] = "NULL_CARRIED_INTEGRITY"
    else:
        report["verdict"] = full["verdict"]
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--iter46-episodes", default=str(DEFAULT_ITER46_EPISODES))
    ap.add_argument("--new-episodes", required=True,
                    help="proof-completion/episodes with the 14 new episode dirs")
    ap.add_argument("--box-hashes", required=True,
                    help="sha256sum output over eval.json/episode_meta.json for all 52 on-box dirs")
    ap.add_argument("--out", required=True)
    ap.add_argument("--markdown-out", help="optional per-episode markdown table")
    args = ap.parse_args()
    report = analyze_completion(
        Path(args.iter46_episodes), Path(args.new_episodes), Path(args.box_hashes))
    Path(args.out).write_text(json.dumps(report, indent=2, default=str) + "\n")
    if args.markdown_out:
        analyzer46 = load_iter46_analyzer()
        Path(args.markdown_out).write_text(
            analyzer46.render_markdown(report["full_52"]) + "\n")
    print(f"iter47 analyzer verdict: {report['verdict']}")
    print(f"carried integrity: {report['carried_integrity']['pass']} "
          f"({report['carried_integrity']['files_checked']} files)")
    print(f"full-52 bars: {report['full_52'].get('bars')}")
    if "hdscore" in report["full_52"]:
        print(f"hdscore aggregate: {report['full_52']['hdscore']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
