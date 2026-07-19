# HANDOFF — retained mission snapshot

Generation-fifteen control-integrity recovery is in source validation on 2026-07-19.
Read `CONTINUITY.md` first. This file is a repository snapshot, not live host authority.

## Repository and publication state

```text
canonical branch       master
accepted baton         B14 69bd2e2face00ccabb426382347eb04e8a0dbe83
remote master          B14 at this source snapshot
superseded candidate   failed F15 4d8801605f1e285c5000b4220e965e97a8aff345
replacement F15        the commit containing this snapshot; acceptance requires exact external evidence
run state              UNKNOWN
iteration-135 phase    PREREGISTERED_TOOLING_REQUIRED
host mutation          forbidden
H/E/P/S descendants    forbidden
```

Generation fourteen published as F14 `4a62cc4` → R14 `b260ca5` → T14 `a084198` → B14
`69bd2e2`. The later attempt-eleven H commit `4bd0a23` briefly reached `master` before its
checks completed. Master run 774 (`29653147271`) failed, retained evidence-branch run 775
(`29653375226`) also failed in both matrix jobs, and restore run 776 returned B14 to a green
`master`. The H evidence remains on `evidence/stage0-h11-b14`. The interval was a
publication-discipline failure and never became stage authority.

The first unpublished F15 source candidate, `619083e`, passed its local suite but failed
disposable Actions run 777 (`29680678241`): Python 3.11 was green and Python 3.10 had two
synthetic-Git exit-128 failures. Its helper discarded stderr, so the operating-system mechanism
cannot be recovered from that run. It was not rerun or promoted.

The second candidate, `4d88016`, passed both lanes in disposable run 778
(`29681850274`) and then reached `master`. Distinct master run 779 (`29682001941`) failed:
Python 3.10 was green; Python 3.11 reported one failed test and 1,404 passes. Retained stderr
showed a missing reachable parent object in a synthetic repository. At failure observation the
runner reported `82,920,296,448` free bytes and `18,439,733` free inodes. This excludes only
contemporaneous filesystem-wide free-block and free-inode exhaustion on the probed mount; it
does not exclude quotas, earlier transient depletion, overlay or reservation behavior, or
writeback failure. `master` was restored with an exact lease to B14. Restore run 780
(`29682216942`) passed both lanes. Run 779 was not rerun, and `4d88016` is not accepted.
The exact failed candidate is retained on `ci-validate-f15`.

## Current-status correction

The current-status sentences in `README.md` and `docs/NEXT_PHASE.md` that say no run is in
flight are retracted as lifecycle claims. They are frozen generation-one source bytes, not
current execution evidence. The only supported lifecycle value is `UNKNOWN`; neither completed
iteration-134 evidence nor absent containers or processes proves termination of every possible
iteration-135 producer. The first separately registered documentation-source generation after
the atomic F15/R15/T15/B15 control publication must correct those two files before any host,
GPU, H/E/P/S, smoke, or analytic work can be considered.

The broad `docs/REPORT.md` statement that the public state of the art is failing is also
quarantined as unsupported positioning shorthand. It licenses no Sentinel state-of-the-art
claim. The same documentation generation must either replace it with a named benchmark,
comparator, scope, evidence date, and retained sources or remove it.

## Replacement F15 contract

F15 is a source-only child of B14 with exactly these nineteen paths:

1. `CONTINUITY.md`
2. `HANDOFF.md`
3. `MISSION_STATE.json`
4. `experiments/iter135_neuroncap_blind_braking_dose_response/authorize_launch135.py`
5. `experiments/iter135_neuroncap_blind_braking_dose_response/capture_environment135.py`
6. `experiments/iter135_neuroncap_blind_braking_dose_response/prepare_host135.py`
7. `experiments/iter135_neuroncap_blind_braking_dose_response/run_dose135.sh`
8. `experiments/iter135_neuroncap_blind_braking_dose_response/run_smoke135.sh`
9. `experiments/iter135_neuroncap_blind_braking_dose_response/verify_tooling135.py`
10. `scripts/make_handoff.py`
11. `scripts/mission_state.py`
12. `tests/test_handoff_generator.py`
13. `tests/test_iter135_environment_capture.py`
14. `tests/test_iter135_host_preparation.py`
15. `tests/test_iter135_launch_authorization.py`
16. `tests/test_iter135_launcher.py`
17. `tests/test_iter135_smoke_pipeline.py`
18. `tests/test_iter135_tooling_verifier.py`
19. `tests/test_mission_state.py`

