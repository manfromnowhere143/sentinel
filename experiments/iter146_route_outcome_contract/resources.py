"""Finite output policy; host measurements remain required before cloud admission."""

import os
from pathlib import Path
import shutil
import stat

CASE_CAP = 512 * 1024**2
CASE_STOP = 448 * 1024**2
STUDY_CAP = 112 * CASE_CAP


def output_guard(path, *, reserve=25 * 1024**3, usage=shutil.disk_usage):
    path = Path(path)
    if path.is_symlink() or not path.is_dir():
        raise ValueError("output_root_type")
    total = 0
    for root, dirs, files in os.walk(path, followlinks=False):
        for name in dirs + files:
            p = Path(root) / name
            mode = p.lstat().st_mode
            if stat.S_ISLNK(mode) or not (
                stat.S_ISDIR(mode) or stat.S_ISREG(mode) or stat.S_ISFIFO(mode)
            ):
                raise ValueError("output_entry_type")
            if stat.S_ISREG(mode):
                total += p.stat().st_size
    if total >= CASE_STOP or usage(path).free < reserve:
        raise ValueError("output_or_storage_limit")
    return total


def proposed_storage(free_bytes, bound_copies_bytes):
    if (
        type(free_bytes) is not int
        or type(bound_copies_bytes) is not int
        or min(free_bytes, bound_copies_bytes) < 0
    ):
        raise ValueError("storage_observation")
    return dict(
        status="proposed",
        live_admitted=False,
        slots=112,
        per_case_cap_bytes=CASE_CAP,
        study_cap_bytes=STUDY_CAP,
        bound_copy_bytes=bound_copies_bytes,
        reserve_bytes=25 * 1024**3,
        fits=free_bytes - STUDY_CAP - bound_copies_bytes >= 25 * 1024**3,
        enforcement="Poll owned output once per second and between steps; stop at 448 MiB with 64 MiB buffer. Per-file cap and process watchdog still required; no instantaneous aggregate quota claim.",
    )
