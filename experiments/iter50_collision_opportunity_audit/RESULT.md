# Iteration 50 - collision-opportunity audit: A1_CONFIRMED, OPPORTUNITY_PRESENT_NULL

Status: `OPPORTUNITY_AUDIT_COMPLETE` — every integrity gate passed, no falsifier fired, and
the two registered sub-verdicts are **A1_CONFIRMED** (NeuroNCAP) and
**`OPPORTUNITY_PRESENT_NULL`** (HUGSIM). Entirely offline over committed evidence; zero GPU,
zero gcloud, zero box reads. The iteration-49 firewall held: the pre-registration
([`HYPOTHESIS.md`](HYPOTHESIS.md), commit `fbd1b3d`) was committed and pushed ALONE, with the
prediction P1 frozen, before any iteration-49 outcome data was read; no iteration-49 episode
artifact, log, or aggregate has been read by this iteration at publication time.

## The registered question, answered

Does collision opportunity explain where the released union's benefit appears? **Half of
it does — and that half makes the other half sharper.** On NeuroNCAP, the benefit
concentrates exactly where the unmonitored planner collides (A1 confirmed, rho `0.70`). On
HUGSIM easy+medium, opportunity was NOT scarce — `40/52` OFF episodes (`76.9%`) contain a
collision event under the frozen definition — so iteration 48's `TRANSFER_NULL` is
classified **`OPPORTUNITY_PRESENT_NULL`**: the monitor operated (37/52 ON episodes
intervened), collisions were abundantly available to prevent, and the interventions still
bought no measurable HD-Score change. The transfer failure cannot be explained away as an
opportunity-starved test domain. **Stated plainly, per the registration: this
classification is an explanation of the null's domain, not an excuse, and it does NOT
upgrade, soften, or reopen the null. Iteration 48's `TRANSFER_NULL` stands as published.**

## Integrity gates (all passed; `problems = []`)

- full14/power: `analysis_output.txt` H-P0 PASS; `p14-runs.tar.gz` metrics counts exactly
  `399` OFF / `400` best over `20` pairs; merged-log `P14PAIR` parsing yields `20` episodes
  per arm per pair with the recorded `off/side-0921 n=19` exception detected (the
  iteration-40 frozen facts, reproduced).
- HUGSIM: H48-OFF `52/52` episodes read (iteration-48 OFF arm), HBASE `52/52` (38 iteration-46
  completed + 14 iteration-47); every `eval.json` carried numeric `nc`/`ttc` top-level and in
  all `details` steps — the frozen primary definition was fully supported (no
  definition-ambiguity null).
- Cross-check: the 52 paired HD deltas recomputed from committed `eval.json` files match the
  published iteration-48 mean (`−0.016636793770462406`) within `1e-9`.

## A1 — NeuroNCAP: the benefit concentrates where the OFF arm collides: **A1_CONFIRMED**

Over the 20 full14/power scenario pairs — `x` = OFF-arm collision rate
(`any_collide@0.0s`), `y` = per-pair benefit (mean best − mean OFF `ncap_score`):

| statistic | value | registered bar |
|---|---|---|
| Spearman rho (average ranks) | **+0.7003** | `>= +0.5` — met |
| 95% bootstrap CI (10,000 pair-resampling draws, seed 50) | **[+0.3909, +0.8762]** | excludes 0 from below — met |
| verdict | **A1_CONFIRMED** | |

Stratified means (registered support, no bar): the 12 pairs with OFF collision rate
`>= 0.5` carry mean benefit **+0.989**; the 8 pairs below carry **+0.263**; difference
**+0.727**. The per-pair table is committed
([`proof-audit/neuroncap_pairs.md`](proof-audit/neuroncap_pairs.md)); the known outlier
`frontal-0346` (rate 0.50, benefit `−0.758` — the published stop-policy regression) sits
inside the rank correlation, not removed. Reading: on the benchmark where the union earned
its +0.783, the benefit is an opportunity-conversion effect — it appears where the
unmonitored planner collides.

## A2 — HUGSIM easy+medium: opportunity was abundant: **`OPPORTUNITY_PRESENT_NULL`**

Frozen primary definition per OFF episode: `nc_min < 1.0` over top-level `nc` and every
`details.<t>.nc`. Measured `nc_min` is exactly binary in both sets (0.0 or 1.0):

| set | episodes | primary opportunity | fraction | near-miss (secondary, descriptive) |
|---|---:|---:|---:|---:|
| **H48-OFF** (iteration-48 OFF arm, the classifying set) | 52 | **40** | **0.769** | 6 |
| HBASE (iteration-46/47 baseline, corroboration) | 52 | **40** | **0.769** | 9 |

Per tier (H48-OFF): easy `12/18`, medium `28/34`. Both independent 52-episode OFF sets
agree at exactly `40/52`. Against the registered bar (`0.25`, i.e. 13/52), the fraction is
three times over: the iteration-48 `TRANSFER_NULL` is classified
**`OPPORTUNITY_PRESENT_NULL`**, NOT opportunity-scarce.