Its exact reason code is:

```text
B14_H_DESCENDANT_CONTROLLER_OMISSION_GITHUB_RUN_AUTHORITY_AND_CI_FIXTURE_OBJECT_CONNECTIVITY_AND_RECEIPT_SCHEMA_EXACTNESS_AND_FALSE_IDLE_LEGACY_HANDOFF_REMOTE_PROBE_AND_RECEIPT_FAILURE_BOUNDARY_STOP
```

The recovery changes no hypothesis, schedule, estimand, verdict rule, intervention, simulator,
monitor, braking policy, smoke payload, or analytic payload. It repairs:

- canonical GitHub authority selection by exact workflow, branch, head SHA, newest
  `run_number`, exact `run_attempt`, and exact two-job matrix;
- replay of the selected workflow row and branch observation to reject concurrent reruns;
- exact positive-integer GitHub identities, rejecting booleans and numerically equal floats;
- generation-fourteen/fifteen frozen-controller coverage;
- nested receipt shapes, boolean/float zero impostors, stream bindings, canonical UTC ordering,
  and compatibility of the retained R14 receipt with the stricter nested-shape validator;
- synthetic-Git command diagnostics, fixed environment, SHA-1/empty-template initialization,
  rename-based object publication, committed-object/reference fsync settings, disabled automatic
  maintenance, strict reachable-object connectivity checks, bounded diagnostics, and teardown
  that attempts every safe repository cleanup before raising;
- the false static `IDLE` claim, the legacy live handoff probe, and every live action during the
  control freeze;
- receipt failure boundaries so admitted H/E attempts retain red evidence instead of escaping or
  overwriting an earlier attempt.

These controls establish neither whole-object integrity nor a proven filesystem root cause.
They also do not make hosted CI hermetic.

## Pre-publication findings closed in the replacement

Adversarial review rejected several working snapshots even after focused or full tests passed.
Those passes are diagnostic only because later bytes changed.

- Host preparation originally inspected preserved B14 paths before authenticating packet state
  and could write a red H receipt during a control stop. It now authenticates the complete packet,
  invoked controller, and manifest-bound mission state before host, clock, environment,
  forbidden-path, GitHub, runtime, mutation, or receipt work. Control, preregistered, unknown,
  malformed, unbound, and out-of-scope packets are non-performing stops.
- The active baton required the legacy handoff generator and a binary `IDLE`/`IN FLIGHT`
  statement. F15 replaces that probe with a deterministic offline tombstone that grants no
  authority and rejects malformed, future, or authority-bearing state until a source-bound
  lifecycle observer is accepted.
- The exact T15/B15 pair initially required `origin/master == B15`, making disposable validation
  impossible. The repaired contract accepts `origin/master == R15` only as
  `non-authoritative-control-candidate`, and exact `origin/master == B15` only as
  `origin-published-control-baton`. Both retain `authority=none` and
  `launch_authorized=false`; every other upstream fails.
- Post-admission clock or hostname faults could escape without the promised durable red H
  receipt. Red receipts now preserve unobserved metadata as JSON null, append stable problems,
  and remain durable at the packet or installed destination. Null attempt metadata is forbidden
  in a green receipt.
- H receipt publication now begins with a durable nonauthority marker, commits the pending and
  canonical names as one exact hard-link pair, and consumes a process-local completion witness
  before returning. Deterministic failures cover attempt and pending writes, every receipt file
  and parent sync boundary, marker restoration, recovery, and completion. All six numeric
  `HostConfig` fields require exact positive integers before packet observation or attempt
  creation; booleans, integral floats, zero, and negative values fail before an H attempt.
- Environment capture no longer samples time before the packet-bound control stop. Its admitted
  H evidence, dataset identity, and storage-device links use recursive exact JSON equality;
  booleans, integral floats, and negative device identifiers fail closed.
