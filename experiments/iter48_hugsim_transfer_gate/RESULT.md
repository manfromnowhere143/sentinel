# Iteration 48 - HUGSIM Stage-2 transfer gate: TRANSFER_NULL

Status: `TRANSFER_NULL` (analyzer verdict; K1/K2 passed, F1 void check passed, no falsifier
fired) — **this is THE transfer verdict of the second-benchmark line, published at full
weight.**

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested exactly as registered: the single
detached 104-episode run (26 scenarios x 2 runs x 2 arms, within-launch back-to-back pairing
`OFF r1 -> ON r1 -> OFF r2 -> ON r2` per the carried stochastic D0 verdict) launched on
`sentinel-gpu` at 07:17:38 UTC behind the full provenance gate (`I48_STAGE2_PROVENANCE_OK`:
frozen HUGSIM/UniAD_SIM SHAs, checkpoint SHA `0ad0c2f5…`, shim SHA `5bf69a11…`, image id
`f73ef3884063`, all 52 scenario-yaml SHA256s, four map jsons, carried D0 verdict `stochastic`)
and reached `I48_STAGE2_DONE` at 16:29:13 UTC, 2026-07-12, with zero `I48_ABORT_*` markers and
no containers left up. Proof was collected and committed FIRST; ONE run of the committed
analyzer over the committed artifacts then produced the verdict.

**The transfer verdict.** On HUGSIM's frozen 26-scenario easy+medium subset, under the seven
NeuroNCAP-frozen parameters with zero retuning, the released union **actively fires and
brakes** (37/52 ON episodes intervened; 887 fired frames, 1,392 brake frames = 26.9% of the
5,172 monitored frames; 134 latch releases) **and produces no detectable change in closed-loop
HD-Score**: mean paired delta (ON − OFF) over the 52 pairs = **−0.0166**, 95%
scenario-clustered bootstrap CI **[−0.0551, +0.0255]** (26 clusters, 10,000 draws, seed 48) —
the CI includes zero. The registered answer is the null: the NeuroNCAP benefit does not
measurably transfer to this benchmark at this N, and any true mean effect on these scenarios
is bounded by the CI to roughly ±0.05 HD-Score in either direction.

**F1 void check (verified FIRST, mechanically).** The receipts record
`monitor_patch_sha = 6b39fd79d00c7bdb937c6d240fbc4648661b235f1a3024912d62874937146c5c` —
byte-identical to the committed patch copy
([`client_patch_union_iter48.py`](client_patch_union_iter48.py)) — and the frozen parameter
block (cpa 1.5 / ttc 2.5 / min-closing 3.0 / max-gap 30.0 / min-score 0.3 / release-K 4 /
dt 0.5) is echoed identically in the receipts and in every params row of all 52 ON-arm
decision logs (analyzer `F1_retuned.problems = []`). Nothing was retuned before, during, or
after the run; the iteration is not void.

**Completion bars.**

- **K1 — all 104 episodes complete: PASS.** `104/104` with finite `hdscore`,
  `retried_episodes = 0`, zero `__failed` dirs. OFF walls 101-514 s; ON walls 107-1,188 s —
  the two longest (`scene-0051-medium-00__on_r1` 1,172 s, `scene-0051-medium-01__on_r1`
  1,188 s) ran to the 400-step cap under sustained braking, still inside the 1,200 s bound.
- **K2 — per-step and decision logs: PASS.** `output.txt` round-trip lines and positive step
  counts for all 104; all 52 ON episodes carry the patch load marker and per-frame decision
  lines plus the full-input `sentinel_iter48_decisions.jsonl` (`trace_error_rows = 0`).
- **K3 — evidence committed: PASS.** Receipts, run log, all 104 episode artifact sets, the
  ON-arm decision JSONLs, box hashes (`208/208` local files byte-identical to the box), the
  heavy manifest, and the single analyzer report are committed; no file over 90 MB.

Harness:

- [`client_patch_union_iter48.py`](client_patch_union_iter48.py) (the released union at the
  registered UniAD_SIM client-side interception point, frozen params baked in),
  [`run_transfer_gate.sh`](run_transfer_gate.sh) (box-side launcher, interleaved OFF/ON
  schedule), [`analyze_transfer.py`](analyze_transfer.py) (offline, run ONCE)
- [`../../tests/test_iter48_transfer.py`](../../tests/test_iter48_transfer.py)

Primary evidence:

- [`proof-stage2/transfer_report.json`](proof-stage2/transfer_report.json) (the single
  analyzer run; command receipt in
  [`proof-stage2/analyze_transfer.command.txt`](proof-stage2/analyze_transfer.command.txt))
- [`proof-stage2/transfer_pairs.md`](proof-stage2/transfer_pairs.md) (all 52 paired deltas)
- [`proof-stage2/receipts.json`](proof-stage2/receipts.json) (launch provenance gate, patch
  SHA, frozen-param echo, carried D0 verdict)
- [`proof-stage2/episodes/`](proof-stage2/episodes) (104 episode dirs: `eval.json`,
  `output.txt`, `episode_meta.json`, ON-arm `sentinel_iter48_decisions.jsonl`)
- [`proof-stage2/i48-stage2-run.log`](proof-stage2/i48-stage2-run.log) (full box-side log,
  arm-labelled per-episode markers, final `I48_STAGE2_DONE`)
- [`proof-stage2/box_episode_hashes.txt`](proof-stage2/box_episode_hashes.txt) (on-box SHA256
  over `eval.json`/`episode_meta.json` for all 104 dirs)
- [`proof-stage2/heavy_manifest_iter48.txt`](proof-stage2/heavy_manifest_iter48.txt) (heavy
  pickles/videos stay on the box)

## Verdict

| gate | result |
|---|---|
| S0 provenance | **PASS**: HYPOTHESIS committed alone (`889770c`) before tooling (`ff3772c`); disclosed non-scheduled ON-arm smoke committed and excluded (`bddb6f1`, [smoke-evidence/SMOKE_NOTE.md](smoke-evidence/SMOKE_NOTE.md)); launch gate `I48_STAGE2_PROVENANCE_OK`; single-tenant rule held; proof committed before the analyzer ran (`c78b301`) |
| F1 retuning void | **NOT fired**: patch SHA byte-identical to the committed copy; frozen params echoed in receipts and all 52 decision-log params rows; `0` problems |
| K1 all 104 complete | **PASS**: `104/104`, `0` retries, `0` dual failures; walls 101-1,188 s (bound 1,200 s) |
| K2 per-step + decision logs | **PASS**: all 104 step logs; all 52 ON decision logs + load markers; `0` trace-error rows |
| K3 evidence committed | **PASS**: `208/208` collected files byte-identical to the box; no split needed |
| **Primary: mean paired HD delta CI** | **TRANSFER_NULL**: point `−0.0166`, 95% CI `[−0.0551, +0.0255]` — includes zero |
| Median delta (heavy-tail treatment) | point `+0.0032`, 95% CI `[−0.0467, +0.0178]` — also includes zero; no mean/median CI sign disagreement |
| F2 splat-noise mistuning | **NOT fired** (either direction): pooled brake-frame fraction `26.9%` (over-fire bar `80%`); `887` fired frames (never-fire bar `0`) |
| F3 RC collapse | **NOT fired**: mean paired RC delta `−0.0147` (bar `−0.30`); OFF RC mean `0.5644` vs ON `0.5497` |
| F4 crash/deadlock loop | not fired: `0` dual-failure episodes, `0` consecutive-failure aborts |
| F5 pairing infeasibility (fresh) | **NOT fired**: fresh OFF-OFF median \|dHD\| `0.0307` (bar `0.15`); CI not noise-flagged |
| F6 VRAM/disk | not fired: no CUDA OOM, disk guard held, no `I48_ABORT_DISK` |
| Budget | `9.17` GPU-h of episode walls (OFF `4.09` + ON `5.08`), inside the expected 8-16 and far under the `34.7` ceiling |

## The paired-delta table and what it shows

All 52 pairs are committed in [`proof-stage2/transfer_pairs.md`](proof-stage2/transfer_pairs.md).
The distribution is wide and two-sided: 29 pairs positive, 23 negative, range `−0.4745`
(`scene-0166-easy-00` r2) to `+0.3260` (`scene-0062-easy-00` r1); per-arm aggregate HD means
OFF `0.3910` vs ON `0.3744`. The carried noise floor binds the reading, as registered: this
run's own fresh OFF-OFF within-scenario spread has median |dHD| `0.0307` with a heavy tail to
`0.4288` (`scene-0071-easy-00`; 16/26 pairs at or under `0.09`, heavier than iteration 47's
22/26) — single stochastic replay pairs swing by most of the score range, so no per-pair delta
is interpretable alone and only the clustered CI speaks. It says: no detectable mean effect.

