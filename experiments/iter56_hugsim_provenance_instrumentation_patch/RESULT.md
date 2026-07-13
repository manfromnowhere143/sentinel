# Iteration 56 - HUGSIM provenance instrumentation patch design: INSTRUMENTATION_PATCH_DESIGN_NULL

Status: `INSTRUMENTATION_PATCH_DESIGN_NULL` (source-only patch-design gate over the frozen HUGSIM
checkout at `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`).

This iteration did not run HUGSIM, did not touch GPU/cloud resources, did not edit Sentinel monitor
parameters, did not run a planner process, and did not inspect uncommitted simulator outputs. The
patch was drafted against a temporary local checkout and then statically verified against a clean
temporary clone of the frozen source.

## Frozen proof

- Patch draft:
  [`proof-patch/hugsim_provenance_instrumentation.patch`](proof-patch/hugsim_provenance_instrumentation.patch)
- Command receipt: [`proof-patch/verify_patch.command.txt`](proof-patch/verify_patch.command.txt)
- JSON report: [`proof-patch/patch_verification_report.json`](proof-patch/patch_verification_report.json)
- Markdown report: [`proof-patch/patch_verification.md`](proof-patch/patch_verification.md)
- Verifier: [`verify_patch.py`](verify_patch.py)
- Tests: [`tests/test_iter56_patch_verifier.py`](../../tests/test_iter56_patch_verifier.py)

## Result

The verifier confirmed several necessary conditions:

- source SHA matched `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`;
- the patch applied cleanly to a clean temporary clone;
- changed files were limited to `sim/utils/score_calculator.py`;
- required provenance fields were present;
- the changed Python file compiled.

The registered static guard still failed:

- `forbidden_metric_or_control_change:sim/utils/score_calculator.py:score_nc =:if score_nc == 0.0:`

The failed line is an additive branch intended to append provenance only when the existing
`score_nc` value is already `0.0`. The verifier nevertheless flags changed lines containing
`score_nc =` as metric/control-sensitive. Under the frozen protocol, that is a verifier failure,
not something to waive after the run.

## Interpretation

Iteration 56 produced a useful patch draft, but it did not produce an authorized instrumentation
patch. The draft's intended design is to keep HUGSIM scalar metric rows unchanged and add a
top-level `collision_provenance` sidecar to `eval.json`, populated from the existing
`ScoreCalculator` collision geometry path. Static application and compilation passed, but the
registered metric/control guard was too conservative for this branch form and returned null.

A successor may pre-register a narrower verifier that distinguishes assignment changes from
read-only branching on an existing score variable, or it may draft an alternative patch shape that
does not add any changed line matching the metric-control guard. Either successor still needs a
fresh pre-registration and one-shot verification before any HUGSIM run.

## Claim boundary

No patch is authorized for a HUGSIM run. No actor-match result is claimed. No prior HUGSIM collision
is attributed to any object. No safety, transfer, deployment, robustness, benchmark-ranking,
real-world, monitor-performance, HUGSIM-equivalence, HD-Score-execution, or retuning claim is made.
The only claim is that the first patch-design attempt was rejected by the registered static guard.
