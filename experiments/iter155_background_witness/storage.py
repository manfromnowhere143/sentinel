"""Bounded array evidence with no-follow input reads and explicit little-endian types."""

import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re

from experiments.iter150_cloud_observation.native import file, parse

CHUNK = 8 * 1024**2
CAP = 384 * 1024**2
DTYPES = {"<f4": 4, "<f8": 8, "|u1": 1, "<i8": 8}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path, limit=8 * 1024**2):
    path = Path(path)
    return parse(file(path.parent, path.name, limit, content=True)[1])


def write_json(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def put_array(root, name, array, inventory):
    import numpy as np

    if not re.fullmatch("[a-z][a-z0-9_]*", name):
        raise ValueError("array_name")
    array = np.ascontiguousarray(array)
    dtype = array.dtype.str
    if dtype not in DTYPES or array.nbytes > CAP:
        raise ValueError("array_dtype_or_size")
    raw = array.tobytes()
    chunks = []
    for i, start in enumerate(range(0, len(raw), CHUNK)):
        part = raw[start : start + CHUNK]
        compressed = gzip.compress(part, mtime=0)
        filename = f"{name}_{i:03d}.bin.gz"
        (root / filename).write_bytes(compressed)
        chunks.append(
            {
                "path": filename,
                "bytes": len(compressed),
                "sha256": digest(compressed),
                "raw_bytes": len(part),
                "raw_sha256": digest(part),
            }
        )
    inventory[name] = {
        "shape": list(array.shape),
        "dtype": dtype,
        "bytes": len(raw),
        "sha256": digest(raw),
        "chunks": chunks,
    }


def get_arrays(root, inventory):
    import numpy as np

    total = 0
    seen = set()
    arrays = {}
    for name, row in inventory.items():
        if not re.fullmatch("[a-z][a-z0-9_]*", name) or row["dtype"] not in DTYPES:
            raise ValueError("array_header")
        shape = row["shape"]
        if not 1 <= len(shape) <= 3 or any(type(v) is not int or v < 0 for v in shape):
            raise ValueError("array_shape")
        expected = math.prod(shape) * DTYPES[row["dtype"]]
        total += expected
        if expected != row["bytes"] or total > CAP:
            raise ValueError("array_capacity")
        raw = bytearray()
        for i, chunk in enumerate(row["chunks"]):
            name_expected = f"{name}_{i:03d}.bin.gz"
            if chunk["path"] != name_expected or name_expected in seen:
                raise ValueError("chunk_order_or_duplicate")
            seen.add(name_expected)
            record, compressed = file(root, name_expected, CHUNK + 65536, content=True)
            if len(compressed) != chunk["bytes"] or digest(compressed) != chunk["sha256"]:
                raise ValueError("chunk_identity")
            size = min(CHUNK, expected - len(raw))
            if size <= 0 or chunk["raw_bytes"] != size:
                raise ValueError("chunk_raw_size")
            with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
                part = stream.read(size + 1)
            if len(part) != size or digest(part) != chunk["raw_sha256"]:
                raise ValueError("chunk_expansion_or_identity")
            raw.extend(part)
        if len(raw) != expected or digest(raw) != row["sha256"]:
            raise ValueError("array_identity")
        values = np.frombuffer(raw, dtype=row["dtype"]).reshape(shape)
        if not np.isfinite(values).all():
            raise ValueError("array_nonfinite")
        arrays[name] = values
    return arrays, seen
