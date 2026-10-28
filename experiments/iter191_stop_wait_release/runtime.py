"""Bind the previously admitted native and numerical runtime without rebuilding."""

from pathlib import Path
from experiments.iter189_uniform_timing_eligibility.runtime import verify as previous

PREFIX = Path("/Users/danielwahnich/.codex/reports/sentinel/iter165/runtime/env")
LIBRARY = Path("/Users/danielwahnich/.codex/reports/sentinel/iter186/libsentinel186.dylib")


def verify(root, library=LIBRARY):
    return previous(root, library, PREFIX)
