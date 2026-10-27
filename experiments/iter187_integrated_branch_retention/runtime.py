"""Verify the already qualified binary, its headers and observed runtime."""

import json
from pathlib import Path

from experiments.iter171_centered_shooting.runtime import identity
from .common import BASE, read, require, sha


def verify(root, library, prefix):
    manifest = json.loads(read(root, BASE / "RUNTIME.json"))
    require(sha(Path(library).read_bytes()) == manifest["bridge_sha256"], "bridge_identity")
    require(identity() == manifest["python_runtime"], "python_runtime")
    for name, expected in manifest["libraries"].items():
        require(sha((Path(prefix) / name).read_bytes()) == expected, "runtime_library:" + name)
    for namespace, directory in (("repository", root), ("prefix", Path(prefix))):
        for name, expected in manifest["headers"][namespace].items():
            require(sha(read(directory, name)) == expected, "build_input:" + name)
    return manifest
