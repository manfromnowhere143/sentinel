# Frontier positioning survey — 2026-07-11

Status: research/positioning document. It is not a pre-registration and authorizes no run.
Purpose: record, with sources, where this campaign sits against the mid-2026 external state of
the art, so positioning claims in the paper and README trace to checked evidence. Compiled from
a three-stream external survey (benchmark landscape; monitor + interpretability literature;
industry/frontier-lab landscape) run on 2026-07-11. Key numeric claims below were re-verified
directly against the primary sources where marked [verified]; the rest carry their origin URL
and should be re-verified before entering the paper.

## 1. NeuroNCAP landscape (mid-2026)

Two protocol families exist and must never be conflated: with UniAD-style trajectory
post-processing (published UniAD 1.84 / VAD 2.75 — our family) and without post-processing
(UniAD 0.73 / VAD 0.66).

| result | family | score / CR | source |
|---|---|---|---|
| UniAD baseline (published) | w/ pp | 1.84 / 68.7% | arXiv 2404.07762 |
| UniAD rerun by DMAD [verified: repo README] | w/ pp | 2.11 / 60.4% | github.com/shenyinzhe/DMAD |
| **Our reproduction (full14 power, n=20/pair)** | w/ pp | **2.12** | experiments/full14_power |
| DMAD | w/ pp | 2.65 / 50.1% | arXiv 2502.07631 |
| **Our released union (frozen planner + monitor)** | w/ pp | **2.91, delta CI [+0.605, +0.928]** | experiments/full14_power |
| BridgeAD-S / BridgeAD-B (CVPR 2025) [verified: HTML Table 2] | w/ pp | 2.98 / 46.1% · 3.06 / 44.3% | arXiv 2503.14182 |
| Impromptu VLA (NeurIPS 2025 D&B) | no pp | 2.15 / 65.5% | arXiv 2505.23757 |
| Reasoning-VLA | no pp | 2.25 / 59.4% | arXiv 2511.19912 |
| ImagiDrive (ICRA 2026) [verified: HTML table] | no pp | 3.49 / 44.9% | arXiv 2508.11428 |

Readings:

- DMAD's independent UniAD rerun (2.11) corroborates our 2.12 reproduction. The official
  neuro-ncap repository also lists UniAD at 2.111 / 60.4%.
- Every result above ours changes or replaces the planner (retraining or a VLM agent). No
  published work reports the NeuroNCAP composite score for a runtime monitor on a frozen
  planner. Correct framing: a training-free plug-in on the frozen planner recovers most of the
  gap to retrained state of the art (2.12 → 2.91 vs BridgeAD-B 3.06), at a measured
  deployment-metric cost of approximately zero, with the benchmark's only pre-registered,
  CI-reported protocol. Never frame 2.91 as absolute benchmark state of the art.
