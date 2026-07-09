# Iteration 34 - direction-specificity audit no-dose-response null

Status: `DIRECTION_AUDIT_NULL_NO_DOSE_RESPONSE`

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested once with the committed offline
analyzer. The audit used only committed iteration-33 calibration proof artifacts. It did not run
gcloud, Docker, a GPU, UniAD, NeuroNCAP, heldout replay, iteration-12 scoring, selector evaluation,
or closed-loop work.

Claim boundary: this is a **post-result audit null**. It does not select an alpha, rescue
iteration 33, prove or disprove a causal mechanism, authorize heldout replay, or make any
deployment or safety claim.

Harness:

- [`analyze_direction_specificity.py`](analyze_direction_specificity.py)

Primary evidence:

- [`proof-audit/direction_specificity_report.json`](proof-audit/direction_specificity_report.json)
- [`proof-audit/analyze_direction_specificity.command.txt`](proof-audit/analyze_direction_specificity.command.txt)
- [`proof-audit/local_verification.txt`](proof-audit/local_verification.txt)

## Verdict

| gate | result |
|---|---|
| S0 artifact and row integrity | **PASS**: calibration verdict was `CALIBRATION_NULL_NO_USABLE_ALPHA`; prefix replay integrity passed; all five alpha cells had `2452` target keys, `108` `eligible_lowdiv` rows, `2344` `benign_control` rows, zero error rows, zero gross-validity failures, no duplicate target keys, and matching target keys across alphas |
| Hash/receipt validation | **PASS**: `17` committed proof artifacts were checked against receipts, with zero hash failures; the audit records the `sha256s.txt` and `unsplit_sha256s.txt` receipts |
| S1 dose-response coupling | **FAIL/NULL**: only `74/108` `eligible_lowdiv` rows had nonnegative endpoint-spread slope across the frozen alpha grid (`0.685185`), below the frozen `0.70` bar |
| S2 target specificity and safety alignment | **NOT EVALUATED**: prohibited because S1 failed |
| Heldout, iteration-12, selector, closed loop | **NOT RUN**: prohibited by both iteration 33 and this audit |

## Audit Result

The audit report verdict is:

```text
verdict=DIRECTION_AUDIT_NULL_NO_DOSE_RESPONSE
s0_pass=true
s1_pass=false
s2=null
```

S1 had some ordered aggregate movement, but not enough row-level coupling to pass:

| alpha | eligible median endpoint-spread delta |
|---:|---:|
| `0.00` | `0.000000` |
| `0.25` | `0.004535` |
| `0.50` | `0.009948` |
| `0.75` | `0.019271` |
| `1.00` | `0.030803` |

The aggregate alpha/median correlation was `0.980514`, and alpha `1.00` moved `0.129630` of
eligible rows by more than `0.25 m`, clearing those S1 sub-bars. The failing frozen bar was the
row-level sign consistency: `74/108` eligible rows had nonnegative endpoint-spread slope, fraction
`0.685185 < 0.70`. Median eligible slope was only `0.030706 m/alpha`.

Because S1 failed, the audit did not evaluate S2 and did not issue any target-specificity,
safety-alignment, or scale-headroom claim.

## Interpretation

Iteration 34 narrows the iteration-33 null. The committed global bridge-centroid direction is not
just too weak under the original calibration bars; it also fails this audit's minimum row-level
dose-response consistency bar. That closes the same global direction for a scale-only successor
from these artifacts.

This does not erase iteration 30's localization result. The bridge representation can still carry
diagnostic low-diversity information. What failed here is a narrower governance question: the
already-tested global centroid direction does not show enough consistent target-row response to
justify a bigger-alpha or same-direction follow-up.

## Next Authorized Step

Stop iteration 34. No heldout replay, iteration-12 scoring, selector evaluation, closed-loop work,
deployment language, or safety claim is authorized. A successor would need a fresh
pre-registration that changes the intervention family, target site, row conditioning, or claim.
