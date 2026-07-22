# Iteration 135 source-bound lifecycle control preacceptance design record

Status: `preacceptance design record`; not an independently prior preregistration, not accepted,
not executed, not lifecycle-observation evidence, and not host authority.

Date: 2026-07-21

Provenance correction: this document first entered Git atomically with the rejected source
candidate `050b9b831e780405c2d2bab595adb960d37909b8`. Calling that sequence preregistered was
unsupported. A subsequent offline audit also showed that the candidate's purported global
container source still applied an iteration-135 binding and could therefore omit foreign,
unlabelled, or differently labelled running containers while returning quiescence. The corrected
v3 design below records that negative result before acceptance. No host, provider, container,
process, experiment, or outcome evidence was accessed to make this correction.

## Pre-acceptance portability amendment

The first disposable hosted-CI attempt on 2026-07-22 rejected the initial source candidate in
both Python lanes. Linux immediately reused an unlinked staging inode number in two hostile writer
fixtures after the writer had closed its only descriptor, so the numeric device/inode pair no
longer distinguished the replacement. No rerun or canonical publication followed that failure.
Before any accepted source publication, this amendment requires the writer to retain the exact
exclusive-open staging descriptor through every name and directory postcondition and close it
last. This pins the inode against allocator reuse while preserving the explicit limitation that
portable pathname checks cannot make the later link or unlink operation inode-conditional. It
changes no lifecycle verdict, scientific design, authority, schedule, threshold, or launch rule.

## Pre-acceptance synthetic-Git integrity amendment

The first replacement source candidate, exact commit
`9cc549358f0ebf86cda3dd99e8ca29c733375540`, passed its first disposable hosted-CI branch in both
Python lanes. Its distinct second disposable branch then failed attempt 1 in Python 3.10 while
Python 3.11 passed. The sole failure occurred before the tested policy mutation: construction of a
synthetic publication returned a final-manifest commit and the immediately following read-only
`git show COMMIT:launch_manifest.json` probe returned nonzero. The retained controller discarded
both Git stderr and the numeric return code, and the hosted runner did not retain the temporary
repository. The low-level cause is therefore `inconclusive`; the evidence does not establish that
the commit, tree, or blob was absent. The failed run was not rerun, `master` remained exact B15,
and both disposable branches were retained.

The same exact policy case passed 21 of 21 bounded local repetitions. Across the local diagnostic
campaign, all 46 relevant synthetic-publication constructions passed; all 45 retained repositories
contained the exact final-manifest blob and passed full Git object-graph validation. Those results,
the other three green hosted lanes, and the failed runner's materially slower fetch and test times
reject a deterministic policy or numeric-alias defect on the tested local stacks and support—but do
not prove—a runner-local transient. They cannot recover the discarded error. The 45 repositories
were retained only as disposable, non-authoritative local diagnostics under
`/private/tmp/sentinel-f16-repro.RZyIih` (15) and
`/private/tmp/sentinel-f16-paramgroup.JMtoHd` (30); they are not committed evidence and the
operating system may remove them.

Before another source candidate may be proposed, this amendment requires the launch-authorization
synthetic Git helper to use a fixed sanitized environment, forced SHA-1 object format, an empty
template directory, rename-based object creation, committed-object and reference fsync, disabled
hooks, automatic garbage collection, and maintenance, a bounded command deadline, bounded failure
diagnostics including free bytes and inodes, and strict connectivity validation after every
synthetic commit. The controller's bounded Git subprocess wrapper must retain a bounded single-line
stderr preview, complete stderr/stdout byte counts and SHA-256 digests, and the exact return code
for a nonzero process result. Those details are retained in the direct low-level
`AuthorizationError` and the activation-builder path that exposed this defect. Higher validation
reducers may deliberately map that exception to a stable problem code; this amendment does not
claim end-to-end diagnostic retention through every wrapper. Failed-probe stdout content is not
previewed. The wrapper remains fail closed and must not retry the failed authority probe.
Known-bads must inject a missing reachable object, hostile inherited Git configuration, a nonzero
Git exit, a signal-style negative return code, all-invalid UTF-8 streams, and diagnostics whose
escaped form exceeds the final output bound. This amendment changes no lifecycle verdict,
scientific design, authority, schedule, threshold, launch rule, or external governance setting.

