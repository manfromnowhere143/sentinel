# Iteration 135 source-bound lifecycle control preregistration

Status: `preregistered` prospective offline receipt-schema reducer; not accepted, not executed,
not lifecycle-observation evidence, and not host authority.

Date: 2026-07-21

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
7. Positive retained producer records yield `RUNNING`; active-plus-terminal evidence or
   cross-round record drift is inconsistent.
8. Terminal classification requires stable, cross-bound records from the attempt journal,
   terminal witness, retained proof manifest, and provider registry, with all active-only domains
   empty. `EXIT_ZERO` maps only to `TERMINATED_COMPLETE` and provider `SUCCEEDED`; `CANCELLED` maps
   to provider `CANCELLED`; `EXIT_NONZERO`, `INFRA_FAILURE`, `SIGNALLED`, and `TIMEOUT` map to
   `TERMINATED_PARTIAL` and provider `FAILED`.
9. The proof-manifest record retains bounded base64 bytes, byte count, and SHA-256. Those bytes must
   be canonical JSON and must independently bind the attempt, launch manifest, exact terminal state
   and cause, and an exactly typed artifact count. A digest assertion without valid retained bytes
   is insufficient.
10. There is deliberately no `IDLE` verdict. The strongest pre-execution classification is
   `QUIESCENCE_EVIDENCE_COMPLETE`: all nine paired parsers returned stable empty records across the
   global dwell. This is point-in-time retained evidence, not permission.
11. Any structural, parser, detached, deadline, or binding problem forces `UNKNOWN`; no such fault
   may retain `QUIESCENCE_EVIDENCE_COMPLETE` or another positive verdict.
12. No serialized field or offline API grants a host boundary. A later accepted H controller must
   retain the original open lease descriptor as a nonserializable process-local capability,
   revalidate it immediately before mutation, and atomically consume a one-shot challenge. A
   stored receipt is never reusable authority.
13. `launch_authorized` and `relaunch_authorized` are always false.
14. The embedded payload SHA-256 is a self-consistency checksum only. The public validator also
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
- container domains retain attempt, manifest, container ID, and exact `RUNNING` state;
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

The generation-sixteen verifier also preregisters a narrow next-source bootstrap mode. This mode
may be used only after an operator has independently accepted and retained both the exact B16
40-hex commit OID and the SHA-256 of the canonical R16 tooling receipt. Those two values are
external trust axioms. The binder neither discovers acceptance from `origin/master` or topology
nor turns a locally present commit into an accepted baton.

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
Publication writes and fsyncs a mode-`0600` temporary inode, revalidates that opened parent, and
uses a same-directory hard link as the atomic no-clobber commit point. The complete
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
inode/mode/link-count, parent-revalidation, or directory-close failure preserves the final file
and reports the distinct `I135_NEXT_SOURCE_BINDING_COMMITTED_POSTCONDITION_FAILED` outcome; it
never overwrites an existing path. If the hard-link call raises after the kernel has already
created the final name, the writer reconciles the final no-follow inode, content, mode, size, and
link count against the temporary inode and reports that committed outcome. If the link call
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

With independently retained literal values, the only preregistered generation and replay forms
are:

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
pre-link fsync/link faults, unreadable or interrupted link reconciliation, a catchable fault in
each listed post-link validation class (including a `BaseException` interruption),
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
3. well-formed source or cross-binding drift -> `INCONSISTENT`;
4. stable positive producer evidence -> `RUNNING`, while active-plus-terminal conflict ->
   `INCONSISTENT`;
5. exact cross-bound complete terminal records with no active producer -> `TERMINATED_COMPLETE`;
6. exact cross-bound partial terminal records with no active producer -> `TERMINATED_PARTIAL`;
7. nine stable empty record sets separated by the preregistered global dwell ->
   `QUIESCENCE_EVIDENCE_COMPLETE`;
8. every other combination -> `UNKNOWN`.

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
- every lifecycle variant coupled to `launch_authorized=true` or `relaunch_authorized=true`.

Positive fixtures must cover `RUNNING`, `TERMINATED_COMPLETE`, `TERMINATED_PARTIAL`, and
`QUIESCENCE_EVIDENCE_COMPLETE`. Every case retains both authority flags false; none returns
permission. These are reducer unit fixtures, not claims about the actual iteration-135 lifecycle.

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