- The launch controller and smoke preflight now preserve recursive JSON type identity across H,
  E, manifest, sidecar, and remote-artifact links. Bound H, tooling, and schedule documents reject
  duplicate keys and non-finite numbers, and the exact byte buffer used for decoding is also the
  buffer checked against source path, SHA-256, and byte count. The smoke target selector validates
  exact run, frame, donor, count, range, and zero-problem metadata with retained known-bad
  fixtures; it cannot select a numerically equal Boolean or float.
- Mission-state validation now models launch-controller results with exact phase- and
  candidate-specific field sets. A local candidate must return an exact Boolean
  `candidate_valid` consistent with its problem set, nonauthoritative authority, and
  `launch_authorized=false`; numeric aliases fail closed.

During this working session, a shell search pattern accidentally executed the legacy handoff
generator and overwrote this file with its stale false-`IDLE` output. The probe reached
`sentinel-gpu`; its command created or truncated and then removed
`/tmp/sentinel_handoff_docker_ps.txt`. That temporary remote-filesystem mutation was not
authorized by the active freeze. The generated local bytes were discarded before staging. No
retained install, evidence-path, container, or GPU mutation was observed, and no Git ref or
GitHub resource changed. No follow-up host probe was performed, and the output does not establish
`IDLE`. This snapshot was reconstructed from B14, retained Actions evidence, `CONTINUITY.md`,
and `MISSION_STATE.json`. F15 turns the legacy generator into an offline-only tombstone and
retains known-bads against its former live behavior.

## Canonical mission state (`MISSION_STATE.json`)

- Current: iteration 134 / PLACEBO_HARM_OR_NULL / run UNKNOWN / next
  iteration 135 / PREREGISTERED_TOOLING_REQUIRED
- Canonical completed experiment: experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md
- Next program: semantics-free placebo dose-response causal closure
- Canonical next action: iteration 135 / PREREGISTERED_TOOLING_REQUIRED / semantics-free
  placebo dose-response causal closure.
- Authorized now:
  - perform only offline, repository-local, preregistered architecture, lifecycle,
    terminal-proof, CI, supply-chain, test, and publication-control work;
  - retain and review evidence for the later control-hardening publication without changing
    external governance settings.
- Forbidden now:
  - de-prepare, rebuild, normalize, clean, install, write, delete, or otherwise mutate any
    iteration-135 remote host, remote filesystem, host-side repository, packet, runtime, lock,
    container, GPU, or evidence path before lifecycle and hermetic CI controls are separately
    accepted;
  - create, execute, publish, or advance any H, E, P, or S descendant; launch activation; live
    smoke; or analytic episode before lifecycle and hermetic CI controls are separately accepted;
  - infer `IDLE`, termination, completion, readiness, approval, or authority from static state,
    absent containers, absent processes, missing reviewers, timeouts, retry exhaustion, or
    incomplete proof;
  - run analyzers or publish iteration-135 data, results, claims, figures, paper text, or
    scientific conclusions;
  - change branch protection, rulesets, Actions policy, repository visibility, credentials,
    secrets, access control, or other external governance settings without explicit operator
    authorization;
  - rerun iteration 134;
  - adopt run-index resampling as the iteration-135 primary after observing iteration-134
    results.

## Publication sequence

1. Freeze a clean replacement F15 whose parent is exact B14 and whose changed paths are the
   registered nineteen.
2. Require complete local validation in Python 3.10 and 3.11.
3. Push the exact F15 SHA to two fresh disposable branches. Preserve every red run; do not use a
   rerun to erase it.
4. Only after both disposable runs are green, normally push the same SHA to `master` and require
   a distinct green master run.
5. Generate R15 from the exact accepted F15, independently replay it, publish it through
   disposable and distinct master runs, and preserve the protected receipt controls.
6. Construct T15 as the state-only `CONTROL_HARDENING_REQUIRED`/`UNKNOWN` child of R15 and B15 as
   its immediately following documentation-only baton.
7. Validate exact B15 on a disposable branch with `origin/master == R15`; this is explicitly
   non-authoritative. Then normally publish exact B15 and require a distinct master run with
   `origin/master == B15`.

T15 is never published alone. F15, R15, T15, and B15 authorize no host access, H/E/P/S,
activation, smoke, analytics, or scientific claim.

## Retained host snapshot

