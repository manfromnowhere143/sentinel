from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "iter129_support_core_artifact_naming_preflight"
    / "generate_support_core_artifact_naming_preflight.py"
)
SPEC = importlib.util.spec_from_file_location("iter129_naming", MODULE_PATH)
assert SPEC is not None
naming = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(naming)


def test_reserved_paths_are_under_frozen_root() -> None:
    paths = naming.reserved_paths("scbs_demo", "stem_demo")

    assert set(paths) == {"scenario_spec", "provenance_receipt", "validation_manifest"}
    assert all(path.startswith(f"{naming.RESERVED_ROOT}/") for path in paths.values())
    assert all(path.endswith(".json") for path in paths.values())


def test_committed_inputs_build_complete_preflight() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = naming.build_report(
        repo,
        repo / naming.ITER128_REPORT_PATH,
        repo / naming.ITER128_RESULT_PATH,
        repo / naming.ITER128_NOTE_PATH,
        repo / naming.ITER126_REPORT_PATH,
    )

    assert report["verdict"] == naming.COMPLETE_VERDICT
    assert not report["problems"]
    assert report["summary"]["artifact_reservation_count"] == 10
    assert report["summary"]["reserved_relative_path_count"] == 30
    assert report["summary"]["duplicate_reserved_path_count"] == 0
    assert report["summary"]["existing_reserved_path_count"] == 0
    assert report["summary"]["bad_reserved_path_count"] == 0
    assert report["summary"]["true_authorization_count"] == 0


def test_reservations_are_unique_and_nonexistent() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = naming.build_report(
        repo,
        repo / naming.ITER128_REPORT_PATH,
        repo / naming.ITER128_RESULT_PATH,
        repo / naming.ITER128_NOTE_PATH,
        repo / naming.ITER126_REPORT_PATH,
    )
    all_paths = [
        relpath
        for reservation in report["artifact_reservations"]
        for relpath in reservation["reserved_relative_paths"].values()
    ]

    assert len(all_paths) == 30
    assert len(set(all_paths)) == 30
    assert all(not (repo / relpath).exists() for relpath in all_paths)


def test_reservations_are_inert() -> None:
    repo = Path(__file__).resolve().parents[1]
    report = naming.build_report(
        repo,
        repo / naming.ITER128_REPORT_PATH,
        repo / naming.ITER128_RESULT_PATH,
        repo / naming.ITER128_NOTE_PATH,
        repo / naming.ITER126_REPORT_PATH,
    )

    for reservation in report["artifact_reservations"]:
        for field in naming.FALSE_AUTHORIZATION_FIELDS:
            assert reservation[field] is False
        assert naming.check_forbidden_keys(reservation) == []
        assert naming.check_forbidden_text(reservation) == []
