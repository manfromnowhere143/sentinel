# The power run — the benchmark result at 20 runs per pair: confirmed, tighter, and honest

All hypotheses were frozen before the run ([HYPOTHESIS.md](HYPOTHESIS.md)); the best-arm
decision rule fired for the **released union** (iteration 16's crawl failed its safety
criterion). 799 of 800 planned episodes were measured — every pair at n=20 in both arms except
off/side-0921 at n=19 (below). Everything here is what the pre-registered analyzer
([analyze_power14.py](analyze_power14.py)) prints from the committed evidence.

## H-P0 — the validity gate: PASS

Run indices 0–5 of **every pair in both arms** reproduce the committed RUNS=6 evidence exactly
— through the five machine-freezing incidents, one host migration, and four relaunches
documented below. The stationary-0101 replay additionally reproduced its original 17-episode
partial byte-for-byte (the merge script's prefix check), and the two independent 19-episode
recordings of side-0921 are identical.

## H-P1 — the benchmark result at triple power

| pooled (mean of class means, n=20/pair) | OFF | released union | delta | 95% CI |
|---|---:|---:|---:|---|
| **NCAP score** | 2.12 | **2.91** | **+0.783** | **[+0.605, +0.928] — excludes 0** |

The published UniAD baseline (1.84) reproduces at 2.12 (n=6 gave 2.15 — consistent). The
monitor's benchmark win stands decisively at 3.3× the statistical power; the n=6 point estimate
(+0.934) was modestly optimistic, and the n=20 number replaces it as this repository's headline.

## H-P2 — the deployment question, resolved into a tight null

Safe-progress (released − OFF): **−0.032, 95% CI [−0.127, +0.065]** — includes zero, now tightly.
The n=6 interval (+0.076, [−0.122, +0.262]) is sharpened to a band around zero: at benchmark
scope the released union's deployment-metric effect vs the unmonitored planner is statistically
indistinguishable from zero, with any cost bounded below 0.13. Stated plainly: **the benchmark
safety gain (+0.78) is bought at a deployment cost of approximately nothing** — the
cost-of-stopping floor identified by iteration 15 is real, small, and now precisely measured.

## H-P3 — structure at n=20

| class | OFF score / coll% | released score / coll% |
|---|---|---|
| stationary | 3.65 / 29% | **4.13 / 18%** |
| frontal | 1.24 / 78% | 1.78 / 90% (mitigation, not prevention) |
| side | 1.48 / 74% | **2.81 / 44%** |

- Side and stationary improvements hold at power; frontal remains what every iteration found —
  softer impacts, not fewer.
- **The frontal/0346 regression is real, not run-noise**: 3.07/50% → 2.31/100% at n=20 — the
  committed stop converts some of the planner's occasional escapes into low-speed collisions on
  this pair. It remains the named cost of the stop policy.
- stationary-0101 at n=20 shows the residual over-braking plainly: OFF drives 62.7 m, the
  released union 19.7 m (score 3.99 → 4.79) — safety up, progress down; the deployment metric
  nets these to the tight null above.

## The incident record (in full, because it is part of the measurement)

The run survived **five machine-freezing incidents across two physical hosts**. The diagnostic
arc, preserved in the committed vitals log and this repository's continuation scripts: host
migration and unattended-upgrades were tested and refuted; an on-box vitals watchdog then caught
the cause — **memory exhaustion on a swapless image** (31.6/32.1 GB in the final samples before
a freeze), which stalls the kernel in reclaim: ssh cannot fork, disk writes stop, no kernel log
is emitted. Two pairs (stationary-0101, side-0921) crest the ceiling late in their episode
sequences, which produced the episode-linked freeze pattern. An 8 GB swapfile eliminated the
failure (both pairs subsequently completed in the best arm, including side-0921's full 20).

**off/side-0921 is reported at n=19**: its run_19 froze the pre-swap host on all three attempts
(two hosts); per the rule committed before the final relaunch, no fourth attempt was made. Its
19 seed-paired episodes are complete and internally reproduced.

Recovery machinery, all committed: idempotent resumable runner
([power14c_resume.sh](power14c_resume.sh)), append-only logs, the vitals watchdog, and the log
merge with a determinism cross-check ([merge_power14_logs.py](merge_power14_logs.py)). No
completed episode was lost or re-measured differently at any point — H-P0 is the proof.

## Evidence

[`proof/`](proof/): the three raw run logs, the merged analysis log, the vitals log, per-run
trajectories/metrics/actors for all 799 episodes, both per-frame decision logs (split into
<100 MB parts for hosting; `cat sentinel_p14_*.jsonl.gz.part-* > file.gz` to reassemble), and
the analyzer output. Reproduce:
`python3 merge_power14_logs.py <merged> proof/sentinel-power14.log proof/sentinel-power14b-attempt3.log proof/sentinel-power14c.log`
then `python3 analyze_power14.py <merged> <runs root> ../full14_benchmark/proof/sentinel-full14.log ../iter15_latch_release/proof/sentinel-iter15.log I15PAIR released`.
