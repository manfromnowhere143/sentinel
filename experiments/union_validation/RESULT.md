# Union — statistical validation: CORRECTED (the original pooling was invalid)

> **Correction (2026-07-02, independent verification pass).** This document originally claimed
> "net-positive confirmed at n=20 with a bootstrap CI excluding zero." The verification audit
> ([`../VERIFICATION.md`](../VERIFICATION.md)) found the pooling invalid: NeuroNCAP episodes are
> **deterministic per run index**, so the union/OFF arms of iterations 8, 9 and 10 — pooled here as
> "independent replications" — were the *same episodes* re-executed (iteration 9 ≡ iteration 10
> run-for-run; iteration 8's first six runs ≡ iteration 9's). The honest sample is **8 unique
> episodes per scene per arm**, not 20, and at n=8 the CI does not exclude zero. The original
> claim is withdrawn; the corrected analysis is below, and the definitive re-measurement with 20
> genuinely distinct episodes is in [`../VERIFICATION.md`](../VERIFICATION.md) §4.
> Reproduce both from committed evidence: `../verification/audit_pooling.py`.

## What the evidence supports

**Corrected analysis — unique episodes (run indices 0–7, iteration 8), seed-paired bootstrap:**

| scene (unique n=8) | OFF score / collision % | union score / collision % |
|---|---|---|
| stationary/0103 (clean) | 5.00 / 0% | 5.00 / 0% |
| frontal/0103 | 1.31 / 75% | 2.43 / 88% |
| side/0103 | 0.65 / 100% | 4.38 / **12.5%** (1 of 8) |

Safe-progress OFF 2.228 → union 2.476, delta **+0.247, 95% CI [−0.272, +0.782]** — positive in
direction, **not significant at 8 episodes**. The side-impact reduction (100% → 12.5%) and the
frontal impact mitigation remain the structural sources of the gain; the clean scene is unchanged.

**Definitive resolution (2026-07-02):** the verification pass then ran the same comparison on
**20 genuinely-unique episodes per scene** (run indices 0–19, a single `--runs 20` pass per arm;
indices 0–7 reproduce this iteration's data exactly). Result: safe-progress OFF 1.826 → union
2.224, **delta +0.398, 95% CI [+0.133, +0.665] — excludes zero; net-positive re-established on
valid statistics**. Side-impact at n=20 is 100% → 30%. Full table and raw evidence:
[`../VERIFICATION.md`](../VERIFICATION.md) §4.

## What was wrong, precisely

- Pooling deterministic replays as independent runs triple-counted episodes 0–5 (n inflated 8 → 20),
  shrinking the bootstrap CI by roughly √2.5 and pulling it past zero.
- The same duplication *diluted* the one union side-impact collision (run 6, which only the
  8-run iteration-8 pass reached) from its true 1/8 = 12.5% to the published "1 of 20 = 5%".
- The original text called the safe-progress CI "the pre-registration's own bar". The frozen
  pre-registration bar is NCAP score / collision rate (met by iteration 2); safe-progress was
  introduced in iteration 3 and adopted as a bar in iteration 4's hypothesis. The distinction
  matters and is now stated.

## What survives

Determinism cuts both ways: it invalidates the pooling but makes every OFF-vs-union comparison
**seed-paired on identical episodes** — the per-iteration results themselves are exact and
reproducible (the audit re-derived them run-for-run from the committed logs). The union remains
selective (clean ≈ OFF), side-solving in 7 of 8 unique episodes, and frontal-mitigating. Whether
its net advantage on safe-progress is statistically significant is settled honestly by the fresh
n=20 evaluation in [`../VERIFICATION.md`](../VERIFICATION.md) §4 — not by this pooling.
