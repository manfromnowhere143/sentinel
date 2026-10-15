# Equal ceilings yield the same three checkpoint witnesses

**Status: null for the frozen gain-without-loss claim.** The actual retained program
generator and the width-two stepwise beam each find a verified continuation through
frame 16 from the same three roots: calls 51, 91 and 131. There are **zero gains,
zero losses and zero censored pairs** across all 16 distinct retained late states.
Integrated qualification remains **3/4**; source comparison stays closed.

Each arm/root receives 128 attempted transitions and three seconds checked before
propagation. The 32 runs use a common checkpoint-feasibility objective and the
frozen route-target rule; they do not replay the original sampled targets. Both
arms retain the original physical, scene, checkpoint and absolute-clock rules.
The program arm preserves the analytic seed, three phase patterns, Halton order,
cache and invalid-suffix accounting. Its wrapper returns the first entire verified
checkpoint program. The beam preserves its proposals and retention at width two.
[Protocol](PROTOCOL.md) · [mathematical specification](MATHEMATICS.md).

| Root call | Program attempts | Beam attempts | Paired result |
|---|---:|---:|---|
| 3 | 128 | 16 | Both bounded misses |
| 51 | 112 | 78 | Both witnesses |
| 59 | 128 | 15 | Both bounded misses |
| 63 | 128 | 15 | Both bounded misses; prior progress exclusion |
| 64 | 128 | 75 | Both bounded misses |
| 67 | 126 | 16 | Both bounded misses |
| 69 | 126 | 45 | Both bounded misses |
| 84 | 128 | 45 | Both bounded misses |
| 85 | 126 | 15 | Both bounded misses |
| 88 | 126 | 15 | Both bounded misses |
| 91 | 4 | 77 | Both witnesses |
| 110 | 128 | 15 | Both bounded misses |
| 112 | 128 | 45 | Both bounded misses |
| 121 | 128 | 48 | Both bounded misses |
| 131 | 4 | 77 | Both witnesses |
| 132 | 128 | 105 | Both bounded misses; prior progress exclusion |

![Paired continuation work and outcomes](proof/continuation_comparison.png)

The program arm uses **1,776 transitions**, the beam **702**, for **2,478 total**
and 2,204 background queries. Equal ceilings do not imply equal work consumed.
All program misses stop at the reservation limit; a three-step program can leave
two attempts unused. All beam misses stop beam-empty. This is a finite search
result, not equivalence of the methods or proof of infeasibility. The two earlier
progress exclusions were searched in both arms and did not prune either search.
The remaining eleven misses remain unresolved.

Program witnesses for calls 91 and 131 use only their four-step initial program.
Call 51 uses 112 attempts and a two-phase acceleration program. Witnesses reach
only the first checkpoint; neither frame 32 nor route completion is established.
The exposed roots are related states from one development case, not independent
cases or a holdout population. No population confidence interval is inferred.

Independent admission checks **1,502 distinct full scalar masks / 9,814,068
point-state classifications**, including every queried state in both arms, selected
or unselected, valid or invalid suffix. It also checks 259 retained-path and 480
returned-path state records, proposals, cache, targets, motion, clocks, stopping
and complete mask inventory. Exact numerical disagreement would invalidate the
comparison even if coarse decisions agreed. Missing preempted queries remain absent.

Post-admission read-only inspection identifies a specific selection loss in the
original integrated record. Call 67, from root 51, evaluated a valid program through
frame 16 at evaluation 28 within its original 128-transition allowance. Its four
transition records exactly match the newly admitted program witness. Original
sampled-target ranking preferred frame 13 within that evaluation, then selected
frame 13 from evaluation 6 for the connection. The respective target distances are
6.011673 at the valid checkpoint, 2.898358 at the witness's first prefix, and
2.612032 at the returned prefix. Recomputing the original metric reproduces all
32 evaluation selections and the connection selection. This describes generated
work lost at selection; it does not establish the outcome of a different tree.
[Bound records](proof/selection_notes.json) · [read-only calculation](proof/describe_selection.py).

One frozen acquisition, raw commit, then separate admission. Supervised producer
and checker walls are **7.514 / 82.400 seconds**; both processes are reaped. Sixty-six
new constructed controls and 174 focused/retained tests pass with zero skips.
A real point-wall control demonstrates that the narrow beam can lose a program
witness; the retained null is not guaranteed by construction. No new integrated
schedule, driving episode, source recovery query, provider use or spending.
Actual-history recovery, intervention latency, safety, transfer and superiority
remain unestablished.

Frozen source: `999390d2e5135190c9c190a7f0ecc188b5b7a1a7`.
Raw committed before admission: `b9a86860a6b58c676c55620cf8ce9aa83a941128`.
Admission: `a133930242bca149801a1fbd9bb808ff2a8a36a1`.
[Independent admission](proof/admission.json) · [execution](proof/study_raw/execution.json) ·
[next decision](DECISION.md).
