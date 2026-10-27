"""Observed runtime identity and IEEE assumptions; no hermeticity claim."""

import json
import math
import platform
from pathlib import Path
import sys

import numpy as np

from .common import BASE, read, require, sha


def observe():
    require(sys.float_info.radix == 2 and sys.float_info.mant_dig == 53 and sys.float_info.rounds == 1, "binary64_rounding")
    require(1.0 + 2.0**-53 == 1.0 and math.nextafter(1.0, math.inf) == 1.0 + 2.0**-52, "rounding_controls")
    return dict(python=sys.version, platform=platform.platform(), numpy=np.__version__,
                math_binary_sha256=sha(Path(math.__file__).read_bytes()),
                float_mantissa=sys.float_info.mant_dig, float_rounding=sys.float_info.rounds,
                semantics="Observed CPython binary64 arithmetic and actual libm coefficients; no compiler/libm formal proof or hermeticity claim.")


def verify(root):
    require(observe() == json.loads(read(root, BASE / "RUNTIME.json")), "runtime_identity")
