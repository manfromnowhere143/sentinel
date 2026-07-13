# Iteration 55 - HUGSIM collision instrumentation source audit

Frozen before any iteration-55 source clone, analyzer, proof artifact, result, or claim.
This is a source-map audit only: zero GPU work, zero gcloud commands, zero simulator launches,
zero HUGSIM episodes, zero monitor retuning, zero metric edits, and zero box reads.

## Process disclosure

This is not blind. Iterations 48-54 are already published. Before freezing this file, the
post-iteration-54 docs, local launch scripts, and iteration-45 setup log were inspected. Those
inspections confirmed:

- the frozen HUGSIM source commit used for the transfer lane is
  `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`;
- HUGSIM's run entry point is `closed_loop.py`;
- previous committed proof artifacts include only scalar HUGSIM `eval.json` outputs, not the
  source that produced them;
- iteration 54 concluded that actor matching requires new collision actor/contact/proximity
  instrumentation.

Those inspections are disclosed rather than hidden. This audit therefore makes no inferential
surprise claim and uses no statistical pass/fail bar.

## Research question

Iteration 54 proved the current committed HUGSIM proof cannot identify the actor that produced an
`nc` drop. The next mature step is not another transfer run; it is a source-map audit:

**Where in the frozen HUGSIM source is `eval.json` / `nc` / HD-Score produced, and is there an
obvious non-semantic instrumentation point for logging collision/contact/proximity provenance in
a future run?**

This audit does not implement the instrumentation and does not run HUGSIM.

## Frozen evidence inputs

Allowed inputs:

- a read-only local clone of `https://github.com/hyzhou404/HUGSIM` checked out exactly at
  `62c690d39fd90020e68a196bd8bcc1c4d4191f2e`;
- `experiments/iter54_hugsim_provenance_support_audit/RESULT.md`;
- `experiments/iter54_hugsim_provenance_support_audit/proof-provenance/provenance_support_report.json`;
- committed HUGSIM launch scripts from iterations 46/48/49 for path/context cross-checks only.

Forbidden inputs:

- `sentinel-gpu` or any other remote box;
- staged datasets or scenario YAMLs outside the repository;
- simulator outputs outside committed proof trees;
- future experiment directories;
- any source checkout not at the frozen HUGSIM SHA.

## Frozen source-map method

The analyzer must inspect source text only and produce:

1. repository identity:
   - `git rev-parse HEAD`;
   - `git remote -v` redacted to host/repo, no credentials.
2. candidate source files containing metric/eval terms:
   - `eval.json`, `hdscore`, `pdms`, `nc`, `dac`, `ttc`, `comfort`, `rc`;
   - collision/contact/proximity terms: `collision`, `collide`, `contact`, `overlap`,
     `intersect`, `distance`, `bbox`, `box`, `actor`, `agent`, `vehicle`, `object`.
3. a ranked source map with short snippets around candidate lines, respecting repo-size limits;
4. whether a likely instrumentation point exists under these labels:
   - `metric_source_identified`: the file/function writing or returning scalar `eval.json` fields
     is identified;
   - `collision_geometry_source_identified`: source includes a geometry/contact/proximity
     computation used by the `nc`/collision metric;
   - `actor_identity_available_in_source`: the metric path appears to have object/actor identity
     available at the collision/proximity decision point;
   - `instrumentation_point_supported`: source supports a future no-metric-change logging patch
     that can add actor/contact/proximity provenance to per-episode outputs;
   - `source_map_insufficient`: source text inspection cannot identify enough to design the
     instrumentation.

The analyzer must not edit the cloned source.

## Verdicts

- `COLLISION_INSTRUMENTATION_SOURCE_NULL`: source checkout, identity, or parsing fails, or the
  metric/collision path cannot be identified well enough for an instrumentation design.
- `COLLISION_INSTRUMENTATION_SOURCE_MAP_COMPLETE`: source checkout identity is correct and the
  audit identifies a concrete future instrumentation point or a concrete missing-code boundary.

Either verdict is acceptable. If the source map is complete, the result may draft a future
instrumentation pre-registration, but it must not authorize a run by itself.

## Forbidden claims

No new safety, transfer, deployment, robustness, benchmark-ranking, real-world,
monitor-performance, HUGSIM-equivalence, actor-identity, actor-match, collision-cause, or
retuning claim. This audit may only map source locations and instrumentation feasibility.

## Required proof artifacts

- analyzer source and unit tests;
- `proof-source/source_map_report.json`;
- `proof-source/source_map.md`;
- `proof-source/analyze_source_map.command.txt`.

## Protocol

1. Commit this `HYPOTHESIS.md` ALONE.
2. Add and commit analyzer/tests; run `ruff check .`, `pytest -q`, and
   `python3 scripts/validate_docs.py`.
3. Clone/check out the frozen HUGSIM source into a temp/source-cache directory outside the repo.
4. Run the analyzer ONCE over that source tree.
5. Publish `RESULT.md` at full weight.
6. Update README, CONTINUITY, HANDOFF, and push.
