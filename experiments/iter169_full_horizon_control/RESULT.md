# Full-horizon prediction alone does not qualify the longer turns

**Status: contradicted.** Independent admission accepts the evidence, but the
preregistered controller completes **10/12** unchanged tasks. Both eight-frame
turns fail. Stopping, waiting, restarting and both two-frame turns pass. The
retained two-step connector also completed 10/12.

The full-horizon controller uses **731 attempted transitions**, versus 6,899 for
the retained two-step connector, within the same 8,192-transition/30-second cap
per case. There are 132 full trajectory evaluations and seven exact cache hits.
This is a comparison on exposed constructed tasks, not general efficiency evidence.

Both longer turns return SciPy's successful `xtol` termination status, yet retain
the initial trajectory: normalized terminal error does not improve from
10,020.4623. Each uses 264 transitions; neither reaches a resource cap. Optimizer
termination therefore does not establish task completion.

The initialization contains steering values of magnitude 5.300924469105862e-17.
The configured relative derivative step of 1e-6 produces perturbations near
5e-23. A separate scalar diagnostic shows how such a representable perturbation
can leave a residual unchanged. This identifies a numerical hypothesis; this
study alone does not prove that correcting the step qualifies either turn.

Independent admission replays all 731 attempted transitions for motion, physical
and task constraints and accounting. It reconstructs **213 states and full masks**
across twelve witnesses, twelve selected paths and twelve retained comparator
paths: **206,184 scalar point-state classifications**. Unselected background
labels remain producer evidence. These are twelve deterministic model cases,
not road trials, source recovery or safety evidence. All twelve witnesses pass.

One initialized run, no retries, no source comparison, no native driving, no
provider use or spending. Producer and checker exited successfully and were
reaped. Source: `fb6d6e28e59e4d09ce48977ada851e9e89cf3b95`.
Raw committed before admission: `a3fff76456fd74f8739baf03bfcab0b96c66c1f9`.

[Independent admission](proof/admission.json) · [raw execution](proof/search_raw/execution.json) ·
[protocol](PROTOCOL.md) · [decision](DECISION.md).
