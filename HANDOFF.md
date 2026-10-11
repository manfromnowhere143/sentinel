# Sentinel — next-session handoff

Updated 11 October 2026. **Start here.** Iter148 is closed and inconclusive. The README,
architecture and diagram review is complete. The next engineering task is to qualify recovery
from unavailable progress observations before proposing another live scientific comparison.
No driving job is running under this session's ownership; both owned VM starts have retained
termination receipts. Verify current provider state before any future provider action.

## Mission and standard

Build a monitor and evaluation system that can demonstrate which failures remain preventable,
which information changes an effective control decision, and the resulting cost to progress,
intervention burden and computation. The ambition is a result that another serious engineering
team can inspect, reproduce and use to make a better decision about its own system.

The scientific question after Iter135 is:

> What additional information allows a responsive monitor to prevent failures that a strong
> responsive baseline misses, while an effective intervention is still available and useful
> progress is preserved?

A better collision predictor, a higher composite score, a converged solver and a useful recovery
are separate results. Test the weakest link first. When an experiment fails, retain the raw
failure, isolate its cause, construct a counterexample, and test a bounded correction. Do not
reward persistence with a favourable interpretation of missing or adverse evidence.

Keep the ambition high and the claims specific. A state-of-the-art, physical-safety, industrial
superiority, commercial-value or new-theorem claim needs its own comparator, scope and evidence.
No endorsement by a university or industrial team has been established. Daniel's writing voice
is precise, confident, dignified and candid; use concrete findings and clear uncertainties.

## Recover the repository before changing it

Canonical root: `/Users/danielwahnich/workspace/sentinel`.
Remote: `https://github.com/manfromnowhere143/sentinel.git`.

```bash
pwd
git rev-parse --show-toplevel
git remote get-url origin
git status --short --branch
git rev-parse research/iter148-recovery-study
```

Run these from the canonical root. Confirm the named project, directory, Git identity and
AGENTS.md agree.

Read, in order:

1. [AGENTS.md](AGENTS.md) and this handoff.
2. [Iter148 result](experiments/iter148_recovery_study/RESULT.md),
   [state](experiments/iter148_recovery_study/STATE.json) and
   [decision](experiments/iter148_recovery_study/DECISION.md).
3. [README](README.md) and [architecture](docs/ARCHITECTURE.md).
4. [Research direction](docs/research/SENTINEL_INFORMATION_AND_RECOVERABILITY_RESEARCH_DIRECTION_2026-10-09.md),
   particularly the distinction between information, useful computation and recoverability.
5. The top and final sections of [CONTINUITY.md](CONTINUITY.md). Consult older entries only
   for the specific question at hand.

The root remains a dirty `wip-gen17-ci-hardening` checkout. It contains unrelated preserved work.
The current research lineage is `research/iter148-recovery-study`, descended from master without
rewriting its accepted commits. The prior editorial checkpoint is
`cc0db9f0fd427f6d70a5bad7ff085481fcc1c264`; later handoff/publication commits follow it.
Use an isolated Git index or an owned checkout for candidate work. Never reset, clean, stash,
checkout over, or bulk-stage the root's unrelated changes. Preserve Daniel's configured author
and committer identity; do not add model co-author or generated-by trailers.

The root README has an immutable file flag and a deny-delete ACL. Its authorized editorial
update preserved old bytes and restored both protections. Read its protection state before a
future edit, preserve a prior copy, and restore protections afterwards. This is a mechanical
operation the agent can perform; it is not a reason to require a human ceremony.

## What the evidence establishes

| Scope | Finding | Limit that must travel with it |
|---|---|---|
| NeuroNCAP power run | Score 2.12 → 2.91; +0.783 [95% CI +0.605, +0.928]. | 799/800 episodes; registered run-index bootstrap. Frontal collisions increased; safe-progress −0.032 [−0.127, +0.065]. |
| Iter134 placebo test | Gain over OFF reproduced. | Primary union–placebo interval includes zero; placebo realized 859/1,205 scheduled brake frames. Semantic attribution remains unresolved. |
| HUGSIM transfer | Easy/medium and hard/extreme tests returned TRANSFER_NULL. | Neither equivalence nor universal failure follows; do not erase the nulls. |
| Earlier recoverability | Iter139 0/6 and Iter142 0/2 useful recoveries. | Finite tested libraries and cases; no global unavoidability theorem. |
| Current monitor | Decoded objects, track IDs, pose and planned path drive geometric CPA/TTC conditions. | Hidden-representation benefit and independent perception are unestablished. |
| Current execution | Explicit trajectory times, coordinate conventions, projected controls and independent replay. | This new regime changes more than the monitor; do not pool it with the old HUGSIM transfer data. |

