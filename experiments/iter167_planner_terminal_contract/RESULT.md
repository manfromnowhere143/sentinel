# Iter167: the corrected control-RRT adapter does not qualify

**Contradicted.** The fixed adapter completes **0 of 4** disclosed feasible controls.
Every run exhausts 18,000 attempted transitions; none reaches the 120-second cap.
The terminal-clock correction prevents the early completions that invalidated
Iter166. All four retained partial paths pass separate scalar admission.

| Case | Attempts | Selected actions | Final progress | Observed checkpoints |
| --- | ---: | ---: | ---: | ---: |
| Bend left | 18,000 | 18 | 0.999468 | 1 of 2 |
| Bend right | 18,000 | 27 | 0.813397 | 1 of 2 |
| Chicane left | 18,000 | 23 | 0.700389 | 1 of 2 |
| Chicane right | 18,000 | 25 | 0.990056 | 1 of 2 |

The independent checker validates **97 states and full masks**, 706,398 scalar
point-state classifications, the four observed checkpoint conditions, motion,
controls and geometry. An unobserved second checkpoint is not a pass. Native
approximate-solution status is not completion. Budget and selected-edge accounting
pass. Unselected physical rejection labels remain producer evidence.

The native tree uses released OMPL 2.0.1; Sentinel supplies a fixed one-step directed
sampler, route-biased targets and the physical callbacks. This result concerns that
adapter, those seeds and those exposed development cases. It is not a general RRT
benchmark or proof that Sentinel outperforms released planners. No RRT source-scene
comparison, native recovery, information benefit or transfer is established.

Source `1641ff1e355e4ae28222b3502b3249915eb13aae`; raw
`9232d3565d25c0cf08d9af49ab8332ee331d4455` committed before independent admission.
Producer 60.934 seconds; checker 7.774 seconds. All four worker processes and both
supervisors reaped; local CPU only, no provider access or spending. The preceding
invalid qualification remains visible in Iter166. No valid run was retried.
