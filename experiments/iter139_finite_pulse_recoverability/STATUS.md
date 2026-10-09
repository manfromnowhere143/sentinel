# Iteration 139 status

Complete: **null / FINITE_PULSE_RECOVERY_NULL**. All eight episodes validated; all six pulses
collided, so none met useful recovery. The 2-second-onset, 1-second pulse delayed collision
from 6.5 to 7.0 seconds. Read [RESULT.md](RESULT.md) for the complete grid and limitations.

All 206 live controller calls passed original-source replay; all stopped by convergence.
Complete calls exceeded 50 ms on 166/206 observations; full solver calls on 137/206. Timing
and numerical repeatability remain distinct. The independent Decimal checks and arithmetic
recount agree. All prefixes, complete pulses and resumptions validated; no episode retry.

179 distinct focused tests passed; implementation/test Ruff passed. The bound-host stub
passed before live execution. Full/frozen/hosted CI is not claimed. Initial tooling failures,
zone stockout, failed dependent SSH attempts and their pre-live correction remain retained.

Cloud host **TERMINATED**, confirmed by [provider readback](proof/final_provider_state.stdout).
[Postflight](proof/postflight_summary.json) matched all 471 bound files and found no owned
processes, containers or GPU applications. The run is closed; do not extend or retry its grid.

Candidate branch: `research/iter139-finite-pulse`, local and unpushed. Canonical master and
unrelated WIP remain unchanged. Read [NEXT_STEP.md](NEXT_STEP.md) before new research.