Iter135 is **deferred and unrun**. It is not the current execution program. A new representation
or another dose experiment should earn compute through a specific falsifiable question; the
immediate scientific priority is a constructive recovery opportunity against responsive baselines.

## Iter148: exact accounting

The fixed development library has 14 scenarios from three previously exposed source scenes,
four arms and two replicas: 112 slots. It has zero untouched holdouts. Replicas establish
agreement; they do not create new independent scenes.

- Nominal: two admitted replicas, 92 actions each, source-defined completion.
- Responsive monitor: two admitted replicas, 92 actions each, completion, zero activation.
- Pulse at 0 s: first replica recorded 88 actions without a terminal summary; paired admission
  is invalid. The second replica was never initialized.
- Pulse at 2.5 s: neither replica initialized.

Totals: **4 admitted, 1 incomplete, 107 uninitialized; 368 verified actions; no complete
four-arm comparison. Recovery and harm rates are unestimated.** The easy case had no configured
dynamic actors. Its completion follows the simulator's rule near 90% of sampled route points,
not the literal final sample. Nominal already succeeded, so this is not a recovery gain.
Natural monitor release was not observed in these admitted runs.

The largest checked stationarity residual is 9.759011668497575e-7 against a 1e-6 bar.
**6/368 controller calls exceeded 50 ms; all 368 loops exceeded 250 ms.** Loop median was
1.792 s. The simulator waits synchronously. There is no demonstrated 4 Hz operation or
late-result policy. Incomplete pulse timing and terminal outcomes remain incomplete.

The immediate cause of stopping was an IAP connection failure during a read-only progress
query. The frozen coordinator treated observation failure as a stop condition. A later query
found the worker still running before shutdown. This is evidence of a coordinator limitation;
it does not establish a simulator fault or a cloud-wide outage.

## Exact next task and completion criteria

**Next task: design and qualify bounded observation recovery.** Do not restart Iter148 or
begin a new scientific run merely because this handoff exists.

1. Read the retained failure and supervisor response:
   [transport error](experiments/iter148_recovery_study/proof/block_000_attempt_002/gpu_progress_auto_002_002.stderr),
   [supervisor result](experiments/iter148_recovery_study/proof/block_000_attempt_002/supervisor_result.json),
   [supervisor source](experiments/iter148_recovery_study/proof/session_tools/i148a_supervise.py).
   Inspect those scripts as evidence; they contain closed paths and must not be rerun.
2. Write a prospective protocol for a new control qualification. Define observation-unavailable,
   worker-running, worker-failed, worker-complete, partial-evidence and identity-mismatch states.
   Define the evidence required for each transition. Do not infer worker failure from one
   transport error, or infer success from a missing process or empty reply.
3. Bind every observation to the same VM identity and start timestamp, source identity, plan,
   pair and durable initialization marker. Observation retries must be read-only. Use a fixed
   retry count, monotonic deadline and bounded backoff inside the existing total budget.
4. Keep a host deadline independent of the observer and an ownership-checked shutdown path.
   Successful reconnection cannot extend the deadline, spending bound or scientific retry rule.
   Reconcile durable completion evidence before deciding what the next permitted action is.
5. Qualify with deterministic fault injection before any GPU: delayed response, temporary
   disconnection, permanent disconnection, duplicated reply, stale reply, wrong VM start,
   malformed reply, partial writes, worker crash, completion during disconnection and budget
   exhaustion. Retain a known-bad for every new rejection or stop condition.
6. Have a separate replay/checker reconstruct the transition trace. Acceptance requires correct
   distinctions, no duplicate initialization or execution, bounded resource use, preserved
   partial evidence, and verified termination of owned work when the bound is reached.
7. Record pass, failure or inconclusive evidence literally. Only then propose a fresh scientific
   continuation protocol accounting for the interrupted study and its observed data. Preserve
   the original population, missingness and estimands unless a visible prospective amendment
   explicitly supersedes them. Never silently retry an initialized Iter148 slot.

The following scientific step is a finite recovery comparison, followed by one motivated
information ablation against a competent responsive baseline. Keep action library, timing,
progress constraints and observation interfaces explicit. If a successful intervention exists,
then ask whether an added signal helps select it in time. If none is found, state the tested
library and horizon; reconsider the action or case family before fitting another detector.
Hold out genuinely new source scenes before a generalization claim.

## Resource closure and commands that must stay closed

Owned VM: `sentinel-gpu`, ID `3834622546652649531`, project `sunlit-unison-487018-b0`,
zone `us-west1-a`, one L4. Retained observation at closure:

| Envelope | Owned start | Verified stop | State |
|---|---|---|---|
| Main study attempt | 2026-10-10T22:05:46.919-07:00 | 2026-10-10T22:29:54.495-07:00 | TERMINATED |
| Evidence recovery only | 2026-10-10T22:31:47.574-07:00 | 2026-10-10T22:38:08.936-07:00 | TERMINATED |

