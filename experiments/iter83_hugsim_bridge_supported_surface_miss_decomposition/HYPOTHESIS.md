# Iteration 83 - HUGSIM bridge-supported surface-miss decomposition

Status: `PRE_REGISTERED`

## Question

Iteration 82 showed that the two fixed support objects both have same-object foreground bridge
support, but neither has an active same-frame released-surface co-occurrence. Object `9` has only
borderline bridge+surface co-occurrence, while object `10` has bridge support in every present
frame and never reaches the released CPA/TTC surface.

This iteration asks the immediate decomposition question:

When a fixed support object is bridge-supported, which released-surface channel prevents active
same-frame co-occurrence: CPA distance, TTC/closing, or a mixed channel pattern?

## Frozen inputs

The audit is offline only and may read:

- committed iteration-59 actor-match report and proof episode artifacts, including `eval.json`
  and `sentinel_iter48_decisions.jsonl`;
- committed iteration-82 support-object surface/provenance co-occurrence report.

It may import already-committed helper code from earlier iterations only for deterministic report
loading, decision-row loading, foreground provenance loading, frozen bridge-variant generation,
per-object CPA/TTC metric reconstruction, threshold-state classification, and compact proof
formatting.

It must not launch GPU work, read live box state, create HUGSIM episodes, modify simulator code,
approve a patch, change thresholds, fit a transform, retune Sentinel, or reinterpret simulation
artifacts as live system state.

## Fixed support objects

The fixed support objects are exactly the two iteration-82 objects:

- `both_distinct_extreme` / `scene-0138-extreme-00` / support object `9`;
  iteration-82 label `support_surface_bridge_borderline_only`;
- `ttc_medium_a` / `scene-0071-medium-01` / support object `10`;
  iteration-82 label `support_bridge_never_surface`.

## Registered procedure

1. Cross-check source verdicts before analysis:
   - iteration 59: `ACTOR_MATCH_AUDIT_COMPLETE`;
   - iteration 82: `HUGSIM_SUPPORT_SURFACE_BRIDGE_BORDERLINE_ONLY_COMPLETE`.
2. Cross-check that iteration 82 contains exactly the two fixed support objects above with no
   object-level problems and with the registered labels above.
3. For each fixed support object, load only the committed iteration-59 ON decision log and
   `eval.json` from the episode directory recorded in the iteration-59 report.
4. Recompute same-object bridge support using the iteration-82/iteration-76 bridge procedure, and
   keep only frames whose bridge band is `match` or `ambiguous`.
5. For every bridge-supported frame, reconstruct the fixed support object's released CPA/TTC
   metric state using the row's logged thresholds.
6. For every bridge-supported frame, record:
   - bridge band and best bridge distance;
   - released surface state (`active`, `borderline`, or `subthreshold`);
   - `min_cpa`, finite or missing `ttc`, `cpa_rank`, `ttc_rank`, `gap`, `closing`, and score;
   - active CPA margin: `min_cpa - cpa_margin`;
   - active TTC margin: `ttc - ttc_thresh` when TTC is finite, else `None`;
   - borderline CPA margin: `min_cpa - 3.0`;
   - borderline TTC margin: `ttc - 5.0` when TTC is finite, else `None`;
   - whether the frame is CPA-active, TTC-active, CPA-borderline, or TTC-borderline.
7. For each object, summarize bridge-supported frames:
   - total bridge-supported frames;
   - active bridge-supported frames;
   - borderline bridge-supported frames;
   - subthreshold bridge-supported frames;
   - finite-TTC bridge-supported frames;
   - minimum active CPA margin;
   - minimum active TTC margin, if any finite TTC exists;
   - minimum borderline CPA/TTC margins;
   - the best frame for each surface channel.
8. Assign one registered object label per fixed support object.
9. Emit JSON and Markdown proof with per-object channel summaries and compact frame evidence.

## Registered object labels

Labels are assigned in this order:

- `bridge_supported_active_surface_present`: at least one bridge-supported frame is active.
- `bridge_supported_borderline_ttc_only`: no bridge-supported frame is active, and at least one
  bridge-supported frame is TTC-borderline with no CPA-borderline frame.
- `bridge_supported_borderline_cpa_only`: no bridge-supported frame is active, and at least one
  bridge-supported frame is CPA-borderline with no TTC-borderline frame.
- `bridge_supported_borderline_mixed`: no bridge-supported frame is active, and bridge-supported
  borderline frames include both CPA-borderline and TTC-borderline evidence.
- `bridge_supported_subthreshold_no_finite_ttc`: every bridge-supported frame is subthreshold and
  no bridge-supported frame has finite TTC.
- `bridge_supported_subthreshold_finite_ttc_far`: every bridge-supported frame is subthreshold
  and at least one bridge-supported frame has finite TTC.
- `bridge_supported_surface_miss_insufficient`: required source, log, object, foreground,
  threshold, metric, or bridge facts are missing or inconsistent, or the fixed object has no
  bridge-supported frames.

## Registered verdicts

- `HUGSIM_BRIDGE_SUPPORTED_ACTIVE_SURFACE_PRESENT_COMPLETE`: at least one fixed support object is
  `bridge_supported_active_surface_present` and no object is blocked.
- `HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_MIXED_COMPLETE`: no object is active, no object is
  blocked, and at least two non-active object-label families appear.
- `HUGSIM_BRIDGE_SUPPORTED_BORDERLINE_TTC_ONLY_COMPLETE`: every classified non-active object is
  `bridge_supported_borderline_ttc_only`.
- `HUGSIM_BRIDGE_SUPPORTED_BORDERLINE_CPA_ONLY_COMPLETE`: every classified non-active object is
  `bridge_supported_borderline_cpa_only`.
- `HUGSIM_BRIDGE_SUPPORTED_SUBTHRESHOLD_NO_TTC_COMPLETE`: every classified non-active object is
  `bridge_supported_subthreshold_no_finite_ttc`.
- `HUGSIM_BRIDGE_SUPPORTED_SUBTHRESHOLD_FINITE_TTC_COMPLETE`: every classified non-active object
  is `bridge_supported_subthreshold_finite_ttc_far`.
- `HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_BLOCKED`: source verdicts, fixed object identities,
  decision logs, object metrics, thresholds, foreground provenance, or bridge facts fail
  cross-checks, or any object is `bridge_supported_surface_miss_insufficient`.

## Claim boundary

This is a two-object descriptive bridge-supported surface-miss decomposition only. It cannot claim
actor causality, repair, threshold value, transfer improvement, safety, deployment readiness,
robustness, benchmark ranking, HD-Score-invariance, population rate, retuning value, or commercial
value.