## Pre-acceptance global-occupancy integration correction

A later full local-branch topology audit established that the binder candidates
`bc2643ff190f46a69e11e763659ef051b15843d0`,
`9cc549358f0ebf86cda3dd99e8ca29c733375540`, and
`64ccca8e47732b432319492ec16955c598ec50a7` retained the lifecycle validator and lifecycle-test
blobs byte-identical to rejected candidate `050b9b831e780405c2d2bab595adb960d37909b8`.
They therefore retained the filtered-global-registry false-green class even when their separate
next-source binder fixes were valid. Hosted runs 790 through 792 bind those rejected trees and
cannot validate the corrected v3 lifecycle contract.

The integrated replacement must be one new direct child of accepted B15, retain the latest
next-source binder and synthetic-Git hardening, and use the corrected unfiltered-global-registry
validator and hostile fixtures recorded by direct-child correction candidate
`0c63fbe5e5001745559df2d8cedb0b3725d74058`. It requires entirely fresh local and hosted
validation; no prior candidate run can be inherited as acceptance evidence. This correction was
made without host, provider, container, process, experiment, or outcome access.

Adversarial replay of the integrated working tree then found fail-closed reduction-order
mismatches when stable foreign occupancy coexisted with either coherent active-plus-terminal
evidence or an incomplete terminal-source set. Those combinations reduced to `INCONSISTENT` or
`UNKNOWN`, although the frozen order places `HOST_OCCUPIED` first. Conversely, a first patch could
mask cross-source binding drift with `HOST_OCCUPIED`, violating the earlier `INCONSISTENT`
precedence. None could grant quiescence or launch authority, but each contradicted the exact
contract. The reducer now checks non-global drift and all available positive bindings first,
then stable foreign occupancy, then lifecycle composition and terminal completeness. Hostile
fixtures retain all three combined cases. No earlier green suite contained those fixtures, so
fresh validation remains mandatory.

## Purpose

Sentinel knows the scientific result through iteration 134, but it does not possess accepted
source-bound evidence for the execution lifecycle of iteration 135. The canonical lifecycle value
therefore remains `UNKNOWN`. Static repository state, elapsed time, missing reviewers, timeouts,
absent processes, an empty container inventory, or a missing lock cannot change that value.

This control freezes only the offline retained-record parsers, receipt validator, and lifecycle
reducer that must be accepted before a later generation may define a host observer. It does not
freeze or implement a host command, `argv`, environment, working directory, provider request, or
capture executable. This generation accesses no host or provider and authorizes no H, E, P, S,
smoke, analytic, publication, retry, or relaunch activity.

## Invariants

1. The default lifecycle verdict is `UNKNOWN`.
2. Every JSON field set and scalar type is exact. Boolean/integer aliases, integral floats,
   duplicate keys, non-finite numbers, excessive nesting, huge integers, unbounded text, and
   unknown fields fail closed.
3. Every source payload is bounded raw canonical JSON with an exact source-specific `records`
   schema. Arrays permit multiple matching processes, containers, jobs, or artifacts and require
   canonical ordering, no duplicate records, source-specific cardinality (the canonical launch
   and analytic lock paths are singleton), exact scope/filter/sort metadata, exact record/page
   counts, `complete=true`, and a null continuation token. There is no producer-supplied
   `registry_state`: the validator derives `EMPTY`, `ACTIVE`, a terminal fact, or a conflict from
   the retained records.
4. The nine distinct digests freeze parser/output domain separation only. They are not hashes of
   an executable host query or invocation. The later observer generation must bind its actual
   implementation bytes, `argv`, environment, working directory, and provider request before use.
5. The two rounds are global: every initial capture must finish, at least 500,000,000 monotonic
   nanoseconds must dwell, and only then may any terminal capture begin. Per-source pairing alone is
   insufficient.
6. The public entrypoint requires detached trusted bindings for the receipt, control and observed
   source commits, mission state, host identity, one-shot challenge, boot ID, approved observer
   executable and build digests, cgroup-policy digest, lease ID, trusted current boot-monotonic
   time, and exact receipt deadline.
