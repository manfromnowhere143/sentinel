# Iteration 138 execution binding

Preregistration: `43bc7ff185123e9cb91ef748b54d94f37ea9c343`.
Executed source packet: `a25e9f09be2a495893c430a3c62bd2da2f4eef8c`.
Runtime manifest SHA-256: `2afa5216879316314e3bafb976bfc959a5c8759b673b5ffe922fd2453380ce08`.
All 409 previously bound upstream/assets/control files matched before deployment; the new
manifest binds 439 files, including the new isolated packet and driver. Historical files were
not edited. The initial draft accidentally inherited Iter136 schema/counter labels; these were
corrected before any live episode and retained separately as draft evidence.

The original `sentinel-gpu` g2-standard-8/L4 started on the first asynchronous request.
Project sunlit-unison-487018-b0, zone us-west1-a, instance ID 3834622546652649531.
The guest shutdown timer is armed against the fixed session budget, with a conservative margin.
No package or image installation. Exact prepared client image and upstream revisions are in
HYPOTHESIS.md. Simulator PYTHONPATH excludes the client-only Torch shim; the client retains it.

Source and asset checks, 138 focused tests and implementation/test Ruff passed. The host's
actual environment-class import and a CPU capture-to-action fixture passed, including independent
original-source replay. The fixture constructed no simulator and is not a driving episode.
An initial known-bad test exposed missing structured input-failure logging; its failure and the
fix are retained. Unsupported/nonfinite input fails before actuation, with no substitute control.

Driver seed remains 136, client seed 0. NumPy/BLAS/OpenMP threads are fixed to one. Effective
libraries, versions and CPU affinity are retained in each controller-log header and must match
across references. The Iter137 controller source is byte-identical and always uses numerical
mode. Actual input dtype is preserved. No timed-mode live branch is included.

The standard driving trace reuses the validated `sentinel.iter136.trace.v1` format under the
new filename `iter138_trace.jsonl`, with the new driver identity. `controller138.jsonl` has a new
Iter138 schema and links one solver receipt to each original trace frame and applied action.
The new pair must pass both original trace comparators and exact numerical-record equality.
B's launcher independently replays all A controller calls before allowing B to start.

## Timing boundaries

- Solver and internal adapter durations retain Iter137 definitions.
- `complete_call_ns` is measured immediately around the returning adapter call and includes
  its final outer metadata construction. Controller-log serialization and write are outside it.
- `client_roundtrip_ns` starts after observation/state trace hashing and immediately before
  sending the observation. It ends after the plan is received and unpickled, before trace
  selection/logging. It includes pipe transport and client work; it is not isolated inference time.
- None of these wall times determines the simulator's fixed 0.25 s step. The 50 ms threshold
  remains descriptive engineering accounting, not a validated vehicle control deadline.

Raw A proof is committed before B; raw B proof before paired interpretation. Each episode has
one exclusive output path and no retry. Generated videos and raw scene files remain in the
remote new output directory; collect the receipts, controller/observation traces, monitor output,
state/data logs and evaluation artifacts needed for every reported outcome. If a large asset
is left remote, retain its path, size and hash rather than imply it is in Git.
