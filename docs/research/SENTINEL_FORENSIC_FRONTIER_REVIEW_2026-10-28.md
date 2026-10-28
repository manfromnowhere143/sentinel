# Sentinel: forensic frontier and direction review

28 October 2026. **Strategic assessment: proposed.** Retained scientific state remains
Iter191 `supported`; integrated qualification remains **3/4**. This review is not a new
experiment, comparative benchmark, safety certification or valuation. Evidence base:
commit `345495fee70c12a30928353779f3507046484791` in the owned Sentinel worktree.
Selected repository inputs have a retained [identity inventory](forensic_2026_10_28/review_inputs.json).

## Verdict

Sentinel addresses an important problem and has earned a narrow, credible research result.
It has **not demonstrated state-of-the-art performance, deployable runtime assurance,
competitive superiority, or an acquisition case**. The strongest reason to continue is the
possibility of measuring which failures can still be prevented, with what information,
action and response time. That possibility remains a hypothesis worth testing.

The immediate danger is spending indefinitely on the behavior of a few exposed development
cases while mistaking verification volume for independent evidence of general capability.
The latest connector improvement is useful engineering. It should be closed with a bounded
integration test, then connected back to actual-history recovery and unseen cases.

My recommendation is to pursue a specific capability: **recoverability-grounded evaluation
that produces checked intervention witnesses, explicit uncertainty, and useful failure data**.
An offline evaluator can support training and validation before a runtime policy is ready.
The mission should remain broad enough to investigate information value, but the next
deliverable needs one measurable capability and strong comparators.

## What was reviewed

This is a dated, targeted review, not an exhaustive systematic review of every relevant paper
or every repository artifact. The [source ledger](forensic_2026_10_28/sources.json) identifies
versions, reading depth and limitations. Primary research was inspected at the abstract,
method, result and limitation levels indicated there. Papers and company announcements
were not independently reproduced. Company descriptions establish public positioning;
they do not establish comparative performance.

Repository review covered the current recovery documents, README evidence narrative,
the released union adapter, current feedback proposal and inherited dynamics, retained
results from the driving, attribution, timing and recovery campaigns, and the October 9
[information and recoverability direction](SENTINEL_INFORMATION_AND_RECOVERABILITY_RESEARCH_DIRECTION_2026-10-09.md).
It included one new isolated constructed probe of unchanged legacy input handling.
No driving, integrated search, provider operation or GPU experiment was launched.

## Sentinel's evidence, with the costs included

| Question | Retained evidence | Assessment |
|---|---|---|
| Does the released monitor improve its original benchmark? | NeuroNCAP score 2.12 → 2.91; registered run-index bootstrap difference +0.783 [0.605, 0.928], 799/800 planned episodes. | Supported for that campaign; not a modern competitor comparison. |
| Does every safety outcome improve? | Side collisions 74% → 44%, stationary 29% → 18%, frontal 78% → 90%. Frontal/0346 rises 50% → 100%. | Aggregate score hides an important adverse stratum. |
| Is progress preserved? | Safe-progress difference −0.032 [−0.127, 0.065]. VAD transfer shows 2.30 → 0.75 safe-progress with over-braking. | Neither broad progress benefit nor equivalence is established. |
| Is the semantic mechanism established? | Iter134's 1,200 episodes give union-minus-placebo +0.3683 [−0.1901, 0.8866]; realized brake exposure differs. | `PLACEBO_HARM_OR_NULL`; attribution unresolved. Do not adjust away a post-treatment exposure difference. |
| Does the original gain transfer? | HUGSIM easy/medium −0.017 [−0.055, 0.026]; hard/extreme −0.0089 [−0.0438, 0.0203], 104 episodes each. | Both `TRANSFER_NULL`; not proof of equivalence or universal failure. |
| Is useful recovery demonstrated at actual intervention time? | Iter163 completes a fixed native path from reset. Iter164 preserves the 6.25 s first-fire history and finds no complete continuation under its registered search. | Reset success does not answer the actual-history question. Finite search failure does not prove unavoidability. |
| Is the latest proposal useful? | Iter191 original completions 1/23 → 8/23, seven gains and zero losses; synthetic requests separately 5/21 → 13/21. | Supported connector qualification on exposed, dependent requests from four cases. No new integrated result. |
| Is end-to-end deadline behavior established? | Iter148: all 368 verified loops exceed 250 ms; median 1.792 s. The synchronous simulator waits. | No demonstrated 4 Hz operation or robust late-result behavior. This is not isolated Sentinel inference latency. |

