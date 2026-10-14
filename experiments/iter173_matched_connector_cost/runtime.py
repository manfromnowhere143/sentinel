"""Observed interpreter/package fingerprints; not a hermetic build claim."""

import hashlib
import importlib
import json
from pathlib import Path
import platform
import sys

import numpy
import scipy

from .common import BASE, read, require

MODULES = (
    "scipy.optimize._lsq.least_squares",
    "scipy.optimize._lsq.trf",
    "scipy.optimize._lsq.common",
    "scipy.optimize._minimize",
    "scipy.optimize._numdiff",
    "scipy.optimize._differentiable_functions",
    "scipy.optimize._optimize",
    "scipy._lib._util",
    "scipy.linalg._decomp_svd",
    "scipy.linalg._flapack",
    "scipy.linalg._fblas",
    "numpy._core._multiarray_umath",
)


def identity():
    files = {}
    for name in MODULES:
        p = Path(importlib.import_module(name).__file__)
        files[name] = dict(filename=p.name, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    return dict(
        python=sys.version,
        platform=platform.platform(),
        numpy=numpy.__version__,
        scipy=scipy.__version__,
        files=files,
        scope="Selected loaded implementation files and versions; OS/native dependency closure is not certified.",
    )


def verify(root):
    expected = json.loads(read(root, BASE / "RUNTIME.json"))
    require(identity() == expected, "runtime_identity")
    return expected
