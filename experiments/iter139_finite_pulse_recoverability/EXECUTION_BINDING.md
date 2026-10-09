# Iteration 139 execution binding

Preregistration: `0b1ab853c78ad89db102483e590d7349c8998210`.
Executed packet source: `6991f8f48559ce8f6539a05a8b0eef749639eb26`.
Runtime manifest SHA-256: `5d03684bc43dee61a384ddc284e906d3077373cad211bfbff4e288bdc1694c33`.
Generated driver SHA-256: `e88524c44eb248a8da513a3f5686c6d3f2b142e4ce67acb4de190583264a7ba5`.

All 439 previously bound runtime/source/assets files matched before deployment. New files use
exclusive Iter139 paths. The original first start failed with zone stockout; the second succeeded
within the registered recovery allowance. The original 180-minute budget was not reset. The
owned shutdown timer was armed with a conservative margin. No package/image installation or
replacement machine. The source-bound numerical controller and released monitor are unchanged.
The [pre-execution correction](PRE_EXECUTION_INFRASTRUCTURE_CORRECTION.md) retains the failed
outer orchestration and the tested guard added before any successful host connection.

The core 37 new tests passed from extracted commit `887bac9...`; the only later source addition
is the operational provider guard, with four known-bads also passing from exact executed commit
`6991f8f...`. Together with inherited suites, 179 distinct focused tests passed. Initial lint
findings and an isolated-test invocation that inherited incompatible home-directory pytest
arguments remain retained; the isolated configuration and implementation Ruff pass. No full,
frozen-environment or hosted CI result is claimed.

The new trace schema preserves raw progress through the source's 10/9 maximum, preserves typed
incoming and executed plans, and records exact pulse/resumption semantics. Timing boundaries
remain those of [Iter138](../iter138_numerical_live_replay/EXECUTION_BINDING.md). The simulator
still advances fixed 0.25 s steps independently of wall time; the numerical policy has no
wall-clock stop. Deadline and deployed-vehicle feasibility remain separate research questions.

Raw episode proof is committed before interpretation and before the next arm. Controller replay
uses original upstream source in a separate process; Decimal pulse/prefix/outcome computation
imports neither the producer nor the primary checker. The generated-driver host fixture is CPU
only with stub state, not a simulator episode or observed recovery benefit.

## Final execution and closure

All eight frozen episodes completed and validated without initialized-episode retry. The
206 live calls independently replayed, and all six pulse prefixes and Decimal outcomes matched.
The complete grid is null; see [RESULT.md](RESULT.md). Every raw episode was committed before
interpretation; the [ledger](proof/episode_commit_ledger.json) retains those commits.

Postflight matched all 471 bound files and found no owned active work. The final provider state
is [TERMINATED](proof/final_provider_state.stdout), with a completed stop operation. The original
resource budget was not reset after the failed start; [accounting](proof/resource_accounting.json)
retains observed intervals and leaves billed cost unknown. The experiment is closed.
