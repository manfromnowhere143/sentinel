from __future__ import annotations

import os
import subprocess
from pathlib import Path

from scripts.mission_state import load_state


def test_generator_uses_canonical_state_and_never_elevates_iter38() -> None:
    repo = Path(__file__).resolve().parents[1]
    state = load_state()
    next_program = state["next_program"]
    env = dict(os.environ, SENTINEL_HANDOFF_SKIP_LIVE_PROBE="1")
    run = subprocess.run(
        ["python3", "scripts/make_handoff.py"],
        cwd=repo,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert (
        f"iteration {state['current_completed_iteration']} / {state['current_verdict']}"
        in run.stdout
    )
    assert f"iteration {next_program['iteration']} / {next_program['phase']}" in run.stdout
    assert "Deprecated pending pre-registration: experiments/iter38_" in run.stdout
    assert "its gate governs the next action" not in run.stdout
