# Sentinel mission evidence and frontier-alignment audit

Status: iteration-123 audit note. It is not a pre-registration and authorizes no run.
Purpose: review Sentinel as a hostile technical reviewer would after iteration 122, with the
standard set by current runtime-monitoring, long-tail, auditability, and closed-loop validation
work. This note records alignment and gaps only; it does not upgrade any empirical claim.

## Source Refresh

The source refresh reinforces the same pressure surface:

- Mobileye frames the long-tail problem as rare edge-case discovery, diagnosis, targeted
  scenario generation, and better signal-to-noise rather than more ordinary data:
  <https://www.mobileye.com/blog/diagnosing-the-long-tail-how-mobileye-turns-edge-cases-into-targeted-training/>
  and <https://www.mobileye.com/opinion/driving-the-long-tail/>.
- Tesla's own FSD Supervised v14 support page keeps the supervision boundary explicit:
  <https://www.tesla.com/support/fsd/v14-trial>.
- Recent arXiv runtime-monitoring work makes self-evolving monitors and targeted blind-spot
  acquisition an active frontier:
  <https://arxiv.org/abs/2607.03755>.
- Mission-level runtime assurance separates local collision avoidance from route/mission
  feasibility:
  <https://arxiv.org/abs/2606.06996>.
- Rulebook-aware NMPC work emphasizes auditability of how safety, regulation, comfort, and
  efficiency conflicts are resolved:
  <https://arxiv.org/html/2607.10975v1>.
- Real-world perturbation testing shows offline/model-level robustness can fail to predict
  hardware or vehicle-level behavior:
  <https://arxiv.org/html/2607.04953v1>.

These sources support the audit frame. They do not imply Sentinel matches or exceeds any current
industrial autonomy stack.

## Defensible Strengths

1. Evidence discipline is real. The campaign has pre-registrations, frozen bars, nulls, a
   verification pass that withdrew an over-claim, full gates, and published handoff state. This is
   materially stronger than a typical single-run benchmark story.
2. The core NeuroNCAP result is still sharply framed: a frozen UniAD planner plus a released union
   monitor improves the full14 benchmark score with a confidence interval excluding zero, while the
   deployment metric resolves to a tight null. That distinction is preserved in README, report, and
   manuscript.
3. The HUGSIM result is not hidden. The HUGSIM transfer null is published, and the subsequent
   mechanism work explains the support-core branch without pretending the monitor was repaired.
4. Iteration 122 fixed a real documentation gap: the support-core taxonomy now appears in a
   dedicated mechanism note, technical report, and manuscript, with a verifier enforcing the claim
   boundary.
5. Frontier alignment is credible when Sentinel is described as runtime monitoring,
   failure-localization, and safety-evidence infrastructure around opaque planners.

## Reviewer Attack Surface

1. Top-level freshness was inconsistent before this audit. README's table was current through
   iteration 122, but its opening prose still said "Ninety-three registered iterations" and its
   long opener did not identify iterations 98-122 as summarized elsewhere. This audit fixes that
   surgically.
2. The July 13 frontier memory capsule named iteration 84 as the latest HUGSIM mechanism result.
   That was historically true for that source pass but stale after iterations 85-122. This audit
   updates the memory capsule to point future sessions at the support-core taxonomy note.
3. The report and manuscript now include the support-core taxonomy, but they remain compact rather
   than fully reauthored around the HUGSIM transfer/mechanism arc. That is acceptable for this
   audit; a publication push should get a separate manuscript-refresh pass.
4. Sentinel does not yet solve self-evolving monitor improvement or targeted scenario generation.
   EvoEye-like blind-spot acquisition is adjacent, not covered by the current evidence.
5. Sentinel does not yet evaluate mission-level route feasibility or rulebook-priority conflict
   resolution. It is a collision-risk/runtime-monitor evidence system, not a mission-planning or
   regulatory-compliance controller.
6. Sensor perturbation and real-world transfer remain bounded. Iterations 41-44 created exact
   replay support and offline perturbation findings, but no hardware-in-loop, vehicle-in-loop, or
   real-world robustness claim follows from them.
7. The HUGSIM support-core taxonomy is `8` rows. It is valuable mechanism evidence, not a
   population-rate estimate.

## Freshness Fixes

- README now says the campaign is current through iteration 122 and points readers to the status
  table as the canonical per-iteration ledger.
- README "The result" wording now describes the registered campaign through iteration 122 without
  implying the core released-union metric changed after HUGSIM.
- `FRONTIER_ALIGNMENT_MEMORY_2026-07-13.md` now marks the iteration-84 note as historical and
  points future sessions to the iteration-122 support-core taxonomy documentation.

## Next Bounded Actions

1. If the next goal is publication quality, run a dedicated manuscript/report freshness pass that
   rewrites the HUGSIM transfer and support-core mechanism arc coherently rather than adding more
   paragraphs.
2. If the next goal is frontier research leverage, design a pre-registered blind-spot acquisition
   or scenario-generation audit seeded by HUGSIM support-core failure modes. Keep it offline until
   candidate generation rules and claim boundaries are frozen.
3. If the next goal is robustness, design a closed-loop or higher-fidelity successor to the
   iter41-44 object-stream perturbation line. Do not infer real-world robustness from offline replay.
4. If the next goal is control architecture, define a mission/rulebook boundary explicitly before
   claiming anything about comfort, regulation, mission completion, or real-time feasibility.
5. Before any external pitch, run a one-page claim ledger: what is proven, what is a null, what is
   mechanism-only, and what is out of scope.

## Claim Boundary

This audit authorizes no repair, actor-causality, threshold-value, transfer upgrade, safety,
deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior,
first-responder behavior, acquisition-value, retuning, production, commercial claim, or claim that
Sentinel matches or exceeds Tesla, Mobileye, SpaceX, Waymo, NVIDIA, or any current frontier
autonomy stack.
