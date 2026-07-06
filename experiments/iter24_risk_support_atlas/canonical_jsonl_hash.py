#!/usr/bin/env python3
"""Canonical SHA256 for JSONL or JSONL.GZ artifacts."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json


def open_text(path: str):
    return gzip.open(path, "rt") if path.endswith(".gz") else open(path)


def canonical_sha256(path: str) -> tuple[str, int]:
    h = hashlib.sha256()
    rows = 0
    with open_text(path) as f:
        for line in f:
            if not line.strip():
                continue
            payload = json.loads(line)
            encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            h.update(encoded)
            h.update(b"\n")
            rows += 1
    return h.hexdigest(), rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()
    for path in args.paths:
        digest, rows = canonical_sha256(path)
        print(f"{digest}  {rows}  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
