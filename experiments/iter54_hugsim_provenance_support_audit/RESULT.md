# Iteration 54 - HUGSIM provenance support audit: PROVENANCE_SUPPORT_NULL

Status: `PROVENANCE_SUPPORT_NULL` (offline support audit over committed iteration-48/49 HUGSIM
proof only; zero GPU, zero gcloud, zero box reads, zero simulator launches, zero retuning).

## Process Disclosure

This audit is not blind. Before `HYPOTHESIS.md` was frozen, the post-iteration-53 successor rule,
proof directory shape, one ON decision-log schema, one HUGSIM `eval.json` schema, and the
committed iteration-48 HUGSIM patch were inspected. Those inspections are disclosed in the
hypothesis. This result therefore makes no inferential surprise claim and uses no statistical
pass/fail bar.

## Registered Question

Iteration 53 showed that the HUGSIM pre-collision-fire failures split across both sides of the
released union, so the next mature line is object/path provenance rather than threshold retuning.
Iteration 54 asks a support question:

Do the committed iteration-48/49 HUGSIM artifacts support reconstructing the monitor-side
first-hazard object/path, and do they support matching that hazard to the actual HUGSIM collision
actor?

## Evidence And Integrity

Inputs were exactly the committed artifacts named in `HYPOTHESIS.md`:

- iteration 48 `proof-stage2/episodes/`;
- iteration 49 `proof-hard/episodes/`;
- iteration 53 `proof-channel/first_fire_channel_report.json` for pair-count and first-fire
  cross-checks only.

Analyzer command receipt:
[`proof-provenance/analyze_provenance_support.command.txt`](proof-provenance/analyze_provenance_support.command.txt).

Proof outputs:

- [`proof-provenance/provenance_support_report.json`](proof-provenance/provenance_support_report.json);
- [`proof-provenance/provenance_support_pairs.md`](proof-provenance/provenance_support_pairs.md).

Infrastructure checks passed:

- `104` paired HUGSIM ON episodes read;
- pair count cross-checked against iteration 53 exactly: `104` vs `104`;
- first-fire channel mismatches against iteration 53: `0`;
- fire-timing mismatches against iteration 53: `0`;
- no parse, missing-file, schema, or argmin reconstruction infrastructure problem fired.

## Monitor-Side Provenance Result

Monitor first-fire argmin provenance is reconstructable from the committed decision logs.

Combined monitor provenance over all `104` ON-arm paired episodes:

| monitor provenance label | count |
|---|---:|
| `unique_ttc_object` | 40 |
| `unique_cpa_object` | 36 |
| `no_fire` | 27 |
| `both_distinct_objects` | 1 |
| `unique_both_same_object` | 0 |
| `ambiguous_cpa_object` | 0 |
| `ambiguous_ttc_object` | 0 |
| `argmin_reconstruction_failed` | 0 |
| `schema_unsupported` | 0 |

Over the `92` ON-collision episodes:

| monitor provenance label | count |
|---|---:|
| `unique_ttc_object` | 36 |
| `unique_cpa_object` | 33 |
| `no_fire` | 22 |
| `both_distinct_objects` | 1 |
| `unique_both_same_object` | 0 |
| `ambiguous_cpa_object` | 0 |
| `ambiguous_ttc_object` | 0 |
| `argmin_reconstruction_failed` | 0 |
| `schema_unsupported` | 0 |

Over the `35` pre-collision-fire ON-collision episodes:

| monitor provenance label | count |
|---|---:|
| `unique_cpa_object` | 19 |
| `unique_ttc_object` | 16 |
| all other labels | 0 |

This is a clean positive support finding for the monitor side only: the logged `objs`, `traj`,
`l2g_r_mat`, `l2g_t`, and scalar minima are enough to reconstruct which logged object produced
the first-fire CPA or TTC argmin. The single `both` first-fire case reconstructs as two distinct
objects, one for CPA and one for TTC.

## Collision-Actor Support Result

Collision-actor identity is not logged in the committed HUGSIM proof artifacts:

| collision actor support label | all pairs | ON-collision pairs |
|---|---:|---:|
| `collision_actor_not_logged` | 104 | 92 |
| `collision_actor_supported` | 0 | 0 |

The observed `eval.json` schema is scalar:

- top-level keys: `c`, `dac`, `details`, `hdscore`, `nc`, `pdms`, `rc`, `ttc`;
- per-step detail keys: `c`, `dac`, `nc`, `pdms`, `ttc`;
- collision actor identity fields found: none.

Therefore the committed evidence does not support matching "the object Sentinel braked for" to
"the actor HUGSIM says the ego collided with." Any such actor-match claim requires new
instrumentation in a future run.

## Dataset Split

Iteration 48 easy+medium:

- monitor provenance over all `52` ON episodes: unique CPA object `19`, unique TTC object `18`,
  no fire `15`;
- ON-collision episodes `40`: unique CPA `16`, unique TTC `14`, no fire `10`;
- pre-collision-fire ON-collision episodes `16`: unique CPA `11`, unique TTC `5`;
- collision actor support: `0/52` supported, `0/40` among ON-collision episodes.

Iteration 49 hard/extreme:

- monitor provenance over all `52` ON episodes: unique TTC object `22`, unique CPA object `17`,
  no fire `12`, both-distinct-objects `1`;
- ON-collision episodes `52`: same counts;
- pre-collision-fire ON-collision episodes `19`: unique TTC `11`, unique CPA `8`;
- collision actor support: `0/52` supported.

Iteration 49 AttackPlanner split:

- AttackPlanner episodes `30`: unique TTC `17`, unique CPA `6`, no fire `6`,
  both-distinct-objects `1`; pre-collision-fire unique TTC `9`, unique CPA `3`;
- non-AttackPlanner episodes `22`: unique CPA `11`, no fire `6`, unique TTC `5`;
  pre-collision-fire unique CPA `5`, unique TTC `2`;
- collision actor support: `0` in both groups.

## Interpretation

Iteration 54 separates two surfaces that should not be conflated:

1. The monitor side is strong enough for object/path provenance reconstruction. For every fired
   episode, the first-fire scalar argmin reconstructs from committed logs with no ambiguity except
   the single `both` case, where the CPA and TTC argmins are distinct objects.
2. The collision side is not strong enough for actor matching. HUGSIM's committed `eval.json`
   stores scalar metric time series, not collision actor identity.

The next credible HUGSIM run, if one is launched later under a fresh pre-registration, should add
instrumentation that logs collision actor/object identity or enough simulator contact/proximity
state to bind the HUGSIM `nc` drop to an actor. Without that, the repository can say which object
the monitor braked for, but cannot say whether it was the object that caused the HUGSIM collision.

## Boundaries

This result does not change iterations 48, 49, 50, 51, 52, or 53. It makes no new safety,
transfer, deployment, robustness, benchmark-ranking, real-world, monitor-performance,
HUGSIM-equivalence, actor-identity, actor-match, or retuning claim. It is a provenance support
audit only.
