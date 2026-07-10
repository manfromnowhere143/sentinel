# Iteration 39 - external-validity claim audit and doc-narrowing result

Status: `CLAIM_AUDIT_DOC_NARROWING_REQUIRED`

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested with the committed offline analyzer.
The audit used only committed evidence and active story documents. It did not run gcloud, Docker,
a GPU, UniAD, NeuroNCAP, sensor perturbations, adversarial perturbations, iteration-38
calibration, heldout replay, selector evaluation, or closed-loop work.

Claim boundary: this is a **scientific-scope governance result**. It creates no new planner,
sensor, adversarial, deployment, or safety evidence. Its purpose is to keep the active paper and
repository story no broader than the evidence.

Harness:

- [`analyze_external_validity.py`](analyze_external_validity.py)

Primary evidence:

- [`proof-audit/claim_ledger.json`](proof-audit/claim_ledger.json)
- [`proof-audit/external_validity_report.json`](proof-audit/external_validity_report.json)
- [`proof-audit/analyze_external_validity.command.txt`](proof-audit/analyze_external_validity.command.txt)
- [`proof-audit/post_narrowing_check.command.txt`](proof-audit/post_narrowing_check.command.txt)
- [`proof-audit/local_verification.txt`](proof-audit/local_verification.txt)

## Verdict

| gate | result |
|---|---|
| S0 evidence and status integrity | **PASS**: all frozen input paths existed and were committed; docs guard passed; iteration 37 was recorded as `CALIBRATION_NULL_NO_USABLE_ALPHA`; iteration 38 was S0-canary-only with calibration not launched |
| S1 claim-ledger completeness | **PASS**: all 14 required claim families were present, scoped, evidence-linked or explicitly marked untested, and paired with permitted wording, forbidden wording, and a next falsifier |
| S2 hostile external-validity classification | **PASS**: VAD transfer was marked failed/split for selectivity; full14 deployment was marked a tight-null/split result; full-trainval localization was diagnostic only; iterations 31-38 were null/active-gate, not safety evidence; sensor, adversarial, latency/cost, and deployment-trade-off axes were untested |
| S3 active-document overclaim audit | **FAIL/REPAIRED**: the analyzer found three active-doc wording problems; the same result state narrows them |
| S4 next falsification selector | **PASS**: default next scientific priority is external-validity falsification/claim hardening, not incremental mechanism search |

The authoritative audit report verdict is:

```text
verdict=CLAIM_AUDIT_DOC_NARROWING_REQUIRED
s0_pass=true
s1_pass=true
s2_pass=true
s3_pass=false
```

After the narrowing edits below, the same analyzer was run to `/tmp/iter39_external_validity_after_narrowing.json`
as a non-authoritative final check and returned:

```text
verdict=CLAIM_AUDIT_PASS_EXTERNAL_VALIDITY_ALIGNED
s3_pass=true
s3_findings=0
```

## S3 Findings and Corrections

The audit found these active-doc locations:

| path | line | finding | correction |
|---|---:|---|---|
| `docs/REPORT.md` | 1 | title said "runtime safety monitor for frozen end-to-end driving planners" | narrowed to "frozen UniAD, with measured cross-planner limits" |
| `docs/paper/MANUSCRIPT.md` | 1 | title said "runtime safety monitor for frozen end-to-end driving planners" | narrowed to "frozen UniAD, with measured cross-planner limits" |
| `docs/REPORT.md` | 234 | "certified what reproduces exactly" was ambiguous in an active report | replaced with "recorded what reproduces exactly" |

Two stale count phrasings were also removed while editing the same active docs:

- `docs/REPORT.md`: "Across 30 documented iterations" became "Across the documented
  pre-registered campaign";
- `docs/paper/MANUSCRIPT.md`: "Across nineteen pre-registered iterations" became "Across the
  pre-registered campaign".

These edits do not weaken any measured result. They remove wording that could be read as broader
planner-general or certification/deployment language than the evidence supports.

## Claim Ledger Summary

| claim family | status | external-validity classification |
|---|---|---|
| UniAD collision prediction | established | within tested scope |
| released-union full14 benchmark | established | within tested UniAD/NeuroNCAP scope |
| deployment metric | split | mini-scene positive; full14/power tight null |
| frontal mitigation | split | mitigation, not prevention |
| RSS/formal envelope | established | within identical-input simulation scope |
| VAD planner transfer | split | failed transfer for selectivity |
| candidate diversity / plan B | split | tested sources fail viability bars; VAD partial |
| full-trainval localization | diagnostic | not causal or safety evidence |
| activation interventions | active/null | no heldout causal or closed-loop result |
| sensor/input degradation | untested | no robustness claim authorized |
| adversarial perturbation | untested | no robustness claim authorized |
| calibration stability | split/untested | canary/grid integrity only; no cross-domain stability |
| latency/cost | untested | needs a dedicated audit |
| deployment trade-offs | untested | simulation safe-progress only |

## Interpretation

The research suggestion that triggered this audit was correct: after the stable benchmark result,
the highest-value contribution is no longer another stronger-looking mechanism result by default.
The paper is stronger if it is narrower and harder to dismiss.

Iteration 39 therefore changes the campaign posture:

- Sentinel's strongest established empirical claim is the frozen-UniAD, full14/power,
  seed-paired closed-loop benchmark result for the released union.
- Cross-planner validity is not established. VAD is a split finding: safety transfers on VAD's
  failure cells, but selectivity fails.
- The full-trainval causal-localization line remains diagnostic unless an intervention passes all
  registered gates. Iteration 38 has passed S0 only.
- Sensor degradation, adversarial perturbations, latency/cost, calibration stability beyond the
  frozen grids, and deployment trade-offs are not evidence-backed claims yet.

## Next Authorized Step

No further narrowing is required before ordinary repository work: the active docs now pass the
same overclaim scanner. But the scientific priority has changed.

The default next pre-registration should be an external-validity falsifier, preferably an offline
latency/intervention-cost audit over committed decision logs or a sensor/input-degradation stress
gate for the released union. Iteration-38 calibration remains allowed by its own hypothesis, but it
is not the primary scientific direction unless a future decision explicitly argues that its narrow
causal-handle value is more defensible than the external-validity falsifier.
