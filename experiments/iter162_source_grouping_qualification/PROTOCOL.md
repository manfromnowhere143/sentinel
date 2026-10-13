# Iter162: matched source-model qualification

Freeze PLAN, this protocol, the decision packet, qualifications and source inventory
before source search outcomes. One acquisition, two fixed arms, raw commit before
independent admission. No outcome-driven tuning, retries or additional arms.

## Population and intervention

One already exposed source model, scene-0013-medium-00. Preserve the Iter153 reset,
route, foreground and model contract, and the entire Iter155 selected background:
276,519 binary32 centers. Inputs are content-bound to the retained files. The checker
reconstructs semantic/opacity selection from the full population and compares every
selected point. This is static privileged geometry, not a new native driving episode.

Fixed order: quantized grouping/width24, exact grouping/width24. Import the unchanged
Iter161 search directly. Both use the same route guide, proposals, speed-group beam
ordering, duplicate-command removal, hard checks, completion and stopping. Only the
state key changes. Exact grouping preserves all five binary64 state components,
signed zero and absolute frame; quantized grouping retains the original cells.
The source scene has no independently known complete constructive witness. Do not
invent one or turn witness-free admission into a feasibility guarantee.

Each arm receives 60,000 attempted transitions, 401 actions and 1,800 search seconds.
Attempts include hard rejections. Search queries include the reset; materialization
queries are counted separately. The same caps do not imply equal actual work, depth
or time. A completed depth may admit a complete path before the beam is truncated;
an interrupted partial depth admits neither a new beam nor completion. Failed search
returns its recorded best prefix from completed depths. All results are retained.
The timer's inherited reset-query exclusion is covered by the producer envelope.

Preserve the 0.25-second bicycle model, acceleration/steering/speed/yaw/lateral bounds,
foreground sweep and margin, route distance <=10 m, and progress slack 0.05. Absolute
progress requirements remain 7.75 s / 0.32925097621583244 and 9 s / 0.32215122470713525,
before slack. Strict background count >100 and numerical ambiguity policy are
unchanged. Every sampled selected state must be clear. Complete admission must
observe both checkpoints; partial prefixes report only those actually observed.
Nearest-index 90%-route completion remains the original modeled outcome.

## Measurements and decision

Primary claim: exact grouping at width24 finds a complete independently admitted
path on this retained source model within this envelope. A valid completion supports
that bounded claim; a valid miss contradicts it. Missing evidence, admission failure,
identity mismatch or resource violation makes the study invalid, not a search miss.
Quantized/24 is a matched comparator. Report completion contrast, both stopping
reasons, attempts, queries, depths, progress, selected-state background maxima and
observed checkpoints. Report grouping removals, width removals and retained nodes
at complete depths; partial survivors separately. These are repeated events, not
unique paths or causal failure contributions. No statistical population claim.
Iter158's endpoint-guided search is historical context, not the matched comparator.

Independent admission reconstructs selected-path dynamics, controls, foreground
and sweep, route, progress, all full scalar background masks, and completion. It
independently reconstructs the population and mechanically replays grouping and
beam selection from retained clear labels and guide scores. It does not recompute
every unselected hard predicate or guide score. Raw inventory, Git source ancestry,
byte identity, initialization and resource records must all match.

No physical safety, continuous background clearance, road compliance, source
infeasibility, native recovery, actual decision-time responsiveness, information
advantage, transfer or competitor superiority follows. A complete reset-time path
is only a prerequisite for a separately registered native eligibility check.
If exact/24 misses, stop default bespoke search expansion and qualify a released
kinodynamic adapter before considering another source search.

## Resources and reproducible execution

Local CPU; no provider, GPU or spend. Producer <=4,200 s; checker <=3,000 s; each
<=1 GiB peak RSS. Raw <=256 MiB, at least 2 GiB free before initialization.
Reserve 64 MiB beyond streamed search logs for at most 804 selected masks and
trace/final records. Setup, search, materialization and admission costs are reported
separately. Preserve partial files and a failure record if acquisition fails.
Time-budget stopping is a valid capped miss if the full acquisition/admission
still meets its envelope; wall-time comparisons remain exploratory and order-bound.

The source route's relaxed geometric/acceleration lower bound is about 58 actions.
An 18,000 cap can stop a full width24 beam near depth50 even at 15 proposals per
parent. The larger prospective cap removes that evident planning mismatch without
promising completeness. Historical vector query median was 16.564 ms; scalar
median 1,460.081 ms. These are planning measurements, not guaranteed current rates.

Run from the frozen source HEAD, substituting its actual full Git hash:

```bash
python3 -m experiments.iter162_source_grouping_qualification.run --root . --output experiments/iter162_source_grouping_qualification/proof/raw --source FULL_SOURCE_HASH
```

Commit raw before running the separate checker with the actual raw commit:

```bash
python3 -m experiments.iter162_source_grouping_qualification.check --root . --raw experiments/iter162_source_grouping_qualification/proof/raw --raw-commit FULL_RAW_HASH --output experiments/iter162_source_grouping_qualification/proof/admission.json
```
