"""Hostile gates for the Iteration-135 union extractor and nested dose schedules."""

from __future__ import annotations

from copy import deepcopy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments" / "iter135_neuroncap_blind_braking_dose_response"
I134_PROOF = ROOT / "experiments" / "iter134_neuroncap_placebo_semantics_execution" / "proof"
PARTS = [
    I134_PROOF / "sentinel_i134_union.jsonl.gz.part-aa",
    I134_PROOF / "sentinel_i134_union.jsonl.gz.part-ab",
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


EXTRACT = load_module("iter135_extract_union_windows_test", EXP / "extract_union_windows.py")
GENERATE = load_module(
    "iter135_generate_nested_dose_schedules_test", EXP / "generate_nested_dose_schedules.py"
)
SCHEDULES = json.loads((EXP / "dose_schedules.json").read_text(encoding="utf-8"))


def _frame(run: int, ts: int) -> dict:
    return {"run": run, "ts": ts, "traj": [], "objs": [], "scores": [], "futs": []}


def _brake(run: int) -> dict:
    return {"run": run, "brake": True, "clear": 0, "cpa": 1.0, "ttc": 2.0}


def _release(run: int) -> dict:
    return {"run": run, "release": True, "cpa": 2.0, "ttc": 3.0}


def _write_split_gzip(tmp_path: Path, rows: list[dict], split: int | None = None) -> list[Path]:
    payload = ("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n").encode()
    compressed = gzip.compress(payload, mtime=0)
    split = split if split is not None else max(1, len(compressed) // 2 + 3)
    first = tmp_path / "source.jsonl.gz.part-aa"
    second = tmp_path / "source.jsonl.gz.part-ab"
    first.write_bytes(compressed[:split])
    second.write_bytes(compressed[split:])
    return [first, second]


def test_split_gzip_parser_joins_arbitrary_shards_in_lexical_order(tmp_path):
    rows = [
        {"reset": True, "run": 0},
        _frame(0, 10),
        _brake(0),
        _frame(0, 20),
        _release(0),
        _frame(0, 30),
        _brake(0),
        {"reset": True, "run": 1},
        _frame(1, 40),
    ]
    parts = _write_split_gzip(tmp_path, rows, split=11)
    blocks, canonical = EXTRACT.read_blocks(reversed(parts))

    assert canonical == parts
    assert blocks == [
        {
            "log_run": 0,
            "frame_count": 3,
            "brake_frames": [0, 2],
            "brake_row_count": 2,
            "release_row_count": 1,
            "brake_windows": [[0], [2]],
        },
        {
            "log_run": 1,
            "frame_count": 1,
            "brake_frames": [],
            "brake_row_count": 0,
            "release_row_count": 0,
            "brake_windows": [],
        },
    ]


def test_split_gzip_parser_rejects_truncation_and_duplicate_parts(tmp_path):
    rows = [{"reset": True, "run": 0}, _frame(0, 10)]
    parts = _write_split_gzip(tmp_path, rows)
    parts[1].write_bytes(parts[1].read_bytes()[:-5])
    with pytest.raises(EXTRACT.UnionLogError, match="gzip"):
        EXTRACT.read_blocks(parts)
    with pytest.raises(EXTRACT.UnionLogError, match="duplicate"):
        EXTRACT.read_blocks([parts[0], parts[0]])


def test_split_gzip_parser_rejects_malformed_and_semantically_unknown_rows(tmp_path):
    bad_json = gzip.compress(b'{"reset":true,"run":0}\nnot-json\n', mtime=0)
    path = tmp_path / "bad.jsonl.gz.part-aa"
    path.write_bytes(bad_json)
    with pytest.raises(EXTRACT.UnionLogError, match="invalid JSON"):
        EXTRACT.read_blocks([path])

    parts = _write_split_gzip(
        tmp_path,
        [{"reset": True, "run": 0}, _frame(0, 10), {"run": 0, "mystery": True}],
    )
    with pytest.raises(EXTRACT.UnionLogError, match="unknown union-log row"):
        EXTRACT.read_blocks(parts)


def test_split_gzip_parser_rejects_run_leak_and_duplicate_brake_frame(tmp_path):
    parts = _write_split_gzip(
        tmp_path,
        [{"reset": True, "run": 0}, _frame(0, 10), _brake(0), _brake(0)],
    )
    with pytest.raises(EXTRACT.UnionLogError, match="duplicate brake frame"):
        EXTRACT.read_blocks(parts)

    parts = _write_split_gzip(
        tmp_path,
        [{"reset": True, "run": 0}, _frame(1, 10)],
    )
    with pytest.raises(EXTRACT.UnionLogError, match="run mismatch"):
        EXTRACT.read_blocks(parts)


def _independent_hash(cls, target_seq, target_run, donor_seq, donor_run, frame):
    value = (
        f"iter135.blind_dose.v1|{cls}|{target_seq}|{target_run}|"
        f"{donor_seq}|{donor_run}|{frame}"
    )
    return hashlib.sha256(value.encode()).hexdigest()


def test_candidate_order_implements_anchor_windows_distance_and_sha_ties():
    kwargs = {
        "cls": "stationary",
        "target_seq": "0099",
        "target_run": 0,
        "donor_seq": "0103",
        "donor_run": 7,
        "donor_frame_count": 10,
        "donor_brake_frames": [1, 2, 3, 7, 8],
    }
    observed = GENERATE.ordered_candidate_frames(**kwargs)
    hash_for = lambda frame: _independent_hash(  # noqa: E731
        "stationary", "0099", 0, "0103", 7, frame
    )

    assert observed[0] == 3  # nearest brake to the all-brake median
    expected_remaining_brakes = sorted(
        [1, 2, 7, 8], key=lambda frame: ({1: 1, 2: 0, 7: 0.5, 8: 0.5}[frame], hash_for(frame))
    )
    assert observed[1:5] == expected_remaining_brakes
    expected_non_brakes = sorted(
        [0, 4, 5, 6, 9],
        key=lambda frame: (
            min(abs(frame - brake) for brake in [1, 2, 3, 7, 8]),
            hash_for(frame),
        ),
    )
    assert observed[5:] == expected_non_brakes
    assert sorted(observed) == list(range(10))


def test_zero_brake_candidate_order_is_sha_order_over_entire_horizon():
    observed = GENERATE.ordered_candidate_frames(
        cls="side",
        target_seq="0103",
        target_run=19,
        donor_seq="0110",
        donor_run=6,
        donor_frame_count=8,
        donor_brake_frames=[],
    )
    expected = sorted(
        range(8),
        key=lambda frame: _independent_hash("side", "0103", 19, "0110", 6, frame),
    )
    assert observed == expected


def test_candidate_order_rejects_duplicate_or_out_of_horizon_source_brakes():
    base = {
        "cls": "frontal",
        "target_seq": "0103",
        "target_run": 0,
        "donor_seq": "0110",
        "donor_run": 7,
        "donor_frame_count": 5,
    }
    with pytest.raises(GENERATE.ScheduleError, match="unique"):
        GENERATE.ordered_candidate_frames(**base, donor_brake_frames=[1, 1])
    with pytest.raises(GENERATE.ScheduleError, match="outside horizon"):
        GENERATE.ordered_candidate_frames(**base, donor_brake_frames=[5])


def test_committed_schedule_binds_exact_frozen_source_and_budgets():
    assert SCHEDULES["schema"] == "iter135.nested_dose_schedules.v1"
    assert SCHEDULES["verdict"] == "NESTED_DOSE_SCHEDULES_OK"
    assert SCHEDULES["problem_count"] == 0
    assert SCHEDULES["source"]["source_joined_sha256"] == (
        "f06178aba6d7b5fd7424469891795f039eca65dd8eb4942f0b0706ccd838a21c"
    )
    assert [row["sha256"] for row in SCHEDULES["source"]["source_log_parts"]] == [
        "4a4b90a383613ebd228a24b510d59f2214695a3a020858d082187f1e507ffb85",
        "93a39b950789c1416055e32ea2056e3a9f8202f14f885b4f789458f4d8b4ca97",
    ]
    assert SCHEDULES["source"]["totals"] == {
        "frame_rows": 6474,
        "brake_rows": 1205,
        "release_rows": 156,
        "braking_windows": 265,
        "zero_brake_episodes": 170,
    }
    assert GENERATE.expected_budgets() == GENERATE.FROZEN_BUDGETS == {
        "blind_0_5x": {"stationary": 208, "frontal": 238, "side": 157},
        "blind_1_0x": {"stationary": 416, "frontal": 475, "side": 314},
        "blind_1_5x": {"stationary": 624, "frontal": 713, "side": 471},
        "blind_2_0x": {"stationary": 832, "frontal": 950, "side": 628},
    }


def test_committed_schedule_has_nested_runtime_keys_and_exact_q2_j7_bijection():
    assert SCHEDULES["schedule_count"] == 1600
    assert set(SCHEDULES["schedules"]) == set(GENERATE.DOSES)
    assert all(len(SCHEDULES["schedules"][dose]) == 400 for dose in GENERATE.DOSES)
    donors_by_class = {cls: set() for cls in GENERATE.CLASSES}
    for cls in GENERATE.CLASSES:
        for pair_index, seq in enumerate(GENERATE.CLASS_SEQS[cls]):
            expected_donor_seq = GENERATE.CLASS_SEQS[cls][
                (pair_index + 2) % len(GENERATE.CLASS_SEQS[cls])
            ]
            for run in range(GENERATE.RUNS):
                expected_donor = (expected_donor_seq, (run + 7) % GENERATE.RUNS)
                donors_by_class[cls].add(expected_donor)
                for dose in GENERATE.DOSES:
                    key = f"{cls}/{seq}/{run}"
                    row = SCHEDULES["schedules"][dose][key]
                    assert (row["donor_seq"], row["donor_run"]) == expected_donor
                    assert row["donor_seq"] != seq
                    assert row["donor_run"] != run
        assert len(donors_by_class[cls]) == len(GENERATE.CLASS_SEQS[cls]) * GENERATE.RUNS


def test_every_schedule_is_supported_unique_bounded_and_nested():
    for cls in GENERATE.CLASSES:
        for seq in GENERATE.CLASS_SEQS[cls]:
            for run in range(GENERATE.RUNS):
                previous = set()
                for dose in GENERATE.DOSES:
                    row = SCHEDULES["schedules"][dose][f"{cls}/{seq}/{run}"]
                    frames = row["brake_frames"]
                    assert frames
                    assert frames == sorted(set(frames))
                    assert row["scheduled_brake_count"] == len(frames)
                    assert all(0 <= frame < row["donor_frame_count"] for frame in frames)
                    assert previous <= set(frames)
                    previous = set(frames)


def test_class_global_budgets_are_exact_and_round_robin_support_is_complete():
    for dose in GENERATE.DOSES:
        for cls in GENERATE.CLASSES:
            rows = [
                row
                for key, row in SCHEDULES["schedules"][dose].items()
                if key.startswith(f"{cls}/")
            ]
            assert len(rows) == len(GENERATE.CLASS_SEQS[cls]) * GENERATE.RUNS
            assert sum(row["scheduled_brake_count"] for row in rows) == (
                GENERATE.FROZEN_BUDGETS[dose][cls]
            )
            assert all(row["scheduled_brake_count"] >= 1 for row in rows)
            assert SCHEDULES["class_summary"][cls]["supported_schedule_count"][dose] == len(rows)


def test_validator_recomputes_the_exact_master_prefix():
    assert GENERATE.validate_schedule_report(SCHEDULES) == []

    dose = "blind_1_0x"
    key = "stationary/0099/0"
    mutated = deepcopy(SCHEDULES)
    mutated["schedules"][dose][key]["brake_frames"].pop()
    mutated["schedules"][dose][key]["scheduled_brake_count"] -= 1
    problems = GENERATE.validate_schedule_report(mutated)
    assert f"master-prefix:{dose}/{key}" in problems
    assert any(problem.startswith("class-budget:blind_1_0x/stationary") for problem in problems)


@pytest.mark.parametrize(
    ("mutation", "expected_problem"),
    [
        ("donor_pair", "donor-pair:blind_0_5x/stationary/0099/0"),
        ("outside_horizon", "brake-horizon:blind_0_5x/stationary/0099/0"),
        ("duplicate_frame", "brake-unique-order:blind_0_5x/stationary/0099/0"),
        (
            "missing_schedule",
            "schedule-target-keys:blind_0_5x:missing=1:extra=0",
        ),
    ],
)
def test_validator_fails_closed_on_hostile_schedule_mutations(mutation, expected_problem):
    dose = "blind_0_5x"
    target = "stationary/0099/0"
    mutated = deepcopy(SCHEDULES)
    row = mutated["schedules"][dose][target]
    if mutation == "donor_pair":
        row["donor_seq"] = row["target_seq"]
    elif mutation == "outside_horizon":
        row["brake_frames"] = [row["donor_frame_count"]]
        row["scheduled_brake_count"] = 1
    elif mutation == "duplicate_frame":
        row["brake_frames"] = [row["brake_frames"][0], row["brake_frames"][0]]
        row["scheduled_brake_count"] = 2
    elif mutation == "missing_schedule":
        del mutated["schedules"][dose][target]
    else:  # pragma: no cover - the parameter list is frozen above
        raise AssertionError(mutation)
    assert expected_problem in GENERATE.validate_schedule_report(mutated)


def test_generator_reproduces_committed_schedule_from_split_proof(monkeypatch):
    monkeypatch.chdir(ROOT)
    relative_parts = [part.relative_to(ROOT) for part in PARTS]
    source = EXTRACT.extract_union_windows(reversed(relative_parts))
    assert source["verdict"] == "UNION_WINDOWS_OK"
    regenerated = GENERATE.generate_nested_dose_schedules(source)
    assert regenerated == SCHEDULES