7. `mission_containers` is the exact iteration-135-labelled projection;
   `global_containers` is the unfiltered, mission-agnostic complete host runtime registry. The
   mission projection must equal the iteration-135-labelled subset of the global registry in each
   round. Stable additional global rows yield the blocking `HOST_OCCUPIED` verdict; global churn
   or a subset mismatch yields `UNKNOWN`.
8. Positive retained producer records yield `RUNNING`; active-plus-terminal evidence or
   non-global cross-round record drift is inconsistent.
9. Terminal classification requires stable, cross-bound records from the attempt journal,
   terminal witness, retained proof manifest, and provider registry, with all active-only domains
   empty. `EXIT_ZERO` maps only to `TERMINATED_COMPLETE` and provider `SUCCEEDED`; `CANCELLED` maps
   to provider `CANCELLED`; `EXIT_NONZERO`, `INFRA_FAILURE`, `SIGNALLED`, and `TIMEOUT` map to
   `TERMINATED_PARTIAL` and provider `FAILED`.
10. The proof-manifest record retains bounded base64 bytes, byte count, and SHA-256. Those bytes must
   be canonical JSON and must independently bind the attempt, launch manifest, exact terminal state
   and cause, and an exactly typed artifact count. A digest assertion without valid retained bytes
   is insufficient.
11. There is deliberately no `IDLE` verdict. The strongest pre-execution classification is
   `QUIESCENCE_EVIDENCE_COMPLETE`: all nine paired parsers returned stable empty records across the
   global dwell, and both unfiltered global-container rounds were empty. This is point-in-time
   retained evidence, not permission.
12. Any structural, parser, detached, deadline, or binding problem forces `UNKNOWN`; no such fault
   may retain `QUIESCENCE_EVIDENCE_COMPLETE` or another positive verdict.
13. No serialized field or offline API grants a host boundary. A later accepted H controller must
   retain the original open lease descriptor as a nonserializable process-local capability,
   revalidate it immediately before mutation, and atomically consume a one-shot challenge. A
   stored receipt is never reusable authority.
14. `launch_authorized` and `relaunch_authorized` are always false.
15. The embedded payload SHA-256 is a self-consistency checksum only. The public validator also
    requires a detached expected receipt digest supplied by an independently accepted manifest or
    performing controller. Neither digest is identity, independent approval, scientific
    verification, or permission.

## Receipt contract

The exact root fields are:

- `schema`;
- `mission` — iteration, experiment path, source commit, mission-state digest, optional launch
  manifest digest, and optional attempt identifier;
- `observer` — control source, parser-policy digest, challenge digest, paired
  host/boot/process/executable/build/cgroup-policy identities, UTC and monotonic intervals, and a
  short capture deadline;
- `lease` — lease identifier, canonical path, matching claimed owner identity, acquisition time,
  and paired device/inode/mount/mode/owner/link/time snapshots. It deliberately has no serialized
  `lock-held`, OFD-lock, no-follow, or live-file-descriptor authority field;
- `sources` — paired raw capture envelopes for the durable launch lock, launcher process,
  mission-labelled containers, global container inventory, analytic lock, attempt journal,
  terminal witness, proof manifest, and provider job registry;
- `verdict`, `quiescence_evidence_complete`, `launch_authorized`, `relaunch_authorized`,
  `problems`, `problem_count`, and `receipt_payload_self_checksum_sha256`.

Every capture envelope binds its parser-domain digest, monotonic interval, exact return status,
timeout/truncation state, bounded raw stdout/stderr bytes, byte counts, and stream digests.
Successful stdout is strict-decoded again. Its source payload binds only the source domain,
challenge, parser contract, host, boot, observation time, and actual retained records. The record
parsers accept a bounded canonically sorted array of exactly typed records:

- launch and analytic locks admit at most one canonical-path row and retain attempt, manifest,
  owner PID, and owner start ticks;
- the launcher retains attempt, manifest, PID, start ticks, and executable digest;
- the mission-container domain retains attempt, manifest, container ID, and exact `RUNNING` state;
- the unfiltered global-container domain retains every running container ID, exact `RUNNING`
  state, and bounded nullable raw iteration, attempt, and manifest label values without requiring
  a Sentinel or iteration-135 binding;
- the attempt journal retains its exact active or terminal row;
- the terminal witness retains only a terminal row;
- the proof domain retains and validates the complete proof-manifest bytes; and
- the provider domain retains job ID, exact provider state, cause, and proof binding.

