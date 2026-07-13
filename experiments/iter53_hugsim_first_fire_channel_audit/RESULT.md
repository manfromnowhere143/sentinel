# Iteration 53 - HUGSIM first-fire channel audit: FIRST_FIRE_CHANNEL_COMPLETE

Status: `FIRST_FIRE_CHANNEL_COMPLETE` (offline post-result audit over committed iteration-48/49
HUGSIM proof only; zero GPU, zero gcloud, zero box reads, zero simulator launches, zero
retuning).

## Process Disclosure

This audit is not blind. Before `HYPOTHESIS.md` was frozen, the committed iteration-48 HUGSIM
patch was inspected and a small aggregate probe over the already-published iteration-52 timing
report was run. Both inspections are disclosed in the hypothesis. This result therefore makes no
inferential surprise claim and uses no statistical pass/fail bar.

## Registered Question

Iteration 52 found `35/92` ON-collision episodes where the monitor braked before the ON collision,
including `26` long-lead cases. Iteration 53 asks which side of the released union fired first in
those episodes and in the rest of the HUGSIM ON-collision set:

- `ttc_only`: `min_ttc < 2.5` and `min_cpa >= 1.5`;
- `cpa_only`: `min_cpa < 1.5` and `min_ttc >= 2.5`;
- `both`: both thresholds crossed on the first fired row;
- `no_fire`;
- `fired_channel_unreconstructable`.

## Evidence And Integrity

Inputs were exactly the committed artifacts named in `HYPOTHESIS.md`:

- iteration 48 `proof-stage2/episodes/`;
- iteration 49 `proof-hard/episodes/`;
- iteration 52 `proof-timing/on_collision_timing_report.json` for cross-checks only.

Analyzer command receipt:
[`proof-channel/analyze_first_fire_channel.command.txt`](proof-channel/analyze_first_fire_channel.command.txt).

Proof outputs:

- [`proof-channel/first_fire_channel_report.json`](proof-channel/first_fire_channel_report.json);
- [`proof-channel/first_fire_channel_pairs.md`](proof-channel/first_fire_channel_pairs.md).

Infrastructure checks passed:

- `104` paired HUGSIM transfer episodes read;
- pair count cross-checked against iteration 52 exactly: `104` vs `104`;
- timing-bin cross-check mismatches against iteration 52: `0`;
- no missing-file, schema, or unreconstructable-channel infrastructure problem fired.

## First-Fire Channel Result

Combined first-fire channels over all `104` ON-arm paired episodes:

| first-fire channel | count |
|---|---:|
| `ttc_only` | 40 |
| `cpa_only` | 36 |
| `no_fire` | 27 |
| `both` | 1 |
| `fired_channel_unreconstructable` | 0 |

Over the `92` ON-collision episodes:

| first-fire channel | count |
|---|---:|
| `ttc_only` | 36 |
| `cpa_only` | 33 |
| `no_fire` | 22 |
| `both` | 1 |
| `fired_channel_unreconstructable` | 0 |

Over the `35` pre-collision-fire ON-collision episodes (`short_lead_fire + long_lead_fire`):

| first-fire channel | count |
|---|---:|
| `cpa_only` | 19 |
| `ttc_only` | 16 |
| `both` | 0 |
| `no_fire` | 0 |
| `fired_channel_unreconstructable` | 0 |

The pre-collision-fire family is therefore split across both sides of the union. It is not one bad
branch, and it is not explained by the stricter simultaneous TTC+CPA surface proxy from iteration
52.

## Dataset Split

Iteration 48 easy+medium ON collisions (`40`):

- `cpa_only`: `16`;
- `ttc_only`: `14`;
- `no_fire`: `10`;
- `both`: `0`.

Iteration 48 pre-collision-fire ON collisions (`16`):

- `cpa_only`: `11`;
- `ttc_only`: `5`.

Iteration 49 hard/extreme ON collisions (`52`):

- `ttc_only`: `22`;
- `cpa_only`: `17`;
- `no_fire`: `12`;
- `both`: `1`.

Iteration 49 pre-collision-fire ON collisions (`19`):

- `ttc_only`: `11`;
- `cpa_only`: `8`.

Iteration 49 AttackPlanner split:

- AttackPlanner ON collisions (`30`): `ttc_only` `17`, `cpa_only` `6`, `no_fire` `6`,
  `both` `1`; pre-collision-fire channels `ttc_only` `9`, `cpa_only` `3`;
- non-AttackPlanner hard/extreme ON collisions (`22`): `cpa_only` `11`, `no_fire` `6`,
  `ttc_only` `5`, `both` `0`; pre-collision-fire channels `cpa_only` `5`, `ttc_only` `2`.

## Iteration 52 Cross-Tab

The iteration-52 timing bins crossed with first-fire channel give the sharper mechanism picture:

- `no_brake_no_surface_proxy`: `22` `no_fire`, matching iteration 52 exactly;
- `post_collision_first_brake`: `20` `ttc_only`, `14` `cpa_only`, `1` `both`;
- `short_lead_brake`: `7` `ttc_only`, `2` `cpa_only`;
- `long_lead_brake`: `17` `cpa_only`, `9` `ttc_only`;
- `excluded_no_on_collision`: `5` `no_fire`, `4` `ttc_only`, `3` `cpa_only`.

This confirms the scalar surface issue precisely: the simultaneous TTC+CPA proxy was too strict to
describe the actual released OR predicate. But even after reconstructing the OR predicate, the
pre-collision-fire persistent cases remain split across CPA-only and TTC-only first fires.

## Interpretation

Iteration 53 narrows the post-HUGSIM-null story:

1. The `22` no-fire ON-collision cases remain monitor-surface misses under the actual decision
   logs.
2. The `35` pre-collision-fire ON-collision cases are not a single-channel failure:
   `19` first fired through CPA-only and `16` through TTC-only.
3. The long-lead subset leans CPA-only (`17` CPA-only vs `9` TTC-only), while short-lead leans
   TTC-only (`7` vs `2`), but this is descriptive only.

The next mature pre-registration should therefore move from scalar first-fire timing to
object/path geometry and provenance: which object/path pair triggered the monitor, which object
or condition produced the HUGSIM collision, and whether HD-Score movement is dominated by terms
outside collision conversion. A one-branch threshold tweak is not supported by this audit.

## Boundaries

This result does not change iterations 48, 49, 50, 51, or 52. It makes no new safety, transfer,
deployment, robustness, benchmark-ranking, real-world, monitor-performance, HUGSIM-equivalence,
actor-identity, or retuning claim. The audit reconstructs scalar first-fire channels from the
committed decision logs; it cannot identify the true colliding actor and cannot select a new rule
family without a later fresh pre-registration.