Sources: [power run](../../experiments/full14_power/RESULT.md),
[placebo](../../experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md),
[easy/medium transfer](../../experiments/iter48_hugsim_transfer_gate/RESULT.md),
[hard/extreme transfer](../../experiments/iter49_hugsim_hard_tier_gate/RESULT.md),
[VAD](../../experiments/vad_generalization/RESULT.md),
[reset replay](../../experiments/iter163_native_path_replay/RESULT.md),
[actual history](../../experiments/iter164_monitor_time_continuation/RESULT.md),
[connector](../../experiments/iter191_stop_wait_release/RESULT.md),
[timing](../../experiments/iter148_recovery_study/RESULT.md).

The retained source freezes, independent replay implementations, known-bad controls and
visible null results are valuable engineering assets. Millions of point classifications
measure verification work, however; they are not millions of independent driving situations.
Repeated development on four cases cannot become a held-out benchmark by adding more seeds.

## Three concrete findings from the code

**Missing perception can be mistaken for a clear scene in the released adapter.**
The [Iter15 helper](../../experiments/iter15_latch_release/server_patch_union_release.py)
normalizes missing or null object arrays to an empty list. With an existing braking latch,
four such calls advance the clear counter and release braking. A decoding exception returns
the nominal plan even while the latch remains set. The
[constructed probe](forensic_2026_10_28/probe_legacy_inputs.py) extracts the literal helper
without running the installer. [Its result](forensic_2026_10_28/legacy_input_probe.json)
confirms all-field missing, object-field missing, null-object, valid-empty, present-threat
and decoder-exception behavior across 24 calls. This demonstrates a code path, not its
frequency or causal contribution to any historical collision.

For a future runtime successor, missing, stale, invalid and observed-clear inputs need
distinct states and a qualified fallback. Blindly retaining braking is not a universal
fix: rear impacts, road position and loss of control can make stopping hazardous. The fallback
must be qualified for the actual operating conditions. Preserve the historical implementation
and results; make any successor a separately tested change.

**The new stopping proposal has privileged timing.**
[Iter191 policy](../../experiments/iter191_stop_wait_release/policy.py) takes its final
checkpoint from retained comparator `hazard_time` values. That is legitimate for a scoped
offline qualification. It is not evidence that a deployed system can infer when to release
from uncertain observations. This input boundary must remain explicit in comparisons.

**Exact discrete replay is not physical-model validation.**
The inherited [transition](../../experiments/iter153_action_feasibility/planner.py) updates
speed before position. At 0.125 m/s, a −0.5 m/s² command over 0.25 s yields zero translation
in this discrete update. Ideal continuous constant-deceleration motion travels 0.015625 m.
Both calculations can be internally correct for their respective models. The difference
shows why checked discrete witnesses require model-error and swept-occupancy analysis before
physical claims. It does not invalidate the frozen discrete qualification or prove that this
particular discrepancy caused an observed miss.

## What relevant research already does