All local supervisors/watchdogs exited. The second envelope restarted no driving worker.
Postflight checked 6,101 bound/original files and 20 actor aliases unchanged.
The combined conservative compute estimate was $1.659 against the original $9 cap; this is
not an invoice and excludes persistent storage and taxes. See
[resource closure](experiments/iter148_recovery_study/proof/block_000_attempt_002/combined_resource_closure.json)
and [final postflight](experiments/iter148_recovery_study/proof/block_000_forensic/gpu_postflight_integrity_report.json).

The host path `/datasets/nuscenes-full/hugsim/iter148_study_20261011` contains initialized work.
Do not erase its markers or reuse its output paths, budgets or timer identities. Retained
`i148a_*` and `i148f_*` helpers embed that closed state. Future access begins with read-only
identity and lifecycle verification and a fresh bounded envelope appropriate to the new task.
No new cloud compute was used for the README/handoff work.

## Evidence and verification entrypoints

Frozen scientific source: `dd45ad39b26602ad81626ca55332e7ce6d308e91`.
Raw committed before replay: nominal `ad1066ea9e5fdbd795a7f2fa43c3f63a6cac1058`,
monitor `c94c47c7bdbfad77250b7807cc5fa478b2c4de5f`, partial pulse
`841ba8d4dcec4b5cded70783c7494345b4a835f5`.
Scientific closure and preservation: `3e79f028abd63c365e0b23e3f9a388c238c8498f`.

- [165 focused tests](experiments/iter148_recovery_study/proof/commands/final_local_tests.json)
  passed before live execution, with 40 retained upstream warnings. Scientific source has not
  changed since. The exact command is recorded; inspect its environment before repeating it.
- [Qualification](experiments/iter148_recovery_study/QUALIFICATION.json) replayed 1,104 prior GPU
  actions. Numerical replica and prefix checks do not prove physical fidelity.
- [Editorial audit](docs/editorial/2026-10-11/validation.json) checked all 148 result links,
  250 current relative links/anchors, five diagrams in two themes, and evidence preservation.
  That is a dated check of the prior editorial commit, not an automatically current receipt.
- [Publication review](docs/publication/2026-10-11/REVIEW.md) records this handoff/publication task
  and the remaining repository-level validation limits.

For an actual controller change, the previously used focused command was:

```bash
python3 -m pytest -q tests/test_iter146_route_outcome_contract.py \
  tests/test_iter147_full_horizon_execution.py tests/test_iter148_recovery_study.py
```

Use the exact applicable environment, add meaningful fault checks for the new change, and retain
both failure streams and scope. Do not run live helpers as a shortcut to reconstructing state.

## Publication boundary and historical mission state

Research branch: [research/iter148-recovery-study](https://github.com/manfromnowhere143/sentinel/tree/research/iter148-recovery-study).
This branch carries the updated README and complete retained research lineage. Publishing it
makes the work inspectable; it does not establish scientific correctness or promote it to master.
The accepted master snapshot remains `8c118b74c699bf0f139f9bd659192bad06b895f8`.

### Canonical mission state (`MISSION_STATE.json`)

The historical contract records **iteration 134 / PLACEBO_HARM_OR_NULL**, with
**iteration 135 / CI_HARDENING_REQUIRED**. It remains byte-identical. Iter135 is deferred;
its old phase does not describe the current research task. The legacy documentation guard
expects the largest RESULT directory to equal 134 and the checkout to be the exact F17 source
commit. Those assumptions are incompatible with this later research branch. Its findings remain
visible; do not relabel them as green, rewrite accepted history, or consume research-branch
publication as an Iter135 launch or tooling-receipt acceptance.

`HANDOFF.md` is now this maintained operational brief, under Daniel's explicit request.
`scripts/make_handoff.py` remains the frozen historical snapshot renderer for the Iter135
contract. Its output must not replace this handoff. The prior root and candidate handoffs are
archived under [docs/history](docs/history). Historical generator tests concern that renderer;
they do not validate this current operational brief.

## Operator authority and completion discipline

Daniel authorizes autonomous work within the requested mission, including relevant local,
provider, validation and publication steps. No independent human reviewer, hand-authored
acceptance file or repeated permission ceremony is required. Keep actual provenance: automated
checks and agent review are not independent human review or external endorsement.

Finish the bounded task before starting another. Keep source, evidence, interpretation and
current handoff consistent; preserve adverse results and unknowns. Use separate implementations
and constructed corruptions where they test a real risk. Spend compute to distinguish hypotheses,
not to manufacture activity. Tell Daniel when a result changes the scientific conclusion, and
state precisely what remains unproven.
