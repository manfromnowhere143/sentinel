"""Bounded records and exclusive, durable publication within an owned directory."""

import os
from pathlib import Path

from experiments.iter149_observation_recovery.recovery import encode
from experiments.iter150_cloud_observation.native import document


def read(path):
    path = Path(path).absolute()
    return document(path.parent, path.name)[1]


def record(path, value):
    path = Path(path).absolute()
    raw = encode(value) + b"\n"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