| Primary work and version | Relevant contribution and boundary | Consequence for Sentinel |
|---|---|---|
| [RiskMonitor](https://arxiv.org/html/2503.07425v2), 8 February 2026 | Predicts collision-related loss from frozen planner tokens; reports closed-loop braking improvements. Its discussion identifies distribution shift and simulator limits; its examples include a shared perception miss. | Mandatory learned-monitor comparator. Better token classification alone does not establish timely prevention or independent perception. |
| [FORCE-OPT](https://arxiv.org/html/2507.22389v1), 30 July 2025 | Converts multimodal predictions into calibrated reachable sets, with adaptive conservatism. Evaluation includes synthetic unsafe plans and city shift. Coverage guarantees depend on calibration assumptions; average coverage is not a guarantee for every rare subgroup. | Compare uncertainty-aware monitoring, not just TTC. Keep detection metrics separate from actual closed-loop recovery. |
| [RAYA](https://arxiv.org/html/2609.21690v1), 18 September 2026 | Embeds a learned finite-horizon recovery margin and bounded objective reweighting inside MPC. Reports 7,200 simulation episodes per controller and onboard quadrotor experiments. Its structural constraint argument does not certify learned-margin accuracy. | Recoverability-aware control is already an active frontier. Include an in-solver comparator where the task and interface permit it. |
| [PL-CBF](https://arxiv.org/html/2605.16588v1), 15 May 2026 | Parallel rollout of multiple fallback policies plus a minimally modifying safety filter. Completeness depends on policy-library coverage relative to clearance; finite-horizon operation is distinguished from invariant-set guarantees. | A small fallback library is a strong, interpretable comparator before inventing another planner. A finite library miss stays unknown without stronger evidence. |
| [Model-aware scene generation](https://arxiv.org/html/2610.35448v1), 26 October 2026 | Distills planner surrogates, generates attacks and escape labels, then fine-tunes two planners. Reports NeuroNCAP collision reductions 28.0% → 12.2% and 37.5% → 19.2%. Evidence is limited to two planners and one closed-loop simulator. | Failure-to-repair data generation is occupied territory. These author-reported numbers are not comparable to Sentinel without matching protocols. |
| [Bench2Drive-Robust](https://arxiv.org/html/2605.18059v1), 18 May 2026 | Evaluates camera failures, ego-state errors and delayed execution; main delay tests use fixed FIFO buffering. | Delays and stale observations must change the simulated action history, not just appear as profiler numbers. |
| [Argus](https://arxiv.org/html/2511.09032v1), 12 November 2025 | Runtime hazard monitoring and takeover across TCP, UniAD and VAD. | Monitor-plus-mitigator architecture itself is not a novelty claim. |
| [EvoEye](https://arxiv.org/html/2607.03755v2), displayed 7 July 2026 | Uses monitor errors to guide additional scenario acquisition on Apollo/CARLA. | Sampling the monitor's blind spots already has a direct comparator; detection improvement still needs an intervention test. |
| [VeriFine](https://arxiv.org/html/2610.08761v1), 6 October 2026 | Co-evolves policy, curriculum and a rubric judge; retains separate evaluation sets and a fixed reference judge. | A judge score can guide discovery. Final Sentinel claims should remain anchored in independent physical outcomes and measurement contracts. |
| [DualShield](https://arxiv.org/html/2601.15729v1), 22 January 2026 | Uses HJ values both to guide model-based diffusion and to filter executed controls. Reports 100 simulated U-turn trials in a scaled setting; acknowledges greater computational cost than baselines. Equation 15 permits safety slack. | Proactive planning plus reactive shielding is established prior work. My interpretation: invariance cannot automatically be claimed when the safety constraint is relaxed. Match dynamics, disturbance bounds, discretization and computation before comparison. |
| [GUARDIAN](https://arxiv.org/html/2602.06026v1), 5 February 2026 | Combines verified neural-estimator output bounds with HJ filtering. Its theorem requires bounded nominal estimation error, bounded observation attacks and assumptions enabling a common safe control direction over the uncertain state set. Examples include aircraft taxiing and decomposable motion models. | Input uncertainty is part of the control problem. Sentinel has not established these assumptions for its perception interface; neural verification alone does not bound unknown real-world estimator bias. |

Two further leads were screened at abstract level, not reproduced or fully audited:
[PMP boundary sampling](https://arxiv.org/abs/2604.13325v1) concentrates training near
constraint boundaries, and [Sim2Val](https://arxiv.org/abs/2506.20553v2) uses paired
cross-platform observations to improve metric estimation. They motivate selective data
acquisition and measured simulator fidelity; neither supplies those properties to Sentinel
merely by being cited.

The supplied GPT verdict also pointed to [HiDrive](https://arxiv.org/abs/2605.09972v1),
screened here at abstract level as a candidate harder benchmark. A benchmark's advertised
realism is not a substitute for validating the specific intervention and physical quantities
that Sentinel will measure.

There is also a useful methodological distinction in the newest scene-generation paper:
its finite escape search rejects scenes without a found qualifying trajectory as
unavoidable. For Sentinel, retain the stronger separation between **a checked witness,
a justified model-scoped exclusion, and a bounded search miss**. This is an opportunity for
measurement discipline, not evidence that Sentinel already outperforms that method.

## What the companies imply, and what they do not

NVIDIA's [Halos SAFE architecture](https://docs.nvidia.com/halos-safe/technical-brief/our-architecture)
already spans requirements, data curation, simulation, analysis and traceable safety evidence.
Its [credibility guidance](https://docs.nvidia.com/halos-safe/technical-brief/making-halos-safe-credible-and-auditable)
separates implementation verification from validation against physical reference data.
A general claim to be an evidence platform is therefore insufficient differentiation.
Its [introduction](https://docs.nvidia.com/halos-safe/technical-brief/introduction) explicitly
allows partner components, making a specialized analyzer a plausible integration hypothesis.

Mobileye describes hypothesis-driven failure mining and targeted synthetic variations through
[Meteor and Genario](https://www.mobileye.com/blog/diagnosing-the-long-tail-how-mobileye-turns-edge-cases-into-targeted-training/).
Its [scenario-boosting account](https://www.mobileye.com/opinion/driving-the-long-tail/)
focuses on reproducible scenario classes. Its
[long-tail mathematical discussion](https://www.mobileye.com/opinion/why-learning-from-data-gets-harder-in-the-tail/)
uses a particular simplified construction; it should not be treated as a universal impossibility
theorem for modern driving models. Sentinel should test a concrete failure distribution.

Waymo's [world-model article](https://waymo.com/blog/2026/02/the-waymo-world-model-a-new-frontier-for-autonomous-driving-simulation/)
describes controllable camera/lidar simulation and counterfactual driving. It reinforces the
need for realistic reactions and sensors; attractive generated scenes alone do not validate
a recovery label. [Foretellix's NVIDIA integration](https://www.foretellix.com/foretellix-foretify-physical-ai-toolchain-integrates-with-nvidia-drive-av/)
and [Applied Intuition's Dana announcement](https://www.appliedintuition.com/press-releases/applied-intuition-launches-dana)
show that validation tooling and agent-assisted workflows also have established competitors.
Their announcements are not independent demonstrations of claimed benefits.

The [Alpamayo 2 Super technical article](https://developer.nvidia.com/blog/generate-trajectories-reasoning-traces-and-auto-labels-with-nvidia-alpamayo-2-super)
and [AlpaGym announcement](https://nvidianews.nvidia.com/news/nvidia-alpamayo-2-super-robotaxis)
describe a larger planner, labeling and closed-loop learning ecosystem built around AlpaSim.
[OmniDreams](https://research.nvidia.com/publication/2026-06_nvidia-omnidreams-real-time-generative-world-model-closed-loop-autonomous)
adds action-conditioned sensor generation. These were reviewed as primary descriptions,
not reproduced software. [Waabi's research index](https://waabi.ai/research) also identifies
current traffic-modeling and sensor-simulation work; individual implementations were not
audited. Building a competing general world model is not the best next use of Sentinel's
present evidence or resources.

OpenAI's public [robotics safety role](https://openai.com/careers/lead-safety-engineer-robotics-san-francisco/)
names hazard analysis, safety cases and verification planning. That is evidence of a staffing
priority, not interest in Sentinel. SpaceX's
[May 2025 Falcon guide](https://www.spacex.com/assets/media/falcon-users-guide-2025-05-09.pdf)
describes mission-profile hardware-in-the-loop testing. NASA's
[runtime-assurance verification work](https://ntrs.nasa.gov/citations/20240007986)
connects switching conditions to sampling requirements while explicitly excluding many
industrial deployment difficulties. Driving evidence does not establish aerospace transfer.
NASA is a potential research or procurement context, not a corporate acquisition target.

This review has no comparable access to Tesla's or these companies' proprietary evaluation
stacks. It cannot rank Sentinel against them. Public [Tesla FSD documentation](https://www.tesla.com/support/fsd)
also makes the supervision scope explicit; that public product label is not a matched
technical comparator for Sentinel's simulator studies.

## The fundamental question to make operational

For the actual observation history, remaining control authority and deadline:

> Does an implementable intervention still exist, can the system identify it in time,
> and does it improve outcomes without unacceptable new harms or lost progress?

Four different explanations must remain separate: the world is unrecoverable under the
specified model; useful actions exist but the available observations cannot select them;
the search fails to find them within its budget; or a found action arrives too late.
One failed search cannot distinguish these explanations.

A proposed robust formulation is: find **one non-anticipating policy**, based only on available
observations, that satisfies specified safety and progress constraints for every state and
disturbance inside an explicitly justified uncertainty set. Proving that each hidden world
has its own different escape is weaker: the agent may not know which escape to choose.
This quantifier distinction is essential when converting privileged oracle results into a
usable monitor or recovery policy. It is a problem definition, not a new proven theorem.

Keep physical viability separate from an algorithm's achieved recovery coverage under a
compute budget. An empty bounded search result shrinks what that algorithm established;
it does not automatically shrink the physically viable set. Likewise, improving proposal
coverage does not establish the causal value of preserving discarded branches. A retention
claim needs its own comparison with matched proposals, budgets and information.

Deadline accounting must include sensing, estimation, inference, checking, communication and
actuation. Measure tails and what executes while a computation is pending. A 120-second
offline oracle can be useful for labeling; it cannot be represented as a 120-second runtime
intervention on a vehicle with a much shorter recoverable window.

Return three evidence types: **checked witness**, **model-scoped exclusion with a valid
bound**, or **unknown** with the exhausted budget and failed assumptions. Even a witness
certifies only the declared model and checks until sensor, dynamics and response uncertainty
have been included. Measure both false-safe conclusions and unnecessary intervention.

## Choice among the proposed research directions

These are qualitative judgments from the reviewed evidence, not measured commercial scores.

| Direction | Evidence and novelty burden | Practical cost and decision |
|---|---|---|
| A. Improve reactive shielding | Existing benchmark gain, frontal harms and transfer nulls; heavily studied prior art. | Necessary baseline and input-handling work; insufficient central differentiation alone. |
| B. Estimate recoverability online | Important question, but no qualified general recoverability labels or deployed margin yet. | Promising after actual-history witnesses, uncertainty bounds and timing qualification. |
| C. Retain and reuse discarded branches | Local evidence identifies missed opportunities; it does not isolate retention as the cause of improvement. | Compare retention on/off with matched proposals and accounting before choosing it as the thesis. |
| D. State-dependent recovery proposals | Iter191 directly supports this mechanism in its retained request population. The stopping controller is conventional. | Best immediate integration experiment; do not equate a useful connector repair with a new control theory. |
| E. Uncertainty-aware certificates | Strong long-term scientific question; current exact replay covers a declared discrete model. | High modeling and verification burden. Qualify assumptions before using certificate language beyond that model. |
| F. Planner-agnostic runtime supervisor | Broad product hypothesis; transfer, observation interfaces and deadlines are unresolved. | Defer general runtime claims until at least two planners and distinct scenarios qualify. |
| G. Offline recovery qualification instrument | Best fit to existing replay, diagnostics, bounded search and explicit-unknown assets. | Highest near-term expected research value in this review; requires a blind benchmark and a useful customer workflow. |

Select D for the immediate controlled experiment, G as the first product hypothesis, and B/E
as conditional research extensions. C remains a falsifiable mechanism question. This ordering
preserves the mission while avoiding a premature rewrite or a claim that all seven directions
have already been validated.

## The next sequence, with decisions that can stop unproductive work

1. **Close the current engineering question.** Preregister one all-four integrated trial of
   the exact Iter191 proposal, with the existing 18,000-transition / 120-second case limits
   and unchanged sampling, metric and allocation. Retain comparisons against Iter189 and
   Iter183, all losses and costs. Four successes would close a development gate, not establish
   state of the art. If it fails, allow a bounded diagnostic accounting; do not make endless
   four-case optimization the main research program.
2. **Return to actual intervention histories.** In a new protocol, preserve the complete
   history and absolute clock at first fire. Compare a small diverse feedback library with
   the existing search and responsive baseline. Construct recovery-versus-start-time and
   imposed-delay maps. Preserve unknowns; check any witness in the native execution semantics.
   If useful recovery is not demonstrated, resolve action/model capability before training
   another detector or claiming information value.
3. **Make information usable.** Compare decoded observations, planner tokens and, only when
   justified, independent measurements under matched action sets and charged computation.
   Include stale, missing and contradictory observations, common perception misses, actuator
   limits and uncertain hazard clearance. Separate representational/computational value from
   genuinely additional information. Do not move an oracle's future schedule into the runtime
   inputs.
4. **Run one locked comparative study.** Keep the four development cases and previously
   exposed scenes outside confirmatory holdouts. Split by scene/family, not adjacent frames
   or duplicate seeds. Use a current released planner such as SparseDrive or DiffusionDrive
   alongside the existing baseline, then a second simulator for transfer. Compare suitable
   implementations of TTC/RSS-style control, RiskMonitor, a feedback-policy library and a
   predictive safety filter. Match available inputs, dynamics and budgets; label adaptations
   honestly rather than claiming to reproduce a paper that has not been reproduced.
5. **Choose the product from the evidence.** If offline recovery labels improve held-out
   training or validation efficiency, develop that analyzer and its adapters. If a runtime
   policy additionally meets deadline and robustness requirements, pursue that separately.
   If neither beats a strong simple baseline, narrow the scope or stop that implementation
   direction. Evidence must be allowed to change the plan.

Before collecting confirmatory outcomes, fix the independent sampling unit, minimum useful
effect, uncertainty analysis, harm/progress constraints, worst-group rules, missingness,
compute ceilings and stop rules. Power the study around independent scene families and
paired outcomes. Report severity, collision rates, progress and intervention burden together.
Conditioning all results on oracle-recoverable cases would hide coverage and selection costs;
report the complete eligible population as well as that conditional slice.

The most promising later acceleration is to learn from checked boundary cases and amortize
expensive recovery reasoning into a fast proposal or margin predictor, retaining an independent
checker and explicit abstention. First establish that the labels and interventions are useful.
Changing the representation, planner, action library and allocation simultaneously would make
the next result difficult to explain.

## Commercial judgment

A valuable business is plausible in this problem area; a billion-dollar Sentinel valuation
is **not supported by the evidence reviewed**. No named organization's acquisition interest,
customer willingness to pay, repeatable revenue, integration economics or exclusive technical
advantage has been established here. Public attention does not substitute for those measures.
No claim is made about private conversations or business evidence outside the reviewed material.

The first prospective buyer should be a team with a concrete evaluation bottleneck, a usable
interface and a measurable cost of missed failures or expensive validation. A paid pilot would
need to show, on the buyer's withheld cases, either better valid recovery coverage at fixed
cost or lower evaluation cost at fixed error and coverage. Measure engineer time, compute,
integration effort and repeat usage alongside technical outcomes.

Potential defensibility would come from hard-to-reproduce validated data, efficient algorithms,
trusted adapters and repeated customer results. The inspected root license is Apache-2.0;
public code volume alone should not be presumed exclusive. Dataset, model and third-party
rights would require a separate commercial review, not an assumption that a root license
covers every artifact. No licensing conclusion is made here.

I cannot know what Musk, Altman or an unconsulted engineering team would privately choose.
The rigorous decision is to name the bottleneck, beat the strongest applicable baseline,
measure the improvement independently, and stop or redirect work that fails its declared bar.
That is the standard this proposed next sequence is designed to meet.

## Retained audit and limits

The new probe is diagnostic evidence only. It ran with Python 3.14.2 and NumPy 2.4.2 against
legacy source SHA-256 `d0338d5cee088d2271ee886b86ccac6f03775bf94991b4128013015159b91189`.
The first interpreter import checks found NumPy absent in default Python and the worktree
virtual environment; the existing scientific Python 3.14 environment succeeded. No packages
were installed. The probe uses temporary local logs and executes no server installer.

Historical experiment files, the canonical dirty checkout, integrated credit and scientific
mission state remain unchanged. This document does not authorize a claim of superiority,
amend a frozen experiment, or turn the proposed sequence into an executed result.
