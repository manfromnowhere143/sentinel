# Iter141 result: reference reproduced; comparison incomplete

Operational status: **failed / COORDINATOR_BRANCH_LOOKUP_FAILED**.
Scientific comparison: **inconclusive / SCHEDULE_INCOMPLETE**. One of four scheduled
episodes ran. Neither nominal continuation was observed, so there is no recovery result.

## What happened

The first reference completed successfully and its 12 retained raw files were committed
at `888a8a3c86f327de15612d5b7a8553e66b43805f` before interpretation. The outer
coordinator then queried `research/iter141-finite-pulse`, a stale name copied from
Iter139. The actual branch is `research/iter141-nominal-continuation`. Git returned
128, before the commit ledger was written or a verifier/next episode was started.
The literal preregistered failure rule stopped the rest of the schedule. The existing
raw commit was recovered into the ledger, without another episode. The error and
its stage are retained in [coordinator_failure.json](proof/coordinator_failure.json).

This was an outer orchestration error by the implementing agent. The 223 focused
tests and host fixture did not exercise that branch lookup. Their passes do not
establish a working complete coordinator. No initialized retry, outcome-dependent
threshold change, or nominal episode occurred. A successor requires a new protocol
and a tested complete orchestration path; this closed schedule will not be resumed.

## Retained reference evidence

| Measure | Observed reference |
| --- | ---: |
| Actions / original-source controller replays | 26 / 26 |
| Actual collision time | 6.5 simulated seconds |
| Raw final route completion | 0.11557062998555366 |
| Stop reasons | 26 converged; 0 deadline; 0 iteration limit |
| Monitor brake proposals / changed plans | 8 / 8 |
| First changed monitor plan | frame 18, pre-action time 4.5 s |
| Effective-controller-envelope violations | 0 |
| Declared Gym acceleration violations | 4 / 26 |
| Declared Gym steering-rate violations | 11 / 26 |
| Either declared Gym limit exceeded | 13 / 26 |
| Complete controller call >50 ms | 17 / 26 |
| Solver >50 ms | 13 / 26 |

The new reference matched Iter139's complete driving trace within the fixed numeric
contract, with exact observation hashes and exact numerical controller records.
Original-source replay validated every call in the bound runtime. A separate Decimal
recount agreed on the trace, control bounds, violation counts, timing counts and outcome;
see [analysis](proof/analysis/reference_a.json) and
[independent recount](proof/independent_reference_recount.json).
This is one new reference, not the planned fresh reference pair or a nominal comparison.

The declared Gym limits are ±2 m/s² and ±pi/12 rad/s. Effective controller limits
are ±3 m/s² and ±0.4 rad/s; the simulator accepts these larger controls. The count
confirms the model-interface mismatch, not physical actuator feasibility. Mixed
controller/environment/actor clocks remain .5/.25/.1 seconds. No limit was silently
changed or enforced by clipping during this run.

Timing medians: complete call 53.629131 ms,
solver 49.971864 ms and client roundtrip
1734.150077 ms. Startup-inclusive maximum client roundtrip
was 32290.394141 ms. Numerical convergence does not establish
an end-to-end deadline; the simulator uses fixed 0.25-second steps independently.

## Schedule and missingness

| Arm | Status |
| --- | --- |
| reference_a | completed, raw committed, descriptively validated |
| reference_b | unobserved after coordinator failure |
| nominal_a | unobserved after coordinator failure |
| nominal_b | unobserved after coordinator failure |

Unobserved continuations are not zero recoveries. The null in Iter139 remains its
own six-pulse result. The nominal-continuation question is still open.

## Validation and resources

223 distinct focused tests passed, including 44 Iter141 tests; those 44 also passed
from exact committed source. The bound-host synthetic four-arm fixture passed
without mocking threadpool observation. Its synthetic success labels are not live
outcomes. Initial local environment/lint failures remain visible. No full/frozen/
hosted CI result is claimed.

Postflight checked all 532 bound files unchanged, with no owned
processes, running containers or GPU applications, and 109.616 GiB free.
Provider readback confirmed [TERMINATED](proof/final_provider_state.stdout).
The observed provider start-to-stop interval was 528.391
seconds; original budget epoch through completed shutdown was
618.839 seconds of the 9,000-second
ceiling. Billed cost remains unobserved. All 12 raw files are retained; 82 media
assets remain remotely inventoried. No new package/image installation or replacement host.

Local storage was recovered by deleting one clean duplicate checkout only after
hashing every tracked file against retained Git objects. A handoff status helper
briefly copied candidate-only docs onto dirty root docs; the WIP historical sections
were restored from retained backup and the session recovery read, and the helper was
corrected. Both operational corrections have retained records. Scientific source,
historical evidence, root index and canonical master were not changed by those fixes.

This is a local, unpushed research candidate. Canonical master remains F17; Iter135
is deferred. No useful recovery, safety, state-of-the-art or population claim follows.
