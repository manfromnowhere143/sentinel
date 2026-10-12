# Diagnose a missed opportunity before expanding the planner

12 October 2026. Pre-acquisition decision for Iter159.

The immediate bottleneck is still a complete admissible action. Iter158 searched
10,633 transitions and retained only a 4.5 s prefix. Its beam failure cannot
distinguish infeasibility from inadequate search. Increasing its compute budget
without a constructive control would leave that ambiguity intact.

The recommended milestone is a route-aware baseline qualified on four disclosed
curved, cluttered fixtures with separately checked executable witnesses. All four
witnesses already pass scalar dynamics, foreground sweep, full background masks,
actuator limits and both progress checkpoints. Their commands belong to the
existing primitive alphabet. The search receives geometry and route, never these
witness commands. Routes are constructed from the witnesses: this is an intentionally
favorable engineering control, not hidden test data or a road benchmark.

| Alternative | Decision and evidence needed |
|---|---|
| More beam width on the exposed scene | Defer until a feasible opportunity can be preserved on controls. |
| New learned proposals or training | Defer: witness command coverage can first be tested without training. |
| Route-aware ranking with unchanged proposals | Test against the current endpoint guide at a fixed expansion budget. |
| Different pruning | Cross both rankings with ordinary rank selection and the existing speed-group selection; isolate the factors. |
| Full Smac/CommonRoad integration | Potential later comparator; its dynamics, map and progress interfaces need qualification. |
| Change the development scene | Remains available if the original case has no economical constructive opportunity; disclose selection. |

The candidate is route ranking with existing speed-group selection. Acceptance
requires four complete independently verified trajectories, including both progress
conditions and all declared constraints. As in the inherited contract, a
completion before a later checkpoint ends the trajectory; that checkpoint is
unobserved, not counted as a measured pass. One missed verified opportunity falsifies
that four-case qualification claim. It does not invalidate the witnesses or prove
that every route-aware planner fails. Improvements over the endpoint comparator
are counted only within each fixed pruning arm; no separate component receives
credit for a combined intervention.

Resources: local CPU only; 16 fixed runs, 18,000 attempted transitions per run,
24 retained nodes per depth, 96-action horizon, 120 s per run, 2,400 s producer
cap, 1,800 s independent admission cap, 1 GiB RSS, 256 MiB raw. All attempts,
pruning selections and selected paths are retained. A resource failure is invalid;
an incomplete bounded search is an explicit miss on this known feasible fixture.
No retry, outcome-driven tuning, source-scene search, native episode or provider use.

The outcome determines the next step. Passing controls permits registration of
one new source-scene search, with a qualified background-aware guide still an
open alternative. A miss requires inspecting the first lost witness prefix and
its surviving cell representative before changing proposals or spending on native
execution. Sentinel's broader sequence stays model opportunity, native execution,
actual monitor-time opportunity, equal-budget information ablation and held-out
transfer. No synthetic success establishes safety or competitive superiority.

## Primary-source decision review

Retrieved 12 October 2026; exact downloads and released source identities are in
SOURCES.json. These methods are not reimplemented or defeated in this study.

- [Smac Planner, 2401.13078v2, 8 May 2025](https://arxiv.org/html/2401.13078v2)
  separates executable motion search from obstacle-aware and nonholonomic
  guidance. Its released node implementation separately checks collision and
  combines obstacle and distance heuristics. This supports retaining exact
  admission while testing a ranking change. Sentinel's route score is neither
  Smac's method nor a qualified obstacle cost field, and has no admissibility bound.
- [CommonRoad competition report, 2512.19564v1, 22 December 2025](https://arxiv.org/html/2512.19564v1)
  verifies feasibility before cost and separates development from unknown
  evaluation scenarios. Its route-relative reactive planner uses curvature-aware
  velocity constraints; reference association can be ambiguous at overlapping
  lanes. Sentinel's nearest-route ranking is therefore a bounded control, not a
  universal route representation. Road compliance remains unmeasured here.
- [Multi-Heuristic A*, RSS 2014](https://www.ri.cmu.edu/pub_files/2014/7/rss14.pdf)
  addresses heuristic depressions using multiple guidance functions and an anchor
  search. Its completeness and suboptimality bounds depend on that algorithm's
  conditions. A pruned beam does not inherit those guarantees. Adding another
  heuristic without the anchor would not justify a completeness claim.

The current 2026 company/arXiv review remains in
[the engine review](../../docs/research/SENTINEL_FRONTIER_ENGINE_REVIEW_2026-10-12.md).
This narrower research changes the experimental design: known feasible controls,
factorial attribution and an explicit audit of proposal coverage versus pruning.