**Where the monitor concentrated.** Braking is not uniform: 4 of 52 ON episodes spent over
half their frames braking, with per-episode maxima `82.3%` (`scene-0051-medium-01__on_r1`) and
`81.2%` (`scene-0051-medium-00__on_r1`). Those two episodes ran to the step cap with RC cut
roughly in half against their paired OFF runs (1.00 -> 0.47 and 0.64 -> 0.50) and HD collapsed
(`0.2439 -> 0.0415`, `0.1879 -> 0.0345`) — localized over-braking, on the record. Pooled, it
stays far from both bars: F2's constant-firing bar is pooled at `80%` (measured `26.9%`) and
F3's RC bar is `−0.30` (measured `−0.0147`). The same scenarios' r2 pairs show mild or zero
deltas, consistent with the stochastic loop rather than a deterministic failure mode.

## Secondaries (descriptive, NOT bars; mean paired deltas over 52)

| term | mean delta (ON − OFF) | median delta |
|---|---:|---:|
| NC (no-collision) | −0.0369 | 0.0000 |
| DAC (drivable area) | +0.0069 | 0.0000 |
| TTC term | −0.0248 | +0.0087 |
| comfort | +0.0652 | +0.0213 |
| RC (route completion) | −0.0147 | −0.0071 |

No term moves decisively; the small comfort gain and small NC/TTC losses are all inside the
pairing noise. RC — the iteration-3/13 paralysis axis — is the finding that did NOT happen:
the monitor braked 1,392 frames across 37 episodes and route completion moved `−0.0147`.

## Connection to the campaign arc

- **Iteration 43's over-firing prediction — partially confirmed, below the registered bar.**
  Iteration 43 measured that 5 cm position jitter makes the frozen rule over-fire in replay
  and predicted splat-reconstructed tracking might sit in that regime. On HUGSIM the rule is
  indeed **active far beyond NeuroNCAP-like selectivity** — it intervened in 71% of ON
  episodes (37/52), including easy scenes with no scripted threat, and saturated two episodes
  above 80% brake frames — but pooled firing (`26.9%`) stayed well under the F2
  constant-firing bar, and the never-fires direction is refuted outright. The transfer
  boundary is therefore NOT trigger mistuning by the registered definition: the rule fires,
  brakes, releases (134 latch releases — the iteration-15 mechanism works on HUGSIM), and the
  interventions simply do not buy a measurable HD-Score improvement here.
- **Iteration 13's paralysis lesson — did not recur.** The RSS-style failure (winning safety
  by destroying progress) is exactly what F3 watched for; RC delta `−0.0147` against the
  `−0.30` bar says the latch release kept the car driving, with the two `scene-0051` r1
  episodes as the visible localized exception.

## Honest scope boundary (registered, binding)

This is a closed-loop HUGSIM transfer measurement of the frozen-parameter released union on
26 easy+medium scenarios with the same frozen UniAD checkpoint, and nothing else. **No
NeuroNCAP-equivalence claim** — HD-Score and NeuroNCAP score are different metrics on
different scene families; NeuroNCAP's scenarios are scripted safety-critical collisions while
this subset measures general closed-loop driving, so a null here does not contradict the
NeuroNCAP result and the NeuroNCAP result does not license expectations here. **No
deployment, real-world, production, or safety claim. No benchmark-ranking or UniAD-performance
claim. No monitor-robustness claim** (iteration 43's mild-fragile finding stands). No
generalization beyond UniAD-class planners on these 26 scenarios. The iteration-39 wording
rules apply.

## Successor boundary

The registered question is answered: the released union's NeuroNCAP benefit does not
measurably transfer to HUGSIM easy+medium scenarios at N=2 per arm, while the mechanism
itself (fire, latch, release) demonstrably operates there. Successors require fresh
pre-registrations; the natural candidates, in defensibility order: (a) fold this null into
the manuscript as the measured external-validity boundary of the released union — the
campaign's stated priority is exactly this kind of falsification pressure; (b) an
expanded-N confirmation only if a tighter CI on the transfer effect justifies the GPU spend
(halving the CI needs roughly 4x the pairs); (c) a hard-tier scenario extension, where
safety-critical events are denser and the NC term carries more of the score. None of these
is authorized by this iteration; each needs its own HYPOTHESIS.md committed alone.
