# Intervention-mechanism verdict — what could repair the collapse (survey 2026-07-11)

Planning-only document; not a pre-registration; authorizes no run. Question: after five
pre-registered linear-steering nulls (iters 31-38 family), does any published mechanism class
repair probe-detected failures where linear steering failed — or does detection-without-
correction hold across mechanisms? ~30 primary sources; load-bearing claims verified against
paper tables.

## Findings

1. **The asymmetry claim stands and is now a replicated cross-domain phenomenon.** Detection
   without correction (arXiv 2604.13068) has independent replications: probe-vs-control
   directions at cos 0.12-0.20 across 4 models (2606.24952); 29 fixed linear configs zero or
   harmful in medical LLMs (2605.05715); clinical triage probes at 98.2% AUROC with SAE
   clamping producing zero corrections (2603.18353); causal correction requires sustained
   multi-layer patching where corruption is one-shot (2604.15400). No published counterexample
   exists where a probe-derived centroid direction fixed anything. Our nulls extend the
   phenomenon to a continuous driving planner with stronger methodology than the LLM entries.
2. **Our five arms are the signature of causally inert directions, not under-dosed ones:**
   flat at every alpha, both signs, two sites (~0.03-0.04 m movement, no dose-response).
   Genuinely causal directions show monotonic dose-response with a degradation onset
   (2603.16335). Probe AUROC 0.95-0.97 was never evidence the direction was causal
   (2511.18284: separation metrics do not predict steering success).
3. **Scope guard for the claim:** Words in Motion (ICLR 2025, arXiv 2406.11624) steers graded
   kinematic attributes (speed) in continuous motion-forecasting transformers with
   paired-difference vectors at Pearson 0.988-0.993 — so the claim is that PROBE-DETECTED
   FAILURE MODES resist linear correction, not that regression transformers cannot be linearly
   steered.
4. **What has repaired safety failures on a frozen continuous policy:** LAE (arXiv 2509.20623,
   verified) — probe-gated LEARNED activation editing on a frozen multirobot RL policy, ~90%
   collision reduction, real hardware; convergent: CTRL-STEER closed-loop control
   (2606.00269), minimal-norm targeted interventions incl. a flow head (2603.05487). The
   working recipes are learned + state-dependent + gated — never fixed additive centroid
   vectors. Also credible: outcome-contrastive vectors at output-proximal sites (+39-71pp
   secure code, 2604.16697 — linear, but behavior-contrastive at the final layer, not
   probe-derived). Weak class: SAE zero-ablation (2607.06328 on GTRS is 7 days old,
   uncontrolled, discrete-scorer-specific, trades away ego progress; SAE-action is the weakest
   class everywhere else — GDM deprioritization 2025-03).

## Decision rules adopted

- No sixth linear-centroid variant, ever. Iter38 calibration stays deprioritized.
- Paper #2 (detection-without-correction in a driving planner) is publishable NOW with the
  monitor/abstention framing (probe-gated runtime gating beat every correction attempt in
  2605.05715 — which is what the released union already is).
- If ONE more intervention iteration is ever pre-registered, it is the two-arm design with
  the strongest published priors: (arm 1) probe-gated learned state-dependent edit
  (LAE-style: small gated editor on planner activations, trained to restore endpoint spread on
  collapse scenes with a retain loss, disjoint train scenes); (arm 2) outcome-contrastive
  linear vector fit from diverse-vs-collapsed PLAN OUTPUTS injected at the pre-head site.
  Mandatory controls: random-direction, random-gating, dose-response, benign-retain bars.
  Either outcome is valuable: repair extends LAE to driving; a null extends the asymmetry from
  "fixed linear" to "learned nonlinear."
- Sequencing unchanged: iter42 analyzer → HUGSIM transfer → deployment-flip successor rank
  ahead of any new intervention iteration.

Key sources: arXiv 2604.13068, 2606.24952, 2605.05715, 2603.18353, 2604.15400, 2509.20623,
2606.00269, 2603.05487, 2604.16697, 2406.11624, 2607.06328, 2511.18284, 2501.17148 (AxBench),
2602.09783.