These are parser fixtures and an offline acceptance contract. Because no acquisition implementation
exists in this generation, the serialized scope, pagination, and completeness fields are claims to
be authenticated by a future collector, not independent proof of enumeration. They are not
evidence that a real host query ran or that an empty list exhausts a real registry.

## Detached trust inputs

The caller must supply every detached binding explicitly. The validator rejects malformed hashes,
commits, UUIDs, and Boolean-as-integer values before receipt reduction. The detached boot ID scopes
the monotonic clock; the trusted current value must be at or after capture completion and no later
than the exact detached deadline. Matching a detached executable, build, or cgroup-policy digest is
necessary but does not prove execution; those values must eventually come from an independently
accepted performing-controller artifact and capture path.

## Generation-sixteen next-source bootstrap binder

The generation-sixteen verifier also records a narrow preacceptance next-source bootstrap mode.
This mode may be used only after an operator has independently accepted and retained both the
exact B16 40-hex commit OID and the SHA-256 of the canonical R16 tooling receipt. Those two values
are external trust axioms. The binder neither discovers acceptance from `origin/master` or
topology nor turns a locally present commit into an accepted baton.

The operator must select and measure the exact R16 Python and B16 verifier before either executes;
that pre-execution selection is an external bootstrap trust axiom because executing code cannot
authenticate itself before execution. Binding starts under that exact Python executable and
requires isolated, no-bytecode, no-site execution (`-I -B -S`). The executable row authenticates
the interpreter binary, not its standard-library installation; that installation is an additional
explicit external trust axiom. Once started and before any structural Git read, the binder
bounded-reads and stable-hashes the working R16 receipt, compares that digest with the detached
value, and checks the current verifier, Python, and Git bytes, metadata, and version rows against
the authenticated receipt.
It then requires a physical clean worktree detached at the literal accepted B16 OID; rejects
shallow, graft, alternate-object, replacement, promisor, partial-clone, skip-worktree, and
assume-unchanged state; and checks the exact B16 -> T16 -> R16 -> F16 -> B15 path topology. Every Git call
uses the authenticated executable, sanitized environment, global `--no-replace-objects`, and
explicit discovered `--git-dir`; worktree-sensitive calls also use the explicit physical
`--work-tree`. A linked worktree is admissible only through a regular `.git` gitfile whose target
is under the common repository's canonical `.git/worktrees` registry with an exact backlink.
Bounded no-follow snapshots retain the identities and digests or explicit absence of the gitfile,
commondir, backlink, `HEAD`, index, common and worktree configs, and packed refs, plus identities
for the worktree, Git/common/object directories and their graph/object-metadata subdirectories.
Every receipt, binder, and control-file read walks each absolute parent component through
descriptor-relative no-follow directory opens, opens the final file nonblocking, and repeats the
path/descriptor identity check after the bounded read. Ancestor swaps, FIFOs, config includes, and
symlinked control files or metadata directories fail closed. Exact snapshots must agree before
and after binding.

The proposed candidate must be one commit whose sole parent is the literal accepted B16 OID. The
binder uses one authenticated local `git cat-file --batch` object reader to parse and SHA-verify
the accepted chain and candidate raw commit, tree, and blob objects itself. The accepted-chain
reducer recursively compares raw basename/mode/OID maps, skips equal subtree OIDs, and derives the
exact byte-sorted change scope without `rev-list`, `diff-tree`, `show`, or `ls-tree`; it reads no
topology blobs and then reads only the exact R16 receipt and F16 binder blobs. It never checks out,
imports, executes, or otherwise materializes candidate content. It recomputes every Git SHA-1 object identity from
`type + size + NUL + payload`, computes SHA-256 for each retained content identity, and emits a
complete, bytewise-sorted manifest of regular files with path, mode, byte count, blob OID, and
SHA-256. Candidate names are restricted to bounded ASCII components; `.git` in any case, empty
trees, symlinks, gitlinks, duplicate components, and modes other than `100644` and `100755` fail
closed.

