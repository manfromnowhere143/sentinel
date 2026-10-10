# Prospective Iter146 GPU qualification

2026-10-10. Eight fresh short qualification episodes on fixed scene-0013-easy-00.yaml:
nominal replicas 1,2; monitor replicas 1,2; brake_t0 replicas 1,2; brake_t2_5 replicas 1,2.
The case is fixed before this regime's outcomes. Seed 144 in both host and client; one reset;
24 actions maximum (six simulated seconds) covers the late pulse through its end at 3.5 s.
This separately qualifies all four actual transport/actuation paths, fresh replicas and the
new display-output policy. Full 401-action execution was qualified with CPU substitutes;
full-horizon GPU execution is still unobserved. No 112-slot study admission or recovery
comparison follows from short qualification. An unexpected terminal is retained and stops
qualification; no initialized retry, replacement, seed search or success stopping.

One new start of the existing g2-standard-8 / L4 sentinel-gpu, same exact provider identity
as Iter145. Maximum 5,400 seconds and $4.50 incremental compute at conservative $3/hour.
No new VM/disk/bucket or package installation. Refresh official pricing, identity, idle
state, source and asset hashes, >=100 GiB host free, >=15 GiB local free, >=24 GiB host RAM,
>=20,000 MiB free GPU memory. Copy source map cache into owned control. Preserve all originals.
Arm host and local shutdown protection; verify TERMINATED and watchdog exit at the end.
All prior envelopes are closed. No authority or budget carries over from their timers.

Each child process has a hard 600-second inclusive deadline; the parent kills only its
owned process group and container. Before each pair, require remaining provider budget
>1,300 seconds. Stop on any failed worker, invalid replay or replica disagreement. No later
arm is admitted until prior raw is committed locally and independent replay passes. All
missing later arms remain missing. This is agent-generated operational verification.

Keep the original model, monitor, source/asset/config identities and numerical bars.
Remove only visualization-process creation from the generated client; retain the exact AST
delta. Constructor PLY files remain. Per-case output: 512 MiB allocation, stop polling at
448 MiB, 256 MiB per-file hard bound, 4 MiB per event, 25 GiB host reserve. Eight-case output
allocation is 4 GiB. No instantaneous aggregate quota claim. The proposed later 112-slot
allocation is 56 GiB and needs a fresh resource admission and runtime budget.

Pass requires 24 recorded steps per case, exact arm/timestamp/monitor/transport alignment,
independent control/transition/route/outcome replay, CUDA rendering and foreground geometry,
explicit stop and cleanup, plus fresh replica agreement. Compare numeric state/action/actor
values at 1e-9 absolute tolerance; require typed plan bytes and input image hashes exactly
equal. Ignore elapsed timing and episode-name differences for replica comparisons. Preserve
any disagreement as invalid paired evidence, not as averaged outcomes or a rerun request.
Physical validity, independent background point-cloud collision and real-time operation
remain unestablished. Report full-loop, exchange, controller and simulator timing separately.