```text
GPU_RUN_STATE=OBSERVATION_UNAVAILABLE_BLOCKED_STATIC_SNAPSHOT_ONLY_2026-07-19
HOST_INSTALL=B14_ATTEMPT_11_GREEN_PRESERVE
CONTAINERS=NONE_AT_LAST_NONAUTHORITATIVE_PROBE
SMOKE_OR_ANALYTIC_LOCKS=NONE_AT_LAST_NONAUTHORITATIVE_PROBE
ANALYTIC_ROOT=EXISTS_EMPTY_AT_LAST_NONAUTHORITATIVE_PROBE
```

This is not a fresh runtime observation. Container absence cannot prove `IDLE`: the frozen dose
runner removes containers between blocks while its process and irreversible lock may remain.
Do not redirect `scripts/make_handoff.py` onto this retained file or treat its offline output as
authority. Do not probe, relaunch, clean, or mutate the host during this control freeze.

## Scientific and paper status

- NeuroNCAP union gain: `ESTABLISHED_ON_NEURONCAP`
- Semantic attribution: `UNRESOLVED`
- HUGSIM transfer: `TRANSFER_NULL`
- Production readiness: `NOT_ESTABLISHED`
- Paper: `ARCHIVED_NOT_SUBMISSION_READY`

The paper must not claim state of the art, deployment readiness, formal guarantees, universal
decoder effects, semantic causation, or cross-simulator benefit without the named comparator,
scope, date, and retained evidence. Iteration 135 exists to test whether semantics-free braking
can reproduce part of the headline effect; it has not yet run.

An independent source-only scientific audit on 2026-07-19 found two interpretation boundaries and
one pre-run tooling blocker. The exact committed schedule payload
`42008ca73ae6cef32d843e410bbba52f290388612a4e697df57486c79a9ba592` assigns 1,205
frames in the nominal 1.0x arm, matching the donor-union count, but only 735 assigned frames are
donor-union brake positions; 470 are donor non-brake positions. The blind arm has 603 scheduled
windows versus 265 donor windows, and 186/400 cells use only donor-brake positions. The comparator
therefore removes live risk information but does not match state conditioning, per-episode
support, window structure, or the union's latch/release behavior. A competitive blind arm can
weaken semantic necessity; a union advantage supports only the released union policy over this
frozen clock policy at equal class-global assigned-frame count. It cannot isolate semantics.

The primary resampling treats twenty class/pairs as independent although they contain fourteen
unique source sequences. The source-clustered sensitivity must accompany any future headline and
any disagreement must block a robust semantic interpretation. Separately, the production raw CLI
derives a two-bin terminal label from collision status instead of retaining the observed terminal
cause, and the successful raw CLI path lacks an end-to-end known-good fixture. No analytic launch
is permitted until a separate, pre-evidence tooling candidate closes terminal provenance,
successful-CLI coverage, mandatory-report assertions, and analyzer-path parity. These findings do
not alter the frozen F15 hypothesis, schedule, estimand, or verdict.

## Next safe work

- Finish replacement-F15 validation and independent GO review on one frozen byte hash.
- Publish F15, then R15, then the atomic T15/B15 control baton using the sequence above.
- Keep the B14 host and evidence unchanged.
- Correct the retracted current-status prose in `README.md` and `docs/NEXT_PHASE.md`, and the
  quarantined state-of-the-art shorthand in `docs/REPORT.md`, through a separately registered
  source generation; do not weaken the frozen receipt history to edit them.
- Before any iteration-135 run, publish a separate preregistered tooling amendment that closes
  raw terminal provenance and successful-CLI parity, and records the comparator and fourteen-
  source interpretation limits without adapting to outcome evidence.
- Implement the smallest separately reviewable source-bound lifecycle/terminal-proof control and
  content-addressed CI/supply-chain control needed to permit a fresh host boundary.
- Run iteration 135 only after both controls and their distinct canonical checks are accepted.
- Revise the paper only from retained experimental evidence, including negative results and
  uncertainty.

## Verification before any publication

```bash
ruff check .
pytest -q
python3 scripts/validate_docs.py
python3 scripts/mission_state.py
git diff --check
git fsck --connectivity-only --strict --no-dangling
```

Passing validation is necessary but not publication authority. Bind every verdict to exact bytes,
commit ancestry, branch context, and retained CI evidence.
