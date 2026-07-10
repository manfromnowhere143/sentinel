# Iteration 35 - response-heterogeneity audit null

Status: `HETEROGENEITY_NULL_NO_ACTIONABLE_STRATUM`

The hypothesis ([`HYPOTHESIS.md`](HYPOTHESIS.md)) was tested with the committed offline analyzer.
The audit used only committed iteration-33 calibration proof artifacts plus the committed
iteration-34 audit report. It did not run gcloud, Docker, a GPU, UniAD, NeuroNCAP, heldout replay,
iteration-12 scoring, selector evaluation, or closed-loop work.

Claim boundary: this is a **post-result offline audit null**. It does not select an alpha, rescue
iteration 33 or 34, prove or disprove a causal mechanism, authorize heldout replay, or make any
deployment or safety claim.

Harness:

- [`analyze_response_heterogeneity.py`](analyze_response_heterogeneity.py)

Primary evidence:

- [`proof-audit/response_heterogeneity_report.json`](proof-audit/response_heterogeneity_report.json)
- [`proof-audit/analyze_response_heterogeneity.command.txt`](proof-audit/analyze_response_heterogeneity.command.txt)
- [`proof-audit/local_verification.txt`](proof-audit/local_verification.txt)

## Verdict

| gate | result |
|---|---|
| S0 artifact and row integrity | **PASS**: iteration 34 verdict was `DIRECTION_AUDIT_NULL_NO_DOSE_RESPONSE`; iteration 33 calibration verdict was `CALIBRATION_NULL_NO_USABLE_ALPHA`; all five alpha cells had `2452` target rows, `108` `eligible_lowdiv` rows, `2344` `benign_control` rows, zero error rows, zero gross-validity failures, no duplicate target keys, and matching target keys across alphas |
| S1 measurable heterogeneity | **PASS**: `42/108` eligible rows had endpoint-spread slope `>= 0.05 m/alpha`, `34/108` had slope `< 0.00 m/alpha`, and the eligible slope IQR was `0.126519 m/alpha` |
| S2 frozen stratum localization | **FAIL/NULL**: no pre-declared baseline-geometry stratum passed all support, target-response, gap-alignment, and benign-control bars |
| Heldout, iteration-12, selector, closed loop | **NOT RUN**: prohibited by iterations 33, 34, and this audit |

## Audit Result

The audit report verdict is:

```text
verdict=HETEROGENEITY_NULL_NO_ACTIONABLE_STRATUM
s0_pass=true
s1_pass=true
s2_pass=false
passing_strata=
```

S1 shows that the failed global direction did not fail as a perfectly uniform nonresponse:

| S1 metric | value |
|---|---:|
| eligible rows | `108` |
| endpoint-spread slope `>= 0.05 m/alpha` | `42` |
| endpoint-spread slope `< 0.00 m/alpha` | `34` |
| median endpoint-spread slope | `0.030706` |
| p25 endpoint-spread slope | `-0.010798` |
| p75 endpoint-spread slope | `0.115720` |
| slope IQR | `0.126519` |

But S2 rejected every frozen stratum:

| stratum | eligible | benign | key failures |
|---|---:|---:|---|
| `executed_danger` | `108` | `0` | no benign support; nonnegative slope fraction `0.685185 < 0.85`; median spread slope `0.030706 < 0.08`; median best-gap slope `-0.000025 < 0.00`; alpha-1 spread fraction `0.129630 < 0.25` |
| `best_candidate_danger` | `104` | `0` | no benign support; nonnegative slope fraction `0.692308 < 0.85`; median spread slope `0.030706 < 0.08`; median best-gap slope `-0.000025 < 0.00`; alpha-1 spread fraction `0.134615 < 0.25` |
| `very_low_spread` | `21` | `0` | eligible support `21 < 24`; no benign support; response and gap bars failed |
| `near_lowdiv_threshold` | `87` | `0` | no benign support; nonnegative slope fraction `0.689655 < 0.85`; median spread slope `0.034146 < 0.08`; alpha-1 spread fraction `0.126437 < 0.25` |
| `multi_object` | `108` | `2284` | benign support passed, but nonnegative slope fraction `0.685185 < 0.85`; median spread slope `0.030706 < 0.08`; median best-gap slope `-0.000025 < 0.00`; alpha-1 spread fraction `0.129630 < 0.25` |
| `executed_not_danger` | `0` | `2344` | no eligible support |
| `best_candidate_safe` | `0` | `2344` | no eligible support |
| `single_object` | `0` | `47` | no eligible support; benign support `47 < 100` |

## Interpretation

Iteration 35 narrows the iteration-34 null. The row response is heterogeneous, so the failure is
not merely a single flat average hiding identical rows. However, the heterogeneity does not
localize to any frozen baseline-geometry stratum strongly enough to justify a conditioned
successor from these artifacts.

The current causal-intervention line is therefore closed in two ways:

- no same-global-direction scale-only successor is authorized by iteration 34;
- no frozen baseline-geometry row-conditioned successor is authorized by iteration 35.

This does not erase iteration 30's diagnostic localization result. The bridge representation can
still carry low-diversity information. What failed is the narrower intervention-governance claim:
the tested global bridge-centroid direction, even when audited by simple baseline geometry, does
not provide a reliable intervention route.

## Next Authorized Step

Stop iteration 35. No heldout replay, iteration-12 scoring, selector evaluation, closed-loop work,
deployment language, or safety claim is authorized. A successor would need a fresh
pre-registration that changes the intervention family or target site, rather than scaling or
row-conditioning the current global bridge-centroid direction from these artifacts.