The object contract is explicit: at most 1 MiB per commit, depth 64, 10,000 tree objects, 64 MiB
of tree bytes, 10,000 files, 1,024 path bytes, 255 component bytes, 128 MiB per blob, and 8 GiB of
aggregate file bytes. The object reader has one 900-second deadline, a 256-byte response-header
bound, and an empty-stderr requirement with a 1 MiB diagnostic bound. The canonical receipt is at
most 16 MiB and its parser rejects duplicate keys, every float and non-finite value, integers
outside signed 64-bit range, Boolean/integer aliases, more than 32 levels, and more than 200,000
nodes. After the candidate read, the verifier repeats the complete non-executing R16/tool/binder,
Git-layout, clean-index/worktree, and raw B16-chain authentication with a fresh object reader and
requires exact start/end identity before constructing a receipt.

The exact `sentinel.next_source_binding.v1` receipt is deterministic and contains no clock. Its
payload checksum covers the fixed policy, authenticated trust root, raw-object aggregates, and
complete file manifest. Its fixed limitations state that the detached B16 OID and R16 digest are
external axioms, that the R16-bound Python standard-library installation is a further external
axiom, that pre-execution selection and measurement of the exact R16 Python and B16 verifier is an
external bootstrap axiom, and that the writer assumes no adversarial same-UID mutation of the
output-parent route, the staging or final names, or their inodes, content, or metadata throughout
publication or after its last observation before independent replay. Portable POSIX interfaces
neither isolate processes sharing a UID nor make name-based link or unlink inode-conditional. The
writer validates parent ownership and group/world write mode bits but does not bind filesystem
ACLs, mount policy, or permission enforcement; those remain external host axioms. They also state
that only the direct-child candidate content is bound, that the operator must separately accept
the binding before any candidate checkout, import, execution, or publication, and that the
receipt has no repository-publication, hosted-CI, scientific, host, lifecycle, launch, or safety
authority. Both publication and launch authority fields are exactly `false`.

The output path must be a safe basename in a physical, operator-owned, non-group/world-writable
directory outside both the trusted worktree and common Git directory. It opens the output-parent
component chain without following links and rejects any ancestor whose device/inode identity
matches either separately opened forbidden root, including a differently cased filesystem alias.
Publication writes and fsyncs a mode-`0600` temporary inode, retains the exact exclusive-open
descriptor through every name and directory postcondition, revalidates that opened parent, and
uses a same-directory hard link as the atomic no-clobber commit point. Retaining the descriptor
prevents the inode number from being recycled while the writer relies on its identity. The complete
`.next-source.*.tmp` staging namespace is reserved case-insensitively, so no requested output can
alias a generated staging name on a case-insensitive filesystem. The writer records the inode
created by its successful exclusive open, checks that exact no-follow inode immediately before
linking, and repeats that check immediately before unlinking. A collision or replacement observed
by those checks is preserved and fails closed.
The owner-owned, non-group/world-writable directory is an external assumption against adversarial
same-UID mutation of the output-parent route, the staging or final names, and their inodes,
content, or metadata throughout publication. The checks and subsequent link or unlink cannot be
made inode-conditional with portable POSIX interfaces, and filesystem permissions do not isolate
processes sharing a UID. ACL and mount-policy enforcement are separately external host axioms.
Writer success proves the bytes and postconditions it observed, not persistence after its final
observation; detached hashing and full replay remain prerequisites for operator acceptance. This
same-UID exclusion is therefore an explicit threat-model axiom, not a claimed known-bad gate. Any
pre-link failure creates no new final receipt; an already existing final is preserved unchanged
and remains unaccepted.
Once the link succeeds, any catchable directory-fsync, temporary-unlink, final-read,
inode/mode/link-count, parent-revalidation, directory-close, or retained-temporary-descriptor-close
failure preserves the final file and reports the distinct
`I135_NEXT_SOURCE_BINDING_COMMITTED_POSTCONDITION_FAILED` outcome; it never overwrites an existing
path. If the hard-link call raises after the kernel has already created the final name, the writer
reconciles the final no-follow inode, content, mode, size, and link count against the temporary
inode and reports that committed outcome. If the link call
raises and reconciliation itself cannot classify the final state, the writer preserves the owned
staging name and reports the separate
`I135_NEXT_SOURCE_BINDING_COMMIT_STATE_INDETERMINATE` outcome. The four CLI outcomes are success
(exit 0), definite pre-commit failure (exit 2), proven committed/postcondition failure (exit 3),
and indeterminate commit state (exit 4). A catchable CLI-reporting failure after successful
publication is also a committed postcondition failure at exit 3; success requires exit 0 plus the
exact complete report whose final line is `I135_NEXT_SOURCE_BINDING_OK`. Marker text without exit 0
has no authority. An otherwise unclassified `BaseException` is conservatively reported through
the indeterminate exit-4 envelope because it can arrive after the final link but before the caller
receives the publication result. Best-effort stderr failure never changes an already classified
exit code. Neither exit 3 nor exit 4 may be retried or used until exact final-path inspection and
full replay with the detached values completes. `SIGKILL`, process death, kernel panic, and power
loss cannot emit a verdict and may leave a final and/or temporary name after the hard-link point.
After such an interruption, presence is never evidence of success: the final remains unaccepted
until an independent bounded read and hash plus full replay with the detached B16, R16, candidate,
and binding values succeeds before any retry or use.

