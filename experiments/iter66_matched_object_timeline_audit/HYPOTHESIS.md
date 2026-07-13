# Iteration 66 - matched-object hazard timeline audit

Status: `PRE_REGISTERED`

## Question

Iteration 64 found pre-contact monitor-object matches for the two rows that lacked first-fire
object support. Iteration 65 then showed those matched objects were present but subthreshold at
their best bridge-matched decision timestamps.

This iteration asks the next narrow timing question: across the full pre-contact decision
window, do those same matched monitor objects ever become active released-union hazards before
the first eligible foreground collision timestamp?

Targets are fixed from iteration 65:

- `ttc_extreme_short` / `scene-0038-extreme-00` / `object_id=2`;
- `cpa_medium_b` / `scene-0166-medium-00` / `object_id=6`.

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 proof artifacts and report;
- committed iteration-61 object-surface report;
- committed iteration-64 unsupported-temporal report;
- committed iteration-65 temporal-alignment report.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, or retune Sentinel.

## Registered procedure

For each fixed target object:

1. Cross-check the iteration-59, iteration-61, iteration-64, and iteration-65 verdicts and row
   identities before analysis.
2. Load the ON decision log and the first eligible foreground collision timestamp from the
   committed iteration-59 proof.
3. For every pre-contact decision frame (`ts < first_foreground_ts`), reconstruct the target
   object's released CPA/TTC metrics using the same frozen metric reconstruction as iterations
   62 and 65.
4. Count target-object presence, missing frames, active hazard frames, and borderline frames.
5. Record the first active hazard frame if any, the first borderline frame if any, minimum CPA,
   minimum TTC, and whether active/borderline emergence occurs before or after the iteration-65
   matched decision timestamp and before or after the first-fire timestamp.

Released hazard thresholds remain frozen:

- active CPA: `min_cpa < 1.5 m`;
- active TTC: `ttc < 2.5 s`;
- borderline CPA: `min_cpa < 3.0 m`;
- borderline TTC: `ttc < 5.0 s`.

## Registered verdicts

- `MATCHED_OBJECT_TIMELINE_EVER_HAZARD_COMPLETE`: both fixed target objects have at least one
  active released-union hazard frame before first foreground collision.
- `MATCHED_OBJECT_TIMELINE_NEVER_HAZARD_COMPLETE`: both fixed target objects are present in at
  least one pre-contact frame and have zero active released-union hazard frames before first
  foreground collision.
- `MATCHED_OBJECT_TIMELINE_MIXED_COMPLETE`: the two rows split between ever-active,
  never-active, or insufficient-presence labels.
- `MATCHED_OBJECT_TIMELINE_AUDIT_BLOCKED`: committed artifacts cannot reconstruct the fixed
  target-object timelines without new data.

## Claim boundary

This is a two-row target-object temporal surface audit only. It cannot claim actor identity,
actor causality, repair, transfer, safety, deployment readiness, robustness, benchmark ranking,
HD-Score invariance, population mismatch rate, or threshold retuning value.
