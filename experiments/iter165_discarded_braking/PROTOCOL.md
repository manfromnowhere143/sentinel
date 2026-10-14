# Frozen continuation protocol

The PLAN and CANDIDATES files define the population, schedule, resources and input
identities. `candidates.py` enumerates exactly 25 discarded full-braking and 24
retained frame-27 roots from committed Iter164 records. `prefix_for` reconstructs
the unchanged 25-control historical prefix and the two selected controls.

`run` uses the unchanged Iter164 exact/24 search from absolute frame 27 (6.75 s).
Every root retains 374 possible later controls, bounded by absolute frame 401.
No checkpoint is rebased. Controls, geometry, 276,519 selected centers, diagnostic
ambiguity handling and route-progress completion are unchanged. Initial-prefix
eligibility is decided by independent admission, never inferred from producer
labels alone. All raw candidates are retained even if admission later fails.

`check` checks committed raw bytes against their complete inventory; binds the
frozen source; reconstructs population selection; mechanically audits every beam;
and independently checks complete joined selected paths. The scalar classifier
caches only its own classifications for identical binary64 vertex encodings
against one fixed population. It stores exact packed masks and reports new and
reused checks separately. Different geometry or another population cannot reuse
an entry. The cache does not import vector producer classifications.

Complete means route progress at least 1 with both original checkpoints checked.
A finite failure is a method/budget result. All 49 paths remain visible. No stopping
on success, retries, parameter changes, seed selection, alternative source runs,
or native execution is included. Future planner qualification has its own frozen
source and cannot alter this experiment's accepted bytes.
