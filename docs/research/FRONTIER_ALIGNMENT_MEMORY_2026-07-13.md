# Frontier alignment memory capsule - 2026-07-13

Status: durable research-memory note. It is not a pre-registration and authorizes no run.
Use this when a future session needs the compressed memory of the wider Stanford/MIT/Tesla/
Mobileye/NHTSA/Waymo/NVIDIA research pass. The longer source-backed memo is
[`FRONTIER_PROBLEM_ALIGNMENT_2026-07-13.md`](FRONTIER_PROBLEM_ALIGNMENT_2026-07-13.md).

## Durable findings

1. The frontier problem is long-tail failure discovery, not average-case driving. Mobileye's
   2026 framing is signal-to-noise: rare events, intrinsic uncertainty, shortcut learning, and
   weak supervision mean more ordinary data is not enough. Valuable systems mine, synthesize,
   diagnose, and validate the tail.

2. The academic safety frontier is validation, falsification, failure distributions, and safety
   cases. Stanford SISL/AA228V/NAV/ASL and MIT REALM all point to rigorous specification,
   uncertainty, formal methods, safety filters, and efficient failure search rather than broad
   performance storytelling.

3. Supervised autonomy remains supervised. Tesla's official FSD language still requires active
   driver supervision and does not claim full autonomy. MIT AVT/AgeLab reinforces that trust,
   driver interaction, and real-world use patterns are first-class problems, not presentation
   details.

4. World models and controllable simulation are becoming frontier infrastructure. Waymo World
   Model/DeepMind Genie/NVIDIA Cosmos imply a later Sentinel lane: generate or mutate rare
   scenarios after the observed HUGSIM failure mechanism is understood well enough to know what
   scenarios are informative.

5. Operational semantics matter. NHTSA's July 2026 first-responder warning is a hard boundary:
   emergency scenes, flares, smoke, fire, cones, ambulances, and police interactions are not
   covered by the current NeuroNCAP/HUGSIM evidence.

6. Sentinel's strongest defensible niche is not a full AV stack. It is a runtime monitor,
   failure-localization system, and safety-evidence ledger around opaque planners. Its value is
   highest when it produces pre-registered mechanisms, falsifiers, negative results, and exact
   claim boundaries.

7. Historical note: at the time of the July 13 research pass, the latest HUGSIM mechanism result
   was iteration 84, `HUGSIM_SELECTED_SURFACE_SUPPORT_BRIDGE_SPLIT_COMPLETE`. In the fixed rows,
   released hazard-surface selection followed logged path geometry, while logged collision
   provenance bridged to different surface-ineligible support objects.

8. Post-iteration-122 update: the HUGSIM mechanism line continued through the support-core branch
   and now has a bounded documentation integration:
   [`SUPPORT_CORE_TWO_TRACK_TAXONOMY_2026-07-14.md`](SUPPORT_CORE_TWO_TRACK_TAXONOMY_2026-07-14.md).
   Future sessions should read that note, iteration 122, and `docs/NEXT_PHASE.md` before treating
   the old iteration-84 recommendation as current.

## Working memory for future sessions

- Do not spend the next session on open-ended frontier research unless a new current event or
  paper changes the decision surface.
- Do not describe Sentinel as deployment-ready, safe, autonomous, first-responder-capable,
  world-model-based, robotaxi-grade, or commercially validated.
- Do describe Sentinel as a disciplined monitor/evidence system whose HUGSIM branch has moved
  from transfer null to mechanism decomposition.
- The old next-scientific-question note about the iteration-84 arbitration split is now historical:
  later iterations decomposed that branch and the support-core line through iteration 122. Use
  `docs/NEXT_PHASE.md` and the support-core taxonomy note as the current HUGSIM state.
- Any next experiment still requires a fresh `HYPOTHESIS.md` before analyzer work, no GPU unless
  pre-registered, and no threshold/repair/safety/transfer/deployment claim unless proven.

## Source anchors

- [Mobileye - Driving The Long Tail](https://www.mobileye.com/opinion/driving-the-long-tail/)
- [Mobileye - Diagnosing the long tail](https://www.mobileye.com/blog/diagnosing-the-long-tail-how-mobileye-turns-edge-cases-into-targeted-training/)
- [Stanford AA228V/CS238V](https://aa228v.stanford.edu/)
- [Stanford SISL research](https://sisl.stanford.edu/research/)
- [MIT AVT](https://news.mit.edu/2024/mit-advanced-vehicle-technology-consortium-1122)
- [MIT REALM](https://aeroastro.mit.edu/realm/)
- [Tesla FSD support](https://www.tesla.com/support/fsd)
- [NHTSA first-responder AV call to action](https://www.nhtsa.gov/press-releases/av-developers-automated-vehicle-that-cannot-safely-interact-first-responders-danger)
- [Waymo World Model](https://waymo.com/blog/2026/02/the-waymo-world-model-a-new-frontier-for-autonomous-driving-simulation/)
- [NVIDIA Cosmos](https://www.nvidia.com/en-us/ai/cosmos/)

## Boundary

This memory capsule is recall infrastructure only. It authorizes no experiment, no GPU work, no
HUGSIM run, no threshold change, no repair, no retuning, no deployment/safety/benchmark claim, no
commercial-value claim, and no real-world/first-responder claim.
