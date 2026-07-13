# Iteration 65 - matched pre-contact temporal alignment audit

Status: `PRE_REGISTERED`

## Question

Iteration 64 showed that the two iteration-61 rows with no first-fire monitor-object support are
not globally object-unsupported: each has at least one pre-contact monitor object that matches a
HUGSIM foreground provenance row under the frozen bridge grid. That result does not tell us
whether the matched monitor object was an active released-union hazard at its matched decision
time, or whether it was only visible geometry that never crossed the Sentinel hazard surface.

This iteration asks that narrower timing/provenance question for exactly those two Iteration-64
matches:

- `ttc_extreme_short` / `scene-0038-extreme-00`;
- `cpa_medium_b` / `scene-0166-medium-00`.

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 proof artifacts and report;
- committed iteration-61 object-surface report;
- committed iteration-64 unsupported-temporal report.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, or retune Sentinel.

## Registered procedure

For each Iteration-64 best pre-contact match:

1. Load the matched decision timestamp, matched monitor `object_id`, matched foreground
   timestamp, and bridge variant from the Iteration-64 report.
2. Reconstruct the monitor-object metrics at that exact decision timestamp from the committed
   iteration-59 ON decision logs.
3. Classify the matched object as one of:
   - `matched_object_active_hazard`: the matched object is present and crosses the released TTC
     or CPA fire surface at that decision timestamp;
   - `matched_object_subthreshold`: the matched object is present but crosses neither released
     fire surface at that decision timestamp;
   - `matched_object_missing`: the matched object cannot be reconstructed at that decision
     timestamp despite the Iteration-64 match.
4. Record the first-fire timestamp, first-fire channel/object summary, and whether the matched
   object is the first-fire trigger object.

## Registered verdicts

- `TEMPORAL_ALIGNMENT_ACTIVE_HAZARD_COMPLETE`: both Iteration-64 matched objects are active
  released-union hazards at their matched timestamps.
- `TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE`: both Iteration-64 matched objects are present but
  subthreshold at their matched timestamps.
- `TEMPORAL_ALIGNMENT_MIXED_COMPLETE`: rows classify into a non-empty mix of active-hazard,
  subthreshold, or missing labels.
- `TEMPORAL_ALIGNMENT_AUDIT_BLOCKED`: committed artifacts cannot reconstruct a required matched
  object or first-fire summary without new data.

## Claim boundary

This is a two-row temporal/provenance alignment audit only. It cannot claim actor identity,
actor causality, repair, transfer, safety, deployment readiness, robustness, benchmark ranking,
HD-Score invariance, population mismatch rate, or threshold retuning value.
