"""Account for every owned output, including parent logs, source copies and archives."""

import os
from pathlib import Path
import shutil
import stat
from experiments.iter146_route_outcome_contract.resources import CASE_CAP, CASE_STOP

RESERVE = 25 * 1024**3
OVERHEAD = 1024**3


def tree_bytes(directory):
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("owned_root_type")
    total = 0
    for root, dirs, files in os.walk(directory, followlinks=False):
        for name in dirs + files:
            path = Path(root) / name
            info = path.lstat()
            if stat.S_ISREG(info.st_mode):
                total += info.st_size
            elif not (stat.S_ISDIR(info.st_mode) or stat.S_ISFIFO(info.st_mode)):
                raise ValueError("owned_entry_type")
    return total


def guard(control, case, slots, *, usage=shutil.disk_usage):
    if type(slots) is not int or not 1 <= slots <= 112:
        raise ValueError("slot_count")
    case_size = tree_bytes(case) if case.exists() else 0
    total = tree_bytes(control)
    if case_size >= CASE_STOP or total >= slots * CASE_CAP + OVERHEAD - (CASE_CAP - CASE_STOP):
        raise ValueError("owned_output_limit")
    if usage(control).free < RESERVE:
        raise ValueError("host_reserve")
    return dict(case_bytes=case_size, total_owned_bytes=total)
