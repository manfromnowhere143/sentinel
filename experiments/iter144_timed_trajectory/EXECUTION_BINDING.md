# Iter144 execution binding

The original preregistration is commit b84348d0a50a80f6050ce8cb3bcf11f876e402ea.
The geometry dependency addition is 45177728347d9afa2a3691875a936b7dfc898622.
The tested and executed implementation is c7dce0639c7fca8f8f34171b31f282811ab31d44.
The raw artifact commit is bc8c1b7ca52b34797d9f7cd75846defdf6418f0e.

Run from the extracted source packet identified in proof/source_packet.json:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 -m experiments.iter144_timed_trajectory.qualify --root PACKET --output NEW_RAW_PATH
python3 -m experiments.iter144_timed_trajectory.independent --root PACKET --raw RAW_PATH --output NEW_ANALYSIS_PATH
```

Use new output paths; runners reject overwrite. Exact absolute paths, argv, cwd,
exit code and elapsed wall time are retained under proof/commands. Source packet
file hashes bind the executed bytes. The independent checker imports only stdlib,
reconstructs interpolation/costs/transitions and checks candidate selection, clocks,
source identity, controls, Jacobians, stopping and numerical replicas.

The retained tests include admission known-bads; proof/artifact_knownbads.json adds
17 mutations of complete measured artifacts with exact mutation paths and hashes.
The mutation helper makes each from the same committed raw artifact and calls the
committed independent checker. Successful rejection does not assert completeness of
all possible corruptions. proof/qualification_binding.json binds raw, source, checker,
analysis and known-bad identities. Canonical master and hosted CI are unchanged.
