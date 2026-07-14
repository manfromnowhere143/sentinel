from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter104_hugsim_provenance_batch_actor_match_audit"
    / "analyze_provenance_batch_actor_match.py"
)
SPEC = importlib.util.spec_from_file_location("iter104_actor_match", MODULE_PATH)
assert SPEC is not None
actor_match = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(actor_match)


def _row(label: str, *, problems: list[str] | None = None) -> dict:
    return {"support_label": label, "problems": problems or []}


def test_actor_match_verdict_requires_four_classifiable_rows() -> None:
    rows = [_row("classifiable_foreground") for _ in range(3)] + [_row("no_monitor_fire") for _ in range(10)]

    assert actor_match.choose_verdict(rows, []) == actor_match.SUPPORT_NULL_VERDICT

    rows.append(_row("classifiable_foreground"))
    assert actor_match.choose_verdict(rows, []) == actor_match.COMPLETE_VERDICT


def test_actor_match_verdict_blocks_row_problem() -> None:
    rows = [_row("classifiable_foreground") for _ in range(4)]
    rows.append(_row("parse_failed", problems=["parse-failed"]))

    assert actor_match.choose_verdict(rows, []) == actor_match.INFRA_NULL_VERDICT


def test_iter103_proof_builds_actor_match_report() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = actor_match.build_report(
        repo
        / "experiments"
        / "iter102_hugsim_provenance_batch_launch_manifest"
        / "proof-launch-manifest"
        / "provenance_batch_launch_manifest.json",
        repo
        / "experiments"
        / "iter103_hugsim_provenance_batch_execution"
        / "proof-execution"
        / "provenance_batch_execution_report.json",
        repo / "experiments" / "iter103_hugsim_provenance_batch_execution" / "proof-execution",
    )

    assert not report["infra_problems"]
    assert len(report["episodes"]) == 13
    assert report["summary"]["completed_rows"] == 13
    assert sum(report["summary"]["support_counts"].values()) == 13
    assert report["verdict"] in {
        actor_match.COMPLETE_VERDICT,
        actor_match.SUPPORT_NULL_VERDICT,
    }
