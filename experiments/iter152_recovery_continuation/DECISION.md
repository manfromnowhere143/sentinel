# Next decision: establish a useful action around the observed stationary obstacle

11 October 2026. **Proposed next work after the completed Iter152 continuation.**
All fourteen new episodes and both scenario comparisons passed replay. The collision case
has no recovery witness in either one-second pulse arm. All benign-case arms completed;
the monitor added 13 simulated seconds and the pulses added 0.75 and 1.25 s versus nominal.
The study is closed, both compute envelopes are closed and no owned job remains.

The [exploratory applied-action inspection](proof/applied_action_inspection.json) narrows the
next question. It reads the actual simulator step input, rather than the nominal controller
output that precedes the pulse override. The early pulse applies -2 m/s², reaches zero speed
after 0.5 simulated seconds and holds zero through the pulse window. The late pulse applies
-2 m/s² for all four registered steps. All observed actor states are unchanged across the
four retained pulse replicas; the final source-defined foreground collision still occurs.
These are trace descriptions from exposed cases, not a newly registered mechanism claim.

The next useful investigation is a bounded **action-feasibility diagnostic** using the retained
source geometry and execution model. A brief stop followed by the existing nominal policy has
already been measured. Before collecting new driving outcomes:

1. Register a finite family of candidate maneuvers, including any proposed lateral/reference
   change, its timing, duration, control limits and progress constraints. Define a fixed search
   budget, stopping, missingness and claim rules. Preserve all current negative outcomes.
2. Keep privileged source actor geometry explicitly diagnostic. An action constructed using
   that geometry can test whether a recovery is available; it cannot establish a deployable
   information channel or monitor benefit. Maintain separate interfaces and provenance for
   available observations, source state, candidate action and measured outcome.
3. Qualify candidate dynamics, reference timing and source-defined collision/route checks with
   deterministic replay and known-bads before new GPU work. Require actual applied controls
   and sufficient continuation to assess eventual outcome. A converged optimizer, a surrogate
   collision score or temporary non-collision cannot substitute for that outcome.
4. If the bounded model search finds a candidate, register a fresh simulator validation with
   identical initial state, independent replay, matched control budgets and a competent
   responsive baseline. Any held-out generalization claim needs genuinely new source scenes.
5. If no candidate succeeds, report the tested family and budget. A failed finite search is
   not a proof of inevitable collision. Reassess action coverage and model adequacy before
   investing in a new detector or latent-information model.

Only after an effective action is established should a controlled information-selection study
ask which additional observation selects it in time, against that responsive baseline and with
costs held fixed. Timing, intervention burden, useful progress, nulls and unknowns remain visible.

This decision does not authorize reopening Iter148 or Iter151, relabelling their missing slots,
retrying initialized Iter152 slots, or changing the frozen source. A future protocol uses fresh
identities and resources under Daniel's existing autonomous-work authority; no human ceremony
is pending. No physical safety, complete reachability, production readiness or industrial
superiority is established.
