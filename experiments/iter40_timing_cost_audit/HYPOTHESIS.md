# Iteration 40 - timing and intervention-cost audit pre-registration

Frozen after iteration 39 was published as `CLAIM_AUDIT_DOC_NARROWING_REQUIRED`, and before any
iteration-40 analyzer, timing table, cost table, proof report, documentation claim update, gcloud
command, Docker command, model replay, sensor-degradation run, adversarial-perturbation run,
iteration-38 calibration replay, heldout replay, selector evaluation, or closed-loop work.

Iteration 40 is an offline deployment-trade-off audit over committed evidence. It does not tune the
monitor, replay the planner, or create new safety evidence. Its purpose is to quantify what the
repository can defensibly say about intervention timing and intervention cost in simulation, and
to identify what remains untested for real-time or production claims.

This is the first concrete successor chosen by iteration 39's defensibility rule.

## Research question

Using only committed full14/power and verification decision logs plus committed run archives, what
is the released union's intervention timing and intervention-cost envelope in the measured
simulation, and which latency/cost claims remain unsupported?

Acceptable positive claim if every bar passes:

> On committed simulation evidence, the released union's intervention budget and reconstructable
> counterfactual-contact lead-time coverage are quantified at the run/frame level, with exact
> unsupported boundaries for wall-clock latency, production cost, and real-world deployment.

Acceptable negative claim if coverage or joins fail:

> The committed evidence is insufficient for a full timing/cost audit; active docs must not make
> timing, latency, cheapness, or deployment-cost claims beyond the previously published narrow
> safety-case summaries.

Forbidden claims, even on a pass:

- no wall-clock real-time inference latency claim;
- no production compute-cost, fleet-cost, certification, or real-vehicle claim;
- no sensor-degradation, adversarial, cross-planner, or deployment-readiness claim;
- no claim that intervention cost is acceptable to passengers, regulators, or traffic;
- no claim that iteration 38 passed calibration or any closed-loop gate;
- no new benchmark, selector, heldout, or safety result.

## Frozen input artifacts

Iteration 40 may read only committed artifacts:

- `experiments/iter39_external_validity_claim_audit/RESULT.md`;
- `experiments/full14_power/RESULT.md`;
- `experiments/full14_power/proof/analysis_output.txt`;
- `experiments/full14_power/proof/p14-runs.tar.gz`;
- `experiments/full14_power/proof/sentinel-power14-merged.log`;
- `experiments/full14_power/proof/sentinel_p14_best.jsonl.gz.part-aa`;
- `experiments/full14_power/proof/sentinel_p14_best.jsonl.gz.part-ab`;
- `experiments/full14_power/proof/sentinel_p14_off.jsonl.gz.part-aa`;
- `experiments/full14_power/proof/sentinel_p14_off.jsonl.gz.part-ab`;
- `experiments/full14_power/proof/sentinel_p14_off.jsonl.gz.part-ac`;
- `experiments/verification/README.md`;
- `experiments/verification/analyze_safety_case.py`;
- `experiments/verification/proof_v20.txt`;
- `experiments/verification/evidence/jsonl/sentinel_i8_union.jsonl.gz`;
- `experiments/verification/evidence/jsonl/sentinel_i8_off.jsonl.gz`;
- `experiments/verification/evidence/runs/i8-union.tar.gz`;
- `experiments/verification/evidence/runs/i8-off.tar.gz`;
- `experiments/verification/evidence/logs/sentinel-i8.log`;
- `experiments/iter15_latch_release/RESULT.md`;
- `docs/REPORT.md`;
- `docs/paper/MANUSCRIPT.md`;
- `README.md`.

Iteration 40 must not read remote GPU files, uncommitted logs, unpublished iteration-38 calibration
output, fresh model output, external web sources, or any dataset files outside committed archives.

## Known artifact facts frozen for integrity checks

The full14/power evidence is known to include relaunch history and one missing OFF metric run. The
audit must preserve that messiness instead of cleaning it away:

- `experiments/full14_power/proof/analysis_output.txt` reports H-P0 PASS;
- the scorer archive contains `400` `p14-best` `metrics.json` files across `20` scenario pairs;
- the scorer archive contains `399` `p14-off` `metrics.json` files across `20` scenario pairs;
- the published analysis reports `side-0921` as `n=19/20` for OFF and `n=20/20` for best;
- reconstructed `sentinel_p14_best.jsonl.gz` has `400` reset blocks, `7,835` non-reset frames,
  and `1,205` rows carrying the `brake` key;
- reconstructed `sentinel_p14_off.jsonl.gz` has relaunch/duplicate reset history and must not be
  treated as a one-reset-per-completed-run source.

If any of these facts differ, publish an infrastructure null and stop before timing/cost
interpretation.

## Frozen metric definitions

Episode identity:

- full14/power completed episodes are keyed by `(arm, scenario_class, scenario_id, run_index)` from
  `p14-runs.tar.gz` and `sentinel-power14-merged.log`;
- `p14-best` decision-log blocks are aligned to the `20` scenario pairs in run-script order and
  run index order only after S0 proves `400` reset blocks;
- `p14-off` decision-log reset blocks are not a completed-episode source because of relaunch
  duplicates; OFF timing uses `p14-runs.tar.gz` instead.

Intervention-cost metrics:

- `brake_frame_count`: number of best-arm decision rows with a `brake` key for an episode;
- `intervention_episode`: `brake_frame_count > 0`;
- `first_brake_frame_index` and `first_brake_timestamp_us`;
- `last_brake_frame_index` and `last_brake_timestamp_us`;
- `brake_duration_s = (last_brake_timestamp_us - first_brake_timestamp_us) / 1e6` for episodes
  with at least two brake frames, otherwise `0`;
