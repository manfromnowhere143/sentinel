# Iter152: fixed recovery continuation

11 October 2026. **Closed; scientific result: null for the tested recovery library.**
All fourteen new episodes passed independent replay: **1,420 verified new actions, zero
incomplete and zero uninitialized slots**. Two complete scenario comparisons are retained.
The two historical nominal episodes remain separate: two slots and 62 actions from Iter151.
Neither one-second pulse produced progress-preserving recovery in the eligible collision case.
Both pulses completed the benign case without the registered binary harm outcome; completion
time still increased. Both owned VM starts are verified TERMINATED and no owned job remains.

[State](STATE.json) · [aggregate](proof/aggregate.json) · [full analysis](proof/analysis.json) ·
[next decision](DECISION.md). `supported` in replay and aggregate receipts means the checks
passed; it does not turn the scientific null into a positive recovery finding.

## Admitted collision-case comparison

Scene `scene-0013-medium-00.yaml`, seed 144, two replicas per arm:

| Arm | Source-defined outcome in both replicas | Simulated collision time | Actions per replica |
|---|---|---:|---:|
| Nominal, retained Iter151 evidence | Collision | 7.75 s | 31 |
| Released monitor, new Iter152 runs | Collision | 9.0 s | 36 |
| One-second pulse starting at 0 s | Collision | 9.0 s | 36 |
| One-second pulse starting at 2.5 s | Collision | 8.5 s | 34 |

All six new episodes passed independent execution checks and replica agreement: **212 new
verified actions**. Both pulse comparisons passed the fixed comparator and full-prefix checks;
the later pulse matched all ten pre-intervention frames against the retained nominal baseline.
Both pulses changed the action, but neither produced a recovery witness. The earlier pulse
also failed the progress condition at the nominal hazard time. Progress at the monitor's later
hazard is unknown for the 2.5 s pulse because it had already collided; unknown remains explicit.

This is a negative finding for the tested finite action/timing library, not proof that this
collision is unavoidable. The observed delay does not satisfy the recovery criterion. No new
information channel or threshold was tested. The nominal pair is disclosed historical evidence:
its two episodes and 62 actions contribute zero to the fourteen-new-slot denominator.

[First-block analysis](proof/block_000_analysis.json) ·
[monitor admission](proof/admissions/pair_000.json) ·
[time-zero pulse admission](proof/admissions/pair_001.json) ·
[later pulse and complete comparison](proof/admissions/pair_002.json).

## Benign-case observations

Scene `scene-0038-easy-00.yaml`, seed 144, two replicas per arm. All eight episodes passed
replay, with 1,208 verified actions. All arms completed without recorded collision, off-route
or censoring; none supplies an eligible baseline failure for a recovery witness.

| Arm | Admitted outcome in both replicas | Completion time | Actions per replica |
|---|---|---:|---:|
| Nominal | Source-defined completion, no collision or off-route | 34.0 s | 136 |
| Released monitor | Source-defined completion, no collision or off-route | 47.0 s | 188 |
| One-second pulse starting at 0 s | Source-defined completion, no collision or off-route | 34.75 s | 139 |
| One-second pulse starting at 2.5 s | Source-defined completion, no collision or off-route | 35.25 s | 141 |

The admitted monitor pair takes 13 simulated seconds longer than nominal. Completion and
progress cost are separate observations; a binary non-collision result does not erase that cost.
The two pulse arms took 0.75 and 1.25 s longer than nominal. These observations describe
one exposed benign scenario, not a population harm rate or a proof of harmlessness. The later
pulse's ten pre-intervention frames matched nominal. The completion criterion remains the
simulator's qualified route rule; literal final-route-sample observation is false and retained.

[Nominal admission](proof/admissions/pair_003.json) ·
[monitor admission](proof/admissions/pair_004.json) ·
[time-zero pulse admission](proof/admissions/pair_005.json) ·
[later pulse and complete comparison](proof/admissions/pair_006.json).

## Actuation, intervention burden and timing

The following counts are per replica and agree across each pair. Monitor decisions are
replayed in every arm, but only the monitor arm delivers its changed plan. Shadow firings in
nominal or pulse arms are not applied interventions. Each pulse actually overrides four
acceleration commands; the nominal controller output preceding the override is a different
record. [Analysis implementation](proof/summarize.py.txt).

| Scenario / arm | Monitor firings | Braking-flag frames | Releases | Changed delivered-plan frames | Pulse-override frames |
|---|---:|---:|---:|---:|---:|
| Collision / monitor | 4 | 9 | 1 | 9 | 0 |
| Collision / early pulse | 1 | 4 | 0 | 0 | 4 |
| Collision / late pulse | 1 | 4 | 0 | 0 | 4 |
| Benign / nominal | 20 | 44 | 6 | 0 | 0 |
| Benign / monitor | 24 | 61 | 9 | 61 | 0 |
| Benign / early pulse | 14 | 34 | 5 | 0 | 4 |
| Benign / late pulse | 19 | 44 | 7 | 0 | 4 |

