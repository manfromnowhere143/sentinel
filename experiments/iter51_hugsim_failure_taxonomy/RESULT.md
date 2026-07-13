# Iteration 51 - HUGSIM transfer-failure taxonomy: TAXONOMY_COMPLETE

Status: `TAXONOMY_COMPLETE` (offline post-result audit over committed iteration-48/49
HUGSIM proof only; zero GPU, zero gcloud, zero box reads, zero new simulator launches).

## Registered Question

Iterations 48 and 49 established the transfer null: the released union fires, latches, and
releases on HUGSIM, but the paired HD-Score benefit does not measurably transfer. Iteration
50 then resolved P1: iteration 49 had primary collision opportunity in `51/52` OFF episodes,
so the failure is real, not opportunity-scarce.

Iteration 51 asks only the narrower post-result question: how do those HUGSIM nulls decompose
under a frozen failure taxonomy?

## Evidence And Integrity

Inputs were exactly the committed artifacts named in `HYPOTHESIS.md`:

- iteration 48 `proof-stage2/episodes/` and `transfer_report.json`;
- iteration 49 `proof-hard/episodes/` and `transfer_report.json`;
- iteration 49 `proof-hard/p1_opportunity_report.json` for the published P1 count cross-check.

Analyzer command receipt:
[`proof-taxonomy/analyze_failure_taxonomy.command.txt`](proof-taxonomy/analyze_failure_taxonomy.command.txt).

Proof outputs:

- [`proof-taxonomy/failure_taxonomy_report.json`](proof-taxonomy/failure_taxonomy_report.json);
- [`proof-taxonomy/failure_pairs.md`](proof-taxonomy/failure_pairs.md).

Infrastructure checks passed:

- `104` paired HUGSIM episodes classified (`52` iteration 48, `52` iteration 49);
- transfer-report point means reproduced exactly for both datasets;
- P1 cross-check matched the published count: `51` recomputed vs `51` recorded, branch
  `B_REFUTED`;
- no schema or missing-file infrastructure problem fired.

## Frozen Taxonomy Result

Combined category counts over the `104` paired HUGSIM transfer episodes:

| category | count |
|---|---:|
| `persistent_collision_late_by_proxy` | 34 |
| `persistent_collision_early_by_proxy` | 33 |
| `persistent_collision_no_brake` | 18 |
| `induced_collision` | 7 |
| `clean_no_off_opportunity` | 6 |
| `converted_collision_no_material_gain` | 4 |
| `converted_collision_material_gain` | 2 |

The frozen dominance rule did **not** identify one combined dominant category:
`mixed_taxonomy` (`34/91 = 0.374` of OFF-opportunity pairs for the largest category, below
the `0.40` bar).

The main decomposition:

- OFF-opportunity pairs: `91/104`;
- persistent collision pairs: `85/104`;
- converted collision pairs: `6/104`;
- material HD gains above the descriptive `0.03` deadband: `24/104`;
- material HD losses below `-0.03`: `28/104`;
- score-loss-under-brake pairs: `21/104`.

## Dataset Split

Iteration 48 easy+medium (`52` pairs):

- OFF-opportunity pairs: `40/52`;
- persistent collision pairs: `34/52`;
- converted collision pairs: `6/52`;
- largest OFF-opportunity category: `persistent_collision_early_by_proxy`, `14/40 = 0.350`
  (below dominance bar);
- mean delta reproduced: `-0.016636793770462406`.

Iteration 49 hard/extreme (`52` pairs):

- OFF-opportunity pairs: `51/52`;
- persistent collision pairs: `51/52`;
- converted collision pairs: `0/52`;
- largest OFF-opportunity category: `persistent_collision_late_by_proxy`, `21/51 = 0.412`
  (dominant inside iteration 49 only);
- mean delta reproduced: `-0.008912334107860385`.

AttackPlanner split inside iteration 49:

- AttackPlanner scenarios: `30/30` OFF-opportunity pairs, `30/30` persistent collisions,
  largest category `persistent_collision_late_by_proxy` (`15/30 = 0.500`), mean delta
  `-0.019026675581778858`;
- non-AttackPlanner hard/extreme scenarios: `21/22` OFF-opportunity pairs, `21/22`
  persistent collisions, largest category `persistent_collision_early_by_proxy`
  (`10/21 = 0.476`), mean delta `+0.004879949720210261`.

## Interpretation

The failure is not one clean story. The released union almost never converts HUGSIM
collisions: only `6/91` OFF-opportunity pairs become non-collision ON pairs, and only `2`
of those clear the descriptive material-gain deadband. Most opportunity remains a collision
after the monitor is applied.

The hard/extreme tier is especially informative: it has near-universal opportunity
(`51/52`) and zero conversions. AttackPlanner scenarios lean toward the late-by-proxy bucket;
non-AttackPlanner harder scenes lean toward early-by-proxy persistence. That split argues
against simply widening the frozen monitor or retuning a threshold as the next mature move.

The honest next pre-registration should therefore be a narrower mechanism-cause audit, not a
new transfer claim: explain whether HUGSIM persistence is caused by timing, wrong hazard
surface, planner/path geometry, or HD-Score components outside collision conversion.

## Boundaries

This result does **not** change iteration 48 or 49. Both transfer nulls stand. This audit makes
no new safety, deployment, robustness, benchmark-ranking, real-world, monitor-performance, or
HUGSIM-equivalence claim. The timing labels are descriptive proxies only because OFF and ON
trajectories are stochastic and not frame-identical.