- `ego_distance_m`: path length from committed `ego_poses.json`;
- `brake_frames_per_km = brake_frame_count / max(ego_distance_km, 1e-9)`;
- summaries by scenario class and by scenario pair.

Lead-time metrics:

- use OFF-arm committed `actors.json` and `ego_poses.json` for the same `(scenario_class,
  scenario_id, run_index)` to reconstruct the first counterfactual contact crossing at the
  registered `2.0 m` center-distance plane;
- use only episodes where OFF has a reconstructable contact time and best has at least one brake;
- `lead_time_s = (off_contact_timestamp_us - best_first_brake_timestamp_us) / 1e6`;
- negative lead time is allowed and must be reported as late intervention, not clipped.

Coverage metrics:

- number and fraction of best episodes with a joined `metrics.json`, `ego_poses.json`, and
  decision-log block;
- number and fraction of best intervention episodes with reconstructable OFF contact time;
- number and fraction excluded by missing OFF run, no OFF contact crossing, no best brake, or
  malformed archive member.

## S0 - artifact and join integrity

S0 passes only if:

- every frozen input path exists and is committed;
- full14/power H-P0 is PASS in the committed analysis output;
- `p14-runs.tar.gz` contains `400` best metrics files and `399` OFF metrics files across `20`
  scenario pairs;
- the published `side-0921` OFF `n=19/20` exception is detected and recorded;
- reconstructed `sentinel_p14_best.jsonl.gz` matches the frozen `400` reset blocks, `7,835`
  non-reset frames, and `1,205` brake-key rows;
- the analyzer does not use `p14-off` decision-log reset blocks as completed episodes;
- every `p14-best` completed episode joins exactly one decision-log block and one run-archive
  ego path;
- no gcloud, Docker, model replay, selector, heldout, or closed-loop command runs.

If S0 fails, publish `TIMING_COST_INFRASTRUCTURE_NULL` and stop.

## S1 - intervention-cost coverage bars

S1 passes only if cost metrics are complete enough to support a simulation intervention-budget
claim:

- all `400/400` best completed episodes have `brake_frame_count`, intervention flag, and ego
  distance;
- scenario-pair summaries cover all `20/20` scenario pairs;
- class summaries cover `stationary`, `frontal`, and `side`;
- at least one summary is emitted for OFF-noncollision episodes and at least one for OFF-collision
  episodes, so the audit distinguishes benign-ish cost from safety-critical cost;
- the report includes total brake frames, intervention episodes, median brake frames per
  intervention episode, p95 brake frames per intervention episode, and brake frames per km.

If S1 fails, publish `TIMING_COST_NULL_COST_COVERAGE_INCOMPLETE`. No intervention-cost claim is
authorized.

## S2 - lead-time coverage bars

S2 passes only if lead-time reconstruction is explicit about coverage:

- every best intervention episode is assigned exactly one lead-time status:
  `measured`, `no_off_contact_crossing`, `missing_off_run`, `no_best_brake`, or `malformed`;
- at least `20` measured lead-time episodes exist across at least two scenario classes;
- the report includes median, p05, p95, min, max, and fraction negative for measured lead times;
- excluded episodes are reported by scenario class and reason.

If S2 fails, publish `TIMING_COST_NULL_LEADTIME_COVERAGE_INCOMPLETE`. Intervention-cost metrics may
still be reported, but no broad lead-time claim is authorized.

## S3 - unsupported latency/deployment-cost boundary

S3 passes only if the RESULT and any active-doc edits state all boundaries:

- decision-log timing is simulation timestamp timing, not wall-clock inference latency;
- brake-frame count is intervention budget, not passenger comfort or production cost;
- full14/power safe-progress remains a tight null, not a deployment win;
- sensor degradation, adversarial perturbation, and real-world deployment trade-offs remain
  untested.

If S3 fails, publish `TIMING_COST_OVERCLAIM_NULL` and narrow the active docs before any new
GPU/model work.

## Named falsifiers

- **Artifact drift.** Required committed archives/logs are missing, untracked, unreadable, or no
  longer match the frozen integrity facts.
- **Relaunch contamination.** The analyzer treats duplicate OFF decision-log resets as completed
  episodes.
- **Join failure.** Best decision blocks do not join one-to-one to completed best run archives.
- **Cost coverage failure.** Intervention budget cannot be summarized for all best episodes and
  scenario pairs.
- **Lead-time coverage failure.** Reconstructable lead-time support is too small or not reported
  with exclusions.
- **Timing overclaim.** Simulation lead time is described as wall-clock latency.
- **Cost overclaim.** Brake-frame budget is described as passenger comfort, production cost, or
  deployment readiness.
- **GPU leakage.** Any model/GPU/closed-loop work runs before this offline audit is published.

## Required proof artifacts

If run, the RESULT must commit:

- exact command line;
- analyzer source and tests;
- `proof-audit/timing_cost_report.json`;
- `proof-audit/local_verification.txt`;
- reconstructed gzip receipt paths and SHA256 values if temporary reconstruction is used;
- S0/S1/S2/S3 pass/fail tables with every failed bar listed;
- intervention-cost summaries by class and scenario pair;
- lead-time summaries and exclusion counts;
- claim-boundary paragraph before interpretation.

## Protocol

1. Commit this `HYPOTHESIS.md` before writing or running iteration-40 tooling.
2. Commit analyzer code and tests before producing the audit report.
3. Run the audit once on committed inputs.
4. Publish `RESULT.md` at full weight whether S0, S1, S2, or S3 fails or passes.
5. A pass authorizes only scoped timing/cost wording in simulation. It does not authorize
   iteration-38 calibration, sensor-degradation runs, adversarial runs, selector evaluation,
   closed-loop work, deployment language, or safety claims.
