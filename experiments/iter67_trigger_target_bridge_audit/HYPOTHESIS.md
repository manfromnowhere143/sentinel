# Iteration 67 - trigger-target bridge audit

Status: `PRE_REGISTERED`

## Question

Iteration 66 split the two iteration-65 targets into two mechanisms:

- `ttc_extreme_short` / `object_id=2`: the bridge-matched target later becomes the first-fire
  TTC object exactly at first fire;
- `cpa_medium_b` / `object_id=6`: the bridge-matched target remains visible-never-active, while
  Sentinel first fires CPA-only on a different object (`object_id=1`).

This iteration asks whether the first-fire trigger object itself has foreground bridge support
under the same frozen bridge grid, or whether the evidence supports a trigger/target geometry
split: Sentinel fires on one monitor object while the foreground-bridged target object is another.

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 proof artifacts and report;
- committed iteration-61 object-surface report;
- committed iteration-64 unsupported-temporal report;
- committed iteration-65 temporal-alignment report;
- committed iteration-66 matched-object timeline report.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, or retune Sentinel.

## Registered procedure

For each fixed iteration-66 row:

1. Cross-check the iteration-59, iteration-61, iteration-64, iteration-65, and iteration-66
   verdicts and row identities before analysis.
2. Load the ON decision log and eligible foreground provenance rows from committed
   iteration-59 proof.
3. Identify:
   - the iteration-66 target object;
   - the unique first-fire trigger object from the committed first-fire reconstruction.
4. For both the target object and the first-fire trigger object, compare every pre-contact
   instance of that object to every eligible foreground provenance row using the same frozen
   16-variant bridge grid as iteration 64.
5. Record best target distance, best trigger distance, first-fire trigger distance, and whether
   trigger and target are the same object.

Bridge labels are frozen:

- `match`: distance `<= 3.0 m`;
- `ambiguous`: distance `> 3.0 m` and `<= 6.0 m`;
- `no_support`: distance `> 6.0 m`;
- `missing`: no evaluable object/foreground pair.

## Registered row labels

- `same_object_target_trigger_match`: target and trigger are the same object and the object has
  a bridge match.
- `same_object_target_trigger_nonmatch`: target and trigger are the same object but the object
  lacks a bridge match.
- `split_target_match_trigger_match`: target and trigger differ, and both have bridge matches.
- `split_target_match_trigger_ambiguous`: target and trigger differ, target has a bridge match,
  and trigger is bridge-ambiguous.
- `split_target_match_trigger_no_support`: target and trigger differ, target has a bridge
  match, and trigger has no bridge support.
- `trigger_target_bridge_insufficient`: committed artifacts cannot evaluate a required target
  or trigger bridge surface.

## Registered verdicts

- `TRIGGER_TARGET_SAME_AND_SPLIT_COMPLETE`: evaluated rows include at least one same-object
  target/trigger row and at least one split target/trigger row.
- `TRIGGER_TARGET_ALL_SAME_COMPLETE`: all evaluated rows are same-object target/trigger rows.
- `TRIGGER_TARGET_ALL_SPLIT_COMPLETE`: all evaluated rows are split target/trigger rows.
- `TRIGGER_TARGET_BRIDGE_AUDIT_BLOCKED`: committed artifacts cannot reconstruct the required
  trigger/target bridge surfaces without new data.

## Claim boundary

This is a two-row trigger/target bridge audit only. It cannot claim actor identity, actor
causality, repair, transfer, safety, deployment readiness, robustness, benchmark ranking,
HD-Score invariance, population mismatch rate, or threshold retuning value.
