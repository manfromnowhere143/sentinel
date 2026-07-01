# Verification — scripts and raw-evidence archive

This directory holds the independent verification pass's tooling and the campaign's raw evidence,
pulled from the (ephemeral) GPU box and committed so that **every quantitative claim in this
repository can be re-derived offline from the repository alone**. The audit report itself is
[`../VERIFICATION.md`](../VERIFICATION.md).

## Scripts

| script | what it does | reproduces |
|---|---|---|
| [`audit_pooling.py`](audit_pooling.py) | parses the iteration 8/9/10 run logs run-by-run, proves episode determinism (i9 ≡ i10; i8[:6] ≡ i9), recounts the union side-impact collisions, recomputes safe-progress on unique episodes with a seed-paired bootstrap | every number in VERIFICATION.md §3.1–3.2 |
| [`analyze_v20.py`](analyze_v20.py) | parses the fresh 20-unique-episode OFF-vs-union pass, cross-checks run indices 0–7 against the committed iteration-8 evidence, computes the honest n=20 CI | VERIFICATION.md §4 |

Both run with no arguments beyond paths, no network, no GPU: `python3 audit_pooling.py`.

## Evidence layout

```
evidence/
  logs/    sentinel-<iter>.log        full run logs: every episode's ncap_score + impact_speed,
                                      arm/scene markers, the exact docker invocations (set -x)
  jsonl/   sentinel_<iter>_<arm>...   per-frame monitor decision logs written inside the model
                                      container: plan, tracked objects, risk terms, brake/act
                                      decisions — one JSON line per inference frame (gzipped)
  runs/    <iter>-<arm>.tar.gz        per-run ego_poses.json (the driven trajectory — progress is
                                      computed from it) + metrics.json, per scene, per run index
```

## Coverage

| iteration | logs | decision logs | per-run ego/metrics |
|---|---|---|---|
| 1b partial baseline | `sentinel-iter1b.log` | — (pre-monitor) | — |
| 2 A/B + ablation | `sentinel-ab.log`, `sentinel-abl.log` | `ab`, `abl_always`, `abl_proximity` | — |
| 3 progress metric | `sentinel-i3.log` | `i3_off`, `i3_always`, `i3_ttc` | `i3-*` |
| 4 gated | `sentinel-i4.log` | `i4_off`, `i4_ttcold`, `i4_gated` | `i4-*` |
| 5 tracked velocity | `sentinel-i5.log` | `i5_off`, `i5_tracked` | `i5-*` |
| 6 CPA | `sentinel-i6.log` | `i6_off`, `i6_cpa` | `i6-*` |
| 7 margin sweep | `sentinel-i7.log` | `i7_cpa10`, `i7_cpa15` | `i7-*` |
| 8 union | `sentinel-i8.log` | `i8_off`, `i8_union` | `i8-*` |
| 9 evade null | `sentinel-i9.log` | `i9_off`, `i9_union`, `i9_evade` | `i9-*` |
| 10 brakevade null | `sentinel-i10.log` | `i10_*` | `i10-*` |
| 11 early-evade null | `sentinel-i11.log` | `i11_off`, `i11_stop`, `i11_evade` | `i11-*` |
| G1 shadow study | — | committed earlier at [`../iter2_monitor/proof/risk.jsonl.gz`](../iter2_monitor/proof/risk.jsonl.gz) | — |
| v20 fresh measurement | committed with the §4 follow-up | idem | idem |

## Reading a decision log

Each `sentinel_*.jsonl` line is one `/infer` frame: `{"reset": true, "run": k}` marks episode
boundaries; frames carry the planner's trajectory, the tracked objects (id, position, score), the
monitor's risk terms (CPA, closing TTC where applicable), and the action taken (`act`/brake latch).
This is the ground truth for statements like "fired 0 times on the clean scene" — they are counts
over these lines, not inferences.

## Provenance and integrity

Logs were copied verbatim from `/var/log/` and `/opt/sentinel-stack/UniAD/` on the `sentinel-gpu`
box on 2026-07-02 (before and during the v20 pass). Nothing was filtered or rewritten; the
gzip/tar containers are for size only. Where a published number disagreed with these files, the
*file* won and the document was corrected — the three cases are listed in
[`../VERIFICATION.md`](../VERIFICATION.md) §3.