- Nearest peer: CATPlan/RiskMonitor (arXiv 2503.07425; v2 2026-02-08 retitled "Collision Risk
  Estimation via Loss Prediction...") — learned head over planner internals trained on the sign
  of the planner's collision loss, max-brake policy, NeuroNCAP closed-loop AUROC 70.6%,
  collision-rate-only reporting, no composite score, no CIs, no progress/deployment cost, ~1
  citation, no venue. Our result must cite it as closest prior and compare explicitly.
- Other adjacent systems: Argus (ASE 2025, arXiv 2511.09032) — monitor + takeover on frozen
  TCP/UniAD/VAD but in CARLA, with an invented replacement trajectory; TOAD (arXiv 2606.07170)
  and MPA (NeurIPS 2025, arXiv 2511.21584) — test-time optimization/adaptation, not monitors;
  DriveSafer (arXiv 2605.16737) — needs a training-time component, NAVSIM only.
- Benchmark health: NeuroNCAP is alive but niche (~62 Semantic Scholar citations 2026-07-11;
  no leaderboard; used by the 2025-26 VLA wave). The field's closed-loop center of mass:
  NAVSIM v2/navhard, Bench2Drive, HUGSIM (TPAMI 2026; RealADSim @ ICCV 2025), Waymo WOD-E2E.
  Its authors' own limitations: rendering artifacts worst in the collision-imminent regime,
  scripted non-reactive adversaries, 14 scenes, vehicle-only, one shared LQR controller, no
  sim-to-real validation of outcomes. The 14-scene count — not run count — is the binding
  statistical constraint; our CIs answer run noise, not scene diversity.

## 2. Monitor + interpretability literature

- Runtime shielding of camera-input E2E planners in photorealistic closed loop is nearly
  unoccupied: no CBF/safety-filter paper found filtering UniAD-class planners on
  NeuroNCAP/HUGSIM/Bench2Drive; RSS literature concedes over-conservatism (our iter13
  quantified it closed-loop); VLM-as-monitor work is offline anomaly detection at ~1-2 Hz, no
  closed-loop collision-avoidance evidence. A June 2026 survey ("Silent Failures in Physical
  AI," arXiv 2606.00090) states no surveyed stream supplies a complete runtime authorization
  boundary between black-box physical-AI models and execution.
- Planner-internals interpretability is near-empty: the only substantive entry is arXiv
  2607.06328 (submitted 2026-07-07): SAEs at the pre-scoring latent of GTRS/iPAD
  (vocabulary-scoring planners), open-loop NAVSIM only. No published probing or steering of
  UniAD/VAD-class query-based planner internals; no published measurement of plan-diversity
  collapse conditioned on hazard; no published localization of that collapse to an internal
  representation. Our iters 29-38 line appears first-of-kind on both the positive (probe AUROC
  0.950 bridge / 0.971 track_query, scene-clustered bootstrap) and negative (linear steering
  nulls at both sites, both signs) sides.
- The steering nulls have an LLM-side mirror: "Detection Without Correction: A Robust Asymmetry
  in Activation-Based Hallucination Probing" (arXiv 2604.13068, 2026-04). Independent evidence
  of the same asymmetry in a different model class is a cross-domain safety finding, not a
  failed experiment. VLA steering (CoRL 2025, arXiv 2509.00328 and follow-ons) succeeds on
  language-conditioned transformers — the contrast with imitation-trained geometric planners is
  itself a claim.
- Mode collapse under imitation is now named at the training-objective level (GuideFlow, CVPR
  2026, arXiv 2511.18729; DIVER, arXiv 2507.04049; TransDiffuser; DiffusionDriveV2 — even
  diffusion planners collapse), but nobody measures it hazard-conditioned or internally. Scope
  our claim to imitation-regression planners; anchor/vocabulary planners are an open question.
- Methodology norms: single-run, CI-free reporting is standard (Bench2Drive DS run-to-run sd
  ~19; CARLA DS variance ~5 across seeds, typically reported single-run, arXiv 2605.00066);
  pre-registration never entered mainline AD venues; negative results structurally
  disincentivized. Our protocol exceeds field norms; sell it at safety-adjacent venues (TMLR,
  NeurIPS D&B, SafeAI/WAISE) and to frontier-lab audiences rather than expecting AD reviewers
  to reward it per se.

## 3. Industry and frontier-lab landscape

- The architecture thesis is shipped practice: Zoox's Collision Avoidance System is a parallel
  guardian channel with dedicated CAS teams and live postings; Waymo describes independent
  collision-avoidance backups and published the Reference Driver model (Nature Communications,
  announced 2026-06-10) benchmarking collision avoidance against a competent-human reference;
  Mobileye's Compound AI Systems / Primary-Guardian-Fallback position paper is this campaign's
  thesis stated by a public company; an NVIDIA posting asks near-verbatim for "runtime
  arbitration and safety enforcement mechanisms between AI-generated trajectories and
  rule-based safety constraints... Minimum Risk Maneuver strategies."
- Big-headcount directions are VLA driving models (NVIDIA Alpamayo, CES 2026; Waymo EMMA line)
  and generative world models for evaluation (Waymo World Model on Genie 3, 2026-02; Wayve
  GAIA-3, 2025-12; NVIDIA Cosmos; Applied Intuition RAYNOVA). "Verification of learned
  drivers" appears on every stated open-problem list. Regulatory tailwind: ISO/PAS 8800:2024,
  UNECE draft global ADS regulation adopted 2026 with mandatory safety cases and in-service
  monitoring.
- Frontier-lab overlap: runtime monitoring of opaque policies is the dominant 2026 AI-control
  agenda (DeepMind AI Control Roadmap 2026-06-18; Anthropic production probe cascades and
  monitor-blind-spot benchmarks; OpenAI agent-monitoring posts; ControlConf 2026). DeepMind
  deprioritized SAEs after linear probes won (2025-03) and now ships production probes for
  Gemini (arXiv 2601.11516). Probe-based, causally-tested representation findings on an opaque
  safety-critical policy with closed-loop ground truth is precisely the available, unoccupied
  bridge position: control-style monitoring demonstrated on a physical-substrate policy. Honest
  non-overlap: no frontier-lab safety team works on driving; Thinking Machines has no safety
  agenda; Tesla has no guardian-channel culture or research-hiring surface.
- Independent-researcher routes with documented conversion: Anthropic Fellows (>40% to
  full-time) and MATS on the safety side; on the AV side, arXiv+GitHub evidence is admissible
  at Waymo/NVIDIA/Zoox hiring lines but no verified 2024-26 case of a fully unaffiliated hire
  off a repo alone. Leaderboard-chasing has falling currency ("The Leaderboard Illusion,"
  arXiv 2504.20879, NeurIPS 2025).

## 4. Consequences adopted by the campaign (2026-07-11)

1. Paper related work now carries a source-verified "retrained planners on the same benchmark"
   paragraph (BridgeAD, ImagiDrive, DMAD corroboration); the headline framing rule above is
   binding for all documents.
2. The linear-steering mechanism line (iters 31-38 family: centroid directions, alpha grids,
   both sites, both signs) is closed by weight of five consecutive pre-registered nulls unless
   a successor arrives with a qualitatively different mechanism class and a fresh
   pre-registration. Iter38's authorized-but-unlaunched calibration is deprioritized under the
   defensibility rule.
3. The two external upgrades that most change expert reception, both single-digit-GPU and
   pre-registerable: (a) finish the VAD second-planner line (staged since
   docs/vad_generalization/STATUS.md); (b) a second closed-loop benchmark family transfer
   (HUGSIM or Bench2Drive) for the released union.
4. The iters 29-38 probe/steering line is a second paper for a safety-methods audience
   (detection-without-correction in a driving planner), not a bolt-on to the current
   submission.
5. NeuroNCAP scene count is the binding statistical constraint and is stated as such wherever
   the power-run CIs are quoted.
