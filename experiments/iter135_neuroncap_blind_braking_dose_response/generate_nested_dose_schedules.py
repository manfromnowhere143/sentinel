#!/usr/bin/env python3
"""Generate the frozen Iteration-135 supported, nested blind-braking schedules.

The source union log is parsed by ``extract_union_windows.py``.  This generator applies only the
pre-registered q+2/j+7 donor bijection, candidate ordering, class-global round-half-up budgets,
and prefix selection.  It has no access to target-arm outcomes.

Runtime lookup is ``schedules[dose_id]["class/seq/run"]["brake_frames"]``.

Usage:
    generate_nested_dose_schedules.py OUT.json UNION.jsonl.gz.part-aa [part-ab ...]
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys
from typing import Mapping, Sequence


CLASS_SEQS = {
    "stationary": [
        "0099",
        "0101",
        "0103",
        "0106",
        "0108",
        "0278",
        "0331",
        "0783",
        "0796",
        "0966",
    ],
    "frontal": ["0103", "0106", "0110", "0346", "0923"],
    "side": ["0103", "0108", "0110", "0278", "0921"],
}
CLASSES = ["stationary", "frontal", "side"]
RUNS = 20
DOSES = ["blind_0_5x", "blind_1_0x", "blind_1_5x", "blind_2_0x"]
DOSE_MULTIPLIERS = {
    "blind_0_5x": Decimal("0.5"),
    "blind_1_0x": Decimal("1.0"),
    "blind_1_5x": Decimal("1.5"),
    "blind_2_0x": Decimal("2.0"),
}
UNION_CLASS_BRAKE_ROWS = {"stationary": 416, "frontal": 475, "side": 314}
UNION_CLASS_HORIZON_FRAMES = {"stationary": 3624, "frontal": 1347, "side": 1503}
FROZEN_BUDGETS = {
    "blind_0_5x": {"stationary": 208, "frontal": 238, "side": 157},
    "blind_1_0x": {"stationary": 416, "frontal": 475, "side": 314},
    "blind_1_5x": {"stationary": 624, "frontal": 713, "side": 471},
    "blind_2_0x": {"stationary": 832, "frontal": 950, "side": 628},
}

SCHEMA = "iter135.nested_dose_schedules.v1"
TIE_DOMAIN = "iter135.blind_dose.v1"
EXPECTED_SOURCE_SCHEMA = "iter135.union_windows.v1"
EXPECTED_SOURCE_PART_SHA256 = [
    "4a4b90a383613ebd228a24b510d59f2214695a3a020858d082187f1e507ffb85",
    "93a39b950789c1416055e32ea2056e3a9f8202f14f885b4f789458f4d8b4ca97",
]
EXPECTED_SOURCE_JOINED_SHA256 = (
    "f06178aba6d7b5fd7424469891795f039eca65dd8eb4942f0b0706ccd838a21c"
)
EXPECTED_SOURCE_TOTALS = {
    "frame_rows": 6474,
    "brake_rows": 1205,
    "release_rows": 156,
    "braking_windows": 265,
    "zero_brake_episodes": 170,
}
EXPECTED_SOURCE_PER_CLASS = {
    "stationary": {
        "episodes": 200,
        "frame_rows": 3624,
        "brake_rows": 416,
        "release_rows": 80,
        "braking_windows": 109,
        "zero_brake_episodes": 126,
    },
    "frontal": {
        "episodes": 100,
        "frame_rows": 1347,
        "brake_rows": 475,
        "release_rows": 18,
        "braking_windows": 92,
        "zero_brake_episodes": 8,
    },
    "side": {
        "episodes": 100,
        "frame_rows": 1503,
        "brake_rows": 314,
        "release_rows": 58,
        "braking_windows": 64,
        "zero_brake_episodes": 36,
    },
}
EXPECTED_DONOR_RULE = {
    "pair": "q=(p+2)%len(class)",
    "run": "j=(i+7)%20",
    "class_preserving": True,
    "target_pair_excluded": True,
    "target_run_excluded": True,
}


class ScheduleError(ValueError):
    """A source inventory or generated schedule violates the frozen contract."""


def round_half_up_budget(base: int, multiplier: Decimal) -> int:
    return int((Decimal(base) * multiplier).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def expected_budgets() -> dict[str, dict[str, int]]:
    return {
        dose: {
            cls: round_half_up_budget(UNION_CLASS_BRAKE_ROWS[cls], DOSE_MULTIPLIERS[dose])
            for cls in CLASSES
        }
        for dose in DOSES
    }


def tie_hash(
    cls: str,
    target_seq: str,
    target_run: int,
    donor_seq: str,
    donor_run: int,
    frame: int,
) -> str:
    payload = (
        f"{TIE_DOMAIN}|{cls}|{target_seq}|{target_run}|{donor_seq}|{donor_run}|{frame}"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _contiguous_windows(frames: Sequence[int]) -> list[list[int]]:
    if not frames:
        return []
    ordered = sorted(frames)
    if len(ordered) != len(set(ordered)):
        raise ScheduleError("donor brake frames are not unique")
    windows = [[ordered[0]]]
    for frame in ordered[1:]:
        if frame == windows[-1][-1] + 1:
            windows[-1].append(frame)
        else:
            windows.append([frame])
    return windows


def ordered_candidate_frames(
    *,
    cls: str,
    target_seq: str,
    target_run: int,
    donor_seq: str,
    donor_run: int,
    donor_frame_count: int,
    donor_brake_frames: Sequence[int],
) -> list[int]:
    """Return the exact per-target candidate order frozen in HYPOTHESIS.md."""
    if not isinstance(donor_frame_count, int) or isinstance(donor_frame_count, bool):
        raise ScheduleError("donor frame count must be an integer")
    if donor_frame_count <= 0:
        raise ScheduleError("donor horizon must be positive")
    if any(not isinstance(frame, int) or isinstance(frame, bool) for frame in donor_brake_frames):
        raise ScheduleError("donor brake frames must be integers")
    brake_frames = sorted(donor_brake_frames)
    if len(brake_frames) != len(set(brake_frames)):
        raise ScheduleError("donor brake frames are not unique")
    if any(frame < 0 or frame >= donor_frame_count for frame in brake_frames):
        raise ScheduleError("donor brake frame outside horizon")

    hash_for = lambda frame: tie_hash(  # noqa: E731 - the frozen tuple belongs next to its use
        cls, target_seq, target_run, donor_seq, donor_run, frame
    )
    all_frames = list(range(donor_frame_count))
    if not brake_frames:
        return sorted(all_frames, key=hash_for)

    overall_median = statistics.median(brake_frames)
    anchor = min(brake_frames, key=lambda frame: (abs(frame - overall_median), hash_for(frame)))

    window_median_by_frame = {}
    for window in _contiguous_windows(brake_frames):
        window_median = statistics.median(window)
        for frame in window:
            window_median_by_frame[frame] = window_median

    remaining_brakes = sorted(
        (frame for frame in brake_frames if frame != anchor),
        key=lambda frame: (abs(frame - window_median_by_frame[frame]), hash_for(frame)),
    )
    brake_set = set(brake_frames)
    non_brakes = sorted(
        (frame for frame in all_frames if frame not in brake_set),
        key=lambda frame: (min(abs(frame - brake) for brake in brake_frames), hash_for(frame)),
    )
    candidates = [anchor, *remaining_brakes, *non_brakes]
    if len(candidates) != donor_frame_count or len(set(candidates)) != donor_frame_count:
        raise ScheduleError("candidate order is not a horizon permutation")
    return candidates


def donor_identity(cls: str, target_seq: str, target_run: int) -> tuple[str, int]:
    seqs = CLASS_SEQS[cls]
    pair_index = seqs.index(target_seq)
    return seqs[(pair_index + 2) % len(seqs)], (target_run + 7) % RUNS


def _candidate_record(
    cls: str,
    target_seq: str,
    target_run: int,
    donor_seq: str,
    donor_run: int,
    ordinal: int,
    frame: int,
) -> dict:
    return {
        "target_seq": target_seq,
        "target_run": target_run,
        "donor_seq": donor_seq,
        "donor_run": donor_run,
        "ordinal": ordinal,
        "frame": frame,
        "tie_hash": tie_hash(
            cls, target_seq, target_run, donor_seq, donor_run, frame
        ),
    }


def _master_order(cls: str, target_sources: Mapping[tuple[str, int], dict]) -> list[dict]:
    candidates = []
    for target_seq in CLASS_SEQS[cls]:
        for target_run in range(RUNS):
            source = target_sources[(target_seq, target_run)]
            ordered = ordered_candidate_frames(
                cls=cls,
                target_seq=target_seq,
                target_run=target_run,
                donor_seq=source["donor_seq"],
                donor_run=source["donor_run"],
                donor_frame_count=source["donor_frame_count"],
                donor_brake_frames=source["donor_brake_frames"],
            )
            for ordinal, frame in enumerate(ordered):
                candidates.append(
                    _candidate_record(
                        cls,
                        target_seq,
                        target_run,
                        source["donor_seq"],
                        source["donor_run"],
                        ordinal,
                        frame,
                    )
                )
    candidates.sort(key=lambda row: (row["ordinal"], row["tie_hash"]))
    if len({row["tie_hash"] for row in candidates}) != len(candidates):
        raise ScheduleError(f"SHA-256 tie collision in {cls}")
    identities = [(row["target_seq"], row["target_run"], row["frame"]) for row in candidates]
    if len(identities) != len(set(identities)):
        raise ScheduleError(f"duplicate master candidate in {cls}")
    return candidates


def _master_sha256(master_order: Sequence[dict]) -> str:
    payload = json.dumps(master_order, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _source_target_rows(source_report: Mapping) -> dict[str, dict[tuple[str, int], dict]]:
    if source_report.get("verdict") != "UNION_WINDOWS_OK":
        raise ScheduleError("union-window source is not valid")
    if source_report.get("schema") != EXPECTED_SOURCE_SCHEMA:
        raise ScheduleError("union-window source schema drift")
    if source_report.get("source_joined_sha256") != EXPECTED_SOURCE_JOINED_SHA256:
        raise ScheduleError("union-window joined SHA256 drift")
    source_parts = source_report.get("source_log_parts")
    if not isinstance(source_parts, list) or [
        row.get("sha256") if isinstance(row, dict) else None for row in source_parts
    ] != EXPECTED_SOURCE_PART_SHA256:
        raise ScheduleError("union-window part SHA256 drift")
    if source_report.get("totals") != EXPECTED_SOURCE_TOTALS:
        raise ScheduleError("union-window source totals drift")
    if source_report.get("per_class") != EXPECTED_SOURCE_PER_CLASS:
        raise ScheduleError("union-window class totals drift")
    if source_report.get("block_count") != sum(len(seqs) for seqs in CLASS_SEQS.values()) * RUNS:
        raise ScheduleError("union-window source block count drift")
    episodes = source_report.get("episodes")
    if not isinstance(episodes, dict):
        raise ScheduleError("union-window source has no episode map")
    expected_episode_keys = {
        f"{cls}/{seq}/{run}"
        for cls in CLASSES
        for seq in CLASS_SEQS[cls]
        for run in range(RUNS)
    }
    if set(episodes) != expected_episode_keys:
        raise ScheduleError("union-window source episode population drift")

    targets: dict[str, dict[tuple[str, int], dict]] = {cls: {} for cls in CLASSES}
    seen_donors: dict[str, set[tuple[str, int]]] = {cls: set() for cls in CLASSES}
    for cls in CLASSES:
        for target_seq in CLASS_SEQS[cls]:
            for target_run in range(RUNS):
                donor_seq, donor_run = donor_identity(cls, target_seq, target_run)
                if donor_seq == target_seq or donor_run == target_run:
                    raise ScheduleError(f"donor exclusion failed for {cls}/{target_seq}/{target_run}")
                donor_key = f"{cls}/{donor_seq}/{donor_run}"
                donor = episodes.get(donor_key)
                if not isinstance(donor, dict):
                    raise ScheduleError(f"missing donor episode {donor_key}")
                if donor.get("class") != cls or donor.get("seq") != donor_seq:
                    raise ScheduleError(f"donor identity mismatch for {donor_key}")
                if donor.get("run") != donor_run:
                    raise ScheduleError(f"donor run mismatch for {donor_key}")
                ordered_candidate_frames(
                    cls=cls,
                    target_seq=target_seq,
                    target_run=target_run,
                    donor_seq=donor_seq,
                    donor_run=donor_run,
                    donor_frame_count=donor.get("frame_count"),
                    donor_brake_frames=donor.get("brake_frames", []),
                )
                target_key = (target_seq, target_run)
                targets[cls][target_key] = {
                    "donor_seq": donor_seq,
                    "donor_run": donor_run,
                    "donor_frame_count": donor["frame_count"],
                    "donor_brake_frames": list(donor["brake_frames"]),
                }
                donor_identity_key = (donor_seq, donor_run)
                if donor_identity_key in seen_donors[cls]:
                    raise ScheduleError(f"donor map is not bijective in {cls}")
                seen_donors[cls].add(donor_identity_key)
        expected_donors = len(CLASS_SEQS[cls]) * RUNS
        if len(seen_donors[cls]) != expected_donors:
            raise ScheduleError(f"donor map is incomplete in {cls}")
        observed_horizon = sum(row["donor_frame_count"] for row in targets[cls].values())
        if observed_horizon != UNION_CLASS_HORIZON_FRAMES[cls]:
            raise ScheduleError(f"donor horizon drift in {cls}")
        observed_brakes = sum(len(row["donor_brake_frames"]) for row in targets[cls].values())
        if observed_brakes != UNION_CLASS_BRAKE_ROWS[cls]:
            raise ScheduleError(f"donor brake budget drift in {cls}")
    return targets


def _source_receipt(source_report: Mapping) -> dict:
    return {
        "schema": source_report["schema"],
        "source_log_parts": deepcopy(source_report["source_log_parts"]),
        "source_joined_sha256": source_report["source_joined_sha256"],
        "pair_order": deepcopy(source_report["pair_order"]),
        "runs_per_pair": source_report["runs_per_pair"],
        "block_count": source_report["block_count"],
        "totals": deepcopy(source_report["totals"]),
        "per_class": deepcopy(source_report["per_class"]),
    }


def generate_nested_dose_schedules(source_report: Mapping) -> dict:
    """Generate all 1,600 dose/target rows from a valid frozen source receipt."""
    computed_budgets = expected_budgets()
    if computed_budgets != FROZEN_BUDGETS:
        raise ScheduleError("round-half-up budgets differ from the preregistration")
    targets = _source_target_rows(source_report)

    schedules: dict[str, dict] = {dose: {} for dose in DOSES}
    class_summary = {}
    for cls in CLASSES:
        master = _master_order(cls, targets[cls])
        max_budget = FROZEN_BUDGETS["blind_2_0x"][cls]
        if max_budget > len(master):
            raise ScheduleError(f"2.0x budget exceeds available horizon in {cls}")

        scheduled_counts = {}
        supported_counts = {}
        for dose in DOSES:
            budget = FROZEN_BUDGETS[dose][cls]
            selected: dict[tuple[str, int], list[int]] = {
                (seq, run): [] for seq in CLASS_SEQS[cls] for run in range(RUNS)
            }
            for candidate in master[:budget]:
                selected[(candidate["target_seq"], candidate["target_run"])].append(
                    candidate["frame"]
                )

            for target_seq in CLASS_SEQS[cls]:
                for target_run in range(RUNS):
                    source = targets[cls][(target_seq, target_run)]
                    brake_frames = sorted(selected[(target_seq, target_run)])
                    key = f"{cls}/{target_seq}/{target_run}"
                    schedules[dose][key] = {
                        "dose_id": dose,
                        "target_class": cls,
                        "target_seq": target_seq,
                        "target_run": target_run,
                        "donor_class": cls,
                        "donor_seq": source["donor_seq"],
                        "donor_run": source["donor_run"],
                        "donor_frame_count": source["donor_frame_count"],
                        "donor_brake_frames": source["donor_brake_frames"],
                        "brake_frames": brake_frames,
                        "scheduled_brake_count": len(brake_frames),
                    }

            scheduled_counts[dose] = sum(len(frames) for frames in selected.values())
            supported_counts[dose] = sum(bool(frames) for frames in selected.values())

        class_summary[cls] = {
            "target_count": len(targets[cls]),
            "donor_horizon_frames": sum(
                source["donor_frame_count"] for source in targets[cls].values()
            ),
            "donor_brake_frames": sum(
                len(source["donor_brake_frames"]) for source in targets[cls].values()
            ),
            "master_candidate_count": len(master),
            "master_order_sha256": _master_sha256(master),
            "scheduled_brake_frames": scheduled_counts,
            "supported_schedule_count": supported_counts,
        }

    report = {
        "schema": SCHEMA,
        "verdict": "NESTED_DOSE_SCHEDULES_OK",
        "source": _source_receipt(source_report),
        "donor_rule": deepcopy(EXPECTED_DONOR_RULE),
        "dose_multipliers": {dose: str(DOSE_MULTIPLIERS[dose]) for dose in DOSES},
        "dose_budgets": deepcopy(FROZEN_BUDGETS),
        "class_summary": class_summary,
        "schedule_count": sum(len(rows) for rows in schedules.values()),
        "schedules": schedules,
        "problem_count": 0,
        "problems": [],
    }
    problems = validate_schedule_report(report)
    report["problems"] = problems
    report["problem_count"] = len(problems)
    report["verdict"] = (
        "NESTED_DOSE_SCHEDULES_OK" if not problems else "NESTED_DOSE_SCHEDULES_INVALID"
    )
    return report


def _parse_schedule_key(key: str) -> tuple[str, str, str, int] | None:
    parts = key.split("/")
    if len(parts) != 4:
        return None
    dose, cls, seq, run_text = parts
    try:
        run = int(run_text)
    except ValueError:
        return None
    if str(run) != run_text:
        return None
    return dose, cls, seq, run


def validate_schedule_report(report: Mapping) -> list[str]:
    """Recompute schedule identities and master-prefix allocation from artifact rows."""
    problems: list[str] = []
    if report.get("schema") != SCHEMA:
        problems.append("schema-metadata")
    if report.get("verdict") != "NESTED_DOSE_SCHEDULES_OK":
        problems.append("verdict-metadata")
    if report.get("donor_rule") != EXPECTED_DONOR_RULE:
        problems.append("donor-rule-metadata")
    expected_multipliers = {dose: str(DOSE_MULTIPLIERS[dose]) for dose in DOSES}
    if report.get("dose_multipliers") != expected_multipliers:
        problems.append("dose-multiplier-metadata")
    source = report.get("source")
    if not isinstance(source, dict):
        problems.append("source-receipt")
    else:
        if source.get("schema") != EXPECTED_SOURCE_SCHEMA:
            problems.append("source-schema")
        if source.get("source_joined_sha256") != EXPECTED_SOURCE_JOINED_SHA256:
            problems.append("source-joined-sha256")
        source_parts = source.get("source_log_parts")
        source_hashes = (
            [row.get("sha256") if isinstance(row, dict) else None for row in source_parts]
            if isinstance(source_parts, list)
            else []
        )
        if source_hashes != EXPECTED_SOURCE_PART_SHA256:
            problems.append("source-part-sha256")
        if source.get("block_count") != sum(len(seqs) for seqs in CLASS_SEQS.values()) * RUNS:
            problems.append("source-block-count")
        expected_pair_order = [
            f"{cls}/{seq}" for cls in CLASSES for seq in CLASS_SEQS[cls]
        ]
        if source.get("pair_order") != expected_pair_order:
            problems.append("source-pair-order")
        if source.get("runs_per_pair") != RUNS:
            problems.append("source-runs-per-pair")
        if source.get("totals") != EXPECTED_SOURCE_TOTALS:
            problems.append("source-totals")
        if source.get("per_class") != EXPECTED_SOURCE_PER_CLASS:
            problems.append("source-class-totals")
    if report.get("problem_count") != 0 or report.get("problems") != []:
        problems.append("problem-metadata")
    nested_schedules = report.get("schedules")
    if not isinstance(nested_schedules, dict):
        return ["schedules-not-object"]

    expected_target_keys = {
        f"{cls}/{seq}/{run}"
        for cls in CLASSES
        for seq in CLASS_SEQS[cls]
        for run in range(RUNS)
    }
    if set(nested_schedules) != set(DOSES):
        problems.append("schedule-dose-keys")
    schedules: dict[str, object] = {}
    for dose in DOSES:
        dose_rows = nested_schedules.get(dose)
        if not isinstance(dose_rows, dict):
            problems.append(f"schedule-dose-not-object:{dose}")
            continue
        observed_targets = set(dose_rows)
        if observed_targets != expected_target_keys:
            problems.append(
                f"schedule-target-keys:{dose}:"
                f"missing={len(expected_target_keys - observed_targets)}:"
                f"extra={len(observed_targets - expected_target_keys)}"
            )
        schedules.update({f"{dose}/{key}": row for key, row in dose_rows.items()})

    expected_keys = {
        f"{dose}/{cls}/{seq}/{run}"
        for dose in DOSES
        for cls in CLASSES
        for seq in CLASS_SEQS[cls]
        for run in range(RUNS)
    }
    observed_keys = set(schedules)
    if observed_keys != expected_keys:
        problems.append(
            f"schedule-keys:missing={len(expected_keys - observed_keys)}:"
            f"extra={len(observed_keys - expected_keys)}"
        )

    target_sources: dict[str, dict[tuple[str, int], dict]] = {cls: {} for cls in CLASSES}
    for key in sorted(observed_keys & expected_keys):
        parsed = _parse_schedule_key(key)
        if parsed is None:
            problems.append(f"schedule-key-format:{key}")
            continue
        dose, cls, seq, run = parsed
        row = schedules[key]
        if not isinstance(row, dict):
            problems.append(f"schedule-row-not-object:{key}")
            continue
        identity = (row.get("dose_id"), row.get("target_class"), row.get("target_seq"), row.get("target_run"))
        if identity != (dose, cls, seq, run):
            problems.append(f"target-identity:{key}")
        expected_donor_seq, expected_donor_run = donor_identity(cls, seq, run)
        if row.get("donor_class") != cls:
            problems.append(f"donor-class:{key}")
        if row.get("donor_seq") != expected_donor_seq:
            problems.append(f"donor-pair:{key}")
        if row.get("donor_run") != expected_donor_run:
            problems.append(f"donor-run:{key}")

        frame_count = row.get("donor_frame_count")
        donor_brakes = row.get("donor_brake_frames")
        brake_frames = row.get("brake_frames")
        if not isinstance(frame_count, int) or isinstance(frame_count, bool) or frame_count <= 0:
            problems.append(f"donor-horizon:{key}")
            continue
        if not isinstance(donor_brakes, list) or any(
            not isinstance(frame, int) or isinstance(frame, bool) for frame in donor_brakes
        ):
            problems.append(f"donor-brake-type:{key}")
            continue
        if donor_brakes != sorted(set(donor_brakes)):
            problems.append(f"donor-brake-unique-order:{key}")
        if any(frame < 0 or frame >= frame_count for frame in donor_brakes):
            problems.append(f"donor-brake-horizon:{key}")
        if not isinstance(brake_frames, list) or any(
            not isinstance(frame, int) or isinstance(frame, bool) for frame in brake_frames
        ):
            problems.append(f"brake-type:{key}")
            continue
        if brake_frames != sorted(set(brake_frames)):
            problems.append(f"brake-unique-order:{key}")
        if any(frame < 0 or frame >= frame_count for frame in brake_frames):
            problems.append(f"brake-horizon:{key}")
        if row.get("scheduled_brake_count") != len(brake_frames):
            problems.append(f"scheduled-count:{key}")
        if not brake_frames:
            problems.append(f"unsupported-schedule:{key}")

        source_key = (seq, run)
        source_value = {
            "donor_seq": row.get("donor_seq"),
            "donor_run": row.get("donor_run"),
            "donor_frame_count": frame_count,
            "donor_brake_frames": donor_brakes,
        }
        prior = target_sources[cls].get(source_key)
        if prior is not None and prior != source_value:
            problems.append(f"dose-source-drift:{cls}/{seq}/{run}")
        else:
            target_sources[cls][source_key] = source_value

    for cls in CLASSES:
        expected_target_count = len(CLASS_SEQS[cls]) * RUNS
        if len(target_sources[cls]) != expected_target_count:
            problems.append(f"target-source-count:{cls}:{len(target_sources[cls])}")
            continue
        try:
            master = _master_order(cls, target_sources[cls])
        except (KeyError, ScheduleError, TypeError) as exc:
            problems.append(f"master-order:{cls}:{exc}")
            continue

        expected_summary = {
            "target_count": expected_target_count,
            "donor_horizon_frames": UNION_CLASS_HORIZON_FRAMES[cls],
            "donor_brake_frames": UNION_CLASS_BRAKE_ROWS[cls],
            "master_candidate_count": UNION_CLASS_HORIZON_FRAMES[cls],
            "master_order_sha256": _master_sha256(master),
            "scheduled_brake_frames": {
                dose: FROZEN_BUDGETS[dose][cls] for dose in DOSES
            },
            "supported_schedule_count": {dose: expected_target_count for dose in DOSES},
        }
        class_summary = report.get("class_summary")
        observed_summary = (
            class_summary.get(cls) if isinstance(class_summary, dict) else None
        )
        if observed_summary != expected_summary:
            problems.append(f"class-summary:{cls}")

        for dose in DOSES:
            budget = FROZEN_BUDGETS[dose][cls]
            selected = {
                (seq, run): [] for seq in CLASS_SEQS[cls] for run in range(RUNS)
            }
            for candidate in master[:budget]:
                selected[(candidate["target_seq"], candidate["target_run"])].append(
                    candidate["frame"]
                )
            observed_budget = 0
            for seq in CLASS_SEQS[cls]:
                for run in range(RUNS):
                    key = f"{dose}/{cls}/{seq}/{run}"
                    row = schedules.get(key)
                    if not isinstance(row, dict) or not isinstance(row.get("brake_frames"), list):
                        continue
                    expected_frames = sorted(selected[(seq, run)])
                    if row["brake_frames"] != expected_frames:
                        problems.append(f"master-prefix:{key}")
                    observed_budget += len(row["brake_frames"])
            if observed_budget != budget:
                problems.append(f"class-budget:{dose}/{cls}:{observed_budget}!={budget}")

        for seq in CLASS_SEQS[cls]:
            for run in range(RUNS):
                dose_sets = []
                for dose in DOSES:
                    row = schedules.get(f"{dose}/{cls}/{seq}/{run}")
                    if not isinstance(row, dict) or not isinstance(row.get("brake_frames"), list):
                        break
                    dose_sets.append(set(row["brake_frames"]))
                if len(dose_sets) == len(DOSES) and not all(
                    lower <= upper for lower, upper in zip(dose_sets, dose_sets[1:])
                ):
                    problems.append(f"dose-nesting:{cls}/{seq}/{run}")

    if report.get("dose_budgets") != FROZEN_BUDGETS:
        problems.append("dose-budget-metadata")
    if report.get("schedule_count") != len(expected_keys):
        problems.append("schedule-count-metadata")
    return problems


def _load_extractor():
    path = Path(__file__).with_name("extract_union_windows.py")
    spec = importlib.util.spec_from_file_location("iter135_extract_union_windows", path)
    if spec is None or spec.loader is None:
        raise ScheduleError("cannot load union-window extractor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, value: Mapping) -> None:
    path.write_text(json.dumps(value, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("parts", nargs="+", type=Path)
    args = parser.parse_args(argv)
    try:
        source_report = _load_extractor().extract_union_windows(args.parts)
        report = generate_nested_dose_schedules(source_report)
    except (OSError, ScheduleError, ValueError) as exc:
        print(f"NESTED_DOSE_SCHEDULES_INVALID: {exc}", file=sys.stderr)
        return 1
    _write_json(args.output, report)
    totals = {
        dose: sum(report["dose_budgets"][dose].values())
        for dose in DOSES
    }
    print(
        f"{report['verdict']} schedules={report['schedule_count']} "
        f"budgets={totals} problems={report['problem_count']}"
    )
    return 0 if report["verdict"] == "NESTED_DOSE_SCHEDULES_OK" else 1


if __name__ == "__main__":
    sys.exit(main())
