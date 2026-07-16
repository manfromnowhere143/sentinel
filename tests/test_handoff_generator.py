from __future__ import annotations

import os
import subprocess
from pathlib import Path


def test_generator_uses_canonical_state_and_never_elevates_iter38() -> None:
    repo = Path(__file__).resolve().parents[1]
    env = dict(os.environ, SENTINEL_HANDOFF_SKIP_LIVE_PROBE="1")
    run = subprocess.run(
        ["python3", "scripts/make_handoff.py"],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "iteration 134 / PLACEBO_HARM_OR_NULL" in run.stdout
    assert "iteration 135 / PREREGISTRATION_REQUIRED" in run.stdout
    assert "Deprecated pending pre-registration: experiments/iter38_" in run.stdout
    assert "its gate governs the next action" not in run.stdout
