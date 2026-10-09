# Iteration 137 — controller replay and deadline behavior

Status: **supported**, limited to numerical repeatability on the registered development corpus
and runtime. Deadline misses were observed; a 50 ms execution guarantee is **not supported**.
Date: 2026-10-09. Local research candidate, not a canonical publication or a driving result.

## Result

All **912/912 registered calls** completed in eight fresh worker processes. Every one of the
**114 typed inputs** produced exactly the same numerical record in all four numerical-mode
observations: two idle and two with three competitors on the same CPU. This includes raw
output bytes, all iterate identities, convergence norms, iteration count and stopping reason.
There were **zero numerical repeat mismatches**. All 456 numerical-mode calls converged;
none used wall time to select an iterate.

The separately implemented upstream-source replay verified every receipt, all eight blocks,
and the exact repetition rule in the measured Python 3.11.10 / NumPy 1.26.4 environment.
All four timed-mode observations together produced differing final control commands for
**114/114 typed inputs**. This is a within-fixture scheduling effect, not a new live result.

The corpus contains 57 dependent frames from the already disclosed Iter136 development case,
each reconstructed in two dtypes. It is not 114 independent driving scenarios. The historical
live dtype and stopping reasons remain unknown. Iter136 remains `REPLAY_DIVERGED`.

## Deadline behavior

Each mode/load group contains 228 calls (114 inputs, two repetitions). Quantiles use the
preregistered nearest-rank definition. Values below are rounded to 0.001 ms; exact values are
in [analysis.json](proof/analysis.json). There are no population confidence intervals.

### Adapter duration

Includes validation, trajectory conversion, full solve, numerical receipt construction and
digest. Excludes outer metadata packaging and JSON transport. See the exact boundaries in
[EXECUTION_BINDING.md](EXECUTION_BINDING.md).

| Mode / CPU load | Calls | >50 ms | p50 ms | p95 ms | p99 ms | Maximum ms |
|---|---:|---:|---:|---:|---:|---:|
| numerical/idle | 228 | 99 | 49.083 | 57.799 | 61.014 | 61.190 |
| numerical/contended | 228 | 228 | 204.440 | 242.433 | 254.113 | 254.544 |
| timed/idle | 228 | 86 | 48.523 | 56.162 | 56.521 | 56.754 |
| timed/contended | 228 | 228 | 70.743 | 72.017 | 74.236 | 74.999 |

### Full solver duration

Includes warm start and finalization, which the original loop deadline omits.

| Mode / CPU load | >50 ms | p50 ms | p95 ms | p99 ms | Maximum ms |
|---|---:|---:|---:|---:|---:|
| numerical/idle | 38 | 45.662 | 54.025 | 56.973 | 57.092 |
| numerical/contended | 228 | 191.832 | 228.819 | 239.627 | 241.517 |
| timed/idle | 38 | 45.113 | 52.289 | 52.577 | 53.019 |
| timed/contended | 228 | 60.315 | 70.401 | 70.577 | 73.395 |

### Recorded stopping reasons

| Mode / CPU load | Converged | Deadline | Iteration limit |
|---|---:|---:|---:|
| numerical/idle | 228 | 0 | 0 |
| numerical/contended | 228 | 0 | 0 |
| timed/idle | 209 | 19 | 0 |
| timed/contended | 0 | 228 | 0 |

Convergence does not imply meeting the deadline: **67/209** timed/idle calls labelled
`converged` exceeded 50 ms at the adapter boundary. Every contended timed call stopped at its
loop deadline, yet every one exceeded 50 ms for the full solver and adapter. A loop cutoff is
not an end-to-end execution bound. The convergence-first branch intentionally retains a null
last deadline reading when that check was skipped.

## Interpretation and next step

This establishes a reproducible numerical research controller for this source, corpus and
runtime. It also exposes a scheduling dependency in the instrumented timed policy. Removing
the deadline changes that policy and does not solve real-time execution: numerical-mode
adapter p99 was 61.014 ms idle and 254.113 ms contended.

The next useful step is a **fresh preregistered live reference pair** under an explicitly named
numerical execution mode, with actual dtype, input/state/reference, stop reason, iteration
sequence and control identity retained at each frame. Keep simulation time and observed compute
latency separate. Admit the later recoverability intervention grid only after that fresh pair
passes its frozen replay rule. Do not retry or reinterpret Iter136, and do not silently present
numerical mode as the historical timed controller.

A deployable deadline policy remains a separate research/engineering question, including its
compute reservation, admissible latency, control quality and behavior when a result is late.
No fallback is validated here. The broader mission remains testing what additional information
enables useful intervention beyond a strong responsive baseline. This CPU prerequisite supplies
no collision-prevention, general safety, transfer or industrial superiority result.

## Evidence and limitations

- Raw benchmark evidence was committed **before interpretation** at
  `0dfb06b8fcd45fb5e6bc977d8d1969d3bba6c6aa`. All 33 downloaded raw files matched the host inventory.
- Source/corpus and operational amendments preceded measurement. The executed source packet was
  `3bbf160bc6be02b405d81d80ad2347a0167f9c73`; [binding](binding.json) and
  [execution details](EXECUTION_BINDING.md) retain exact identities.
- [Independent replay receipt](proof/independent_replay.stdout) returned zero with all numerical
  and accounting checks passing. [Raw benchmark](proof/benchmark/run.json) retains schedule,
  affinity, competitor liveness/reaping, per-worker environments and all 912 call records.
- **51 focused tests passed** locally and from the extracted committed candidate, including
  branch boundaries, source-clock parity and known-bads. Runtime-specific parity also passed
  on the host before measurement (10 scripted-clock pairs, two independent numerical fixtures).
- Implementation/test Ruff checks passed. The extracted local pytest run had one cache-directory
  warning from `-c /dev/null`; tests passed. A broad directory Ruff invocation encountered
  multi-import statements in retained forensic preflight scripts. Those executed bytes remain
  intact; no whole-repository, frozen-dependency or hosted-CI pass is claimed.
- One CPU/runtime, dependent development frames, reconstructed historical dtypes, and two
  declared load conditions bound the result. Bit equality across library versions, architectures
  or arbitrary inputs is untested. Timing includes instrumentation; this is not an uninstrumented
  controller benchmark, worst-case execution analysis or measured actuation latency.
- No simulator construction, model inference, GPU computation, driving episode or intervention
  occurred in Iter137. The 92.028-second benchmark used the existing GPU-equipped host's CPU.
- The first provider start lost its client connection but started the VM; about 58 minutes of
  preparation window were consumed before shutdown. One recovery RPC then hit a zone stockout;
  the next succeeded. Both failures and pre-measurement resource amendments are retained.
  No measured call or block was retried, replaced, dropped or added.

Reproduce the numerical replay in the bound environment using the command in
[EXECUTION_BINDING.md](EXECUTION_BINDING.md). The portable descriptive cross-tabulation is:

```bash
python3 experiments/iter137_controller_execution_contract/describe_controls.py
```

See [STATUS.md](STATUS.md) and [STATE.json](STATE.json) for final provider and candidate state.