With independently retained literal values, the only recorded candidate-generation and replay
forms are:

```text
/ABSOLUTE/R16/PYTHON -I -B -S /ABSOLUTE/B16/experiments/iter135_neuroncap_blind_braking_dose_response/verify_tooling135.py \
  --bind-next-source F17_COMMIT \
  --accepted-baton-commit B16_COMMIT \
  --accepted-tooling-receipt-sha256 R16_SHA256 \
  --next-source-output /PHYSICAL/OUTSIDE/TRUSTED/TREES/f17-binding.json

/ABSOLUTE/R16/PYTHON -I -B -S /ABSOLUTE/B16/experiments/iter135_neuroncap_blind_braking_dose_response/verify_tooling135.py \
  --verify-next-source-binding /PHYSICAL/OUTSIDE/TRUSTED/TREES/f17-binding.json \
  --accepted-baton-commit B16_COMMIT \
  --accepted-tooling-receipt-sha256 R16_SHA256 \
  --expected-candidate-commit F17_COMMIT \
  --expected-binding-sha256 F17_BINDING_SHA256
```

Required bootstrap known-bads include wrong detached B16 or R16 identities, a non-direct parent,
candidate execution tripwires, object-ID/type/size/framing drift, deadline or stderr output,
empty/recursive/deep/oversized trees, `.git`, duplicate file/tree names, symlinks, gitlinks,
hidden index flags, config includes, control-file/directory symlinks or transient metadata drift,
replacement/alternate/promisor state, linked-worktree redirection, exact-chain parent/scope drift,
incomplete or noncanonical manifests, duplicate-OID content-identity drift, JSON
type/size/depth/node faults, an oversized receipt rejected before reading, two concurrent writers,
foreign staging collisions or replacements, case-insensitive reserved staging-name aliases,
pre-link fsync/link faults, unreadable or interrupted link reconciliation, retained temporary
descriptor close faults in every publication state, a catchable fault in each listed post-link
validation class (including a `BaseException` interruption),
unclassified `BaseException` indeterminacy, post-publication CLI-reporting and flush faults,
stderr-reporting faults, interrupted-process recovery, output symlinks, redirected parents,
physical or case-aliased forbidden roots, and existing-output no-clobber behavior.

This binder is part of the still-unaccepted F16 source surface. It cannot bind F17 before F16,
R16, T16, and B16 have been independently reviewed, retained, and accepted, and it does not
authorize F17 execution after producing a binding. Acceptance of a later source generation remains
a separate operator decision.

## Frozen reduction order

The reducer applies this precedence without consulting the claimed verdict:

1. malformed, failed, timed-out, truncated, or incomplete captures -> `UNKNOWN`;
2. any structural, detached, deadline, or binding fault -> `UNKNOWN`;
3. global-container churn or mission/global subset disagreement -> `UNKNOWN`;
4. well-formed non-global source or cross-binding drift -> `INCONSISTENT`;
5. stable global rows outside the exact mission projection -> `HOST_OCCUPIED`;
6. stable positive producer evidence -> `RUNNING`, while active-plus-terminal conflict ->
   `INCONSISTENT`;
7. exact cross-bound complete terminal records with no active producer or foreign global
   occupancy -> `TERMINATED_COMPLETE`;
