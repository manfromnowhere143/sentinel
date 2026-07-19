# HANDOFF — retained mission snapshot

Generation-fifteen control-integrity recovery has reached a local B15 publication candidate on
2026-07-20.
Read `CONTINUITY.md` first. This file is a repository snapshot, not live host authority.

## Repository and publication state

```text
canonical branch       master
accepted source        F15 3bc8913fb8e7b09650fbf2b7370ac17a57f7e2d0
accepted receipt       R15 80f4b37d7c7c1f2a917e68bdcb015f188299f1fe
remote master          R15 at this B15 source snapshot
local state child      T15 5366d8f714d8d1c49e99f238ba4e88733d7904ab
local baton            B15 is the commit containing this snapshot; external acceptance pending
superseded candidates  failed F15 4d8801605f1e285c5000b4220e965e97a8aff345;
                       pre-publication F15 132c01eab2414a628376631cdf1c24fa6d9a7ab9
run state              UNKNOWN
iteration-135 phase    CONTROL_HARDENING_REQUIRED
authority              none
launch authorized      false
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

The third candidate, `132c01eab2414a628376631cdf1c24fa6d9a7ab9`, passed the complete
local suite in both frozen lanes (`1,934` passed and one expected skip per lane) and two distinct
disposable runs: `ci-validate-f15-a-132c01eab241` run 781 (`29699807562`, check suite
`80422375129`, jobs `88226821175` and `88226821183`) and
`ci-validate-f15-b-132c01eab241` run 782 (`29699808989`, check suite `80422378838`, jobs
`88226825097` and `88226825159`). A pre-publication topology review then found that the
active-HANDOFF test helper hard-coded the preregistration action constants. It would reject the truthful
`CONTROL_HARDENING_REQUIRED` action block when B15 followed T15, despite
`MISSION_STATE.json` being valid. The commit never reached `master` and is superseded, so its
green runs are retained diagnostic evidence rather than promotion authority. The replacement
binds the HANDOFF action block to the exact canonical `MISSION_STATE.json` arrays and retains a
positive and known-bad control-hardening fixture.

## Accepted F15 and R15 evidence

The accepted publication chain through the canonical remote tip is:

```text
B14 69bd2e2face00ccabb426382347eb04e8a0dbe83
 └─ F15 3bc8913fb8e7b09650fbf2b7370ac17a57f7e2d0
     └─ R15 80f4b37d7c7c1f2a917e68bdcb015f188299f1fe
         └─ T15 5366d8f714d8d1c49e99f238ba4e88733d7904ab  local only
             └─ B15 the commit containing this snapshot              local only