An [exploratory inspection](proof/applied_action_inspection.json) of the collision-case pulse
traces confirms actual braking. The early pulse reaches zero speed at 0.5 s, then the policy
returns to nominal after the pulse window and eventually collides. All logged actor states
in these four pulse episodes remain unchanged. This motivates a bounded maneuver-feasibility
diagnostic; it does not establish physical inevitability or a preregistered causal mechanism.

| Measurement, fourteen new episodes only | Retained observation |
|---|---:|
| Maximum checked stationarity residual | 9.8965212 × 10⁻⁷, below the fixed 10⁻⁶ bar |
| Complete controller-call median / maximum | 39.112 / 79.165 ms |
| Complete controller calls exceeding 50 ms | 37 / 1,420 |
| Full-loop median / maximum | 1.890 / 35.292 s |
| Full loops exceeding 250 ms | 1,420 / 1,420 |

The synchronous simulator waits for computation. Convergence passes while real-time operation
remains unestablished. Loop timing includes the final guard and stop decision, excludes reset,
summary serialization and worker cleanup, and does not isolate model inference from transport.

## Engineering and provenance

The [protocol](HYPOTHESIS.md) was committed at `3e696b8` before new execution. The fixed plan
contains fourteen new slots; original Iter151 remains closed and inconclusive with 2 admitted,
0 incomplete and 14 uninitialized. Original Iter148 remains unchanged. Historical scientific
workers, controller, monitor, outcome rules and validators were not edited.
Legacy `live_study_admitted:false` fields inside reused component reports retain their original
scope. The new plan, host permit, parent record and committed continuation receipt establish
this study's operational admission; historical fields were not rewritten.

Pre-live validation in ambient macOS Python 3.14.2: 382 regression tests passed with 40 retained
upstream warnings, then 74 final focused tests passed. The [real-data retention rehearsal](proof/retention_rehearsal.json)
preserved captured whitespace-bearing source through the new commit helper and original
scientific replay. It rechecked 62 historical actions and added zero new outcomes. The separate
new continuation chain checks include changed baseline evidence, receipt order, scenario and
block boundaries, duplicate launches, ownership and deadlines.

Actual Linux qualification passed before driving. A short systemd deadline expired; process
birth/command/boot and duplicate refusal were checked. A [separate structural audit](proof/host_independent_audit.json)
rejected eight corrupted records. The configured 2,500 s scientific cap did not need to expire.
These are automated checks, not independent human review or institutional certification.

The first local invocation used an incorrect source argument. Packet construction rejected it
before provider access, budget creation or any VM start. Its failure is retained under
[local attempt](proof/local_preflight_attempt_000/record.json); a visible
[pre-evidence amendment](PRE_EVIDENCE_AMENDMENT_001.md) records the corrected invocation.
Subsequent commands read the full verified source commit directly from the packet receipt.
This operational error created no scientific episode or extra compute envelope.

## Resource closure and limits

| Envelope | Local elapsed time | Conservative compute | Exact VM start / stop, provider UTC−07:00 |
|---|---:|---:|---|
| 0 | 1,103.223 s | $0.919 | 03:07:43.919 / 03:25:54.145 |
| 1 | 3,103.863 s | $2.587 | 03:26:46.349 / 04:18:16.222 |

Both are within their 10,800 s / $9 limits. Total conservative compute is **$3.506 within $18**;
costs exclude persistent storage and taxes and are not invoices. Both local watchdogs exited 0.
Both postflights found all 11,665 bound files and actor aliases unchanged, with no remaining
container or GPU process. VM ID `3834622546652649531` and both exact starts are bound in the
[combined resource closure](proof/resource_closure.json),
[first postflight](proof/block_000/postflight.json) and
[second postflight](proof/block_001/postflight.json).

The corrected archive → exact-byte Git commit → independent replay → committed admission
pipeline was exercised in the live Iter152 coordinator for all seven pairs. Each raw commit
precedes its receipt and the following pair. This closes the specific retention integration gap
from Iter151 under the new prospective protocol; the original Iter151 failure remains retained.
The source freeze and pre-live qualification records deliberately keep their original
`cloud_execution: unobserved` description of the evidence available at qualification time.

Both scenes are exposed development cases, not independent holdouts. Numerical replicas do not
increase the number of independent scenes. No population rate, physical-safety, transfer,
real-time execution or superiority to industrial teams follows. The [engineering review](ENGINEERING_REVIEW.md)
documents relevant public guidance and its limited application here. Master integration remains open.
Final local supply-chain verification and new authored source/analysis lint pass. Whole-repository
Ruff reports **832 findings in 168 files**, including 126 in seven newly retained unchanged
client snapshots. Explicit lint of the carried-forward Iter151 host auditor also reports seven
style findings; that script is an exact retained copy. No captured source was formatted or
excluded to erase findings. [Commands and validation scope](proof/final_validation.json).
Hosted run `38135368709` at scientific closure commit `e9b6fa2` passed supply-chain and
locked-install verification in both Python 3.10 and 3.11 jobs, then failed Ruff with 832
findings per job; later tests were skipped. [Hosted outcome](proof/hosted_ci_outcome.json).
The [dated automotive catalogue review](proof/standards_catalogue_review.json) retains exact
edition, publication, scope and revision observations for ISO 21448, ISO 34502 and UL 4600.
This is a review of public publisher material; normative compliance has not been audited.