8. exact cross-bound partial terminal records with no active producer or foreign global
   occupancy -> `TERMINATED_PARTIAL`;
9. nine stable empty record sets separated by the frozen global dwell, including two empty
   unfiltered global-container rounds ->
   `QUIESCENCE_EVIDENCE_COMPLETE`;
10. every other combination -> `UNKNOWN`.

The serialized verdict, quiescence-evidence flag, authority booleans, self-checksum, and problem
count must agree with independent reduction. A detached expected digest must match the complete
canonical receipt bytes. A claimed positive verdict never survives any accumulated problem.

## Required known-bad evidence

The source gate must retain fixtures for:

- empty container inventories with a live launcher;
- incomplete or missing attempt, analytic-lock, terminal, proof, or provider evidence;
- the right-looking bytes with the wrong challenge, boot, host, source commit, mission state,
  parser policy, executable, build, cgroup policy, lease ID, deadline, trusted current time, or
  detached receipt digest;
- timeout, truncation, command error, unreadable output, PID reuse, boot change, executable drift,
  capture reorder, source change, or clock-duration disagreement;
- a world-writable, wrongly owned, hard-linked, path-swapped, inode-swapped, or mount-swapped lease
  snapshot, plus any attempt to serialize a live FD/OFD-lock/no-follow claim as authority;
- terminal records missing an attempt, manifest, cause, or proof; unregistered or contradictory
  cause/state/provider mappings; cross-source terminal drift; partial proof represented as
  complete; and invalid, noncanonical, count-drifted, or digest-drifted proof-manifest bytes;
- duplicate keys, non-finite values, excessive nesting, huge integers, Boolean/integer aliases,
  integral floats, unknown fields, stream-count/hash drift, and self-checksum or detached-digest
  mismatch;
- copied or colliding parser domains, a missing provider registry, insufficient global dwell, and
  a producer appearing between rounds;
- foreign, unlabelled, differently labelled, appearing, disappearing, or identity-churning global
  containers; mission rows absent from the global registry; iteration-135 global rows absent from
  the mission projection; subset binding drift; and complete or partial terminal evidence paired
  with any retained running global container;
- every lifecycle variant coupled to `launch_authorized=true` or `relaunch_authorized=true`.

Classification fixtures must cover `RUNNING`, `HOST_OCCUPIED`, `TERMINATED_COMPLETE`,
`TERMINATED_PARTIAL`, `QUIESCENCE_EVIDENCE_COMPLETE`, and the required `UNKNOWN`/`INCONSISTENT`
known-bads. Every case retains both authority flags false; none returns permission. These are
reducer unit fixtures, not claims about the actual iteration-135 lifecycle.

## Acceptance and phase boundary

Acceptance may move the mission only from `CONTROL_HARDENING_REQUIRED / UNKNOWN` to
`CI_HARDENING_REQUIRED / UNKNOWN`. It cannot move to tooling-frozen preflight and cannot create
`IDLE`. Acceptance means only that the prospective schema/parser/reducer source is controlled; it
does not establish a source-bound host observation or actual `QUIESCENCE_EVIDENCE_COMPLETE`.

The independently reviewable CI/supply-chain baton remains mandatory. A later generation may
define the observation phase and performing controller only after both source-control batons are
accepted. No current artifact authorizes that observer to run.

## Later performing-controller boundary

Before any host preparation, environment capture, manifest generation, smoke, or analytic action,
every static `run_state == "IDLE"` admission must be replaced. The later controller must retain
the original no-follow OFD-locked descriptor, its first `fstat`, host/boot/PID/start-time/executable
identity, challenge nonce, deadline, validated receipt digest, and provider snapshot in process
memory. Immediately before H it must recheck every binding under the same descriptor and create a
durable one-shot launch-intent/attempt-journal record with exclusive creation, receipt digest, and
nonce, then fsync the record and directory while still holding the lock. Reopen, replay, timeout,
or an existing intent fails closed. That performing integration is outside this source generation.

That later generation must additionally retain and bind the actual observer/query implementation
bytes and every invocation input (`argv`, environment, working directory, and provider request).
Until that exists and is independently accepted, the parser fixtures in this document cannot be
used as evidence that iteration 135 was observed, quiescent, running, or terminated.