**Descriptive stratification (registered, no bar):** iteration 48's 52 paired HD deltas
split by the OFF episode's opportunity label (OFF-only label; ON data enters only as the
outcome side): with opportunity `n=40`, mean delta **+0.0013** (median `+0.0088`); without
opportunity `n=12`, mean delta **−0.0765** (median `−0.0636`). Even restricted to the 40
pairs where a collision was on the table, the monitored arm gained nothing detectable; on
the 12 collision-free pairs the deltas lean negative (single stochastic pairs swing widely —
iteration 48's noise floor binds this reading, and no bar was registered on it).

**The sharpened reading (classification of published numbers, no new claim):** iteration 48
already published that the union fires, latches, and releases on HUGSIM, and that the NC
term's mean paired delta is `−0.0369` (median `0.0000`). This audit adds the missing
denominator: `76.9%` of the OFF episodes contained a collision event, so the monitor had
roughly forty opportunities and converted none into a measurable outcome difference. On
NeuroNCAP the same frozen rule converts opportunity into +0.99 mean benefit on
high-collision pairs (A1). The external-validity boundary is therefore about the
MECHANISM's transferability — the rule's firing does not align with what actually causes
HUGSIM collisions — not about the benchmark lacking safety-critical content.

## P1 — the frozen prediction for iteration 49, as registered (quoted verbatim)

The following was registered in [`HYPOTHESIS.md`](HYPOTHESIS.md) (commit `fbd1b3d`) while
iteration 49's run was in flight and unread, and remains binding on whichever operator
publishes iteration 49's RESULT:

> **P1.** Compute the primary-opportunity fraction over iteration 49's 52 OFF episodes
> (`proof-hard/episodes/*__off_r*/eval.json`, frozen primary definition: `nc_min < 1.0`).
>
> **Branch A (opportunity present, benefit ports):** if at least 13/52 (`>= 0.25`) of the
> iteration-49 OFF episodes show primary collision opportunity AND iteration 49's own
> registered analyzer reports a mean paired HD delta (ON - OFF) whose 95%
> scenario-clustered CI excludes zero from below, P1 is **CONFIRMED**: the union's benefit
> reappears where collision opportunity is present, and iteration 48's null is explained
> as an opportunity-scarce transfer domain.
>
> **Branch B (opportunity present, benefit does not port):** if at least 13/52 show primary
> opportunity AND the CI includes zero or excludes it from above, P1 is **REFUTED**, and
> the conclusion is binding: the transfer failure is REAL, not opportunity-scarce — the
> monitor's mechanism does not port to HUGSIM even where collisions are available to
> prevent.
>
> **Branch C (opportunity absent at the harder tier):** if fewer than 13/52 show primary
> opportunity, P1 is **NOT TESTABLE** at the hard/extreme tier; that scarcity is itself a
> finding and is NOT a confirmation of anything.
>
> Iteration 49's analyzer remains its own registered gate with its own verdict classes;
> P1 pre-commits only the INTERPRETATION of that outcome relative to collision
> opportunity. Whichever branch obtains publishes on the record.

One factual note this audit adds without touching iteration 49: both measured easy+medium
OFF sets sit at `0.769`, three times the Branch-C threshold, so on the committed evidence
the harder tiers reaching `>= 0.25` is the expected case and P1 will most likely be decided
between Branches A and B. Note also that Branch A's wording ("opportunity-scarce transfer
domain") was frozen before this audit measured the easy+medium fractions; A2's measured
`OPPORTUNITY_PRESENT_NULL` means a Branch-A outcome would need its explanation refined on
the record rather than adopted verbatim — the branch decision procedure itself is
unaffected.

## Falsifier evaluations

| falsifier | result |
|---|---|
| Definition ambiguity (infrastructure null) | **NOT fired**: `problems = []`; all frozen fields present and numeric; tar counts, pair counts, and the n=19 exception match the iteration-40 frozen facts |
| Circularity | **NOT fired**: every opportunity label computed from OFF-arm `eval.json` only; the opportunity reader mechanically refuses ON-arm paths (tested) |
| Post-hoc definition changes | **NOT fired**: definitions, the `0.25` bar, A1 bars, and P1 are byte-identical to the pre-registration |
| Iteration-49 leakage | **NOT fired**: pre-registration committed alone (`fbd1b3d`) before any iteration-49 outcome read; the three HANDOFF launch-verification HD values were disclosed in the registration itself |
| GPU/gcloud leakage | **NOT fired**: the audit ran no GPU, Docker, gcloud, or box command |

## Honest scope boundary (registered, binding)

No new safety, transfer, deployment, robustness, benchmark-ranking, real-world, or
monitor-performance claim. A1 characterizes where the ALREADY-PUBLISHED NeuroNCAP benefit
sits; A2 classifies the ALREADY-PUBLISHED iteration-48 null; P1 pre-commits an
interpretation of iteration 49's own registered verdict. Iteration 48's `TRANSFER_NULL`
and the full14/power results are unchanged. The iteration-39 wording rules apply.

## Harness and evidence

- [`analyze_opportunity.py`](analyze_opportunity.py) (run ONCE; command receipt in
  [`proof-audit/analyze_opportunity.command.txt`](proof-audit/analyze_opportunity.command.txt))
- [`../../tests/test_iter50_opportunity.py`](../../tests/test_iter50_opportunity.py)
- [`proof-audit/opportunity_report.json`](proof-audit/opportunity_report.json) (full A1/A2
  numbers, per-episode rows, falsifier inputs)
- [`proof-audit/opportunity_episodes.md`](proof-audit/opportunity_episodes.md) (all 104
  OFF episodes, both sets, `nc_min`/`ttc_min`/labels)
- [`proof-audit/neuroncap_pairs.md`](proof-audit/neuroncap_pairs.md) (all 20 pairs:
  collision rate, n, benefit)

## Successor boundary

This audit authorizes nothing beyond what its registration states: P1's resolution belongs
to the operator who publishes iteration 49's RESULT, quoting the registered text and naming
the branch. Any further opportunity-conditioned analysis (e.g. a per-scenario
collision-cause taxonomy, or an opportunity-stratified expanded-N design) requires a fresh
pre-registration.
