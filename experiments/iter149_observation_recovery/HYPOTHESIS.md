# Iter149: bounded observation recovery qualification

Prospective engineering protocol, 11 October 2026. Parent research commit:
`2e59af25280d1c780c7abe7a076a9ee9df8da312`.
This is a local control qualification, with no driving episodes, provider access or GPU budget.
Freeze this document in Git before qualification. Iter148 remains closed and inconclusive.

## Question and reason to continue

Can an observer recover from temporary transport loss without duplicating initialized work,
accepting stale or incomplete completion evidence, or extending a resource deadline?
Iter148's supervisor stopped on the first failed IAP observation while its worker was alive.
The correction must distinguish observation availability from execution state.

## Contract

The observer attaches to already initialized work. Its API has no launch, resume or reset action.
Bind observations to VM ID, exact start, source digest, plan digest, pair, initialization digest,
host boot and host deadline identity. Initialization is exclusive and immutable. A request token
must match the response; durable snapshot revisions may stay equal only when their bytes agree.
Older revisions, reused replies, changed identities and conflicting snapshots cannot advance work.

States are `observation_unavailable`, `worker_running`, `worker_failed`, `worker_complete`,
`partial_evidence`, and `identity_mismatch`. Empty output, a vanished process and a transport
error are never completion. A complete snapshot requires a successful terminal worker record,
summary and raw inventory, reconciled against their retained content digests. Completion is
operational only; existing scientific replay and pair admission remain separate requirements.
Partial evidence may resolve on a later read; an explicit failed worker terminates observation.

Use finite total observations, consecutive unavailable-observation allowance, fixed bounded
backoff, bounded individual reads and an absolute local monotonic deadline. Successful reads
reset only the consecutive fault count. They never replenish total reads or move any deadline.
Reject malformed, partial, duplicated, stale and excessively large responses without trusting
them. Identity mismatch stops reconciliation immediately. No action targets a newly started VM.

A host watchdog independent of the observer enforces its own monotonic deadline. Cross-host
monotonic clock values are not subtracted. Shutdown requires exact ownership reconciliation;
unavailable or mismatched closure evidence is `unknown`, never verified termination. The
local qualification uses a synthetic subprocess and separate watchdog; cloud adapter behavior
and provider shutdown remain unqualified until tested in a fresh, non-scientific envelope.

## Fixed qualification and acceptance

Exercise delayed responses, temporary and permanent disconnection, duplicate and stale replies,
wrong VM start, malformed replies, partial writes, worker crash, completion during disconnection,
budget exhaustion and observation recovery followed by another outage. Also test deadline
boundaries, changed source/plan/pair/marker/boot/deadline, conflicting revisions, missing or corrupt
terminal artifacts, duplicate initialization and unavailable or mismatched shutdown readback.

Retain an input/output trace for each deterministic case. A separately implemented checker must
reconstruct each decision without calling the production transition function. Corrupt traces
must be rejected. Use an exhaustive bounded combination test in addition to named cases.
The real subprocess test must prove watchdog termination while the observer is disconnected,
preserve partial output, and reject a second initialization of the same path. Tests may reveal
implementation defects; retain failures and corrections without changing these acceptance rules.

Acceptance: all named requirements pass, checker agrees, known-bads are rejected, no duplicate
execution, bounded observations and elapsed budget, durable partial evidence, and observed local
owned-process termination. Scope is explicitly local. No cloud, physical safety, generalization,
real-time driving or state-of-the-art result follows from this qualification.

## Scientific continuation after control qualification

Propose a fresh prospective development protocol, keeping the interrupted study's accounting
visible. Seek one constructive recovery witness against nominal and a responsive monitor before
adding a signal. Use fixed action/time choices, full-prefix checks, completion/progress and harm
outcomes, with no adaptive retries of initialized slots. A future design must bind actual host
adapters and costs before launch. The three exposed scenes cannot supply a fresh holdout claim.

Stop expanding infrastructure once the named failure class is qualified; use the next experiment
to distinguish inadequate action, late intervention and missing information. Failure to find a
recovery in a finite library is not a global impossibility result.
