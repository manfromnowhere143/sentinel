# Iteration 88 - HUGSIM bridge/surface margin residual decomposition

Status: `PRE_REGISTERED`

## Question

Iteration 87 showed that support-object bridge-time replay is mixed: one support object reaches
borderline, while support object `10` remains subthreshold at both replay rows.

This iteration asks the immediate residual question:

When support-object provenance bridge evidence is paired with the iteration-87 replay-row released
surface metrics, are the remaining support-side outcomes explained as TTC-borderline/CPA-far for
object `9` and no-finite-TTC/CPA-far for object `10`?

This is a report-level margin decomposition. It is not a threshold search, repair, actor-causality
test, interpolation, or new simulator run.

## Frozen inputs

The audit is offline only and may read:

- committed iteration-85 path-horizon/provenance-timing report;
- committed iteration-87 interval bridge-time support-surface replay report.

It may import already-committed helper code from earlier iterations only for deterministic report
loading, finite-number checks, bridge-band checks, and compact proof formatting.

It must not launch GPU work, read live box state, create HUGSIM episodes, read raw decision logs,
modify simulator code, approve a patch, change thresholds, fit a transform, retune Sentinel,
interpolate metrics, or reinterpret simulation artifacts as live system state.

## Fixed rows

The fixed rows are exactly the three iteration-87 evaluated rows:

- `both_distinct_extreme` / `scene-0138-extreme-00` / pre event:
  support object `9`, support bridge `ambiguous`, replay timestamp `5.5 s`;
- `ttc_medium_a` / `scene-0071-medium-01` / pre event:
  support object `10`, support bridge `match`, replay timestamp `4.0 s`;
- `ttc_medium_a` / `scene-0071-medium-01` / active event:
  support object `10`, support bridge `match`, replay timestamp `5.75 s`.

## Registered procedure

1. Cross-check source verdicts before analysis:
   - iteration 85: `HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE`;
   - iteration 87: `HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE`.
2. Cross-check that iteration 85 contains exactly the fixed support objects and bridge bands
   above, with support bridge support present and selected bridge support absent.
3. Cross-check that iteration 87 contains exactly the fixed rows above, with no row problems and
   replay alignments `exact_bridge_ts`, `exact_bridge_ts`, and `nearest_before_bridge_ts`.
4. For each fixed row, read only the iteration-87 replay metric and iteration-85 support bridge
   summary.
5. Record:
   - support bridge band and best bridge distance;
   - replay released state;
   - replay `min_cpa`;
   - replay active CPA margin;
   - replay finite or missing TTC;
   - replay active TTC margin when finite;
   - replay borderline CPA/TTC flags;
   - replay CPA rank and TTC rank.
6. Assign one registered row label per fixed row.
7. Emit JSON and Markdown proof with per-row bridge/surface residual evidence.

## Registered labels

- `bridge_surface_ttc_borderline_cpa_far`: support bridge is `match` or `ambiguous`, replay state
  is `borderline`, replay TTC is finite and borderline, active TTC margin is positive, active CPA
  margin is at least `6.0 m`, and active CPA is not crossed.
- `bridge_surface_no_finite_ttc_cpa_far`: support bridge is `match` or `ambiguous`, replay state
  is `subthreshold`, replay TTC is missing, active CPA margin is at least `6.0 m`, and active CPA
  is not crossed.
- `bridge_surface_active`: support bridge is `match` or `ambiguous`, and replay state is
  `active`.
- `bridge_surface_other_residual`: support bridge is `match` or `ambiguous`, but none of the
  residual labels above applies.
- `bridge_surface_margin_residual_insufficient`: required source, row, bridge, state, metric, or
  margin fact is missing or inconsistent.

## Registered verdicts

- `HUGSIM_BRIDGE_SURFACE_MARGIN_RESIDUAL_SPLIT_COMPLETE`: every fixed row is classified as either
  `bridge_surface_ttc_borderline_cpa_far` or `bridge_surface_no_finite_ttc_cpa_far`, and both
  labels appear.
- `HUGSIM_BRIDGE_SURFACE_MARGIN_RESIDUAL_ACTIVE_COMPLETE`: at least one fixed row is
  `bridge_surface_active`, and no row is blocked.
- `HUGSIM_BRIDGE_SURFACE_MARGIN_RESIDUAL_OTHER_COMPLETE`: all fixed rows are classified without
  blocking, but neither complete verdict above holds.
- `HUGSIM_BRIDGE_SURFACE_MARGIN_RESIDUAL_BLOCKED`: source verdicts, fixed row identities,
  bridge facts, replay metrics, margins, or labels fail cross-checks, or any row is
  `bridge_surface_margin_residual_insufficient`.

## Claim boundary

This is a three-row descriptive bridge/surface margin residual decomposition only. It cannot claim
actor causality, repair, threshold value, transfer improvement, safety, deployment readiness,
robustness, benchmark ranking, HD-Score-invariance, population rate, retuning value, commercial
value, or real-world/first-responder behavior.
