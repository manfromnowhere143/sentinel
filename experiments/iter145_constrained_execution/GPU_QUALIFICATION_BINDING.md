# Prospective GPU integration qualification

2026-10-10. This is a finite engineering qualification after complete asset inventory,
not the proposed 14-scenario study or a safety/recovery comparison. No new outcome has
been observed. Preserve all controller thresholds, seed 136 and explicit .25-second
execution/.5-second nominal knots. Nominal delivery only; monitor runs in shadow. Explicitly set both driver and
client seed to 136; the released client default was 0. This new qualification
regime is not a byte-identical reproduction of historical episodes.

Execute these fresh cases once each in order, stopping the batch on any failure:
scene-0013-easy-00, scene-0038-extreme-00, scene-0013-hard-00,
scene-0038-medium-01. These cover empty actors, Attack plus Constant, IDM with map,
and Constant with map. Each has at most 12 steps and 1,200 seconds including
initialization; the complete batch has at most 4,800 seconds. No episode retry.
A normal simulator terminal event is retained but does not qualify the 12-step contract.
No forced-brake outcome is produced. Scientific study admission remains false.

Before launch, qualify the exact source packet under the installed interpreter, verify
all frozen source/asset bindings, current image, available memory/storage, idle GPU and
owned cleanup. One new VM start after inspection shutdown; total provider envelope
5,400 seconds, at most $4.50 incremental VM compute at conservative $3/hour. No new
hardware/disk/bucket or package installation. Existing persistent storage baseline is
excluded. Keep local free >=15 GiB, host free >=100 GiB, projected remaining >=25 GiB;
output <=8 GiB. Arm independent host and local shutdown protection. Do not kill foreign
containers or workloads. Use one exclusive control/output tree and named owned container.

Run the actual HUGSIM constructor, renderer, CUDA, GEOS foreground geometry, background
collision code and frozen UniAD image/checkpoint. The new bounded driver owns the sole
reset, FIFO deadlines, controller/actor execution and terminal receipts. Preserve the
original runtime/source files. The model/client container reads source and checkpoint
mounts read-only; only its owned output is writable. Copy the existing trajdata cache
into the owned control tree and redirect the loader's cache_location argument explicitly
to this copy, retaining original file hashes. This prevents incidental cache construction
from changing the inventoried source cache. No map algorithm or scene selection changes.

Record actual CUDA device/model identities, every camera call and synchronized rendering
time, GEOS version, observations, monitor decisions, typed deliveries, control certificates,
actor transitions, wall times, stops and cleanup. Require complete 12-step traces, one reset,
correct epoch/frame/timestamp/delivery alignment and independent scalar control/transition
replay. Retain failed partial traces. Verify raw identities before interpretation and commit
raw before aggregate claims. Report latency distributions separately from convergence;
50 ms remains a descriptive complete-controller deadline bar, not an admission threshold.
Do not infer physical fidelity, global optimality, industrial superiority or generalization.
