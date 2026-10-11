# Sentinel engineering and research assessment — 11 October 2026

**Judgment: continue the recovery-first research direction. Sentinel has not established
state-of-the-art superiority, useful recovery advantage, real-time operation or industrial
readiness.** The direction is justified because it tests whether an effective action exists
before spending on a detector intended to select it. This is an engineering assessment by the
agent, not independent institutional review. No claim is made about private SpaceX, Tesla or
Mobileye decisions or endorsement.

The review covered the current handoff, controlling continuity entries, historical mission
state, README, architecture, information/recoverability direction, Iter147–148 protocols,
results, accounting, actual pair launcher and failed observation supervisor. It is not a
claim to have audited every historical source file or mastered every component.

## What deserves confidence

The research distinguishes score, collision, progress, attribution, transfer and useful
recovery. The +0.783 NeuroNCAP score contrast is reported alongside increased frontal
collisions and an inconclusive progress contrast. Placebo attribution and HUGSIM transfer
nulls remain visible. Raw-before-replay commits, replica checks, complete-prefix checking
and explicit missingness make the results inspectable. Those practices are worth preserving.

The main scientific idea is consequential: demonstrate which extra signal changes a timely,
effective decision at an acceptable intervention and computation cost. A better classifier
alone cannot establish this. A representation computed from the same observations may offer
useful computation without supplying new Shannon information.

## Where the program falls short

1. **No current recovery comparison.** Iter148 admitted four easy-case baseline episodes,
   with no dynamic actors, no monitor activation and no complete four-arm comparison.
2. **Fragile orchestration.** The actual supervisor asserted on the first failed IAP query.
   Observation loss and worker failure are different states; their consequences must differ.
3. **Timing is a substantive negative.** Every verified Iter148 loop missed 250 ms, with
   median 1.792 s. Synchronous simulation results do not establish an operational 4 Hz system.
   A future real-time claim requires a stated late-result policy and deadline fault tests.
4. **Weak external-validity basis.** The development library contains three exposed scenes
   and no untouched holdout. Two replicas test agreement, not independent scene diversity.
5. **Common information failures remain.** The monitor shares decoded objects with the
   planner. It has no demonstrated independent perception or hidden-representation advantage.
6. **Integration debt remains.** The historical mission contract describes Iter134/135 while
   current research is later; hosted CI had 688 Ruff findings and skipped subsequent tests.
   A local component pass does not repair that whole-repository condition.

## Public comparison and standards checked

Sources were consulted on 11 October 2026; this is a targeted positioning review, not an
exhaustive survey or a benchmark ranking.

- [RiskMonitor, v2, 8 February 2026](https://arxiv.org/abs/2503.07425v2) already studies token-based
  risk estimation and braking with a frozen planner in NeuroNCAP. Token monitoring alone is
  therefore insufficient novelty. Its numerical results are not a matched Sentinel comparison.
- [Argus, v1, 12 November 2025](https://arxiv.org/abs/2511.09032v1) studies runtime hazard
  monitoring and mitigation across TCP, UniAD and VAD. Multi-planner takeover is also adjacent work.
- [Waymo collision-avoidance testing](https://www.waymo.com/research/collision-avoidance-testing-of-the-waymo-automated/)
  supports using specified conflict scenarios and evasive-response evaluation. It does not
  validate Sentinel's simulator fidelity or population coverage.
- [Mobileye RSS](https://www.mobileye.com/technology/responsibility-sensitive-safety/) provides
  a public formal behavioral-safety reference. A geometric TTC trigger is not an RSS compliance
  argument. Model assumptions and sensing/control validity must remain explicit.
- [NASA independent test capability](https://www.nasa.gov/enabling-technology/) describes
  repeatable execution and fault injection. That supports the engineering choice to test
  disconnections and deadlines before another scientific run, not a spaceflight qualification.
- [ISO 21448:2022, edition 1, June 2022](https://www.iso.org/standard/77490.html) addresses intended
  functionality insufficiencies. The official page identifies revision work underway. Only
  public scope/version information was checked; no clause audit or compliance claim is made.
- [ISO 34502:2022, edition 1, November 2022](https://www.iso.org/standard/78951.html) describes a
  scenario-based ADS safety-evaluation framework for limited-access highways. That scope must
  not be generalized to every Sentinel scene; its public abstract is not the full standard.

## Highest-value sequence

Qualify the observed coordinator failure locally, then bind and qualify the actual cloud
adapter in a small non-scientific envelope. An adapter is still necessary: the new local
fixture is not a drop-in replacement for the closed Iter148 scripts. Keep their source frozen.

Then run a prospectively registered development canary on a known collision opportunity and
a benign candidate, with nominal, responsive-monitor and two fixed pulse arms. The
[proposal](NEXT_STUDY_PROPOSAL.md) explicitly replaces no missing Iter148 outcome. It reduces
the initial question to whether this finite action library can supply a useful recovery.
Only a successful witness justifies the next information ablation; follow that with genuinely
new-scene evaluation and appropriate learned/responsive comparators.

Do not turn infrastructure qualification into an open-ended program. The stopping condition
for this repair is specified behavior under the registered faults. The next scientific output
should be a falsifiable action/information result. Industrial value remains to be demonstrated
with a useful result, reproducible integration and an actual external user's requirements.
