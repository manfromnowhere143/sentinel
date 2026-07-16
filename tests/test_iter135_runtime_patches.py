from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
ITER135 = REPO / "experiments/iter135_neuroncap_blind_braking_dose_response"
UNION = ITER135 / "server_patch_union_release.py"
RELEASED_UNION = REPO / "experiments/iter15_latch_release/server_patch_union_release.py"
BLIND = ITER135 / "server_patch_blind_dose.py"
RELEASED_SHA256 = "d0338d5cee088d2271ee886b86ccac6f03775bf94991b4128013015159b91189"
RISK_TOKENS = (
    "aux_outputs",
    "objects_in_bev",
    "object_scores",
    "future_trajs",
    "object_ids",
    "ego2world",
    "timestamp",
    "SENTINEL_TTC",
    "SENTINEL_CPA_MARGIN",
    "SENTINEL_MIN_CLOSING",
    "SENTINEL_MAXGAP",
    "SENTINEL_MIN_SCORE",
    "SENTINEL_RELEASE_K",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def helper_source(path: Path) -> str:
    tree = ast.parse(path.read_text())
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "HELPERS" for target in node.targets)
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(f"HELPERS assignment missing from {path}")


class FakeTrajectory:
    def __init__(self, rows: list[list[float]]) -> None:
        self.rows = rows

    def tolist(self) -> list[list[float]]:
        return self.rows


class FakeOutput:
    def __init__(self, rows: list[list[float]]) -> None:
        self.trajectory = FakeTrajectory(rows)


def test_union_copy_is_byte_identical_to_released_behavior() -> None:
    assert UNION.read_bytes() == RELEASED_UNION.read_bytes()
    assert sha256(UNION) == RELEASED_SHA256


def test_semantic_leak_guard_discriminates_union_from_blind() -> None:
    union_text = UNION.read_text()
    blind_text = BLIND.read_text()

    assert all(token in union_text for token in RISK_TOKENS)
    assert all(token not in blind_text for token in RISK_TOKENS)
    assert "data." not in blind_text


def test_blind_patch_fires_only_on_frozen_frames(tmp_path: Path) -> None:
    schedule = tmp_path / "dose_schedules.json"
    log = tmp_path / "blind.jsonl"
    schedule.write_text(
        json.dumps(
                {
                    "schema": "iter135.nested_dose_schedules.v1",
                    "schedules": {
                        "blind_1_0x": {
                        "stationary/0099/0": {
                            "brake_frames": [1, 3],
                        }
                    }
                }
            }
        )
    )
    old_env = dict(os.environ)
    os.environ.update(
        {
            "SENTINEL_ENABLED": "1",
            "SENTINEL_LOG": str(log),
            "SENTINEL_DOSE_SCHEDULE": str(schedule),
            "SENTINEL_DOSE_PAIR": "stationary/0099",
            "SENTINEL_DOSE_ID": "blind_1_0x",
        }
    )
    namespace: dict[str, object] = {}
    try:
        exec(helper_source(BLIND), namespace)
        namespace["_sentinel_reset"]()
        out = FakeOutput([[1.0, 0.1], [2.0, 0.2]])
        returned = [namespace["_sentinel_intervene"](out) for _ in range(5)]
    finally:
        os.environ.clear()
        os.environ.update(old_env)

    assert returned == [
        [[1.0, 0.1], [2.0, 0.2]],
        [[0.0, 0.0], [0.0, 0.0]],
        [[1.0, 0.1], [2.0, 0.2]],
        [[0.0, 0.0], [0.0, 0.0]],
        [[1.0, 0.1], [2.0, 0.2]],
    ]
    rows = [json.loads(line) for line in log.read_text().splitlines()]
    frame_rows = [row for row in rows if row.get("frame")]
    assert [row["frame_index"] for row in frame_rows] == list(range(5))
    assert all(row["class"] == "stationary" for row in frame_rows)
    assert all(row["pair"] == "0099" for row in frame_rows)
    assert all(row["dose"] == "blind_1_0x" for row in frame_rows)
    assert all(row["base_trajectory"] == [[1.0, 0.1], [2.0, 0.2]] for row in frame_rows)
    assert [row["returned_trajectory"] for row in frame_rows] == returned
    assert [row["frame_index"] for row in rows if row.get("brake")] == [1, 3]


def test_block_reset_advances_to_the_next_frozen_run(tmp_path: Path) -> None:
    schedule = tmp_path / "dose_schedules.json"
    log = tmp_path / "blind.jsonl"
    schedule.write_text(
        json.dumps(
            {
                "schema": "iter135.nested_dose_schedules.v1",
                "schedules": {
                    "blind_2_0x": {
                        "side/0921/0": {"brake_frames": [0]},
                        "side/0921/1": {"brake_frames": [1]},
                    }
                },
            }
        )
    )
    old_env = dict(os.environ)
    os.environ.update(
        {
            "SENTINEL_ENABLED": "1",
            "SENTINEL_LOG": str(log),
            "SENTINEL_DOSE_SCHEDULE": str(schedule),
            "SENTINEL_DOSE_PAIR": "side/0921",
            "SENTINEL_DOSE_ID": "blind_2_0x",
        }
    )
    namespace: dict[str, object] = {}
    try:
        exec(helper_source(BLIND), namespace)
        namespace["_sentinel_reset"]()
        out = FakeOutput([[1.0, -0.1]])
        first = namespace["_sentinel_intervene"](out)
        namespace["_sentinel_reset"]()
        second = [namespace["_sentinel_intervene"](out) for _ in range(2)]
    finally:
        os.environ.clear()
        os.environ.update(old_env)

    assert first == [[0.0, 0.0]]
    assert second == [[[1.0, -0.1]], [[0.0, 0.0]]]
    rows = [json.loads(line) for line in log.read_text().splitlines()]
    assert [row["run"] for row in rows if row.get("reset")] == [0, 1]
    assert [row["frame_index"] for row in rows if row.get("brake")] == [0, 1]


def test_missing_schedule_logs_identity_and_fails_closed(tmp_path: Path) -> None:
    schedule = tmp_path / "dose_schedules.json"
    log = tmp_path / "blind.jsonl"
    schedule.write_text(json.dumps({"schedules": {}}))
    old_env = dict(os.environ)
    os.environ.update(
        {
            "SENTINEL_ENABLED": "1",
            "SENTINEL_LOG": str(log),
            "SENTINEL_DOSE_SCHEDULE": str(schedule),
            "SENTINEL_DOSE_PAIR": "side/0921",
            "SENTINEL_DOSE_ID": "blind_2_0x",
        }
    )
    namespace: dict[str, object] = {}
    try:
        exec(helper_source(BLIND), namespace)
        namespace["_sentinel_reset"]()
        out = FakeOutput([[1.0, -0.1]])
        try:
            namespace["_sentinel_intervene"](out)
        except RuntimeError as exc:
            assert "schedule row missing" in str(exc)
        else:
            raise AssertionError("missing frozen schedule passed through")
    finally:
        os.environ.clear()
        os.environ.update(old_env)

    rows = [json.loads(line) for line in log.read_text().splitlines()]
    missing = [row for row in rows if row.get("schedule_missing")]
    assert missing == [
        {
            "class": "side",
            "dose": "blind_2_0x",
            "frame_index": 0,
            "pair": "0921",
            "run": 0,
            "schedule_key": "side/0921/0",
            "schedule_missing": True,
        }
    ]
