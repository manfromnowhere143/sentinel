"""Local binary and package identity checks; no scientific authority."""

import json
from pathlib import Path
from .common import BASE, read, require, sha


def verify(root, library):
    manifest = json.loads(read(root, BASE / "RUNTIME.json"))
    require(sha(Path(library).read_bytes()) == manifest["bridge_sha256"], "bridge_identity")
    prefix = Path(library).parent / "env"
    for name, expected in manifest["libraries"].items():
        require(sha((prefix / name).read_bytes()) == expected, "runtime_library:" + name)
    return manifest
