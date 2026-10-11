# HANDOFF — offline repository snapshot

Mode: deterministic repository-local tombstone from `scripts/make_handoff.py`. Read `CONTINUITY.md` first.
Authority: NONE. This output is not execution-lifecycle evidence.
Publication: do not replace the retained `HANDOFF.md` without a separately reviewed repository publication control.

## Repository observation

- Working-tree state: OBSERVATION_UNAVAILABLE_SOURCE_BOUND_LIFECYCLE_OBSERVER_NOT_ACCEPTED
- Commit identity: UNKNOWN
- This renderer does not execute commands; validate repository identity and working-tree status through an independently accepted control.

## Canonical mission state (`MISSION_STATE.json`)

- Current: iteration 134 / PLACEBO_HARM_OR_NULL / run UNKNOWN / next iteration 135 CI_HARDENING_REQUIRED
- Current result: experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md
- Next program: semantics-free placebo dose-response causal closure
- Authorized now:
  - implement and validate only offline, content-addressed CI inputs, exact dependency locks, supply-chain manifests, independent evidence replay, and known-bad controls
  - retain the accepted lifecycle-control source without running a host observer or changing external governance settings
- Forbidden now:
  - access, inventory, prepare, mutate, or execute on any iteration-135 remote host, provider, filesystem, packet, runtime, lock, container, GPU, credential, or evidence path
  - create, execute, publish, or advance any H, E, P, or S descendant; lifecycle observation; launch activation; live smoke; or analytic episode
  - infer IDLE, termination, completion, readiness, approval, authority, hermeticity, authenticity, reproducibility, or SLSA conformance from a green workflow or incomplete proof
  - run analyzers or publish iteration-135 data, results, claims, figures, paper text, or scientific conclusions
  - change branch protection, rulesets, Actions policy, repository visibility, credentials, secrets, access control, or other external governance settings without explicit operator authorization
  - rerun iteration 134 or adapt iteration-135 schedules, estimands, verdicts, or policies after evidence

## Execution lifecycle observation

- Observation status: OBSERVATION_UNAVAILABLE_SOURCE_BOUND_LIFECYCLE_OBSERVER_NOT_ACCEPTED
- Lifecycle state: UNKNOWN
- No execution, completion, termination, readiness, or relaunch conclusion is licensed by this snapshot.

## Open threads (from repository-local experiment docs)

- Canonical completed experiment: experiments/iter134_neuroncap_placebo_semantics_execution/RESULT.md — read it before opening new work.
- Active preregistered hypothesis / pending experiment: experiments/iter135_neuroncap_blind_braking_dose_response/HYPOTHESIS.md — read it with `MISSION_STATE.json`; neither file overrides the other.
- Deprecated pending pre-registration: experiments/iter38_track_query_opposite_direction/HYPOTHESIS.md — historical only; it does not govern the next action.
- Canonical next action: iteration 135 / CI_HARDENING_REQUIRED / semantics-free placebo dose-response causal closure.
- Lifecycle correction: earlier current-status prose in `README.md` and `docs/NEXT_PHASE.md` said no run was in flight; both surfaces now report that lifecycle is `UNKNOWN`.
- docs/NEXT_PHASE.md: check its status ledger and decision rules.
- docs/paper/MANUSCRIPT.md: check its status ledger and decision rules.

## Verification before you act

- Run: `ruff check . && pytest -q && python3 scripts/validate_docs.py`
- All three must pass before and after changes. The current workflow runs the same commands on push; a green workflow is validation evidence, not authority.
