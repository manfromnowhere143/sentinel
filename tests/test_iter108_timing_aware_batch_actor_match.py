from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter108_hugsim_timing_aware_batch_actor_match_audit"
    / "analyze_timing_aware_batch_actor_match.py"
)
SPEC = importlib.util.spec_from_file_location("iter108_actor_match", MODULE_PATH)
assert SPEC is not None
actor_match = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(actor_match)


def _row(label: str, *, problems: list[str] | None = None) -> dict:
    return {"support_label": label, "problems": problems or []}


def test_timing_aware_actor_match_verdict_requires_four_classifiable_rows() -> None:
    rows = [_row("classifiable_foreground") for _ in range(3)] + [_row("no_monitor_fire") for _ in range(10)]

    assert actor_match.choose_verdict(rows, []) == actor_match.SUPPORT_NULL_VERDICT

    rows.append(_row("classifiable_foreground"))
    assert actor_match.choose_verdict(rows, []) == actor_match.COMPLETE_VERDICT


def test_timing_aware_actor_match_verdict_blocks_row_problem() -> None:
    rows = [_row("classifiable_foreground") for _ in range(4)]
    rows.append(_row("parse_failed", problems=["parse-failed"]))

    assert actor_match.choose_verdict(rows, []) == actor_match.INFRA_NULL_VERDICT


def test_timing_aware_actor_match_crosscheck_blocks_wrong_iter107_verdict() -> None:
    problems: list[str] = []
    actor_match.crosscheck_iter107({"verdict": "wrong", "summary": {}, "slots": []}, [], problems)

    assert "iter107-verdict-mismatch:'wrong'!='HUGSIM_TIMING_AWARE_BATCH_EXECUTION_COMPLETE'" in problems


def test_iter107_proof_builds_timing_aware_actor_match_report() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = actor_match.build_report(
        repo
        / "experiments"
        / "iter106_hugsim_timing_aware_launch_manifest"
        / "proof-launch-manifest"
        / "timing_aware_launch_manifest.json",
        repo
        / "experiments"
        / "iter107_hugsim_timing_aware_batch_execution"
        / "proof-execution"
        / "timing_aware_batch_execution_report.json",
        repo / "experiments" / "iter107_hugsim_timing_aware_batch_execution" / "proof-execution",
    )

    assert not report["infra_problems"]
    assert len(report["episodes"]) == 13
    assert report["summary"]["completed_rows"] == 13
    assert sum(report["summary"]["support_counts"].values()) == 13
    assert report["summary"]["iter104_classifiable_baseline"] == 1
    assert report["verdict"] in {
        actor_match.COMPLETE_VERDICT,
        actor_match.SUPPORT_NULL_VERDICT,
    }
