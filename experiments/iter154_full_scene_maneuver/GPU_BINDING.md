# Iter154 execution binding

Only block0 and the two fixed slots in STUDY_PLAN.json. Fresh exclusive remote root:
/datasets/nuscenes-full/hugsim/iter154_maneuver_20261011. Retain all older roots and markers.
Run the qualified source with python3 -u -m experiments.iter154_full_scene_maneuver.execute
--block 0 --source <frozen-commit> from the owned same-repository checkout. No initialized retry.
Reuse the existing Iter150 Cloud transport/watchdog and Iter151 ownership/collection semantics.
The native observation adapter has its own Iter154 summary schema and requires no absent client
logs; no UniAD container launches. The simulator's renderer and collision functions remain active.
Read HYPOTHESIS.md for outcome, validation, resource and inference boundaries.
