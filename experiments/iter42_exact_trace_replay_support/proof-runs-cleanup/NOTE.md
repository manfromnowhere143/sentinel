# proof-runs-cleanup — supplementary preservation archive (added 2026-07-12)

This directory was added on 2026-07-12 by the pre-HUGSIM disk cleanup
(`docs/research/BOX_CLEANUP_2026-07-12.md`), AFTER iteration 42's result was published. It is
NOT part of the iteration-42 registered evidence chain, which is complete in `proof-trace/`
(the exact trace, run/watch logs, analyzer report, and command record). Nothing in
`proof-trace/` was modified.

`i42-runs.tar.gz` preserves the per-run NeuroNCAP JSON outputs of the iteration-42 trace run
from `sentinel-gpu:/opt/sentinel-stack/NeuroNCAP/outoutput/iter42-trace/` before that
directory was deleted to free root disk for the HUGSIM transfer lane. It follows the
committed run-archive convention of `full14_benchmark/proof/f14-runs.tar.gz` and
`full14_power/proof/p14-runs.tar.gz`, extended with two additional JSON types:

- members: `i42-trace/<scenario>/run_<n>/{metrics,actors,ego_poses,trajectories,reference_trajectory}.json`
- 20 scenarios x 20 runs = 400 run directories, 2,000 members total
- SHA256 `a1a55d5409511d07ca9db13e787ca3f338718c987935d0338457f0b271e214ff`
  (verified identical on the box before transfer and locally after transfer)
- created on the box with:
  `tar -czf /tmp/i42-runs.tar.gz --transform 's,^iter42-trace,i42-trace,' $(find iter42-trace -name metrics.json -o -name actors.json -o -name ego_poses.json -o -name trajectories.json -o -name reference_trajectory.json | sort)`
  from `/opt/sentinel-stack/NeuroNCAP/outoutput/`

Rendered frames (`CAM_FRONT/`, `FC_TRAJ/`, `COMBINED_OUTPUTS/`) were not preserved; they have
never been part of any committed evidence chain in this campaign (the f14/p14 run archives
kept JSON only), and the registered iteration-42 evidence object is the exact trace in
`proof-trace/`, whose SHA256 is unchanged.
