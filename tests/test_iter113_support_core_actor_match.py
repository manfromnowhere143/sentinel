from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter113_hugsim_support_core_actor_match_audit"
    / "analyze_support_core_actor_match.py"
)
SPEC = importlib.util.spec_from_file_location("iter113_actor_match", MODULE_PATH)
assert SPEC is not None
actor_match = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(actor_match)


def _row(label: str, *, problems: list[str] | None = None, design_label: str = "exact") -> dict:
    return {"design_label": design_label, "support_label": label, "problems": problems or []}


def test_support_core_actor_match_verdict_requires_four_classifiable_rows() -> None:
    rows = [_row("classifiable_foreground") for _ in range(3)] + [
        _row("background_collision_only") for _ in range(5)
    ]

    assert actor_match.choose_verdict(rows, []) == actor_match.SUPPORT_NULL_VERDICT

    rows.append(_row("classifiable_foreground"))
    assert actor_match.choose_verdict(rows, []) == actor_match.COMPLETE_VERDICT


def test_support_core_actor_match_verdict_blocks_row_problem() -> None:
    rows = [_row("classifiable_foreground") for _ in range(4)]
    rows.append(_row("parse_failed", problems=["parse-failed"]))

    assert actor_match.choose_verdict(rows, []) == actor_match.INFRA_NULL_VERDICT


def test_support_core_actor_match_crosscheck_blocks_wrong_iter112_verdict() -> None:
    problems: list[str] = []
    actor_match.crosscheck_iter112({"verdict": "wrong", "summary": {}, "slots": []}, [], problems)

    assert "iter112-verdict-mismatch:'wrong'!='HUGSIM_SUPPORT_CORE_BATCH_EXECUTION_COMPLETE'" in problems


def test_iter112_proof_builds_support_core_actor_match_report() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = actor_match.build_report(
        repo
        / "experiments"
        / "iter111_hugsim_support_core_launch_manifest"
        / "proof-launch-manifest"
        / "support_core_launch_manifest.json",
        repo
        / "experiments"
        / "iter112_hugsim_support_core_batch_execution"
        / "proof-execution"
        / "support_core_batch_execution_report.json",
        repo / "experiments" / "iter112_hugsim_support_core_batch_execution" / "proof-execution",
    )

    assert not report["infra_problems"]
    assert len(report["episodes"]) == 8
    assert report["summary"]["completed_rows"] == 8
    assert sum(report["summary"]["support_counts"].values()) == 8
    assert report["summary"]["design_counts"] == {
        "exact_ttc_classifiable_anchor": 3,
        "ttc_classifiable_scenario_analogue": 5,
    }
    assert report["summary"]["iter108_classifiable_baseline"] == 2
    assert report["verdict"] in {
        actor_match.COMPLETE_VERDICT,
        actor_match.SUPPORT_NULL_VERDICT,
    }
