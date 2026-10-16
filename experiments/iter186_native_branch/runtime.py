"""Named native build and observed inputs; no hermetic-build claim."""

from pathlib import Path
from experiments.iter171_centered_shooting.runtime import identity
from .common import BASE, document, read, require, sha


def verify(root, library, parent_library, prefix):
    manifest = document(root, BASE / "RUNTIME.json")
    require(sha(Path(library).read_bytes()) == manifest["bridge_sha256"], "bridge_identity")
    require(
        sha(Path(parent_library).read_bytes()) == manifest["parent_bridge_sha256"],
        "parent_bridge_identity",
    )
    require(identity() == manifest["python_runtime"], "python_runtime")
    for name, expected in manifest["libraries"].items():
        require(sha((Path(prefix) / name).read_bytes()) == expected, "runtime_library:" + name)
    for namespace, directory in (("repository", root), ("prefix", Path(prefix))):
        for name, expected in manifest["headers"][namespace].items():
            require(sha(read(directory, name)) == expected, "build_input:" + name)
    return manifest