```

F15 is a direct B14 child with tree `1a16c0fb7031a401578afd41b78ed83e92008eb4`
and exactly the registered nineteen paths. Its canonical committed-byte manifest SHA-256 is
`c3828f74e3ea209d08c5aa75d7da3c55a85c4b309ddb36b7439ad173bb0db930`
under the retained contract: a path-sorted UTF-8 canonical JSON array of
`{bytes,mode,path,sha256}` rows, sorted keys, comma/colon separators, and no trailing newline.
The modes remain sixteen `100644` and three `100755`; independent Git-blob replay found no
working-byte, object-ID, or mode mismatch.

The final F15 bytes passed repository-wide Ruff, all tests, and the documentation guard in both
local lanes:

- Python 3.10.19 / pytest 9.1.1 / NumPy 2.2.6 / scikit-learn 1.7.2:
  `1,935 passed, 1 skipped` in 1,727.32 seconds;
- Python 3.11.15 / pytest 9.1.1 / NumPy 2.4.6 / scikit-learn 1.9.0:
  `1,935 passed, 1 skipped` in 1,693.20 seconds;
- each lane's documentation guard reported 402 Markdown files clean and every RESULT surfaced
  in `README.md`.

All retained acceptance runs used workflow ID `304353015`, name `ci`, path
`.github/workflows/ci.yml`, event `push`, attempt 1, exactly two successful jobs, and exact
branch and workflow projection replay:

- F15 disposable A: branch `ci-validate-f15-a-3bc8913fb8e7`,
  [run 783 / `29701426376`](https://github.com/manfromnowhere143/sentinel/actions/runs/29701426376),
  check suite `80426354852`, created/started `2026-07-19T19:52:11Z`, updated
  `2026-07-19T19:59:18Z`. Jobs:
  [3.10 / `88231009141`](https://github.com/manfromnowhere143/sentinel/actions/runs/29701426376/job/88231009141),
  `19:52:13Z`–`19:59:17Z`; and
  [3.11 / `88231009154`](https://github.com/manfromnowhere143/sentinel/actions/runs/29701426376/job/88231009154),
  `19:52:13Z`–`19:58:48Z`.
- F15 disposable B: branch `ci-validate-f15-b-3bc8913fb8e7`,
  [run 784 / `29701428822`](https://github.com/manfromnowhere143/sentinel/actions/runs/29701428822),
  check suite `80426360735`, created/started `2026-07-19T19:52:16Z`, updated
  `2026-07-19T19:59:17Z`. Jobs:
  [3.10 / `88231015086`](https://github.com/manfromnowhere143/sentinel/actions/runs/29701428822/job/88231015086),
  `19:52:19Z`–`19:59:16Z`; and
  [3.11 / `88231015067`](https://github.com/manfromnowhere143/sentinel/actions/runs/29701428822/job/88231015067),
  `19:52:19Z`–`19:58:47Z`.
- F15 canonical: branch `master`,
  [run 785 / `29701663552`](https://github.com/manfromnowhere143/sentinel/actions/runs/29701663552),
  check suite `80426919838`, created/started `2026-07-19T19:59:49Z`, updated
  `2026-07-19T20:06:37Z`. Jobs:
  [3.10 / `88231608750`](https://github.com/manfromnowhere143/sentinel/actions/runs/29701663552/job/88231608750),
  `19:59:52Z`–`20:06:36Z`; and
  [3.11 / `88231608751`](https://github.com/manfromnowhere143/sentinel/actions/runs/29701663552/job/88231608751),
  `19:59:52Z`–`20:05:38Z`.
- R15 disposable: branch `ci-validate-r15-80f4b37d7c7c`,
  [run 786 / `29703998610`](https://github.com/manfromnowhere143/sentinel/actions/runs/29703998610),
  check suite `80432704034`, created/started `2026-07-19T21:14:32Z`, updated
  `2026-07-19T21:21:52Z`. Jobs:
  [3.10 / `88237755340`](https://github.com/manfromnowhere143/sentinel/actions/runs/29703998610/job/88237755340),
  `21:14:35Z`–`21:21:51Z`; and
  [3.11 / `88237755333`](https://github.com/manfromnowhere143/sentinel/actions/runs/29703998610/job/88237755333),
  `21:14:35Z`–`21:21:29Z`.
- R15 canonical: branch `master`,
  [run 787 / `29704232755`](https://github.com/manfromnowhere143/sentinel/actions/runs/29704232755),
  check suite `80433282212`, created/started `2026-07-19T21:22:14Z`, updated
  `2026-07-19T21:28:48Z`. Jobs:
  [3.10 / `88238396944`](https://github.com/manfromnowhere143/sentinel/actions/runs/29704232755/job/88238396944),
  `21:22:17Z`–`21:28:26Z`; and
  [3.11 / `88238396913`](https://github.com/manfromnowhere143/sentinel/actions/runs/29704232755/job/88238396913),
  `21:22:16Z`–`21:28:47Z`.

R15 is the receipt-only direct F15 child. The protected receipt is 36,922 bytes with SHA-256
`0d169cf0c58b1d6c597ae3381003bf3b06a2f630d6f8d51b7c82c6004406b0c8`
and payload SHA-256
`aac3cab0ddcf512766c0b9b18dfdfa38dd17a890f51322fd463ce7dc9fc21f5d`.
Its exact publication block names generation integer 15, B14 as recovery parent, R14
`b260ca5b0910c4d499c13e42add97affd726b77c` as the superseded receipt, and the frozen F15
reason code. The one-shot verifier ran from `2026-07-19T20:08:30.961491Z` through
`2026-07-19T20:38:39.041141Z`, returned `I135_TOOLING_VERIFICATION_OK`, exact integer zero,
and an empty problem list. All eight retained command rows have exact integer return code zero.
The committed receipt then independently replayed to `I135_TOOLING_VERIFICATION_OK`.

The transaction wrapper's first read-only post-generation module load failed because the
Python 3.14 `dataclass` module was not registered in `sys.modules`; its cleanup function also
left shell `errexit` disabled, so the wrapper printed a nonauthoritative terminal marker after
that failed check. That marker was quarantined and was not used as evidence. The generator was
not rerun. A corrected strict loader verified the already relocked bytes, and the later
committed-receipt replay independently passed.

The working receipt matches the R15 Git blob and is a one-link regular file owned by
`danielwahnich:staff`, mode `0600`, with exact `uchg` and the single ACL
`user:danielwahnich deny delete`. The experiment-directory device and inode remained stable
through generation. T15 changes only `MISSION_STATE.json`; B15 changes only this file and
`CONTINUITY.md`. No host, GPU, H/E/P/S, smoke, analytic, result, or paper authority was created.

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

## Accepted F15 contract

F15 `3bc8913fb8e7b09650fbf2b7370ac17a57f7e2d0` is a source-only child of B14 with
exactly these nineteen paths:

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
  iteration 135 / CONTROL_HARDENING_REQUIRED
- Canonical completed experiment: experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md
- Next program: semantics-free placebo dose-response causal closure
- Canonical next action: iteration 135 / CONTROL_HARDENING_REQUIRED / semantics-free
  placebo dose-response causal closure.
- Authorized now:
  - implement and validate only offline, preregistered, source-bound lifecycle observation,
    terminal-proof, partial-proof, inconsistency, and fail-closed recovery controls;
  - implement and validate separately reviewable hermetic CI, supply-chain, and
    publication-evidence controls without changing external governance settings.
- Forbidden now:
  - de-prepare, rebuild, normalize, clean, install, write, delete, mutate, inventory, or access
    any iteration-135 remote host, remote filesystem, host-side repository, packet, runtime,
    lock, container, GPU, credential, or external provider in a way that could create H, E, P,
    or S;
  - create, execute, publish, or advance any H, E, P, or S descendant; launch activation; live
    smoke; or analytic episode;
  - infer `IDLE`, termination, completion, readiness, approval, or authority from static state,
    absent containers, absent processes, missing reviewers, timeouts, retry exhaustion, or
    incomplete proof;
  - run analyzers or publish iteration-135 data, results, claims, figures, paper text, or
    scientific conclusions;
  - change branch protection, rulesets, Actions policy, repository visibility, credentials,
    secrets, access control, or other external governance settings without explicit operator
    authorization;
  - rerun iteration 134 or adapt iteration-135 schedules, estimands, verdicts, or policies after
    evidence.

## Publication sequence

1. F15 and R15 are accepted at the exact SHAs and evidence identities above.
2. T15 is the exact state-only R15 child `5366d8f714d8d1c49e99f238ba4e88733d7904ab`;
   it must never be pushed as a standalone branch tip.
3. B15 is the immediately following documentation-only child and the commit containing this
   snapshot. Its SHA cannot be embedded in its own bytes.
4. Validate exact B15 on one fresh disposable branch while `origin/master == R15`. This is
   `non-authoritative-control-candidate`, with `authority=none`,
   `launch_authorized=false`, and empty references.
5. Only after that exact run succeeds, normally fast-forward `master` from R15 through T15 to
   B15 and require a distinct master run that observes `origin/master == B15` and
   `origin-published-control-baton`.
6. If disposable validation fails, preserve the branch and run and leave `master` at R15. If
   canonical B15 validation fails, preserve the red evidence and restore R15 only with an exact
   `master:B15` lease.
7. Retain final B15 SHA, run, check-suite, and job evidence externally; writing those future
   values into this file would create a different B15.

F15, R15, T15, and B15 authorize no host access, H/E/P/S, activation, smoke, analytics, or
scientific claim. B15 only advances the offline control-hardening stop.

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

- Freeze and validate the exact B15 documentation-only child on one fresh disposable branch
  while canonical `master` remains R15.
- If and only if that candidate is exact green, publish the same B15 tip atomically through T15,
  require a distinct canonical run, and preserve or restore under the sequence above.
- Keep the preserved B14 host install and all host/evidence paths unchanged.
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
