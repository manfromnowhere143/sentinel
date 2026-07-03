# The power run — OFF vs the best configuration at 20 runs per pair: pre-registration

Frozen before the run. Every benchmark-scope number so far rests on 6 seed-paired runs per
scene-scenario pair against the paper's 100-run protocol. This run re-measures the two arms that
matter — the unmonitored planner and the campaign's best configuration — at **20 runs per pair on
all 14 official scenes (20 pairs × 20 runs × 2 arms = 800 episodes)**, tripling the power behind
every published CI and hardening the result toward the published protocol.

## Which configuration runs (decision rule, frozen now)

The best-arm configuration is decided by iteration 16's pre-registered verdict, not by taste:

- **If H16 criteria 1 and 3 hold** (safety held AND crawl − released safe-progress CI excludes
  zero), the best arm is the **crawl** (`SENTINEL_RELEASE_K=4, SENTINEL_CRAWL_V=2.0`).
- **Otherwise** it is the **released-union** (`SENTINEL_RELEASE_K=4`), the incumbent best from
  iteration 15.

The launch record in RESULT.md states which branch fired, citing the iteration-16 result.

## Hypotheses

- **H-P0 (validity gate, not a result).** Episodes are deterministic per run index, so run
  indices 0–5 of each arm must reproduce the committed RUNS=6 evidence **exactly** (per-episode
  NCAP scores identical: OFF vs `full14_benchmark/proof`; best vs the iteration-15 or -16 proof
  per the decision rule). If this fails, the apparatus has drifted: the run stops being evidence,
  the drift is diagnosed and reported, and no result claims are drawn until it is resolved.
- **H-P1.** The benchmark-score delta (best − OFF, pooled mean of class means) remains positive
  with the seed-paired bootstrap CI excluding zero at n=20 (the n=6 measurement was +0.934,
  CI [+0.713, +1.155]).
- **H-P2 (the deployment question at 3.3× power).** Branch-dependent, both stated now:
  - If the best arm is the **crawl** (iteration 16 flipped the deployment verdict at n=6), H-P2
    predicts the flip survives: safe-progress (best − OFF) > 0 with the n=20 CI excluding zero.
  - If the best arm is the **released-union**, iteration 15 measured +0.076 with CI
    [−0.122, +0.262] at n=6. No direction is claimed; the n=20 CI is reported exactly as it
    lands, including a hardened null.
- **H-P3 (structure).** The per-class cells at n=20 are reported against the n=6 structure:
  side and stationary improvements, frontal mitigation-not-prevention, and specifically whether
  the named frontal/0346 regression persists or was run-noise.

## Falsifiers and discipline

- H-P0 failure supersedes everything — apparatus first.
- Any episode failure (traceback, container death) is reported per pair; no silent exclusions.
- The two arms run sequentially on the single-tenant GPU (shared container names); the script is
  not modified mid-run.
- Disk: the box must have ≥ 25 GB free before launch (this run writes ~23 GB of per-run
  evidence); pre-launch cleanup may remove only `outoutput/` directories whose evidence is
  verified present in committed proof archives.

## Protocol

[`power14_run.sh`](power14_run.sh): OFF arm fully first, then the best arm; markers `P14PAIR
<arm> <scenario> <seq>`; `RUNS=20`; the best arm's patch is selected by the decision rule at
launch (`server_patch_union_crawl.py` or `server_patch_union_release.py`, both already
committed). Analysis: [`analyze_power14.py`](analyze_power14.py) — the full14 analyzer at n=20
plus the H-P0 first-6 exact-reproduction check against the committed comparators. All evidence
(run log, both decision logs, per-run trajectories/metrics) committed under `proof/`. Estimated
duration ~37 h.
